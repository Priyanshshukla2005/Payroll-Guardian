"""AI Payroll Guardian — Grounded LLM Explanation & AI Assistant Module (Phase 6)."""

from ai.llm.assistant import PayrollAIAssistant
from ai.llm.client import PayrollLLMClient
from ai.llm.context_builder import ContextBuilder, StructuredLLMInput
from ai.llm.eval_dataset import LLMEvalCase, get_default_llm_eval_dataset
from ai.llm.evaluator import CaseEvaluationResult, LLMEvalScorecard, LLMEvaluator
from ai.llm.grounded_generator import GroundedExplanationGenerator
from ai.llm.prompts import (
    ANOMALY_EXPLANATION_PROMPT,
    COMPLIANCE_EXPLANATION_PROMPT,
    CORRECTION_PROMPT,
    PAYROLL_ADMIN_QA_PROMPT,
    SUMMARY_GENERATION_PROMPT,
    SYSTEM_PROMPT_GROUNDED_EXPLAINER,
)
from ai.llm.provider import (
    AnthropicLLMProvider,
    BaseLLMProvider,
    LLMResponse,
    MockGroundedLLMProvider,
    OpenAILLMProvider,
    ProviderConfig,
    ProviderFactory,
)
from ai.llm.response_schema import (
    AssistantQueryResponse,
    CitationReference,
    ExplanationSeverity,
    GroundedAnomalyItem,
    PayrollExplanationResponse,
)
from ai.llm.safety import (
    ConfidenceDecoupler,
    PIISanitizer,
    PromptInjectionDefense,
    RefusalEngine,
)
from ai.llm.validator import (
    GroundednessChecker,
    PayrollLLMValidator,
    ValidationResult,
)

__all__ = [
    # Providers & Configuration
    "BaseLLMProvider",
    "ProviderConfig",
    "LLMResponse",
    "MockGroundedLLMProvider",
    "OpenAILLMProvider",
    "AnthropicLLMProvider",
    "ProviderFactory",
    # Response Schemas
    "ExplanationSeverity",
    "CitationReference",
    "GroundedAnomalyItem",
    "PayrollExplanationResponse",
    "AssistantQueryResponse",
    # Context & Prompts
    "ContextBuilder",
    "StructuredLLMInput",
    "SYSTEM_PROMPT_GROUNDED_EXPLAINER",
    "ANOMALY_EXPLANATION_PROMPT",
    "COMPLIANCE_EXPLANATION_PROMPT",
    "PAYROLL_ADMIN_QA_PROMPT",
    "SUMMARY_GENERATION_PROMPT",
    "CORRECTION_PROMPT",
    # Safety & Sanitization
    "PIISanitizer",
    "PromptInjectionDefense",
    "RefusalEngine",
    "ConfidenceDecoupler",
    # Validation
    "PayrollLLMValidator",
    "ValidationResult",
    "GroundednessChecker",
    # Generation & Assistant
    "GroundedExplanationGenerator",
    "PayrollAIAssistant",
    "PayrollLLMClient",
    # Evaluation
    "LLMEvalCase",
    "get_default_llm_eval_dataset",
    "CaseEvaluationResult",
    "LLMEvalScorecard",
    "LLMEvaluator",
]
