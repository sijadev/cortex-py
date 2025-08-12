# Obsidian MCP Integration für Cortex AI System

## Übersicht

Die MCP (Model Context Protocol) Integration verbindet das Cortex AI System nahtlos mit Obsidian, um automatisch AI-Insights, Cross-Vault-Links und Chat-Sessions als strukturierte Notes zu synchronisieren.

## Features

### 🧠 AI Insights Sync
- Automatische Erstellung von Obsidian-Notes aus Cortex AI Insights
- Strukturierte Formatierung mit Metadaten
- Cross-Vault-Referenzen als Obsidian-Links
- Tag-basierte Organisation

### 🔗 Cross-Vault Linking
- Automatische bidirektionale Links zwischen verwandten Notes
- Link-Stärke-basierte Kategorisierung (Strong/Medium/Weak)
- Summary-Notes mit Analyse-Übersichten
- Tag-Korrelations-Analysen

### 💬 Chat-to-Obsidian Sync
- Automatische Extraktion von Entscheidungen aus Chat-Sessions
- Code-Snippets als Code-Fragment-Notes
- Action-Items mit Prioritäts-Bewertung
- Intelligente Topic-Erkennung

### ⚡ Real-time File Watching
- Überwachung von Vault-Änderungen in Echtzeit
- Automatische AI-Re-Analyse bei bedeutsamen Änderungen
- Debouncing und Batch-Verarbeitung
- Performance-optimierte Event-Behandlung

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Cortex AI System                         │
├─────────────────────────────────────────────────────────────┤
│ Multi-Vault AI Engine │ Cross-Vault Linker │ Chat Analyzer  │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCP Integration Layer                      │
├─────────────────────────────────────────────────────────────┤
│ obsidian_mcp_bridge.py │ chat_obsidian_sync.py │ file_watcher.py │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Obsidian Vault                           │
├─────────────────────────────────────────────────────────────┤
│ 02-Neural-Links/     │ Auto-generated Notes               │
│ ├── AI-Generated/    │ Cross-Vault Links                  │
│ ├── Summaries/       │ Chat Sessions                      │
│ └── Chat-Sessions/   │ Real-time Updates                  │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### 1. Dependencies installieren

```bash
cd /Users/simonjanke/Projects/cortex/00-System/Services
pip install -r requirements.txt
```

### 2. Obsidian MCP Server konfigurieren

Füge in `~/Library/Application Support/Claude/claude_desktop_config.json` hinzu:

```json
{
  "mcpServers": {
    "obsidian-cortex": {
      "command": "node",
      "args": ["/path/to/obsidian-mcp-server"],
      "env": {
        "VAULT_PATH": "/Users/simonjanke/Projects/cortex"
      }
    }
  }
}
```

## Verwendung

### Manuelle Synchronisation

```python
from obsidian_mcp_bridge import integrate_with_obsidian

# AI Insights und Links zu Obsidian syncen
result = await integrate_with_obsidian(
    ai_insights=insights,
    cross_vault_links=links,
    target_vault="cortex"
)

print(f"Synced: {result.notes_created} notes, {result.links_added} links")
```

### Chat-Session Sync

```python
from chat_obsidian_sync import sync_current_chat_to_obsidian

# Aktuelle Konversation syncen
await sync_current_chat_to_obsidian(
    conversation_text=chat_content,
    topic="MCP Integration Discussion"
)
```

### Real-time File Watching

```python
from file_watcher import WatcherIntegration

# File Watcher starten
integration = WatcherIntegration("/Users/simonjanke/Projects/cortex")
await integration.start()

# Läuft automatisch und triggered bei Änderungen AI-Analyse
```

### Cross-Vault-Linker mit Obsidian Integration

```python
from cross_vault_linker import CrossVaultLinker

linker = CrossVaultLinker()
# Automatische Obsidian-Sync ist standardmäßig aktiviert
report = linker.run_full_linking_cycle(sync_to_obsidian=True)
```

## Generierte Note-Strukturen

### AI Insight Note
```markdown
# Cross-Vault Pattern Discovery

> 🧠 **Cortex AI Generated Insight**
> Generated: 2025-01-10 14:30:22
> Confidence: 0.92

## Summary
Discovered consistent API design patterns across multiple projects

## Key Findings
- All authentication endpoints follow RESTful conventions
- Error handling uses consistent HTTP status codes

## Cross-Vault Connections
- **01-Projects**: [[ADR-004-API-Design-Approach]] (confidence: 0.95)
- **04-Code-Fragments**: [[Python-FastAPI-Patterns]] (confidence: 0.88)

## Tags
#api-design #patterns #cross-vault #cortex-ai #auto-generated
```

### Cross-Vault Link Summary
```markdown
# Cross-Vault Link Summary

> 🔗 **Automatically Generated Cross-Vault Connections**
> Generated: 2025-01-10 14:30:25
> Total Suggestions: 15

## Strong Connections (≥0.8)
### [[project-overview.md]] ↔ [[ADR-004-Architecture.md]]
- **Confidence**: 0.92
- **Shared Tags**: #architecture #api-design #multi-vault
- **Reason**: Strong semantic correlation in architectural decisions

## Tag Correlation Analysis
- **#api-design** (12 connections)
- **#architecture** (8 connections)
- **#testing** (6 connections)
```

