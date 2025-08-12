# Cortex-CLI

Eine umfassende Befehlszeilen-Schnittstelle für Cortex-Workspaces.

## Installation

```bash
# Grundinstallation
./install.sh

# Mit Entwicklertools
./install.sh --dev

# Mit Cortex-AI Integration
./install.sh --ai
```

## Verwendung

```bash
# Hilfe anzeigen
cortex --help

# Link-Befehle
cortex linking --help
cortex linking validate
cortex linking rule-linker --run

# Analysebefehle
cortex analyze --help

# Testbefehle
cortex test --help

# Cortex-AI Befehle (wenn aktiviert)
cortex ai --help
cortex ai chat -i  # Interaktiver Chat
cortex ai analyze -f datei.md
cortex ai validate
```

## Cortex-AI Webanwendung

```bash
# Starten der Webanwendung
cortex-ai

# Mit angepasstem Port
cortex-ai --port=8080

# Ohne Browser zu öffnen
cortex-ai --no-browser
```

## Programmierbare API

Sie können die Cortex-Funktionen auch aus Ihrem eigenen Python-Code aufrufen:

```python
from cortex.cli.linking import validate_command
from cortex.cli.ai_commands import chat, analyze

# Link-Validierung ausführen
result = validate_command(cortex_path='/path/to/workspace', fix=True)
print(f"Ergebnis: {result['success']}")

# Mit Cortex-AI chatten
chat_result = chat(message="Was ist Cortex?", vault_id=1)
print(f"Antwort: {chat_result['response']}")
```

## Konfiguration

Die Konfiguration erfolgt über die Datei `config/cortex.yaml`. Um Cortex-AI zu aktivieren, fügen Sie folgendes hinzu:

```yaml
cortex_ai:
  enabled: true
  api_url: "http://localhost:8000"
```

## Entwicklung

```bash
# Installieren der Entwicklungsabhängigkeiten
./install.sh --dev

# Tests ausführen
pytest

# Code-Stil prüfen
black cortex/
pylint cortex/
```
