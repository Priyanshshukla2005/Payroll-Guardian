"""Semantic structural chunker for AI Payroll Guardian (Phase 5).

Chunks documents by logical statutory sections, preserving section headings,
metadata bindings, and complete regulatory paragraphs without arbitrary text truncation.
"""

import re
from typing import Dict, List, Optional, Tuple
from rag.metadata import ChunkMetadata, DocumentMetadata


class SemanticChunker:
    """Chunks structured regulatory and policy documents into standalone semantic units."""

    def __init__(self, target_chunk_size: int = 600, overlap_chars: int = 80):
        self.target_chunk_size = target_chunk_size
        self.overlap_chars = overlap_chars

    def chunk_document(
        self,
        doc_meta: DocumentMetadata,
        content: str,
    ) -> List[Tuple[ChunkMetadata, str]]:
        """Chunk a document into semantically bounded units bound to ChunkMetadata."""
        chunks: List[Tuple[ChunkMetadata, str]] = []

        # Split content by markdown section headers (## or ###)
        section_pattern = r"(^#{2,3}\s+.+$)"
        splits = re.split(section_pattern, content, flags=re.MULTILINE)

        current_section = "General Overview"
        current_heading = doc_meta.title

        chunk_idx = 0
        i = 0
        while i < len(splits):
            part = splits[i].strip()
            if not part:
                i += 1
                continue

            if part.startswith("##"):
                current_section = part.lstrip("#").strip()
                current_heading = current_section
                i += 1
                if i < len(splits):
                    section_body = splits[i].strip()
                    i += 1
                else:
                    section_body = ""
            else:
                section_body = part
                i += 1

            if not section_body:
                continue

            # Split large section bodies by subsections or double newlines if too long
            paragraphs = [p.strip() for p in section_body.split("\n\n") if p.strip()]
            current_buffer = []
            current_len = 0

            for p in paragraphs:
                p_len = len(p)
                if current_len + p_len > self.target_chunk_size and current_buffer:
                    # Flush current buffer
                    chunk_text = "\n\n".join(current_buffer)
                    # Contextual prefix for high semantic retrieval
                    annotated_text = (
                        f"[{doc_meta.source_name} | {doc_meta.title} | {current_section}]\n"
                        f"{chunk_text}"
                    )

                    chunk_id = f"{doc_meta.document_id}_CH_{chunk_idx:03d}"
                    c_meta = ChunkMetadata(
                        chunk_id=chunk_id,
                        document_id=doc_meta.document_id,
                        chunk_index=chunk_idx,
                        title=doc_meta.title,
                        source_name=doc_meta.source_name,
                        authority_level=doc_meta.authority_level,
                        jurisdiction=doc_meta.jurisdiction,
                        topic=doc_meta.topic,
                        effective_from=doc_meta.effective_from,
                        effective_until=doc_meta.effective_until,
                        document_version=doc_meta.document_version,
                        section=current_section,
                        heading=current_heading,
                        char_count=len(annotated_text),
                        token_count=len(annotated_text.split()),
                    )
                    chunks.append((c_meta, annotated_text))
                    chunk_idx += 1
                    current_buffer = [p]
                    current_len = p_len
                else:
                    current_buffer.append(p)
                    current_len += p_len

            if current_buffer:
                chunk_text = "\n\n".join(current_buffer)
                annotated_text = (
                    f"[{doc_meta.source_name} | {doc_meta.title} | {current_section}]\n"
                    f"{chunk_text}"
                )

                chunk_id = f"{doc_meta.document_id}_CH_{chunk_idx:03d}"
                c_meta = ChunkMetadata(
                    chunk_id=chunk_id,
                    document_id=doc_meta.document_id,
                    chunk_index=chunk_idx,
                    title=doc_meta.title,
                    source_name=doc_meta.source_name,
                    authority_level=doc_meta.authority_level,
                    jurisdiction=doc_meta.jurisdiction,
                    topic=doc_meta.topic,
                    effective_from=doc_meta.effective_from,
                    effective_until=doc_meta.effective_until,
                    document_version=doc_meta.document_version,
                    section=current_section,
                    heading=current_heading,
                    char_count=len(annotated_text),
                    token_count=len(annotated_text.split()),
                )
                chunks.append((c_meta, annotated_text))
                chunk_idx += 1

        return chunks
