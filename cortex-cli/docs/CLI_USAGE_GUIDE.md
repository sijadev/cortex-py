# Cortex CLI - Nutzungsanleitung

## Installation und Setup

Die Cortex CLI ist jetzt vollständig dynamisch und kann von überall aus verwendet werden, ohne feste Pfade zu verwenden.

### 1. Installation der CLI
```bash
cd /workspaces/cortex-py/cortex-cli
pip install -e . --force-reinstall
```

### 2. Wrapper-Script für universellen Zugriff
Das Wrapper-Script ermöglicht es, die CLI von jedem Verzeichnis aus zu verwenden:
```bash
# Das Script ist bereits verfügbar unter:
/workspaces/cortex-py/cortex-cli-wrapper

# Optional: In PATH einbinden für einfacheren Zugriff
sudo ln -s /workspaces/cortex-py/cortex-cli-wrapper /usr/local/bin/cortex-cli
```

## Verwendung

### Von überall aus verwenden
Die CLI funktioniert aus jedem Verzeichnis:

```bash
# Status prüfen
/workspaces/cortex-py/cortex-cli-wrapper status

# AI-Chat von /tmp aus
cd /tmp
/workspaces/cortex-py/cortex-cli-wrapper ai chat -m "Teste von /tmp"

# Datei analysieren von /home aus
cd /home/vscode
/workspaces/cortex-py/cortex-cli-wrapper ai analyze -f /workspaces/cortex-py/cortex/README.md

# Links validieren aus Root-Verzeichnis
cd /
/workspaces/cortex-py/cortex-cli-wrapper ai validate
```

### Verfügbare Befehle

#### Allgemein
- `status` - Workspace Status anzeigen
- `init` - Neues Cortex Workspace initialisieren
- `--help` - Hilfe anzeigen

#### AI-Befehle
- `ai chat -m "Nachricht"` - Einmalige Chat-Nachricht
- `ai chat -i` - Interaktiver Chat-Modus
- `ai analyze -f /path/file.md` - Datei analysieren
- `ai analyze -c "Text"` - Text analysieren
- `ai validate` - Links validieren

#### Erweiterte Befehle
- `analysis` - Analysis and learning commands
- `linking` - Linking und Vault-Management
- `test` - Test-Befehle
- `testing` - Test-Befehle (alt)

### Dynamische Pfad-Erkennung

Die CLI erkennt automatisch Cortex-Installationen:

1. **Aktuelle Verzeichnis-Prüfung**: Sucht nach Cortex-Indikatoren im aktuellen Verzeichnis
2. **Eltern-Verzeichnis-Suche**: Durchsucht Elternverzeichnisse nach Cortex-Root
3. **Standard-Pfade**: Fallback auf bekannte Cortex-Installationen
4. **Umgebungsvariable**: `CORTEX_PATH` kann gesetzt werden

### Indikatoren für Cortex-Root
Die CLI erkennt ein Verzeichnis als Cortex-Root anhand dieser Dateien/Ordner:
- `.cortex/`
- `cortex-cmd`
- `00-System/`
- `01-Projects/`
- `99-Archive/`

### JSON-Ausgabe
Alle Befehle unterstützen `--json` für maschinelle Verarbeitung:
```bash
/workspaces/cortex-py/cortex-cli-wrapper status --json
/workspaces/cortex-py/cortex-cli-wrapper ai chat -m "Test" --json
```

### Verbose-Modus
Für Debugging und detaillierte Informationen:
```bash
/workspaces/cortex-py/cortex-cli-wrapper --verbose status
/workspaces/cortex-py/cortex-cli-wrapper -v ai validate
```

## Vorteile der neuen CLI

### ✅ Keine festen Pfade
- Arbeitet von jedem Verzeichnis aus
- Automatische Cortex-Erkennung
- Flexible Cloud/Local-Nutzung

### ✅ Modular und erweiterbar
- Klare Trennung der Befehle
- Einfach neue Funktionen hinzufügen
- Konsistente Fehlerbehandlung

### ✅ Rich-Ausgabe
- Farbige und formatierte Ausgabe
- Markdown-Rendering
- Progress-Indikatoren

### ✅ Python-Ökosystem
- Pip-Installation
- Entry Points
- Testbare Module

## Unterschied zu cortex-cmd

- **cortex-cli**: Python-basiert, moderne Features, portable
- **cortex-cmd**: Bash-basiert, System-Integration, lokale Services

Beide können parallel verwendet werden und ergänzen sich.
