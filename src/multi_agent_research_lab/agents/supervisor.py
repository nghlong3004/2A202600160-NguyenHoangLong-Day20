"""Supervisor / router — decides which worker should run next and when to stop."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop.

    Routing policy (rule-based for reliability):
    1. If no research_notes → route to researcher.
    2. If research_notes but no analysis_notes → route to analyst.
    3. If analysis_notes but no final_answer → route to writer.
    4. If final_answer exists → done.
    5. Guardrail: if iteration >= max_iterations → force done.
    """

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update ``state.route_history`` with the next route."""

        settings = get_settings()

        # Guardrail: enforce max iterations
        if state.iteration >= settings.max_iterations:
            logger.warning(
                "[Supervisor] Max iterations (%d) reached — forcing done",
                settings.max_iterations,
            )
            state.record_route("done")
            state.add_trace_event(
                "supervisor",
                {"decision": "done", "reason": "max_iterations"},
            )
            return state

        # Rule-based routing
        if not state.research_notes:
            next_route = "researcher"
            reason = "no research notes yet"
        elif not state.analysis_notes:
            next_route = "analyst"
            reason = "research done, need analysis"
        elif not state.final_answer:
            next_route = "writer"
            reason = "analysis done, need final answer"
        else:
            next_route = "done"
            reason = "final answer produced"

        logger.info(
            "[Supervisor] Route → %s (reason: %s, iter: %d)",
            next_route,
            reason,
            state.iteration,
        )

        state.record_route(next_route)
        state.add_trace_event("supervisor", {
            "decision": next_route,
            "reason": reason,
            "iteration": state.iteration,
        })

        return state
