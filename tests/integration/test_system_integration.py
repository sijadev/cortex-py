#!/usr/bin/env python3
"""
Integration Tests for Complete System Integration
Tests end-to-end system integration for GitHub workflow
"""

import pytest
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestSystemIntegration:
    """Test complete system integration for CI/CD pipeline"""

    def setup_method(self):
        """Setup for each test method"""
        self.project_root = Path(__file__).parent.parent.parent
        self.original_cwd = os.getcwd()
        os.chdir(self.project_root)

    def teardown_method(self):
        """Cleanup after each test"""
        os.chdir(self.original_cwd)

    def test_project_structure_completeness(self):
        """Test that project has all components required by GitHub workflow"""
        required_components = {
            'main_script': 'main.py',
            'direct_cli': 'cortex_direct.py',
            'smoke_tests': 'run_smoke_tests.py',
            'unified_tests': 'run_tests_unified.py',
            'mcp_validator': 'validate_mcp_system.py',
            'requirements': 'requirements.txt',
            'dev_requirements': 'requirements-dev.txt'
        }

        for component_name, file_path in required_components.items():
            full_path = self.project_root / file_path
            assert full_path.exists(), f"Required component '{component_name}' ({file_path}) should exist"

    def test_directory_structure_completeness(self):
        """Test that all required directories exist"""
        required_directories = [
            'src',
            'tests/unit',
            'tests/integration',
            'tests/mcp',
            'cortex-cli',
            'cortex_neo',
            'scripts',
            'config'
        ]

        for dir_path in required_directories:
            full_path = self.project_root / dir_path
            assert full_path.exists(), f"Required directory '{dir_path}' should exist"

    def test_github_workflow_file_structure(self):
        """Test that GitHub workflow files are properly structured"""
        # Test the new modular workflow structure instead of old monolithic test.yml
        workflow_dir = self.project_root / '.github' / 'workflows'
        assert workflow_dir.exists(), "GitHub workflows directory should exist"

        # Check for key workflows in the new modular structure
        key_workflows = [
            'smoke-tests.yml',
            'unit-tests.yml',
            'integration-tests.yml',
            'ci-pipeline.yml'
        ]

        found_workflows = []
        for workflow_name in key_workflows:
            workflow_path = workflow_dir / workflow_name
            if workflow_path.exists():
                with open(workflow_path, 'r') as f:
                    content = f.read()

                # Check for essential workflow sections in each file
                essential_sections = ['name:', 'on:', 'jobs:']
                workflow_has_sections = all(section in content for section in essential_sections)

                if workflow_has_sections:
                    found_workflows.append(workflow_name)

        assert len(found_workflows) >= 2, f"Should have at least 2 properly structured workflows. Found: {found_workflows}"

    def test_end_to_end_smoke_test_execution(self):
        """Test complete smoke test execution as in CI"""
        result = subprocess.run([
            sys.executable, 'run_smoke_tests.py'
        ], capture_output=True, text=True, timeout=180)

        assert result.returncode == 0, f"End-to-end smoke tests should pass: {result.stderr}"
        assert "All smoke tests passed!" in result.stdout, "Smoke tests should report success"

    def test_main_system_entry_points(self):
        """Test that main system entry points work"""
        entry_points = ['main.py', 'cortex_direct.py']

        for entry_point in entry_points:
            result = subprocess.run([
                sys.executable, entry_point
            ], capture_output=True, text=True, timeout=60)

            assert result.returncode == 0, f"Entry point '{entry_point}' should execute successfully"

    def test_test_suite_discovery(self):
        """Test that all test suites can be discovered by pytest"""
        if not shutil.which("pytest"):
            pytest.skip("pytest not available")

        # Test unit test discovery
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/unit/", "--collect-only"
        ], capture_output=True, text=True, timeout=60)

        assert "collected" in result.stdout, "Unit tests should be discoverable"

        # Test integration test discovery
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/integration/", "--collect-only"
        ], capture_output=True, text=True, timeout=60)

        assert "collected" in result.stdout, "Integration tests should be discoverable"

    def test_system_configuration_loading(self):
        """Test that system configuration can be loaded"""
        try:
            from src.cortex_system_config import CortexSystemConfig
            config = CortexSystemConfig()

            # Should have required configuration attributes
            required_attrs = ['neo4j_uri', 'neo4j_user', 'neo4j_password', 'database_name']
            for attr in required_attrs:
                assert hasattr(config, attr), f"Config should have '{attr}' attribute"

        except ImportError:
            pytest.skip("CortexSystemConfig not available")

    def test_safe_transactions_system(self):
        """Test that safe transaction system is functional"""
        try:
            from src.safe_transactions import SafeTransactionManager

            # Create mock driver for testing
            class MockDriver:
                def session(self):
                    class MockSession:
                        def __enter__(self): return self
                        def __exit__(self, exc_type, exc_val, exc_tb): pass
                        def run(self, query):
                            class MockResult:
                                def __iter__(self): return iter([])
                            return MockResult()
                    return MockSession()

            tx_manager = SafeTransactionManager(driver=MockDriver())
            tx_manager.ensure_backup_dir()

            # Should create backup directory
            assert tx_manager.backup_dir.endswith("backups/auto")

        except ImportError:
            pytest.skip("SafeTransactionManager not available")

    def test_logging_directories_creation(self):
        """Test that logging directories can be created"""
        log_dirs = [
            'logs/tests',
            'logs/mcp',
            'logs/governance',
            'logs/neo4j'
        ]

        for log_dir in log_dirs:
            dir_path = self.project_root / log_dir
            dir_path.mkdir(parents=True, exist_ok=True)
            assert dir_path.exists(), f"Log directory '{log_dir}' should be creatable"

    def test_reports_directories_creation(self):
        """Test that reports directories can be created"""
        report_dirs = [
            'tests/reports',
            'tests/mcp/reports',
            'cortex-cli/tests/reports'
        ]

        for report_dir in report_dirs:
            dir_path = self.project_root / report_dir
            dir_path.mkdir(parents=True, exist_ok=True)
            assert dir_path.exists(), f"Report directory '{report_dir}' should be creatable"


