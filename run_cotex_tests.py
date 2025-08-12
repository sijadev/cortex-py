#!/usr/bin/env python3
"""
Skript zum Ausführen aller Tests im cortex-cli Verzeichnis
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    print("Führe alle Tests im cortex-cli Verzeichnis aus...")
    
    # Pfad zum Cortex-CLI Verzeichnis
    cortex_cli_dir = Path('/workspaces/cortex-py/cortex-cli')
    
    if not cortex_cli_dir.exists():
        print(f"Fehler: Verzeichnis {cortex_cli_dir} existiert nicht.")
        return 1
        
    os.chdir(cortex_cli_dir)
    print(f"Arbeitsverzeichnis: {os.getcwd()}")
    
    # Prüfe auf vorhandene Test-Runner
    test_runners = [
        ("tests/run_tests.py", "Eigener Test-Runner"),
        ("pytest", "pytest"),
        ("python -m unittest discover", "unittest")
    ]
    
    success = False
    
    for cmd, name in test_runners:
        print(f"\n===== Versuche Tests mit {name} auszuführen =====")
        
        try:
            if cmd.endswith(".py") and Path(cmd).exists():
                # Mache das Skript ausführbar
                os.chmod(cmd, os.stat(cmd).st_mode | 0o755)
                result = subprocess.run(f"python {cmd}", shell=True)
            else:
                result = subprocess.run(cmd, shell=True)
                
            if result.returncode == 0:
                print(f"\n✅ Tests mit {name} erfolgreich ausgeführt!")
                success = True
                break
            else:
                print(f"\n❌ Tests mit {name} fehlgeschlagen (Exit-Code: {result.returncode})")
        except Exception as e:
            print(f"Fehler beim Ausführen der Tests mit {name}: {str(e)}")
    
    if not success:
        print("\n❌ Alle Testmethoden sind fehlgeschlagen.")
        
        # Überprüfe die Struktur des Tests-Verzeichnisses für weitere Informationen
        if Path("tests").exists():
            print("\nInhalt des tests/-Verzeichnisses:")
            subprocess.run(["ls", "-la", "tests"])
            
            # Suche nach Test-Dateien
            test_files = list(Path("tests").glob("test_*.py"))
            if test_files:
                print(f"\nGefundene Test-Dateien: {len(test_files)}")
                for test_file in test_files:
                    print(f"  - {test_file}")
                    
                # Versuche, eine einzelne Testdatei auszuführen
                print("\nVersuche, eine einzelne Testdatei auszuführen:")
                test_file = test_files[0]
                subprocess.run(["python", "-m", f"tests.{test_file.stem}"])
        
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())    