"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown with analysis."""

    lines = [
        "# Benchmark Report",
        "",
        "**Student**: Nguyễn Hoàng Long (2A202600160)",
        "",
        "## Summary Table",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = (
            ""
            if item.estimated_cost_usd is None
            else f"${item.estimated_cost_usd:.6f}"
        )
        quality = (
            ""
            if item.quality_score is None
            else f"{item.quality_score:.1f}"
        )
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} "
            f"| {cost} | {quality} | {item.notes} |"
        )

    lines.append("")

    # Add comparison analysis
    if len(metrics) >= 2:
        baseline = metrics[0]
        multi = metrics[1]

        ratio = multi.latency_seconds / baseline.latency_seconds
        direction = (
            "slower"
            if multi.latency_seconds > baseline.latency_seconds
            else "faster"
        )

        lines.extend([
            "## Analysis",
            "",
            f"- **Latency ratio**: Multi-agent is "
            f"{ratio:.1f}x {direction} than baseline",
        ])

        if baseline.estimated_cost_usd and multi.estimated_cost_usd:
            cost_r = multi.estimated_cost_usd / baseline.estimated_cost_usd
            lines.append(
                f"- **Cost ratio**: Multi-agent costs "
                f"{cost_r:.1f}x the baseline"
            )

        lines.extend([
            "- **Trade-off**: Multi-agent provides structured "
            "research with sources and analysis at the cost of "
            "higher latency and token usage",
            "",
        ])

    return "\n".join(lines) + "\n"
