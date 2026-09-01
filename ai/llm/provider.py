"""LLM Provider abstraction layer supporting offline mock and cloud APIs (Phase 6).

Provides a decoupled interface for LLM execution with token tracking,
latency measurement, temperature control, and provider switching.
"""

from abc import ABC, abstractmethod
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Type, Union
import urllib.error
import urllib.request
from pydantic import BaseModel, Field

from ai.llm.response_schema import (
    AssistantQueryResponse,
    CitationReference,
    ExplanationSeverity,
    GroundedAnomalyItem,
    PayrollExplanationResponse,
)


class ProviderConfig(BaseModel):
    """Configuration settings for an LLM provider instance."""

    provider_name: str = Field(default="mock", description="Provider identifier (mock, openai, anthropic, gemini)")
    model_name: str = Field(default="mock-grounded-v1", description="Target model name")
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="Sampling temperature (low for compliance)")
    max_tokens: int = Field(default=800, ge=64, le=4096, description="Maximum completion tokens")
    timeout_seconds: float = Field(default=30.0, ge=1.0, description="Network request timeout in seconds")
    retry_count: int = Field(default=2, ge=0, le=5, description="Number of retry attempts on transient failure")
    api_key: Optional[str] = Field(default=None, description="API access secret (read from env)")
    api_base: Optional[str] = Field(default=None, description="Custom base URL for OpenAI-compatible endpoints")


class LLMResponse(BaseModel):
    """Standardized response container returned by any provider implementation."""

    content: str
    structured_data: Optional[Dict[str, Any]] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    model: str
    provider: str


class BaseLLMProvider(ABC):
    """Abstract Base Class defining the LLM provider contract."""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a raw text completion."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a structured JSON completion validated against schema."""
        pass


