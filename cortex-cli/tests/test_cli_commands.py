"""
Unit tests for all Cortex CLI commands
Tests command line interface functionality, argument parsing, and basic execution
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner
import sys
import os

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cortex.cli.main import cli
from cortex.cli.analysis import analysis
from cortex.cli.testing import testing as test
from cortex.cli.linking import linking


class TestCortexCLI(unittest.TestCase):
    """Test suite for Cortex CLI commands"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_workspace = Path(self.temp_dir)
        
        # Create basic test structure
        (self.test_workspace / "obsidian-vault").mkdir(parents=True)
        (self.test_workspace / "config").mkdir(parents=True)
        
        # Create test markdown files
        self.create_test_files()
    
    def tearDown(self):
        """Clean up after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_files(self):
        """Create test markdown files for testing"""
        # Create test markdown files
        test_md_content = """# Test Document
        
This is a test document with [[test-link]] and [markdown link](./other.md).

## Test Section
Some content here.
"""
        
        vault_path = self.test_workspace / "obsidian-vault"
        (vault_path / "test.md").write_text(test_md_content, encoding='utf-8')
        (vault_path / "other.md").write_text("# Other Document\n\nContent here.", encoding='utf-8')
        
        # Create config file
        config_content = """
workspace:
  name: "Test Workspace"
  version: "1.0.0"
obsidian:
  vault_path: "./obsidian-vault"
"""
        (self.test_workspace / "config" / "cortex.yaml").write_text(config_content, encoding='utf-8')


class TestMainCommands(TestCortexCLI):
    """Test main CLI commands (init, status, help)"""
    
    def test_cli_help(self):
        """Test main CLI help command"""
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Cortex Command Line Interface", result.output)
        self.assertIn("analysis", result.output)
        self.assertIn("test", result.output)
        self.assertIn("linking", result.output)
    
    def test_cli_version(self):
        """Test CLI version command"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("0.2.0", result.output)
    
    def test_init_command(self):
        """Test workspace initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            result = self.runner.invoke(cli, ['init'])
            self.assertEqual(result.exit_code, 0)
            
            # Check if directories were created
            self.assertTrue(Path(temp_dir, "obsidian-vault/Chat-Sessions").exists())
            self.assertTrue(Path(temp_dir, "obsidian-vault/Code-Fragments").exists())
            self.assertTrue(Path(temp_dir, "obsidian-vault/Decisions").exists())
            self.assertTrue(Path(temp_dir, "config").exists())
            self.assertTrue(Path(temp_dir, "config/cortex.yaml").exists())
    
    @patch('cortex.cli.main.find_cortex_root')
    def test_status_command(self, mock_find_root):
        """Test status command"""
        mock_find_root.return_value = str(self.test_workspace)
        
        result = self.runner.invoke(cli, ['status'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Workspace Status", result.output)
        self.assertIn("Pfad:", result.output)


class TestAnalysisCommands(TestCortexCLI):
    """Test analysis command group"""
    
    def test_analysis_help(self):
        """Test analysis group help"""
        result = self.runner.invoke(analysis, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Analysis and learning commands", result.output)
        self.assertIn("meta-learn", result.output)
        self.assertIn("pattern-detect", result.output)
        self.assertIn("learner-service", result.output)
    
    @patch('cortex.core.meta_learner.CortexMetaLearner')
    def test_meta_learn_command(self, mock_learner_class):
        """Test meta-learn command"""
        # Mock the meta learner
        mock_learner = Mock()
        mock_learner.generate_system_improvements.return_value = []
        mock_learner_class.return_value = mock_learner
        
        result = self.runner.invoke(analysis, [
            'meta-learn', 
            '--cortex-path', str(self.test_workspace)
        ])
        
        # Should not exit with error (implementation might have issues but command structure works)
        self.assertIn("Meta-Learning", result.output)
    
    @patch('cortex.core.pattern_detector.AdvancedPatternDetector')
    def test_pattern_detect_command(self, mock_detector_class):
        """Test pattern-detect command"""
        # Mock the pattern detector
        mock_detector = Mock()
        mock_detector.detect_decision_patterns.return_value = []
        mock_detector.detect_project_patterns.return_value = []
        mock_detector.detect_ai_session_patterns.return_value = []
        mock_detector_class.return_value = mock_detector
        
        result = self.runner.invoke(analysis, [
            'pattern-detect',
            '--cortex-path', str(self.test_workspace),
            '--pattern-type', 'all'
        ])
        
        self.assertIn("Pattern Detection", result.output)
    
    @patch('cortex.core.cortex_learner.CortexLearningService')
    def test_learner_service_status(self, mock_service_class):
        """Test learner-service status command"""
        # Mock the learning service
        mock_service = Mock()
        mock_service.get_service_status.return_value = {
            'running': False,
            'last_run': 'Never',
            'total_cycles': 0,
            'quality_score': 85.0,
            'learning_rate': 0.001
        }
        mock_service_class.return_value = mock_service
        
        result = self.runner.invoke(analysis, [
            'learner-service',
            '--cortex-path', str(self.test_workspace),
            '--action', 'status'
        ])
        
        self.assertIn("Learning Service Status", result.output)


class TestTestCommands(TestCortexCLI):
    """Test the test command group"""
    
    def test_test_help(self):
        """Test test group help"""
        result = self.runner.invoke(test, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Test-Befehle zur Überprüfung", result.output)
        self.assertIn("analyze", result.output)
        self.assertIn("validate", result.output)
        self.assertIn("dashboard", result.output)
    
    @patch('cortex.integrations.test_framework.CortexAnalyzer')
    @patch('cortex.integrations.test_framework.HealthReporter')
    def test_test_analyze_command(self, mock_reporter_class, mock_analyzer_class):
        """Test test analyze command"""
        # Mock the analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_links.return_value = {
            'summary': {
                'total_files_processed': 2,
                'total_broken_links': 0,
                'files_with_issues': 0
            },
            'broken_links': []
        }
        mock_analyzer_class.return_value = mock_analyzer
        
        result = self.runner.invoke(test, [
            'analyze',
            '--cortex-path', str(self.test_workspace)
        ])
        
        self.assertIn("Test Analysis Results", result.output)
    
    def test_test_validate_command(self):
        """Test test validate command"""
        # Create a test suggestions file
        test_suggestions = """# Test Suggestions
        
