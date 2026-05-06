"""LangGraph-based multi-agent workflow orchestrator."""

import logging
from time import perf_counter

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """Builds and runs the LangGraph multi-agent workflow.

    Flow: Supervisor decides → dispatch to worker → return to supervisor.
    Guardrails: max_iterations (via supervisor), timeout_seconds.
    """

    def __init__(self) -> None:
        self._supervisor = SupervisorAgent()
        self._agents = {
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
            "critic": CriticAgent(),
        }

    def _route(self, state: ResearchState) -> str:
        """Route from supervisor based on the last recorded route."""
        last_route = (
            state.route_history[-1] if state.route_history else "done"
        )
        if last_route == "done":
            return END
        return last_route

    def build(self) -> object:
        """Compile and return the LangGraph application."""

        builder = StateGraph(ResearchState)

        # Add nodes
        builder.add_node("supervisor", self._supervisor.run)
        builder.add_node("researcher", self._agents["researcher"].run)
        builder.add_node("analyst", self._agents["analyst"].run)
        builder.add_node("writer", self._agents["writer"].run)
        builder.add_node("critic", self._agents["critic"].run)

        # Add edges
        builder.add_edge(START, "supervisor")

        # Supervisor conditional routing
        builder.add_conditional_edges(
            "supervisor",
            self._route,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "critic": "critic",
                END: END,
            },
        )

        # All workers return to supervisor
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", "supervisor")
        builder.add_edge("critic", "supervisor")

        return builder.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the workflow graph and return the final state."""

        settings = get_settings()
        started = perf_counter()

        logger.info("=== Multi-Agent Workflow START ===")
        logger.info("Query: %s", state.request.query)
        logger.info(
            "Max iter: %d, timeout: %ds",
            settings.max_iterations,
            settings.timeout_seconds,
        )

        app = self.build()

        try:
            # We use stream to intercept execution and check timeout
            for output in app.stream(
                state,
                {"recursion_limit": settings.max_iterations * 3},
            ):
                # Update our current reference to the state object
                node_name = list(output.keys())[0]
                node_output = output[node_name]
                
                # LangGraph converts BaseModel to dict in stream output
                if isinstance(node_output, dict):
                    state = ResearchState(**node_output)
                else:
                    state = node_output

                # Check timeout
                elapsed = perf_counter() - started
                if elapsed > settings.timeout_seconds:
                    logger.warning("Workflow timeout after %.1fs", elapsed)
                    state.errors.append(
                        f"Workflow timeout after {elapsed:.1f}s"
                    )
                    state.add_trace_event("workflow", {
                        "event": "timeout",
                        "elapsed": elapsed,
                    })
                    break
        except GraphRecursionError:
            # Handled internally by SupervisorAgent guardrails usually,
            # but if it escapes, we catch it here.
            error_msg = "GraphRecursionError: Max iterations exceeded"
            logger.error(error_msg)
            state.errors.append(error_msg)
            state.add_trace_event("error", {"error": error_msg})
        except Exception as exc:
            error_msg = f"Workflow failed: {exc}"
            logger.error(error_msg, exc_info=True)
            state.errors.append(error_msg)
            state.add_trace_event("error", {"error": str(exc)})

        total_time = perf_counter() - started
        state.add_trace_event("workflow", {
            "event": "complete",
            "total_seconds": total_time,
        })
        logger.info(
            "=== Multi-Agent Workflow END (%.2fs) ===", total_time,
        )

        return state
