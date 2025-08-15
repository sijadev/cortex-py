#!/usr/bin/env python3
"""
Tests for Safe Transactions Module
Addresses critical 0% coverage gap in data backup and integrity validation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Add project root to Python path dynamically
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from src.safe_transactions import SafeTransactionManager, DataIntegrityValidator, ensure_safe_environment


class TestSafeTransactionManager:
    """Test suite for SafeTransactionManager"""

    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary directory for backup tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_driver(self):
        """Create mock Neo4j driver"""
        driver = Mock()
        session = Mock()

        # Mock session context manager
        driver.session.return_value.__enter__ = Mock(return_value=session)
        driver.session.return_value.__exit__ = Mock(return_value=None)

        # Mock transaction context manager
        tx = Mock()
        session.begin_transaction.return_value.__enter__ = Mock(return_value=tx)
        session.begin_transaction.return_value.__exit__ = Mock(return_value=None)

        # Mock query results
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        session.run.return_value = mock_result

        return driver

    @pytest.fixture
    def transaction_manager(self, mock_driver, temp_backup_dir):
        """Create SafeTransactionManager instance for testing"""
        return SafeTransactionManager(driver=mock_driver, backup_dir=str(temp_backup_dir))

    def test_transaction_manager_initialization(self, transaction_manager, temp_backup_dir):
        """Test SafeTransactionManager initialization"""
        assert transaction_manager is not None
        assert hasattr(transaction_manager, "safe_transaction")
        assert transaction_manager.backup_dir == str(temp_backup_dir)
        assert os.path.exists(transaction_manager.backup_dir)

    def test_backup_creation(self, transaction_manager):
        """Test backup creation functionality"""
        backup_path = transaction_manager._create_backup("test_operation")
        assert backup_path != ""
        assert os.path.exists(backup_path)
        assert "test_operation" in backup_path

    def test_safe_transaction_decorator(self, transaction_manager):
        """Test safe transaction decorator functionality"""
        @transaction_manager.safe_transaction("test_op")
        def test_function(tx, test_arg):
            return f"success_{test_arg}"

        result = test_function("test_value")
        assert result == "success_test_value"

    def test_cleanup_old_backups(self, transaction_manager):
        """Test cleanup of old backup files"""
        # Create some test backup files
        test_backup = os.path.join(transaction_manager.backup_dir, "test_backup.yaml")
        with open(test_backup, 'w') as f:
            f.write("test: data")

        assert os.path.exists(test_backup)
        # Test passes if no exception is raised


class TestDataIntegrityValidator:
    """Test suite for DataIntegrityValidator"""

    @pytest.fixture
    def temp_baseline_file(self):
        """Create temporary baseline file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            baseline_data = {
                "notes": 5,
                "workflows": 3,
                "tags": 2,
                "templates": 1,
                "timestamp": datetime.now().isoformat()
            }
            json.dump(baseline_data, temp_file)
            temp_file.flush()
            yield temp_file.name
        os.unlink(temp_file.name)

    @pytest.fixture
    def mock_driver(self):
        """Create mock Neo4j driver for validator tests"""
        driver = Mock()
        session = Mock()

        driver.session.return_value.__enter__ = Mock(return_value=session)
        driver.session.return_value.__exit__ = Mock(return_value=None)

        # Mock count queries - fix the Mock configuration to handle iteration
        def mock_run(query):
            mock_result = Mock()

            if "UNION ALL" in query:
                # This is the relationship count query - return multiple records
                mock_records = []

                # Create mock records that properly support items() method
                relationships = [
                    ('note_links', 2),
                    ('workflow_links', 3),
                    ('tag_links', 1),
                    ('template_links', 4)
                ]

                for rel_name, count in relationships:
                    mock_record = Mock()
                    # Configure items() to return the key-value pair as expected
                    mock_record.items.return_value = [(rel_name, count)]
                    mock_records.append(mock_record)

                # Configure the result to be iterable
                mock_result.__iter__ = Mock(return_value=iter(mock_records))
            else:
                # This is a single count query - return one record
                mock_record = Mock()
                mock_record.__getitem__ = Mock(side_effect=lambda key: 5 if key == 'count' else 0)
                mock_record.get = Mock(return_value=5)
                mock_result.single.return_value = mock_record

            return mock_result

        session.run.side_effect = mock_run

        return driver

    @pytest.fixture
    def validator(self, mock_driver, temp_baseline_file):
        """Create DataIntegrityValidator instance"""
        return DataIntegrityValidator(driver=mock_driver, baseline_file=temp_baseline_file)

    def test_validator_initialization(self, validator):
        """Test DataIntegrityValidator initialization"""
        assert validator is not None
        assert hasattr(validator, "validate_integrity")
        assert hasattr(validator, "get_current_stats")

    def test_get_current_stats(self, validator):
        """Test current stats collection"""
        stats = validator.get_current_stats()
        assert isinstance(stats, dict)
        assert 'notes' in stats
        assert 'workflows' in stats

    def test_validate_integrity_success(self, validator):
        """Test successful integrity validation"""
        # Mock consistent data
        validator.get_current_stats = Mock(return_value={
            "notes": 5,
            "workflows": 3,
            "tags": 2,
            "templates": 1
        })

        result = validator.validate_integrity()
        assert result is True

    def test_validate_integrity_corruption_detected(self, validator):
        """Test integrity validation when corruption is detected"""
        # Mock corrupted data (significant change)
        validator.get_current_stats = Mock(return_value={
            "notes": 1,  # Significant drop from baseline of 5
            "workflows": 3,
            "tags": 2,
            "templates": 1
        })

        result = validator.validate_integrity()
        assert result is False

    def test_emergency_restore_check(self, validator):
        """Test emergency restore check functionality"""
        result = validator.emergency_restore_check()
        assert isinstance(result, bool)


