# Cortex-py: AI-Enhanced Knowledge Management System

Ein intelligentes Knowledge Management System mit Neo4j Backend und Claude Desktop Integration über MCP (Model Context Protocol).

## Features

🧠 **AI-basierte Tag-Vorschläge**: Machine Learning-basierte automatische Tag-Generierung
🔗 **Content-basierte Verlinkung**: Automatische Verknüpfung ähnlicher Notes
📝 **Vollständiges Content-Management**: Notes mit Rich Text Content
🌐 **Claude Desktop Integration**: Nahtlose MCP Server Integration
📊 **Neo4j Knowledge Graph**: Strukturierte Wissensspeicherung

## Quick Start

1. **Installation:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Neo4j Setup:**
   - Starte Neo4j Database (localhost:7687)
   - Standard Credentials: neo4j/neo4jtest

3. **MCP Server für Claude Desktop:**
   ```bash
   make claude-restart
   ```

## Verfügbare Befehle

### Content Management
- `python3 cortex_neo/cortex_cli.py add-note "Note Name" --content "Content..." --type "project"`
- `python3 cortex_neo/cortex_cli.py show-note "Note Name"`
- `python3 cortex_neo/cortex_cli.py search-notes "query" --in-content`

### AI-Features
- `python3 cortex_neo/cortex_cli.py ai-suggest-tags` - AI-basierte Tag-Vorschläge
- `python3 cortex_neo/cortex_cli.py auto-link-by-content` - Automatische Content-Verlinkung
- `python3 cortex_neo/cortex_cli.py suggest-links "Note Name"` - Link-Vorschläge für spezifische Note

### Claude Desktop Integration
Die folgenden Tools sind direkt in Claude Desktop verfügbar:
- `cortex_add_note` - Erstelle Notes mit Content
- `cortex_ai_suggest_tags` - AI-basierte Tag-Vorschläge
- `cortex_auto_link_content` - Automatische Verlinkung
- `cortex_search_content` - Erweiterte Suche

## Makefile Commands

- `make help` - Zeige verfügbare Befehle
- `make test` - Teste MCP Server
- `make status` - Zeige System-Status
- `make claude-restart` - Starte Claude Desktop neu

## Projektstruktur

- `cortex_neo/cortex_cli.py` - Hauptkommandozeilen-Interface
- `mcp_cortex_server_simple.py` - MCP Server für Claude Desktop
- `claude_desktop_config.json` - Claude Desktop Konfiguration
- `assets/` - PlantUML Diagramme und Dokumentation

## System Requirements

- Python 3.8+
- Neo4j Database
- Claude Desktop (für MCP Integration)
