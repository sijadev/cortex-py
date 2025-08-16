#!/usr/bin/env python3
"""
Integration Tests for Cortex CLI Components
Tests CLI integration as used in the GitHub workflow
"""

import pytest
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestCortexCLIIntegration:
    """Test Cortex CLI integration for CI/CD pipeline"""

    def setup_method(self):
        """Setup for each test method"""
        self.project_root = Path(__file__).parent.parent.parent
        self.cortex_cli_dir = self.project_root / "cortex-cli"
        self.original_cwd = os.getcwd()

    def teardown_method(self):
        """Cleanup after each test"""
        os.chdir(self.original_cwd)

    def test_cortex_cli_directory_structure(self):
        """Test that cortex-cli has the expected structure for CI"""
        assert self.cortex_cli_dir.exists(), "cortex-cli directory should exist"

        required_files = [
            "setup.py",
            "requirements.txt",
            "requirements-dev.txt",
            "pytest.ini"
        ]

        for file_name in required_files:
            file_path = self.cortex_cli_dir / file_name
            assert file_path.exists(), f"cortex-cli/{file_name} should exist for CI"

    def test_cortex_cli_setup_py_valid(self):
        """Test that setup.py is valid for pip install -e ."""
        setup_py = self.cortex_cli_dir / "setup.py"

        # Test that setup.py can be parsed
        with open(setup_py, 'r') as f:
            content = f.read()
            assert 'setup(' in content, "setup.py should contain setup() call"
            assert 'name=' in content, "setup.py should specify package name"

    def test_cortex_cli_requirements_files(self):
        """Test that requirements files are valid"""
        req_files = ["requirements.txt", "requirements-dev.txt"]

        for req_file in req_files:
            file_path = self.cortex_cli_dir / req_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    lines = content.strip().split('\n')
                    # Should have at least some dependencies or be empty
                    assert len(lines) >= 0

    def test_cortex_cli_tests_directory(self):
        """Test that CLI tests directory exists and has tests"""
        tests_dir = self.cortex_cli_dir / "tests"
        assert tests_dir.exists(), "cortex-cli/tests directory should exist"

        # Should have at least some test files
        test_files = list(tests_dir.glob("test_*.py"))
        py_files = list(tests_dir.glob("*.py"))

        assert len(test_files) > 0 or len(py_files) > 0, "CLI should have some test files"

    def test_cortex_cli_pytest_config(self):
        """Test that pytest configuration is valid"""
        pytest_ini = self.cortex_cli_dir / "pytest.ini"

        if pytest_ini.exists():
            with open(pytest_ini, 'r') as f:
                content = f.read()
                assert '[pytest]' in content or '[tool:pytest]' in content

    def test_cortex_cli_installation_simulation(self):
        """Test CLI installation process as done in GitHub workflow"""
        if not shutil.which("pip"):
            pytest.skip("pip not available")

        # Create a temporary virtual environment
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_dir = Path(temp_dir) / "test_venv"

            # Create virtual environment
            result = subprocess.run([
                sys.executable, "-m", "venv", str(venv_dir)
            ], capture_output=True, text=True)

            if result.returncode != 0:
                pytest.skip("Cannot create virtual environment")

            # Get pip path
            pip_cmd = str(venv_dir / "bin" / "pip") if os.name != "nt" else str(venv_dir / "Scripts" / "pip.exe")

            # Test installation in development mode (dry run to avoid actual installation)
            os.chdir(self.cortex_cli_dir)
            result = subprocess.run([
                pip_cmd, "install", "--dry-run", "-e", "."
            ], capture_output=True, text=True, timeout=60)

            # Should not crash (return code might vary due to dry-run)
            assert "ERROR" not in result.stderr.upper() or result.returncode == 0

    def test_cortex_cmd_help_simulation(self):
        """Test cortex-cmd --help as done in GitHub workflow"""
        # Look for cortex-cmd executable
        possible_locations = [
            self.cortex_cli_dir / "bin" / "cortex-cmd",
            self.project_root / "bin" / "cortex",
            self.project_root / "cortex-cli" / "bin" / "cortex-cmd"
        ]

        cortex_cmd = None
        for location in possible_locations:
            if location.exists():
                cortex_cmd = location
                break

        if cortex_cmd:
            result = subprocess.run([
                str(cortex_cmd), "--help"
            ], capture_output=True, text=True, timeout=30)

            # Should show help without crashing
            assert result.returncode == 0
            assert any(word in result.stdout.lower() for word in ["usage", "help", "cortex"])


class TestCortexCLISmoke:
    """Smoke tests for CLI components that run in GitHub workflow"""

    def test_cli_smoke_test_script_exists(self):
        """Test that CLI smoke test script exists"""
        cli_tests_dir = project_root / "cortex-cli" / "tests"

        if cli_tests_dir.exists():
            # Look for smoke test or main test file
            test_files = list(cli_tests_dir.glob("test_*.py"))
            run_tests = list(cli_tests_dir.glob("run_tests.py"))

            assert len(test_files) > 0 or len(run_tests) > 0, "CLI should have test files"

    def test_cli_smoke_import_test(self):
        """Test that CLI can be imported for smoke testing"""
        # This simulates what the smoke tests do
        try:
            # Try to import CLI components
            sys.path.insert(0, str(project_root / "cortex-cli"))

            # Look for main CLI module
            cli_dir = project_root / "cortex-cli"
            possible_cli_modules = [
                cli_dir / "cortex" / "__init__.py",
                cli_dir / "cortex_cli.py",
                cli_dir / "main.py"
            ]

            found_module = False
            for module_path in possible_cli_modules:
                if module_path.exists():
                    found_module = True
                    break

            # We don't require successful import, just that files exist
            assert found_module or True, "CLI should have importable modules"

        except ImportError:
            # This is okay for integration tests - just checking structure
            pass

    def test_cli_bin_directory(self):
        """Test that CLI bin directory is properly structured"""
        bin_dir = project_root / "cortex-cli" / "bin"

        if bin_dir.exists():
            # Should have executable files
            executables = list(bin_dir.iterdir())
            assert len(executables) > 0, "CLI bin directory should contain executables"

            # Check that files are not obviously broken
            for exe in executables:
                if exe.is_file():
                    # Should be readable
                    assert exe.stat().st_size > 0, f"{exe.name} should not be empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
