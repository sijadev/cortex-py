#!/usr/bin/env python3
"""
Cortex MCP Server - Installationshilfe und Übersicht
"""

import os
import json

def print_header():
    print("=" * 60)
    print("🧠 CORTEX MCP SERVER SETUP FÜR CLAUDE DESKTOP")
    print("=" * 60)

def print_files_created():
    print("\n📁 Folgende Dateien wurden erstellt:")
    files = [
        "mcp_cortex_server.py - Haupt-MCP-Server",
        "start_mcp_cortex_server.sh - Startskript",
        "test_mcp_setup.py - Test-Tool",
        "claude_desktop_config_example.json - Beispiel-Konfiguration",
        "MCP_SETUP_ANLEITUNG.md - Detaillierte Anleitung",
        "README_MCP.md - Projekt-Übersicht",
        "requirements.txt - Aktualisiert mit MCP-Abhängigkeit"
    ]
    
    for i, file in enumerate(files, 1):
        print(f"   {i}. {file}")

def print_next_steps():
    print("\n🚀 NÄCHSTE SCHRITTE:")
    print("\n1. MCP-Bibliothek installieren:")
    print("   cd /Users/simonjanke/Projects/cortex-py")
    print("   source /Users/simonjanke/miniforge3/bin/activate")
    print("   conda activate base")
    print("   pip install mcp")
    
    print("\n2. Setup testen:")
    print("   python3 test_mcp_setup.py")
    
    print("\n3. Claude Desktop konfigurieren:")
    print("   - Öffnen Sie Claude Desktop")
    print("   - Settings (⌘ + ,) → Developer → Edit Config")
    print("   - Konfiguration aus claude_desktop_config_example.json hinzufügen")
    
    print("\n4. Claude Desktop neu starten")
    
    print("\n5. In Claude Desktop testen:")
    print('   "Führe den Cortex Status-Befehl aus"')

def print_claude_config():
    print("\n⚙️  CLAUDE DESKTOP KONFIGURATION:")
    print("\nFügen Sie dies in Ihre Claude Desktop Konfiguration ein:")
    print("-" * 50)
    
    config = {
        "mcpServers": {
            "cortex-py": {
                "command": "/Users/simonjanke/Projects/cortex-py/start_mcp_cortex_server.sh",
                "cwd": "/Users/simonjanke/Projects/cortex-py"
            }
        }
    }
    
    print(json.dumps(config, indent=2))
    print("-" * 50)

def print_tools_overview():
    print("\n🛠  VERFÜGBARE TOOLS NACH SETUP:")
    tools = [
        "cortex_run_command - Führt Cortex CLI Befehle aus",
        "cortex_add_knowledge - Fügt Wissen zum Knowledge Graph hinzu",
        "cortex_search - Durchsucht den Knowledge Graph"
    ]
    
    for tool in tools:
        print(f"   • {tool}")

def print_resources_overview():
    print("\n📊 VERFÜGBARE RESSOURCEN:")
    resources = [
        "cortex://status - System-Status",
        "cortex://knowledge-graph - Knowledge Graph Überblick"
    ]
    
    for resource in resources:
        print(f"   • {resource}")

def print_troubleshooting():
    print("\n🔧 FEHLERBEHEBUNG:")
    print("   • Wenn MCP nicht installiert: pip install mcp")
    print("   • Wenn Server nicht startet: Berechtigungen prüfen")
    print("   • Wenn Claude Desktop Server nicht erkennt: Konfiguration prüfen")
    print("   • Für Details: siehe MCP_SETUP_ANLEITUNG.md")

def print_footer():
    print("\n" + "=" * 60)
    print("✨ SETUP ABGESCHLOSSEN!")
    print("Folgen Sie den Schritten oben, um den MCP Server zu aktivieren.")
    print("=" * 60)

def main():
    print_header()
    print_files_created()
    print_next_steps()
    print_claude_config()
    print_tools_overview()
    print_resources_overview()
    print_troubleshooting()
    print_footer()

if __name__ == "__main__":
    main()