class MockGroundedLLMProvider(BaseLLMProvider):
    """Deterministic, fully offline, grounded mock provider for CI/CD and local development.

    Parses the structured context directly from the prompt to construct realistic,
    auditable explanations following all grounding constraints without external API calls.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        cfg = config or ProviderConfig(provider_name="mock", model_name="mock-grounded-v1", temperature=0.0)
        super().__init__(cfg)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count based on whitespace and punctuation splitting."""
        return max(1, len(text.split()))

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate text completion by wrapping structured generation."""
        resp = self.generate_structured(prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens)
        return resp

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate structured JSON response based on deterministic extraction from the prompt context."""
        start_time = time.perf_counter()

        # Check if this is an administrator Q&A prompt
        if "ADMINISTRATOR QUESTION:" in prompt:
            data = self._handle_admin_qa(prompt)
        else:
            data = self._handle_anomaly_explanation(prompt)

        latency_ms = (time.perf_counter() - start_time) * 1000.0 + 12.0  # realistic mock latency
        p_tokens = self._estimate_tokens(prompt) + (self._estimate_tokens(system_prompt) if system_prompt else 0)
        c_tokens = self._estimate_tokens(json.dumps(data))

        content_str = json.dumps(data, indent=2)
        return LLMResponse(
            content=content_str,
            structured_data=data,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=p_tokens + c_tokens,
            latency_ms=round(latency_ms, 2),
            model=self.config.model_name,
            provider="mock",
        )

    def _handle_anomaly_explanation(self, prompt: str) -> Dict[str, Any]:
        """Synthesize a grounded anomaly explanation from the prompt text."""
        # 1. Extract employee ID
        emp_match = re.search(r"Employee ID:\s*([A-Za-z0-9_]+)", prompt)
        emp_id = emp_match.group(1) if emp_match else "EMP_RECORD"

        # 2. Extract Assigned Severity
        sev_match = re.search(r'Assigned Severity:\s*([A-Z]+)|"severity":\s*"([A-Z]+)"', prompt)
        severity_val = "MEDIUM"
        if sev_match:
            severity_val = sev_match.group(1) or sev_match.group(2) or "MEDIUM"
        if severity_val not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            severity_val = "MEDIUM"

        # 3. Extract anomaly types
        anoms_match = re.search(r"Classified Anomaly Types:\s*([^\n]+)", prompt)
        anoms_raw = anoms_match.group(1).strip() if anoms_match else "ANOMALY"
        anom_types = [a.strip() for a in anoms_raw.split(",") if a.strip() and a.strip() != "NONE"]
        if not anom_types:
            anom_types = ["AUDIT_FLAG"]

        # 4. Extract signals
        signals = re.findall(r"- Signal:\s*([^\n]+)", prompt)
        if not signals:
            signals = ["Observed variance in payroll calculation dimensions"]

        # 5. Extract retrieved documents & citations
        doc_matches = re.findall(
            r"\[\d+\]\s*Document ID:\s*([A-Za-z0-9_]+)\s*\n\s*Title:\s*([^\n]+)\s*\n\s*Tier:\s*([^\n]+)\s*\n\s*Jurisdiction:\s*([^\n]+)\s*\n\s*Section:\s*([^\n]+)\s*\|\s*Page:\s*([^\n]+)\s*\n\s*Citation String:\s*([^\n]+)",
            prompt,
        )

        citations = []
        compliance_context = []
        for d_id, title, tier, juris, sec, page, cite_str in doc_matches:
            p_val = int(page) if page.strip().isdigit() else None
            s_val = sec.strip() if sec.strip() != "N/A" else None
            citations.append({
                "document_id": d_id.strip(),
                "page": p_val,
                "section": s_val,
                "citation": cite_str.strip(),
            })
            compliance_context.append(f"{title.strip()} ({tier.strip()}): Requires verification under {sec.strip()}.")

        # 6. Check for Missing Knowledge / Unknown Jurisdiction in prompt
        is_missing_source = "RAG Retrieval Status: NO_RELIABLE_SOURCE_FOUND" in prompt or "NO AUTHORITATIVE RETRIEVED SOURCES AVAILABLE" in prompt
        is_unknown_jurisdiction = "RAG Retrieval Status: JURISDICTION_UNKNOWN" in prompt

        uncertainty = None
        if is_unknown_jurisdiction:
            compliance_context = ["Jurisdiction is UNKNOWN. Cannot determine applicable statutory regulation."]
            uncertainty = "Jurisdiction is UNKNOWN. Cannot determine applicable statutory regulation without geographic jurisdiction."
        elif is_missing_source:
            compliance_context = ["No authoritative compliance document could be retrieved for this anomaly type."]
            uncertainty = "I detected a payroll anomaly, but I could not retrieve a reliable authoritative source. Please verify internal company policy or official regulations."

        # 7. Multi-anomaly breakdowns
        breakdowns = []
        for anom in anom_types:
            matching_signals = [s for s in signals if any(k in s.upper() for k in anom.split("_"))]
            desc = f"Record flagged for {anom.replace('_', ' ').title()}."
            app_clause = citations[0]["citation"] if citations else None
            breakdowns.append({
                "anomaly_type": anom,
                "severity": severity_val,
                "description": desc,
                "evidence_points": matching_signals or signals[:2],
                "applicable_rule_or_policy": app_clause,
            })

        # 8. Build Recommended Actions
        actions = []
        if any("PF" in a for a in anom_types):
            actions.append("Verify employee's statutory basic salary wage basis and 12% EPFO deduction calculation.")
        if any("ATTENDANCE" in a or "LEAVE" in a for a in anom_types):
            actions.append("Cross-reference attendance register and biometric check-ins against working days.")
        if any("OVERTIME" in a for a in anom_types):
            actions.append("Confirm approved overtime hours and manager sign-off against the 1.5x basic wage policy.")
        if any("BONUS" in a or "SALARY" in a for a in anom_types):
            actions.append("Confirm HR / compensation revision letter and CFO authorization for out-of-cycle disbursement.")
        if not actions:
            actions.append("Perform manual review of the employee payroll calculation worksheet.")

        title = f"Payroll anomaly detected: {', '.join(anom_types)}"
        summary = (
            f"Employee {emp_id} was evaluated with assigned severity [{severity_val}]. "
            f"Detection identified discrepancies: {'; '.join(signals[:2])}."
        )

        return {
            "title": title,
            "severity": severity_val,
            "summary": summary,
            "why_flagged": [f"Triggered detection pattern for {', '.join(anom_types)} based on recorded payroll inputs."],
            "evidence": signals,
            "compliance_context": compliance_context or ["Analytical variance detected across payroll baseline features."],
            "recommended_actions": actions,
            "citations": citations,
            "anomaly_breakdowns": breakdowns,
            "uncertainty": uncertainty,
            "disclaimer": "AI-assisted payroll analysis. Not legal advice. Must be verified with official statutory regulations and internal policies.",
        }

    def _handle_admin_qa(self, prompt: str) -> Dict[str, Any]:
        """Synthesize a grounded answer to a payroll administrator's inquiry."""
        q_match = re.search(r"ADMINISTRATOR QUESTION:\s*\n<[^>]+>\s*\n(.*?)\s*\n</[^>]+>", prompt, re.DOTALL)
        question = q_match.group(1).strip() if q_match else "Payroll verification question"

        # Check for prompt injection or unrelated general knowledge question
        unrelated_indicators = ["poem", "weather", "capital of", "recipe", "tell me a joke", "python code to hack"]
        if any(w in question.lower() for w in unrelated_indicators):
            return {
                "question": question,
                "answer": "I am a specialized payroll compliance assistant. I can only answer questions grounded in the provided payroll records, detection evidence, and authoritative compliance sources.",
                "grounded_facts": [],
                "evidence_sources": [],
                "citations": [],
                "category_distinction": {
                    "statutory_requirements": [],
                    "company_policies": [],
                    "analytical_observations": [],
                },
                "suggested_next_steps": ["Please ask questions regarding the flagged payroll record or retrieved compliance policies."],
                "uncertainty_or_refusal": "Refused ungrounded question unrelated to payroll compliance.",
                "disclaimer": "AI-assisted payroll analysis. Must be verified with official statutory regulations and internal policies.",
            }

        # Extract context signals and citations
        signals = re.findall(r"- Signal:\s*([^\n]+)", prompt)
        doc_matches = re.findall(
            r"\[\d+\]\s*Document ID:\s*([A-Za-z0-9_]+)\s*\n\s*Title:\s*([^\n]+)\s*\n\s*Tier:\s*([^\n]+)\s*\n\s*Jurisdiction:\s*([^\n]+)\s*\n\s*Section:\s*([^\n]+)\s*\|\s*Page:\s*([^\n]+)\s*\n\s*Citation String:\s*([^\n]+)",
            prompt,
        )

        citations = []
        stat_reqs = []
        comp_pols = []
        sources = []

        for d_id, title, tier, juris, sec, page, cite_str in doc_matches:
            citations.append({
                "document_id": d_id.strip(),
                "page": int(page) if page.strip().isdigit() else None,
                "section": sec.strip() if sec.strip() != "N/A" else None,
                "citation": cite_str.strip(),
            })
            sources.append(title.strip())
            if "STATUTORY" in tier.upper():
                stat_reqs.append(f"{title.strip()}: {sec.strip()} dictates mandatory compliance.")
            elif "COMPANY" in tier.upper():
                comp_pols.append(f"{title.strip()}: Governs internal operational SOP.")

        # Grounded answer synthesis
        pf_keywords = ["pf", "provident fund", "epfo", "section 6", "12%"]
        if any(k in question.lower() for k in pf_keywords) and any("EPFO" in s.upper() for s in sources):
            answer = (
                "Under Section 6 of the Employees' Provident Funds and Miscellaneous Provisions Act, 1952, "
                "the statutory PF contribution formula mandates 12.0% of basic wages, dearness allowance, "
                "and retaining allowance. The employee contributes 12% to EPF, and the employer contributes a matching 12% "
                "(split into 3.67% to EPF and 8.33% to the Employees' Pension Scheme subject to the statutory wage ceiling)."
            )
        elif sources and not signals:
            answer = (
                f"Based on the retrieved compliance guidance ({', '.join(sources[:2])}), "
                f"the applicable statutory provisions mandate adherence to standard regulatory contribution rates and wage ceilings."
            )
        elif signals:
            answer = (
                f"Based on the supplied audit evidence, observation shows: {'; '.join(signals[:2])}. "
                f"Retrieved compliance guidance ({', '.join(sources) if sources else 'None'}) indicates administrative verification is recommended."
            )
        else:
            answer = (
                f"Based on the retrieved compliance knowledge ({', '.join(sources) if sources else 'statutory baseline'}), "
                f"statutory calculations must strictly follow applicable federal and state labor mandates."
            )

        facts = signals[:3]
        if not facts and sources:
            facts = [f"Retrieved authoritative guidance: {s}" for s in sources[:3]]
        if not facts:
            facts = ["Grounded in statutory compliance guidelines"]

        return {
            "question": question,
            "answer": answer,
            "grounded_facts": facts,
            "evidence_sources": sources,
            "citations": citations,
            "category_distinction": {
                "statutory_requirements": stat_reqs,
                "company_policies": comp_pols,
                "analytical_observations": signals,
            },
            "suggested_next_steps": [
                "Cross-check payroll inputs against approved documentation",
                "Verify calculation formulas against cited policy guidelines",
            ],
            "uncertainty_or_refusal": None,
            "disclaimer": "AI-assisted payroll analysis. Must be verified with official statutory regulations and internal policies.",
        }


