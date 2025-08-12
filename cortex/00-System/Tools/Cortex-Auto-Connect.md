# 🔗 Cortex Auto-Connect Configuration

*Automatische Systemverbindung für neue Claude-Sessions*

## ⚡ **SOFORTIGE VERBINDUNG**

**CORTEX-PFAD**: `/Users/simonjanke/Projects/cortex`
**OBSIDIAN-PORT**: `27124`
**SERVICE-NAME**: `com.cortex.learning.service`

## 🤖 **CLAUDE AUTO-SETUP**

Kopiere diese Befehle für eine neue Claude-Session:

```markdown
CORTEX AUTO-CONNECT:

1. System-Pfad: /Users/simonjanke/Projects/cortex
2. Obsidian-Test: obsidian:search_notes mit query "cortex"
3. Service-Check: Cortex Learning Service Status prüfen
4. Tools verfügbar: filesystem, obsidian, super-shell, artifacts
```

## 📋 **VERFÜGBARE BEFEHLE**

### **Cortex Core Commands:**
- `obsidian:search_notes` - Notizen durchsuchen
- `obsidian:read_notes` - Notizen lesen
- `filesystem:read_text_file` - Dateien lesen
- `filesystem:list_directory` - Verzeichnisse anzeigen
- `super-shell:execute_command` - Cortex-Service Befehle

### **Service Commands:**
- Service Status: `launchctl list com.cortex.learning.service`
- Service Start: `launchctl start com.cortex.learning.service`
- Service Logs: Logs unter `/00-System/Services/logs/`

## 🎯 **SCHNELLSTART FÜR CLAUDE**

```bash
# Direkte Verbindung testen:
obsidian:search_notes → "cortex"
filesystem:list_directory → "/Users/simonjanke/Projects/cortex"
```

## 📊 **SYSTEM-STATUS-CHECK**

### Obsidian Vault:
- ✅ Konfiguriert auf Port 27124
- ✅ Local REST API Plugin aktiv
- ✅ MCP Tools Plugin installiert

### Learning Service:
- ✅ Python Virtual Environment konfiguriert
- ✅ Alle Dependencies installiert
- ✅ Service läuft automatisch alle 30 Minuten

### File System:
- ✅ Vollzugriff auf Cortex-Verzeichnis
- ✅ Alle Templates und Algorithmen verfügbar
- ✅ State-Management.md bereit für Context-Loading

---
**READY-STATUS**: ✅ Alle Systeme betriebsbereit für sofortige Nutzung
**NEXT-SESSION**: Claude kann direkt mit Cortex-Befehlen starten
