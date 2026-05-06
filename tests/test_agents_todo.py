"""Tests for agent implementations."""

from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def _make_state(**kwargs: object) -> ResearchState:
    return ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        **kwargs,
    )


def test_supervisor_routes_to_researcher_first() -> None:
    """When state is fresh, supervisor should route to researcher."""
    state = _make_state()
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "researcher"


def test_supervisor_routes_to_analyst_after_research() -> None:
    """When research_notes exist, route to analyst."""
    state = _make_state(research_notes="Some research findings")
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "analyst"


def test_supervisor_routes_to_writer_after_analysis() -> None:
    """When analysis_notes exist, route to writer."""
    state = _make_state(
        research_notes="Notes", analysis_notes="Analysis",
    )
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "writer"


def test_supervisor_routes_done_when_complete() -> None:
    """When final_answer exists, route done."""
    state = _make_state(
        research_notes="N",
        analysis_notes="A",
        final_answer="Done",
    )
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "done"


def test_supervisor_enforces_max_iterations() -> None:
    """When max iterations reached, force done."""
    state = _make_state()
    state.iteration = 100  # exceed any max
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "done"
