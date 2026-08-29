"""AI structured explainability and audit evidence generator."""

from ai.explainability.explainer import PayrollExplainer
from ai.explainability.explainer_v2 import DetailedEvidenceCard, PayrollExplainerV2

__all__ = ["PayrollExplainer", "PayrollExplainerV2", "DetailedEvidenceCard"]
