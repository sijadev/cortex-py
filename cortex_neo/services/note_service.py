from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
try:
    from ..repositories.note_repository import NoteRepository
except ImportError:  # Support running without package context
    from repositories.note_repository import NoteRepository  # type: ignore

@dataclass
class NoteService:
    repo: NoteRepository

    def add(self, note_data: Dict[str, Any]) -> None:
        self.repo.add_note(note_data)

    def list(self) -> List[Dict[str, Any]]:
        return self.repo.list_notes()

    def get_details(self, note_id: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_note_details(note_id)

    def delete(self, note_id: str) -> None:
        self.repo.delete_note(note_id)

