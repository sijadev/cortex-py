from typing import Any, Dict, List, Optional

class NoteRepository:
    def __init__(self):
        self._notes = {}
        self._next_id = 1

    def add_note(self, note_data: Dict[str, Any]) -> None:
        note_id = str(self._next_id)
        self._next_id += 1
        note_data['id'] = note_id
        self._notes[note_id] = note_data

    def list_notes(self) -> List[Dict[str, Any]]:
        return list(self._notes.values())

    def get_note_details(self, note_id: str) -> Optional[Dict[str, Any]]:
        return self._notes.get(note_id)

    def delete_note(self, note_id: str) -> None:
        if note_id in self._notes:
            del self._notes[note_id]

