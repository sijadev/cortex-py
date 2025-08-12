"""
Storage Provider Abstraction

Decouples core logic from a specific data container (e.g., Obsidian vault).
Default implementation operates on a plain Markdown filesystem rooted at the
workspace path.
"""
from __future__ import annotations

from pathlib import Path
from typing import List


class StorageProvider:
    """Abstract storage provider contract."""

    def __init__(self, root_path: Path):
        self._root = Path(root_path).resolve()

    @property
    def root_path(self) -> Path:
        return self._root

    def list_files(self, pattern: str) -> List[Path]:
        # pragma: no cover - interface
        raise NotImplementedError

    def read_text(self, path: Path) -> str:
        # pragma: no cover - interface
        raise NotImplementedError

    def write_text(self, path: Path, content: str) -> None:
        # pragma: no cover - interface
        raise NotImplementedError


class MarkdownFSProvider(StorageProvider):
    """Filesystem-based provider for Markdown workspaces.

    - Patterns are resolved relative to the root path.
    - Reads/writes use UTF-8 encoding.
    """

    def list_files(self, pattern: str) -> List[Path]:
        if pattern.startswith("/"):
            return list(Path(pattern).glob("*"))
        return list(self.root_path.glob(pattern))

    def read_text(self, path: Path) -> str:
        p = path if path.is_absolute() else (self.root_path / path)
        return Path(p).read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        p = path if path.is_absolute() else (self.root_path / path)
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(content, encoding="utf-8")
