"""Phase 6: Grounded LLM Explanation & Payroll AI Assistant Evaluation Runner.

Runs the benchmark across all 15 curated evaluation scenarios, generates a formatted scorecard,
and produces evaluation artifacts and markdown summaries.
"""

import json
from pathlib import Path
import sys

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.llm.eval_dataset import get_default_llm_eval_dataset
from ai.llm.evaluator import LLMEvaluator
from ai.llm.provider import MockGroundedLLMProvider, ProviderConfig


def main():
    print("=" * 90)
    print("  AI PAYROLL GUARDIAN — PHASE 6 LLM EXPLANATION & ASSISTANT EVALUATION")
    print("=" * 90)

    # 1. Initialize Evaluator with Mock Grounded Provider
    print("\n[1/4] Initializing LLM Evaluator with deterministic provider...")
    config = ProviderConfig(provider_name="mock", model_name="mock-grounded-v1", temperature=0.0)
    provider = MockGroundedLLMProvider(config=config)
    evaluator = LLMEvaluator(provider=provider)

    # 2. Run Benchmark
    print("\n[2/4] Executing 15-case evaluation benchmark across diverse payroll scenarios...")
    cases = get_default_llm_eval_dataset()
    scorecard = evaluator.evaluate(cases)

    # 3. Print Formatted Scorecard
    print("\n[3/4] Evaluation Results Scorecard:")
    print("-" * 90)
    print(f"{'Metric':<38} | {'Score / Value':>18}")
    print("-" * 90)
    print(f"{'Total Evaluation Cases':<38} | {scorecard.total_cases:>18}")
    print(f"{'JSON Schema Validity Rate':<38} | {scorecard.format_validity_rate * 100:>17.1f}%")
    print(f"{'Groundedness Rate':<38} | {scorecard.mean_groundedness * 100:>17.1f}%")
    print(f"{'Citation Accuracy (Zero Fabrication)':<38} | {scorecard.mean_citation_accuracy * 100:>17.1f}%")
    print(f"{'Completeness Score':<38} | {scorecard.mean_completeness * 100:>17.1f}%")
    print(f"{'Detector Faithfulness Score':<38} | {scorecard.mean_faithfulness * 100:>17.1f}%")
    print(f"{'Hallucination Rate':<38} | {scorecard.hallucination_rate * 100:>17.1f}%")
    print(f"{'Refusal & Uncertainty Correctness':<38} | {scorecard.refusal_correctness_rate * 100:>17.1f}%")
    print(f"{'Average Latency per Explanation':<38} | {scorecard.mean_latency_ms:>15.1f} ms")
    print(f"{'Total Tokens Consumed':<38} | {scorecard.total_tokens_consumed:>18}")
    print("-" * 90)

    print("\nDetailed Scenario Breakdown:")
    for r in scorecard.case_results:
        status = "PASSED" if r.is_schema_valid and not r.hallucination_detected and r.refusal_correctness else "FLAGGED"
        print(f"  [{status:<6}] {r.case_id:<36} | Grounded: {r.groundedness_score*100:>5.1f}% | Cites: {r.citation_accuracy*100:>5.1f}% | {r.latency_ms:>5.1f}ms")

    # 4. Save JSON Report
    out_dir = PROJECT_ROOT / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "llm_eval_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(scorecard.model_dump(), f, indent=2)
    print(f"\n[4/4] Saved evaluation report JSON to: {out_json}")
    print("\n" + "=" * 90)
    print("  PHASE 6 LLM BENCHMARK COMPLETE & VERIFIED")
    print("=" * 90)


if __name__ == "__main__":
    main()
