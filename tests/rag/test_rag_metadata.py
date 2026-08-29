"""Unit tests for RAG metadata models and registry deduplication."""

from pathlib import Path
import pytest

from rag.ingestion.document_registry import DocumentRegistry
from rag.metadata import (
    AuthorityLevel,
    DocumentMetadata,
    Jurisdiction,
    SourceType,
    Topic,
)


def test_document_metadata_serialization():
    """Verify DocumentMetadata model validation and JSON serialization."""
    meta = DocumentMetadata(
        document_id="TEST_EPFO_001",
        title="EPFO Contribution Test",
        source_name="EPFO",
        source_type=SourceType.GOVERNMENT_ACT,
        authority_level=AuthorityLevel.AUTHORITATIVE,
        jurisdiction=Jurisdiction.INDIA,
        topic=Topic.PF,
        effective_from="2024-01-01",
        effective_until=None,
        document_version="v1.0",
        file_hash="abc123hash",
        content_hash="def456hash",
    )

    d = meta.model_dump()
    assert d["document_id"] == "TEST_EPFO_001"
    assert d["authority_level"] == "AUTHORITATIVE"
    assert d["jurisdiction"] == "INDIA"


def test_registry_duplicate_detection(tmp_path):
    """Verify DocumentRegistry detects duplicate content hashes."""
    reg_file = tmp_path / "test_reg.json"
    registry = DocumentRegistry(registry_file=reg_file)

    meta1 = DocumentMetadata(
        document_id="DOC_01",
        title="Doc 1",
        source_name="Official",
        source_type=SourceType.GOVERNMENT_ACT,
        authority_level=AuthorityLevel.AUTHORITATIVE,
        jurisdiction=Jurisdiction.INDIA,
        topic=Topic.PF,
        effective_from="2024-01-01",
        file_hash="h1",
        content_hash="",
    )

    content = "This is unique statutory text."
    ok1, msg1 = registry.register_document(meta1, content)
    assert ok1 is True

    # Try registering second document with identical text
    meta2 = DocumentMetadata(
        document_id="DOC_02",
        title="Doc 2",
        source_name="Official",
        source_type=SourceType.GOVERNMENT_ACT,
        authority_level=AuthorityLevel.AUTHORITATIVE,
        jurisdiction=Jurisdiction.INDIA,
        topic=Topic.PF,
        effective_from="2024-01-01",
        file_hash="h2",
        content_hash="",
    )

    ok2, msg2 = registry.register_document(meta2, content)
    assert ok2 is False
    assert "Duplicate content" in msg2
