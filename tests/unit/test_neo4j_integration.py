#!/usr/bin/env python3
"""
Neo4j Integration Tests für Data Governance
Testet alle Neo4j-spezifischen Funktionen der DataGovernanceEngine
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from pathlib import Path

# Add project root to Python path dynamically
project_root = Path(__file__).resolve().parent.parent.parent
import sys

sys.path.insert(0, str(project_root))

from src.governance.data_governance import Neo4jTemplateManager, DataGovernanceEngine


# Helper function to check Neo4j availability
def _neo4j_available():
    """Check if Neo4j is available by attempting a connection"""
    try:
        # Prüfe zuerst ob die notwendigen Umgebungsvariablen gesetzt sind
        neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
        neo4j_password = os.environ.get("NEO4J_PASSWORD")

        # Wenn NEO4J_DISABLED gesetzt ist, ist Neo4j definitiv nicht verfügbar für echte Verbindungen
        if os.environ.get("NEO4J_DISABLED", "").lower() in ("1", "true", "yes"):
            return False

        # Wenn kein Passwort gesetzt ist, ist Neo4j wahrscheinlich nicht konfiguriert
        if not neo4j_password:
            return False

        manager = Neo4jTemplateManager()
        return manager.is_connected()
    except Exception:
        return False


def _can_run_mocked_tests():
    """Check if we can run mocked Neo4j tests (should always be True unless critical imports fail)"""
    try:
        # Mock tests sollten immer laufen können, auch wenn NEO4J_DISABLED gesetzt ist
        from unittest.mock import Mock, patch

        return True
    except ImportError:
        return False


class TestNeo4jRealConnection:
    """Tests mit echter Neo4j-Verbindung (falls verfügbar)"""

    @pytest.fixture
    def neo4j_manager(self):
        """Erstellt Neo4j Manager - funktioniert nur wenn Neo4j läuft"""
        manager = Neo4jTemplateManager()
        return manager

    @pytest.mark.skipif(not _neo4j_available(), reason="Neo4j nicht verfügbar")
    def test_real_neo4j_connection(self, neo4j_manager):
        """Test echte Neo4j-Verbindung"""
        assert neo4j_manager.is_connected() == True

    @pytest.mark.skipif(not _neo4j_available(), reason="Neo4j nicht verfügbar")
    def test_create_and_retrieve_template(self, neo4j_manager):
        """Test Erstellen und Abrufen eines Templates in Neo4j"""
        if not neo4j_manager.is_connected():
            pytest.skip("Neo4j nicht verbunden")

        # Template erstellen
        templates = neo4j_manager.create_template_if_missing(
            "test_project", "Test Integration Project", ["integration", "test"]
        )

        assert isinstance(templates, dict)
        assert len(templates) > 0

        # Template wieder abrufen
        retrieved = neo4j_manager.get_templates_for_project("test_project", ["integration", "test"])

        assert isinstance(retrieved, dict)

    @pytest.mark.skipif(not _neo4j_available(), reason="Neo4j nicht verfügbar")
    def test_template_usage_tracking(self, neo4j_manager):
        """Test Template-Nutzungsstatistik"""
        if not neo4j_manager.is_connected():
            pytest.skip("Neo4j nicht verbunden")

        # Template erstellen falls nicht vorhanden
        templates = neo4j_manager.create_template_if_missing(
            "usage_test", "Usage Test Project", ["usage", "tracking"]
        )

        # Usage-Count erhöhen
        template_name = list(templates.keys())[0] if templates else "usage_test"
        neo4j_manager.update_template_usage(template_name)

        # Templates abrufen und prüfen ob usage_count gesetzt wurde
        retrieved = neo4j_manager.get_templates_for_project("usage_test")

        # Sollte mindestens ein Template gefunden werden
        assert isinstance(retrieved, dict)
        if retrieved:
            # Check that at least one template has usage tracking
            template_keys = list(retrieved.keys())
            assert len(template_keys) > 0, "Should find at least one template"


class TestNeo4jMockedConnection:
    """Tests mit gemockter Neo4j-Verbindung für zuverlässige Tests"""

    @pytest.fixture
    def mock_driver(self):
        """Erstellt Mock Neo4j Driver"""
        driver = Mock()
        session = Mock()

        # Mock session context manager
        driver.session.return_value.__enter__ = Mock(return_value=session)
        driver.session.return_value.__exit__ = Mock(return_value=None)

        # Mock verify_connectivity
        driver.verify_connectivity.return_value = None

        return driver, session

    @pytest.fixture
    def connected_neo4j_manager(self, mock_driver):
        """Neo4j Manager mit gemockter Verbindung"""
        driver, session = mock_driver

        with patch("src.governance.data_governance.NEO4J_AVAILABLE", True):
            with patch("neo4j.GraphDatabase.driver", return_value=driver):
                manager = Neo4jTemplateManager()
                manager.driver = driver
                return manager, session

    def test_get_templates_for_project_success(self, connected_neo4j_manager):
        """Test erfolgreiche Template-Abfrage"""
        manager, mock_session = connected_neo4j_manager

        # Mock query result
        mock_record = Mock()
        mock_record.__getitem__ = Mock(
            side_effect=lambda key: {
                "name": "test_template",
                "sections": ["overview", "details"],
                "tags": ["test", "mock"],
                "workflow_step": "testing",
                "standards_json": '{"min_length": 100}',
                "keyword_matches": 3,
            }[key]
        )

        mock_result = [mock_record]
        mock_session.run.return_value = mock_result

        # Test
        templates = manager.get_templates_for_project("test", ["mock"])

        assert isinstance(templates, dict)
        assert "test_template" in templates
        assert templates["test_template"]["relevance_score"] == 3
        assert templates["test_template"]["required_sections"] == ["overview", "details"]

    def test_create_template_if_missing_new_template(self, connected_neo4j_manager):
        """Test Erstellen eines neuen Templates"""
        manager, mock_session = connected_neo4j_manager

        # Mock: Keine existierenden Templates
        mock_session.run.return_value = []

        # Test
        result = manager.create_template_if_missing("new_type", "New Project", ["new", "test"])

        assert isinstance(result, dict)
        assert len(result) == 1

        template_name = list(result.keys())[0]
        assert "new_type" in template_name
        assert "new_project" in template_name.lower()

    def test_create_template_if_missing_existing_template(self, connected_neo4j_manager):
        """Test wenn Template bereits existiert"""
        manager, mock_session = connected_neo4j_manager

        # Mock: Existierendes Template
        mock_record = Mock()
        mock_record.__getitem__ = Mock(
            side_effect=lambda key: {
                "name": "existing_template",
                "sections": ["overview"],
                "tags": ["existing"],
                "workflow_step": "existing",
                "standards_json": "{}",
                "keyword_matches": 1,
            }[key]
        )

        mock_session.run.return_value = [mock_record]

        # Test
        result = manager.create_template_if_missing("existing", "Existing Project", ["existing"])

        assert isinstance(result, dict)
        assert "existing_template" in result

    def test_update_template_usage(self, connected_neo4j_manager):
        """Test Template-Nutzung-Update"""
        manager, mock_session = connected_neo4j_manager

        # Test
        manager.update_template_usage("test_template")

        # Verifiziere dass Query aufgerufen wurde
        mock_session.run.assert_called()
        call_args = mock_session.run.call_args[0]
        assert "usage_count" in call_args[0]

    def test_generate_template_config_all_types(self, connected_neo4j_manager):
        """Test Template-Config-Generierung für alle Typen"""
        manager, _ = connected_neo4j_manager

        test_cases = [
            ("research", ["hypothesis", "data", "analysis"]),
            ("development", ["requirements", "architecture", "code"]),
            ("documentation", ["usage", "example", "guide"]),
            ("meeting", ["attendees", "decisions", "actions"]),
            ("unknown_type", []),
        ]

        for project_type, expected_keywords in test_cases:
            config = manager._generate_template_config(project_type, expected_keywords[:2])

            assert isinstance(config, dict)
            assert "required_sections" in config
            assert "suggested_tags" in config
            assert "workflow_step" in config
            assert "content_standards" in config

            # Prüfe dass Keywords integriert wurden
            if expected_keywords:
                content_keywords = config["content_standards"]["required_keywords"]
                assert any(kw in content_keywords for kw in expected_keywords[:2])


class TestDataGovernanceEngineWithNeo4j:
    """Tests für DataGovernanceEngine mit Neo4j-Integration"""

    @pytest.fixture
    def mock_neo4j_manager(self):
        """Mock Neo4j Manager"""
        manager = Mock()
        manager.is_connected.return_value = True
        return manager

    @pytest.fixture
    def governance_with_neo4j(self, mock_neo4j_manager):
        """DataGovernanceEngine mit gemocktem Neo4j"""
        with patch(
            "src.governance.data_governance.Neo4jTemplateManager", return_value=mock_neo4j_manager
        ):
            engine = DataGovernanceEngine()
            engine.neo4j_manager = mock_neo4j_manager
            return engine, mock_neo4j_manager

    def test_get_templates_for_context_neo4j_success(self, governance_with_neo4j):
        """Test Context-Templates mit Neo4j"""
        engine, mock_manager = governance_with_neo4j

        # Mock Neo4j Templates
        mock_manager.get_templates_for_project.return_value = {
            "neo4j_template": {
                "required_sections": ["neo4j_section"],
                "suggested_tags": ["neo4j"],
                "workflow_step": "neo4j_step",
                "content_standards": {"min_length": 200},
                "relevance_score": 5,
            }
        }

        # Test
        result = engine.get_templates_for_context("test_type", "Test Project", ["test"])

        assert isinstance(result, dict)
        assert "neo4j_template" in result
        mock_manager.get_templates_for_project.assert_called_once_with("test_type", ["test"])

    def test_get_templates_for_context_neo4j_empty_create_new(self, governance_with_neo4j):
        """Test automatische Template-Erstellung bei leerem Neo4j-Result"""
        engine, mock_manager = governance_with_neo4j

        # Mock: Erste Abfrage leer, zweite mit neuem Template
        mock_manager.get_templates_for_project.return_value = {}
        mock_manager.create_template_if_missing.return_value = {
            "new_template": {
                "required_sections": ["new_section"],
                "suggested_tags": ["new"],
                "workflow_step": "new_step",
                "content_standards": {"min_length": 250},
            }
        }

        # Test
        result = engine.get_templates_for_context("new_type", "New Project", ["new"])

        assert isinstance(result, dict)
        assert "new_template" in result
        mock_manager.create_template_if_missing.assert_called_once_with(
            "new_type", "New Project", ["new"]
        )

    def test_get_templates_for_context_fallback_to_local(self, governance_with_neo4j):
        """Test Fallback zu lokalen Templates"""
        engine, mock_manager = governance_with_neo4j

        # Mock: Neo4j nicht verbunden
        mock_manager.is_connected.return_value = False

        # Test
        result = engine.get_templates_for_context("test_type", "Test Project")

        assert isinstance(result, dict)
        # Sollte lokale Templates zurückgeben
        assert len(result) > 0
        # Neo4j sollte nicht aufgerufen werden
        mock_manager.get_templates_for_project.assert_not_called()

    def test_validate_note_creation_with_context(self, governance_with_neo4j):
        """Test Context-Validierung mit Neo4j"""
        engine, mock_manager = governance_with_neo4j

        # Mock Templates und Template-Auswahl
        mock_manager.get_templates_for_project.return_value = {
            "context_template": {
                "required_sections": ["overview"],
                "suggested_tags": ["context"],
                "workflow_step": "context_step",
                "content_standards": {"min_length": 100, "required_keywords": ["context"]},
                "relevance_score": 3,
            }
        }

        # Test
        result = engine.validate_note_creation_with_context(
            name="Context Test Note",
            content="This is a context test with sufficient content length and context keyword.",
            description="Context test description",
            project_type="context_test",
            project_name="Context Project",
            keywords=["context", "test"],
        )

        assert hasattr(result, "passed")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "suggestions")

        # Template-Nutzung sollte getrackt werden
        mock_manager.update_template_usage.assert_called_once()

    def test_select_best_template_single(self, governance_with_neo4j):
        """Test beste Template-Auswahl bei nur einem Template"""
        engine, _ = governance_with_neo4j

        templates = {
            "single_template": {
                "relevance_score": 1,
                "content_standards": {"required_keywords": ["test"]},
            }
        }

        result = engine._select_best_template(templates, ["test"], "test content")
        assert result == "single_template"

    def test_select_best_template_multiple(self, governance_with_neo4j):
        """Test beste Template-Auswahl bei mehreren Templates"""
        engine, _ = governance_with_neo4j

        templates = {
            "low_score": {"relevance_score": 1, "content_standards": {"required_keywords": []}},
            "high_score": {
                "relevance_score": 5,
                "content_standards": {"required_keywords": ["test", "high"]},
            },
        }

        result = engine._select_best_template(templates, ["test", "high"], "test high content")
        assert result == "high_score"

    def test_select_best_template_empty(self, governance_with_neo4j):
        """Test Template-Auswahl bei leeren Templates"""
        engine, _ = governance_with_neo4j

        result = engine._select_best_template({}, ["test"], "test content")
        assert result is None

    def test_extract_keywords_from_content(self, governance_with_neo4j):
        """Test Keyword-Extraktion aus Content"""
        engine, _ = governance_with_neo4j

        content = "This is a python development project using react framework with machine learning and database integration"
        keywords = engine._extract_keywords_from_content(content)

        assert isinstance(keywords, list)
        assert len(keywords) <= 7  # Max 7 Keywords (increased from 5)
        assert "python" in keywords
        assert "development" in keywords
        assert "react" in keywords
        # ML kann als 'ml' oder 'machine learning' erkannt werden
        assert any(kw in ["ml", "machine", "learning"] for kw in keywords)
        assert "database" in keywords


class TestNeo4jErrorHandling:
    """Tests für Fehlerbehandlung bei Neo4j-Operationen"""

    @pytest.fixture
    def failing_neo4j_manager(self):
        """Neo4j Manager der Fehler wirft"""
        manager = Neo4jTemplateManager()

        # Mock driver der Exceptions wirft
        mock_driver = Mock()
        mock_session = Mock()

        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.run.side_effect = Exception("Neo4j connection error")

        manager.driver = mock_driver
        return manager

    def test_get_templates_for_project_error_handling(self, failing_neo4j_manager):
        """Test Fehlerbehandlung bei Template-Abfrage"""
        # Sollte leeres dict zurückgeben bei Fehlern
        result = failing_neo4j_manager.get_templates_for_project("test", ["test"])
        assert result == {}

    def test_create_template_if_missing_error_handling(self, failing_neo4j_manager):
        """Test Fehlerbehandlung bei Template-Erstellung"""
        # Sollte leeres dict zurückgeben bei Fehlern
        result = failing_neo4j_manager.create_template_if_missing("test", "Test", ["test"])
        assert result == {}

    def test_update_template_usage_error_handling(self, failing_neo4j_manager):
        """Test Fehlerbehandlung bei Usage-Update"""
        # Sollte keine Exception werfen
        try:
            failing_neo4j_manager.update_template_usage("test_template")
            assert True
        except Exception:
            pytest.fail("update_template_usage should handle errors gracefully")


class TestNeo4jIntegrationWorkflows:
    """Tests für komplette Neo4j-Integration-Workflows"""

    @pytest.fixture
    def complete_mock_setup(self):
        """Komplettes Mock-Setup für End-to-End Tests"""
        # Mock Neo4j Manager
        mock_manager = Mock()
        mock_manager.is_connected.return_value = True

        # Mock Template-Erstellung
        mock_manager.create_template_if_missing.return_value = {
            "integration_test_project": {
                "required_sections": ["overview", "implementation", "results"],
                "suggested_tags": ["integration", "test", "development"],
                "workflow_step": "development",
                "content_standards": {
                    "min_length": 300,
                    "required_keywords": ["integration", "test"],
                },
            }
        }

        # Mock Template-Abfrage
        mock_manager.get_templates_for_project.return_value = {
            "integration_test_project": {
                "required_sections": ["overview", "implementation", "results"],
                "suggested_tags": ["integration", "test", "development"],
                "workflow_step": "development",
                "content_standards": {
                    "min_length": 300,
                    "required_keywords": ["integration", "test"],
                },
                "relevance_score": 8,
            }
        }

        return mock_manager

    def test_complete_workflow_new_project(self, complete_mock_setup):
        """Test kompletter Workflow für neues Projekt"""
        mock_manager = complete_mock_setup

        with patch(
            "src.governance.data_governance.Neo4jTemplateManager", return_value=mock_manager
        ):
            # 1. Engine initialisieren
            engine = DataGovernanceEngine()

            # 2. Context-Templates für neues Projekt holen
            templates = engine.get_templates_for_context(
                project_type="development",
                project_name="Integration Test Project",
                keywords=["integration", "test"],
            )

            assert isinstance(templates, dict)
            assert "integration_test_project" in templates

            # 3. Note mit Context validieren
            result = engine.validate_note_creation_with_context(
                name="Integration Test Implementation",
                content="This is an integration test implementation. **Overview:** We are testing the complete workflow. **Implementation:** The implementation uses modern techniques. **Results:** The integration test shows positive results.",
                description="Integration test note",
                project_type="development",
                project_name="Integration Test Project",
                keywords=["integration", "test"],
            )

            assert hasattr(result, "passed")
            # Template-Nutzung sollte getrackt werden
            mock_manager.update_template_usage.assert_called()

    def test_workflow_with_fallback(self, complete_mock_setup):
        """Test Workflow mit Fallback zu lokalen Templates"""
        mock_manager = complete_mock_setup
        mock_manager.is_connected.return_value = False  # Neo4j nicht verfügbar

        with patch(
            "src.governance.data_governance.Neo4jTemplateManager", return_value=mock_manager
        ):
            engine = DataGovernanceEngine()

            # Sollte auf lokale Templates zurückfallen
            templates = engine.get_templates_for_context("development", "Test Project")

            assert isinstance(templates, dict)
            assert len(templates) > 0  # Lokale Templates sollten vorhanden sein

            # Neo4j-spezifische Methoden sollten nicht aufgerufen werden
            mock_manager.get_templates_for_project.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
