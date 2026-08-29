"""Script to generate and execute notebooks/05_rag_evaluation.ipynb."""

import base64
import io
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def create_rag_notebook(notebook_path: Path):
    cells = []

    def md_cell(source: str):
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in source.split("\n")],
        }

    def code_cell(source: str):
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in source.split("\n")],
        }

    # Title
    cells.append(md_cell("""# 📚 AI Payroll Guardian — Payroll & Compliance RAG Knowledge System (Phase 5)
**Project**: AI Payroll Guardian  
**Phase**: Phase 5 — Authoritative Compliance Retrieval & Knowledge Grounding  
**Goal**: Ground detected payroll anomalies in authoritative statutory regulations and internal organizational policies with strict versioning, jurisdiction checking, and date applicability filtering.

---
### 📌 Scope of Analysis
1. **Knowledge Corpus Registry & Authority Tier Distribution**
2. **Structural Semantic Chunking Telemetry**
3. **Date- and Jurisdiction-Aware Hybrid Retrieval**
4. **Retrieval Evaluation Metrics (Recall@K, MRR, Authority Accuracy)**
5. **Negative Query Constraint Verification**
6. **End-to-End Evidence Card $\rightarrow$ Knowledge Grounding Integration**
7. **Traceable Citations & Audit Footnotes**"""))

    # Section 1
    cells.append(md_cell("""## 1. Ingest Knowledge Registry & Vector Store"""))

    cells.append(code_cell("""import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["figure.figsize"] = (12, 5)
plt.rcParams["font.size"] = 10

ROOT_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rag.ingestion.document_registry import DocumentRegistry
from rag.retrieval.vector_store import PayrollVectorStore
from rag.retrieval.retriever import PayrollRAGRetriever
from rag.embeddings.embeddings import TFIDFEmbeddingProvider
from rag.retrieval.reranker import AuthorityAwareReranker
from rag.metadata import Jurisdiction, Topic

reg = DocumentRegistry(ROOT_DIR / "data" / "knowledge" / "metadata" / "registry.json")
v_store = PayrollVectorStore.load(ROOT_DIR / "data" / "knowledge" / "embeddings")

print(f"Loaded Knowledge Registry: {len(reg.documents)} registered documents.")
print(f"Loaded Vector Store     : {len(v_store.chunks_metadata)} semantic chunks (Dim={v_store.embedding_dimension}).")
"""))

    # Section 2
    cells.append(md_cell("""## 2. Document Registry by Authority Tier & Jurisdiction"""))

    cells.append(code_cell("""doc_data = []
for doc in reg.documents.values():
    doc_data.append({
        "Document ID": doc.document_id,
        "Title": doc.title,
        "Authority Tier": doc.authority_level.value,
        "Jurisdiction": doc.jurisdiction.value,
        "Topic": doc.topic.value,
        "Effective From": doc.effective_from,
        "Effective Until": doc.effective_until or "CURRENT",
        "Version": doc.document_version,
    })

doc_df = pd.DataFrame(doc_data)
display(doc_df)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4))
doc_df["Authority Tier"].value_counts().plot(kind="bar", ax=ax1, color="#1971c2")
ax1.set_title("Documents by Authority Tier", fontweight="bold")
ax1.set_ylabel("Count")

doc_df["Topic"].value_counts().plot(kind="barh", ax=ax2, color="#2f9e44")
ax2.set_title("Documents by Compliance Topic", fontweight="bold")
ax2.set_xlabel("Count")

plt.tight_layout()
plt.show()
"""))

    # Section 3
    cells.append(md_cell("""## 3. Structural Semantic Chunk Distribution"""))

    cells.append(code_cell("""chunk_data = []
for m, text in zip(v_store.chunks_metadata, v_store.chunks_text):
    chunk_data.append({
        "Chunk ID": m.chunk_id,
        "Document ID": m.document_id,
        "Section": m.section,
        "Char Count": m.char_count,
        "Token Count": m.token_count,
    })

chunk_df = pd.DataFrame(chunk_data)
display(chunk_df.head(10))

plt.figure(figsize=(10, 4))
sns.histplot(chunk_df["Token Count"], bins=15, kde=True, color="#f08c00")
plt.title("Semantic Chunk Token Length Distribution", fontweight="bold")
plt.xlabel("Token Count per Chunk")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()
"""))

    # Section 4
    cells.append(md_cell("""## 4. Benchmark Retrieval Evaluation Results (Ground Truth Queries)"""))

    cells.append(code_cell("""with open(ROOT_DIR / "data" / "knowledge" / "metadata" / "rag_eval_results.json", "r") as f:
    eval_data = json.load(f)

metrics_table = pd.DataFrame([
    {"Metric": "Recall@1", "Value": f"{eval_data['recall_at_1']*100:.1f}%"},
    {"Metric": "Recall@3", "Value": f"{eval_data['recall_at_3']*100:.1f}%"},
    {"Metric": "Recall@5", "Value": f"{eval_data['recall_at_5']*100:.1f}%"},
    {"Metric": "Mean Reciprocal Rank (MRR)", "Value": f"{eval_data['mrr']:.4f}"},
    {"Metric": "Authority Tier Accuracy", "Value": f"{eval_data['authority_accuracy']*100:.1f}%"},
    {"Metric": "Jurisdiction Accuracy", "Value": f"{eval_data['jurisdiction_accuracy']*100:.1f}%"},
    {"Metric": "Date Applicability Accuracy", "Value": f"{eval_data['date_applicability_accuracy']*100:.1f}%"},
    {"Metric": "Negative Constraint Pass Rate", "Value": f"{eval_data['negative_test_pass_rate']*100:.1f}%"},
])
display(metrics_table)
"""))

    # Section 5
    cells.append(md_cell("## 5. End-to-End Evidence Card to Regulatory Knowledge Retrieval"))

    code_5 = (
        "emb_provider = TFIDFEmbeddingProvider(max_features=256)\n"
        "emb_provider.fit(v_store.chunks_text)\n"
        "reranker = AuthorityAwareReranker()\n"
        "retriever = PayrollRAGRetriever(v_store, emb_provider, reranker)\n\n"
        "with open(ROOT_DIR / 'models' / 'v2' / 'sample_evidence_v2.json', 'r') as f:\n"
        "    sample_evidence = json.load(f)\n\n"
        "resp = retriever.retrieve_for_evidence_card(sample_evidence, top_n=2)\n\n"
        "print('=== INPUT EVIDENCE CARD ===')\n"
        "print('Employee ID    :', sample_evidence.get('employee_id'))\n"
        "print('Anomaly Types  :', sample_evidence.get('anomaly_types'))\n"
        "print('Rule Violations:', sample_evidence.get('rule_violations'))\n"
        "print('Payroll Month  :', sample_evidence.get('payroll_month'))\n\n"
        "print('\\n=== RAG RETRIEVAL RESULT ===')\n"
        "print('Generated Query:', resp.query)\n"
        "print('Jurisdiction   :', resp.jurisdiction.value)\n"
        "print('Status         :', resp.status)\n\n"
        "for i, r in enumerate(resp.results, 1):\n"
        "    print(f'\\n[Result {i}] {r.title} ({r.authority_level.value})')\n"
        "    print(f'  Citation  : {r.citation}')\n"
        "    print(f'  Section   : {r.section}')\n"
        "    print(f'  Relevance : {r.rerank_score*100:.1f}%')\n"
        "    print(f'  Excerpt   : {r.text[:220]}...')\n"
    )
    cells.append(code_cell(code_5))

    notebook_dict = {
        "cells": cells,
        "metadata": {
            "language_info": {"name": "python"}
        },
        "nbformat": 4,
        "nbformat_minor": 2,
    }

    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook_dict, f, indent=2)
    print(f"Created notebook at {notebook_path}")


