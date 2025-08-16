from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
try:
    from ..repositories.protocols import SystemRepositoryProtocol
except ImportError:  # Support running without package context
    from repositories.protocols import SystemRepositoryProtocol  # type: ignore


@dataclass
class SystemService:
    repo: SystemRepositoryProtocol

    def connection_ok(self) -> bool:
        return self.repo.connection_ok()

    def get_server_time(self) -> int:
        return self.repo.server_time()

    def get_quick_stats(self) -> Dict[str, int]:
        return self.repo.quick_stats()

    def status_overview(self) -> Dict[str, Any]:
        time = self.get_server_time()
        stats = self.get_quick_stats()
        # Health heuristic copied from CLI
        health_score = min(100, (stats["notes"] * 10 + stats["links"] * 5 + stats["tags"] * 3))
        if health_score > 50:
            health_status = "🟢 Excellent"
        elif health_score > 20:
            health_status = "🟡 Good"
        else:
            health_status = "🔴 Needs Content"
        return {"time": time, "stats": stats, "health_score": health_score, "health_status": health_status}

    def health_check(self) -> Dict[str, Any]:
        integ = self.repo.integrity()
        total = max(integ["total_notes"], 1)
        tag_coverage = (integ["tagged_notes"] / total) * 100
        link_coverage = (integ["linked_notes"] / total) * 100
        return {"integrity": integ, "tag_coverage": tag_coverage, "link_coverage": link_coverage}
