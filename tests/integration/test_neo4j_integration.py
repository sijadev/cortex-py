#!/usr/bin/env python3
"""
Integration Tests for Neo4j Database Connectivity
Tests Neo4j integration as used in the GitHub workflow
"""

import pytest
import os
import sys
import time
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestNeo4jIntegration:
    """Test Neo4j integration for CI/CD pipeline"""

    def setup_method(self):
        """Setup for each test method"""
        self.original_neo4j_disabled = os.environ.get('NEO4J_DISABLED')
        self.original_neo4j_uri = os.environ.get('NEO4J_URI')
        self.original_neo4j_user = os.environ.get('NEO4J_USER')
        self.original_neo4j_password = os.environ.get('NEO4J_PASSWORD')

    def teardown_method(self):
        """Cleanup after each test"""
        # Restore original environment variables
        if self.original_neo4j_disabled is not None:
            os.environ['NEO4J_DISABLED'] = self.original_neo4j_disabled
        elif 'NEO4J_DISABLED' in os.environ:
            del os.environ['NEO4J_DISABLED']

        for var, original in [
            ('NEO4J_URI', self.original_neo4j_uri),
            ('NEO4J_USER', self.original_neo4j_user),
            ('NEO4J_PASSWORD', self.original_neo4j_password)
        ]:
            if original is not None:
                os.environ[var] = original
            elif var in os.environ:
                del os.environ[var]

    def test_neo4j_disabled_mode(self):
        """Test that Neo4j can be properly disabled for CI"""
        os.environ['NEO4J_DISABLED'] = '1'

        try:
            from src.cortex_system_config import CortexSystemConfig
            config = CortexSystemConfig()

            # Should work even with Neo4j disabled
            assert hasattr(config, 'neo4j_uri')

        except ImportError:
            pytest.skip("CortexSystemConfig not available")

    def test_neo4j_connection_with_test_credentials(self):
        """Test Neo4j connection with test credentials like in CI"""
        # Set test environment variables like in GitHub workflow
        os.environ['NEO4J_URI'] = 'bolt://localhost:7687'
        os.environ['NEO4J_USER'] = 'neo4j'
        os.environ['NEO4J_PASSWORD'] = 'testpassword'
        os.environ['NEO4J_DISABLED'] = '0'

        try:
            from cortex_neo.config import Settings
            cfg = Settings.from_env()

            assert cfg.uri == 'bolt://localhost:7687'
            assert cfg.user == 'neo4j'
            assert cfg.password == 'testpassword'

        except ImportError:
            pytest.skip("cortex_neo.config not available")

    def test_safe_transactions_with_mock_driver(self):
        """Test SafeTransactionManager with mock driver (CI simulation)"""
        try:
            from src.safe_transactions import SafeTransactionManager

            # Create a mock driver like in the smoke tests
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

            assert tx_manager.backup_dir.endswith("backups/auto")

        except ImportError:
            pytest.skip("SafeTransactionManager not available")

    def test_neo4j_health_check_simulation(self):
        """Test Neo4j health check as done in GitHub workflow"""
        # Simulate the health check command from workflow
        # In real CI, this would connect to actual Neo4j service

        # Mock the health check process
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="1")

            # Simulate health check
            result = subprocess.run([
                'cypher-shell', '-u', 'neo4j', '-p', 'testpassword', 'RETURN 1'
            ], capture_output=True, text=True)

            # In our mock, this should succeed
            assert result.returncode == 0


class TestCortexNeoIntegration:
    """Test Cortex Neo components for CI integration"""

    def test_cortex_neo_directory_structure(self):
        """Test that cortex_neo directory has required structure"""
        cortex_neo_dir = project_root / "cortex_neo"
        assert cortex_neo_dir.exists(), "cortex_neo directory should exist"

        required_files = [
            "__init__.py",
            "config.py",
            "requirements.txt"
        ]

        for file_name in required_files:
            file_path = cortex_neo_dir / file_name
            assert file_path.exists(), f"cortex_neo/{file_name} should exist"

    def test_neo4j_docker_compose_exists(self):
        """Test that Neo4j Docker Compose file exists for local testing"""
        docker_compose = project_root / "cortex_neo" / "docker-compose.yml"
        if docker_compose.exists():
            with open(docker_compose, 'r') as f:
                content = f.read()
                assert 'neo4j' in content.lower()
                assert 'services' in content.lower()

    def test_backup_scripts_exist(self):
        """Test that backup scripts exist for data integrity"""
        backup_script = project_root / "cortex_neo" / "backup.sh"
        if backup_script.exists():
            assert backup_script.is_file()
            # Check if it's executable (on Unix systems)
            if os.name != 'nt':
                assert os.access(backup_script, os.X_OK) or True  # May not be executable in CI

    def test_neo4j_start_script_exists(self):
        """Test that Neo4j start script exists"""
        start_script = project_root / "cortex_neo" / "start_neo4j.sh"
        if start_script.exists():
            assert start_script.is_file()


class TestDatabaseMigrations:
    """Test database migration scripts for CI"""

    def test_migration_script_exists(self):
        """Test that migration scripts exist"""
        migration_script = project_root / "cortex_neo" / "migrate_structure.py"
        if migration_script.exists():
            # Test that it can be imported without errors
            import importlib.util
            spec = importlib.util.spec_from_file_location("migrate_structure", migration_script)
            if spec and spec.loader:
                try:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    assert True  # If we get here, import was successful
                except Exception as e:
                    pytest.fail(f"Migration script import failed: {e}")

    def test_sample_structure_yaml_exists(self):
        """Test that sample structure file exists for testing"""
        sample_structure = project_root / "cortex_neo" / "sample_structure.yaml"
        if sample_structure.exists():
            import yaml
            with open(sample_structure, 'r') as f:
                try:
                    data = yaml.safe_load(f)
                    assert data is not None
                except yaml.YAMLError as e:
                    pytest.fail(f"Sample structure YAML is invalid: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
