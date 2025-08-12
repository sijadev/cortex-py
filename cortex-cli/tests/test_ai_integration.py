"""
Tests für die Cortex-AI Integration
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from cortex.cli.ai import chat, analyze, validate
from tests.enhanced_test_utils import CortexTestRunner, mock_cortex_ai_client

@pytest.fixture
def runner():
    """Fixture for a CortexTestRunner"""
    runner = CortexTestRunner()
    try:
        yield runner
    finally:
        runner.cleanup_test_workspace()

def test_chat_command(runner):
    """Test the chat command"""
    with mock_cortex_ai_client() as mock_client:
        # Test programmatic chat
        result = chat(message="Test message", vault_id=1)
        assert result['success'] is True
        assert "response" in result
        
        # Test CLI chat
        cli_result = runner.invoke_cortex(['ai', 'chat', '-m', 'Test message'])
        assert cli_result.exit_code == 0
        assert "This is a test response" in cli_result.output
        
        mock_client.chat.assert_called_with("Test message", 1)

def test_analyze_command(runner):
    """Test the analyze command"""
    with mock_cortex_ai_client() as mock_client:
        # Create test file
        workspace = runner.setup_test_workspace()
        test_file = Path(workspace) / "test.md"
        test_file.write_text("This is test content")
        
        # Test programmatic analyze
        result = analyze(file=str(test_file), vault_id=1)
        assert result['success'] is True
        assert "links" in result['analysis']
        
        # Test CLI analyze
        cli_result = runner.invoke_cortex(['ai', 'analyze', '-f', str(test_file)])
        assert cli_result.exit_code == 0
        assert "potentielle Verknüpfungen gefunden" in cli_result.output
        
        # Make sure client was called with correct parameters
        mock_client.analyze_content.assert_called()

def test_validate_command(runner):
    """Test the validate command"""
    with mock_cortex_ai_client() as mock_client:
        # Test programmatic validate
        result = validate()
        assert result['success'] is True
        
        # Test CLI validate
        cli_result = runner.invoke_cortex(['ai', 'validate'])
        assert cli_result.exit_code == 0
        assert "Alle Links sind gültig" in cli_result.output
        
        mock_client.validate_links.assert_called()

def test_error_handling():
    """Test error handling in AI commands"""
    with patch('cortex.integrations.cortex_ai.client.get_client') as mock_get_client:
        mock_client = mock_get_client.return_value
        mock_client.is_enabled.return_value = False
        
        # Test disabled AI
        result = chat(message="Test")
        assert result['success'] is False
        assert "nicht aktiviert" in result['error']
        
        # Test exception handling
        mock_client.is_enabled.return_value = True
        mock_client.chat.side_effect = Exception("Test error")
        
        result = chat(message="Test", verbose=True)
        assert result['success'] is False
        assert "error" in result
        assert "traceback" in result
