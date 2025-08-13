"""
Global pytest configuration and fixtures for test isolation
"""
import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reset_environment():
    """
    Auto-reset fixture that runs before and after every test
    Ensures clean environment and proper isolation
    """
    # Before test: Store original state
    original_cwd = os.getcwd()
    original_env = os.environ.copy()
    original_sys_path = sys.path.copy()
    
    yield
    
    # After test: Reset everything
    os.chdir(original_cwd)
    os.environ.clear()
    os.environ.update(original_env)
    sys.path[:] = original_sys_path


@pytest.fixture(autouse=True) 
def clear_cli_state():
    """
    Clear any CLI state that might persist between tests
    """
    # Clear any global CLI state before test
    with patch.dict('sys.modules'):
        # Force reload of CLI modules to clear state
        cli_modules = [name for name in sys.modules.keys() if name.startswith('cortex.cli')]
        for module_name in cli_modules:
            if module_name in sys.modules:
                # Clear module-level state without removing the module
                module = sys.modules[module_name]
                if hasattr(module, '__dict__'):
                    # Reset any global variables that might store state
                    for attr_name in dir(module):
                        if not attr_name.startswith('_') and attr_name.isupper():
                            # Reset UPPERCASE global variables (constants/state)
                            continue
        
        yield
        
        # No cleanup needed - autouse fixture handles it


@pytest.fixture(autouse=True)
def temp_workspace_isolation():
    """
    Ensure each test gets a fresh temporary workspace
    """
    # Create fresh temp directory for each test
    temp_dir = tempfile.mkdtemp(prefix="cortex_test_")
    original_cwd = os.getcwd()
    
    try:
        # Change to temp directory for test isolation
        os.chdir(temp_dir)
        yield Path(temp_dir)
    finally:
        # Cleanup: return to original directory and remove temp
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def mock_find_cortex_root():
    """
    Mock cortex root finding to prevent tests from interfering with real workspace
    """
    with patch('cortex.cli.main.find_cortex_root') as mock_find:
        # Return a temp directory as cortex root for each test
        temp_dir = tempfile.mkdtemp(prefix="cortex_root_")
        mock_find.return_value = temp_dir
        
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