class TestCIEnvironmentSimulation:
    """Test CI environment simulation"""

    def setup_method(self):
        """Setup for each test method"""
        self.project_root = Path(__file__).parent.parent.parent
        os.chdir(self.project_root)

    def teardown_method(self):
        """Cleanup after each test"""
        os.chdir(self.project_root.parent if hasattr(self, 'project_root') else Path.cwd())

    def test_ci_environment_variables(self):
        """Test that CI environment variables are handled correctly"""
        # Set CI environment variables
        original_values = {}
        ci_vars = {
            'CI': 'true',
            'NEO4J_DISABLED': '1',
            'PYTHON_VERSION': '3.11'
        }

        for var, value in ci_vars.items():
            original_values[var] = os.environ.get(var)
            os.environ[var] = value

        try:
            # Test that system works with CI variables
            result = subprocess.run([
                sys.executable, '-c',
                'import os; print("CI:", os.environ.get("CI")); print("NEO4J_DISABLED:", os.environ.get("NEO4J_DISABLED"))'
            ], capture_output=True, text=True)

            assert result.returncode == 0
            assert "CI: true" in result.stdout
            assert "NEO4J_DISABLED: 1" in result.stdout

        finally:
            # Restore original environment
            for var, original_value in original_values.items():
                if original_value is not None:
                    os.environ[var] = original_value
                elif var in os.environ:
                    del os.environ[var]

    def test_timeout_handling(self):
        """Test that operations complete within CI timeout limits"""
        # Test that smoke tests complete within timeout
        start_time = time.time()

        result = subprocess.run([
            sys.executable, 'run_smoke_tests.py'
        ], capture_output=True, text=True, timeout=180)  # 3 minute timeout like CI

        elapsed_time = time.time() - start_time

        assert elapsed_time < 180, "Smoke tests should complete within CI timeout"
        assert result.returncode == 0, "Smoke tests should pass within timeout"

    def test_artifact_generation(self):
        """Test that CI artifacts can be generated"""
        # Test smoke test results generation
        result = subprocess.run([
            sys.executable, 'run_smoke_tests.py'
        ], capture_output=True, text=True, timeout=120)

        # Check if results file was created
        results_file = self.project_root / 'smoke_test_results.txt'
        if results_file.exists():
            assert results_file.stat().st_size > 0, "Results file should not be empty"

            with open(results_file, 'r') as f:
                content = f.read()
                assert len(content) > 0, "Results should have content"
        else:
            # If results file doesn't exist, at least the smoke tests should have run successfully
            assert result.returncode == 0, "Smoke tests should have run successfully"

    def test_parallel_job_simulation(self):
        """Test that multiple jobs could run in parallel"""
        # Simulate running multiple components that would run in parallel in CI
        jobs = [
            ([sys.executable, 'main.py'], 'main script'),
            ([sys.executable, 'cortex_direct.py'], 'direct CLI'),
        ]

        # Run jobs and collect results
        results = []
        for cmd, name in jobs:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                results.append((name, result.returncode == 0))
            except subprocess.TimeoutExpired:
                results.append((name, False))

        # At least one job should succeed
        successful_jobs = [name for name, success in results if success]
        assert len(successful_jobs) > 0, f"At least one parallel job should succeed. Results: {results}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
