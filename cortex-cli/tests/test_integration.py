"""
Advanced integration tests for Cortex CLI
Tests complex workflows, error conditions, and edge cases
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, Mock
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cortex.cli.main import cli
from tests.enhanced_test_utils import CortexTestRunner, create_test_content


class TestCortexIntegration:
    """Integration tests for complete Cortex workflows"""
    
    @pytest.fixture
    def cortex_runner(self):
        """Create a Cortex test runner with workspace setup"""
        runner = CortexTestRunner()
        yield runner
        runner.cleanup_test_workspace()
    
    def test_complete_analysis_workflow(self, cortex_runner):
        """Test complete analysis workflow"""
        with patch('cortex.core.meta_learner.CortexMetaLearner') as mock_learner:
            # Create a mock improvement object with attributes
            mock_improvement = Mock()
            mock_improvement.improvement_type = "optimization"
            mock_improvement.description = "Test improvement"
            mock_improvement.confidence = 85.0
            mock_improvement.impact = "medium"
            mock_improvement.safety = "SAFE"
            mock_improvement.implementation_notes = "Test notes"
            
            mock_learner.return_value.generate_system_improvements.return_value = [
                mock_improvement
            ]
            
            # Test meta-learning
            result = cortex_runner.invoke_with_workspace(cli, [
                'analysis', 'meta-learn',
                '--cortex-path', '.'
            ])
            
            # Check for successful execution
            assert result.exit_code == 0
    
    def test_complete_testing_workflow(self, cortex_runner):
        """Test complete testing workflow"""
        with patch('cortex.integrations.test_framework.CortexAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.analyze_links.return_value = {
                'summary': {
                    'total_files_processed': 2,
                    'total_broken_links': 0,  # No broken links = success
                    'files_with_issues': 0
                },
                'broken_links': []
            }
            
            # Test analysis
            result = cortex_runner.invoke_with_workspace(cli, [
                'test', 'analyze',
                '--cortex-path', '.'
            ])
            
            # Check for successful execution when no broken links
            assert result.exit_code == 0
    
    def test_testing_workflow_with_broken_links(self, cortex_runner):
        """Test testing workflow behavior when broken links are found"""
        with patch('cortex.integrations.test_framework.CortexAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.analyze_links.return_value = {
                'summary': {
                    'total_files_processed': 2,
                    'total_broken_links': 2,  # Has broken links = exit code 1
                    'files_with_issues': 1
                },
                'broken_links': [
                    {
                        'file': 'test.md',
                        'line': 3,
                        'type': 'wikilink',
                        'target': 'broken-link'
                    }
                ]
            }
            
            # Test analysis with broken links
            result = cortex_runner.invoke_with_workspace(cli, [
                'test', 'analyze',
                '--cortex-path', '.'
            ])
            
            # Should exit with code 1 when broken links are found (expected behavior)
            assert result.exit_code == 1
    
    def test_workspace_initialization_and_status(self, cortex_runner):
        """Test workspace initialization and status checking"""
        # Test initialization in empty directory
        with tempfile.TemporaryDirectory() as empty_dir:
            result = cortex_runner.invoke_with_workspace(cli, ['init'], workspace=empty_dir)
            assert result.exit_code == 0
            assert "Cortex workspace initialized successfully" in result.output
            
            # Verify files were created
            assert Path(empty_dir, "config", "cortex.yaml").exists()
            assert Path(empty_dir, "obsidian-vault").exists()
    
    def test_error_conditions(self, cortex_runner):
        """Test various error conditions"""
        # Test with non-existent path
        result = cortex_runner.invoke_with_workspace(cli, [
            'test', 'analyze',
            '--cortex-path', '/non/existent/path'
        ])
        
        assert "does not exist" in result.output or result.exit_code != 0
    
    def test_help_system_completeness(self, cortex_runner):
        """Test that help system is complete and consistent"""
        # Test main help
        result = cortex_runner.invoke_with_workspace(cli, ['--help'])
        assert result.exit_code == 0
        assert "analysis" in result.output
        assert "test" in result.output
        assert "linking" in result.output
        
        # Test subcommand help
        subcommands = [
            ['analysis', '--help'],
            ['test', '--help'], 
            ['linking', '--help']
        ]
        
        for cmd in subcommands:
            result = cortex_runner.invoke_with_workspace(cli, cmd)
            assert result.exit_code == 0
            assert "Options:" in result.output or "Commands:" in result.output


@pytest.mark.parametrize("command,expected_output", [
    (['--version'], "0.1.0"),
    (['--help'], "Cortex CLI"),
    (['status'], "Workspace Status"),
    (['init'], "Initializing"),
])
def test_basic_commands(command, expected_output):
    """Parameterized test for basic commands"""
    cortex_runner = CortexTestRunner()
    
    try:
        if command[0] == 'init':
            # init needs to run in a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                result = cortex_runner.invoke_with_workspace(cli, command, workspace=temp_dir)
        else:
            result = cortex_runner.invoke_with_workspace(cli, command)
        
        assert expected_output in result.output
    finally:
        cortex_runner.cleanup_test_workspace()


class TestCommandArgumentValidation:
    """Test command argument validation"""
    
    def test_required_arguments(self):
        """Test that required arguments are enforced"""
        cortex_runner = CortexTestRunner()
        
        try:
            # Mock the meta learner to prevent actual execution
            with patch('cortex.core.meta_learner.CortexMetaLearner') as mock_learner:
                mock_instance = Mock()
                mock_instance.generate_system_improvements.return_value = []
                mock_learner.return_value = mock_instance
                
                # Test meta-learn command (should succeed with default cortex-path)
                result = cortex_runner.invoke_with_workspace(cli, ['analysis', 'meta-learn'])
                # Should succeed with mocked meta learner
                assert result.exit_code == 0
        finally:
            cortex_runner.cleanup_test_workspace()
    
    def test_choice_validation(self):
        """Test that choice arguments are validated"""
        runner = CliRunner()
        
        # Invalid format choice
        result = runner.invoke(cli, [
            'test', 'dashboard', 
            '--format', 'invalid-format'
        ])
        assert result.exit_code != 0
    
    def test_path_validation(self):
        """Test path argument validation"""
        runner = CliRunner()
        
        # Config file must exist if specified
        result = runner.invoke(cli, [
            '--config', '/non/existent/config.yaml',
            'status'
        ])
        assert result.exit_code != 0


class TestMockingAndIsolation:
    """Test that mocking properly isolates external dependencies"""
    
    @patch('cortex.core.meta_learner.CortexMetaLearner')
    def test_meta_learner_isolation(self, mock_learner):
        """Test that meta-learner is properly mocked"""
        cortex_runner = CortexTestRunner()
        
        try:
            # Configure mock
            mock_instance = Mock()
            mock_instance.generate_system_improvements.return_value = []
            mock_learner.return_value = mock_instance
            
            result = cortex_runner.invoke_with_workspace(cli, [
                'analysis', 'meta-learn',
                '--cortex-path', '.'
            ])
            
            # Should execute successfully (mock prevents real execution)
            assert result.exit_code == 0
        finally:
            cortex_runner.cleanup_test_workspace()
    
    @patch('cortex.integrations.test_framework.CortexAnalyzer')
    def test_analyzer_isolation(self, mock_analyzer):
        """Test that analyzer is properly mocked"""
        cortex_runner = CortexTestRunner()
        
        try:
            # Configure mock
            mock_instance = Mock()
            mock_instance.analyze_links.return_value = {
                'summary': {'total_files_processed': 0, 'total_broken_links': 0, 'files_with_issues': 0},
                'broken_links': []
            }
            mock_analyzer.return_value = mock_instance
            
            result = cortex_runner.invoke_with_workspace(cli, [
                'test', 'analyze',
                '--cortex-path', '.'
            ])
            
            # Should execute successfully (mock prevents real execution)
            assert result.exit_code == 0
        finally:
            cortex_runner.cleanup_test_workspace()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
