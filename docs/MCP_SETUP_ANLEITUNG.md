# Cortex MCP Server Setup für Claude Desktop

## Installation

### 1. MCP-Bibliothek installieren

Öffnen Sie ein Terminal und führen Sie folgende Befehle aus:

```bash
cd /Users/simonjanke/Projects/cortex-py
source /Users/simonjanke/miniforge3/bin/activate
conda activate base
pip install mcp
```

### 2. MCP Server testen

Testen Sie den MCP Server:

```bash
cd /Users/simonjanke/Projects/cortex-py
./start_mcp_cortex_server.sh
```

## 3. Claude Desktop Konfiguration

### Option A: Über das GUI (Empfohlen)

1. Öffnen Sie Claude Desktop
2. Gehen Sie zu Settings (⌘ + ,)
3. Klicken Sie auf "Developer"
4. Klicken Sie auf "Edit Config"
5. Fügen Sie diese Konfiguration in den entsprechenden Projekt-Bereich ein:

```json
{
  "mcpServers": {
    "cortex-py": {
      "command": "/Users/simonjanke/Projects/cortex-py/start_mcp_cortex_server.sh",
      "cwd": "/Users/simonjanke/Projects/cortex-py"
    }
  }
}
```

### Option B: Manuelle Bearbeitung

Alternativ können Sie die Konfiguration direkt in der `.claude.json` Datei bearbeiten:

1. Öffnen Sie `/Users/simonjanke/.claude.json`
2. Suchen Sie den Bereich für Ihr Projekt `/Users/simonjanke/Projects/cortex-py`
3. Fügen Sie die MCP Server Konfiguration hinzu:

```json
"/Users/simonjanke/Projects/cortex-py": {
  "allowedTools": [],
  "history": [...],
  "mcpServers": {
    "cortex-py": {
      "command": "/Users/simonjanke/Projects/cortex-py/start_mcp_cortex_server.sh",
      "cwd": "/Users/simonjanke/Projects/cortex-py"
    }
  },
  ...
}
```

## 4. Claude Desktop neu starten

Nach der Konfiguration starten Sie Claude Desktop neu.

## 5. Testen der Integration

Sobald der MCP Server verbunden ist, können Sie folgende Befehle in Claude Desktop verwenden:

- **cortex_run_command**: Führt Cortex CLI Befehle aus
- **cortex_add_knowledge**: Fügt Wissen zum Knowledge Graph hinzu  
- **cortex_search**: Durchsucht den Knowledge Graph

### Beispiele:

```
Führe den Cortex Status-Befehl aus
```

```
Durchsuche den Knowledge Graph nach "Machine Learning"
```

```
Füge neues Wissen hinzu: Titel "Python Best Practices", Inhalt "..."
```

## Verfügbare Tools und Ressourcen

### Tools:
1. **cortex_run_command**: Führt beliebige Cortex CLI Befehle aus
2. **cortex_add_knowledge**: Fügt neues Wissen hinzu
3. **cortex_search**: Durchsucht den Knowledge Graph

### Ressourcen:
1. **cortex://status**: Zeigt den aktuellen System-Status
2. **cortex://knowledge-graph**: Überblick über den Knowledge Graph

## Fehlerbehebung

### MCP Server startet nicht:
- Überprüfen Sie, ob die MCP-Bibliothek installiert ist: `pip list | grep mcp`
- Überprüfen Sie die Pfade in den Skripten
- Testen Sie den Server manuell: `python mcp_cortex_server.py`

### Claude Desktop erkennt den Server nicht:
- Überprüfen Sie die JSON-Syntax in der Konfiguration
- Stellen Sie sicher, dass der Pfad zum Startskript korrekt ist
- Überprüfen Sie die Dateiberechtigungen: `ls -la start_mcp_cortex_server.sh`

### Debugging:
- Logs finden Sie in der Claude Desktop Console
- Testen Sie einzelne Cortex-Befehle direkt: `python3 cortex_neo/cortex_cli.py status`
