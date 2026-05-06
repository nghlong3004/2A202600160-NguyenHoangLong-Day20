"""Tracing hooks.

Provides both a minimal span context manager and a TraceCollector that
accumulates all spans and can export them to JSON for analysis.
"""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

logger = logging.getLogger(__name__)


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the skeleton."""

    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
    }
    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started


class TraceCollector:
    """Collects trace events and exports them to JSON."""

    def __init__(self) -> None:
        self.spans: list[dict[str, Any]] = []
        self._start_time = perf_counter()

    def add_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.spans.append({
            "name": name,
            "attributes": attributes or {},
            "timestamp_offset": perf_counter() - self._start_time,
        })

    def export_json(
        self, output_dir: Path = Path("reports"),
    ) -> Path:
        """Export collected spans to a JSON file."""

        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"trace_{timestamp}.json"

        data = {
            "total_spans": len(self.spans),
            "export_time": datetime.now(tz=UTC).isoformat(),
            "spans": self.spans,
        }
        path.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Trace exported to %s", path)
        return path
