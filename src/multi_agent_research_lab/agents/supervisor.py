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
        elif not state.critic_review:
            next_route = "critic"
            reason = "final answer produced, need critic review"
        else:
            # Parse score from critic
            import re
            match = re.search(r"SCORE:\s*(\d+)", state.critic_review)
            score = int(match.group(1)) if match else 0
            
            if score >= 7:
                next_route = "done"
                reason = f"critic approved with score {score}/10"
            else:
                next_route = "writer"
                reason = f"critic rejected (score {score}/10) - rewriting"
                # Reset for the next loop
                state.final_answer = None
                state.critic_review = None

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
