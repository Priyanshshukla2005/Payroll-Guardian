"""Vector Store and Metadata Index for AI Payroll Guardian RAG (Phase 5).

Stores chunk metadata, embeddings, and performs high-speed cosine similarity search
with strict date, jurisdiction, and authority metadata filtering.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from rag.metadata import AuthorityLevel, ChunkMetadata, Jurisdiction, Topic


class PayrollVectorStore:
    """Local vector store with cosine similarity index and rich metadata filtering."""

    def __init__(self, embedding_dimension: int = 256):
        self.embedding_dimension = embedding_dimension
        self.chunks_metadata: List[ChunkMetadata] = []
        self.chunks_text: List[str] = []
        self.embeddings: Optional[np.ndarray] = None  # Shape (N, Dim)

    def add_chunks(
        self,
        chunks_with_meta: List[Tuple[ChunkMetadata, str]],
        embeddings: np.ndarray,
    ) -> None:
        """Add new chunks and their corresponding embedding vectors."""
        if len(chunks_with_meta) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match exactly.")

        for meta, text in chunks_with_meta:
            self.chunks_metadata.append(meta)
            self.chunks_text.append(text)

        if self.embeddings is None:
            self.embeddings = embeddings.astype(np.float32)
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings.astype(np.float32)])

    def _matches_filters(
        self,
        meta: ChunkMetadata,
        jurisdiction: Optional[Jurisdiction] = None,
        payroll_date: Optional[str] = None,
        topic: Optional[Topic] = None,
        authority_level: Optional[AuthorityLevel] = None,
    ) -> bool:
        """Evaluate whether a chunk satisfies all hard metadata filters."""
        # 1. Jurisdiction filter
        if jurisdiction and jurisdiction != Jurisdiction.UNKNOWN:
            if meta.jurisdiction not in (jurisdiction, Jurisdiction.ALL, Jurisdiction.INDIA):
                return False

        # 2. Date applicability filter (effective_from <= payroll_date <= effective_until)
        if payroll_date:
            p_date = payroll_date if len(payroll_date) == 10 else f"{payroll_date[:7]}-01"
            if p_date < meta.effective_from:
                return False
            if meta.effective_until and p_date > meta.effective_until:
                return False

        # 3. Topic filter
        if topic and meta.topic != topic:
            return False

        # 4. Authority level filter
        if authority_level and meta.authority_level != authority_level:
            return False

        return True

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        jurisdiction: Optional[Jurisdiction] = None,
        payroll_date: Optional[str] = None,
        topic: Optional[Topic] = None,
        authority_level: Optional[AuthorityLevel] = None,
    ) -> List[Tuple[ChunkMetadata, str, float]]:
        """Search the vector store returning filtered, ranked (metadata, text, score) tuples."""
        if self.embeddings is None or len(self.chunks_metadata) == 0:
            return []

        # Find candidate indices that satisfy all hard metadata filters
        candidate_indices = []
        for idx, meta in enumerate(self.chunks_metadata):
            if self._matches_filters(meta, jurisdiction, payroll_date, topic, authority_level):
                candidate_indices.append(idx)

        if not candidate_indices:
            return []

        # Cosine similarity on candidate subset (embeddings are L2 normalized)
        cand_embeddings = self.embeddings[candidate_indices]
        q_vec = query_vector.reshape(1, -1)
        sim_scores = np.dot(cand_embeddings, q_vec.T).flatten()

        # Sort descending
        top_cand_order = np.argsort(-sim_scores)[:top_k]
        results = []

        for c_idx in top_cand_order:
            orig_idx = candidate_indices[c_idx]
            score = float(sim_scores[c_idx])
            results.append((self.chunks_metadata[orig_idx], self.chunks_text[orig_idx], score))

        return results

    def save(self, directory_path: Union[str, Path]) -> None:
        """Serialize vector store to directory."""
        d = Path(directory_path)
        d.mkdir(parents=True, exist_ok=True)

        meta_data = [m.model_dump() for m in self.chunks_metadata]
        with open(d / "chunks_metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2)

        with open(d / "chunks_text.json", "w", encoding="utf-8") as f:
            json.dump(self.chunks_text, f, indent=2)

        if self.embeddings is not None:
            np.save(d / "embeddings.npy", self.embeddings)

    @classmethod
    def load(cls, directory_path: Union[str, Path]) -> "PayrollVectorStore":
        """Load serialized vector store."""
        d = Path(directory_path)
        store = cls()

        with open(d / "chunks_metadata.json", "r", encoding="utf-8") as f:
            meta_data = json.load(f)
            store.chunks_metadata = [ChunkMetadata(**m) for m in meta_data]

        with open(d / "chunks_text.json", "r", encoding="utf-8") as f:
            store.chunks_text = json.load(f)

        emb_file = d / "embeddings.npy"
        if emb_file.exists():
            store.embeddings = np.load(emb_file)
            store.embedding_dimension = store.embeddings.shape[1]

        return store
