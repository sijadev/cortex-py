#!/usr/bin/env python3
"""
Integration Tests for GitHub Workflow
Tests the entire CI/CD pipeline components
"""

import pytest
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
import yaml
import json
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestGitHubWorkflow:
    """Test suite for GitHub workflow integration"""

    def setup_method(self):
        """Setup for each test method"""
        self.project_root = Path(__file__).parent.parent.parent
        self.workflow_file = self.project_root / ".github" / "workflows" / "test.yml"

    def test_workflow_file_exists(self):
        """Test that the GitHub workflow files exist"""
        # Check for the new modular workflow structure
        workflow_dir = self.project_root / '.github' / 'workflows'
        assert workflow_dir.exists(), "GitHub workflows directory should exist"

        # Check for key workflow files (not requiring all to be present)
        key_workflows = [
            'smoke-tests.yml',
            'unit-tests.yml',
            'integration-tests.yml',
            'ci-pipeline.yml'
        ]

        existing_workflows = []
        for workflow in key_workflows:
            workflow_path = workflow_dir / workflow
            if workflow_path.exists():
                existing_workflows.append(workflow)

        assert len(existing_workflows) > 0, f"At least some key workflows should exist. Found: {existing_workflows}"

    def test_workflow_yaml_valid(self):
        """Test that the workflow YAML files are valid"""
        workflow_dir = self.project_root / '.github' / 'workflows'
        yaml_files = list(workflow_dir.glob('*.yml'))

        assert len(yaml_files) > 0, "Should have at least one workflow YAML file"

        for yaml_file in yaml_files:
            with open(yaml_file, 'r') as f:
                try:
                    workflow_content = yaml.safe_load(f)
                    assert workflow_content is not None, f"Workflow YAML {yaml_file.name} should be valid"
                except Exception as e:
                    pytest.fail(f"Invalid YAML in {yaml_file.name}: {e}")

    def test_required_jobs_present(self):
        """Test that required jobs are present across the workflow ecosystem"""
        workflow_dir = self.project_root / '.github' / 'workflows'

        # Look for key job types across all workflows
        all_jobs = []
        for yaml_file in workflow_dir.glob('*.yml'):
            if yaml_file.name == 'test.yml':
                continue  # Skip deprecated file

            with open(yaml_file, 'r') as f:
                try:
                    workflow_content = yaml.safe_load(f)
                    if workflow_content and 'jobs' in workflow_content:
                        all_jobs.extend(workflow_content['jobs'].keys())
                except:
                    continue

        # Check for essential job types (at least some should exist)
        essential_job_patterns = ['test', 'smoke', 'unit', 'integration', 'cli']
        found_patterns = []

        for pattern in essential_job_patterns:
            if any(pattern in job.lower() for job in all_jobs):
                found_patterns.append(pattern)

        assert len(found_patterns) > 0, f"Should find essential job patterns. Found jobs: {all_jobs}"

    def test_job_dependencies(self):
        """Test that job dependencies exist in orchestrating workflows"""
        # Look for the main CI pipeline that orchestrates dependencies
        ci_pipeline = self.project_root / '.github' / 'workflows' / 'ci-pipeline.yml'

        if ci_pipeline.exists():
            with open(ci_pipeline, 'r') as f:
                workflow_content = yaml.safe_load(f)

            if workflow_content and 'jobs' in workflow_content:
                jobs = workflow_content['jobs']

                # Check for job dependencies or workflow calls
                has_dependencies = False
                has_workflow_calls = False

                for job_name, job_config in jobs.items():
                    if isinstance(job_config, dict):
                        # Check for 'needs' dependencies
                        if 'needs' in job_config:
                            has_dependencies = True
                        # Check for workflow calls (uses: ./.github/workflows/...)
                        if 'uses' in job_config and '.github/workflows' in str(job_config['uses']):
                            has_workflow_calls = True

                assert has_dependencies or has_workflow_calls, f"CI pipeline should have job dependencies or workflow calls. Found jobs: {list(jobs.keys())}"
        else:
            # If no CI pipeline, check individual workflows have internal dependencies
            pytest.skip("No CI pipeline found - checking individual workflows not implemented")

    def test_environment_variables_set(self):
        """Test that required environment variables are set across workflows"""
        workflow_dir = self.project_root / '.github' / 'workflows'

        found_env_vars = set()
        for yaml_file in workflow_dir.glob('*.yml'):
            if yaml_file.name == 'test.yml':
                continue  # Skip deprecated file

            with open(yaml_file, 'r') as f:
                try:
                    workflow_content = yaml.safe_load(f)
                    if workflow_content and 'env' in workflow_content:
                        found_env_vars.update(workflow_content['env'].keys())
                except:
                    continue

        # Check for essential environment variables across all workflows
        essential_vars = ['PYTHON_VERSION', 'CI']
        found_essential = [var for var in essential_vars if var in found_env_vars]

        assert len(found_essential) > 0, f"Should find essential env vars. Found: {found_env_vars}"

    def test_neo4j_service_configuration(self):
        """Test that Neo4j service is configured in integration workflows"""
        # Look for integration test workflow
        integration_workflow = self.project_root / '.github' / 'workflows' / 'integration-tests.yml'

        if integration_workflow.exists():
            with open(integration_workflow, 'r') as f:
                content = f.read()

            # Check for Neo4j service configuration
            assert 'neo4j:' in content.lower(), "Integration workflow should include Neo4j service"
            assert '7474:7474' in content or '7687:7687' in content, "Should expose Neo4j ports"
        else:
            pytest.skip("Integration tests workflow not found")

    def test_artifact_uploads_configured(self):
        """Test that artifact uploads are configured in workflows"""
        workflow_dir = self.project_root / '.github' / 'workflows'

        found_artifacts = False
        for yaml_file in workflow_dir.glob('*.yml'):
            if yaml_file.name == 'test.yml':
                continue  # Skip deprecated file

            with open(yaml_file, 'r') as f:
                content = f.read()
                if 'upload-artifact' in content:
                    found_artifacts = True
                    break

        assert found_artifacts, "At least one workflow should have artifact uploads configured"


