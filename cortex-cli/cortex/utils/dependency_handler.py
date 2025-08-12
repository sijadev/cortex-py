"""
Dependency Handler für Cortex CLI
Behandelt fehlende oder optionale Dependencies graceful
"""
import importlib
import sys
from typing import Any, Optional

class MissingDependencyError(ImportError):
    """Raised when a required dependency is missing"""
    pass

def safe_import(module_name: str, package: Optional[str] = None) -> Any:
    """
    Importiert ein Modul sicher und gibt eine aussagekräftige Fehlermeldung
    """
    try:
        return importlib.import_module(module_name, package)
    except ImportError as e:
        if 'aiohttp' in module_name:
            raise MissingDependencyError(
                f"aiohttp ist nicht installiert. Installiere es mit: pip install aiohttp"
            ) from e
        elif 'watchdog' in module_name:
            raise MissingDependencyError(
                f"watchdog ist nicht installiert. Installiere es mit: pip install watchdog"  
            ) from e
        else:
            raise MissingDependencyError(
                f"Dependency '{module_name}' ist nicht verfügbar: {e}"
            ) from e

def has_dependency(module_name: str) -> bool:
    """Prüft ob eine Dependency verfügbar ist"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

# Commonly needed dependencies
def get_aiohttp():
    """Get aiohttp with graceful error handling"""
    return safe_import('aiohttp')

def get_watchdog():
    """Get watchdog with graceful error handling"""  
    return safe_import('watchdog')