### Chat Session Note
```markdown
# Claude Chat - MCP Integration Discussion

> 💬 **Claude Chat Session**
> Date: 2025-01-10 14:30:00
> Duration: ~15 minutes
> Messages: 12

## Summary
Conversation that made 2 key decision(s), identified 4 action item(s), addressed 3 question(s).

## Key Insights
- MCP integration enables seamless Obsidian sync
- Real-time file watching improves workflow efficiency

## Decisions Made
- **Integration Architecture**: Use MCP bridge pattern for Obsidian communication
  - *Rationale*: Provides clean separation and testability

## Action Items
- [ ] Implement comprehensive test coverage (priority: high)
- [ ] Create file watcher for real-time sync (priority: medium)

## Related Notes
- [[Obsidian Integration]]
- [[Cross-Vault Linking]]

#chat-session #mcp-integration #architecture #claude-ai
```

## Konfiguration

### WatcherConfig

```python
config = WatcherConfig(
    watch_patterns=['*.md', '*.txt'],
    ignore_patterns=['.*', '*.tmp', '*~', '*.log'],
    debounce_seconds=2,        # Wartezeit für Batch-Verarbeitung
    batch_size=5,              # Anzahl Änderungen vor Verarbeitung
    analysis_delay=10,         # Verzögerung vor AI-Analyse
    max_file_size_mb=10        # Max. Dateigröße
)
```

## Tests

### Unit Tests ausführen

```bash
cd /Users/simonjanke/Projects/cortex/00-System/Tests
python -m pytest test_obsidian_integration.py -v
```

### Integration Tests

```bash
python -m pytest test_integration_obsidian.py -v --asyncio-mode=auto
```

### File Watcher testen

```bash
cd /Users/simonjanke/Projects/cortex/00-System/Cross-Vault-Linker
python file_watcher.py --test-mode --duration 30
```

## Workflow-Beispiele

### 1. Entwickler-Workflow
1. **Entwickler arbeitet in Obsidian** - schreibt Notizen, trifft Entscheidungen
2. **File Watcher erkennt Änderungen** - triggert automatisch AI-Analyse
3. **AI findet neue Patterns** - erstellt Insight-Notes
4. **Cross-Vault-Linker** - verbindet verwandte Inhalte automatisch
5. **Obsidian zeigt neue Links** - Entwickler entdeckt Zusammenhänge

### 2. Chat-Integration-Workflow
1. **Chat mit Claude Code** - diskutiert Implementierung
2. **Automatische Extraktion** - Entscheidungen, Code, Action-Items
3. **Note-Erstellung** - strukturierte Chat-Session-Note
4. **ADR-Generierung** - wichtige Entscheidungen werden zu ADRs
5. **Code-Fragment-Notes** - Code-Snippets als eigene Notes

### 3. Knowledge Discovery
1. **AI analysiert alle Vaults** - findet versteckte Patterns
2. **Korrelations-Erkennung** - Tags und Inhalte werden verknüpft
3. **Insight-Generierung** - neue Erkenntnisse über Projekt-Struktur
4. **Automatische Verlinkung** - verwandte Notes werden verbunden
5. **Wissensaufbau** - kontinuierliche Verbesserung des Knowledge Graph

## Troubleshooting

### MCP Server nicht gefunden
```bash
# MCP Config prüfen
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Fallback-Modus verwenden (direkte Dateisystem-Operationen)
export OBSIDIAN_MCP_FALLBACK=true
```

### File Watcher funktioniert nicht
```bash
# Watchdog installieren
pip install watchdog

# Berechtigungen prüfen
ls -la /Users/simonjanke/Projects/cortex

# Test-Modus starten
python file_watcher.py --test-mode --duration 10
```

### Performance-Probleme
```bash
# File Watcher Statistiken
python -c "from file_watcher import WatcherIntegration; import asyncio; 
integration = WatcherIntegration('/Users/simonjanke/Projects/cortex')
print(integration.get_status())"

# Batch-Größe reduzieren
# In WatcherConfig: batch_size=3, debounce_seconds=5
```

## Weiterentwicklung

### Geplante Features
- [ ] **Semantic Search Integration** - Vektor-basierte Ähnlichkeitssuche
- [ ] **Template-basierte Note-Erstellung** - anpassbare Note-Vorlagen  
- [ ] **Multi-Language Support** - Unterstützung für verschiedene Sprachen
- [ ] **Advanced Analytics** - detaillierte Metriken und Dashboards
- [ ] **Plugin System** - erweiterbare Integration-Plugins

### API Extensions
- [ ] **REST API** - HTTP-Interface für externe Integrations
- [ ] **WebSocket Support** - Real-time Updates für Web-Interfaces
- [ ] **GraphQL Queries** - flexible Datenabfragen
- [ ] **Webhook Integration** - Event-basierte externe Notifications

## Lizenz

Teil des Cortex AI Systems - siehe Haupt-Repository für Lizenzinformationen.

## Support

Bei Problemen oder Fragen:
1. **Tests ausführen** - `python -m pytest test_obsidian_integration.py`
2. **Logs prüfen** - `tail -f /Users/simonjanke/Projects/cortex/00-System/*/logs/*.log`
3. **Issue erstellen** - im Cortex Repository

---

*Diese Integration wurde entwickelt, um eine nahtlose Verbindung zwischen AI-gestützter Wissensverarbeitung und praktischer Notiz-Organisation zu schaffen.*