from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Set

from app.codex.driver import CodexEvent


@dataclass
class MetricsAccumulator:
    """Accumulate orchestration metrics from streamed Codex events.

    Attributes:
        event_counts: Mapping of event type to total occurrences.
        files_touched: Set of file paths referenced by events.
        error_count: Total number of error events observed.
    """

    event_counts: Dict[str, int] = field(default_factory=dict)
    files_touched: Set[str] = field(default_factory=set)
    error_count: int = 0

    def record_event(self, event: CodexEvent) -> None:
        """Record a Codex event into the metrics accumulator.

        Args:
            event: Structured Codex event emitted by a driver.
        """
        event_type = event.get("type", "unknown")
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1

        if event_type == "error":
            self.error_count += 1

        for path in self._extract_paths(event):
            self.files_touched.add(path)

    def summarize(self) -> Dict[str, Any]:
        """Return a snapshot of the collected metrics.

        Returns:
            Dictionary containing event counts, file list, and error totals.
        """
        return {
            "event_counts": dict(self.event_counts),
            "files_touched": sorted(self.files_touched),
            "error_count": self.error_count,
        }

    def _extract_paths(self, event: CodexEvent) -> Iterable[str]:
        """Extract file paths referenced by an event.

        Args:
            event: Codex event that may contain file references.

        Returns:
            Iterable of file paths extracted from the event metadata.
        """
        meta = event.get("meta")
        if not isinstance(meta, dict):
            return []

        if "files" in meta:
            return self._normalize_paths(meta.get("files"))
        if "paths" in meta:
            return self._normalize_paths(meta.get("paths"))
        if "path" in meta:
            return self._normalize_paths(meta.get("path"))
        return []

    def _normalize_paths(self, raw_paths: Any) -> List[str]:
        """Normalize raw path values into a list of strings.

        Args:
            raw_paths: Value from an event metadata payload.

        Returns:
            List of normalized path strings.
        """
        if raw_paths is None:
            return []
        if isinstance(raw_paths, str):
            return [raw_paths]
        if isinstance(raw_paths, (list, tuple, set)):
            return [path for path in raw_paths if isinstance(path, str)]
        return []
