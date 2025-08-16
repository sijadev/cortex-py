from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
try:
    from ..repositories.tag_repository import TagRepository
except ImportError:  # Support running without package context
    from repositories.tag_repository import TagRepository  # type: ignore


@dataclass
class TagService:
    repo: TagRepository

    def add(self, note_name: str, tag_name: str) -> None:
        self.repo.add_tag(note_name, tag_name)

    def list_with_usage(self) -> List[Dict[str, Any]]:
        return self.repo.list_tags_with_usage()

    def get_details(self, tag_name: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_tag_details(tag_name)

    def create_performance(self) -> List[Dict[str, str]]:
        return self.repo.create_performance_tags()
