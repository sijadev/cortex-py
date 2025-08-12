#!/bin/bash
# filepath: /workspaces/cortex-py/fix_test_imports.sh

set -e  # Beende bei Fehlern

echo "===== Repariere Test-Imports ====="

cd /workspaces/cortex-py/cortex-cli

# 1. Untersuche die Test-Datei, um zu verstehen, wie 'test' verwendet wird
echo "1. Analysiere test_cli_commands.py..."
grep -n "from cortex.cli.testing import test" tests/test_cli_commands.py
grep -n "test" tests/test_cli_commands.py

# 2. Aktualisiere testing.py, um die fehlende 'test'-Komponente hinzuzufügen
echo "2. Ergänze die fehlende 'test'-Komponente in testing.py..."

# Sichern der aktuellen Datei
cp cortex/cli/testing.py cortex/cli/testing.py.bak

# Füge die test-Funktion/Variable zur testing.py hinzu
cat >> cortex/cli/testing.py << 'EOF'

# Einfache test-Funktion, die von test_cli_commands.py erwartet wird
def test(args=None):
    """
    Führt Tests mit den angegebenen Argumenten aus
    
    Args:
        args: Argumente für den Testlauf
        
    Returns:
        int: Exit-Code des Testlaufs (0 = erfolg)
    """
    import pytest
    
    if args is None:
        args = []
        
    return pytest.main(args)
EOF

echo "3. Prüfe den Python-Cache..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "4. Führe die Tests erneut aus..."
python -m pytest tests/test_cli_commands.py -v

echo -e "\nFalls weiterhin Probleme bestehen, könnten wir die originale Test-Implementierung aus dem Backup wiederherstellen:"
echo "cp /workspaces/cortex-py/cortex-cli_backup_*/cortex/cli/testing.py cortex/cli/testing.py"

echo -e "\nUm alle Tests auszuführen, nutze:"
echo "bin/cortex-cmd testing run"