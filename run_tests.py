#!/usr/bin/env python3
"""
Cortex-py Main Test Runner
=========================

Der offizielle Test-Runner für das Cortex-py Projekt.
Ersetzt die alten run_tests.py und run_all_tests.py und verhindert doppelte HTML-Reports.
"""

import os
import sys
from pathlib import Path

# Projekt-Root hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importiere den Unified Test Runner
from run_tests_unified import main as run_unified_tests

if __name__ == "__main__":
    """
    Führt die vereinheitlichten Tests aus.
    Dies ist jetzt der einzige Test-Runner, um doppelte Reports zu vermeiden.
    """
    print("🎯 Cortex-py Main Test Runner")
    print("Verwendet Unified Test Runner um doppelte Reports zu vermeiden")
    print()

    exit_code = run_unified_tests()
    sys.exit(exit_code)
