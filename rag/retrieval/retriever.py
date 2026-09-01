"""RAG Retriever and Evidence Card Query Builder for AI Payroll Guardian (Phase 5).

Translates Phase 4 anomaly evidence cards into grounded compliance queries,
performs date- and jurisdiction-aware hybrid retrieval, and generates structured citations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from rag.citations.citations import CitationFormatter
from rag.embeddings.embeddings import BaseEmbeddingProvider, SentenceTransformerEmbeddingProvider, TFIDFEmbeddingProvider
from rag.metadata import (
    AuthorityLevel,
    ChunkMetadata,
    Jurisdiction,
    RetrievedChunk,
    StructuredRAGResponse,
    Topic,
)
from rag.retrieval.reranker import AuthorityAwareReranker
from rag.retrieval.vector_store import PayrollVectorStore


class PayrollRAGRetriever:
    """Primary retrieval engine bridging anomaly detection evidence with authoritative compliance knowledge."""

    def __init__(
        self,
        vector_store: PayrollVectorStore,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        reranker: Optional[AuthorityAwareReranker] = None,
        min_relevance_threshold: float = 0.25,
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider or TFIDFEmbeddingProvider()
        self.reranker = reranker or AuthorityAwareReranker()
        self.min_relevance_threshold = min_relevance_threshold

    @staticmethod
    def build_query_from_evidence_card(
        evidence_card: Union[Dict[str, Any], Any],
        jurisdiction_override: Optional[Jurisdiction] = None,
    ) -> Tuple[str, Optional[Topic], Jurisdiction, str]:
        """Convert a Phase 4 evidence card into a targeted RAG compliance query.

        Returns:
            Tuple of (query_text, topic, jurisdiction, payroll_date).
        """
        rec = evidence_card.model_dump() if hasattr(evidence_card, "model_dump") else dict(evidence_card)

        anom_types = rec.get("anomaly_types", [])
        if isinstance(anom_types, str):
            anom_types = [anom_types]

        rule_violations = rec.get("rule_violations", [])
        payroll_month = rec.get("payroll_month", "2024-06")
        payroll_date = f"{payroll_month[:7]}-01"

        # Extract peer location if present to infer jurisdiction
        peer_comp = rec.get("peer_comparison", {})
        raw_loc = peer_comp.get("location", "INDIA").upper()

        if jurisdiction_override:
            jurisdiction = jurisdiction_override
        elif "MAHARASHTRA" in raw_loc or "MUMBAI" in raw_loc or "PUNE" in raw_loc:
            jurisdiction = Jurisdiction.MAHARASHTRA
        elif "KARNATAKA" in raw_loc or "BENGALURU" in raw_loc or "BANGALORE" in raw_loc:
            jurisdiction = Jurisdiction.KARNATAKA
        elif "DELHI" in raw_loc:
            jurisdiction = Jurisdiction.DELHI
        elif "UP" in raw_loc or "NOIDA" in raw_loc or "UTTAR PRADESH" in raw_loc:
            jurisdiction = Jurisdiction.UTTAR_PRADESH
        else:
            jurisdiction = Jurisdiction.INDIA

        # Map anomaly types and rule violations to queries and topics
        query_terms = []
        topic = None

        if any("PF" in a or "PF" in str(rule_violations) for a in anom_types):
            topic = Topic.PF
            query_terms.append("EPFO Provident Fund statutory 12 percent basic wage contribution ceiling calculation")

        elif any("ESI" in a or "ESI" in str(rule_violations) for a in anom_types):
            topic = Topic.ESI
            query_terms.append("ESIC Employees State Insurance wage ceiling 21000 contribution rate exemption")

        elif any("PROFESSIONAL_TAX" in a or "DEDUCTION" in a for a in anom_types):
            topic = Topic.PROFESSIONAL_TAX
            query_terms.append("State Professional Tax monthly gross salary deduction slabs and exemptions")

        elif any("OVERTIME" in a for a in anom_types):
            topic = Topic.OVERTIME
            query_terms.append("Company Overtime compensation hourly basic rate 1.5x monthly cap policy")

        elif any("BONUS" in a for a in anom_types):
            topic = Topic.BONUS
            query_terms.append("Annual Performance and Festive Diwali Bonus disbursement guidelines")

        elif any("ATTENDANCE" in a or "LEAVE" in a for a in anom_types):
            topic = Topic.LEAVE
            query_terms.append("Working days attendance limits and Loss of Pay LOP salary calculation")

        elif any("NET" in a or "GROSS" in a or "RECONCILIATION" in str(rule_violations) for a in anom_types):
            topic = Topic.WAGES
            query_terms.append("Gross and Net salary arithmetic reconciliation formula deductions")

        else:
            topic = Topic.PAYROLL_PROCESSING
            query_terms.append("General payroll disbursement arithmetic and statutory deduction compliance")

        query_str = " ".join(query_terms)
        return query_str, topic, jurisdiction, payroll_date

    def retrieve(
        self,
        query: str,
        jurisdiction: Jurisdiction = Jurisdiction.INDIA,
        payroll_date: str = "2024-06-01",
        topic: Optional[Topic] = None,
        authority_level: Optional[AuthorityLevel] = None,
        top_k: int = 5,
        top_n: int = 3,
    ) -> StructuredRAGResponse:
        """Perform date- and jurisdiction-aware hybrid retrieval and reranking."""
        # 1. Check for unknown jurisdiction
        if jurisdiction == Jurisdiction.UNKNOWN:
            return StructuredRAGResponse(
                query=query,
                jurisdiction=jurisdiction,
                payroll_date=payroll_date,
                topic=topic,
                results=[],
                total_found=0,
                status="JURISDICTION_UNKNOWN",
                no_answer_reason="Jurisdiction is UNKNOWN. Cannot determine applicable statutory regulation without geographic jurisdiction.",
            )

        if not self.vector_store or len(self.vector_store.chunks_metadata) == 0:
            return StructuredRAGResponse(
                query=query,
                jurisdiction=jurisdiction,
                payroll_date=payroll_date,
                topic=topic,
                results=[],
                total_found=0,
                status="NO_RELIABLE_SOURCE_FOUND",
                no_answer_reason="No authoritative legal sources found in the knowledge index.",
            )

        # 2. Embed query
        q_vec = self.embedding_provider.embed_query(query)

        # 3. Vector search with hard date, topic, and jurisdiction pre-filtering
        candidates = self.vector_store.search(
            query_vector=q_vec,
            top_k=top_k,
            jurisdiction=jurisdiction,
            payroll_date=payroll_date,
            topic=topic,
            authority_level=authority_level,
        )

        if not candidates:
            return StructuredRAGResponse(
                query=query,
                jurisdiction=jurisdiction,
                payroll_date=payroll_date,
                topic=topic,
                results=[],
                total_found=0,
                status="NO_RELIABLE_SOURCE_FOUND",
                no_answer_reason=f"No active authoritative sources found matching topic={topic}, jurisdiction={jurisdiction.value}, payroll_date={payroll_date}.",
            )

        # 4. Rerank candidates using authority tiers and exact regulatory lexical match
        reranked = self.reranker.rerank(query, candidates, top_n=top_n)

        # 5. Format structured evidence chunks
        results: List[RetrievedChunk] = []
        for meta, text, sim_score, rerank_score in reranked:
            if rerank_score < self.min_relevance_threshold:
                continue

            citation = CitationFormatter.format_citation(meta)
            chunk_obj = RetrievedChunk(
                chunk_id=meta.chunk_id,
                document_id=meta.document_id,
                title=meta.title,
                source_name=meta.source_name,
                authority_level=meta.authority_level,
                jurisdiction=meta.jurisdiction,
                effective_from=meta.effective_from,
                effective_until=meta.effective_until,
                page=meta.page_number,
                section=meta.section,
                similarity_score=round(sim_score, 4),
                rerank_score=round(rerank_score, 4),
                text=text,
                citation=citation,
                applicability_status="VERIFIED",
            )
            results.append(chunk_obj)

        if not results:
            return StructuredRAGResponse(
                query=query,
                jurisdiction=jurisdiction,
                payroll_date=payroll_date,
                topic=topic,
                results=[],
                total_found=0,
                status="NO_RELIABLE_SOURCE_FOUND",
                no_answer_reason="Retrieved candidates failed minimum relevance threshold.",
            )

        return StructuredRAGResponse(
            query=query,
            jurisdiction=jurisdiction,
            payroll_date=payroll_date,
            topic=topic,
            results=results,
            total_found=len(results),
            status="SUCCESS",
        )

    def retrieve_for_evidence_card(
        self,
        evidence_card: Union[Dict[str, Any], Any],
        jurisdiction_override: Optional[Jurisdiction] = None,
        top_n: int = 3,
    ) -> StructuredRAGResponse:
        """Convenience method: retrieve directly from a Phase 4 evidence card."""
        query, topic, jurisdiction, payroll_date = self.build_query_from_evidence_card(
            evidence_card,
            jurisdiction_override=jurisdiction_override,
        )
        return self.retrieve(
            query=query,
            jurisdiction=jurisdiction,
            payroll_date=payroll_date,
            topic=topic,
            top_n=top_n,
        )
