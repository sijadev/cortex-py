#!/usr/bin/env python3
"""
Governance CLI mit erweiterten Funktionen für Datenmanagement
Mit Neo4j-Integration, dynamischer Template-Verwaltung und intelligenter Keyword-Extraktion
"""

import click
import os
import sys
import json
import yaml
from datetime import datetime

# Pfad für Data Governance Engine
sys.path.append("/Users/simonjanke/Projects/cortex-py")
from src.governance.data_governance import (
    DataGovernanceEngine,
    ValidationResult,
    print_validation_result,
)


@click.group()
def cli():
    """🛡️ Data Governance CLI - Dynamische Systemverwaltung"""
    pass


# Template-Management
@cli.group()
def templates():
    """📋 Template-Management"""
    pass


@templates.command("list")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
@click.option("--project-type", help="Filtere nach Projekt-Typ")
@click.option("--keywords", help="Filtere nach Keywords (kommagetrennt)")
def list_templates(config, project_type, keywords):
    """Zeigt alle verfügbaren Templates an - mit intelligenter Neo4j-Integration."""
    governance = DataGovernanceEngine(config)

    # Verwende neue Context-basierte Methode
    if project_type or keywords:
        keyword_list = keywords.split(",") if keywords else None
        templates_dict = governance.get_templates_for_context(project_type, keywords=keyword_list)
    else:
        templates_dict = governance.get_templates()

    print("📋 Verfügbare Templates:")
    if project_type:
        print(f"   🎯 Gefiltert nach Projekt-Typ: {project_type}")
    if keywords:
        print(f"   🔑 Gefiltert nach Keywords: {keywords}")
    print("=" * 50)

    for name, details in templates_dict.items():
        print(f"\n🏷️ {name}")
        print(f"   📝 Erforderliche Sektionen: {', '.join(details['required_sections'])}")
        print(f"   🏷️ Vorgeschlagene Tags: {', '.join(details['suggested_tags'])}")
        print(f"   🔄 Workflow-Step: {details.get('workflow_step', 'Nicht zugeordnet')}")

        # Neo4j spezifische Informationen
        if "relevance_score" in details:
            print(f"   🎯 Relevanz-Score: {details['relevance_score']}")

        standards = details.get("content_standards", {})
        if standards:
            print(f"   📏 Min. Länge: {standards.get('min_length', 'Nicht definiert')}")
            if standards.get("required_keywords"):
                print(f"   🔑 Erforderliche Keywords: {', '.join(standards['required_keywords'])}")


@templates.command("add")
@click.argument("name")
@click.option("--sections", help="Erforderliche Sektionen (kommagetrennt)")
@click.option("--tags", help="Vorgeschlagene Tags (kommagetrennt)")
@click.option("--workflow-step", help="Zugeordneter Workflow-Step")
@click.option("--min-length", type=int, default=100, help="Minimale Content-Länge")
@click.option("--keywords", help="Erforderliche Keywords (kommagetrennt)")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def add_template(name, sections, tags, workflow_step, min_length, keywords, config):
    """Fügt ein neues Template hinzu."""
    governance = DataGovernanceEngine(config)

    required_sections = sections.split(",") if sections else []
    suggested_tags = tags.split(",") if tags else []
    required_keywords = keywords.split(",") if keywords else []

    content_standards = {"min_length": min_length, "required_keywords": required_keywords}

    governance.add_template(
        name=name,
        required_sections=required_sections,
        suggested_tags=suggested_tags,
        workflow_step=workflow_step,
        content_standards=content_standards,
    )

    print(f"✅ Template '{name}' erfolgreich hinzugefügt")

    # Optional: In Konfigurationsdatei speichern
    if click.confirm("💾 In Konfigurationsdatei speichern?"):
        save_to_config_file(governance, config or "governance_config.yaml")


