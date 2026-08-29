"""AI training and evaluation metrics package."""

from ai.training.evaluator import (
    AnomalyTypePerformance,
    ModelEvaluationMetrics,
    compute_unique_employee_fp_per_1000,
    evaluate_binary_model,
    sweep_thresholds,
)

__all__ = [
    "ModelEvaluationMetrics",
    "AnomalyTypePerformance",
    "evaluate_binary_model",
    "sweep_thresholds",
    "compute_unique_employee_fp_per_1000",
]
