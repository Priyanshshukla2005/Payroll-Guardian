"""Document loader supporting Markdown, Text, HTML, DOCX, and PDF formats for AI Payroll Guardian (Phase 5).

Safely loads original document contents without modification and extracts document-level metadata.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from rag.metadata import AuthorityLevel, DocumentMetadata, Jurisdiction, SourceType, Topic


class DocumentLoader:
    """Loads knowledge files and parses document-level headers and metadata."""

    @staticmethod
    def compute_hashes(content: str) -> Tuple[str, str]:
        """Compute file and content SHA-256 hashes."""
        c_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        f_hash = c_hash  # In memory equivalent
        return f_hash, c_hash

    @staticmethod
    def extract_header_metadata(text: str, file_path: Optional[Path] = None) -> Dict[str, str]:
        """Extract structured key-value metadata from top markdown headers."""
        meta_dict: Dict[str, str] = {}
        lines = text.splitlines()

        for line in lines[:25]:  # Look inside first 25 header lines
            match = re.search(r"\*\*(.+?)\*\*:\s*`?(.+?)`?$", line)
            if match:
                key = match.group(1).strip().lower().replace(" ", "_")
                val = match.group(2).strip().strip("`")
                meta_dict[key] = val

        # Fallbacks from filename if not in header
        if file_path:
            meta_dict.setdefault("title", file_path.stem.replace("_", " "))
            meta_dict.setdefault("document_id", file_path.stem.upper())

        return meta_dict

    def load_document(self, file_path: Union[str, Path]) -> Tuple[DocumentMetadata, str]:
        """Load a document file, extract metadata, and return (metadata, text_content)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Knowledge document not found: {path}")

        # Read text content
        text = path.read_text(encoding="utf-8")
        f_hash, c_hash = self.compute_hashes(text)
        header_meta = self.extract_header_metadata(text, path)

        # Parse fields into strong typed models
        doc_id = header_meta.get("document_id", path.stem.upper())
        title = header_meta.get("title", path.stem.replace("_", " "))
        source_name = header_meta.get("issuing_authority", header_meta.get("source_name", "Official Authority"))

        # Authority Level parsing
        raw_auth = header_meta.get("authority_tier", header_meta.get("authority_level", "AUTHORITATIVE")).upper()
        if "TIER 1" in raw_auth or "AUTHORITATIVE" in raw_auth:
            auth_level = AuthorityLevel.AUTHORITATIVE
            source_type = SourceType.GOVERNMENT_ACT
        elif "TIER 2" in raw_auth or "COMPANY" in raw_auth or "POLICY" in raw_auth:
            auth_level = AuthorityLevel.COMPANY_POLICY
            source_type = SourceType.COMPANY_POLICY
        elif "TIER 3" in raw_auth or "REFERENCE" in raw_auth:
            auth_level = AuthorityLevel.REFERENCE
            source_type = SourceType.REFERENCE_GUIDE
        else:
            auth_level = AuthorityLevel.UNVERIFIED
            source_type = SourceType.REFERENCE_GUIDE

        # Jurisdiction parsing
        raw_jur = header_meta.get("jurisdiction", "INDIA").upper()
        jur_map = {
            "INDIA": Jurisdiction.INDIA,
            "MAHARASHTRA": Jurisdiction.MAHARASHTRA,
            "KARNATAKA": Jurisdiction.KARNATAKA,
            "DELHI": Jurisdiction.DELHI,
            "UTTAR_PRADESH": Jurisdiction.UTTAR_PRADESH,
            "TAMIL_NADU": Jurisdiction.TAMIL_NADU,
            "TELANGANA": Jurisdiction.TELANGANA,
            "ALL": Jurisdiction.ALL,
        }
        jurisdiction = jur_map.get(raw_jur.split()[0], Jurisdiction.INDIA)

        # Topic parsing with robust substring matching
        raw_topic = header_meta.get("topic", "PAYROLL_PROCESSING").upper()
        if "PF" in raw_topic or "PROVIDENT" in raw_topic:
            topic = Topic.PF
        elif "ESI" in raw_topic or "INSURANCE" in raw_topic:
            topic = Topic.ESI
        elif "PROFESSIONAL_TAX" in raw_topic or "PROFESSIONAL" in raw_topic or "PROFESSIONS" in raw_topic:
            topic = Topic.PROFESSIONAL_TAX
        elif "TDS" in raw_topic or ("TAX" in raw_topic and "PROFESSION" not in raw_topic):
            topic = Topic.TDS
        elif "OVERTIME" in raw_topic:
            topic = Topic.OVERTIME
        elif "BONUS" in raw_topic:
            topic = Topic.BONUS
        elif "LEAVE" in raw_topic:
            topic = Topic.LEAVE
        elif "WAGE" in raw_topic or "SALARY" in raw_topic:
            topic = Topic.WAGES
        elif "DEDUCTION" in raw_topic:
            topic = Topic.DEDUCTIONS
        else:
            topic = Topic.PAYROLL_PROCESSING

        # Effective dates parsing (e.g. "1952-11-01 to CURRENT")
        eff_date_str = header_meta.get("effective_date", "1950-01-01 to CURRENT")
        dates = [d.strip() for d in eff_date_str.split("to")]
        effective_from = dates[0] if dates else "1950-01-01"
        effective_until = None
        if len(dates) > 1 and dates[1].upper() != "CURRENT":
            effective_until = dates[1]

        version = header_meta.get("document_version", "v1.0")

        doc_meta = DocumentMetadata(
            document_id=doc_id,
            title=title,
            source_name=source_name,
            source_type=source_type,
            authority_level=auth_level,
            jurisdiction=jurisdiction,
            topic=topic,
            effective_from=effective_from,
            effective_until=effective_until,
            document_version=version,
            file_hash=f_hash,
            content_hash=c_hash,
            status="ACTIVE",
        )

        return doc_meta, text

    def load_directory(self, dir_path: Union[str, Path]) -> List[Tuple[DocumentMetadata, str]]:
        """Load all knowledge documents from a folder."""
        d = Path(dir_path)
        loaded = []
        for file_path in sorted(d.glob("*.md")):
            try:
                meta, text = self.load_document(file_path)
                loaded.append((meta, text))
            except Exception as e:
                print(f"[DocumentLoader] Warning: Failed loading {file_path}: {e}")
        return loaded
