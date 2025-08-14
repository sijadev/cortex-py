#!/usr/bin/env python3
"""
Test-Skript für den Cortex MCP Server
"""

import subprocess
import sys
import os

def test_mcp_installation():
    """Test ob MCP installiert ist."""
    try:
        import mcp
        print("✅ MCP-Bibliothek ist installiert")
        return True
    except ImportError:
        print("❌ MCP-Bibliothek ist nicht installiert")
        print("Installieren Sie mit: pip install mcp")
        return False

def test_cortex_cli():
    """Test ob Cortex CLI verfügbar ist."""
    try:
        result = subprocess.run([
            "python3", "cortex_neo/cortex_cli.py", "--help"
        ], capture_output=True, text=True, cwd="/Users/simonjanke/Projects/cortex-py")
        
        if result.returncode == 0:
            print("✅ Cortex CLI ist verfügbar")
            return True
        else:
            print("❌ Cortex CLI Fehler:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Fehler beim Testen der Cortex CLI: {e}")
        return False

def test_script_permissions():
    """Test ob Start-Skript ausführbar ist."""
    script_path = "/Users/simonjanke/Projects/cortex-py/start_mcp_cortex_server.sh"
    if os.access(script_path, os.X_OK):
        print("✅ Start-Skript ist ausführbar")
        return True
    else:
        print("❌ Start-Skript ist nicht ausführbar")
        print(f"Führen Sie aus: chmod +x {script_path}")
        return False

def show_configuration_instructions():
    """Zeigt Konfigurationsanweisungen."""
    print("\n📋 Konfiguration für Claude Desktop:")
    print("\n1. Öffnen Sie Claude Desktop")
    print("2. Gehen Sie zu Settings (⌘ + ,)")
    print("3. Klicken Sie auf 'Developer'")
    print("4. Klicken Sie auf 'Edit Config'")
    print("5. Fügen Sie diese Konfiguration hinzu:\n")
    
    config = {
        "mcpServers": {
            "cortex-py": {
                "command": "/Users/simonjanke/Projects/cortex-py/start_mcp_cortex_server.sh",
                "cwd": "/Users/simonjanke/Projects/cortex-py"
            }
        }
    }
    
    import json
    print(json.dumps(config, indent=2))
    print("\n6. Speichern Sie die Konfiguration")
    print("7. Starten Sie Claude Desktop neu")

def main():
    print("🔍 Cortex MCP Server Tests\n")
    
    all_tests_passed = True
    
    # Tests ausführen
    all_tests_passed &= test_mcp_installation()
    all_tests_passed &= test_cortex_cli()
    all_tests_passed &= test_script_permissions()
    
    print("\n" + "="*50)
    
    if all_tests_passed:
        print("🎉 Alle Tests bestanden!")
        show_configuration_instructions()
    else:
        print("⚠️  Einige Tests sind fehlgeschlagen.")
        print("Beheben Sie die oben genannten Probleme und führen Sie das Skript erneut aus.")
    
    print("\n📖 Weitere Informationen finden Sie in: MCP_SETUP_ANLEITUNG.md")

if __name__ == "__main__":
    main()
