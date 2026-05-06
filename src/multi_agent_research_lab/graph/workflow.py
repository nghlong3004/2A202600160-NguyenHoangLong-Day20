"""Loop-based multi-agent workflow orchestrator.

Keep orchestration here; keep agent internals in ``agents/``.
"""

import logging
from time import perf_counter

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Flow: Supervisor decides → dispatch to worker → repeat until done.
    Guardrails: max_iterations, timeout_seconds, per-agent errors.
    """

    def __init__(self) -> None:
        self._supervisor = SupervisorAgent()
        self._agents = {
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
        }

    def build(self) -> dict[str, object]:
        """Return the agent registry."""

        return {"supervisor": self._supervisor, **self._agents}

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the workflow loop and return final state."""

        settings = get_settings()
        started = perf_counter()

        logger.info("=== Multi-Agent Workflow START ===")
        logger.info("Query: %s", state.request.query)
        logger.info(
            "Max iter: %d, timeout: %ds",
            settings.max_iterations,
            settings.timeout_seconds,
        )

        while True:
            # Check timeout
            elapsed = perf_counter() - started
            if elapsed > settings.timeout_seconds:
                logger.warning("Workflow timeout after %.1fs", elapsed)
                state.errors.append(
                    f"Workflow timeout after {elapsed:.1f}s",
                )
                state.add_trace_event("workflow", {
                    "event": "timeout",
                    "elapsed": elapsed,
                })
                break

            # Supervisor decides next step
            state = self._supervisor.run(state)
            last_route = (
                state.route_history[-1]
                if state.route_history
                else "done"
            )

            if last_route == "done":
                logger.info("Supervisor decided: done")
                break

            # Dispatch to worker agent
            agent = self._agents.get(last_route)
            if agent is None:
                logger.error("Unknown route: %s", last_route)
                state.errors.append(f"Unknown route: {last_route}")
                break

            try:
                logger.info(
                    "--- Dispatching: %s (iter %d) ---",
                    last_route,
                    state.iteration,
                )
                state = agent.run(state)
            except Exception as exc:
                error_msg = f"Agent '{last_route}' failed: {exc}"
                logger.error(error_msg, exc_info=True)
                state.errors.append(error_msg)
                state.add_trace_event("error", {
                    "agent": last_route,
                    "error": str(exc),
                })
                continue

        total_time = perf_counter() - started
        state.add_trace_event("workflow", {
            "event": "complete",
            "total_seconds": total_time,
        })
        logger.info(
            "=== Multi-Agent Workflow END (%.2fs) ===", total_time,
        )

        return state
