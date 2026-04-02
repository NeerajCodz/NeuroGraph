"""Redis-backed background memory enrichment worker."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from src.core.logging import get_logger
from src.db.postgres import get_postgres_driver
from src.db.redis import get_redis_driver
from src.models.gemini import get_gemini_client

logger = get_logger(__name__)

MEMORY_ENRICHMENT_QUEUE = "memory:enrichment:queue"
MEMORY_ENRICHMENT_POLL_INTERVAL_SECONDS = 0.5
MEMORY_ENRICHMENT_TIMEOUT_SECONDS = 20.0
MEMORY_ENRICHMENT_MAX_ATTEMPTS = 3

_worker_task: asyncio.Task[None] | None = None
_worker_lock = asyncio.Lock()
_worker_stop_event: asyncio.Event | None = None


def _parse_uuid(value: object) -> UUID | None:
    """Parse UUID from arbitrary payload value."""
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def extract_entity_names(entities_result: dict[str, Any] | None) -> list[str]:
    """Extract normalized entity names from extractor output."""
    if not isinstance(entities_result, dict):
        return []
    entities_raw = entities_result.get("entities")
    if not isinstance(entities_raw, list):
        return []

    names: list[str] = []
    for entity in entities_raw:
        if not isinstance(entity, dict):
            continue
        name = entity.get("name")
        if isinstance(name, str):
            normalized = name.strip()
            if normalized:
                names.append(normalized)
    return names


def build_entity_metadata_patch(
    *,
    status: str,
    source: str,
    entities_result: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Build metadata patch for entity extraction status."""
    patch: dict[str, Any] = {
        "entity_extraction": {
            "status": status,
            "source": source,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        },
        "entities_extracted": extract_entity_names(entities_result)[:25],
    }
    if error:
        patch["entity_extraction"]["error"] = error[:200]
    return patch


def _entity_extraction_error_text(error: Exception) -> str:
    """Create concise error text for metadata/logging."""
    text = str(error)
    if not text:
        return error.__class__.__name__
    if len(text) <= 200:
        return text
    return text[:200]


async def merge_entity_metadata(memory_id: UUID, metadata_patch: dict[str, Any]) -> None:
    """Merge entity metadata patch into memory metadata JSON."""
    postgres = get_postgres_driver()
    async with postgres.connection() as conn:
        await conn.execute(
            """
            UPDATE memory.embeddings
            SET metadata = COALESCE(metadata, '{}'::jsonb) || $2::jsonb,
                updated_at = NOW()
            WHERE id = $1
            """,
            memory_id,
            json.dumps(metadata_patch),
        )


async def enqueue_memory_enrichment(
    *,
    memory_id: UUID,
    user_id: UUID | None,
    layer: str,
    tenant_id: UUID | None,
    attempt: int = 1,
) -> bool:
    """Enqueue a memory enrichment job."""
    payload = {
        "memory_id": str(memory_id),
        "user_id": str(user_id) if user_id else None,
        "layer": layer,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "attempt": attempt,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }
    redis = get_redis_driver()
    try:
        await redis.rpush(MEMORY_ENRICHMENT_QUEUE, json.dumps(payload))
        logger.info(
            "memory_enrichment_queued",
            memory_id=str(memory_id),
            layer=layer,
            attempt=attempt,
        )
        return True
    except Exception as enqueue_error:
        logger.warning(
            "memory_enrichment_queue_failed",
            memory_id=str(memory_id),
            error=str(enqueue_error),
        )
        return False


