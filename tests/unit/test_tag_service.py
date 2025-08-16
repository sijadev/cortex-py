import pytest
from cortex_neo.services.tag_service import TagService

class DummyTagRepository:
    def __init__(self):
        self.tags = {}
    def add_tag(self, note_name, tag_name):
        self.tags.setdefault(tag_name, {'name': tag_name, 'notes': []})
        self.tags[tag_name]['notes'].append(note_name)
    def list_tags_with_usage(self):
        return [ {'name': tag, 'usage_count': len(data['notes'])} for tag, data in self.tags.items() ]
    def get_tag_details(self, tag_name):
        if tag_name in self.tags:
            return {'tag': {'name': tag_name}, 'notes': self.tags[tag_name]['notes'], 'usage_count': len(self.tags[tag_name]['notes'])}
        return None

@pytest.fixture
def repo():
    return DummyTagRepository()

@pytest.fixture
def service(repo):
    return TagService(repo)

def test_add_and_list_tags(service):
    service.add('Note1', 'TagA')
    service.add('Note2', 'TagB')
    tags = service.list_with_usage()
    assert any(tag['name'] == 'TagA' for tag in tags)
    assert any(tag['name'] == 'TagB' for tag in tags)

def test_get_tag_details(service):
    service.add('Note1', 'TagA')
    tags = service.list_with_usage()
    tag_name = tags[0]['name']
    tag = service.get_details(tag_name)
    assert tag is not None
    assert tag['tag']['name'] == tag_name
