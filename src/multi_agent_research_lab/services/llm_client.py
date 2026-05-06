"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

import logging
from dataclasses import dataclass

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)

# DeepSeek pricing (per 1M tokens) — used for cost estimation
_COST_PER_1M_INPUT = 0.14  # USD
_COST_PER_1M_OUTPUT = 0.28  # USD


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client using OpenAI-compatible SDK (DeepSeek, OpenAI, etc.)."""

    def __init__(self, model: str | None = None, temperature: float = 0.2) -> None:
        settings = get_settings()
        self._model = model or settings.openai_model
        self._temperature = temperature
        self._client = OpenAI(
            api_key=settings.openai_api_key or "",
            base_url=settings.openai_base_url or "https://api.openai.com/v1",
            timeout=float(settings.timeout_seconds),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion with retry, timeout, and token logging."""

        logger.info("LLM call: model=%s, temperature=%.1f", self._model, self._temperature)
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        choice = response.choices[0]
        content = choice.message.content or ""
        usage = response.usage

        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None
        cost_usd = None
        if input_tokens is not None and output_tokens is not None:
            cost_usd = (
                input_tokens * _COST_PER_1M_INPUT / 1_000_000
                + output_tokens * _COST_PER_1M_OUTPUT / 1_000_000
            )

        logger.info(
            "LLM response: input_tokens=%s, output_tokens=%s, cost=$%s",
            input_tokens,
            output_tokens,
            f"{cost_usd:.6f}" if cost_usd else "N/A",
        )

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