def execute_notebook(nb_path: Path):
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    exec_globals = {
        "__name__": "__main__",
        "Path": Path,
        "pd": pd,
        "np": np,
        "plt": plt,
    }

    print(f"Executing {nb_path}...")
    exec_count = 1

    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue

        code_text = "".join(cell.get("source", []))
        cell_outputs = []
        old_stdout = io.StringIO()
        real_stdout = sys.stdout
        sys.stdout = old_stdout

        def custom_display(obj):
            if isinstance(obj, (pd.DataFrame, pd.Series)):
                text_repr = obj.to_string()
                html_repr = obj.to_html() if hasattr(obj, "to_html") else f"<pre>{text_repr}</pre>"
                cell_outputs.append({
                    "data": {"text/plain": text_repr, "text/html": html_repr},
                    "metadata": {},
                    "output_type": "display_data"
                })
            else:
                cell_outputs.append({
                    "data": {"text/plain": str(obj)},
                    "metadata": {},
                    "output_type": "display_data"
                })

        exec_globals["display"] = custom_display

        try:
            plt.clf()
            plt.close("all")
            exec(code_text, exec_globals)
            sys.stdout = real_stdout

            stdout_str = old_stdout.getvalue()
            if stdout_str:
                cell_outputs.insert(0, {
                    "name": "stdout",
                    "output_type": "stream",
                    "text": [line + "\n" for line in stdout_str.split("\n") if line]
                })

            figs = [plt.figure(n) for n in plt.get_fignums()]
            for fig in figs:
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
                buf.seek(0)
                img_b64 = base64.b64encode(buf.read()).decode("utf-8")
                cell_outputs.append({
                    "data": {"image/png": img_b64, "text/plain": "<Figure size ...>"},
                    "metadata": {},
                    "output_type": "display_data"
                })
                plt.close(fig)

            cell["execution_count"] = exec_count
            cell["outputs"] = cell_outputs
            print(f"  [Cell {i+1}] Executed successfully ({len(cell_outputs)} outputs).")
            exec_count += 1

        except Exception as e:
            sys.stdout = real_stdout
            print(f"  [Cell {i+1}] ERROR during execution: {e}")
            cell["execution_count"] = exec_count
            cell["outputs"] = [{
                "ename": type(e).__name__,
                "evalue": str(e),
                "output_type": "error",
                "traceback": [f"{type(e).__name__}: {str(e)}"]
            }]
            exec_count += 1

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)

    print(f"\nExecution complete: {nb_path}")


if __name__ == "__main__":
    nb_path = Path("notebooks/05_rag_evaluation.ipynb")
    create_rag_notebook(nb_path)
    execute_notebook(nb_path)
