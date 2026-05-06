"""Search client abstraction for ResearcherAgent."""

import logging

from duckduckgo_search import DDGS

from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Web search client using DuckDuckGo (free, no API key required)."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search the web for documents relevant to a query.

        Falls back to an empty list on error so that the workflow can continue gracefully.
        """

        logger.info("Searching DuckDuckGo: query=%r, max_results=%d", query, max_results)
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
        except Exception:
            logger.warning("DuckDuckGo search failed, returning empty results", exc_info=True)
            return []

        sources: list[SourceDocument] = []
        for item in raw_results:
            sources.append(
                SourceDocument(
                    title=item.get("title", "Untitled"),
                    url=item.get("href"),
                    snippet=item.get("body", ""),
                )
            )

        logger.info("Found %d sources", len(sources))
        return sources
