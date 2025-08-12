"""
Test data utilities for Cortex CLI tests
Provides helper functions to create consistent test data
"""

from pathlib import Path
import tempfile
import shutil


def create_test_workspace(temp_dir=None):
    """Create a temporary test workspace with sample files"""
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    
    workspace = Path(temp_dir)
    vault_path = workspace / "obsidian-vault"
    vault_path.mkdir(parents=True, exist_ok=True)
    
    # Copy test data files
    test_data_dir = Path(__file__).parent
    for file_path in test_data_dir.glob("*.md"):
        shutil.copy2(file_path, vault_path / file_path.name)
    
    # Create config structure
    config_path = workspace / "config"
    config_path.mkdir(exist_ok=True)
    
    # Create minimal cortex.yaml
    cortex_config = """
workspace:
  name: "Test Workspace"
  vault_path: "./obsidian-vault"
  
analysis:
  enabled: true
  auto_link: true
  
ai:
  provider: "mock"
  
logging:
  level: "INFO"
"""
    
    (config_path / "cortex.yaml").write_text(cortex_config)
    
    return workspace


def cleanup_test_workspace(workspace_path):
    """Clean up test workspace"""
    if workspace_path and Path(workspace_path).exists():
        shutil.rmtree(workspace_path, ignore_errors=True)


def get_sample_content():
    """Get sample markdown content for tests"""
    return {
        'valid_doc': """# Valid Document

This document has working links:
- [[valid-link]]
- [Existing file](./existing-file.md)
""",
        
        'broken_doc': """# Broken Document

This document has broken links:
- [[missing-link]]
- [Missing file](./missing-file.md)
""",
        
        'complex_doc': """# Complex Document

## Analysis
- Decision: [[decision-123]]
- Learning: [[learning-session-456]]

## Links
- [External](https://example.com)
- [[internal-link]]
- [Local file](./local.md)

## Tags
#analysis #decisions #learning
"""
    }