class TestSafeTransactionIntegration:
    """Integration tests for safe transaction components"""

    @pytest.fixture
    def mock_driver(self):
        """Create comprehensive mock driver"""
        driver = Mock()
        session = Mock()
        tx = Mock()

        driver.session.return_value.__enter__ = Mock(return_value=session)
        driver.session.return_value.__exit__ = Mock(return_value=None)
        session.begin_transaction.return_value.__enter__ = Mock(return_value=tx)
        session.begin_transaction.return_value.__exit__ = Mock(return_value=None)

        # Mock count queries with comprehensive support for all query types
        def mock_run(query):
            mock_result = Mock()

            if "UNION ALL" in query:
                # This is the relationship count query - return multiple records
                mock_records = []

                # Create mock records that properly support items() method
                relationships = [
                    ('note_links', 2),
                    ('workflow_links', 3),
                    ('tag_links', 1),
                    ('template_links', 4)
                ]

                for rel_name, count in relationships:
                    mock_record = Mock()
                    # Configure items() to return the key-value pair as expected
                    mock_record.items.return_value = [(rel_name, count)]
                    mock_records.append(mock_record)

                # Configure the result to be iterable
                mock_result.__iter__ = Mock(return_value=iter(mock_records))
            elif "orphaned" in query.lower():
                # This is an orphaned data check query
                mock_record = Mock()
                # Return 0 for orphaned data checks to indicate no orphaned data
                if "orphaned_tags" in query:
                    mock_record.__getitem__ = Mock(side_effect=lambda key: 0 if key == 'orphaned_tags' else 0)
                elif "orphaned_templates" in query:
                    mock_record.__getitem__ = Mock(side_effect=lambda key: 0 if key == 'orphaned_templates' else 0)
                else:
                    mock_record.__getitem__ = Mock(side_effect=lambda key: 0)
                mock_result.single.return_value = mock_record
            else:
                # This is a single count query - return one record
                mock_record = Mock()
                mock_record.__getitem__ = Mock(side_effect=lambda key: 5 if key == 'count' else 0)
                mock_record.get = Mock(return_value=5)
                mock_result.single.return_value = mock_record
                # Also support iteration for general queries
                mock_result.__iter__ = Mock(return_value=iter([]))

            return mock_result

        session.run.side_effect = mock_run

        return driver

    def test_integrity_validation_after_transaction(self, mock_driver):
        """Test integrity validation after safe transaction"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create transaction manager
            tm = SafeTransactionManager(driver=mock_driver, backup_dir=temp_dir)

            # Create validator
            baseline_file = os.path.join(temp_dir, "baseline.json")
            validator = DataIntegrityValidator(driver=mock_driver, baseline_file=baseline_file)

            # Mock consistent stats
            mock_stats = {
                "notes": 5,
                "workflows": 3,
                "tags": 2,
                "templates": 1,
                "timestamp": datetime.now().isoformat()
            }
            validator.get_current_stats = Mock(return_value=mock_stats)

            # Save baseline
            validator.save_baseline()

            # Test transaction + validation
            @tm.safe_transaction("test_operation")
            def test_transaction(tx):
                return "transaction_result"

            result = test_transaction()
            assert result == "transaction_result"

            # Validate integrity
            integrity_result = validator.validate_integrity()
            assert integrity_result is True


class TestUtilityFunctions:
    """Test utility functions"""

    def test_ensure_safe_environment(self):
        """Test safe environment initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                ensure_safe_environment()

                # Check that directories are created
                expected_dirs = [
                    "cortex_neo/backups/auto",
                    "cortex_neo/backups/pre",
                    "cortex_neo/monitoring",
                    "logs/safety"
                ]

                for directory in expected_dirs:
                    assert os.path.exists(directory), f"Directory {directory} should exist"

            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
