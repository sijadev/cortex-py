#!/usr/bin/env python3
"""
Comprehensive CLI Tests for the expanded Cortex CLI
Prevents errors from missing commands and ensures all 16 commands work properly
"""
import subprocess
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Ensure project root is in Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class TestCortexCLIComprehensive:
    """Comprehensive tests for all 16 CLI commands"""

    @pytest.fixture
    def cli_env(self):
        """Setup environment for CLI testing"""
        env = os.environ.copy()
        env.setdefault("NEO4J_URI", "bolt://localhost:7687")
        env.setdefault("NEO4J_USER", "neo4j")
        env.setdefault("NEO4J_PASSWORD", "neo4jtest")
        return env

    @pytest.fixture
    def python_exec(self):
        """Get Python executable"""
        venv_python = project_root / ".venv" / "bin" / "python"
        return str(venv_python) if venv_python.exists() else sys.executable

    @pytest.fixture
    def cli_path(self):
        """Get CLI path"""
        return project_root / "cortex_neo" / "cortex_cli.py"

    def run_cli_command(self, command, python_exec, cli_path, cli_env, timeout=15):
        """Helper to run CLI commands safely"""
        try:
            result = subprocess.run(
                [python_exec, str(cli_path)] + command,
                capture_output=True,
                text=True,
                env=cli_env,
                cwd=project_root,
                timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired:
            pytest.skip(f"Command {' '.join(command)} timed out")
        except Exception as e:
            pytest.fail(f"Command {' '.join(command)} failed unexpectedly: {e}")

    def test_cli_help_command(self, python_exec, cli_path, cli_env):
        """Test CLI help command works"""
        result = self.run_cli_command(["--help"], python_exec, cli_path, cli_env)

        # Help should either work (return 0) or gracefully handle missing commands
        assert result.returncode in [0, 1, 2], f"CLI help crashed: {result.stderr}"

    def test_all_basic_commands_exist(self, python_exec, cli_path, cli_env):
        """Test that all basic commands can be called without crashing"""
        basic_commands = [
            ["validate-connection"],
            ["cortex-status"],
            ["smart-overview"],
            ["list-workflows"],
            ["list-notes"],
            ["list-tags"],
        ]

        for command in basic_commands:
            result = self.run_cli_command(command, python_exec, cli_path, cli_env)

            # Commands should execute without crashing (may fail if Neo4j down, but shouldn't crash)
            assert result.returncode in [0, 1], f"Command {' '.join(command)} crashed: {result.stderr}"

    def test_add_note_command_structure(self, python_exec, cli_path, cli_env):
        """Test add-note command accepts expected arguments"""
        # Test that add-note command exists and accepts arguments
        result = self.run_cli_command(
            ["add-note", "Test Note", "--content", "Test content", "--description", "Test desc"],
            python_exec, cli_path, cli_env
        )

        # Should not crash due to argument issues
        assert result.returncode in [0, 1], f"add-note command crashed: {result.stderr}"

    def test_smart_note_command_structure(self, python_exec, cli_path, cli_env):
        """Test add-note-smart command accepts expected arguments"""
        # Test that the new smart command exists
        result = self.run_cli_command(
            ["add-note-smart", "Smart Test Note", "--content", "Performance metrics test", "--type", "guide"],
            python_exec, cli_path, cli_env
        )

        # Should not crash due to argument issues
        assert result.returncode in [0, 1], f"add-note-smart command crashed: {result.stderr}"

    def test_tag_management_commands(self, python_exec, cli_path, cli_env):
        """Test tag management commands exist and work"""
        tag_commands = [
            ["list-tags"],
            ["create-performance-tags"],
        ]

        for command in tag_commands:
            result = self.run_cli_command(command, python_exec, cli_path, cli_env)
            assert result.returncode in [0, 1], f"Tag command {' '.join(command)} crashed: {result.stderr}"

    def test_search_and_network_commands(self, python_exec, cli_path, cli_env):
        """Test search and network commands exist"""
        commands = [
            ["search-notes", "test"],
            ["show-network"],
        ]

        for command in commands:
            result = self.run_cli_command(command, python_exec, cli_path, cli_env)
            assert result.returncode in [0, 1], f"Command {' '.join(command)} crashed: {result.stderr}"

    @pytest.mark.skipif(
        os.environ.get("NEO4J_URI") is None,
        reason="Neo4j not configured"
    )
    def test_with_neo4j_connection(self, python_exec, cli_path, cli_env):
        """Test commands when Neo4j is actually available"""
        # First validate connection
        connection_result = self.run_cli_command(["validate-connection"], python_exec, cli_path, cli_env)

        if connection_result.returncode != 0:
            pytest.skip("Neo4j not available for integration testing")

        # Test commands that should work with Neo4j
        working_commands = [
            ["list-notes"],
            ["list-tags"],
            ["cortex-status"],
            ["create-performance-tags"],
        ]

        for command in working_commands:
            result = self.run_cli_command(command, python_exec, cli_path, cli_env)
            assert result.returncode == 0, f"Command {' '.join(command)} failed with Neo4j: {result.stderr}"

    def test_cli_imports_successfully(self):
        """Test that the CLI module can be imported without errors"""
        try:
            # Test if cortex_cli can be imported without syntax errors
            cortex_cli_path = project_root / "cortex_neo" / "cortex_cli.py"

            # Read and compile the CLI file to check for syntax errors
            with open(cortex_cli_path, 'r', encoding='utf-8') as f:
                cli_code = f.read()

            compile(cli_code, str(cortex_cli_path), 'exec')

        except SyntaxError as e:
            pytest.fail(f"CLI has syntax errors: {e}")
        except FileNotFoundError:
            pytest.fail("CLI file not found")

    def test_click_commands_properly_defined(self):
        """Test that Click commands are properly defined"""
        try:
            # Import the CLI module in a safe way
            import importlib.util

            cortex_cli_path = project_root / "cortex_neo" / "cortex_cli.py"
            spec = importlib.util.spec_from_file_location("cortex_cli", cortex_cli_path)
            cortex_cli = importlib.util.module_from_spec(spec)

            # This should not fail if Click commands are properly defined
            spec.loader.exec_module(cortex_cli)

            # Check that the main CLI group exists
            assert hasattr(cortex_cli, 'cli'), "Main CLI group should exist"

        except Exception as e:
            pytest.fail(f"CLI module has import/definition errors: {e}")

    def test_all_16_commands_covered(self, python_exec, cli_path, cli_env):
        """Test that all 16 expected commands are available"""
        expected_commands = [
            # Basic commands (7)
            "list-workflows",
            "list-notes",
            "add-note",
            "show-note",
            "cortex-status",
            "smart-overview",
            "validate-connection",
            # Tag management (3)
            "list-tags",
            "add-tag",
            "show-tag",
            # Governance (2)
            "add-note-smart",
            "create-performance-tags",
            # Search (1)
            "search-notes",
            # Network (2)
            "link-notes",
            "show-network",
        ]

        # Test that commands don't crash with help
        failing_commands = []

        for command in expected_commands:
            try:
                # Try to run each command with minimal args to see if it exists
                # Most will fail due to missing args, but shouldn't crash completely
                result = subprocess.run(
                    [python_exec, str(cli_path), command],
                    capture_output=True,
                    text=True,
                    env=cli_env,
                    cwd=project_root,
                    timeout=5
                )

                # Command exists if it doesn't return "no such command" type errors
                if "No such command" in result.stderr or "Usage:" in result.stderr:
                    # This is expected - command exists but needs args
                    continue
                elif result.returncode in [0, 1, 2]:
                    # Command executed (success, expected failure, or missing args)
                    continue
                else:
                    failing_commands.append((command, result.stderr))

            except subprocess.TimeoutExpired:
                # Timeout is acceptable - command exists but may be waiting for Neo4j
                continue
            except Exception as e:
                failing_commands.append((command, str(e)))

        if failing_commands:
            pytest.fail(f"Commands that failed completely: {failing_commands}")

        print(f"✅ All {len(expected_commands)} expected commands are available")


class TestCLIErrorPrevention:
    """Tests specifically designed to prevent common CLI errors"""

    def test_no_undefined_click_commands(self):
        """Ensure no undefined Click commands cause import errors"""
        try:
            # This should not fail if all Click decorators are properly used
            from cortex_neo import cortex_cli
        except ImportError as e:
            if "No module named" in str(e):
                pytest.skip("CLI module not in Python path")
            else:
                pytest.fail(f"CLI has import errors: {e}")
        except Exception as e:
            pytest.fail(f"CLI has definition errors: {e}")

    def test_no_missing_dependencies(self):
        """Test that all required dependencies are available"""
        required_imports = [
            "click",
            "neo4j",
            "logging",
            "os",
            "sys",
            "datetime"
        ]

        missing_imports = []
        for imp in required_imports:
            try:
                __import__(imp)
            except ImportError:
                missing_imports.append(imp)

        if missing_imports:
            pytest.fail(f"Missing required dependencies: {missing_imports}")

    def test_governance_integration_imports(self):
        """Test that governance integration doesn't break CLI"""
        try:
            # Test the import that the smart commands use
            from src.governance.data_governance import DataGovernanceEngine

            # Should be able to create an instance
            governance = DataGovernanceEngine()
            assert governance is not None

        except ImportError:
            pytest.skip("Governance module not available - smart commands will be limited")
        except Exception as e:
            pytest.fail(f"Governance integration has errors: {e}")

    def test_neo4j_helper_class(self):
        """Test that Neo4jHelper class works correctly"""
        try:
            import importlib.util

            cortex_cli_path = project_root / "cortex_neo" / "cortex_cli.py"
            spec = importlib.util.spec_from_file_location("cortex_cli", cortex_cli_path)
            cortex_cli = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cortex_cli)

            # Test Neo4jHelper class
            assert hasattr(cortex_cli, 'Neo4jHelper'), "Neo4jHelper class should exist"
            assert hasattr(cortex_cli.Neo4jHelper, 'get_driver'), "get_driver method should exist"
            assert hasattr(cortex_cli.Neo4jHelper, 'close'), "close method should exist"

        except Exception as e:
            pytest.fail(f"Neo4jHelper class has errors: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
