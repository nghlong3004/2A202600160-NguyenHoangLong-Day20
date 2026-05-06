"""Researcher agent — collects sources and creates concise research notes."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a thorough research assistant. Given a query, review "
    "the provided search results and produce concise, well-organized "
    "research notes. Include key facts, statistics, and direct quotes "
    "where useful. Always note the source title for each piece of "
    "information. Write in clear, professional English."
)


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self) -> None:
        self._llm = LLMClient(temperature=0.2)
        self._search = SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate ``state.sources`` and ``state.research_notes``."""

        logger.info("[Researcher] Starting for: %s", state.request.query)

        # Step 1: search the web
        sources = self._search.search(
            state.request.query,
            max_results=state.request.max_sources,
        )
        state.sources.extend(sources)

        # Step 2: format sources for LLM context
        source_context = ""
        for i, src in enumerate(sources, 1):
            source_context += (
                f"\n[{i}] {src.title}\n"
                f"    URL: {src.url}\n"
                f"    {src.snippet}\n"
            )

        if not source_context:
            source_context = "(No search results. Use your knowledge.)"

        user_prompt = (
            f"Research query: {state.request.query}\n\n"
            f"Search results:\n{source_context}\n\n"
            "Based on these sources, write detailed research notes "
            "covering the key findings, trends, and important details. "
            "Cite source numbers like [1], [2], etc."
        )

        # Step 3: ask LLM to synthesize notes
        response = self._llm.complete(_SYSTEM_PROMPT, user_prompt)
        state.research_notes = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=response.content,
                metadata={
                    "sources_found": len(sources),
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("researcher", {
            "sources_found": len(sources),
            "notes_length": len(response.content),
        })

        logger.info(
            "[Researcher] Done — %d sources, %d chars",
            len(sources),
            len(response.content),
        )
        return state
