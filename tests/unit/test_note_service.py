import pytest
from cortex_neo.repositories.note_repository import NoteRepository
from cortex_neo.services.note_service import NoteService

@pytest.fixture
def repo():
    return NoteRepository()

@pytest.fixture
def service(repo):
    return NoteService(repo)

def test_add_and_list_notes(service):
    service.add({'content': 'First note'})
    service.add({'content': 'Second note'})
    notes = service.list()
    assert len(notes) == 2
    assert notes[0]['content'] == 'First note'
    assert notes[1]['content'] == 'Second note'

def test_get_note_details(service):
    service.add({'content': 'Test note'})
    notes = service.list()
    note_id = notes[0]['id']
    note = service.get_details(note_id)
    assert note is not None
    assert note['content'] == 'Test note'

def test_delete_note(service):
    service.add({'content': 'To be deleted'})
    notes = service.list()
    note_id = notes[0]['id']
    service.delete(note_id)
    assert service.get_details(note_id) is None
    assert len(service.list()) == 0

def test_delete_nonexistent_note(service):
    # Should not raise error
    service.delete('999')
    assert service.list() == []

