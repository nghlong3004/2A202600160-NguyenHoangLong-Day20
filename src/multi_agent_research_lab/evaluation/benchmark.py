"""Benchmark skeleton for single-agent vs multi-agent."""

import logging
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import (
    BenchmarkMetrics,
    ResearchQuery,
)
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, estimate cost, and return metrics."""

    logger.info("Benchmark '%s' starting: %s", run_name, query[:80])
    started = perf_counter()

    try:
        state = runner(query)
        latency = perf_counter() - started
    except Exception as exc:
        latency = perf_counter() - started
        logger.error("Benchmark '%s' failed: %s", run_name, exc)
        state = ResearchState(request=ResearchQuery(query=query))
        state.errors.append(str(exc))

    # Aggregate cost from agent results
    total_cost = sum(
        r.metadata.get("cost_usd", 0) or 0
        for r in state.agent_results
    )

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=total_cost if total_cost > 0 else None,
        notes=f"errors={len(state.errors)}",
    )

    logger.info(
        "Benchmark '%s' done: latency=%.2fs, cost=$%s",
        run_name,
        latency,
        f"{total_cost:.6f}" if total_cost > 0 else "N/A",
    )
    return state, metrics
