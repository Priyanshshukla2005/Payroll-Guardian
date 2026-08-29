"""Knowledge Document Registry for AI Payroll Guardian (Phase 5).

Manages document registration, SHA-256 content deduplication, versioning,
and namespace isolation across Authoritative, Company Policy, and Reference sources.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from rag.metadata import AuthorityLevel, DocumentMetadata, Jurisdiction, SourceType, Topic


class DocumentRegistry:
    """Registry maintaining metadata, versions, and integrity hashes for all ingested documents."""

    def __init__(self, registry_file: Optional[Path] = None):
        self.registry_file = registry_file or Path("data/knowledge/metadata/registry.json")
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.documents: Dict[str, DocumentMetadata] = {}
        self.content_hashes: Dict[str, str] = {}  # content_hash -> document_id
        self.load()

    def load(self) -> None:
        """Load registry from disk if it exists."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for doc_id, doc_dict in data.items():
                    meta = DocumentMetadata(**doc_dict)
                    self.documents[doc_id] = meta
                    self.content_hashes[meta.content_hash] = doc_id
            except Exception as e:
                print(f"[DocumentRegistry] Warning: Failed to load registry: {e}")

    def save(self) -> None:
        """Save registry to disk."""
        data = {doc_id: doc.model_dump() for doc_id, doc in self.documents.items()}
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def compute_hash(text: str) -> str:
        """Compute SHA-256 hash of document text content."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def register_document(
        self,
        metadata: DocumentMetadata,
        content: str,
        allow_version_update: bool = True,
    ) -> Tuple[bool, str]:
        """Register a document with validation and duplicate prevention.

        Returns:
            Tuple of (success, message).
        """
        c_hash = self.compute_hash(content)

        # 1. Check for identical duplicate content
        if c_hash in self.content_hashes:
            existing_id = self.content_hashes[c_hash]
            if existing_id == metadata.document_id:
                return True, f"Document {metadata.document_id} already registered with matching content."
            return False, f"Duplicate content: matches existing document {existing_id}."

        # 2. Prevent unauthorized overwrite across authority namespaces
        if metadata.document_id in self.documents:
            existing = self.documents[metadata.document_id]
            if existing.authority_level == AuthorityLevel.AUTHORITATIVE and metadata.authority_level != AuthorityLevel.AUTHORITATIVE:
                return False, f"Permission Denied: Cannot overwrite Authoritative document with {metadata.authority_level}."
            if not allow_version_update:
                return False, f"Document {metadata.document_id} already exists and allow_version_update is False."

        # 3. Register
        metadata.content_hash = c_hash
        self.documents[metadata.document_id] = metadata
        self.content_hashes[c_hash] = metadata.document_id
        self.save()
        return True, f"Successfully registered {metadata.document_id} ({metadata.title}) [{metadata.authority_level}]."

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """Retrieve metadata for a specific document ID."""
        return self.documents.get(document_id)

    def list_documents(
        self,
        topic: Optional[Topic] = None,
        authority_level: Optional[AuthorityLevel] = None,
        jurisdiction: Optional[Jurisdiction] = None,
    ) -> List[DocumentMetadata]:
        """Filter documents by topic, authority level, or jurisdiction."""
        results = []
        for doc in self.documents.values():
            if topic and doc.topic != topic:
                continue
            if authority_level and doc.authority_level != authority_level:
                continue
            if jurisdiction and doc.jurisdiction not in (jurisdiction, Jurisdiction.ALL, Jurisdiction.INDIA):
                continue
            results.append(doc)
        return results

    def is_date_applicable(self, doc: DocumentMetadata, target_date: str) -> bool:
        """Check if target_date (YYYY-MM or YYYY-MM-DD) falls within document's effective lifespan."""
        # Standardize target_date to YYYY-MM-01 if month string
        t_date = target_date if len(target_date) == 10 else f"{target_date[:7]}-01"

        if t_date < doc.effective_from:
            return False
        if doc.effective_until and t_date > doc.effective_until:
            return False
        return True
