#!/usr/bin/env python3
"""
Integration Tests for Cortex GitHub Workflow
============================================

This package contains comprehensive integration tests for the Cortex CI/CD pipeline.

Test Modules:
- test_github_workflow.py: Tests GitHub workflow configuration and structure
- test_neo4j_integration.py: Tests Neo4j database integration for CI
- test_cli_integration.py: Tests Cortex CLI integration
- test_mcp_integration.py: Tests MCP (Model Context Protocol) system integration
- test_system_integration.py: Tests end-to-end system integration

These tests ensure that:
1. GitHub workflow (test.yml) is properly configured
2. All required components exist and are accessible
3. CI environment simulation works correctly
4. Integration between different system components functions properly
5. Smoke tests, unit tests, and integration tests can run in CI environment
"""

__version__ = "1.0.0"
__author__ = "Cortex Development Team"

# Test configuration for GitHub workflow integration
WORKFLOW_CONFIG = {
    "python_version": "3.11",
    "timeout_minutes": {
        "smoke_tests": 10,
        "unit_tests": 15,
        "integration_tests": 20,
        "cli_tests": 15,
        "mcp_tests": 10
    },
    "required_services": ["neo4j"],
    "required_artifacts": [
        "smoke-test-results",
        "unit-test-results",
        "integration-test-results",
        "cli-test-results",
        "mcp-test-results"
    ]
}

def get_workflow_config():
    """Get the workflow configuration for tests"""
    return WORKFLOW_CONFIG

def validate_test_environment():
    """Validate that the test environment is properly set up"""
    import os
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent

    # Check required files
    required_files = [
        ".github/workflows/test.yml",
        "run_smoke_tests.py",
        "validate_mcp_system.py",
        "requirements.txt",
        "requirements-dev.txt"
    ]

    missing_files = []
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        raise ValueError(f"Missing required files for GitHub workflow: {missing_files}")

    # Check required directories
    required_dirs = [
        "src",
        "tests/unit",
        "tests/integration",
        "tests/mcp",
        "cortex-cli"
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not (project_root / dir_path).exists():
            missing_dirs.append(dir_path)

    if missing_dirs:
        raise ValueError(f"Missing required directories for GitHub workflow: {missing_dirs}")

    return True

if __name__ == "__main__":
    print("🧪 Cortex GitHub Workflow Integration Tests")
    print("=" * 50)

    try:
        validate_test_environment()
        print("✅ Test environment validation passed")
    except ValueError as e:
        print(f"❌ Test environment validation failed: {e}")
        exit(1)

    print("\nAvailable test modules:")
    print("- test_github_workflow.py")
    print("- test_neo4j_integration.py")
    print("- test_cli_integration.py")
    print("- test_mcp_integration.py")
    print("- test_system_integration.py")

    print("\nRun with: python -m pytest tests/integration/ -v")
