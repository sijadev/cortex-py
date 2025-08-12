"""
Test Mocks für fehlende oder problematische Module
"""
from unittest.mock import Mock, MagicMock

# Mock für aiohttp wenn nicht verfügbar
try:
    import aiohttp
except ImportError:
    aiohttp = Mock()
    aiohttp.ClientSession = Mock
    aiohttp.web = Mock()

# Mock für watchdog wenn nicht verfügbar  
try:
    import watchdog
except ImportError:
    watchdog = Mock()
    watchdog.observers = Mock()
    watchdog.events = Mock()

class MockCrossVaultLinker:
    """Mock für CrossVaultLinker für Tests"""
    
    def __init__(self, *args, **kwargs):
        pass
    
    def validate_links(self):
        return {'valid': True, 'issues': []}
    
    def fix_invalid_links(self):
        return {'fixed': 0, 'errors': []}

class MockAIEngine:
    """Mock für AI Engine für Tests"""
    
    def __init__(self, *args, **kwargs):
        pass
        
    def generate_suggestion(self, context):
        return "Mock suggestion"