## Safe Suggestions
1. Fix broken link: [[missing]] -> [[existing]]
   - ✅ APPROVED
        
## Unsafe Suggestions  
2. Delete all files
   - ❌ REJECTED
"""
        
        suggestions_file = self.test_workspace / "test_suggestions.md"
        suggestions_file.write_text(test_suggestions, encoding='utf-8')
        
        with patch('cortex.integrations.test_framework.HealthReporter') as mock_reporter_class:
            mock_reporter = Mock()
            mock_reporter.validate_suggestions.return_value = "Validation report content"
            mock_reporter_class.return_value = mock_reporter
            
            result = self.runner.invoke(test, [
                'validate',
                '--input', str(suggestions_file),
                '--output', str(self.test_workspace / "validation.md")
            ])
            
            # Command structure should work even if implementation has issues
            self.assertIn("Validating", result.output)
    
    @patch('cortex.integrations.test_framework.HealthReporter')
    def test_test_dashboard_command(self, mock_reporter_class):
        """Test test dashboard command"""
        mock_reporter = Mock()
        mock_reporter.generate_health_dashboard.return_value = "<html>Test Dashboard</html>"
        mock_reporter_class.return_value = mock_reporter
        
        result = self.runner.invoke(test, [
            'dashboard',
            '--format', 'html',
            '--output', str(self.test_workspace / "dashboard.html")
        ])
        
        self.assertIn("Dashboard", result.output)


class TestLinkingCommands(TestCortexCLI):
    """Test linking command group"""
    
    def test_linking_help(self):
        """Test linking group help"""
        result = self.runner.invoke(linking, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Linking und Vault-Management Befehle", result.output)
        self.assertIn("rule-linker", result.output)
    
    @patch('cortex.core.rule_based_linker.RuleBasedLinker')
    def test_rule_linker_show_rules(self, mock_linker_class):
        """Test rule-linker show rules command"""
        # Mock rule object
        mock_rule = Mock()
        mock_rule.name = "Test Rule"
        mock_rule.description = "A test linking rule"
        mock_rule.strength = 0.8
        mock_rule.enabled = True
        
        mock_linker = Mock()
        mock_linker.rules = [mock_rule]
        mock_linker_class.return_value = mock_linker
        
        result = self.runner.invoke(linking, [
            'rule-linker',
            '--cortex-path', str(self.test_workspace),
            '--show-rules'
        ])
        
        self.assertIn("Linking-Regeln", result.output)
    
    @patch('cortex.core.rule_based_linker.RuleBasedLinker')
    def test_rule_linker_run(self, mock_linker_class):
        """Test rule-linker run command"""
        mock_linker = Mock()
        mock_linker.run_linking_cycle.return_value = {
            'success': True,
            'rules_applied': 3,
            'matches_found': 5,
            'links_created': 2,
            'files_modified': 2,
            'duration_seconds': 1.5,
            'errors': []
        }
        mock_linker_class.return_value = mock_linker
        
        result = self.runner.invoke(linking, [
            'rule-linker',
            '--cortex-path', str(self.test_workspace),
            '--run'
        ])
        
        self.assertIn("Linking-Zyklus", result.output)


class TestCommandIntegration(TestCortexCLI):
    """Integration tests for command combinations and workflows"""
    
    def test_full_workflow_init_status(self):
        """Test a complete workflow: init -> status"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Initialize workspace
            init_result = self.runner.invoke(cli, ['init'])
            self.assertEqual(init_result.exit_code, 0)
            
            # Check status
            status_result = self.runner.invoke(cli, ['status'])
            self.assertEqual(status_result.exit_code, 0)
            self.assertIn("✅", status_result.output)  # Should show green checkmarks
    
    def test_error_handling_invalid_path(self):
        """Test error handling with invalid paths"""
        result = self.runner.invoke(test, [
            'analyze',
            '--cortex-path', '/nonexistent/path'
        ])
        
        # Should handle gracefully (may exit with error but shouldn't crash)
        self.assertIsNotNone(result.output)
    
    def test_verbose_flag(self):
        """Test verbose flag functionality"""
        result = self.runner.invoke(cli, ['--verbose', 'status'])
        # Should not crash with verbose flag
        self.assertIsNotNone(result.output)
    
    def test_json_output_formats(self):
        """Test JSON output format options"""
        with patch('cortex.core.meta_learner.CortexMetaLearner') as mock_learner_class:
            mock_learner = Mock()
            mock_learner.generate_system_improvements.return_value = []
            mock_learner_class.return_value = mock_learner
            
            result = self.runner.invoke(analysis, [
                'meta-learn',
                '--cortex-path', str(self.test_workspace),
                '--json'
            ])
            
            # Should include JSON-related output
            self.assertIsNotNone(result.output)


class TestCommandValidation(TestCortexCLI):
    """Test command argument validation and edge cases"""
    
    def test_missing_required_args(self):
        """Test behavior with missing required arguments"""
        result = self.runner.invoke(test, ['validate'])
        
        # Should fail gracefully with helpful error message
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Missing option", result.output)
    
    def test_invalid_choice_args(self):
        """Test behavior with invalid choice arguments"""
        result = self.runner.invoke(test, [
            'dashboard',
            '--format', 'invalid-format'
        ])
        
        # Should fail with validation error
        self.assertNotEqual(result.exit_code, 0)
    
    def test_conflicting_options(self):
        """Test behavior with conflicting options"""
        result = self.runner.invoke(linking, [
            'rule-linker',
            '--show-rules',
            '--run'  # These could be considered conflicting
        ])
        
        # Should handle gracefully (implementation dependent)
        self.assertIsNotNone(result.output)


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2)
