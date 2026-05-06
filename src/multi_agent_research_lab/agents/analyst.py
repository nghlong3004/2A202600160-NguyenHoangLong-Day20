"""Analyst agent — turns research notes into structured insights."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an expert analyst. Given research notes and source documents, produce a structured "
    "analysis that:\n"
    "1. Identifies the key claims and findings.\n"
    "2. Compares different viewpoints or approaches.\n"
    "3. Flags any weak evidence or contradictions.\n"
    "4. Highlights the most impactful insights.\n"
    "5. Provides a brief assessment of evidence quality.\n"
    "Write in clear, analytical English with bullet points where appropriate."
)


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self) -> None:
        self._llm = LLMClient(temperature=0.1)

    def run(self, state: ResearchState) -> ResearchState:
        """Populate ``state.analysis_notes``."""

        logger.info("[Analyst] Starting analysis")

        source_list = "\n".join(
            f"- [{i}] {s.title}: {s.snippet[:120]}..."
            for i, s in enumerate(state.sources, 1)
        )

        user_prompt = (
            f"Original query: {state.request.query}\n\n"
            f"Research notes:\n{state.research_notes or '(none)'}\n\n"
            f"Sources:\n{source_list or '(none)'}\n\n"
            "Produce a structured analysis following the guidelines in your instructions."
        )

        response = self._llm.complete(_SYSTEM_PROMPT, user_prompt)
        state.analysis_notes = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("analyst", {
            "analysis_length": len(response.content),
        })

        logger.info("[Analyst] Done — %d chars analysis", len(response.content))
        return state
