"""Writer agent — produces final answer from research and analysis notes."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a skilled technical writer. Given research notes and analysis, produce a clear, "
    "well-structured final response. Requirements:\n"
    "1. Write for a {audience} audience.\n"
    "2. Use clear headings and logical structure.\n"
    "3. Include source references like [1], [2] where appropriate.\n"
    "4. Be comprehensive but concise — aim for ~500 words.\n"
    "5. End with a brief 'Sources' section listing the referenced sources."
)


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self) -> None:
        self._llm = LLMClient(temperature=0.4)

    def run(self, state: ResearchState) -> ResearchState:
        """Populate ``state.final_answer``."""

        logger.info("[Writer] Starting final composition")

        system_prompt = _SYSTEM_PROMPT.format(audience=state.request.audience)

        source_refs = "\n".join(
            f"[{i}] {s.title} — {s.url or 'N/A'}"
            for i, s in enumerate(state.sources, 1)
        )

        user_prompt = (
            f"Original query: {state.request.query}\n\n"
            f"Research notes:\n{state.research_notes or '(none)'}\n\n"
            f"Analysis:\n{state.analysis_notes or '(none)'}\n\n"
            f"Available sources:\n{source_refs or '(none)'}\n\n"
            "Write the final, polished response."
        )

        response = self._llm.complete(system_prompt, user_prompt)
        state.final_answer = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("writer", {
            "answer_length": len(response.content),
        })

        logger.info("[Writer] Done — %d chars final answer", len(response.content))
        return state
