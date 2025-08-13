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

## Inhalt
- `create_neo4j_workflow.py`: Legt einen Beispiel-Workflow mit Schritten in Neo4J an
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