@templates.command("validate")
@click.argument("template_name")
@click.argument("content_file", type=click.Path(exists=True))
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def validate_template(template_name, content_file, config):
    """Validiert Content gegen ein Template."""
    governance = DataGovernanceEngine(config)

    # Content aus Datei laden
    with open(content_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Validierung durchführen
    result = governance.validate_note_creation(
        name=f"Test Note ({template_name})",
        content=content,
        description="Test-Validierung",
        note_type="",
        template=template_name,
    )

    print_validation_result(result, f"Template '{template_name}' Validierung")


@templates.command("validate-smart")
@click.argument("content_file", type=click.Path(exists=True))
@click.option("--config", help="Pfad zur Konfigurationsdatei")
@click.option("--project-type", help="Projekt-Typ für intelligente Template-Auswahl")
@click.option("--project-name", help="Projekt-Name")
@click.option("--keywords", help="Keywords für Template-Matching (kommagetrennt)")
def validate_smart_template(content_file, config, project_type, project_name, keywords):
    """Intelligente Validierung mit automatischer Template-Erkennung aus Neo4j."""
    governance = DataGovernanceEngine(config)

    # Content aus Datei laden
    with open(content_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Keywords verarbeiten
    keyword_list = keywords.split(",") if keywords else None

    # Name aus Dateinamen ableiten
    note_name = os.path.basename(content_file).replace(".md", "").replace("_", " ")

    print(f"🤖 Intelligente Template-Validierung für: {note_name}")
    print(f"📁 Datei: {content_file}")
    if project_type:
        print(f"🎯 Projekt-Typ: {project_type}")
    if project_name:
        print(f"📂 Projekt: {project_name}")
    if keywords:
        print(f"🔑 Keywords: {keywords}")
    print("=" * 60)

    # Verwende erweiterte Context-Validierung
    result = governance.validate_note_creation_with_context(
        name=note_name,
        content=content,
        description="Smart-Validierung aus CLI",
        project_type=project_type,
        project_name=project_name,
        keywords=keyword_list,
    )

    print_validation_result(result, note_name)


@templates.command("create-for-project")
@click.argument("project_type")
@click.argument("project_name")
@click.option("--keywords", help="Keywords für Template-Generierung (kommagetrennt)")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def create_project_template(project_type, project_name, keywords, config):
    """Erstellt automatisch Templates für neues Projekt in Neo4j."""
    governance = DataGovernanceEngine(config)

    keyword_list = keywords.split(",") if keywords else []

    print(f"🚀 Erstelle Template für Projekt: {project_name}")
    print(f"🎯 Typ: {project_type}")
    print(f"🔑 Keywords: {', '.join(keyword_list)}")
    print("=" * 50)

    # Template über Neo4j Manager erstellen
    if governance.neo4j_manager.is_connected():
        created_templates = governance.neo4j_manager.create_template_if_missing(
            project_type, project_name, keyword_list
        )

        if created_templates:
            print("✅ Template erfolgreich erstellt!")
            for template_name, template_config in created_templates.items():
                print(f"\n📋 Template: {template_name}")
                print(f"   📝 Sektionen: {', '.join(template_config['required_sections'])}")
                print(f"   🏷️ Tags: {', '.join(template_config['suggested_tags'])}")
                print(f"   🔄 Workflow: {template_config['workflow_step']}")
        else:
            print("ℹ️ Template bereits vorhanden - keine Erstellung notwendig")
    else:
        print("❌ Neo4j nicht verfügbar - Template kann nicht erstellt werden")


# Workflow-Management
@cli.group()
def workflows():
    """🔄 Workflow-Management"""
    pass


@workflows.command("list")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def list_workflows(config):
    """Zeigt alle verfügbaren Workflows an."""
    governance = DataGovernanceEngine(config)
    workflows_dict = governance.get_workflows()

    print("🔄 Verfügbare Workflows:")
    print("=" * 50)

    for name, details in workflows_dict.items():
        print(f"\n📋 {name}")
        print(f"   🔗 Steps: {' → '.join(details['steps'])}")
        print(f"   📋 Templates: {', '.join(details.get('templates', []))}")
        print(f"   🤖 Auto-Assign: {'Ja' if details.get('auto_assign', False) else 'Nein'}")


@workflows.command("add")
@click.argument("name")
@click.option("--steps", required=True, help="Workflow-Steps (kommagetrennt)")
@click.option("--templates", help="Zugeordnete Templates (kommagetrennt)")
@click.option("--auto-assign", is_flag=True, help="Automatische Zuordnung aktivieren")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def add_workflow(name, steps, templates, auto_assign, config):
    """Fügt einen neuen Workflow hinzu."""
    governance = DataGovernanceEngine(config)

    steps_list = steps.split(",")
    templates_list = templates.split(",") if templates else []

    governance.add_workflow(
        name=name, steps=steps_list, templates=templates_list, auto_assign=auto_assign
    )

    print(f"✅ Workflow '{name}' erfolgreich hinzugefügt")
    print(f"   🔗 Steps: {' → '.join(steps_list)}")

    # Optional: In Konfigurationsdatei speichern
    if click.confirm("💾 In Konfigurationsdatei speichern?"):
        save_to_config_file(governance, config or "governance_config.yaml")


@workflows.command("progress")
@click.argument("workflow_name")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def workflow_progress(workflow_name, config):
    """Zeigt Fortschritt eines Workflows (simuliert)."""
    governance = DataGovernanceEngine(config)
    workflows_dict = governance.get_workflows()

    if workflow_name not in workflows_dict:
        print(f"❌ Workflow '{workflow_name}' nicht gefunden")
        return

    workflow = workflows_dict[workflow_name]
    steps = workflow["steps"]

    print(f"🔄 Workflow-Fortschritt: {workflow_name}")
    print("=" * 50)

    # Simuliere Fortschritt (in echter Anwendung aus Neo4j)
    import random

    for i, step in enumerate(steps):
        completed = random.choice([True, False])
        notes_count = random.randint(0, 5)

        status = "✅" if completed else "⏳"
        print(f"{status} Step {i+1}: {step} ({notes_count} Notes)")

    completed_steps = sum(1 for _ in range(len(steps)) if random.choice([True, False]))
    progress = (completed_steps / len(steps)) * 100

    print(f"\n📊 Gesamtfortschritt: {completed_steps}/{len(steps)} ({progress:.1f}%)")


# Validation Rules Management
@cli.group()
def rules():
    """⚙️ Validierungsregeln-Management"""
    pass


@rules.command("show")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def show_rules(config):
    """Zeigt aktuelle Validierungsregeln an."""
    governance = DataGovernanceEngine(config)
    rules_dict = governance.config.get("validation_rules", {})

    print("⚙️ Aktuelle Validierungsregeln:")
    print("=" * 50)

    for rule, value in rules_dict.items():
        print(f"   {rule}: {value}")


@rules.command("update")
@click.argument("rule_name")
@click.argument("value")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def update_rule(rule_name, value, config):
    """Aktualisiert eine Validierungsregel."""
    governance = DataGovernanceEngine(config)

    # Value-Typ erkennen und konvertieren
    if value.lower() in ["true", "false"]:
        value = value.lower() == "true"
    elif value.replace(".", "").isdigit():
        value = float(value) if "." in value else int(value)

    governance.update_validation_rules({rule_name: value})

    print(f"✅ Regel '{rule_name}' auf '{value}' gesetzt")

    # Optional: In Konfigurationsdatei speichern
    if click.confirm("💾 In Konfigurationsdatei speichern?"):
        save_to_config_file(governance, config or "governance_config.yaml")


# System-Management
@cli.group()
def system():
    """🔧 System-Management"""
    pass


@system.command("status")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def system_status(config):
    """Zeigt Systemstatus der Data Governance Engine."""
    governance = DataGovernanceEngine(config)

    print("🔧 Data Governance System Status")
    print("=" * 50)

    templates = governance.get_templates()
    workflows = governance.get_workflows()
    rules = governance.config.get("validation_rules", {})

    print(f"📋 Templates: {len(templates)}")
    print(f"🔄 Workflows: {len(workflows)}")
    print(f"⚙️ Validierungsregeln: {len(rules)}")

    config_file = config or "governance_config.yaml"
    config_exists = os.path.exists(config_file)
    print(f"📁 Konfigurationsdatei: {'✅ Vorhanden' if config_exists else '❌ Nicht gefunden'}")

    if config_exists:
        config_size = os.path.getsize(config_file)
        config_modified = datetime.fromtimestamp(os.path.getmtime(config_file))
        print(f"   📏 Größe: {config_size} bytes")
        print(f"   🕒 Letzte Änderung: {config_modified.strftime('%Y-%m-%d %H:%M:%S')}")


@system.command("export-config")
@click.option("--output", "-o", help="Output-Datei", default="exported_governance_config.yaml")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def export_config(output, config):
    """Exportiert aktuelle Konfiguration."""
    governance = DataGovernanceEngine(config)

    with open(output, "w", encoding="utf-8") as f:
        yaml.safe_dump(governance.config, f, default_flow_style=False, allow_unicode=True)

    print(f"✅ Konfiguration exportiert nach: {output}")


@system.command("validate-config")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def validate_config(config):
    """Validiert Konfigurationsdatei."""
    config_file = config or "governance_config.yaml"

    try:
        governance = DataGovernanceEngine(config_file)
        print(f"✅ Konfigurationsdatei '{config_file}' ist gültig")

        # Zusätzliche Validierungen
        templates = governance.get_templates()
        workflows = governance.get_workflows()

        print(f"📋 {len(templates)} Templates geladen")
        print(f"🔄 {len(workflows)} Workflows geladen")

    except Exception as e:
        print(f"❌ Fehler in Konfigurationsdatei '{config_file}': {e}")


# Test & Diagnostik
@cli.group()
def test():
    """🧪 Test & Diagnostik"""
    pass


@test.command("note")
@click.argument("name")
@click.argument("content")
@click.option("--description", default="Test-Note")
@click.option("--type", "note_type", help="Note-Typ")
@click.option("--template", help="Template für Validierung")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def test_note(name, content, description, note_type, template, config):
    """Testet Note-Validierung ohne Speichern."""
    governance = DataGovernanceEngine(config)

    result = governance.validate_note_creation(
        name=name,
        content=content,
        description=description,
        note_type=note_type or "",
        template=template,
    )

    print_validation_result(result, name)


@test.command("performance")
@click.option("--iterations", type=int, default=100, help="Anzahl Test-Iterationen")
@click.option("--config", help="Pfad zur Konfigurationsdatei")
def test_performance(iterations, config):
    """Testet Performance der Validierung."""
    import time

    governance = DataGovernanceEngine(config)

    test_content = "Python ist eine Programmiersprache. Sie wurde von Guido van Rossum entwickelt und ist sehr beliebt für Web-Entwicklung, Data Science und Automation."

    print(f"🧪 Performance-Test mit {iterations} Iterationen...")

    start_time = time.time()

    for i in range(iterations):
        governance.validate_note_creation(
            name=f"Test Note {i}",
            content=test_content,
            description="Performance-Test",
            note_type="test",
        )

    end_time = time.time()
    duration = end_time - start_time
    avg_time = (duration / iterations) * 1000  # in ms

    print(f"✅ Performance-Test abgeschlossen:")
    print(f"   ⏱️ Gesamtdauer: {duration:.2f} Sekunden")
    print(f"   📊 Durchschnittliche Zeit pro Validierung: {avg_time:.2f} ms")
    print(f"   🚀 Validierungen pro Sekunde: {iterations/duration:.1f}")


# Helper Functions
def save_to_config_file(governance, config_file):
    """Speichert aktuelle Konfiguration in Datei."""
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(governance.config, f, default_flow_style=False, allow_unicode=True)
        print(f"💾 Konfiguration gespeichert in: {config_file}")
    except Exception as e:
        print(f"❌ Fehler beim Speichern: {e}")


if __name__ == "__main__":
    cli()
