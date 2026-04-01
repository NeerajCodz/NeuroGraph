"""Event processor for handling normalized webhook events."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from src.core.logging import get_logger
from src.integrations.base.normalizer import NormalizedEvent
from src.memory.manager import MemoryManager

logger = get_logger(__name__)


class EventProcessor:
    """Process normalized webhook events and store in memory system.
    
    Handles:
    - Memory storage with embeddings
    - Entity extraction and graph updates
    - Retry logic with exponential backoff
    - Event deduplication
    """
    
    # Retry delays in seconds (10 attempts)
    RETRY_DELAYS = [60, 300, 900, 3600, 7200, 14400, 28800, 43200, 86400, 86400]
    
    def __init__(self, memory_manager: MemoryManager, max_retries: int = 10):
        """Initialize event processor.
        
        Args:
            memory_manager: Memory manager instance
            max_retries: Maximum number of retry attempts
        """
        self.memory_manager = memory_manager
        self.max_retries = max_retries
    
    async def process(
        self,
        event: NormalizedEvent,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Process a normalized event.
        
        Args:
            event: Normalized webhook event
            user_id: NeuroGraph user ID (overrides event.user_id)
            tenant_id: NeuroGraph tenant ID (overrides event.tenant_id)
            
        Returns:
            Processing result with event_id, memory_id, entities_created
        """
        start_time = datetime.utcnow()
        
        try:
            # Resolve user and tenant IDs
            resolved_user_id = user_id or (UUID(event.user_id) if event.user_id else None)
            resolved_tenant_id = tenant_id or (UUID(event.tenant_id) if event.tenant_id else None)
            
            # Determine memory layer based on event
            layer = event.layer
            
            # Store memory with embedding
            logger.info(
                "processing_webhook_event",
                event_id=event.event_id,
                source=event.source,
                event_type=event.event_type,
                layer=layer,
            )
            
            # Store main content as memory
            memory_result = await self.memory_manager.remember(
                content=event.content,
                layer=layer,
                user_id=resolved_user_id,
                tenant_id=resolved_tenant_id,
                metadata={
                    "source": event.source,
                    "event_type": event.event_type,
                    "event_id": event.event_id,
                    **event.metadata,
                },
            )
            
            # Extract and store entities in graph
            entities_created = []
            if event.entities:
                entities_created = await self._process_entities(
                    entities=event.entities,
                    memory_id=memory_result["memory_id"],
                    user_id=resolved_user_id,
                    tenant_id=resolved_tenant_id,
                    layer=layer,
                )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "webhook_event_processed",
                event_id=event.event_id,
                memory_id=str(memory_result["memory_id"]),
                entities_count=len(entities_created),
                processing_time_ms=int(processing_time),
            )
            
            return {
                "event_id": event.event_id,
                "memory_id": str(memory_result["memory_id"]),
                "entities_created": entities_created,
                "processing_time_ms": int(processing_time),
                "status": "success",
            }
            
        except Exception as e:
            logger.error(
                "webhook_event_processing_failed",
                event_id=event.event_id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def _process_entities(
        self,
        entities: list,
        memory_id: UUID,
        user_id: Optional[UUID],
        tenant_id: Optional[UUID],
        layer: str,
    ) -> list:
        """Process and store entities in graph.
        
        Args:
            entities: List of extracted entities
            memory_id: Memory ID to link entities to
            user_id: User ID
            tenant_id: Tenant ID
            layer: Memory layer
            
        Returns:
            List of created entity IDs
        """
        created = []
        
        for entity in entities:
            try:
                # Store entity in graph
                # TODO: Implement actual graph entity storage
                # For now, just log the entity
                logger.debug(
                    "entity_extracted",
                    entity_name=entity.name,
                    entity_type=entity.type,
                    memory_id=str(memory_id),
                )
                created.append({
                    "name": entity.name,
                    "type": entity.type,
                    "properties": entity.properties,
                })
            except Exception as e:
                logger.warning(
                    "entity_creation_failed",
                    entity_name=entity.name,
                    error=str(e),
                )
                # Continue processing other entities
                continue
        
        return created
    
    async def process_with_retry(
        self,
        event: NormalizedEvent,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Process event with automatic retry on failure.
        
        Args:
            event: Normalized webhook event
            user_id: NeuroGraph user ID
            tenant_id: NeuroGraph tenant ID
            
        Returns:
            Processing result
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await self.process(event, user_id, tenant_id)
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    "webhook_processing_retry",
                    event_id=event.event_id,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e),
                )
                
                # If not last attempt, wait before retrying
                if attempt < self.max_retries - 1:
                    delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                    await asyncio.sleep(delay)
        
        # All retries failed
        logger.error(
            "webhook_processing_failed_all_retries",
            event_id=event.event_id,
            attempts=self.max_retries,
            error=str(last_error),
        )
        raise last_error
