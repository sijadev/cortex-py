import pytest
from cortex_neo.repositories.content_repository import ContentRepository
from cortex_neo.services.content_service import ContentService

class DummyContentRepository(ContentRepository):
    def __init__(self):
        self.notes = {}
        self.tags = {}
    def create_note(self, name, content, description, note_type, smart):
        self.notes[name] = {
            'name': name,
            'content': content,
            'description': description,
            'type': note_type,
            'smart': smart,
            'tags': []
        }
    def add_tag(self, name, tag):
        if name in self.notes:
            self.notes[name]['tags'].append(tag)
            self.tags.setdefault(tag, []).append(name)
    def search(self, query):
        return [ {'note': note} for note in self.notes.values() if query in note['name'] or query in note['content'] ]
    def get_note_detail(self, name):
        note = self.notes.get(name)
        if not note:
            return None
        return {'note': note, 'tags': note['tags'], 'outgoing': [], 'incoming': []}
    def list_notes_with_tag_count(self):
        return [ {'note': note, 'tag_count': len(note['tags'])} for note in self.notes.values() ]

@pytest.fixture
def repo():
    return DummyContentRepository()

@pytest.fixture
def service(repo):
    return ContentService(repo)

def test_create_note_and_get_detail(service):
    service.create_note('TestNote', 'Some content', 'A description', 'typeA', False)
    detail = service.get_detail('TestNote')
    assert detail is not None
    assert detail['note']['name'] == 'TestNote'
    assert detail['note']['content'] == 'Some content'
    assert detail['note']['description'] == 'A description'
    assert detail['note']['type'] == 'typeA'

def test_create_note_with_tags(service):
    service.create_note('TaggedNote', 'Content', '', '', False, auto_tags=['tag1', 'tag2'])
    detail = service.get_detail('TaggedNote')
    assert set(detail['tags']) == {'tag1', 'tag2'}

def test_search_notes(service):
    service.create_note('Alpha', 'foo', '', '', False)
    service.create_note('Beta', 'bar', '', '', False)
    results = service.search('foo')
    assert any(r['note']['name'] == 'Alpha' for r in results)
    assert all('foo' in r['note']['content'] or 'foo' in r['note']['name'] for r in results)

def test_list_notes_with_tag_count(service):
    service.create_note('Note1', 'A', '', '', False, auto_tags=['x'])
    service.create_note('Note2', 'B', '', '', False)
    notes = service.list_with_tag_count()
    for n in notes:
        if n['note']['name'] == 'Note1':
            assert n['tag_count'] == 1
        elif n['note']['name'] == 'Note2':
            assert n['tag_count'] == 0