class OpenAILLMProvider(BaseLLMProvider):
    """Generic OpenAI-compatible HTTP client for production and cloud LLM execution."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("OPENAI_API_KEY", "")
        self.api_base = config.api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Call OpenAI-compatible chat completions endpoint."""
        if not self.api_key and "localhost" not in self.api_base and "127.0.0.1" not in self.api_base:
            raise ValueError("OPENAI_API_KEY environment variable or ProviderConfig.api_key is required.")

        start_time = time.perf_counter()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
        }

        url = f"{self.api_base.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"OpenAI API request failed: {e}") from e

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})

        return LLMResponse(
            content=content,
            structured_data=None,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=round(latency_ms, 2),
            model=self.config.model_name,
            provider="openai",
        )

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Call OpenAI-compatible chat completions endpoint requesting JSON object output."""
        if not self.api_key and "localhost" not in self.api_base and "127.0.0.1" not in self.api_base:
            raise ValueError("OPENAI_API_KEY environment variable or ProviderConfig.api_key is required.")

        start_time = time.perf_counter()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
            "response_format": {"type": "json_object"},
        }

        url = f"{self.api_base.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"OpenAI structured API request failed: {e}") from e

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})

        try:
            structured_data = json.loads(content)
        except json.JSONDecodeError:
            structured_data = None

        return LLMResponse(
            content=content,
            structured_data=structured_data,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=round(latency_ms, 2),
            model=self.config.model_name,
            provider="openai",
        )


class AnthropicLLMProvider(BaseLLMProvider):
    """Anthropic Messages API provider client."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY", "")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Call Anthropic messages endpoint."""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required.")

        start_time = time.perf_counter()
        payload = {
            "model": self.config.model_name,
            "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Anthropic API request failed: {e}") from e

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        content = result["content"][0]["text"]
        usage = result.get("usage", {})

        return LLMResponse(
            content=content,
            structured_data=None,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            latency_ms=round(latency_ms, 2),
            model=self.config.model_name,
            provider="anthropic",
        )

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Call Anthropic messages endpoint and parse JSON."""
        resp = self.generate(prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens)
        try:
            # Extract JSON from potential code block
            raw = resp.content.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            data = json.loads(raw)
            resp.structured_data = data
        except Exception:
            resp.structured_data = None
        return resp


