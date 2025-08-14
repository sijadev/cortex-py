"""
Enhanced test utilities with proper workspace setup and CLI runner configuration
"""
import os
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager
from click.testing import CliRunner
from unittest.mock import patch

class CortexTestRunner(CliRunner):
    """Enhanced CLI runner for Cortex tests with proper workspace setup"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_workspace = None
    
    def setup_test_workspace(self):
        """Set up a temporary test workspace"""
        self.test_workspace = tempfile.mkdtemp(prefix="cortex_test_")
        
        # Create sample vault directories and files
        sample_vault_path = Path(self.test_workspace) / "sample_vault"
        sample_vault_path.mkdir(exist_ok=True)
        
        # Create config directory
        config_path = Path(self.test_workspace) / "config"
        config_path.mkdir(exist_ok=True)
        
        # Create test config file
        config_content = """
        general:
          log_level: "debug"
          workspace_path: "."
          
        linking:
          auto_link: true
          min_confidence: 0.5
          
        cortex_ai:
          enabled: true
          api_url: "http://localhost:8000"
        """
        
        with open(config_path / "cortex.yaml", "w") as f:
            f.write(config_content)
            
        return self.test_workspace
    
    def teardown_test_workspace(self):
        """Clean up test workspace"""
        if self.test_workspace:
            shutil.rmtree(self.test_workspace, ignore_errors=True)
            self.test_workspace = None
    
    def cleanup_test_workspace(self):
        """Alias for teardown_test_workspace for backward compatibility"""
        self.teardown_test_workspace()
    
    def invoke_command(self, cli, command, workspace=None, *args, **kwargs):
        """Invoke CLI command with proper test environment"""
        if workspace is None:
            workspace = self.test_workspace or self.setup_test_workspace()
        original_cwd = os.getcwd()
        try:
            os.chdir(workspace)
            if isinstance(command, str):
                command = command.split()
            if '--cortex-path' not in command:
                command.extend(['--cortex-path', '.'])
            # Actually invoke the CLI command and return the result
            return self.invoke(cli, command, *args, **kwargs)
        finally:
            os.chdir(original_cwd)

    def invoke_with_workspace(self, cli, args, workspace=None, **kwargs):
        """Invoke CLI command with workspace context"""
        import sys
        print(f"[DEBUG] invoke_with_workspace: workspace={workspace}, args={args}", file=sys.stderr)
        if workspace:
            # Temporär in workspace-Verzeichnis wechseln
            original_cwd = os.getcwd()
            try:
                os.chdir(workspace)
                print(f"[DEBUG] CWD after chdir: {os.getcwd()}", file=sys.stderr)
                result = self.invoke(cli, args, **kwargs)
            finally:
                os.chdir(original_cwd)
            return result
        else:
            return self.invoke(cli, args, **kwargs)
    
    def invoke_cortex(self, command, *args, **kwargs):
        """Invoke a Cortex command with proper setup"""
        from cortex.cli.main import cli
        
        # Create a list of command parts if a string is provided
        if isinstance(command, str):
            command = command.split()
            
        return self.invoke(cli, command, *args, **kwargs)


def create_test_content(content="Sample content", filename="test.md"):
    """Create test content for tests"""
    return {
        "content": content,
        "filename": filename
    }

@contextmanager
def mock_cortex_ai_client():
    """Mock the Cortex AI client for testing"""
    with patch('cortex.integrations.cortex_ai.client.get_client') as mock_get_client:
        mock_client = mock_get_client.return_value
        mock_client.is_enabled.return_value = True
        mock_client.chat.return_value = {
            "message": "This is a test response",
            "links": [{"link_text": "Test Link", "target_type": "file"}]
        }
        mock_client.analyze_content.return_value = {
            "links": [{"link_text": "Test Link", "target_type": "file"}]
        }
        mock_client.validate_links.return_value = {
            "invalid_links": 0
        }
        
        yield mock_client