async def _process_enrichment_payload(payload_raw: str) -> None:
    """Process a single queue payload."""
    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError:
        logger.warning("memory_enrichment_payload_invalid", payload=payload_raw[:200])
        return

    memory_id_raw = payload.get("memory_id")
    if not isinstance(memory_id_raw, str):
        logger.warning("memory_enrichment_payload_missing_id")
        return

    try:
        memory_id = UUID(memory_id_raw)
    except ValueError:
        logger.warning("memory_enrichment_payload_bad_id", memory_id=memory_id_raw)
        return

    attempt = payload.get("attempt", 1)
    if not isinstance(attempt, int):
        attempt = 1

    postgres = get_postgres_driver()
    async with postgres.connection() as conn:
        row = await conn.fetchrow(
            "SELECT content FROM memory.embeddings WHERE id = $1",
            memory_id,
        )

    if not row:
        logger.info("memory_enrichment_memory_missing", memory_id=str(memory_id))
        return

    content = row["content"]
    if not isinstance(content, str) or not content.strip():
        logger.info("memory_enrichment_content_empty", memory_id=str(memory_id))
        return

    gemini = get_gemini_client()
    try:
        entities_result = await asyncio.wait_for(
            gemini.extract_entities(content),
            timeout=MEMORY_ENRICHMENT_TIMEOUT_SECONDS,
        )
        await merge_entity_metadata(
            memory_id,
            build_entity_metadata_patch(
                status="completed",
                source="queue",
                entities_result=entities_result if isinstance(entities_result, dict) else None,
            ),
        )
        logger.info(
            "memory_enrichment_completed",
            memory_id=str(memory_id),
            entities_count=len(extract_entity_names(entities_result if isinstance(entities_result, dict) else None)),
            attempt=attempt,
        )
    except Exception as process_error:
        if attempt < MEMORY_ENRICHMENT_MAX_ATTEMPTS:
            payload_user_id = _parse_uuid(payload.get("user_id"))
            payload_tenant_id = _parse_uuid(payload.get("tenant_id"))
            requeued = await enqueue_memory_enrichment(
                memory_id=memory_id,
                user_id=payload_user_id,
                layer=str(payload.get("layer", "personal")),
                tenant_id=payload_tenant_id,
                attempt=attempt + 1,
            )
            if requeued:
                logger.warning(
                    "memory_enrichment_requeued",
                    memory_id=str(memory_id),
                    attempt=attempt + 1,
                    error=_entity_extraction_error_text(process_error),
                )
            else:
                await merge_entity_metadata(
                    memory_id,
                    build_entity_metadata_patch(
                        status="failed",
                        source="queue",
                        error=_entity_extraction_error_text(process_error),
                    ),
                )
            return

        await merge_entity_metadata(
            memory_id,
            build_entity_metadata_patch(
                status="failed",
                source="queue",
                error=_entity_extraction_error_text(process_error),
            ),
        )
        logger.warning(
            "memory_enrichment_failed",
            memory_id=str(memory_id),
            attempt=attempt,
            error=_entity_extraction_error_text(process_error),
        )


async def _memory_enrichment_worker_loop() -> None:
    """Background loop that processes queued enrichment jobs."""
    global _worker_stop_event
    stop_event = _worker_stop_event
    if stop_event is None:
        return

    logger.info("memory_enrichment_worker_started", queue=MEMORY_ENRICHMENT_QUEUE)
    redis = get_redis_driver()

    while not stop_event.is_set():
        try:
            payload_raw = await redis.lpop(MEMORY_ENRICHMENT_QUEUE)
            if payload_raw is None:
                await asyncio.sleep(MEMORY_ENRICHMENT_POLL_INTERVAL_SECONDS)
                continue
            await _process_enrichment_payload(payload_raw)
        except asyncio.CancelledError:
            raise
        except Exception as loop_error:
            logger.warning("memory_enrichment_worker_error", error=str(loop_error))
            await asyncio.sleep(MEMORY_ENRICHMENT_POLL_INTERVAL_SECONDS)

    logger.info("memory_enrichment_worker_stopped", queue=MEMORY_ENRICHMENT_QUEUE)


async def start_memory_enrichment_worker() -> None:
    """Start singleton enrichment worker task."""
    global _worker_task, _worker_stop_event
    async with _worker_lock:
        if _worker_task is not None and not _worker_task.done():
            return
        _worker_stop_event = asyncio.Event()
        _worker_task = asyncio.create_task(
            _memory_enrichment_worker_loop(),
            name="memory-enrichment-worker",
        )


async def stop_memory_enrichment_worker() -> None:
    """Stop enrichment worker task."""
    global _worker_task, _worker_stop_event
    async with _worker_lock:
        if _worker_task is None:
            return
        if _worker_stop_event is not None:
            _worker_stop_event.set()
        try:
            if not _worker_task.done():
                _worker_task.cancel()
                try:
                    await _worker_task
                except asyncio.CancelledError:
                    pass
        finally:
            _worker_task = None
            _worker_stop_event = None
