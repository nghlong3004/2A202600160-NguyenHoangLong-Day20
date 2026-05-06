"""Command-line entrypoint for the lab."""

import json
import logging
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import TraceCollector
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(
    help="Multi-Agent Research Lab CLI — Nguyen Hoang Long",
)
console = Console()
logger = logging.getLogger(__name__)


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _run_baseline(query: str) -> ResearchState:
    """Single-agent baseline: one LLM call does everything."""

    llm = LLMClient(temperature=0.3)
    system_prompt = (
        "You are a research assistant. Given a query, provide a "
        "comprehensive, well-structured response with clear "
        "reasoning. Aim for ~500 words."
    )
    response = llm.complete(system_prompt, query)

    state = ResearchState(request=ResearchQuery(query=query))
    state.final_answer = response.content
    state.add_trace_event("baseline", {
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "cost_usd": response.cost_usd,
    })
    return state


def _run_multi_agent(query: str) -> ResearchState:
    """Multi-agent: supervisor + researcher + analyst + writer."""

    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


@app.command()
def baseline(
    query: Annotated[
        str, typer.Option("--query", "-q", help="Research query")
    ],
) -> None:
    """Run the single-agent baseline."""

    _init()
    state = _run_baseline(query)
    console.print(
        Panel.fit(
            state.final_answer or "(empty)",
            title="Single-Agent Baseline",
        )
    )


@app.command("multi-agent")
def multi_agent(
    query: Annotated[
        str, typer.Option("--query", "-q", help="Research query")
    ],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = _run_multi_agent(query)
    console.print(
        Panel.fit(
            state.final_answer or "(empty)",
            title="Multi-Agent Result",
        )
    )

    # Show route history
    routes = " → ".join(state.route_history)
    console.print(f"\n[bold]Route history:[/bold] {routes}")

    # Show errors if any
    if state.errors:
        console.print(f"\n[red]Errors:[/red] {state.errors}")

    # Export trace
    collector = TraceCollector()
    for event in state.trace:
        collector.add_span(event["name"], event.get("payload"))
    trace_path = collector.export_json()
    console.print(f"\n[dim]Trace: {trace_path}[/dim]")


_DEFAULT_QUERY = (
    "Research GraphRAG state-of-the-art "
    "and write a 500-word summary"
)


@app.command()
def benchmark(
    query: Annotated[
        str,
        typer.Option("--query", "-q", help="Benchmark query"),
    ] = _DEFAULT_QUERY,
) -> None:
    """Benchmark single-agent vs multi-agent."""

    _init()
    console.print("[bold]Running benchmark...[/bold]\n")

    # Run baseline
    console.print("[cyan]1/2 Single-agent baseline...[/cyan]")
    baseline_state, baseline_metrics = run_benchmark(
        "single-agent-baseline", query, _run_baseline,
    )
    bl_len = len(baseline_state.final_answer or "")
    baseline_metrics.notes = f"answer_length={bl_len}"
    console.print(
        f"  [green]Done[/green] in {baseline_metrics.latency_seconds:.2f}s\n",
    )

    # Run multi-agent
    console.print("[cyan]2/2 Multi-agent workflow...[/cyan]")
    multi_state, multi_metrics = run_benchmark(
        "multi-agent-workflow", query, _run_multi_agent,
    )
    ml_len = len(multi_state.final_answer or "")
    routes = "→".join(multi_state.route_history)
    multi_metrics.notes = (
        f"answer_length={ml_len}, routes={routes}"
    )
    console.print(
        f"  [green]Done[/green] in {multi_metrics.latency_seconds:.2f}s\n",
    )

    # Compute costs from agent results + trace
    for st, mt in [
        (baseline_state, baseline_metrics),
        (multi_state, multi_metrics),
    ]:
        total_cost = sum(
            r.metadata.get("cost_usd", 0) or 0
            for r in st.agent_results
        )
        for event in st.trace:
            payload = event.get("payload", {})
            if payload.get("cost_usd"):
                total_cost += payload["cost_usd"]
        mt.estimated_cost_usd = (
            total_cost if total_cost > 0 else None
        )

    # Render report
    all_metrics = [baseline_metrics, multi_metrics]
    report_md = render_markdown_report(all_metrics)

    # Append detailed comparison
    report_md += "\n## Detailed Comparison\n\n"
    report_md += f"### Query\n\n> {query}\n\n"

    report_md += "### Single-Agent Baseline Output\n\n"
    report_md += f"{baseline_state.final_answer or '(empty)'}\n\n"

    report_md += "### Multi-Agent Output\n\n"
    report_md += f"{multi_state.final_answer or '(empty)'}\n\n"

    report_md += "### Route History\n\n"
    route_str = "  →  ".join(multi_state.route_history)
    report_md += f"`{route_str}`\n\n"

    report_md += "### Trace Events\n\n"
    trace_json = json.dumps(
        multi_state.trace, indent=2, default=str,
    )
    report_md += f"```json\n{trace_json}\n```\n\n"

    report_md += "### Failure Mode Analysis\n\n"
    if multi_state.errors:
        report_md += (
            f"Errors encountered: {multi_state.errors}\n\n"
        )
    else:
        report_md += "No errors encountered during this run.\n\n"

    report_md += (
        "**Known failure modes:**\n\n"
        "1. **Search timeout**: DuckDuckGo may rate-limit — "
        "fallback returns empty results.\n"
        "2. **LLM timeout**: DeepSeek API may be slow — "
        "tenacity retries up to 3 times.\n"
        "3. **Max iterations hit**: Supervisor enforces "
        "max_iterations guardrail.\n"
        "4. **Cost overrun**: Multi-agent uses 3-4x more "
        "tokens than baseline.\n\n"
        "**Fixes applied:**\n\n"
        "- Retry with exponential backoff for LLM calls\n"
        "- Graceful fallback for search failures\n"
        "- Per-agent error catching in workflow\n"
        "- Max iterations + timeout guardrails\n"
    )

    # Save report
    store = LocalArtifactStore()
    path = store.write_text("benchmark_report.md", report_md)
    console.print(f"[green]Report saved to: {path}[/green]\n")

    # Print summary table
    table = Table(title="Benchmark Results")
    table.add_column("Metric", style="bold")
    table.add_column("Single-Agent", justify="right")
    table.add_column("Multi-Agent", justify="right")

    table.add_row(
        "Latency (s)",
        f"{baseline_metrics.latency_seconds:.2f}",
        f"{multi_metrics.latency_seconds:.2f}",
    )

    bl_cost = baseline_metrics.estimated_cost_usd
    ml_cost = multi_metrics.estimated_cost_usd
    table.add_row(
        "Cost (USD)",
        f"${bl_cost:.6f}" if bl_cost else "N/A",
        f"${ml_cost:.6f}" if ml_cost else "N/A",
    )
    table.add_row(
        "Answer Length",
        str(len(baseline_state.final_answer or "")),
        str(len(multi_state.final_answer or "")),
    )
    table.add_row(
        "Sources",
        "0",
        str(len(multi_state.sources)),
    )
    table.add_row(
        "Errors",
        str(len(baseline_state.errors)),
        str(len(multi_state.errors)),
    )
    console.print(table)

    # Export trace
    collector = TraceCollector()
    for event in multi_state.trace:
        collector.add_span(event["name"], event.get("payload"))
    collector.export_json()


if __name__ == "__main__":
    app()
