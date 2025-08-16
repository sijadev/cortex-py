import pytest
from cortex_neo.services.system_service import SystemService

class DummySystemRepo:
    def connection_ok(self):
        return True
    def server_time(self):
        return 1234567890
    def quick_stats(self):
        return {'notes': 5, 'links': 2, 'tags': 3, 'workflows': 1, 'templates': 0}
    def integrity(self):
        return {'total_notes': 5, 'tagged_notes': 3, 'linked_notes': 2}

@pytest.fixture
def repo():
    return DummySystemRepo()

@pytest.fixture
def service(repo):
    return SystemService(repo)

def test_connection_ok(service):
    assert service.connection_ok() is True

def test_get_server_time(service):
    assert service.get_server_time() == 1234567890

def test_get_quick_stats(service):
    stats = service.get_quick_stats()
    assert stats['notes'] == 5
    assert stats['links'] == 2
    assert stats['tags'] == 3

def test_status_overview(service):
    overview = service.status_overview()
    assert overview['health_score'] == min(100, (5*10 + 2*5 + 3*3))
    assert overview['health_status'] in ['🟢 Excellent', '🟡 Good', '🔴 Needs Content']
    assert overview['stats']['notes'] == 5

def test_health_check(service):
    hc = service.health_check()
    assert hc['tag_coverage'] == pytest.approx(60.0)
    assert hc['link_coverage'] == pytest.approx(40.0)
