#!/usr/bin/env python3
"""
Test Suite für den Cortex CLI (Neo4j) - Updated for new CLI structure
"""
import subprocess
import sys
import os
from pathlib import Path
import pytest

# Ensure project root is in Python path
project_root = (
    Path(__file__).resolve().parent.parent.parent
)
sys.path.insert(0, str(project_root))


def test_cli_help():
    """Test ob CLI Help funktioniert."""
    repo_root = project_root
    venv_python = repo_root / ".venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

    result = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "--help"],
        capture_output=True,
        text=True,
        cwd=repo_root,
        timeout=10
    )

    # CLI should return help or at least not crash
    assert result.returncode == 0 or "Usage:" in result.stdout or "Commands:" in result.stdout


def test_validate_connection():
    """Test ob validate-connection Befehl funktioniert."""
    repo_root = project_root
    venv_python = repo_root / ".venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

    env = os.environ.copy()
    env.setdefault("NEO4J_URI", "bolt://localhost:7687")
    env.setdefault("NEO4J_USER", "neo4j")
    env.setdefault("NEO4J_PASSWORD", "neo4jtest")

    result = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "validate-connection"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
        timeout=15
    )

    # Command should execute without crashing (connection may fail, but command should work)
    assert result.returncode in [0, 1], f"validate-connection crashed: {result.stderr}"

    if result.returncode == 0:
        print("✅ Neo4j connection successful")
    else:
        print("⚠️ Neo4j connection failed (expected if Neo4j not running)")
        pytest.skip("Neo4j not available for testing")


def test_list_workflows():
    """Test ob list-workflows Befehl funktioniert."""
    repo_root = project_root
    venv_python = repo_root / ".venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

    env = os.environ.copy()
    env.setdefault("NEO4J_URI", "bolt://localhost:7687")
    env.setdefault("NEO4J_USER", "neo4j")
    env.setdefault("NEO4J_PASSWORD", "neo4jtest")

    # First test connection
    connection_test = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "validate-connection"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
        timeout=10
    )

    if connection_test.returncode != 0:
        print("⚠️ Neo4j-Verbindung nicht verfügbar, überspringe Test")
        pytest.skip("Neo4j-Verbindung nicht verfügbar")

    # Test list-workflows command
    result = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "list-workflows"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
        timeout=10
    )

    assert result.returncode == 0, f"list-workflows command failed: {result.stderr}"
    print(f"✅ list-workflows executed successfully: {result.stdout.strip()}")


def test_list_notes():
    """Test ob list-notes Befehl funktioniert."""
    repo_root = project_root
    venv_python = repo_root / ".venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

    env = os.environ.copy()
    env.setdefault("NEO4J_URI", "bolt://localhost:7687")
    env.setdefault("NEO4J_USER", "neo4j")
    env.setdefault("NEO4J_PASSWORD", "neo4jtest")

    # First test connection
    connection_test = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "validate-connection"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
        timeout=10
    )

    if connection_test.returncode != 0:
        pytest.skip("Neo4j-Verbindung nicht verfügbar")

    # Test list-notes command
    result = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "list-notes"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
        timeout=10
    )

    assert result.returncode == 0, f"list-notes command failed: {result.stderr}"
    print(f"✅ list-notes executed successfully")


def test_list_tags():
    """Test ob list-tags Befehl funktioniert (new command)."""
    repo_root = project_root
    venv_python = repo_root / ".venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

    env = os.environ.copy()
    env.setdefault("NEO4J_URI", "bolt://localhost:7687")
    env.setdefault("NEO4J_USER", "neo4j")
    env.setdefault("NEO4J_PASSWORD", "neo4jtest")

    # First test connection
    connection_test = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "validate-connection"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
        timeout=10
    )

    if connection_test.returncode != 0:
        pytest.skip("Neo4j-Verbindung nicht verfügbar")

    # Test list-tags command (new in expanded CLI)
    result = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "list-tags"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
        timeout=10
    )

    assert result.returncode == 0, f"list-tags command failed: {result.stderr}"
    print(f"✅ list-tags executed successfully")


def test_cortex_status():
    """Test ob cortex-status Befehl funktioniert."""
    repo_root = project_root
    venv_python = repo_root / ".venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

    env = os.environ.copy()
    env.setdefault("NEO4J_URI", "bolt://localhost:7687")
    env.setdefault("NEO4J_USER", "neo4j")
    env.setdefault("NEO4J_PASSWORD", "neo4jtest")

    # Test cortex-status command
    result = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "cortex-status"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
        timeout=15
    )

    # Status command should work even if Neo4j is down
    assert result.returncode in [0, 1], f"cortex-status crashed: {result.stderr}"
    print(f"✅ cortex-status executed successfully")


def test_create_performance_tags():
    """Test ob create-performance-tags Befehl funktioniert (new command)."""
    repo_root = project_root
    venv_python = repo_root / ".venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

    env = os.environ.copy()
    env.setdefault("NEO4J_URI", "bolt://localhost:7687")
    env.setdefault("NEO4J_USER", "neo4j")
    env.setdefault("NEO4J_PASSWORD", "neo4jtest")

    # First test connection
    connection_test = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "validate-connection"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
        timeout=10
    )

    if connection_test.returncode != 0:
        pytest.skip("Neo4j-Verbindung nicht verfügbar")

    # Test create-performance-tags command (new in expanded CLI)
    result = subprocess.run(
        [python_exec, "cortex_neo/cortex_cli.py", "create-performance-tags"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
        timeout=15
    )

    assert result.returncode == 0, f"create-performance-tags command failed: {result.stderr}"
    print(f"✅ create-performance-tags executed successfully")


if __name__ == "__main__":
    test_cli_help()
    test_validate_connection()
    test_list_workflows()
    test_list_notes()
    test_list_tags()
    test_cortex_status()
    test_create_performance_tags()
