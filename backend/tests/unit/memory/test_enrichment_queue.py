"""Unit tests for memory enrichment queue helpers."""

from src.memory.enrichment_queue import (
    build_entity_metadata_patch,
    extract_entity_names,
)


def test_extract_entity_names_filters_invalid_entries() -> None:
    """Entity extractor should keep only valid non-empty names."""
    entities_result = {
        "entities": [
            {"name": "Frank"},
            {"name": "  AI/ML  "},
            {"name": ""},
            {"name": None},
            {},
            "invalid",
        ]
    }

    names = extract_entity_names(entities_result)

    assert names == ["Frank", "AI/ML"]


def test_build_entity_metadata_patch_completed() -> None:
    """Completed patch should include status, source, and extracted entities."""
    patch = build_entity_metadata_patch(
        status="completed",
        source="inline",
        entities_result={"entities": [{"name": "Frank"}, {"name": "DevOps"}]},
    )

    assert patch["entity_extraction"]["status"] == "completed"
    assert patch["entity_extraction"]["source"] == "inline"
    assert "processed_at" in patch["entity_extraction"]
    assert patch["entities_extracted"] == ["Frank", "DevOps"]


def test_build_entity_metadata_patch_failed_truncates_error() -> None:
    """Failed patch should preserve a bounded error payload."""
    long_error = "x" * 500
    patch = build_entity_metadata_patch(
        status="failed",
        source="queue",
        error=long_error,
    )

    assert patch["entity_extraction"]["status"] == "failed"
    assert patch["entity_extraction"]["source"] == "queue"
    assert len(patch["entity_extraction"]["error"]) == 200
    assert patch["entities_extracted"] == []
