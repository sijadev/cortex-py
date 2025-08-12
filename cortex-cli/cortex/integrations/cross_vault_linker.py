#!/usr/bin/env python3
"""
Cross-Vault Linker - Intelligent linking system for multi-vault Cortex.
Converts tag correlations into actionable cross-vault links and suggestions.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from ..core.storage_provider import StorageProvider, MarkdownFSProvider
except Exception:  # pragma: no cover - fallback for direct execution
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.storage_provider import (
        StorageProvider,
        MarkdownFSProvider,
    )  # type: ignore


@dataclass
class LinkSuggestion:
    """Represents a suggested link between vaults."""

    source_vault: str
    source_file: str
    target_vault: str
    target_file: str
    correlation_score: float
    shared_tags: List[str]
    confidence: float
    reason: str
    link_type: str  # 'strong', 'medium', 'weak'
    created_date: str
    semantic_relevance: float = 0.0
    content_overlap: float = 0.0
    is_actionable: bool = False
    # values: reference|related|dependency|example
    link_purpose: str = "related"


@dataclass
class VaultConnection:
    """Represents a connection between two vaults."""

    vault1: str
    vault2: str
    connection_strength: float
    shared_tags: List[str]
    common_files: int
    last_updated: str


@dataclass
class LinkingReport:
    """Comprehensive linking report."""

    timestamp: str
    total_suggestions: int
    strong_links: int
    medium_links: int
    weak_links: int
    vault_connections: int
    actionable_links: int
    links_created: int
    execution_time: float
    top_suggestions: List[LinkSuggestion]
    vault_stats: Dict[str, Any]


class CrossVaultLinker:
    """Cortex Cross-Vault Linking Engine.

    Finds and summarizes connections between files across different Obsidian
    vaults based on tag overlap. This integration version is intentionally
    lightweight and uses the StorageProvider for IO.
    """

    def __init__(
        self,
        hub_vault_path: Optional[str] = None,
        storage_provider: Optional[StorageProvider] = None,
    ) -> None:
        default_hub = "/Users/simonjanke/Projects/cortex"
        self.hub_path = Path(hub_vault_path or default_hub)
        self.linker_path = self.hub_path / "00-System" / "Cross-Vault-Linker"
        self.data_path = self.linker_path / "data"
        self.cache_path = self.linker_path / "cache"
        self.logs_path = self.linker_path / "logs"

        # Storage provider (rooted at parent to allow multi-vault traversal)
        self.storage: StorageProvider = storage_provider or MarkdownFSProvider(
            self.hub_path.parent
        )

        for path in (self.data_path, self.cache_path, self.logs_path):
            path.mkdir(parents=True, exist_ok=True)

        self._setup_logging()

    def _setup_logging(self) -> None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_path / f"cross_vault_linker_{ts}.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("CrossVaultLinker initialized at %s", self.hub_path)

    # ---------- helpers ----------

    def _read_file_safe(self, file_path: Path) -> str:
        try:
            return self.storage.read_text(file_path)
        except (OSError, UnicodeDecodeError) as e:
            self.logger.debug("Read error %s: %s", file_path, e)
            return ""

    def _iter_md_files_in_vault(self, vault_path: Path):
        # Use a provider rooted at the vault to enumerate files
        try:
            vp = MarkdownFSProvider(vault_path)
            for p in vp.list_files("**/*.md"):
                if (
                    "00-System" not in str(p)
                    and ".obsidian" not in str(p)
                    and not p.name.startswith(".")
                ):
                    yield p
        except OSError as e:  # pragma: no cover
            self.logger.debug("List error %s: %s", vault_path, e)

    # ---------- discovery ----------

    def discover_vaults(self) -> List[Path]:
        vaults: List[Path] = []
        parent_provider = MarkdownFSProvider(self.hub_path.parent)
        for item in parent_provider.list_files("*"):
            if item.is_dir() and not item.name.startswith("."):
                vp = MarkdownFSProvider(item)
                if any(vp.list_files("*.md")):
                    vaults.append(item)
                    self.logger.debug("Discovered vault: %s", item)
        return vaults

    # ---------- extraction ----------

    def extract_file_tags(self, file_path: Path) -> Set[str]:
        content = self._read_file_safe(file_path)
        if not content:
            return set()
        tags = set(re.findall(r"#([A-Za-z0-9_\-]+)", content))
        # YAML frontmatter tags: tags: [a, b]
        for block in re.findall(r"tags:\s*\[(.*?)\]", content, re.IGNORECASE):
            parts = (
                t.strip().strip("'\"") for t in block.split(",") if t.strip()
            )
            tags.update(parts)
        return tags

    # ---------- analysis ----------

    def calculate_file_similarity(
        self, file1_tags: Set[str], file2_tags: Set[str]
    ) -> float:
        if not file1_tags or not file2_tags:
            return 0.0
        shared = file1_tags & file2_tags
        total = file1_tags | file2_tags
        return len(shared) / len(total) if total else 0.0

    def find_cross_vault_links(
        self, min_similarity: float = 0.3
    ) -> List[LinkSuggestion]:
        self.logger.info(
            "Discovering links with min_similarity=%.2f", min_similarity
        )
        start = datetime.now()

        vaults = self.discover_vaults()
        vault_files: Dict[str, Dict[Path, Set[str]]] = {}
        for vault in vaults:
            files: Dict[Path, Set[str]] = {}
            for md in self._iter_md_files_in_vault(vault):
                tags = self.extract_file_tags(md)
                if tags:
                    files[md] = tags
            vault_files[vault.name] = files

        suggestions: List[LinkSuggestion] = []
        names = list(vault_files.keys())
        for i, v1 in enumerate(names):
            for v2 in names[i + 1:]:
                for file1, tags1 in vault_files[v1].items():
                    for file2, tags2 in vault_files[v2].items():
                        sim = self.calculate_file_similarity(tags1, tags2)
                        if sim < min_similarity:
                            continue
                        shared = sorted((tags1 & tags2))
                        conf = min(sim * 1.5, 1.0)
                        if sim >= 0.7:
                            lt = "strong"
                        elif sim >= 0.5:
                            lt = "medium"
                        else:
                            lt = "weak"
                        reason_str = (
                            "Shared tags: "
                            + ", ".join(f"#{t}" for t in shared[:3])
                        )
                        suggestions.append(
                            LinkSuggestion(
                                source_vault=v1,
                                source_file=file1.name,
                                target_vault=v2,
                                target_file=file2.name,
                                correlation_score=sim,
                                shared_tags=shared,
                                confidence=conf,
                                reason=reason_str,
                                link_type=lt,
                                created_date=datetime.now().isoformat(),
                                is_actionable=sim >= 0.5,
                            )
                        )

        suggestions.sort(key=lambda s: s.correlation_score, reverse=True)
        elapsed = (datetime.now() - start).total_seconds()
        self.logger.info(
            "Found %d suggestions in %.2fs",
            len(suggestions),
            elapsed,
        )
        return suggestions

    def generate_vault_connections(self) -> List[VaultConnection]:
        self.logger.info("Aggregating vault connections ...")
        vaults = self.discover_vaults()

        tag_usage: Dict[str, Dict[str, int]] = {}
        file_counts: Dict[str, int] = {}
        for v in vaults:
            counts: Dict[str, int] = defaultdict(int)
            total = 0
            for md in self._iter_md_files_in_vault(v):
                total += 1
                for t in self.extract_file_tags(md):
                    counts[t] += 1
            tag_usage[v.name] = dict(counts)
            file_counts[v.name] = total

        conns: List[VaultConnection] = []
        names = list(tag_usage.keys())
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                t1 = set(tag_usage[a].keys())
                t2 = set(tag_usage[b].keys())
                shared = t1 & t2
                if not shared:
                    continue
                common_files = sum(
                    min(
                        tag_usage[a].get(t, 0),
                        tag_usage[b].get(t, 0),
                    )
                    for t in shared
                )
                avg_size = max((file_counts[a] + file_counts[b]) / 2, 1)
                strength = common_files / avg_size
                if strength <= 0.1:
                    continue
                conns.append(
                    VaultConnection(
                        vault1=a,
                        vault2=b,
                        connection_strength=round(strength, 3),
                        shared_tags=sorted(shared)[:20],
                        common_files=common_files,
                        last_updated=datetime.now().isoformat(),
                    )
                )

        conns.sort(key=lambda c: c.connection_strength, reverse=True)
        self.logger.info("Generated %d connections", len(conns))
        return conns

    # ---------- report ----------

    def run_full_analysis(self, min_similarity: float = 0.3) -> LinkingReport:
        start = datetime.now()
        suggestions = self.find_cross_vault_links(min_similarity)
        connections = self.generate_vault_connections()
        elapsed = (datetime.now() - start).total_seconds()

        strong = len([s for s in suggestions if s.link_type == "strong"])
        medium = len([s for s in suggestions if s.link_type == "medium"])
        weak = len([s for s in suggestions if s.link_type == "weak"])
        actionable = len([s for s in suggestions if s.is_actionable])

        stats: Dict[str, Any] = {}
        for v in self.discover_vaults():
            files = list(self._iter_md_files_in_vault(v))
            uniq_tags: Set[str] = set()
            for f in files:
                uniq_tags.update(self.extract_file_tags(f))
            stats[v.name] = {
                "files": len(files),
                "unique_tags": len(uniq_tags),
                "path": str(v),
            }

        return LinkingReport(
            timestamp=datetime.now().isoformat(),
            total_suggestions=len(suggestions),
            strong_links=strong,
            medium_links=medium,
            weak_links=weak,
            vault_connections=len(connections),
            actionable_links=actionable,
            links_created=0,
            execution_time=elapsed,
            top_suggestions=suggestions[:10],
            vault_stats=stats,
        )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Cross-Vault Linker for Cortex"
    )
    parser.add_argument("--hub-path", help="Path to the hub vault")
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.3,
        help="Minimum similarity threshold",
    )
    parser.add_argument("--output", help="Optional output file (JSON)")

    args = parser.parse_args()

    linker = CrossVaultLinker(args.hub_path)
    report = linker.run_full_analysis(args.min_similarity)

    print("\n=== Cross-Vault Linking Report ===")
    print(f"Total Suggestions: {report.total_suggestions}")
    print(f"Strong Links: {report.strong_links}")
    print(f"Medium Links: {report.medium_links}")
    print(f"Weak Links: {report.weak_links}")
    print(f"Actionable Links: {report.actionable_links}")
    print(f"Vault Connections: {report.vault_connections}")
    print(f"Execution Time: {report.execution_time:.2f}s")

    if args.output:
        out = Path(args.output)
        out.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        print(f"Saved report to {out}")


if __name__ == "__main__":  # pragma: no cover
    main()