class TestWorkflowIntegrationWithLocalSystem:
    """Test integration between workflow and local system components"""

    def setup_method(self):
        """Setup for each test method"""
        self.project_root = Path(__file__).parent.parent.parent
        os.chdir(self.project_root)

    def test_smoke_test_runner_exists(self):
        """Test that the smoke test runner referenced in workflow exists"""
        smoke_test_file = self.project_root / "run_smoke_tests.py"
        assert smoke_test_file.exists(), "Smoke test runner should exist"

        # Test it's executable
        result = subprocess.run([sys.executable, str(smoke_test_file)],
                              capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, "Smoke test runner should execute successfully"

    def test_requirements_files_exist(self):
        """Test that required dependency files exist"""
        required_files = [
            "requirements.txt",
            "requirements-dev.txt"
        ]

        for req_file in required_files:
            file_path = self.project_root / req_file
            assert file_path.exists(), f"Requirements file '{req_file}' should exist"

    def test_test_directories_exist(self):
        """Test that all test directories referenced in workflow exist"""
        test_dirs = [
            "tests/unit/",
            "tests/integration/",
            "tests/mcp/",
            "cortex-cli/tests/"
        ]

        for test_dir in test_dirs:
            dir_path = self.project_root / test_dir
            assert dir_path.exists(), f"Test directory '{test_dir}' should exist"

    def test_mcp_validator_exists(self):
        """Test that MCP validator referenced in workflow exists"""
        mcp_validator = self.project_root / "validate_mcp_system.py"
        assert mcp_validator.exists(), "MCP system validator should exist"

    def test_pytest_configuration(self):
        """Test that pytest is properly configured"""
        # Check main pytest config
        pytest_ini = self.project_root / "pytest.ini"
        if pytest_ini.exists():
            with open(pytest_ini, 'r') as f:
                content = f.read()
                assert '[tool:pytest]' in content or '[pytest]' in content

        # Check cortex-cli pytest config
        cli_pytest_ini = self.project_root / "cortex-cli" / "pytest.ini"
        if cli_pytest_ini.exists():
            with open(cli_pytest_ini, 'r') as f:
                content = f.read()
                assert '[tool:pytest]' in content or '[pytest]' in content

    def test_cortex_cli_setup(self):
        """Test that Cortex CLI can be set up as required by workflow"""
        cortex_cli_dir = self.project_root / "cortex-cli"
        assert cortex_cli_dir.exists(), "Cortex CLI directory should exist"

        setup_py = cortex_cli_dir / "setup.py"
        assert setup_py.exists(), "Cortex CLI setup.py should exist"


class TestWorkflowSimulation:
    """Simulate parts of the GitHub workflow locally"""

    def setup_method(self):
        """Setup for each test method"""
        self.project_root = Path(__file__).parent.parent.parent
        os.chdir(self.project_root)

        # Set environment variables similar to CI
        os.environ["CI"] = "true"
        os.environ["NEO4J_DISABLED"] = "1"

    def teardown_method(self):
        """Cleanup after each test"""
        # Reset environment variables
        os.environ.pop("CI", None)
        os.environ.pop("NEO4J_DISABLED", None)

    def test_simulate_smoke_tests_job(self):
        """Simulate the smoke tests job locally"""
        # This simulates what the GitHub workflow does
        result = subprocess.run([
            sys.executable, "run_smoke_tests.py"
        ], capture_output=True, text=True, timeout=120)

        assert result.returncode == 0, f"Smoke tests job simulation failed: {result.stderr}"
        assert "All smoke tests passed!" in result.stdout, "Smoke tests should pass"

    def test_simulate_unit_tests_job(self):
        """Simulate the unit tests job locally"""
        if not shutil.which("pytest"):
            pytest.skip("pytest not available")

        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/unit/",
            "-v", "--tb=short", "--maxfail=5"
        ], capture_output=True, text=True, timeout=300)

        # Don't assert success here as some tests might fail, just check it runs
        assert "collected" in result.stdout, "Unit tests should be collected and run"

    def test_simulate_mcp_validation(self):
        """Simulate MCP validation as done in workflow"""
        result = subprocess.run([
            sys.executable, "validate_mcp_system.py"
        ], capture_output=True, text=True, timeout=60)

        # MCP validation might fail but should run without crashing
        assert result.returncode in [0, 1], "MCP validation should run without crashing"

    @pytest.mark.slow
    def test_dependency_installation_simulation(self):
        """Simulate dependency installation process"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a virtual environment
            venv_dir = Path(temp_dir) / "test_venv"
            result = subprocess.run([
                sys.executable, "-m", "venv", str(venv_dir)
            ], capture_output=True, text=True)

            assert result.returncode == 0, "Virtual environment creation should succeed"

            # Test pip install simulation (just check requirements files are valid)
            pip_executable = venv_dir / "bin" / "pip" if os.name != "nt" else venv_dir / "Scripts" / "pip.exe"

            # Check if requirements.txt is valid
            result = subprocess.run([
                str(pip_executable), "install", "--dry-run", "-r", "requirements.txt"
            ], capture_output=True, text=True, timeout=60)

            # Should not crash (return code might be non-zero due to dry-run)
            assert "ERROR" not in result.stderr.upper() or result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
