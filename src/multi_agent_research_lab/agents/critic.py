"""Optional critic agent for fact-checking and quality validation."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a critical reviewer. Evaluate the provided final answer against the research notes "
    "and sources. Check for:\n"
    "1. Factual accuracy — does the answer align with the sources?\n"
    "2. Citation coverage — are claims properly attributed?\n"
    "3. Completeness — are key findings from the research notes included?\n"
    "4. Hallucination risk — does the answer introduce unsupported claims?\n\n"
    "Rate the answer on a scale of 0-10 and provide a brief justification.\n"
    "Format: SCORE: X/10\\nJUSTIFICATION: ..."
)


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def __init__(self) -> None:
        self._llm = LLMClient(temperature=0.0)

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""

        logger.info("[Critic] Starting fact-check review")

        source_refs = "\n".join(
            f"[{i}] {s.title}: {s.snippet[:100]}..."
            for i, s in enumerate(state.sources, 1)
        )

        user_prompt = (
            f"Original query: {state.request.query}\n\n"
            f"Research notes:\n{state.research_notes or '(none)'}\n\n"
            f"Sources:\n{source_refs or '(none)'}\n\n"
            f"Final answer to review:\n{state.final_answer or '(none)'}\n\n"
            "Evaluate this answer."
        )

        response = self._llm.complete(_SYSTEM_PROMPT, user_prompt)

        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.critic_review = response.content
        state.add_trace_event(
            "critic", {"review_length": len(response.content)},
        )

        logger.info("[Critic] Done — review complete")
        return state
