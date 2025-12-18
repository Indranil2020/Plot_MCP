"""Simple in-memory metrics registry."""

from __future__ import annotations

from typing import Dict, List


class MetricsStore:
    """Track basic request metrics in memory."""

    def __init__(self) -> None:
        self.total_requests = 0
        self.path_counts: Dict[str, int] = {}
        self.latencies_ms: List[float] = []

    def record(self, path: str, latency_ms: float) -> None:
        self.total_requests += 1
        self.path_counts[path] = self.path_counts.get(path, 0) + 1
        self.latencies_ms.append(latency_ms)

    def snapshot(self) -> Dict[str, object]:
        if not self.latencies_ms:
            return {"total_requests": self.total_requests, "paths": self.path_counts, "avg_latency_ms": 0}
        avg_latency = sum(self.latencies_ms) / len(self.latencies_ms)
        return {
            "total_requests": self.total_requests,
            "paths": self.path_counts,
            "avg_latency_ms": round(avg_latency, 2),
        }
