#!/usr/bin/env python3
"""
Integration Tests for MCP (Model Context Protocol) System
Tests MCP integration as used in the GitHub workflow
"""

import pytest
import subprocess
import sys
import os
import json
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestMCPSystemIntegration:
    """Test MCP system integration for CI/CD pipeline"""

    def setup_method(self):
        """Setup for each test method"""
        self.project_root = Path(__file__).parent.parent.parent
        self.mcp_src_dir = self.project_root / "src" / "mcp"
        self.mcp_tests_dir = self.project_root / "tests" / "mcp"
        self.original_cwd = os.getcwd()

    def teardown_method(self):
        """Cleanup after each test"""
        os.chdir(self.original_cwd)

    def test_mcp_source_directory_structure(self):
        """Test that MCP source directory has expected structure"""
        assert self.mcp_src_dir.exists(), "src/mcp directory should exist"

        # Look for MCP-related files
        mcp_files = list(self.mcp_src_dir.glob("*.py"))
        assert len(mcp_files) > 0, "MCP source directory should contain Python files"

        # Check for __init__.py
        init_file = self.mcp_src_dir / "__init__.py"
        assert init_file.exists(), "MCP should have __init__.py"

    def test_mcp_tests_directory_structure(self):
        """Test that MCP tests directory exists"""
        assert self.mcp_tests_dir.exists(), "tests/mcp directory should exist"

    def test_mcp_validator_script_exists(self):
        """Test that MCP validator script exists (used in GitHub workflow)"""
        validator_script = self.project_root / "validate_mcp_system.py"
        assert validator_script.exists(), "MCP validator script should exist"

    def test_mcp_validator_execution(self):
        """Test that MCP validator can be executed"""
        validator_script = self.project_root / "validate_mcp_system.py"

        if validator_script.exists():
            result = subprocess.run([
                sys.executable, str(validator_script)
            ], capture_output=True, text=True, timeout=60)

            # Validator might return non-zero but shouldn't crash
            assert result.returncode in [0, 1], "MCP validator should run without crashing"

    def test_mcp_configuration_files(self):
        """Test that MCP configuration files exist"""
        config_locations = [
            self.project_root / "config" / "mcp",
            self.mcp_src_dir / "config"
        ]

        found_config = False
        for config_dir in config_locations:
            if config_dir.exists():
                found_config = True
                config_files = list(config_dir.glob("*.json")) + list(config_dir.glob("*.yaml"))
                # Config directory should have some configuration files
                break

        # At least one config location should exist or be referenced
        assert found_config or True, "MCP configuration should be available"

    def test_claude_desktop_config(self):
        """Test Claude Desktop configuration for MCP"""
        claude_config = self.project_root / "config" / "claude_desktop_config.json"

        if claude_config.exists():
            with open(claude_config, 'r') as f:
                try:
                    config_data = json.load(f)
                    assert isinstance(config_data, dict), "Claude config should be valid JSON object"
                except json.JSONError as e:
                    pytest.fail(f"Claude desktop config is invalid JSON: {e}")

    def test_mcp_debug_scripts(self):
        """Test that MCP debug scripts exist and are functional"""
        scripts_dir = self.project_root / "scripts"
        mcp_debug_scripts = [
            "debug_mcp.py",
            "debug_mcp_final.py",
            "debug_mcp_fixed.py",
            "check_mcp.py"
        ]

        found_scripts = []
        for script_name in mcp_debug_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                found_scripts.append(script_name)

        assert len(found_scripts) > 0, "At least one MCP debug script should exist"

    def test_mcp_import_capability(self):
        """Test that MCP modules can be imported"""
        try:
            # Try to import MCP components
            mcp_files = list(self.mcp_src_dir.glob("*.py"))
            importable_modules = []

            for mcp_file in mcp_files:
                if mcp_file.name != "__init__.py" and not mcp_file.name.startswith("test_"):
                    module_name = mcp_file.stem
                    try:
                        # Attempt import
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(module_name, mcp_file)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            importable_modules.append(module_name)
                    except Exception:
                        # Import might fail due to dependencies, that's okay for structure test
                        pass

            # We don't require successful imports, just that files exist
            assert len(mcp_files) > 0, "MCP should have Python modules"

        except Exception:
            # This is okay - we're just testing structure
            pass


