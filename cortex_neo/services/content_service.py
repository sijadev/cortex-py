from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
try:
    from ..repositories.content_repository import ContentRepository
except ImportError:  # Support running without package context
    from repositories.content_repository import ContentRepository  # type: ignore


@dataclass
class ContentService:
    repo: ContentRepository

    def create_note(self, name: str, content: str, description: str, note_type: str, smart: bool, auto_tags: List[str] | None = None) -> None:
        self.repo.create_note(name, content or "", description or "", note_type or "", smart)
        for tag in auto_tags or []:
            self.repo.add_tag(name, tag)

    def search(self, query: str) -> List[Dict[str, Any]]:
        return self.repo.search(query)

    def get_detail(self, name: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_note_detail(name)

    def list_with_tag_count(self) -> List[Dict[str, Any]]:
        return self.repo.list_notes_with_tag_count()