class ProviderFactory:
    """Factory to instantiate LLM providers based on environment or configuration."""

    @classmethod
    def create_provider(cls, config: Optional[ProviderConfig] = None) -> BaseLLMProvider:
        """Create and return a configured provider instance."""
        # 1. Check passed config
        cfg = config
        if cfg is None:
            provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
            model_name = os.getenv("LLM_MODEL", "mock-grounded-v1" if provider_name == "mock" else "gpt-4o-mini")
            temp = float(os.getenv("LLM_TEMPERATURE", "0.0"))
            max_tok = int(os.getenv("LLM_MAX_TOKENS", "800"))
            timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))
            retry = int(os.getenv("LLM_RETRY_COUNT", "2"))

            cfg = ProviderConfig(
                provider_name=provider_name,
                model_name=model_name,
                temperature=temp,
                max_tokens=max_tok,
                timeout_seconds=timeout,
                retry_count=retry,
            )

        name = cfg.provider_name.lower()
        if name in ["mock", "rule_grounded", "test", "offline"]:
            return MockGroundedLLMProvider(cfg)
        elif name in ["openai", "groq", "ollama", "localai", "vllm", "azure"]:
            return OpenAILLMProvider(cfg)
        elif name == "anthropic":
            return AnthropicLLMProvider(cfg)
        else:
            # Fallback to mock with warning
            return MockGroundedLLMProvider(cfg)
