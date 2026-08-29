"""Phase 5: RAG Knowledge Pipeline Ingestion, Indexing, and Evaluation runner."""

import json
import sys
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.chunking.chunker import SemanticChunker
from rag.ingestion.document_loader import DocumentLoader
from rag.ingestion.document_registry import DocumentRegistry
from rag.embeddings.embeddings import SentenceTransformerEmbeddingProvider, TFIDFEmbeddingProvider
from rag.evaluation.evaluation import RAGEvaluator, get_default_eval_dataset
from rag.metadata import AuthorityLevel, Jurisdiction, Topic
from rag.retrieval.reranker import AuthorityAwareReranker
from rag.retrieval.retriever import PayrollRAGRetriever
from rag.retrieval.vector_store import PayrollVectorStore


def main():
    print("=" * 90)
    print("  AI PAYROLL GUARDIAN — PHASE 5 RAG KNOWLEDGE INGESTION & EVALUATION")
    print("=" * 90)

    raw_dir = PROJECT_ROOT / "data" / "knowledge" / "raw"
    emb_dir = PROJECT_ROOT / "data" / "knowledge" / "embeddings"
    meta_dir = PROJECT_ROOT / "data" / "knowledge" / "metadata"
    emb_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ingest Raw Documents
    print("\n[1/6] Ingesting knowledge documents from data/knowledge/raw/...")
    loader = DocumentLoader()
    raw_docs = loader.load_directory(raw_dir)
    print(f"      Loaded {len(raw_docs)} source documents.")

    # 2. Register Documents in Registry
    print("\n[2/6] Registering documents with SHA-256 validation...")
    registry = DocumentRegistry(registry_file=meta_dir / "registry.json")
    for doc_meta, text in raw_docs:
        success, msg = registry.register_document(doc_meta, text)
        print(f"      [{doc_meta.authority_level.value:<14}] {doc_meta.document_id:<32} -> {msg}")

    # 3. Structural Semantic Chunking
    print("\n[3/6] Applying semantic structural chunking...")
    chunker = SemanticChunker(target_chunk_size=550, overlap_chars=60)
    all_chunks = []
    for doc_meta, text in raw_docs:
        doc_chunks = chunker.chunk_document(doc_meta, text)
        all_chunks.extend(doc_chunks)
        print(f"      {doc_meta.document_id:<32} -> {len(doc_chunks):>2} semantic chunks.")
    print(f"      Total Chunks Created: {len(all_chunks)}")

    # 4. Generate Embeddings & Build Vector Store
    print("\n[4/6] Embedding semantic chunks and building vector store...")
    chunk_texts = [text for _, text in all_chunks]
    embedding_provider = TFIDFEmbeddingProvider(max_features=256)
    embedding_provider.fit(chunk_texts)
    embeddings = embedding_provider.embed_documents(chunk_texts)

    vector_store = PayrollVectorStore(embedding_dimension=embedding_provider.dimension)
    vector_store.add_chunks(all_chunks, embeddings)
    vector_store.save(emb_dir)
    print(f"      Vector store saved ({len(all_chunks)} vectors, dim={embedding_provider.dimension}).")

    # 5. Initialize RAG Retriever & Run Ground-Truth Benchmark
    print("\n[5/6] Running RAG Retrieval Benchmark across positive and negative queries...")
    reranker = AuthorityAwareReranker(dense_weight=0.55, lexical_weight=0.30, authority_weight=0.15)
    retriever = PayrollRAGRetriever(
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        reranker=reranker,
        min_relevance_threshold=0.20,
    )

    evaluator = RAGEvaluator(retriever)
    eval_report = evaluator.evaluate()

    print("\n--- RAG Retrieval Evaluation Report ---")
    print(f"{'Metric':<35} | {'Value':>12}")
    print("-" * 52)
    print(f"{'Total Evaluation Queries':<35} | {eval_report.total_queries:>12}")
    print(f"{'Recall@1':<35} | {eval_report.recall_at_1*100:>11.1f}%")
    print(f"{'Recall@3':<35} | {eval_report.recall_at_3*100:>11.1f}%")
    print(f"{'Recall@5':<35} | {eval_report.recall_at_5*100:>11.1f}%")
    print(f"{'Mean Reciprocal Rank (MRR)':<35} | {eval_report.mrr:>12.4f}")
    print(f"{'Authority Tier Accuracy':<35} | {eval_report.authority_accuracy*100:>11.1f}%")
    print(f"{'Jurisdiction Accuracy':<35} | {eval_report.jurisdiction_accuracy*100:>11.1f}%")
    print(f"{'Date Applicability Accuracy':<35} | {eval_report.date_applicability_accuracy*100:>11.1f}%")
    print(f"{'Negative Constraint Pass Rate':<35} | {eval_report.negative_test_pass_rate*100:>11.1f}%")

    with open(meta_dir / "rag_eval_results.json", "w", encoding="utf-8") as f:
        json.dump(eval_report.model_dump(), f, indent=2)

    # 6. End-to-End Test with Phase 4 Evidence Card
    print("\n[6/6] Testing End-to-End Evidence Card -> RAG Knowledge Retrieval...")
    sample_evidence_path = PROJECT_ROOT / "models" / "v2" / "sample_evidence_v2.json"
    if sample_evidence_path.exists():
        with open(sample_evidence_path, "r", encoding="utf-8") as f:
            evidence_card = json.load(f)

        rag_resp = retriever.retrieve_for_evidence_card(evidence_card, top_n=2)
        print(f"      Input Evidence Anomaly: {evidence_card.get('anomaly_types')}")
        print(f"      Generated Query       : {rag_resp.query}")
        print(f"      Retrieved Sources ({len(rag_resp.results)}):")
        for idx, res in enumerate(rag_resp.results, 1):
            print(f"        {idx}. {res.title} [{res.authority_level.value}] (Score: {res.rerank_score*100:.1f}%)")
            print(f"           Citation: {res.citation}")
            print(f"           Section : {res.section}")

    print("\n" + "=" * 90)
    print("  PHASE 5 RAG KNOWLEDGE SYSTEM COMPLETE & VERIFIED")
    print("=" * 90)


if __name__ == "__main__":
    main()
