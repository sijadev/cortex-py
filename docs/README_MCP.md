# Cortex MCP Server für Claude Desktop

Dieses Projekt stellt einen MCP (Model Context Protocol) Server bereit, der Ihr Cortex-System mit Claude Desktop verbindet.

## 🚀 Schnellstart

1. **Installieren Sie die Abhängigkeiten:**
   ```bash
   cd /Users/simonjanke/Projects/cortex-py
   pip install mcp
   ```

2. **Testen Sie das Setup:**
   ```bash
   python3 test_mcp_setup.py
   ```

3. **Konfigurieren Sie Claude Desktop:**
   - Öffnen Sie Claude Desktop
   - Gehen Sie zu Settings (⌘ + ,) → Developer → Edit Config
   - Fügen Sie die Konfiguration aus `claude_desktop_config_example.json` hinzu

4. **Starten Sie Claude Desktop neu**

## 📁 Wichtige Dateien

- `mcp_cortex_server.py` - Der Haupt-MCP-Server
- `start_mcp_cortex_server.sh` - Startskript für den Server
- `test_mcp_setup.py` - Test-Skript zur Überprüfung des Setups
- `claude_desktop_config_example.json` - Beispiel-Konfiguration für Claude Desktop
- `MCP_SETUP_ANLEITUNG.md` - Detaillierte Setupanleitung

## 🛠 Verfügbare Tools

Nach erfolgreicher Konfiguration haben Sie in Claude Desktop Zugriff auf folgende Tools:

### 1. cortex_run_command
Führt beliebige Cortex CLI Befehle aus.
```
Führe den Cortex Status-Befehl aus
```

### 2. cortex_add_knowledge
Fügt neues Wissen zum Knowledge Graph hinzu.
```
Füge neues Wissen hinzu: Titel "Python Best Practices", Inhalt "Verwende Type Hints und Docstrings"
```

### 3. cortex_search
Durchsucht den Knowledge Graph.
```
Durchsuche den Knowledge Graph nach "Machine Learning"
```

## 📊 Verfügbare Ressourcen

- **cortex://status** - Aktueller System-Status
- **cortex://knowledge-graph** - Überblick über den Knowledge Graph

## 🔧 Fehlerbehebung

### Server startet nicht
```bash
# Überprüfen Sie die MCP-Installation
pip list | grep mcp

# Testen Sie den Server manuell
python3 mcp_cortex_server.py

# Überprüfen Sie die Berechtigungen
ls -la start_mcp_cortex_server.sh
```

### Claude Desktop erkennt den Server nicht
1. Überprüfen Sie die JSON-Syntax in der Konfiguration
2. Stellen Sie sicher, dass alle Pfade korrekt sind
3. Starten Sie Claude Desktop neu
4. Schauen Sie in die Claude Desktop Logs (Developer Tools)

## 🏗 Anpassungen

Der MCP Server kann leicht angepasst werden:

1. **Neue Tools hinzufügen:** Erweitern Sie die `handle_list_tools()` und `handle_call_tool()` Funktionen in `mcp_cortex_server.py`

2. **Neue Ressourcen hinzufügen:** Erweitern Sie die `handle_list_resources()` und `handle_read_resource()` Funktionen

3. **Cortex CLI Befehle anpassen:** Passen Sie die Befehlsaufrufe in den Tool-Handlers an Ihre spezifischen Cortex-Befehle an

## 📝 Logs und Debugging

Für Debugging können Sie:

1. **Direkte Tests:**
   ```bash
   # Testen Sie einzelne Cortex-Befehle
   python3 cortex_neo/cortex_cli.py --help
   python3 cortex_neo/cortex_cli.py status
   ```

2. **MCP Server Logs:**
   - Ausgaben werden in der Claude Desktop Konsole angezeigt
   - Fügen Sie `print()` Statements in `mcp_cortex_server.py` für Debugging hinzu

3. **Claude Desktop Developer Tools:**
   - Öffnen Sie die Developer Tools in Claude Desktop für detaillierte Logs

## 🤝 Integration mit anderen Systemen

Der MCP Server kann erweitert werden, um mit anderen Systemen zu kommunizieren:

- **APIs:** Fügen Sie HTTP-Requests zu externen APIs hinzu
- **Datenbanken:** Direkte Datenbankverbindungen für erweiterte Abfragen
- **Dateisysteme:** Dateioperation für Knowledge Management
- **CI/CD:** Integration mit Build- und Deployment-Pipelines

## 📚 Weitere Ressourcen

- [MCP Dokumentation](https://modelcontextprotocol.io/)
- [Claude Desktop MCP Integration](https://docs.anthropic.com/claude/docs/desktop-app)
- Cortex-spezifische Dokumentation in den entsprechenden Projektordnern

---

**Erstellt für das Cortex-py Projekt** 🧠

Für Fragen oder Probleme, siehe `MCP_SETUP_ANLEITUNG.md` oder führen Sie `python3 test_mcp_setup.py` aus.
