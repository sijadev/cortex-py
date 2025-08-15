# AI-Chatbot-Entwicklung

**Projekttyp:** research
**Erstellt:** 2025-08-15
**Status:** 🟢 Aktiv

## 📋 Übersicht

[Projektbeschreibung hier einfügen]

## 🎯 Ziele

- [ ] Ziel 1
- [ ] Ziel 2
- [ ] Ziel 3

## 📁 Projektstruktur

- `docs/` - Projektdokumentation
- `notes/` - Arbeitsnoten und Ideen
- `meeting-notes/` - Meeting-Protokolle
- `status-reports/` - Status-Reports
- `deliverables/` - Projektergebnisse

## 🔗 MCP Integration (Model Context Protocol)

Dieses Projekt bietet vollständige **MCP (Model Context Protocol)** Integration für Claude Desktop:

### MCP Server Features
- **Cortex MCP Server**: Direkter Zugriff auf Cortex CLI Funktionen
- **Knowledge Graph Integration**: Durchsuche und verwalte den Neo4j Knowledge Graph
- **Intelligent Templates**: Automatische Template-Erkennung und -Validierung
- **Real-time Status**: Live-Status des Cortex-Systems

### Quick Start mit MCP
```bash
# MCP Server starten
./start_mcp_cortex_server.sh

# Claude Desktop konfigurieren
# Siehe: docs/MCP_SETUP_ANLEITUNG.md
```

### Verfügbare MCP Tools
- `cortex_run_command`: Führe beliebige Cortex CLI Befehle aus
- `cortex_add_knowledge`: Füge neues Wissen zum Knowledge Graph hinzu  
- `cortex_search`: Durchsuche den Knowledge Graph nach Inhalten

### MCP Ressourcen
- `cortex://status`: Aktueller System-Status
- `cortex://knowledge-graph`: Knowledge Graph Übersicht

**Dokumentation:** Siehe `docs/MCP_SETUP_ANLEITUNG.md` für detaillierte Setup-Anweisungen.

## 🛡️ Data Governance

Dieses Projekt nutzt Data Governance Templates:
- Projekt Kickoff: `project_kickoff_AI-Chatbot-Entwicklung`
- Status Reports: `status_report_AI-Chatbot-Entwicklung`

### Validierung
```bash
# Template validieren
governance-cli templates validate project_kickoff_AI-Chatbot-Entwicklung document.md

# Workflow-Status prüfen
governance-cli workflows progress project_lifecycle
```

## 📊 Workflow

```
Initiation → Planning → Execution → Monitoring → Closure
```
