import pytest
import subprocess
import sys
from pathlib import Path

# Markdown System Smoketest (already covered in test_markdown_system.py)
# Cortex CLI Smoketest

def test_smoke_cortex_cli_help():
    result = subprocess.run(["./cortex-cli/bin/cortex-cmd", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Usage" in result.stdout or "usage" in result.stdout

# Cortex Neo Smoketest

def test_smoke_cortex_neo_config():
    from cortex_neo.config import Settings
    cfg = Settings.from_env()
    assert cfg is not None
    assert hasattr(cfg, 'uri')

# Governance Smoketest

def test_smoke_governance_status():
    result = subprocess.run([sys.executable, "src/governance/governance_status.py"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "CORTEX DATA GOVERNANCE SYSTEM STATUS" in result.stdout

# Safe Transactions Smoketest

def test_smoke_safe_transactions():
    from src.safe_transactions import SafeTransactionManager
    class DummyDriver:
        def session(self):
            class DummySession:
                def __enter__(self): return self
                def __exit__(self, exc_type, exc_val, exc_tb): pass
                def run(self, query):
                    class DummyResult:
                        def __iter__(self): return iter([])
                    return DummyResult()
            return DummySession()
    tx_manager = SafeTransactionManager(driver=DummyDriver())
    tx_manager.ensure_backup_dir()
    assert tx_manager.backup_dir.endswith("backups/auto")

# System Config Smoketest

def test_smoke_system_config():
    from src.cortex_system_config import CortexSystemConfig
    config = CortexSystemConfig()
    assert hasattr(config, 'neo4j_uri')
    assert hasattr(config, 'neo4j_user')
    assert hasattr(config, 'neo4j_password')
    assert hasattr(config, 'database_name')

# Note/Data Governance Smoketest

def test_smoke_data_governance():
    from src.governance.data_governance import Neo4jTemplateManager
    manager = Neo4jTemplateManager()
    assert hasattr(manager, 'uri')
    assert hasattr(manager, 'user')
    assert hasattr(manager, 'password')

# Main Entry Points Smoketest

def test_smoke_main_script():
    result = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True)
    assert result.returncode == 0

# Scripts Smoketest

def test_smoke_script_check_integrity():
    import os
    result = subprocess.run([sys.executable, "scripts/check_integrity.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"Integrity check script failed: {result.stdout}\n{result.stderr}"
