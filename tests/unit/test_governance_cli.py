#!/usr/bin/env python3
"""
Tests für die Governance CLI mit Neo4j-Integration
Testet alle CLI-Kommandos und deren Integration mit der DataGovernanceEngine
"""

import pytest
import os
import tempfile
import yaml
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.append('/Users/simonjanke/Projects/cortex-py')
sys.path.append('/Users/simonjanke/Projects/cortex-py/src')

from src.governance.governance_cli import cli
from src.governance.data_governance import DataGovernanceEngine, ValidationResult

@pytest.fixture
def sample_content_file():
    """Erstellt temporäre Content-Datei für CLI-Tests"""
    content = """# Python Framework Test

    **Hauptmerkmale:** Dies ist ein Test-Framework für Python mit hervorragenden Funktionen.
    **Verwendung:** Wird für Entwicklungstest verwendet.
    **Status:** Aktiv und sehr beliebt.
    
    Dieses Framework bietet python-spezifische Funktionalitäten für moderne Entwicklung."""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        yield f.name

    os.unlink(f.name)

@pytest.fixture
def sample_config():
    """Temporäre Test-Konfigurationsdatei"""
    config_data = {
        'templates': {
            'cli_test_template': {
                'required_sections': ['overview', 'details'],
                'suggested_tags': ['cli', 'test'],
                'workflow_step': 'testing',
                'content_standards': {
                    'min_length': 50,
                    'required_keywords': ['test']
                }
            }
        },
        'workflows': {
            'cli_test_workflow': {
                'steps': ['start', 'process', 'end'],
                'templates': ['cli_test_template'],
                'auto_assign': True
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        yield f.name
    os.unlink(f.name)

class TestGovernanceCLI:
    """Tests für die grundlegenden CLI-Funktionen"""

    @pytest.fixture
    def runner(self):
        """Click Test Runner"""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test der CLI-Hilfe"""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert '🛡️ Data Governance CLI' in result.output
        assert 'templates' in result.output
        assert 'workflows' in result.output
        assert 'rules' in result.output
        assert 'system' in result.output
        assert 'test' in result.output

class TestTemplatesCommands:
    """Tests für Template-Kommandos"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_templates_help(self, runner):
        """Test der Templates-Hilfe"""
        result = runner.invoke(cli, ['templates', '--help'])
        assert result.exit_code == 0
        assert 'Template-Management' in result.output

    def test_templates_list(self, runner):
        """Test des Template-Listens"""
        result = runner.invoke(cli, ['templates', 'list'])
        assert result.exit_code == 0
        assert '📋 Verfügbare Templates:' in result.output
        assert 'Python Framework' in result.output
        assert 'Programmiersprache-Geschichte' in result.output

    def test_templates_list_with_filters(self, runner):
        """Test des gefilterten Template-Listens"""
        result = runner.invoke(cli, ['templates', 'list', '--project-type', 'research'])
        assert result.exit_code == 0
        assert '🎯 Gefiltert nach Projekt-Typ: research' in result.output

        result = runner.invoke(cli, ['templates', 'list', '--keywords', 'python,framework'])
        assert result.exit_code == 0
        assert '🔑 Gefiltert nach Keywords: python,framework' in result.output

    def test_templates_validate(self, runner, sample_content_file):
        """Test der Template-Validierung"""
        result = runner.invoke(cli, [
            'templates', 'validate',
            'Python Framework',
            sample_content_file
        ])
        assert result.exit_code == 0
        assert '🔍 Validierung' in result.output

    def test_templates_validate_smart(self, runner, sample_content_file):
        """Test der intelligenten Template-Validierung"""
        result = runner.invoke(cli, [
            'templates', 'validate-smart',
            sample_content_file,
            '--project-type', 'research',
            '--project-name', 'Test Project',
            '--keywords', 'test,validation'
        ])
        assert result.exit_code == 0
        assert '🤖 Intelligente Template-Validierung' in result.output
        assert '🎯 Projekt-Typ: research' in result.output
        assert '📂 Projekt: Test Project' in result.output

    @patch('src.governance.governance_cli.DataGovernanceEngine')
    def test_templates_create_for_project_with_neo4j(self, mock_governance_class, runner):
        """Test der automatischen Template-Erstellung"""
        # Mock der DataGovernanceEngine
        mock_governance = Mock()
        mock_neo4j_manager = Mock()
        mock_neo4j_manager.is_connected.return_value = True
        mock_neo4j_manager.create_template_if_missing.return_value = {
            'research_test_project': {
                'required_sections': ['abstract', 'methodology'],
                'suggested_tags': ['research', 'test'],
                'workflow_step': 'research'
            }
        }
        mock_governance.neo4j_manager = mock_neo4j_manager
        mock_governance_class.return_value = mock_governance

        result = runner.invoke(cli, [
            'templates', 'create-for-project',
            'research', 'Test Project',
            '--keywords', 'ai,ml'
        ])

        assert result.exit_code == 0
        assert '🚀 Erstelle Template für Projekt: Test Project' in result.output
        assert '✅ Template erfolgreich erstellt!' in result.output

    @patch('src.governance.governance_cli.DataGovernanceEngine')
    def test_templates_create_for_project_no_neo4j(self, mock_governance_class, runner):
        """Test der Template-Erstellung ohne Neo4j"""
        mock_governance = Mock()
        mock_neo4j_manager = Mock()
        mock_neo4j_manager.is_connected.return_value = False
        mock_governance.neo4j_manager = mock_neo4j_manager
        mock_governance_class.return_value = mock_governance

        result = runner.invoke(cli, [
            'templates', 'create-for-project',
            'research', 'Test Project'
        ])

        assert result.exit_code == 0
        assert '❌ Neo4j nicht verfügbar' in result.output

    def test_templates_add(self, runner):
        """Test des Template-Hinzufügens"""
        with patch('src.governance.governance_cli.save_to_config_file'):
            with patch('click.confirm', return_value=False):
                result = runner.invoke(cli, [
                    'templates', 'add', 'CLI Test Template',
                    '--sections', 'intro,body,conclusion',
                    '--tags', 'cli,test',
                    '--workflow-step', 'testing',
                    '--min-length', '100',
                    '--keywords', 'cli,test'
                ])

                assert result.exit_code == 0
                assert '✅ Template \'CLI Test Template\' erfolgreich hinzugefügt' in result.output

class TestWorkflowCommands:
    """Tests für Workflow-Kommandos"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_workflows_list(self, runner):
        """Test des Workflow-Listens"""
        result = runner.invoke(cli, ['workflows', 'list'])
        assert result.exit_code == 0
        assert '🔄 Verfügbare Workflows:' in result.output
        assert 'Python Knowledge Base' in result.output

    def test_workflows_add(self, runner):
        """Test des Workflow-Hinzufügens"""
        with patch('src.governance.governance_cli.save_to_config_file'):
            with patch('click.confirm', return_value=False):
                result = runner.invoke(cli, [
                    'workflows', 'add', 'CLI Test Workflow',
                    '--steps', 'start,process,finish',
                    '--templates', 'test_template',
                    '--auto-assign'
                ])

                assert result.exit_code == 0
                assert '✅ Workflow \'CLI Test Workflow\' erfolgreich hinzugefügt' in result.output
                assert 'start → process → finish' in result.output

    def test_workflows_progress(self, runner):
        """Test des Workflow-Progress"""
        result = runner.invoke(cli, ['workflows', 'progress', 'Python Knowledge Base'])
        assert result.exit_code == 0
        assert '🔄 Workflow-Fortschritt: Python Knowledge Base' in result.output
        assert '📊 Gesamtfortschritt:' in result.output

    def test_workflows_progress_not_found(self, runner):
        """Test für nicht existierenden Workflow"""
        result = runner.invoke(cli, ['workflows', 'progress', 'NonExistent'])
        assert result.exit_code == 0
        assert '❌ Workflow \'NonExistent\' nicht gefunden' in result.output

class TestRulesCommands:
    """Tests für Validierungsregeln-Kommandos"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_rules_show(self, runner):
        """Test der Regel-Anzeige"""
        result = runner.invoke(cli, ['rules', 'show'])
        assert result.exit_code == 0
        assert '⚙️ Aktuelle Validierungsregeln:' in result.output
        assert 'name_min_length' in result.output

    def test_rules_update(self, runner):
        """Test der Regel-Aktualisierung"""
        with patch('src.governance.governance_cli.save_to_config_file'):
            with patch('click.confirm', return_value=False):
                result = runner.invoke(cli, [
                    'rules', 'update',
                    'test_rule', 'true'
                ])

                assert result.exit_code == 0
                assert '✅ Regel \'test_rule\' auf \'True\' gesetzt' in result.output

class TestSystemCommands:
    """Tests für System-Kommandos"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_system_status(self, runner):
        """Test des System-Status"""
        result = runner.invoke(cli, ['system', 'status'])
        assert result.exit_code == 0
        assert '🔧 Data Governance System Status' in result.output
        assert '📋 Templates:' in result.output
        assert '🔄 Workflows:' in result.output
        assert '⚙️ Validierungsregeln:' in result.output

    def test_system_export_config(self, runner):
        """Test des Konfigurations-Exports"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'test_export.yaml')
            result = runner.invoke(cli, [
                'system', 'export-config',
                '--output', output_file
            ])

            assert result.exit_code == 0
            assert f'✅ Konfiguration exportiert nach: {output_file}' in result.output
            assert os.path.exists(output_file)

    def test_system_validate_config_valid(self, runner, sample_config):
        """Test der Konfigurations-Validierung mit gültiger Config"""
        result = runner.invoke(cli, [
            'system', 'validate-config',
            '--config', sample_config
        ])

        assert result.exit_code == 0
        assert '✅ Konfigurationsdatei' in result.output
        assert 'ist gültig' in result.output

    def test_system_validate_config_missing(self, runner):
        """Test der Konfigurations-Validierung mit fehlender Datei"""
        result = runner.invoke(cli, [
            'system', 'validate-config',
            '--config', 'nonexistent.yaml'
        ])

        # Sollte nicht crashen, aber Warnung ausgeben
        assert result.exit_code == 0

class TestTestCommands:
    """Tests für Test-Kommandos"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_test_note(self, runner):
        """Test der Note-Validierung"""
        result = runner.invoke(cli, [
            'test', 'note',
            'Test Note Name',
            'This is test content with sufficient length for validation testing.',
            '--description', 'Test description',
            '--type', 'test'
        ])

        assert result.exit_code == 0
        assert '🔍 Validierung für Note:' in result.output

    def test_test_performance(self, runner):
        """Test des Performance-Tests"""
        result = runner.invoke(cli, [
            'test', 'performance',
            '--iterations', '5'  # Wenige Iterationen für schnellen Test
        ])

        assert result.exit_code == 0
        assert '🧪 Performance-Test mit 5 Iterationen...' in result.output
        assert '✅ Performance-Test abgeschlossen:' in result.output
        assert 'Validierungen pro Sekunde:' in result.output

class TestErrorHandling:
    """Tests für Fehlerbehandlung"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_invalid_template_validate(self, runner, sample_content_file):
        """Test mit ungültigem Template"""
        result = runner.invoke(cli, [
            'templates', 'validate',
            'NonExistentTemplate',
            sample_content_file
        ])

        # Sollte nicht crashen
        assert result.exit_code == 0

    def test_missing_content_file(self, runner):
        """Test mit fehlender Content-Datei"""
        result = runner.invoke(cli, [
            'templates', 'validate',
            'Python Framework',
            'nonexistent_file.md'
        ])

        # Click sollte Fehler abfangen
        assert result.exit_code != 0 or 'does not exist' in result.output

    def test_empty_workflow_steps(self, runner):
        """Test mit leeren Workflow-Steps"""
        result = runner.invoke(cli, [
            'workflows', 'add', 'Empty Workflow'
            # --steps fehlt absichtlich
        ])

        # Sollte Fehler wegen fehlendem required Parameter haben
        assert result.exit_code != 0

class TestConfigIntegration:
    """Tests für Konfigurationsdatei-Integration"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_templates_list_with_config(self, runner, sample_config):
        """Test Template-Liste mit Custom-Config"""
        result = runner.invoke(cli, [
            'templates', 'list',
            '--config', sample_config
        ])

        assert result.exit_code == 0
        assert 'cli_test_template' in result.output

    def test_workflows_list_with_config(self, runner, sample_config):
        """Test Workflow-Liste mit Custom-Config"""
        result = runner.invoke(cli, [
            'workflows', 'list',
            '--config', sample_config
        ])

        assert result.exit_code == 0
        assert 'cli_test_workflow' in result.output

    def test_rules_show_with_config(self, runner, sample_config):
        """Test Regel-Anzeige mit Custom-Config"""
        result = runner.invoke(cli, [
            'rules', 'show',
            '--config', sample_config
        ])

        assert result.exit_code == 0
        assert '⚙️ Aktuelle Validierungsregeln:' in result.output

class TestNeo4jIntegration:
    """Tests für Neo4j-Integration in der CLI"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('src.governance.governance_cli.DataGovernanceEngine')
    def test_templates_list_with_neo4j_data(self, mock_governance_class, runner):
        """Test Template-Liste mit Neo4j-Daten"""
        # Mock der DataGovernanceEngine mit Neo4j-Templates
        mock_governance = Mock()
        mock_governance.get_templates_for_context.return_value = {
            'neo4j_template': {
                'required_sections': ['overview'],
                'suggested_tags': ['neo4j'],
                'workflow_step': 'database',
                'relevance_score': 5
            }
        }
        mock_governance_class.return_value = mock_governance

        result = runner.invoke(cli, [
            'templates', 'list',
            '--project-type', 'database'
        ])

        assert result.exit_code == 0
        # Mock wurde aufgerufen
        mock_governance.get_templates_for_context.assert_called_once()

    @patch('src.governance.governance_cli.DataGovernanceEngine')
    def test_validate_smart_with_context(self, mock_governance_class, runner, sample_content_file):
        """Test Smart-Validierung mit Context"""
        # Mock der erweiterten Validierung
        mock_governance = Mock()
        mock_result = Mock()
        mock_result.passed = True
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.suggestions = ['Test suggestion']

        mock_governance.validate_note_creation_with_context.return_value = mock_result
        mock_governance_class.return_value = mock_governance

        result = runner.invoke(cli, [
            'templates', 'validate-smart',
            sample_content_file,
            '--project-type', 'research',
            '--keywords', 'ai,ml'
        ])

        assert result.exit_code == 0
        # Verifiziere dass die erweiterte Methode aufgerufen wurde
        mock_governance.validate_note_creation_with_context.assert_called_once()

if __name__ == "__main__":
    # Führe Tests aus wenn direkt aufgerufen
    pytest.main([__file__, "-v"])
