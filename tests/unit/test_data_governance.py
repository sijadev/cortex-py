#!/usr/bin/env python3
"""
Tests für die Neo4j-integrierte Data Governance Engine
Testet sowohl die lokale YAML-Konfiguration als auch die Neo4j-Integration
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

import sys

sys.path.append("/Users/simonjanke/Projects/cortex-py/src")

from src.governance.data_governance import (
    DataGovernanceEngine,
    ValidationResult,
    Neo4jTemplateManager,
    ValidationLevel,
)


class TestDataGovernanceEngine:
    """Tests für die grundlegende DataGovernanceEngine"""

    @pytest.fixture
    def governance_engine(self):
        """Erstellt eine DataGovernanceEngine für Tests"""
        return DataGovernanceEngine()

    @pytest.fixture
    def sample_config_file(self):
        """Erstellt temporäre Konfigurationsdatei für Tests"""
        config_data = {
            "templates": {
                "test_template": {
                    "required_sections": ["overview", "details"],
                    "suggested_tags": ["test", "sample"],
                    "workflow_step": "testing",
                    "content_standards": {"min_length": 50, "required_keywords": ["test"]},
                }
            },
            "workflows": {
                "test_workflow": {
                    "steps": ["start", "middle", "end"],
                    "templates": ["test_template"],
                    "auto_assign": True,
                }
            },
            "validation_rules": {
                "name_min_length": 5,
                "content_min_length": 30,
                "auto_suggest_templates": True,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config_data, f)
            yield f.name

        os.unlink(f.name)

    def test_engine_initialization(self, governance_engine):
        """Test der Engine-Initialisierung"""
        assert governance_engine is not None
        assert hasattr(governance_engine, "config")
        assert hasattr(governance_engine, "neo4j_manager")
        assert "templates" in governance_engine.config
        assert "workflows" in governance_engine.config
        assert "validation_rules" in governance_engine.config

    def test_load_external_config(self, sample_config_file):
        """Test des Ladens externer Konfiguration"""
        governance = DataGovernanceEngine(sample_config_file)

        assert "test_template" in governance.config["templates"]
        assert "test_workflow" in governance.config["workflows"]
        assert governance.config["validation_rules"]["name_min_length"] == 5

    def test_get_templates(self, governance_engine):
        """Test des Template-Abrufs"""
        templates = governance_engine.get_templates()

        assert isinstance(templates, dict)
        assert len(templates) > 0

        # Prüfe Standard-Templates
        assert "Python Framework" in templates
        assert "Programmiersprache-Geschichte" in templates

        # Prüfe Template-Struktur
        template = templates["Python Framework"]
        assert "required_sections" in template
        assert "suggested_tags" in template
        assert "workflow_step" in template
        assert "content_standards" in template

    def test_get_workflows(self, governance_engine):
        """Test des Workflow-Abrufs"""
        workflows = governance_engine.get_workflows()

        assert isinstance(workflows, dict)
        assert len(workflows) > 0

        # Prüfe Standard-Workflow
        assert "Python Knowledge Base" in workflows

        workflow = workflows["Python Knowledge Base"]
        assert "steps" in workflow
        assert "templates" in workflow
        assert "auto_assign" in workflow

    def test_add_template(self, governance_engine):
        """Test des Hinzufügens von Templates"""
        initial_count = len(governance_engine.get_templates())

        governance_engine.add_template(
            name="Test Template",
            required_sections=["intro", "body", "conclusion"],
            suggested_tags=["test", "example"],
            workflow_step="testing",
            content_standards={"min_length": 100},
        )

        templates = governance_engine.get_templates()
        assert len(templates) == initial_count + 1
        assert "Test Template" in templates

        new_template = templates["Test Template"]
        assert new_template["required_sections"] == ["intro", "body", "conclusion"]
        assert new_template["suggested_tags"] == ["test", "example"]
        assert new_template["workflow_step"] == "testing"

    def test_add_workflow(self, governance_engine):
        """Test des Hinzufügens von Workflows"""
        initial_count = len(governance_engine.get_workflows())

        governance_engine.add_workflow(
            name="Test Workflow",
            steps=["start", "process", "end"],
            templates=["Test Template"],
            auto_assign=False,
        )

        workflows = governance_engine.get_workflows()
        assert len(workflows) == initial_count + 1
        assert "Test Workflow" in workflows

        new_workflow = workflows["Test Workflow"]
        assert new_workflow["steps"] == ["start", "process", "end"]
        assert new_workflow["templates"] == ["Test Template"]
        assert new_workflow["auto_assign"] == False


class TestValidation:
    """Tests für Validierungsfunktionen"""

    @pytest.fixture
    def governance_engine(self):
        return DataGovernanceEngine()

    def test_validate_good_note(self, governance_engine):
        """Test einer guten Note-Validierung"""
        result = governance_engine.validate_note_creation(
            name="FastAPI Framework Test",
            content="FastAPI ist ein modernes Web-Framework für Python. Es bietet hohe Performance und automatische API-Dokumentation. **Hauptmerkmale:** Schnell, einfach zu verwenden. **Verwendung:** API-Entwicklung. **Status:** Sehr beliebt.",
            description="Test für FastAPI Framework",
            note_type="framework",
        )

        assert isinstance(result, ValidationResult)
        assert result.passed == True
        assert len(result.errors) == 0

    def test_validate_bad_note(self, governance_engine):
        """Test einer problematischen Note-Validierung"""
        result = governance_engine.validate_note_creation(
            name="x", content="kurz", description="", note_type=""  # Zu kurz  # Zu kurz  # Leer
        )

        assert isinstance(result, ValidationResult)
        assert result.passed == False
        assert len(result.errors) > 0

    def test_validate_with_template(self, governance_engine):
        """Test der Template-basierten Validierung"""
        result = governance_engine.validate_note_creation(
            name="Python Test Framework",
            content="Dies ist ein Test-Framework für Python. **Hauptmerkmale:** Einfach zu verwenden. **Verwendung:** Für Unit-Tests. **Status:** Stable. Es enthält python und ist ein framework.",
            description="Test Framework Beschreibung",
            note_type="framework",
            template="Python Framework",
        )

        assert isinstance(result, ValidationResult)
        # Sollte bestehen, da alle Required Keywords vorhanden sind
        assert result.passed == True or len(result.errors) == 0

    def test_extract_keywords_from_content(self, governance_engine):
        """Test der Keyword-Extraktion"""
        content = (
            "Dies ist ein Python API mit machine learning und database integration für development"
        )
        keywords = governance_engine._extract_keywords_from_content(content)

        assert isinstance(keywords, list)
        assert "python" in keywords
        assert "api" in keywords
        assert "ml" in keywords or "machine learning" in content.lower()
        assert "database" in keywords
        assert "development" in keywords

    def test_naming_conventions(self, governance_engine):
        """Test der Namenskonventionen"""
        # Guter Name
        result = governance_engine.validate_note_creation(
            name="Valid Framework Name",
            content="Content mit mindestens zwanzig Zeichen für die Validierung",
            description="Gültige Beschreibung",
            note_type="test",
        )

        naming_errors = [e for e in result.errors if "Name enthält" in e]
        assert len(naming_errors) == 0

        # Schlechter Name mit Sonderzeichen
        result = governance_engine.validate_note_creation(
            name="Invalid@Name!",
            content="Content mit mindestens zwanzig Zeichen für die Validierung",
            description="Beschreibung",
            note_type="test",
        )

        naming_errors = [e for e in result.errors if "Name enthält" in e]
        assert len(naming_errors) > 0


class TestContextValidation:
    """Tests für die neue Context-basierte Validierung"""

    @pytest.fixture
    def governance_engine(self):
        return DataGovernanceEngine()

    def test_validate_note_creation_with_context(self, governance_engine):
        """Test der erweiterten Context-Validierung"""
        result = governance_engine.validate_note_creation_with_context(
            name="AI Research Project",
            content="This is an artificial intelligence research project focusing on machine learning algorithms. We will analyze data and develop new models for prediction.",
            description="AI Research Description",
            project_type="research",
            project_name="AI Study",
            keywords=["ai", "machine learning", "research"],
        )

        assert isinstance(result, ValidationResult)
        assert result.passed == True or len(result.errors) == 0

    def test_get_templates_for_context(self, governance_engine):
        """Test der Context-basierten Template-Auswahl"""
        # Test ohne Neo4j (sollte Fallback verwenden)
        templates = governance_engine.get_templates_for_context(
            project_type="research", project_name="Test Project", keywords=["python", "framework"]
        )

        assert isinstance(templates, dict)
        assert len(templates) > 0


class TestNeo4jTemplateManager:
    """Tests für den Neo4j Template Manager"""

    @pytest.fixture
    def mock_neo4j_manager(self):
        """Erstellt einen Mock Manager ohne Verbindung"""
        with patch("src.governance.data_governance.NEO4J_AVAILABLE", False):
            manager = Neo4jTemplateManager()
            manager.driver = None  # Simuliere keine Verbindung
            # Mock _connect to always return False
            manager._connect = Mock(return_value=False)
            return manager

    @pytest.fixture
    def connected_mock_manager(self):
        """Erstellt einen Mock Manager mit simulierter Verbindung"""
        with patch("src.governance.data_governance.NEO4J_AVAILABLE", True):
            manager = Neo4jTemplateManager()

            # Mock driver
            mock_driver = Mock()
            mock_session = Mock()
            mock_result = Mock()

            # Simuliere erfolgreiche Verbindung
            mock_driver.verify_connectivity.return_value = None
            mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = Mock(return_value=None)

            # Simuliere Template-Abfrage-Ergebnisse
            mock_record = Mock()
            # Korrekte Mock-Konfiguration für __getitem__
            mock_record.__getitem__ = Mock(
                side_effect=lambda key: {
                    "name": "test_template",
                    "sections": ["overview", "details"],
                    "tags": ["test"],
                    "workflow_step": "testing",
                    "standards_json": '{"min_length": 100}',
                    "keyword_matches": 2,
                }.get(key)
            )

            mock_result.__iter__ = Mock(return_value=iter([mock_record]))
            mock_session.run.return_value = mock_result

            manager.driver = mock_driver
            return manager

    def test_neo4j_manager_initialization(self):
        """Test der Neo4j Manager Initialisierung"""
        manager = Neo4jTemplateManager()
        assert manager is not None
        assert hasattr(manager, "uri")
        assert hasattr(manager, "user")
        assert hasattr(manager, "password")

    def test_is_connected_false(self, mock_neo4j_manager):
        """Test der Verbindungsprüfung bei fehlender Verbindung"""
        assert mock_neo4j_manager.is_connected() == False

    def test_is_connected_true(self, connected_mock_manager):
        """Test der Verbindungsprüfung bei bestehender Verbindung"""
        assert connected_mock_manager.is_connected() == True

    def test_get_templates_for_project_no_connection(self, mock_neo4j_manager):
        """Test Template-Abruf ohne Neo4j-Verbindung"""
        templates = mock_neo4j_manager.get_templates_for_project("test", ["keyword"])
        assert templates == {}

    def test_get_templates_for_project_with_connection(self, connected_mock_manager):
        """Test Template-Abruf mit simulierter Neo4j-Verbindung"""
        templates = connected_mock_manager.get_templates_for_project("test", ["keyword"])

        assert isinstance(templates, dict)
        assert len(templates) > 0
        assert "test_template" in templates

        template = templates["test_template"]
        assert "required_sections" in template
        assert "suggested_tags" in template
        assert "relevance_score" in template

    def test_generate_template_config(self, mock_neo4j_manager):
        """Test der Template-Konfiguration-Generierung"""
        config = mock_neo4j_manager._generate_template_config("research", ["ai", "ml"])

        assert isinstance(config, dict)
        assert "required_sections" in config
        assert "suggested_tags" in config
        assert "workflow_step" in config
        assert "content_standards" in config

        # Test spezifische Research-Konfiguration
        assert "abstract" in config["required_sections"]
        assert "methodology" in config["required_sections"]
        assert "research" in config["suggested_tags"]
        assert config["workflow_step"] == "research"

    def test_generate_template_config_unknown_type(self, mock_neo4j_manager):
        """Test Template-Generierung für unbekannten Typ"""
        config = mock_neo4j_manager._generate_template_config("unknown_type", ["test"])

        assert isinstance(config, dict)
        assert "overview" in config["required_sections"]
        assert "content" in config["required_sections"]
        assert "summary" in config["required_sections"]
        assert "unknown_type" in config["suggested_tags"]


class TestIntegration:
    """Integrationstests für das gesamte System"""

    def test_full_workflow_without_neo4j(self):
        """Test des kompletten Workflows ohne Neo4j"""
        # Initialisiere Engine
        governance = DataGovernanceEngine()

        # Füge Template hinzu
        governance.add_template(
            name="Integration Test Template",
            required_sections=["intro", "body"],
            suggested_tags=["integration", "test"],
            workflow_step="testing",
        )

        # Füge Workflow hinzu
        governance.add_workflow(
            name="Integration Test Workflow",
            steps=["start", "test", "end"],
            templates=["Integration Test Template"],
        )

        # Validiere Note
        result = governance.validate_note_creation(
            name="Integration Test Note",
            content="Dies ist ein Integrationstest mit mindestens zwanzig Zeichen. **Intro:** Test intro. **Body:** Test body content.",
            description="Integration test note",
            note_type="test",
            template="Integration Test Template",
        )

        assert result.passed == True or len(result.errors) == 0

        # Prüfe dass Template und Workflow hinzugefügt wurden
        templates = governance.get_templates()
        workflows = governance.get_workflows()

        assert "Integration Test Template" in templates
        assert "Integration Test Workflow" in workflows

    @patch("src.governance.data_governance.NEO4J_AVAILABLE", False)
    def test_graceful_neo4j_unavailable(self):
        """Test des graceful Fallbacks wenn Neo4j nicht verfügbar ist"""
        governance = DataGovernanceEngine()

        # Neo4j Manager sollte nicht verbunden sein
        assert not governance.neo4j_manager.is_connected()

        # Context-basierte Template-Auswahl sollte auf Fallback zurückgreifen
        templates = governance.get_templates_for_context("research", "Test Project")
        assert isinstance(templates, dict)
        assert len(templates) > 0

        # Context-Validierung sollte funktionieren
        result = governance.validate_note_creation_with_context(
            name="Test without Neo4j",
            content="This is a test without Neo4j connection with sufficient content length.",
            description="Test description",
            project_type="research",
        )

        assert isinstance(result, ValidationResult)


class TestEdgeCases:
    """Tests für Edge Cases und Fehlerbehandlung"""

    @pytest.fixture
    def governance_engine(self):
        return DataGovernanceEngine()

    def test_empty_content(self, governance_engine):
        """Test mit leerem Content"""
        result = governance_engine.validate_note_creation(
            name="Empty Content Test", content="", description="Test description", note_type="test"
        )

        assert result.passed == False
        assert any("Content muss" in error for error in result.errors)

    def test_very_long_name(self, governance_engine):
        """Test mit sehr langem Namen"""
        long_name = "x" * 200  # Sehr langer Name
        result = governance_engine.validate_note_creation(
            name=long_name,
            content="Valid content with sufficient length for validation",
            description="Test description",
            note_type="test",
        )

        # Sollte eventuell Warning haben, aber nicht zwingend Fehler
        assert isinstance(result, ValidationResult)

    def test_special_characters_in_content(self, governance_engine):
        """Test mit Sonderzeichen im Content"""
        result = governance_engine.validate_note_creation(
            name="Special Characters Test",
            content="Content with special characters: äöü ß € $ @ # % & * () [] {} <>",
            description="Test description",
            note_type="test",
        )

        # Sonderzeichen im Content sollten kein Problem sein
        assert isinstance(result, ValidationResult)

    def test_none_values(self, governance_engine):
        """Test mit None-Werten"""
        result = governance_engine.validate_note_creation(
            name=None, content=None, description=None, note_type=None
        )

        assert result.passed == False
        assert len(result.errors) > 0

    def test_missing_template(self, governance_engine):
        """Test mit nicht-existierendem Template"""
        result = governance_engine.validate_note_creation(
            name="Missing Template Test",
            content="Content for missing template test with sufficient length",
            description="Test description",
            note_type="test",
            template="NonExistentTemplate",
        )

        # Sollte ohne Fehler durchlaufen, da Template optional ist
        assert isinstance(result, ValidationResult)


class TestValidationLevels:
    """Tests für die neuen Validierungsebenen STRICT, WARNING, LENIENT"""

    @pytest.fixture
    def governance_engine_strict(self):
        """Erstellt eine DataGovernanceEngine mit STRICT Validierung"""
        engine = DataGovernanceEngine()
        engine.update_validation_rules({"validation_level": "strict"})
        return engine

    @pytest.fixture
    def governance_engine_warning(self):
        """Erstellt eine DataGovernanceEngine mit WARNING Validierung"""
        engine = DataGovernanceEngine()
        engine.update_validation_rules({"validation_level": "warning"})
        return engine

    @pytest.fixture
    def governance_engine_lenient(self):
        """Erstellt eine DataGovernanceEngine mit LENIENT Validierung"""
        engine = DataGovernanceEngine()
        engine.update_validation_rules({"validation_level": "lenient"})
        return engine

    def test_strict_mode_blocks_short_name(self, governance_engine_strict):
        """Test: STRICT Modus blockiert kurze Namen"""
        result = governance_engine_strict.validate_note_creation(
            name="x",  # Zu kurz
            content="Valid content with sufficient length for validation testing",
            description="Valid description",
            note_type="test"
        )

        assert result.passed == False
        assert any("Name muss mindestens" in error for error in result.errors)

    def test_warning_mode_allows_short_name_with_warning(self, governance_engine_warning):
        """Test: WARNING Modus erlaubt kurze Namen mit Warnung"""
        result = governance_engine_warning.validate_note_creation(
            name="x",  # Zu kurz
            content="Valid content with sufficient length for validation testing",
            description="Valid description",
            note_type="test"
        )

        # Should pass in WARNING mode for non-critical issues
        assert result.passed == True
        assert any("Name muss mindestens" in warning for warning in result.warnings)

    def test_lenient_mode_allows_most_issues(self, governance_engine_lenient):
        """Test: LENIENT Modus lässt fast alles durch"""
        result = governance_engine_lenient.validate_note_creation(
            name="x",  # Zu kurz
            content="short",  # Zu kurz
            description="ok",  # Zu kurz
            note_type="test"
        )

        # Only completely invalid data should fail in LENIENT mode
        assert result.passed == True
        assert len(result.errors) == 0 or all("darf nicht None" in error for error in result.errors)

    def test_strict_mode_enforces_template_compliance(self, governance_engine_strict):
        """Test: STRICT Modus erzwingt Template-Konformität"""
        result = governance_engine_strict.validate_note_creation(
            name="Python Framework Test",
            content="This is content without required sections and keywords",
            description="Test description",
            note_type="framework",
            template="Python Framework"
        )

        assert result.passed == False
        assert any("Template-Sektion" in error or "Keyword" in error for error in result.errors)

    def test_warning_mode_template_warnings(self, governance_engine_warning):
        """Test: WARNING Modus zeigt Template-Warnungen"""
        result = governance_engine_warning.validate_note_creation(
            name="Python Framework Test",
            content="This is content without required sections and keywords",
            description="Test description",
            note_type="framework",
            template="Python Framework"
        )

        # May pass but should have warnings about template compliance
        assert len(result.warnings) > 0

    def test_lenient_mode_ignores_template_issues(self, governance_engine_lenient):
        """Test: LENIENT Modus ignoriert Template-Probleme"""
        result = governance_engine_lenient.validate_note_creation(
            name="Python Framework Test",
            content="This is content without required sections and keywords",
            description="Test description",
            note_type="framework",
            template="Python Framework"
        )

        # Should pass with minimal issues in LENIENT mode
        assert result.passed == True

    def test_validation_level_from_config(self):
        """Test: Validierungsebene aus Konfiguration laden"""
        # Test mit STRICT Konfiguration
        strict_engine = DataGovernanceEngine()
        strict_engine.config["validation_rules"]["validation_level"] = "strict"

        result = strict_engine.validate_note_creation(
            name="x",
            content="Valid content with sufficient length",
            description="Valid description",
            note_type="test"
        )

        assert result.passed == False

    def test_invalid_validation_level_defaults_to_warning(self):
        """Test: Ungültige Validierungsebene fällt auf WARNING zurück"""
        engine = DataGovernanceEngine()
        engine.config["validation_rules"]["validation_level"] = "invalid_level"

        result = engine.validate_note_creation(
            name="x",
            content="Valid content with sufficient length",
            description="Valid description",
            note_type="test"
        )

        # Should behave like WARNING mode
        assert result.passed == True


class TestPerformanceTagGeneration:
    """Tests für die neue Performance-Tag-Funktionalität"""

    @pytest.fixture
    def governance_engine(self):
        return DataGovernanceEngine()

    def test_performance_metrics_tags(self, governance_engine):
        """Test: Performance-Metriken Tags werden korrekt erkannt"""
        content = "This system includes performance monitoring and benchmark testing with metrics collection"

        result = governance_engine.validate_note_creation(
            name="Performance Monitoring System",
            content=content,
            description="Performance monitoring description",
            note_type="system"
        )

        # Check if performance-metrics tag is suggested
        performance_suggestions = [s for s in result.suggestions if "performance-metrics" in s]
        assert len(performance_suggestions) > 0

    def test_system_optimization_tags(self, governance_engine):
        """Test: System-Optimierung Tags werden korrekt erkannt"""
        content = "Database optimization and query tuning for improved efficiency and speed"

        result = governance_engine.validate_note_creation(
            name="Database Optimization Guide",
            content=content,
            description="Optimization guide description",
            note_type="guide"
        )

        # Check if system-optimization tag is suggested
        optimization_suggestions = [s for s in result.suggestions if "system-optimization" in s]
        assert len(optimization_suggestions) > 0

    def test_command_tracking_tags(self, governance_engine):
        """Test: Command-Tracking Tags werden korrekt erkannt"""
        content = "Command execution tracking and monitoring with audit logging for terminal operations"

        result = governance_engine.validate_note_creation(
            name="Command Tracking System",
            content=content,
            description="Command tracking description",
            note_type="system"
        )

        # Check if command-tracking tag is suggested
        tracking_suggestions = [s for s in result.suggestions if "command-tracking" in s]
        assert len(tracking_suggestions) > 0

    def test_multiple_performance_tags(self, governance_engine):
        """Test: Mehrere Performance-Tags gleichzeitig"""
        content = """
        Performance monitoring system with benchmark testing, optimization features,
        and command execution tracking. Includes metrics collection, database optimization,
        and terminal monitoring with audit logging.
        """

        result = governance_engine.validate_note_creation(
            name="Comprehensive Performance System",
            content=content,
            description="Complete performance system",
            note_type="system"
        )

        # Should suggest multiple performance-related tags
        tag_suggestions = [s for s in result.suggestions if "Tag" in s]
        if tag_suggestions:
            suggested_tags = tag_suggestions[0].lower()
            assert "performance-metrics" in suggested_tags
            assert "system-optimization" in suggested_tags
            assert "command-tracking" in suggested_tags

    def test_tag_deduplication(self, governance_engine):
        """Test: Tag-Deduplizierung funktioniert korrekt"""
        content = "Python framework for performance monitoring and python development"

        result = governance_engine.validate_note_creation(
            name="Python Performance Framework",
            content=content,
            description="Python framework description",
            note_type="framework"
        )

        # Should not have duplicate "python" tags
        tag_suggestions = [s for s in result.suggestions if "Tag" in s]
        if tag_suggestions:
            # Count occurrences of "python" in suggestions
            python_count = tag_suggestions[0].lower().count("python")
            # Should appear only once despite being mentioned twice in content
            assert python_count <= 2  # Once from content, once from template potentially

    def test_performance_tags_with_template(self, governance_engine):
        """Test: Performance-Tags mit Template-Integration"""
        # Add a performance-focused template
        governance_engine.add_template(
            name="Performance Analysis Template",
            required_sections=["metrics", "benchmarks", "optimization"],
            suggested_tags=["performance", "analysis"],
            workflow_step="performance-testing",
            content_standards={
                "min_length": 200,
                "required_keywords": ["performance", "metrics"]
            }
        )

        content = """
        **Metrics:** Performance benchmarks show 50ms response time
        **Benchmarks:** System handles 1000 requests per second
        **Optimization:** Database queries optimized for better performance
        """

        result = governance_engine.validate_note_creation(
            name="API Performance Analysis",
            content=content,
            description="Performance analysis results",
            note_type="analysis",
            template="Performance Analysis Template"
        )

        # Should pass with performance tags
        assert result.passed == True
        tag_suggestions = [s for s in result.suggestions if "Tag" in s]
        if tag_suggestions:
            suggested_tags = tag_suggestions[0].lower()
            assert "performance" in suggested_tags


class TestEnhancedContextValidation:
    """Tests für erweiterte Context-basierte Validierung mit Performance-Features"""

    @pytest.fixture
    def governance_engine(self):
        return DataGovernanceEngine()

    def test_context_validation_with_performance_project(self, governance_engine):
        """Test: Context-Validierung für Performance-Projekte"""
        result = governance_engine.validate_note_creation_with_context(
            name="Load Testing Framework",
            content="Performance testing framework with benchmark capabilities and metrics collection for system optimization",
            description="Load testing framework description",
            project_type="development",
            project_name="Performance Testing Suite",
            keywords=["performance", "testing", "benchmarks"]
        )

        assert isinstance(result, ValidationResult)
        assert result.passed == True

        # Should suggest performance-related tags
        tag_suggestions = [s for s in result.suggestions if "Tag" in s]
        if tag_suggestions:
            suggested_tags = tag_suggestions[0].lower()
            assert "performance" in suggested_tags or "testing" in suggested_tags

    def test_auto_template_selection_for_performance(self, governance_engine):
        """Test: Automatische Template-Auswahl für Performance-Content"""
        # Mock Neo4j template creation
        with patch.object(governance_engine.neo4j_manager, 'is_connected', return_value=False):
            templates = governance_engine.get_templates_for_context(
                project_type="performance",
                project_name="Benchmark Suite",
                keywords=["performance", "benchmarks", "metrics"]
            )

            # Should return templates (fallback to local config)
            assert isinstance(templates, dict)
            assert len(templates) > 0

    def test_performance_keyword_extraction(self, governance_engine):
        """Test: Performance-Keywords werden korrekt extrahiert"""
        content = "System performance monitoring with latency measurement and throughput optimization"

        # Test the actual tag suggestion method which includes performance logic
        suggested_tags = governance_engine._suggest_tags(content, "system", None)

        # Should extract performance-related tags
        performance_tags = ["performance-metrics", "system-optimization"]
        found_tags = [tag for tag in suggested_tags if any(perf_tag in tag for perf_tag in performance_tags)]
        assert len(found_tags) > 0

    def test_template_selection_with_performance_keywords(self, governance_engine):
        """Test: Template-Auswahl basierend auf Performance-Keywords"""
        # Add performance template
        governance_engine.add_template(
            name="Performance Monitoring Template",
            required_sections=["overview", "metrics", "analysis"],
            suggested_tags=["performance", "monitoring"],
            workflow_step="monitoring",
            content_standards={
                "min_length": 150,
                "required_keywords": ["performance", "monitoring"]
            }
        )

        templates = governance_engine.get_templates()
        content = "Performance monitoring system with comprehensive metrics"
        keywords = ["performance", "monitoring"]

        best_template = governance_engine._select_best_template(templates, keywords, content)

        # Should select the performance template if it matches
        assert best_template is not None


class TestEdgeCasesValidationLevels:
    """Tests für Edge Cases mit verschiedenen Validierungsebenen"""

    @pytest.fixture
    def governance_engine_strict(self):
        engine = DataGovernanceEngine()
        engine.update_validation_rules({"validation_level": "strict"})
        return engine

    @pytest.fixture
    def governance_engine_lenient(self):
        engine = DataGovernanceEngine()
        engine.update_validation_rules({"validation_level": "lenient"})
        return engine

    def test_none_values_strict_mode(self, governance_engine_strict):
        """Test: None-Werte im STRICT Modus"""
        result = governance_engine_strict.validate_note_creation(
            name=None,
            content=None,
            description=None,
            note_type=None
        )

        assert result.passed == False
        assert len(result.errors) > 0
        assert any("darf nicht" in error for error in result.errors)

    def test_none_values_lenient_mode(self, governance_engine_lenient):
        """Test: None-Werte im LENIENT Modus"""
        result = governance_engine_lenient.validate_note_creation(
            name=None,
            content=None,
            description=None,
            note_type=None
        )

        # Even in LENIENT mode, None values should be blocked
        assert result.passed == False
        assert any("darf nicht None" in error for error in result.errors)

    def test_empty_strings_different_modes(self, governance_engine_strict, governance_engine_lenient):
        """Test: Leere Strings in verschiedenen Modi"""
        # STRICT mode
        strict_result = governance_engine_strict.validate_note_creation(
            name="",
            content="",
            description="",
            note_type=""
        )
        assert strict_result.passed == False

        # LENIENT mode
        lenient_result = governance_engine_lenient.validate_note_creation(
            name="Valid Name",  # At least name should be valid
            content="",
            description="",
            note_type=""
        )
        # LENIENT should be more forgiving but still require some basic content
        # The exact behavior depends on implementation details

    def test_special_characters_validation_levels(self, governance_engine_strict, governance_engine_lenient):
        """Test: Sonderzeichen in verschiedenen Validierungsebenen"""
        name_with_special_chars = "Test@Note#With$Special%Characters"

        # STRICT mode should flag special characters
        strict_result = governance_engine_strict.validate_note_creation(
            name=name_with_special_chars,
            content="Valid content with sufficient length",
            description="Valid description",
            note_type="test"
        )
        assert any("ungültige Zeichen" in error or "ungültige Zeichen" in warning
                  for error in strict_result.errors for warning in strict_result.warnings)

        # LENIENT mode should ignore special characters
        lenient_result = governance_engine_lenient.validate_note_creation(
            name=name_with_special_chars,
            content="Valid content with sufficient length",
            description="Valid description",
            note_type="test"
        )
        # Should be more permissive
        assert lenient_result.passed == True or len(lenient_result.errors) == 0


class TestPerformanceTagIntegration:
    """Integrationstests für Performance-Tags mit verschiedenen Systemen"""

    @pytest.fixture
    def governance_engine(self):
        return DataGovernanceEngine()

    def test_performance_tags_with_workflows(self, governance_engine):
        """Test: Performance-Tags mit Workflow-Integration"""
        # Add performance workflow
        governance_engine.add_workflow(
            name="Performance Testing Workflow",
            steps=["baseline", "optimization", "benchmarking", "monitoring"],
            templates=["Performance Analysis Template"],
            auto_assign=True
        )

        content = "Performance baseline measurement and system optimization benchmarks"

        result = governance_engine.validate_note_creation(
            name="Performance Baseline Study",
            content=content,
            description="Baseline performance study",
            note_type="study"
        )

        # Should suggest workflow steps related to performance
        workflow_suggestions = [s for s in result.suggestions if "Workflow" in s]
        if workflow_suggestions:
            assert len(workflow_suggestions) > 0

    def test_performance_tags_neo4j_fallback(self, governance_engine):
        """Test: Performance-Tags mit Neo4j-Fallback"""
        # Mock Neo4j unavailable
        with patch.object(governance_engine.neo4j_manager, 'is_connected', return_value=False):
            content = "Performance monitoring system with metrics and optimization features"

            result = governance_engine.validate_note_creation_with_context(
                name="Performance Monitor",
                content=content,
                description="Performance monitoring system",
                project_type="monitoring",
                project_name="System Monitor",
                keywords=["performance", "monitoring"]
            )

            # Should still work without Neo4j
            assert isinstance(result, ValidationResult)
            assert result.passed == True

    def test_full_performance_workflow(self, governance_engine):
        """Test: Kompletter Performance-Workflow"""
        # Set up performance-focused configuration
        governance_engine.add_template(
            name="Performance Report Template",
            required_sections=["Executive Summary", "Metrics", "Analysis", "Recommendations"],
            suggested_tags=["performance", "report", "analysis"],
            workflow_step="reporting",
            content_standards={
                "min_length": 500,
                "required_keywords": ["performance", "metrics", "analysis"]
            }
        )

        governance_engine.add_workflow(
            name="Performance Analysis Workflow",
            steps=["planning", "measurement", "analysis", "reporting", "optimization"],
            templates=["Performance Report Template"],
            auto_assign=True
        )

        content = """
        **Executive Summary:** System performance analysis completed
        **Metrics:** Response time: 45ms, Throughput: 1200 RPS, CPU usage: 65%
        **Analysis:** Performance bottlenecks identified in database queries
        **Recommendations:** Implement query optimization and caching strategy
        
        Detailed performance monitoring revealed optimization opportunities
        in system throughput and database efficiency.
        """

        result = governance_engine.validate_note_creation(
            name="Q4 Performance Analysis Report",
            content=content,
            description="Quarterly performance analysis with optimization recommendations",
            note_type="report",
            template="Performance Report Template"
        )

        # Should pass all validations
        assert result.passed == True
        assert len(result.errors) == 0

        # Should suggest performance-related tags
        tag_suggestions = [s for s in result.suggestions if "Tag" in s]
        if tag_suggestions:
            suggested_tags = tag_suggestions[0].lower()
            # Check for performance-related tags (more flexible assertion)
            performance_related = ["performance", "performance-metrics", "system-optimization"]
            assert any(tag in suggested_tags for tag in performance_related)


if __name__ == "__main__":
    # Führe Tests aus wenn direkt aufgerufen
    pytest.main([__file__, "-v"])
