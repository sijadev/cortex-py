# Neo4J Mapping Projekt

Dieses Repository enthält die Grundstruktur und ein Beispielskript für die Abbildung von Workflows (z.B. Decision-Workflow) aus Obsidian/Cortex nach Neo4J.

## Setup

1. Python-Umgebung anlegen:
	```bash
	python -m venv .venv
	source .venv/bin/activate
	pip install -r requirements.txt
	```

2. Neo4J-Instanz bereitstellen (lokal oder remote) und Zugangsdaten ggf. als Umgebungsvariablen setzen:
	- `NEO4J_URI` (z.B. bolt://localhost:7687)
	- `NEO4J_USER` (z.B. neo4j)
	- `NEO4J_PASSWORD`

3. Beispielskript ausführen:
	```bash
	python create_neo4j_workflow.py
	```

## Backup & Restore (Docker)

Dieses Projekt bringt ein Skript zur Sicherung und Wiederherstellung der in Docker betriebenen Neo4j-Instanz mit.

Voraussetzungen:
- Docker ist installiert und lauffähig
- Der Container aus `docker-compose.yml` existiert (Standardname: `neo4j`)
  - Falls noch nicht geschehen: `docker compose up -d`

Skript: `cortex-neo/backup.sh`
- Führt Offline-Operationen aus (Container wird für Dump/Load gestoppt und danach wieder gestartet)
- Nutzt einen One-Off-Container (`neo4j:5`) und `neo4j-admin` zum Erstellen/Laden von Dumps
- Ermittelt automatisch das Volume, das im Container unter `/data` gemountet ist

Verwendung:
```bash
# Backup erstellen (legt Datei in ./backups ab, z.B. neo4j-YYYYmmdd-HHMMSS.dump)
./backup.sh backup

# Backup mit eigenem Namen
./backup.sh backup --file neo4j.dump

# Restore (destruktiv, Container wird gestoppt) – erfordert --force
./backup.sh restore --file neo4j.dump --force
```

Optionen:
- `--name <container>`  Name des Neo4j-Containers (Default: neo4j)
- `--db <name>`         Datenbankname (Default: neo4j)
- `--out <dir>`         Zielverzeichnis für Backups (Default: ./backups)
- `--in <dir>`          Quellverzeichnis für Restore (Default: ./backups)
- `--file <name.dump>`  Dateiname des Dumps
- `--force`             Erforderlich für Restore (bestätigt Destruktivität)

Hinweise:
- Das Skript stoppt den Container für sichere Offline-Backups/Restores
- Dumps werden standardmäßig als `<db>.dump` erstellt; bei abweichendem `--file` wird die Datei entsprechend umbenannt
- Scheitert die automatische Volumenerkennung, bitte sicherstellen, dass der Container existiert und mit Compose erzeugt wurde (`docker compose up -d`)

## Wissensgraph: Notes, Tags, Templates, Links

Neben Workflows können Notizen, Tags, Templates und Links modelliert und verwaltet werden.

Basis-CLI: `cortex-neo/cortex_cli.py`

Beispiele:
```bash
# Notes/Tags/Templates anlegen
python cortex-neo/cortex_cli.py add-note Home
python cortex-neo/cortex_cli.py add-tag important
python cortex-neo/cortex_cli.py add-template Project

# Verknüpfungen
python cortex-neo/cortex_cli.py link-notes Home ProjectA
python cortex-neo/cortex_cli.py tag-note ProjectA important
python cortex-neo/cortex_cli.py use-template ProjectA Project

# Auflisten und Anzeigen
python cortex-neo/cortex_cli.py list-notes
python cortex-neo/cortex_cli.py list-tags
python cortex-neo/cortex_cli.py list-templates
python cortex-neo/cortex_cli.py show-note ProjectA
```

## Migration aus YAML/JSON

Strukturdatei (siehe `cortex-neo/sample_structure.yaml`) kann importiert werden, um Notes, Tags, Templates und Links idempotent anzulegen.

Ausführen:
```bash
python cortex-neo/cortex_cli.py migrate cortex-neo/sample_structure.yaml
```

Schema der Datei (vereinfachter Überblick):
```yaml
notes: [Home, ProjectA]
templates: [Project, Decision]
tags: [important, research]
links:
  - { from: Home, to: ProjectA }
assignments:
  uses_template:
    - { note: ProjectA, template: Project }
  tagged_with:
    - { note: ProjectA, tag: important }
```

## Auto-Verlinkung (Tags/Templates)

Neo kann LINKS_TO-Beziehungen automatisch aus gemeinsamen Tags oder Templates erzeugen.

Befehle:
```bash
# Auto-Links erzeugen (nach Tags, Templates oder beidem)
python cortex-neo/cortex_cli.py auto-link --by tag --min-shared 1 --max-per-note 50
python cortex-neo/cortex_cli.py auto-link --by template
python cortex-neo/cortex_cli.py auto-link --by all

# Auto-Links entfernen (nur automatisch erzeugte, r.auto=true)
python cortex-neo/cortex_cli.py clear-auto-links
```

Erläuterungen:
- Voraussetzungen: Mindestens zwei Notes müssen denselben Tag bzw. dasselbe Template verwenden.
- Parameter:
  - `--by`: tag | template | all (Standard: tag)
  - `--min-shared`: Mindestanzahl gemeinsamer Tags/Templates (Standard: 1)
  - `--max-per-note`: Top‑K Kandidaten pro Note (Standard: 50)
- Eigenschaften auf der Beziehung:
  - `r.auto = true` (als Kennzeichnung)
  - `r.tags_shared` und/oder `r.templates_shared`
  - `r.weight = (tags_shared + templates_shared)`

Beispiel:
```bash
python cortex-neo/cortex_cli.py add-note A
python cortex-neo/cortex_cli.py add-note B
python cortex-neo/cortex_cli.py add-tag t1
python cortex-neo/cortex_cli.py tag-note A t1
python cortex-neo/cortex_cli.py tag-note B t1
python cortex-neo/cortex_cli.py auto-link --by tag --min-shared 1
python cortex-neo/cortex_cli.py validate-graph
```

## Link-Analyse & KI-Validierung

Analysiere und korrigiere LINKs_TO-Beziehungen in Neo4j und prüfe sie optional mit dem Cortex-AI-Service.

Befehle:
```bash
# Analyse (Selbst-Links, Duplikate, Orphans, Auto-Props)
python cortex-neo/cortex_cli.py link-analyze
python cortex-neo/cortex_cli.py link-analyze --json

# Fixes (standardmäßig: Selbst-Links löschen, Duplikate deduplizieren, Auto-Props auffüllen, Gewicht neu berechnen)
python cortex-neo/cortex_cli.py link-fix --dry-run
python cortex-neo/cortex_cli.py link-fix --remove-auto-below 1

# KI-Validierung (ruft den FastAPI-Service auf /ai/validate-links)
# Optional Umgebungsvariable: CORTEX_AI_URL (Default: http://127.0.0.1:8000)
python cortex-neo/cortex_cli.py link-validate-ai
python cortex-neo/cortex_cli.py link-validate-ai --json
```

Hinweise:
- `link-analyze` gibt Kennzahlen und Beispiele aus (JSON-Option für Tooling).
- `link-fix --dry-run` zeigt geplante Änderungen an, ohne sie auszuführen.
- `link-fix --remove-auto-below <x>` entfernt Auto-Links mit Gewicht < x.
- `link-validate-ai` benötigt laufenden FastAPI-Service (siehe cortex-cli/bin/cortex-ai).

## Inhalt
- `create_neo4j_workflow.py`: Legt einen Beispiel-Workflow mit Schritten in Neo4J an
- `cortex_cli.py`: CLI für Workflows und Wissensgraph (Notes/Tags/Templates/Links)
- `migrate_structure.py`: Migration aus YAML/JSON
- `sample_structure.yaml`: Beispiel-Strukturdatei
- `backup.sh`: Backup-/Restore-Helferskript für Neo4j (Docker)
- `backups/`: Ablageordner für erzeugte Dump-Dateien
- `requirements.txt`: Python-Abhängigkeiten
- `.gitignore`: Ignoriert Build-, Editor- und Umgebungsdateien
- `README.md`: Diese Anleitung

## Konzept
Das Mapping orientiert sich am Konzept aus `Konzept.md` (siehe Hauptrepository). Es können weitere Mapping-Skripte für Notizen, Tags, Templates etc. ergänzt werden.

## Weiterentwicklung
- Erweiterung um weitere Strukturen (z.B. Notizen, Tags, Templates)
- Automatisierte Extraktion aus Obsidian Vaults
- Validierung und Visualisierung der Neo4J-Struktur

---

Fragen oder Wünsche? Siehe Issues oder melde dich direkt im Hauptprojekt!