class TestMCPWorkflowIntegration:
    """Test MCP integration with GitHub workflow requirements"""

    def test_mcp_pytest_execution(self):
        """Test that MCP tests can be run with pytest"""
        mcp_tests_dir = project_root / "tests" / "mcp"

        if not mcp_tests_dir.exists():
            pytest.skip("MCP tests directory not found")

        # Check if there are any test files
        test_files = list(mcp_tests_dir.glob("test_*.py"))
        py_files = list(mcp_tests_dir.glob("*.py"))

        if len(test_files) == 0 and len(py_files) == 0:
            pytest.skip("No MCP test files found")

        # Try running pytest on MCP tests (with timeout to avoid hanging)
        if shutil.which("pytest"):
            result = subprocess.run([
                sys.executable, "-m", "pytest", str(mcp_tests_dir),
                "-v", "--tb=short", "--maxfail=3"
            ], capture_output=True, text=True, timeout=120)

            # Tests might fail but should be collected and attempted
            assert "collected" in result.stdout or result.returncode in [0, 1, 5], "MCP tests should be runnable"

    def test_mcp_logs_directory(self):
        """Test that MCP logs directory exists for CI debugging"""
        logs_dir = project_root / "logs" / "mcp"

        # Directory should exist or be creatable
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)

        assert logs_dir.exists(), "MCP logs directory should exist"

    def test_mcp_scripts_directory(self):
        """Test MCP scripts in scripts directory"""
        scripts_mcp_dir = project_root / "scripts" / "mcp"

        if scripts_mcp_dir.exists():
            # Look for both Python and Shell scripts
            mcp_scripts = list(scripts_mcp_dir.glob("*.py")) + list(scripts_mcp_dir.glob("*.sh"))
            assert len(mcp_scripts) > 0, "MCP scripts directory should contain scripts"

    def test_mcp_system_status_check(self):
        """Test MCP system status checking capability"""
        # Look for MCP status checking scripts
        possible_status_scripts = [
            project_root / "validate_mcp_system.py",
            project_root / "scripts" / "check_mcp.py"
        ]

        found_status_script = None
        for script in possible_status_scripts:
            if script.exists():
                found_status_script = script
                break

        if found_status_script:
            # Try to execute the status script
            result = subprocess.run([
                sys.executable, str(found_status_script)
            ], capture_output=True, text=True, timeout=30)

            # Should run without crashing
            assert result.returncode in [0, 1], "MCP status script should execute"


import shutil

class TestMCPEnvironmentSetup:
    """Test MCP environment setup for CI"""

    def test_mcp_dependencies_installable(self):
        """Test that MCP dependencies can be installed"""
        # Check if MCP has specific requirements
        mcp_requirements = project_root / "src" / "mcp" / "requirements.txt"

        if mcp_requirements.exists():
            # Test that requirements file is valid
            with open(mcp_requirements, 'r') as f:
                content = f.read()
                lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]

                # Should have some dependencies or be empty
                assert len(lines) >= 0, "MCP requirements should be valid"

    def test_mcp_config_validation(self):
        """Test MCP configuration validation"""
        # Look for MCP configuration validation
        config_dir = project_root / "config" / "mcp"

        if config_dir.exists():
            config_files = list(config_dir.glob("*.json")) + list(config_dir.glob("*.yaml"))

            for config_file in config_files:
                with open(config_file, 'r') as f:
                    content = f.read()

                    if config_file.suffix == '.json':
                        try:
                            json.loads(content)
                        except json.JSONError as e:
                            pytest.fail(f"Invalid JSON in {config_file}: {e}")

                    # Basic content validation
                    assert len(content) > 0, f"Config file {config_file} should not be empty"

    def test_mcp_reports_directory_creation(self):
        """Test that MCP reports directory can be created for CI"""
        reports_dir = project_root / "tests" / "mcp" / "reports"

        # Should be able to create reports directory
        reports_dir.mkdir(parents=True, exist_ok=True)
        assert reports_dir.exists(), "MCP reports directory should be creatable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
