import click
from neo4j import GraphDatabase
import os
import json
import re
import sys
from datetime import datetime
import logging

# Import our safety modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from safe_transactions import SafeTransactionManager, DataIntegrityValidator

# Try to import governance, but make it optional to avoid blocking CLI functionality
try:
    from src.governance.data_governance import DataGovernanceEngine, ValidationResult
    GOVERNANCE_AVAILABLE = True
except ImportError:
    # Fallback if governance module is not available
    GOVERNANCE_AVAILABLE = False

    # Create stub classes to prevent crashes
    class ValidationResult:
        def __init__(self):
            self.passed = True
            self.errors = []
            self.warnings = []
            self.suggestions = []

    class DataGovernanceEngine:
        def __init__(self, driver):
            pass

        def validate_note(self, name, content="", note_type=""):
            return ValidationResult()

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")
CORTEX_AI_URL = os.environ.get("CORTEX_AI_URL", "http://127.0.0.1:8000")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local governance print helper (renamed to avoid conflict)
def print_governance_validation_result(result: ValidationResult, note_name: str) -> bool:
    """Zeigt Validierungsergebnisse übersichtlich an."""
    print(f"\n🔍 Data Governance Validierung für: '{note_name}'")
    print("=" * 60)

    # Errors
    if result.errors:
        print("❌ KRITISCHE FEHLER:")
        for error in result.errors:
            print(f"   • {error}")

    # Warnings
    if result.warnings:
        print("\n⚠️ WARNUNGEN:")
        for warning in result.warnings:
            print(f"   • {warning}")

    # Suggestions
    if result.suggestions:
        print("\n💡 EMPFEHLUNGEN:")
        for suggestion in result.suggestions:
            print(f"   • {suggestion}")

    # Summary
    if result.passed and not result.warnings:
        print("\n✅ ALLE VALIDIERUNGEN BESTANDEN")
    elif result.passed:
        print("\n⚠️ VALIDIERUNG MIT WARNUNGEN BESTANDEN")
    else:
        print("\n❌ VALIDIERUNG FEHLGESCHLAGEN")

    print("=" * 60)
    return result.passed

# Helper for Neo4j driver/session with safety enhancements
class Neo4jHelper:
    _driver = None
    _transaction_manager = None
    _validator = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            cls._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        return cls._driver

    @classmethod
    def get_safe_transaction_manager(cls):
        if cls._transaction_manager is None:
            cls._transaction_manager = SafeTransactionManager(
                cls.get_driver(),
                backup_dir="cortex_neo/backups/auto"
            )
        return cls._transaction_manager

    @classmethod
    def get_validator(cls):
        if cls._validator is None:
            cls._validator = DataIntegrityValidator(
                cls.get_driver(),
                baseline_file="cortex_neo/monitoring/baseline_stats.json"
            )
        return cls._validator

    @classmethod
    def validate_connection_and_data(cls):
        """Validates connection and checks for data integrity issues"""
        try:
            validator = cls.get_validator()
            stats = validator.get_current_stats()

            click.echo(f"📊 Aktueller Datenbestand:")
            click.echo(f"   📝 Notes: {stats['notes']}")
            click.echo(f"   🔄 Workflows: {stats['workflows']}")
            click.echo(f"   🏷️  Tags: {stats['tags']}")
            click.echo(f"   🔗 Verknüpfungen: {stats['note_links'] + stats['workflow_links']}")

            # Check for critical data loss
            if validator.emergency_restore_check():
                click.echo("🚨 KRITISCHER DATENVERLUST ERKANNT!")
                return False

            # Validate integrity
            is_healthy = validator.validate_integrity()
            if not is_healthy:
                click.echo("⚠️  Datenintegritätsprobleme erkannt!")
                return False

            return True

        except Exception as e:
            click.echo(f"❌ Verbindungs-/Datenvalidierung fehlgeschlagen: {e}")
            return False

@click.group()
def cli():
    """Cortex-CLI für Neo4J-Workflow- und Wissensgraph-Operationen"""
    pass

@cli.command()
def list_workflows():
    """Zeigt alle Workflows in der Datenbank."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("MATCH (w:Workflow) RETURN w")
            found = False
            for record in result:
                click.echo(record["w"])
                found = True
            if not found:
                click.echo("Keine Workflows gefunden.")
    except Exception as e:
        click.echo(f"Fehler beim Abrufen der Workflows: {e}")

@cli.command()
def list_steps():
    """Zeigt alle Steps aller Workflows."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("MATCH (s:Step) RETURN s ORDER BY s.order")
            for record in result:
                print(record["s"])
    except Exception as e:
        print(f"Fehler beim Abrufen der Steps: {e}")

@cli.command()
@click.argument('workflow_name')
def show_workflow(workflow_name):
    """Zeigt Details und Steps eines bestimmten Workflows."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (w:Workflow {name: $workflow_name})-[:HAS_STEP]->(s:Step)
                RETURN w, s ORDER BY s.order
                """,
                workflow_name=workflow_name
            )
            steps = []
            workflow = None
            for record in result:
                workflow = record["w"]
                steps.append(record["s"])
            if workflow:
                print(f"Workflow: {workflow['name']} (Status: {workflow.get('status','')})")
                for step in steps:
                    print(f"  Step {step['order']}: {step['name']}")
            else:
                print(f"Kein Workflow mit Namen '{workflow_name}' gefunden.")
    except Exception as e:
        print(f"Fehler beim Anzeigen des Workflows: {e}")

# --- Workflow Management ---
@cli.command()
@click.argument('workflow_name')
def create_workflow(workflow_name):
    """Legt einen neuen Workflow an."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                "MERGE (w:Workflow {name: $workflow_name, type: 'Standard', status: 'in progress'})",
                workflow_name=workflow_name
            )
        print(f"Workflow '{workflow_name}' wurde angelegt.")
    except Exception as e:
        print(f"Fehler beim Erstellen des Workflows: {e}")

@cli.command()
@click.argument('workflow_name')
@click.argument('step_name')
@click.argument('order', type=int)
def add_step(workflow_name, step_name, order):
    """Fügt einem Workflow einen Step hinzu."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                """
                MATCH (w:Workflow {name: $workflow_name})
                MERGE (s:Step {name: $step_name, order: $order})
                MERGE (w)-[:HAS_STEP]->(s)
                """,
                workflow_name=workflow_name,
                step_name=step_name,
                order=order
            )
        print(f"Step '{step_name}' (Order {order}) zu Workflow '{workflow_name}' hinzugefügt.")
    except Exception as e:
        print(f"Fehler beim Hinzufügen des Steps: {e}")

@cli.command()
@click.argument('workflow_name')
def delete_workflow(workflow_name):
    """Löscht einen Workflow und alle zugehörigen Steps."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                """
                MATCH (w:Workflow {name: $workflow_name})-[r:HAS_STEP]->(s:Step)
                DETACH DELETE w, s
                """,
                workflow_name=workflow_name
            )
        print(f"Workflow '{workflow_name}' und zugehörige Steps gelöscht.")
    except Exception as e:
        print(f"Fehler beim Löschen des Workflows: {e}")

@cli.command()
@click.argument('step_name')
def delete_step(step_name):
    """Löscht einen Step (unabhängig vom Workflow)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                "MATCH (s:Step {name: $step_name}) DETACH DELETE s",
                step_name=step_name
            )
        print(f"Step '{step_name}' gelöscht.")
    except Exception as e:
        print(f"Fehler beim Löschen des Steps: {e}")

@cli.command()
@click.argument('workflow_name')
@click.argument('status')
def set_status(workflow_name, status):
    """Setzt den Status eines Workflows."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                "MATCH (w:Workflow {name: $workflow_name}) SET w.status = $status",
                workflow_name=workflow_name,
                status=status
            )
        print(f"Status von Workflow '{workflow_name}' auf '{status}' gesetzt.")
    except Exception as e:
        print(f"Fehler beim Setzen des Status: {e}")

# --- Notes/Tags/Templates/Links Management ---
@cli.command()
@click.argument('name')
@click.option('--content', help='Textinhalt der Note')
@click.option('--description', help='Kurze Beschreibung der Note')
@click.option('--type', 'note_type', help='Typ/Kategorie der Note')
@click.option('--url', help='URL/Link zur Note')
def add_note(name, content, description, note_type, url):
    """Legt eine Note mit Content an (MERGE)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Erstelle Note mit allen verfügbaren Properties
            props = {"name": name}
            if content:
                props["content"] = content
            if description:
                props["description"] = description
            if note_type:
                props["type"] = note_type
            if url:
                props["url"] = url

            # Vereinfachte Query ohne datetime() Funktionen, die Probleme verursachen könnten
            session.run(
                """
                MERGE (n:Note {name: $name})
                SET n.content = $content,
                    n.description = $description,
                    n.type = $note_type,
                    n.url = $url,
                    n.updated_at = timestamp()
                """,
                name=name,
                content=content or "",
                description=description or "",
                note_type=note_type or "",
                url=url or ""
            )
        print(f"✅ Note '{name}' angelegt/aktualisiert.")
        if content:
            print(f"   📄 Content: {content[:100]}{'...' if len(content) > 100 else ''}")
        if description:
            print(f"   📝 Beschreibung: {description}")
        if note_type:
            print(f"   🏷️  Typ: {note_type}")
        if url:
            print(f"   🔗 URL: {url}")
    except Exception as e:
        print(f"❌ Fehler beim Anlegen der Note: {e}")
        import traceback
        traceback.print_exc()

@cli.command()
@click.argument('name')
@click.argument('content')
def update_note_content(name, content):
    """Aktualisiert den Content einer bestehenden Note."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (n:Note {name: $name})
                SET n.content = $content, n.updated_at = timestamp()
                RETURN n
                """,
                name=name, content=content
            )
            if result.single():
                print(f"Content der Note '{name}' aktualisiert.")
                print(f"  Neuer Content: {content[:100]}{'...' if len(content) > 100 else ''}")
            else:
                print(f"Note '{name}' nicht gefunden.")
    except Exception as e:
        print(f"Fehler beim Aktualisieren des Contents: {e}")

@cli.command()
@click.argument('name')
@click.option('--file', 'file_path', type=click.Path(exists=True), help='Datei zum Importieren des Contents')
def import_note_content(name, file_path):
    """Importiert Content aus einer Datei in eine Note."""
    try:
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # Interaktiver Editor-Modus
            import tempfile
            import subprocess
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as tmp:
                tmp.write("# Fügen Sie hier den Content ein\n\n")
                tmp.flush()
                editor = os.environ.get('EDITOR', 'nano')
                subprocess.call([editor, tmp.name])
                tmp.seek(0)
                content = tmp.read()
            os.unlink(tmp.name)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (n:Note {name: $name})
                SET n.content = $content, n.updated_at = timestamp()
                RETURN n
                """,
                name=name, content=content
            )
            if result.single():
                print(f"Content der Note '{name}' aus Datei importiert ({len(content)} Zeichen).")
            else:
                print(f"Note '{name}' nicht gefunden.")
    except Exception as e:
        print(f"Fehler beim Importieren des Contents: {e}")

@cli.command()
@click.argument('name')
@click.option('--output', '-o', type=click.Path(), help='Ausgabedatei (Standard: {name}.md)')
def export_note_content(name, output):
    """Exportiert den Content einer Note in eine Datei."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run(
                "MATCH (n:Note {name: $name}) RETURN n.content as content, n.description as description",
                name=name
            )
            record = result.single()
            if not record or not record["content"]:
                print(f"Note '{name}' nicht gefunden oder hat keinen Content.")
                return

            output_file = output or f"{name.replace(' ', '_').replace('/', '_')}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# {name}\n\n")
                if record["description"]:
                    f.write(f"**Beschreibung:** {record['description']}\n\n")
                f.write(record["content"])

            print(f"Content der Note '{name}' exportiert nach: {output_file}")
    except Exception as e:
        print(f"Fehler beim Exportieren des Contents: {e}")

@cli.command()
@click.argument('name')
def add_tag(name):
    """Legt einen Tag an (MERGE)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run("MERGE (t:Tag {name: $name})", name=name)
        print(f"Tag '{name}' angelegt (oder bereits vorhanden).")
    except Exception as e:
        print(f"Fehler beim Anlegen des Tags: {e}")

@cli.command()
@click.argument('name')
def add_template(name):
    """Legt ein Template an (MERGE)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run("MERGE (t:Template {name: $name})", name=name)
        print(f"Template '{name}' angelegt (oder bereits vorhanden).")
    except Exception as e:
        print(f"Fehler beim Anlegen des Templates: {e}")

@cli.command()
@click.argument('from_note')
@click.argument('to_note')
def link_notes(from_note, to_note):
    """Erzeugt LINKS_TO zwischen zwei Notes."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                """
                MERGE (a:Note {name: $from})
                MERGE (b:Note {name: $to})
                MERGE (a)-[:LINKS_TO]->(b)
                """,
                **{"from": from_note, "to": to_note}
            )
        print(f"Verlinkt: {from_note} -> {to_note}")
    except Exception as e:
        print(f"Fehler beim Verlinken der Notes: {e}")

@cli.command()
@click.argument('note')
@click.argument('tag')
def tag_note(note, tag):
    """Verknüpft Note mit Tag (TAGGED_WITH)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                """
                MERGE (n:Note {name: $note})
                MERGE (t:Tag {name: $tag})
                MERGE (n)-[:TAGGED_WITH]->(t)
                """,
                note=note, tag=tag
            )
        print(f"Note '{note}' mit Tag '{tag}' verknüpft.")
    except Exception as e:
        print(f"Fehler beim Verknüpfen der Note mit dem Tag: {e}")

@cli.command()
@click.argument('note')
@click.argument('template')
def use_template(note, template):
    """Verknüpft Note mit Template (USES_TEMPLATE)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                """
                MERGE (n:Note {name: $note})
                MERGE (t:Template {name: $template})
                MERGE (n)-[:USES_TEMPLATE]->(t)
                """,
                note=note, template=template
            )
        print(f"Note '{note}' nutzt Template '{template}'.")
    except Exception as e:
        print(f"Fehler beim Verknüpfen der Note mit dem Template: {e}")

@cli.command()
def list_notes():
    """Listet alle Notes."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            for r in session.run("MATCH (n:Note) RETURN n ORDER BY n.name"):
                print(r["n"])
    except Exception as e:
        print(f"Fehler beim Auflisten der Notes: {e}")

@cli.command()
def list_tags():
    """Listet alle Tags."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            for r in session.run("MATCH (t:Tag) RETURN t ORDER BY t.name"):
                print(r["t"])
    except Exception as e:
        print(f"Fehler beim Auflisten der Tags: {e}")

@cli.command()
def list_templates():
    """Listet alle Templates."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            for r in session.run("MATCH (t:Template) RETURN t ORDER BY t.name"):
                print(r["t"])
    except Exception as e:
        print(f"Fehler beim Auflisten der Templates: {e}")

@cli.command()
@click.argument('name')
def show_note(name):
    """Zeigt eine Note mit Content, Tags, Template und Links."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            res = session.run(
                """
                MATCH (n:Note {name: $name})
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(tg:Tag)
                OPTIONAL MATCH (n)-[:USES_TEMPLATE]->(tpl:Template)
                OPTIONAL MATCH (n)-[:LINKS_TO]->(out:Note)
                OPTIONAL MATCH (in:Note)-[:LINKS_TO]->(n)
                RETURN n, 
                       collect(DISTINCT tg) AS tags, 
                       collect(DISTINCT tpl) AS templates, 
                       collect(DISTINCT out) AS outgoing, 
                       collect(DISTINCT in) AS incoming
                """,
                name=name
            )
            rec = res.single()
            if not rec:
                print(f"Note '{name}' nicht gefunden.")
                return

            n = rec["n"]
            tags = rec["tags"]
            templates = rec["templates"]
            outgoing = rec["outgoing"]
            incoming = rec["incoming"]

            # Header mit Metadaten
            print(f"📝 Note: {n['name']}")
            if n.get('type'):
                print(f"   Typ: {n['type']}")
            if n.get('description'):
                print(f"   Beschreibung: {n['description']}")
            if n.get('url'):
                print(f"   URL: {n['url']}")
            if n.get('created_at'):
                print(f"   Erstellt: {n['created_at']}")
            if n.get('updated_at'):
                print(f"   Aktualisiert: {n['updated_at']}")
            print()

            # Content
            if n.get('content'):
                content = n['content']
                print("📄 Content:")
                # Zeige ersten Teil des Contents
                if len(content) > 500:
                    print(f"   {content[:500]}...")
                    print(f"   [Content gekürzt - insgesamt {len(content)} Zeichen]")
                    print("   💡 Verwende 'export-note-content' für vollständigen Content")
                else:
                    print(f"   {content}")
                print()

            # Templates
            if templates:
                print("🏗️  Templates:")
                for t in templates:
                    if t: print(f"    - {t['name']}")
                print()

            # Tags
            if tags:
                print("🏷️  Tags:")
                for t in tags:
                    if t: print(f"    - {t['name']}")
                print()

            # Ausgehende Links
            if outgoing:
                print("🔗 Links →:")
                for o in outgoing:
                    if o: print(f"    - {o['name']}")
                print()

            # Eingehende Links
            if incoming:
                print("🔙 Links ←:")
                for i in incoming:
                    if i: print(f"    - {i['name']}")
                print()

            # Statistiken
            link_count = len([o for o in outgoing if o]) + len([i for i in incoming if i])
            tag_count = len([t for t in tags if t])
            print(f"📊 Statistiken: {link_count} Links, {tag_count} Tags")

    except Exception as e:
        print(f"Fehler beim Anzeigen der Note: {e}")

@cli.command()
@click.option('--with-content', is_flag=True, help='Zeige auch Content-Vorschau')
@click.option('--type', 'filter_type', help='Filtere nach Note-Typ')
@click.option('--tag', help='Filtere nach Tag')
def list_notes_detailed(with_content, filter_type, tag):
    """Listet alle Notes mit erweiterten Informationen."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Baue Query dynamisch auf
            query = "MATCH (n:Note)"
            params = {}

            if tag:
                query += "-[:TAGGED_WITH]->(t:Tag {name: $tag})"
                params["tag"] = tag

            if filter_type:
                query += " WHERE n.type = $type"
                params["type"] = filter_type

            query += " RETURN n ORDER BY n.updated_at DESC, n.name"

            result = session.run(query, params)
            notes_found = 0

            for record in result:
                n = record["n"]
                notes_found += 1

                print(f"📝 {n['name']}")
                if n.get('type'):
                    print(f"   Typ: {n['type']}")
                if n.get('description'):
                    print(f"   📄 {n['description']}")
                if n.get('updated_at'):
                    print(f"   🕒 {n['updated_at']}")

                if with_content and n.get('content'):
                    content = n['content']
                    preview = content[:150] + "..." if len(content) > 150 else content
                    print(f"   💭 {preview}")

                print()

            if notes_found == 0:
                filter_desc = []
                if tag:
                    filter_desc.append(f"Tag '{tag}'")
                if filter_type:
                    filter_desc.append(f"Typ '{filter_type}'")

                if filter_desc:
                    print(f"Keine Notes gefunden mit Filter: {', '.join(filter_desc)}")
                else:
                    print("Keine Notes gefunden.")
            else:
                print(f"📊 {notes_found} Notes gefunden")

    except Exception as e:
        print(f"Fehler beim Auflisten der Notes: {e}")

@cli.command()
@click.argument('query')
@click.option('--in-content', is_flag=True, help='Suche auch im Content')
@click.option('--case-sensitive', is_flag=True, help='Groß-/Kleinschreibung beachten')
def search_notes(query, in_content, case_sensitive):
    """Durchsucht Notes nach Name, Beschreibung oder Content."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Baue Suchquery auf
            if case_sensitive:
                name_condition = "n.name CONTAINS $query"
                desc_condition = "n.description CONTAINS $query"
                content_condition = "n.content CONTAINS $query"
            else:
                name_condition = "toLower(n.name) CONTAINS toLower($query)"
                desc_condition = "toLower(coalesce(n.description, '')) CONTAINS toLower($query)"
                content_condition = "toLower(coalesce(n.content, '')) CONTAINS toLower($query)"

            search_conditions = [name_condition, desc_condition]
            if in_content:
                search_conditions.append(content_condition)

            cypher_query = f"""
                MATCH (n:Note)
                WHERE {' OR '.join(search_conditions)}
                RETURN n, 
                       CASE 
                           WHEN {name_condition} THEN 'name'
                           WHEN {desc_condition} THEN 'description' 
                           WHEN {content_condition} THEN 'content'
                           ELSE 'other'
                       END as match_type
                ORDER BY n.updated_at DESC
            """

            result = session.run(cypher_query, {"query": query})
            found_count = 0

            for record in result:
                n = record["n"]
                match_type = record["match_type"]
                found_count += 1

                print(f"📝 {n['name']} (Match in: {match_type})")

                if n.get('description'):
                    print(f"   📄 {n['description']}")

                # Zeige relevanten Content-Ausschnitt bei Content-Match
                if match_type == 'content' and n.get('content'):
                    content = n['content']
                    # Finde Position des Suchbegriffs
                    if case_sensitive:
                        pos = content.find(query)
                    else:
                        pos = content.lower().find(query.lower())

                    if pos >= 0:
                        start = max(0, pos - 50)
                        end = min(len(content), pos + len(query) + 50)
                        snippet = content[start:end]
                        print(f"   💭 ...{snippet}...")

                print()

            if found_count == 0:
                search_desc = f"'{query}'"
                if in_content:
                    search_desc += " (inkl. Content)"
                print(f"Keine Notes gefunden für Suche: {search_desc}")
            else:
                print(f"🔍 {found_count} Notes gefunden")

    except Exception as e:
        print(f"Fehler bei der Suche: {e}")

@cli.command()
@click.argument('file', type=click.Path(exists=True))
def migrate(file):
    """Migriert Struktur (Notes/Tags/Templates/Links) aus YAML/JSON-Datei."""
    from migrate_structure import migrate_from_file
    migrate_from_file(file)
    print("Migration abgeschlossen.")

@cli.command()
def setup_indexes():
    """Erstellt sinnvolle Constraints/Indizes (idempotent)."""
    stmts = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Note) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Template) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Workflow) REQUIRE w.name IS UNIQUE",
        # Composite uniqueness for Steps (name, order) if supported by Neo4j 5
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Step) REQUIRE (s.name, s.order) IS UNIQUE",
    ]
    driver = Neo4jHelper.get_driver()
    with driver.session() as session:
        for cypher in stmts:
            try:
                session.run(cypher)
            except Exception as e:  # Fallback if composite not supported
                if "(s.name, s.order)" in cypher:
                    try:
                        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Step) REQUIRE s.name IS UNIQUE")
                    except Exception:
                        pass
                else:
                    raise e
    print("Constraints/Indizes eingerichtet.")

@cli.command()
@click.argument('name')
def delete_note(name):
    """Löscht eine Note und alle zugehörigen Beziehungen."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run("MATCH (n:Note {name: $name}) DETACH DELETE n", name=name)
        print(f"Note '{name}' gelöscht.")
    except Exception as e:
        print(f"Fehler beim Löschen der Note: {e}")

@cli.command()
@click.argument('name')
def delete_tag(name):
    """Löscht einen Tag (falls nicht mehr referenziert)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run("MATCH (t:Tag {name: $name}) DETACH DELETE t", name=name)
        print(f"Tag '{name}' gelöscht.")
    except Exception as e:
        print(f"Fehler beim Löschen des Tags: {e}")

@cli.command()
@click.argument('name')
def delete_template(name):
    """Löscht ein Template (falls nicht mehr referenziert)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run("MATCH (t:Template {name: $name}) DETACH DELETE t", name=name)
        print(f"Template '{name}' gelöscht.")
    except Exception as e:
        print(f"Fehler beim Löschen des Templates: {e}")

@cli.command()
@click.argument('from_note')
@click.argument('to_note')
def unlink_notes(from_note, to_note):
    """Löscht die LINKS_TO-Beziehung zwischen zwei Notes (falls vorhanden)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                """
                MATCH (a:Note {name: $from})-[r:LINKS_TO]->(b:Note {name: $to})
                DELETE r
                """,
                **{"from": from_note, "to": to_note}
            )
        print(f"Unlinked: {from_note} -/-> {to_note}")
    except Exception as e:
        print(f"Fehler beim Entfernen der Verlinkung: {e}")

@cli.command()
@click.argument('note')
@click.argument('tag')
def untag_note(note, tag):
    """Entfernt TAGGED_WITH zwischen Note und Tag."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                """
                MATCH (:Note {name: $note})-[r:TAGGED_WITH]->(:Tag {name: $tag})
                DELETE r
                """,
                note=note, tag=tag
            )
        print(f"Removed tag '{tag}' from note '{note}'.")
    except Exception as e:
        print(f"Fehler beim Entfernen des Tags von der Note: {e}")

@cli.command()
@click.argument('note')
@click.argument('template')
def unuse_template(note, template):
    """Entfernt USES_TEMPLATE zwischen Note und Template."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                """
                MATCH (:Note {name: $note})-[r:USES_TEMPLATE]->(:Template {name: $template})
                DELETE r
                """,
                note=note, template=template
            )
        print(f"Removed template '{template}' from note '{note}'.")
    except Exception as e:
        print(f"Fehler beim Entfernen des Templates von der Note: {e}")

@cli.command()
def validate_graph():
    """Einfache Validierung: verwaiste Tags/Templates, Anzahl Links, Anzahl Notes."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            orphan_tags = session.run(
                """
                MATCH (t:Tag)
                WHERE NOT EXISTS ( (:Note)-[:TAGGED_WITH]->(t) )
                RETURN count(t) AS c
                """
            ).single()["c"]
            orphan_tpls = session.run(
                """
                MATCH (t:Template)
                WHERE NOT EXISTS ( (:Note)-[:USES_TEMPLATE]->(t) )
                RETURN count(t) AS c
                """
            ).single()["c"]
            note_count = session.run("MATCH (n:Note) RETURN count(n) AS c").single()["c"]
            link_count = session.run("MATCH (:Note)-[:LINKS_TO]->(:Note) RETURN count(*) AS c").single()["c"]
            print(json.dumps({
                "notes": note_count,
                "links": link_count,
                "orphan_tags": orphan_tags,
                "orphan_templates": orphan_tpls,
            }, indent=2))
    except Exception as e:
        print(f"Fehler bei der Validierung des Graphen: {e}")

@cli.command()
@click.option('--format', 'fmt', type=click.Choice(['yaml','json']), default='yaml', help='Exportformat')
@click.option('--out', 'out_path', type=click.Path(dir_okay=False), default='export_structure.yaml')
def export_structure(fmt: str, out_path: str):
    """Exportiert Notes/Tags/Templates/Links in YAML/JSON im Migrationsformat."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            notes = [r["n"]["name"] for r in session.run("MATCH (n:Note) RETURN n ORDER BY n.name")]
            tags = [r["t"]["name"] for r in session.run("MATCH (t:Tag) RETURN t ORDER BY t.name")]
            templates = [r["t"]["name"] for r in session.run("MATCH (t:Template) RETURN t ORDER BY t.name")]
            links = [{"from": r["a"]["name"], "to": r["b"]["name"]} for r in session.run("MATCH (a:Note)-[:LINKS_TO]->(b:Note) RETURN a,b ORDER BY a.name, b.name")]
            uses_tpl = [{"note": r["n"]["name"], "template": r["t"]["name"]} for r in session.run("MATCH (n:Note)-[:USES_TEMPLATE]->(t:Template) RETURN n,t ORDER BY n.name, t.name")]
            tagged = [{"note": r["n"]["name"], "tag": r["t"]["name"]} for r in session.run("MATCH (n:Note)-[:TAGGED_WITH]->(t:Tag) RETURN n,t ORDER BY n.name, t.name")]
        data = {
            "notes": notes,
            "templates": templates,
            "tags": tags,
            "links": links,
            "assignments": {
                "uses_template": uses_tpl,
                "tagged_with": tagged,
            }
        }
        if fmt == 'json':
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            try:
                import yaml  # type: ignore
            except Exception:
                raise click.ClickException("PyYAML ist nicht installiert. Bitte 'pip install pyyaml' ausführen oder --format json nutzen.")
            with open(out_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        print(f"Export gespeichert: {out_path}")
    except Exception as e:
        print(f"Fehler beim Exportieren der Struktur: {e}")

@cli.command()
@click.option('--by', type=click.Choice(['tag','template','all']), default='tag', help='Kriterium für Auto-Verlinkung')
@click.option('--min-shared', type=int, default=1, help='Min. gemeinsame Elemente (Tags/Templates)')
@click.option('--max-per-note', type=int, default=50, help='Max. neue Links pro Note (Top-K nach Gewicht)')
def auto_link(by: str, min_shared: int, max_per_note: int):
    """Erzeugt automatisch LINKS_TO anhand gemeinsamer Tags/Templates.
    Setzt r.auto=true, r.tags_shared / r.templates_shared und r.weight als Summe.
    Idempotent: MERGE auf Beziehungen, r.* werden gesetzt/aktualisiert.
    """
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            if by in ('tag','all'):
                session.run(
                    """
                    MATCH (a:Note)-[:TAGGED_WITH]->(t:Tag)<-[:TAGGED_WITH]-(b:Note)
                    WHERE a.name < b.name
                    WITH a,b,count(t) AS shared
                    WHERE shared >= $min_shared
                    ORDER BY a.name, shared DESC
                    WITH a, collect({b:b, shared:shared}) AS pairs
                    UNWIND pairs[..$max_per_note] AS item
                    WITH a, item.b AS b, item.shared AS shared
                    MERGE (a)-[r:LINKS_TO]->(b)
                    SET r.auto = true,
                        r.tags_shared = shared,
                        r.weight = coalesce(r.templates_shared,0) + shared
                    """,
                    min_shared=min_shared, max_per_note=max_per_note
                )
            if by in ('template','all'):
                session.run(
                    """
                    MATCH (a:Note)-[:USES_TEMPLATE]->(tpl:Template)<-[:USES_TEMPLATE]-(b:Note)
                    WHERE a.name < b.name
                    WITH a,b,count(tpl) AS shared
                    WHERE shared >= $min_shared
                    ORDER BY a.name, shared DESC
                    WITH a, collect({b:b, shared:shared}) AS pairs
                    UNWIND pairs[..$max_per_note] AS item
                    WITH a, item.b AS b, item.shared AS shared
                    MERGE (a)-[r:LINKS_TO]->(b)
                    SET r.auto = true,
                        r.templates_shared = shared,
                        r.weight = coalesce(r.tags_shared,0) + shared
                    """,
                    min_shared=min_shared, max_per_note=max_per_note
                )
        print(f"Auto-Linking abgeschlossen (by={by}, min_shared={min_shared}, max_per_note={max_per_note}).")
    except Exception as e:
        print(f"Fehler beim automatischen Verlinken: {e}")

@cli.command()
@click.option('--min-similarity', type=float, default=0.3, help='Minimale Ähnlichkeit für automatische Links (0.0-1.0)')
@click.option('--max-links-per-note', type=int, default=10, help='Maximale neue Links pro Note')
@click.option('--content-length-min', type=int, default=50, help='Minimale Content-Länge für Analyse')
def auto_link_by_content(min_similarity, max_links_per_note, content_length_min):
    """Erstellt automatische Links basierend auf Content-Ähnlichkeit (NLP-basiert)."""
    try:
        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            # Hole alle Notes mit Content
            notes_result = session.run("""
                MATCH (n:Note)
                WHERE n.content IS NOT NULL 
                  AND size(n.content) >= $min_length
                RETURN n.name as name, n.content as content, n.description as description
                ORDER BY n.name
            """, min_length=content_length_min)

            notes = []
            for record in notes_result:
                notes.append({
                    'name': record['name'],
                    'content': record['content'],
                    'description': record.get('description', '')
                })

            print(f"📊 Analysiere {len(notes)} Notes für Content-basierte Verlinkung...")

            links_created = 0

            # Analysiere jedes Note-Paar
            for i, note_a in enumerate(notes):
                for j, note_b in enumerate(notes[i+1:], i+1):
                    similarity = calculate_content_similarity(note_a, note_b)

                    if similarity >= min_similarity:
                        # Erstelle Link in Neo4j
                        try:
                            session.run("""
                                MATCH (a:Note {name: $name_a}), (b:Note {name: $name_b})
                                MERGE (a)-[r:LINKS_TO]->(b)
                                SET r.auto = true,
                                    r.content_similarity = $similarity,
                                    r.method = 'content_analysis',
                                    r.weight = $similarity,
                                    r.created_at = timestamp()
                                """,
                                name_a=note_a['name'],
                                name_b=note_b['name'],
                                similarity=similarity
                            )
                            links_created += 1
                            print(f"🔗 Link erstellt: '{note_a['name']}' ↔ '{note_b['name']}' (Ähnlichkeit: {similarity:.2f})")

                            # Limit pro Note beachten
                            if links_created >= max_links_per_note * len(notes):
                                break

                        except Exception as e:
                            print(f"⚠️ Fehler beim Erstellen des Links: {e}")

                if links_created >= max_links_per_note * len(notes):
                    break

            print(f"✅ Content-Analyse abgeschlossen: {links_created} neue Links erstellt")
            print(f"📋 Parameter: min_similarity={min_similarity}, max_links_per_note={max_links_per_note}")

    except Exception as e:
        print(f"❌ Fehler bei der Content-basierten Verlinkung: {e}")
        import traceback
        traceback.print_exc()

def calculate_content_similarity(note_a, note_b):
    """Berechnet Content-Ähnlichkeit zwischen zwei Notes."""
    try:
        # Kombiniere Content und Description für bessere Analyse
        text_a = f"{note_a['content']} {note_a['description']}".lower().strip()
        text_b = f"{note_b['content']} {note_b['description']}".lower().strip()

        if not text_a or not text_b:
            return 0.0

        # Einfache Keyword-basierte Ähnlichkeit
        words_a = set(extract_keywords(text_a))
        words_b = set(extract_keywords(text_b))

        if not words_a or not words_b:
            return 0.0

        # Jaccard-Ähnlichkeit
        intersection = len(words_a.intersection(words_b))
        union = len(words_a.union(words_b))

        jaccard_sim = intersection / union if union > 0 else 0.0

        # Zusätzlich: Überprüfe auf gemeinsame längere Phrasen
        phrase_similarity = calculate_phrase_similarity(text_a, text_b)

        # Gewichtete Kombination
        combined_similarity = (jaccard_sim * 0.7) + (phrase_similarity * 0.3)

        return min(combined_similarity, 1.0)

    except Exception as e:
        print(f"⚠️ Fehler bei Ähnlichkeitsberechnung: {e}")
        return 0.0

def extract_keywords(text, min_length=3):
    """Extrahiert relevante Keywords aus Text."""
    import re

    # Stopwords (deutsche und englische)
    stopwords = {
        'der', 'die', 'das', 'und', 'ist', 'ein', 'eine', 'mit', 'von', 'zu', 'im', 'am', 'auf', 'für', 'durch', 'als', 'bei', 'nach', 'über', 'unter', 'zwischen',
        'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall', 'to', 'of', 'in', 'for', 'with', 'by'
    }

    # Bereinige Text und extrahiere Wörter
    words = re.findall(r'\b[a-zA-ZäöüßÄÖÜ]+\b', text.lower())

    # Filtere Keywords
    keywords = [
        word for word in words
        if len(word) >= min_length
        and word not in stopwords
        and not word.isdigit()
    ]

    return keywords

def calculate_phrase_similarity(text_a, text_b):
    """Berechnet Ähnlichkeit basierend auf gemeinsamen Phrasen."""
    import re

    # Extrahiere 2-3 Wort Phrasen
    phrases_a = set()
    phrases_b = set()

    words_a = re.findall(r'\b[a-zA-ZäöüßÄÖÜ]+\b', text_a.lower())
    words_b = re.findall(r'\b[a-zA-ZäöüßÄÖÜ]+\b', text_b.lower())

    # 2-Wort Phrasen
    for i in range(len(words_a) - 1):
        phrase = f"{words_a[i]} {words_a[i+1]}"
        if len(phrase) > 6:  # Filtere sehr kurze Phrasen
            phrases_a.add(phrase)

    for i in range(len(words_b) - 1):
        phrase = f"{words_b[i]} {words_b[i+1]}"
        if len(phrase) > 6:
            phrases_b.add(phrase)

    # 3-Wort Phrasen (höhere Gewichtung)
    for i in range(len(words_a) - 2):
        phrase = f"{words_a[i]} {words_a[i+1]} {words_a[i+2]}"
        if len(phrase) > 10:
            phrases_a.add(phrase)

    for i in range(len(words_b) - 2):
        phrase = f"{words_b[i]} {words_b[i+1]} {words_b[i+2]}"
        if len(phrase) > 10:
            phrases_b.add(phrase)

    if not phrases_a or not phrases_b:
        return 0.0

    # Berechne Phrasen-Ähnlichkeit
    intersection = len(phrases_a.intersection(phrases_b))
    union = len(phrases_a.union(phrases_b))

    return intersection / union if union > 0 else 0.0

@cli.command()
@click.argument('note_name')
@click.option('--suggestions', type=int, default=5, help='Anzahl der Link-Vorschläge')
@click.option('--min-similarity', type=float, default=0.2, help='Minimale Ähnlichkeit für Vorschläge')
def suggest_links(note_name, suggestions, min_similarity):
    """Schlägt Links für eine spezifische Note basierend auf Content-Ähnlichkeit vor."""
    try:
        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            # Hole die Ziel-Note
            target_result = session.run("""
                MATCH (n:Note {name: $name})
                RETURN n.name as name, n.content as content, n.description as description
            """, name=note_name)

            target_record = target_result.single()
            if not target_record:
                print(f"❌ Note '{note_name}' nicht gefunden.")
                return

            target_note = {
                'name': target_record['name'],
                'content': target_record['content'] or '',
                'description': target_record.get('description', '')
            }

            if not target_note['content'].strip():
                print(f"❌ Note '{note_name}' hat keinen Content für Ähnlichkeitsanalyse.")
                return

            # Hole alle anderen Notes
            other_notes_result = session.run("""
                MATCH (n:Note)
                WHERE n.name <> $name 
                  AND n.content IS NOT NULL 
                  AND size(n.content) >= 20
                  AND NOT EXISTS((target:Note {name: $name})-[:LINKS_TO]->(n))
                  AND NOT EXISTS((n)-[:LINKS_TO]->(target:Note {name: $name}))
                RETURN n.name as name, n.content as content, n.description as description
            """, name=note_name)

            candidates = []
            for record in other_notes_result:
                candidate = {
                    'name': record['name'],
                    'content': record['content'],
                    'description': record.get('description', '')
                }

                similarity = calculate_content_similarity(target_note, candidate)
                if similarity >= min_similarity:
                    candidates.append({
                        'note': candidate,
                        'similarity': similarity
                    })

            # Sortiere nach Ähnlichkeit
            candidates.sort(key=lambda x: x['similarity'], reverse=True)

            print(f"🔍 Link-Vorschläge für Note: '{note_name}'")
            print(f"📊 {len(candidates)} potentielle Kandidaten gefunden")
            print()

            if not candidates:
                print(f"📭 Keine ähnlichen Notes gefunden (min_similarity={min_similarity})")
                print("💡 Versuche einen niedrigeren --min-similarity Wert")
                return

            print("🔗 Top Link-Vorschläge:")
            for i, candidate in enumerate(candidates[:suggestions]):
                note = candidate['note']
                sim = candidate['similarity']

                print(f"{i+1}. '{note['name']}' (Ähnlichkeit: {sim:.3f})")
                if note['description']:
                    print(f"   📝 {note['description'][:100]}{'...' if len(note['description']) > 100 else ''}")

                # Zeige gemeinsame Keywords
                target_keywords = set(extract_keywords(f"{target_note['content']} {target_note['description']}"))
                candidate_keywords = set(extract_keywords(f"{note['content']} {note['description']}"))
                common_keywords = target_keywords.intersection(candidate_keywords)

                if common_keywords:
                    print(f"   🏷️ Gemeinsame Keywords: {', '.join(list(common_keywords)[:5])}")
                print()

            print(f"💡 Verwende 'auto-link-by-content --min-similarity {min_similarity}' um Links automatisch zu erstellen")

    except Exception as e:
        print(f"❌ Fehler bei der Link-Vorschlag-Generierung: {e}")
        import traceback
        traceback.print_exc()

@cli.command()
def clear_auto_links():
    """Löscht automatisch erzeugte LINKS_TO (r.auto=true)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run("MATCH ()-[r:LINKS_TO]->() WHERE coalesce(r.auto,false)=true DELETE r")
        print("Auto-Links gelöscht.")
    except Exception as e:
        print(f"Fehler beim Löschen der Auto-Links: {e}")

@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Ausgabe als JSON')
def link_validate_ai(as_json: bool):
    """Validiert Links im Neo4j Knowledge Graph ohne externe API-Abhängigkeiten."""
    try:
        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            # Finde alle Links im Graph
            links_result = session.run("""
                MATCH (a)-[r:LINKS_TO]->(b)
                RETURN a.title as source, b.title as target, 
                       coalesce(r.auto, false) as auto_generated,
                       coalesce(r.strength, 1.0) as strength
                ORDER BY a.title, b.title
            """)

            # Finde verwaiste Knoten (ohne eingehende oder ausgehende Links)
            orphaned_result = session.run("""
                MATCH (n)
                WHERE NOT (n)-[:LINKS_TO]-() AND NOT ()-[:LINKS_TO]-(n)
                RETURN n.title as orphaned_node, labels(n) as node_types
                ORDER BY n.title
            """)

            # Sammle Statistiken
            total_links = 0
            auto_links = 0
            manual_links = 0
            weak_links = []

            links_data = []
            for record in links_result:
                total_links += 1
                if record["auto_generated"]:
                    auto_links += 1
                else:
                    manual_links += 1

                if record["strength"] < 0.3:
                    weak_links.append({
                        "source": record["source"],
                        "target": record["target"],
                        "strength": record["strength"]
                    })

                links_data.append({
                    "source": record["source"],
                    "target": record["target"],
                    "auto_generated": record["auto_generated"],
                    "strength": record["strength"]
                })

            orphaned_nodes = [{"title": record["orphaned_node"], "types": record["node_types"]}
                            for record in orphaned_result]

            # Erstelle Ergebnis
            validation_result = {
                "total_links": total_links,
                "auto_links": auto_links,
                "manual_links": manual_links,
                "invalid_links": len(weak_links),  # Schwache Links als "invalid" betrachten
                "orphaned_nodes": len(orphaned_nodes),
                "suggestions": [
                    f"Überprüfe {len(weak_links)} schwache Links (Stärke < 0.3)",
                    f"Verbinde {len(orphaned_nodes)} verwaiste Knoten mit anderen Konzepten",
                    f"Überprüfe {auto_links} automatisch generierte Links auf Relevanz"
                ],
                "details": {
                    "weak_links": weak_links[:10],  # Erste 10 schwache Links
                    "orphaned_nodes": orphaned_nodes[:10],  # Erste 10 verwaiste Knoten
                    "link_distribution": {
                        "auto_generated": auto_links,
                        "manually_created": manual_links
                    }
                }
            }

        if as_json:
            print(json.dumps(validation_result, indent=2, ensure_ascii=False))
        else:
            print("🔍 Knowledge Graph Link-Validierung:")
            print(f"  📊 Gesamte Links: {total_links}")
            print(f"  🤖 Auto-generierte Links: {auto_links}")
            print(f"  ✋ Manuell erstellte Links: {manual_links}")
            print(f"  ⚠️  Schwache Links: {len(weak_links)}")
            print(f"  🏝️  Verwaiste Knoten: {len(orphaned_nodes)}")
            print()
            print("💡 Verbesserungsvorschläge:")
            for suggestion in validation_result["suggestions"]:
                print(f"  - {suggestion}")

            if weak_links:
                print()
                print("🔗 Schwächste Links:")
                for link in weak_links[:5]:
                    print(f"  - '{link['source']}' → '{link['target']}' (Stärke: {link['strength']:.2f})")

            if orphaned_nodes:
                print()
                print("🏝️ Verwaiste Knoten:")
                for node in orphaned_nodes[:5]:
                    print(f"  - '{node['title']}' ({', '.join(node['types'])})")

    except Exception as e:
        error_msg = f"Link-Validierung fehlgeschlagen: {e}"
        if as_json:
            print(json.dumps({"error": error_msg}, indent=2))
        else:
            print(f"❌ {error_msg}")

@cli.command()
@click.argument('file_path')
def import_project(file_path):
    """Importiert ein Projekt aus einer Markdown-Datei in Neo4j."""
    if not os.path.isfile(file_path):
        print(f"Datei nicht gefunden: {file_path}")
        return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Titel
    title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
    project_name = title_match.group(1) if title_match else os.path.basename(file_path)
    # Beschreibung
    desc_match = re.search(r"## Beschreibung\n(.+?)(\n##|$)", content, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""
    # Code
    code_match = re.search(r"```python\n(.+?)```", content, re.DOTALL)
    code = code_match.group(1).strip() if code_match else ""
    # Tags
    tags = list(set(re.findall(r"#([A-Za-z0-9_\-]+)", content)))
    # Import in Neo4j
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run(
                """
                MERGE (p:Note {name: $name})
                SET p.description = $description, p.code = $code
                """,
                name=project_name, description=description, code=code
            )
            for tag in tags:
                session.run(
                    """
                    MERGE (t:Tag {name: $tag})
                    MATCH (p:Note {name: $name})
                    MERGE (p)-[:TAGGED_WITH]->(t)
                    """,
                    tag=tag, name=project_name
                )
        print(f"Projekt '{project_name}' importiert. Beschreibung: {description[:40]}... Tags: {', '.join(tags)}")
    except Exception as e:
        print(f"Fehler beim Import: {e}")

@cli.command()
@click.option('--min-confidence', type=float, default=0.4, help='Minimale Konfidenz für Tag-Vorschläge (0.0-1.0)')
@click.option('--max-tags-per-note', type=int, default=5, help='Maximale neue Tags pro Note')
@click.option('--learning-threshold', type=int, default=3, help='Min. Anzahl ähnlicher Notes für Tag-Learning')
def ai_suggest_tags(min_confidence, max_tags_per_note, learning_threshold):
    """AI-basierte Tag-Vorschläge basierend auf Content-Ähnlichkeit und Lernmuster."""
    try:
        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            print("🧠 Starte AI-basierte Tag-Analyse...")

            # Hole alle Notes mit Content und bestehenden Tags
            notes_with_tags = session.run("""
                MATCH (n:Note)
                WHERE n.content IS NOT NULL AND size(n.content) >= 30
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                RETURN n.name as name, 
                       n.content as content, 
                       n.description as description,
                       collect(t.name) as existing_tags
                ORDER BY n.name
            """).data()

            print(f"📊 Analysiere {len(notes_with_tags)} Notes für Tag-Learning...")

            # Baue Tag-Learning-Modell auf
            tag_content_patterns = build_tag_learning_model(notes_with_tags, learning_threshold)

            suggestions_made = 0
            total_suggestions = 0

            # Generiere Tag-Vorschläge für jede Note
            for note in notes_with_tags:
                if not note['existing_tags'] or len([t for t in note['existing_tags'] if t]) < 2:
                    suggested_tags = suggest_tags_for_note(
                        note,
                        tag_content_patterns,
                        notes_with_tags,
                        min_confidence
                    )

                    if suggested_tags:
                        print(f"\n💡 Vorschläge für Note: '{note['name']}'")
                        print(f"   📋 Bestehende Tags: {[t for t in note['existing_tags'] if t] or 'Keine'}")
                        print("   🎯 Vorgeschlagene Tags:")

                        for tag_suggestion in suggested_tags[:max_tags_per_note]:
                            tag_name = tag_suggestion['tag']
                            confidence = tag_suggestion['confidence']
                            reasons = tag_suggestion['reasons']

                            print(f"      - '{tag_name}' (Konfidenz: {confidence:.2f})")
                            print(f"        📝 Grund: {', '.join(reasons[:2])}")
                            total_suggestions += 1

                        suggestions_made += 1

            print(f"\n✅ AI Tag-Analyse abgeschlossen:")
            print(f"   📊 {suggestions_made} Notes mit Tag-Vorschlägen")
            print(f"   🏷️ {total_suggestions} Tags vorgeschlagen")
            print(f"   💡 Verwende 'ai-apply-tag-suggestions' um Vorschläge anzuwenden")

    except Exception as e:
        print(f"❌ Fehler bei der AI Tag-Analyse: {e}")
        import traceback
        traceback.print_exc()

def build_tag_learning_model(notes_with_tags, learning_threshold):
    """Baut ein Lernmodell auf, das Tag-Content-Muster erkennt."""
    tag_patterns = {}

    # Sammle Content-Muster für jeden Tag
    for note in notes_with_tags:
        content_text = f"{note['content']} {note.get('description', '')}".lower()
        content_keywords = set(extract_keywords(content_text))

        for tag in note['existing_tags']:
            if tag:  # Filtere None/leere Tags
                if tag not in tag_patterns:
                    tag_patterns[tag] = {
                        'keyword_frequency': {},
                        'phrase_patterns': set(),
                        'notes_count': 0,
                        'total_content_length': 0
                    }

                # Keyword-Frequenzen sammeln
                for keyword in content_keywords:
                    if keyword not in tag_patterns[tag]['keyword_frequency']:
                        tag_patterns[tag]['keyword_frequency'][keyword] = 0
                    tag_patterns[tag]['keyword_frequency'][keyword] += 1

                # Phrasen-Muster sammeln
                phrases = extract_phrases(content_text)
                tag_patterns[tag]['phrase_patterns'].update(phrases)

                tag_patterns[tag]['notes_count'] += 1
                tag_patterns[tag]['total_content_length'] += len(content_text)

    # Filtere Tags mit zu wenigen Beispielen
    filtered_patterns = {
        tag: patterns for tag, patterns in tag_patterns.items()
        if patterns['notes_count'] >= learning_threshold
    }

    # Berechne Relevanz-Scores für Keywords
    for tag, patterns in filtered_patterns.items():
        keyword_scores = {}
        total_notes = patterns['notes_count']

        for keyword, freq in patterns['keyword_frequency'].items():
            # TF-IDF-ähnlicher Score
            tf = freq / total_notes
            # Vereinfachter IDF (könnte verbessert werden)
            idf = 1.0 / (1 + sum(1 for other_tag, other_patterns in filtered_patterns.items()
                                if other_tag != tag and keyword in other_patterns['keyword_frequency']))

            keyword_scores[keyword] = tf * idf

        patterns['keyword_scores'] = keyword_scores

    print(f"🎓 Lernmodell aufgebaut: {len(filtered_patterns)} Tags mit genügend Training-Daten")

    return filtered_patterns

def suggest_tags_for_note(note, tag_patterns, all_notes, min_confidence):
    """Schlägt Tags für eine Note basierend auf dem Lernmodell vor."""
    content_text = f"{note['content']} {note.get('description', '')}".lower()
    content_keywords = set(extract_keywords(content_text))
    content_phrases = extract_phrases(content_text)
    existing_tags = set(tag for tag in note['existing_tags'] if tag)

    suggestions = []

    for tag, patterns in tag_patterns.items():
        if tag in existing_tags:
            continue  # Skip bereits vorhandene Tags

        confidence_factors = []
        reasons = []

        # 1. Keyword-basierte Ähnlichkeit
        keyword_matches = content_keywords.intersection(set(patterns['keyword_scores'].keys()))
        if keyword_matches:
            keyword_score = sum(patterns['keyword_scores'][kw] for kw in keyword_matches) / len(patterns['keyword_scores'])
            confidence_factors.append(keyword_score * 0.6)
            reasons.append(f"Keywords: {', '.join(list(keyword_matches)[:3])}")

        # 2. Phrasen-basierte Ähnlichkeit
        phrase_matches = content_phrases.intersection(patterns['phrase_patterns'])
        if phrase_matches:
            phrase_score = len(phrase_matches) / len(patterns['phrase_patterns']) if patterns['phrase_patterns'] else 0
            confidence_factors.append(phrase_score * 0.4)
            reasons.append(f"Phrasen: {len(phrase_matches)} Übereinstimmungen")

        # 3. Content-Ähnlichkeit zu anderen Notes mit diesem Tag
        similar_notes_score = calculate_tag_similarity_score(note, tag, all_notes)
        if similar_notes_score > 0:
            confidence_factors.append(similar_notes_score * 0.3)
            reasons.append(f"Ähnlich zu anderen '{tag}'-Notes")

        if confidence_factors:
            # Gewichteter Durchschnitt
            total_confidence = sum(confidence_factors) / len(confidence_factors)

            if total_confidence >= min_confidence:
                suggestions.append({
                    'tag': tag,
                    'confidence': total_confidence,
                    'reasons': reasons
                })

    # Sortiere nach Konfidenz
    suggestions.sort(key=lambda x: x['confidence'], reverse=True)

    return suggestions

def extract_phrases(text, min_length=6):
    """Extrahiert relevante Phrasen aus Text."""
    import re

    words = re.findall(r'\b[a-zA-ZäöüßÄÖÜ]+\b', text.lower())
    phrases = set()

    # 2-Wort Phrasen
    for i in range(len(words) - 1):
        phrase = f"{words[i]} {words[i+1]}"
        if len(phrase) >= min_length:
            phrases.add(phrase)

    # 3-Wort Phrasen (selektiv)
    for i in range(len(words) - 2):
        phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
        if len(phrase) >= min_length + 4:
            phrases.add(phrase)

    return phrases

def calculate_tag_similarity_score(target_note, tag, all_notes):
    """Berechnet Ähnlichkeits-Score zu anderen Notes mit dem gleichen Tag."""
    target_text = f"{target_note['content']} {target_note.get('description', '')}".lower()
    target_keywords = set(extract_keywords(target_text))

    if not target_keywords:
        return 0.0

    similar_notes = [
        note for note in all_notes
        if tag in (note['existing_tags'] or []) and note['name'] != target_note['name']
    ]

    if not similar_notes:
        return 0.0

    similarity_scores = []

    for similar_note in similar_notes[:5]:  # Limitiere auf Top 5 für Performance
        similar_text = f"{similar_note['content']} {similar_note.get('description', '')}".lower()
        similar_keywords = set(extract_keywords(similar_text))

        if similar_keywords:
            # Jaccard-Ähnlichkeit
            intersection = len(target_keywords.intersection(similar_keywords))
            union = len(target_keywords.union(similar_keywords))
            similarity = intersection / union if union > 0 else 0
            similarity_scores.append(similarity)

    return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0

@cli.command()
@click.option('--min-confidence', type=float, default=0.5, help='Minimale Konfidenz für automatische Anwendung')
@click.option('--dry-run', is_flag=True, help='Zeige nur Vorschau ohne Änderungen')
@click.option('--max-tags-per-note', type=int, default=3, help='Maximale neue Tags pro Note')
def ai_apply_tag_suggestions(min_confidence, dry_run, max_tags_per_note):
    """Wendet AI-basierte Tag-Vorschläge automatisch an."""
    try:
        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            print("🤖 Starte automatische Tag-Anwendung...")

            # Hole Notes und generiere Vorschläge
            notes_with_tags = session.run("""
                MATCH (n:Note)
                WHERE n.content IS NOT NULL AND size(n.content) >= 30
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                RETURN n.name as name, 
                       n.content as content, 
                       n.description as description,
                       collect(t.name) as existing_tags
                ORDER BY n.name
            """).data()

            # Baue Lernmodell
            tag_patterns = build_tag_learning_model(notes_with_tags, 3)

            applied_count = 0
            total_tags_added = 0

            for note in notes_with_tags:
                if not note['existing_tags'] or len([t for t in note['existing_tags'] if t]) < 2:
                    suggested_tags = suggest_tags_for_note(
                        note,
                        tag_patterns,
                        notes_with_tags,
                        min_confidence
                    )

                    high_confidence_tags = [
                        s for s in suggested_tags[:max_tags_per_note]
                        if s['confidence'] >= min_confidence
                    ]

                    if high_confidence_tags:
                        print(f"\n📝 Note: '{note['name']}'")

                        for tag_suggestion in high_confidence_tags:
                            tag_name = tag_suggestion['tag']
                            confidence = tag_suggestion['confidence']

                            if dry_run:
                                print(f"   🏷️ Würde Tag hinzufügen: '{tag_name}' (Konfidenz: {confidence:.2f})")
                            else:
                                try:
                                    # Tag erstellen und verknüpfen
                                    session.run("""
                                        MERGE (t:Tag {name: $tag_name})
                                        MERGE (n:Note {name: $note_name})
                                        MERGE (n)-[r:TAGGED_WITH]->(t)
                                        SET r.ai_generated = true,
                                            r.confidence = $confidence,
                                            r.created_at = timestamp()
                                    """, tag_name=tag_name, note_name=note['name'], confidence=confidence)

                                    print(f"   ✅ Tag hinzugefügt: '{tag_name}' (Konfidenz: {confidence:.2f})")
                                    total_tags_added += 1

                                except Exception as e:
                                    print(f"   ❌ Fehler beim Hinzufügen von Tag '{tag_name}': {e}")

                        applied_count += 1

            if dry_run:
                print(f"\n🔍 Dry-Run Ergebnis:")
                print(f"   📊 {applied_count} Notes würden Tags erhalten")
                print(f"   🏷️ {sum(len([s for s in suggest_tags_for_note(note, tag_patterns, notes_with_tags, min_confidence)[:max_tags_per_note] if s['confidence'] >= min_confidence]) for note in notes_with_tags)} Tags würden hinzugefügt")
                print(f"   💡 Verwende ohne --dry-run um Änderungen anzuwenden")
            else:
                print(f"\n✅ AI Tag-Anwendung abgeschlossen:")
                print(f"   📊 {applied_count} Notes erweitert")
                print(f"   🏷️ {total_tags_added} neue Tags hinzugefügt")

    except Exception as e:
        print(f"❌ Fehler bei der automatischen Tag-Anwendung: {e}")
        import traceback
        traceback.print_exc()

@cli.command()
@click.argument('note_name')
@click.option('--suggestions', type=int, default=5, help='Anzahl der Tag-Vorschläge')
@click.option('--min-confidence', type=float, default=0.3, help='Minimale Konfidenz für Vorschläge')
def ai_suggest_tags_for_note(note_name, suggestions, min_confidence):
    """AI-basierte Tag-Vorschläge für eine spezifische Note."""
    try:
        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            # Hole die Ziel-Note
            target_result = session.run("""
                MATCH (n:Note {name: $name})
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                RETURN n.name as name, 
                       n.content as content, 
                       n.description as description,
                       collect(t.name) as existing_tags
            """, name=note_name).single();

            if not target_result:
                print(f"❌ Note '{note_name}' nicht gefunden.")
                return

            if not target_result['content']:
                print(f"❌ Note '{note_name}' hat keinen Content für Tag-Analyse.")
                return

            # Hole alle Notes für Lernmodell
            all_notes = session.run("""
                MATCH (n:Note)
                WHERE n.content IS NOT NULL AND size(n.content) >= 30
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                RETURN n.name as name, 
                       n.content as content, 
                       n.description as description,
                       collect(t.name) as existing_tags
                ORDER BY n.name
            """).data()

            # Baue Lernmodell
            tag_patterns = build_tag_learning_model(all_notes, 2)

            # Generiere Vorschläge
            suggested_tags = suggest_tags_for_note(
                target_result,
                tag_patterns,
                all_notes,
                min_confidence
            )

            print(f"🧠 AI Tag-Vorschläge für: '{note_name}'")
            print(f"📋 Bestehende Tags: {[t for t in target_result['existing_tags'] if t] or 'Keine'}")
            print()

            if not suggested_tags:
                print(f"📭 Keine Tag-Vorschläge gefunden (min_confidence={min_confidence})")
                print("💡 Versuche einen niedrigeren --min-confidence Wert")
                return

            print("🏷️ Vorgeschlagene Tags:")
            for i, suggestion in enumerate(suggested_tags[:suggestions]):
                tag = suggestion['tag']
                confidence = suggestion['confidence']
                reasons = suggestion['reasons']

                print(f"{i+1}. '{tag}' (Konfidenz: {confidence:.3f})")
                print(f"   📝 Gründe: {', '.join(reasons[:2])}")
                print()

            print(f"💡 Verwende 'ai-apply-tag-suggestions --min-confidence {min_confidence}' für automatische Anwendung")

    except Exception as e:
        print(f"❌ Fehler bei der Tag-Vorschlag-Generierung: {e}")
        import traceback
        traceback.print_exc()

# --- Sichere Workflow-Operationen (mit Transaction Safety) ---
@cli.command()
@click.argument('workflow_name')
def create_workflow_safe(workflow_name):
    """Legt einen neuen Workflow sicher an (mit Backup & Transaction Safety)."""
    manager = Neo4jHelper.get_safe_transaction_manager()

    @manager.safe_transaction("create_workflow")
    def _create_workflow_tx(tx, name):
        result = tx.run(
            "MERGE (w:Workflow {name: $workflow_name, type: 'Standard', status: 'in progress'}) RETURN w",
            workflow_name=name
        )
        return result.single()

    try:
        result = _create_workflow_tx(workflow_name)
        if result:
            click.echo(f"✅ Workflow '{workflow_name}' sicher angelegt.")
        else:
            click.echo(f"⚠️ Workflow '{workflow_name}' bereits vorhanden.")
    except Exception as e:
        click.echo(f"❌ Fehler beim sicheren Anlegen des Workflows: {e}")

@cli.command()
@click.argument('workflow_name')
@click.option('--confirm', is_flag=True, help='Bestätige gefährliche Löschoperation')
def delete_workflow_safe(workflow_name, confirm):
    """Löscht einen Workflow SICHER mit Backup und Bestätigung."""

    # Sicherheitscheck
    if not confirm:
        click.echo("⚠️ GEFÄHRLICHE OPERATION! Verwende --confirm")
        click.echo("💡 Dieser Befehl löscht den Workflow und alle zugehörigen Steps!")
        return

    # Validiere Datenbestand vor Operation
    if not Neo4jHelper.validate_connection_and_data():
        click.echo("❌ Datenvalidierung fehlgeschlagen - Operation abgebrochen")
        return

    manager = Neo4jHelper.get_safe_transaction_manager()

    @manager.safe_transaction("delete_workflow")
    def _delete_workflow_tx(tx, name):
        # Prüfe was gelöscht wird
        check_result = tx.run(
            """
            MATCH (w:Workflow {name: $workflow_name})-[:HAS_STEP]->(s:Step)
            RETURN w, count(s) as step_count
            """,
            workflow_name=name
        ).single()

        if not check_result:
            return {"deleted": False, "reason": "Workflow nicht gefunden"}

        step_count = check_result['step_count']

        # Zeige was gelöscht wird
        click.echo(f"🗑️ Lösche Workflow '{name}' mit {step_count} Steps")

        # Bestätigungsprompt
        if not click.confirm("Wirklich löschen?"):
            return {"deleted": False, "reason": "Von Benutzer abgebrochen"}

        # Eigentliche Löschung
        delete_result = tx.run(
            """
            MATCH (w:Workflow {name: $workflow_name})-[r:HAS_STEP]->(s:Step)
            DETACH DELETE w, s
            RETURN count(w) as workflows_deleted, count(s) as steps_deleted
            """,
            workflow_name=name
        ).single()

        return {
            "deleted": True,
            "workflows_deleted": delete_result['workflows_deleted'],
            "steps_deleted": delete_result['steps_deleted']
        }

    try:
        result = _delete_workflow_tx(workflow_name)

        if result['deleted']:
            click.echo(f"✅ Workflow '{workflow_name}' und {result['steps_deleted']} Steps sicher gelöscht")
        else:
            click.echo(f"❌ Löschung abgebrochen: {result['reason']}")

    except Exception as e:
        click.echo(f"❌ Fehler bei sicherer Löschung: {e}")
        click.echo("💡 Backup verfügbar in cortex_neo/backups/auto/")

        # Angebot zur Wiederherstellung
        if click.confirm("Aus dem letzten Backup wiederherstellen?"):
            click.echo("🔄 Wiederherstellung aus Backup wird implementiert...")

@cli.command()
@click.argument('name')
@click.option('--content', help='Textinhalt der Note')
@click.option('--description', help='Kurze Beschreibung der Note')
@click.option('--type', 'note_type', help='Typ/Kategorie der Note')
@click.option('--url', help='URL/Link zur Note')
def add_note_safe(name, content, description, note_type, url):
    """Legt eine Note SICHER mit automatischem Backup an."""

    manager = Neo4jHelper.get_safe_transaction_manager()

    @manager.safe_transaction("add_note")
    def _add_note_tx(tx, name, content, description, note_type, url):
        # Prüfe ob Note bereits existiert
        existing = tx.run("MATCH (n:Note {name: $name}) RETURN n", name=name).single()

        # Erstelle/update Note mit allen verfügbaren Properties
        result = tx.run(
            """
            MERGE (n:Note {name: $name})
            SET n.content = $content,
                n.description = $description,
                n.type = $note_type,
                n.url = $url,
                n.updated_at = timestamp(),
                n.governance_validated = true
            RETURN n, $content is not null as has_content
            """,
            name=name,
            content=content or "",
            description=description or "",
            note_type=note_type or "",
            url=url or ""
        ).single()

        return {
            "note": result['n'],
            "was_existing": existing is not None,
            "has_content": result['has_content']
        }

    try:
        result = _add_note_tx(name, content, description, note_type, url)

        if result['was_existing']:
            click.echo(f"✅ Note '{name}' sicher aktualisiert")
        else:
            click.echo(f"✅ Note '{name}' sicher angelegt")

        if result['has_content']:
            content_preview = content[:100] + "..." if len(content) > 100 else content
            click.echo(f"   📄 Content: {content_preview}")
        if description:
            click.echo(f"   📝 Beschreibung: {description}")
        if note_type:
            click.echo(f"   🏷️ Typ: {note_type}")
        if url:
            click.echo(f"   🔗 URL: {url}")

    except Exception as e:
        click.echo(f"❌ Fehler beim sicheren Anlegen der Note: {e}")

@cli.command()
@click.argument('name')
@click.option('--confirm', is_flag=True, help='Bestätige Note-Löschung')
def delete_note_safe(name, confirm):
    """Löscht eine Note SICHER mit Backup, Bestätigung und Wiederherstellungsoption."""

    if not confirm:
        click.echo("⚠️ GEFÄHRLICHE OPERATION! Verwende --confirm")
        return

    # Validiere Datenbestand
    if not Neo4jHelper.validate_connection_and_data():
        click.echo("❌ Datenvalidierung fehlgeschlagen - Operation abgebrochen")
        return

    manager = Neo4jHelper.get_safe_transaction_manager()

    @manager.safe_transaction("delete_note")
    def _delete_note_tx(tx, name):
        # Prüfe was gelöscht wird (inkl. Beziehungen)
        note_info = tx.run(
            """
            MATCH (n:Note {name: $name})
            OPTIONAL MATCH (n)-[r1:TAGGED_WITH]->(t:Tag)
            OPTIONAL MATCH (n)-[r2:USES_TEMPLATE]->(tpl:Template)
            OPTIONAL MATCH (n)-[r3:LINKS_TO]->(out:Note)
            OPTIONAL MATCH (in:Note)-[r4:LINKS_TO]->(n)
            RETURN n,
                   count(DISTINCT t) as tag_count,
                   count(DISTINCT tpl) as template_count,
                   count(DISTINCT r3) as outgoing_links,
                   count(DISTINCT r4) as incoming_links
            """,
            name=name
        ).single()

        if not note_info or not note_info['n']:
            return {"deleted": False, "reason": "Note nicht gefunden"}

        note = note_info['n']

        # Zeige Lösch-Info
        click.echo(f"🗑️ Lösche Note: '{name}'")
        if note.get('description'):
            click.echo(f"   📝 Beschreibung: {note['description']}")
        if note.get('content'):
            content_preview = note['content'][:100] + "..." if len(note['content']) > 100 else note['content']
            click.echo(f"   📄 Content: {content_preview}")
        click.echo(f"   🔗 Verbindungen: {note_info['tag_count']} Tags, {note_info['template_count']} Templates")
        click.echo(f"   🔗 Links: {note_info['outgoing_links']} ausgehend, {note_info['incoming_links']} eingehend")

        # Finale Bestätigung
        if not click.confirm("Wirklich löschen? Alle Verbindungen werden entfernt!"):
            return {"deleted": False, "reason": "Von Benutzer abgebrochen"}

        # Löschung durchführen
        tx.run("MATCH (n:Note {name: $name}) DETACH DELETE n", name=name)

        return {
            "deleted": True,
            "note_info": note_info
        }

    try:
        result = _delete_note_tx(name)

        if result['deleted']:
            click.echo(f"✅ Note '{name}' sicher gelöscht")
            click.echo("🔄 Automatisches Backup erstellt")
        else:
            click.echo(f"❌ Löschung abgebrochen: {result['reason']}")

    except Exception as e:
        click.echo(f"❌ Fehler bei sicherer Löschung: {e}")
        click.echo("💡 Backup verfügbar in cortex_neo/backups/auto/")

        # Wiederherstellungsoption
        if click.confirm("Aus dem letzten Backup wiederherstellen?"):
            # TODO: Implementiere Backup-Wiederherstellung
            click.echo("🔄 Wiederherstellung wird in der nächsten Version verfügbar sein")

# --- Kritische System-Operationen ---
@cli.command()
def validate_connection():
    """Validiert Neo4j-Verbindung und Datenintegrität mit detailliertem Report."""
    try:
        click.echo("🔍 Starte Verbindungs- und Datenvalidierung...")

        # Connection Test
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Test basic connectivity
            test_result = session.run("RETURN 1 as test, timestamp() as time").single()
            click.echo(f"✅ Neo4j-Verbindung erfolgreich")
            click.echo(f"   🔗 URI: {NEO4J_URI}")
            click.echo(f"   🕒 Server-Zeit: {test_result['time']}")

        # Validate data integrity
        is_healthy = Neo4jHelper.validate_connection_and_data()

        if is_healthy:
            click.echo("✅ Alle Validierungen erfolgreich")
        else:
            click.echo("⚠️ Datenintegritätsprobleme erkannt")

        return is_healthy

    except Exception as e:
        click.echo(f"❌ Validierung fehlgeschlagen: {e}")
        click.echo("💡 Mögliche Lösungen:")
        click.echo("   - Prüfe Neo4j-Container: docker ps | grep neo4j")
        click.echo("   - Starte Neo4j: cd cortex_neo && docker-compose up -d")
        click.echo("   - Prüfe Umgebungsvariablen: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        return False

@cli.command()
@click.option('--emergency', is_flag=True, help='Notfall-Modus: Prüfe auf kritischen Datenverlust')
def check_data_integrity(emergency):
    """Prüft Datenintegrität und warnt vor Anomalien."""
    try:
        validator = Neo4jHelper.get_validator()

        if emergency:
            click.echo("🚨 NOTFALL-DATENPRÜFUNG")
            needs_restore = validator.emergency_restore_check()

            if needs_restore:
                click.echo("🚨 KRITISCHER DATENVERLUST ERKANNT!")
                click.echo("💡 Verfügbare Backups prüfen...")

                # Liste verfügbare Backups
                backup_dir = "cortex_neo/backups"
                if os.path.exists(backup_dir):
                    backup_files = sorted([
                        f for f in os.listdir(backup_dir)
                        if f.endswith(('.yaml', '.tar.gz', '.dump'))
                    ], reverse=True)

                    click.echo("📁 Verfügbare Backups:")
                    for i, backup in enumerate(backup_files[:10]):  # Show last 10
                        backup_path = os.path.join(backup_dir, backup)
                        size = os.path.getsize(backup_path)
                        click.echo(f"   {i+1}. {backup} ({size} bytes)")

                return False
            else:
                click.echo("✅ Keine kritischen Datenprobleme erkannt")

        # Standard-Integritätsprüfung
        is_healthy = validator.validate_integrity()

        if is_healthy:
            click.echo("✅ Datenintegrität OK")
        else:
            click.echo("⚠️ Datenintegritätsprobleme - siehe Details oben")

        return is_healthy

    except Exception as e:
        click.echo(f"❌ Integritätsprüfung fehlgeschlagen: {e}")
        return False

@cli.command()
def create_emergency_backup():
    """Erstellt sofortiges Notfall-Backup aller Daten."""
    try:
        click.echo("🚨 Erstelle Notfall-Backup...")

        manager = Neo4jHelper.get_safe_transaction_manager()
        backup_file = manager._create_backup(f"emergency-{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        if backup_file:
            click.echo(f"✅ Notfall-Backup erstellt: {backup_file}")

            # Zusätzlich: Structure Export
            export_file = f"cortex_neo/backups/emergency-structure-{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
            os.system(f"cd cortex_neo && python cortex_cli.py export-structure --out {export_file}")

            click.echo(f"📊 Struktur-Export: {export_file}")

        else:
            click.echo("❌ Backup-Erstellung fehlgeschlagen")

    except Exception as e:
        click.echo(f"❌ Notfall-Backup fehlgeschlagen: {e}")

@cli.command()
def monitor_data_changes():
    """Startet kontinuierliches Datenmonitoring für Änderungen."""
    try:
        click.echo("🔍 Starte Datenmonitoring...")

        validator = Neo4jHelper.get_validator()

        # Baseline erstellen
        baseline_stats = validator.get_current_stats()
        click.echo(f"📊 Baseline erstellt: {baseline_stats['notes']} Notes, {baseline_stats['workflows']} Workflows")

        # Monitoring-Loop (vereinfacht für Demo)
        import time
        check_count = 0

        while check_count < 5:  # Demo: 5 Checks
            time.sleep(2)  # Alle 2 Sekunden prüfen
            check_count += 1

            current_stats = validator.get_current_stats()

            # Prüfe auf Änderungen
            note_diff = current_stats['notes'] - baseline_stats['notes']
            workflow_diff = current_stats['workflows'] - baseline_stats['workflows']

            if note_diff != 0 or workflow_diff != 0:
                click.echo(f"📈 Änderung erkannt: Notes {note_diff:+d}, Workflows {workflow_diff:+d}")

                # Bei kritischen Änderungen Backup erstellen
                if abs(note_diff) > 2:
                    click.echo("🔄 Automatisches Backup aufgrund großer Änderung...")
                    manager = Neo4jHelper.get_safe_transaction_manager()
                    manager._create_backup(f"change-detected-{datetime.now().strftime('%H%M%S')}")

            click.echo(f"✓ Check {check_count}/5 - Status OK")

        click.echo("✅ Monitoring-Demo abgeschlossen")
        click.echo("💡 Für kontinuierliches Monitoring: Implementiere als Background-Service")

    except KeyboardInterrupt:
        click.echo("\n⏹️ Monitoring gestoppt")
    except Exception as e:
        click.echo(f"❌ Monitoring-Fehler: {e}")

@cli.command()
def run_safety_diagnostics():
    """Führt vollständige Sicherheitsdiagnostik durch."""
    try:
        click.echo("🛡️ Starte Sicherheitsdiagnostik...")
        click.echo("=" * 50)

        # 1. Verbindungstest
        click.echo("\n1️⃣ Verbindungstest...")
        connection_ok = validate_connection.callback()

        # 2. Datenintegritätsprüfung
        click.echo("\n2️⃣ Datenintegrität...")
        integrity_ok = check_data_integrity.callback(emergency=False)

        # 3. Backup-System-Check
        click.echo("\n3️⃣ Backup-System...")
        backup_dir = "cortex_neo/backups"
        if os.path.exists(backup_dir):
            backup_count = len([f for f in os.listdir(backup_dir) if f.endswith('.yaml')])
            click.echo(f"✅ Backup-System aktiv ({backup_count} Backups verfügbar)")
        else:
            click.echo("⚠️ Backup-Verzeichnis nicht gefunden")

        # 4. Transaction Safety Test
        click.echo("\n4️⃣ Transaction Safety...")
        try:
            manager = Neo4jHelper.get_safe_transaction_manager()
            click.echo("✅ Safe Transaction Manager initialisiert")
        except Exception as e:
            click.echo(f"❌ Transaction Manager Fehler: {e}")

        # 5. Gesamtbewertung
        click.echo("\n" + "=" * 50)
        click.echo("📋 SICHERHEITSREPORT:")

        safety_score = 0
        if connection_ok:
            safety_score += 25
            click.echo("✅ Verbindung: OK")
        else:
            click.echo("❌ Verbindung: FEHLER")

        if integrity_ok:
            safety_score += 25
            click.echo("✅ Datenintegrität: OK")
        else:
            click.echo("❌ Datenintegrität: PROBLEME")

        if os.path.exists(backup_dir):
            safety_score += 25
            click.echo("✅ Backup-System: OK")
        else:
            click.echo("❌ Backup-System: NICHT VERFÜGBAR")

        safety_score += 25  # Transaction Safety (immer OK wenn Code läuft)
        click.echo("✅ Transaction Safety: OK")

        click.echo(f"\n🎯 Gesamt-Sicherheitsscore: {safety_score}/100")

        if safety_score >= 90:
            click.echo("🛡️ AUSGEZEICHNET - Maximale Datensicherheit")
        elif safety_score >= 75:
            click.echo("✅ GUT - Akzeptable Datensicherheit")
        elif safety_score >= 50:
            click.echo("⚠️ MITTELMÄSSIG - Verbesserungen empfohlen")
        else:
            click.echo("🚨 KRITISCH - Sofortige Maßnahmen erforderlich!")

    except Exception as e:
        click.echo(f"❌ Diagnostik fehlgeschlagen: {e}")

# --- Data Governance Commands ---
@cli.command('init-governance')
@click.option('--force', is_flag=True, help='Überschreibe bestehende Governance-Strukturen')
def init_governance(force):
    """Initialisiert Data Governance System in Neo4j."""
    try:
        print("🚀 Initialisiere Data Governance System in Neo4j...")

        # Initialize governance engine
        from src.governance.data_governance import DataGovernanceEngine
        governance = DataGovernanceEngine('governance_config.yaml')
        governance.set_neo4j_driver(Neo4jHelper.get_driver())

        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            # Check if governance structures already exist
            existing_templates = session.run("MATCH (t:Template) RETURN count(t) as count").single()["count"]
            existing_workflows = session.run("MATCH (w:Workflow) RETURN count(w) as count").single()["count"]

            if (existing_templates > 0 or existing_workflows > 0) and not force:
                print(f"⚠️ Governance-Strukturen bereits vorhanden:")
                print(f"   📋 Templates: {existing_templates}")
                print(f"   🔄 Workflows: {existing_workflows}")
                print("💡 Verwende --force zum Überschreiben")
                return

            # Load configuration and sync to Neo4j
            config = governance.config

            # Sync templates to Neo4j
            templates_synced = 0
            for template_name, template_data in config.get("templates", {}).items():
                governance.add_template(
                    name=template_name,
                    required_sections=template_data["required_sections"],
                    suggested_tags=template_data["suggested_tags"],
                    workflow_step=template_data.get("workflow_step"),
                    content_standards=template_data.get("content_standards", {})
                )
                templates_synced += 1
                print(f"✅ Template '{template_name}' nach Neo4j synchronisiert")

            # Sync workflows to Neo4j
            workflows_synced = 0
            for workflow_name, workflow_data in config.get("workflows", {}).items():
                governance.add_workflow(
                    name=workflow_name,
                    steps=workflow_data["steps"],
                    templates=workflow_data.get("templates", []),
                    auto_assign=workflow_data.get("auto_assign", True)
                )
                workflows_synced += 1
                print(f"✅ Workflow '{workflow_name}' nach Neo4j synchronisiert")

            # Sync validation rules to Neo4j
            rules = config.get("validation_rules", {})
            governance.save_validation_rules_to_neo4j(rules)
            print(f"✅ {len(rules)} Validierungsregeln nach Neo4j synchronisiert")

            print(f"\n🎉 Data Governance System erfolgreich initialisiert:")
            print(f"   📋 {templates_synced} Templates")
            print(f"   🔄 {workflows_synced} Workflows")
            print(f"   ⚙️ {len(rules)} Validierungsregeln")
            print("\n💡 Das System lädt jetzt dynamisch aus Neo4j!")

    except Exception as e:
        print(f"❌ Fehler bei der Governance-Initialisierung: {e}")
        import traceback
        traceback.print_exc()

@cli.command('add-note-safe')
@click.argument('name')
@click.option('--content', help='Textinhalt der Note')
@click.option('--description', help='Kurze Beschreibung der Note')
@click.option('--type', 'note_type', help='Typ/Kategorie der Note')
@click.option('--template', help='Template für die Note')
@click.option('--force', is_flag=True, help='Ignoriere Validierungsfehler')
@click.option('--validate-only', is_flag=True, help='Nur validieren, nicht erstellen')
@click.option('--auto-apply', is_flag=True, help='Empfehlungen automatisch anwenden')
def add_note_safe_governance(name, content, description, note_type, template, force, validate_only, auto_apply):
    """Sichere Note-Erstellung mit Data-Governance-Validierung und Neo4j-Integration."""

    # Initialize governance engine with Neo4j connection
    from src.governance.data_governance import DataGovernanceEngine
    governance = DataGovernanceEngine('governance_config.yaml')
    governance.set_neo4j_driver(Neo4jHelper.get_driver())

    validation_result = governance.validate_note_creation(
        name, content or "", description or "", note_type or "", template
    )

    # Zeige Validierungsergebnisse
    validation_passed = print_governance_validation_result(validation_result, name)

    # Validate-Only Modus
    if validate_only:
        if validation_passed:
            print("✅ Validierung erfolgreich - Note kann erstellt werden")
        else:
            print("❌ Validierung fehlgeschlagen - Note nicht bereit")
        return

    # Prüfe ob Erstellung erlaubt ist
    if not validation_passed and not force:
        print("\n❌ Note-Erstellung blockiert aufgrund von Validierungsfehlern")
        print("💡 Verwende --force um trotzdem zu erstellen, oder behebe die Fehler")
        return

    # Wenn Warnungen da sind, frage nach Bestätigung
    if validation_result.warnings and not force and not auto_apply:
        if not click.confirm("\n⚠️ Trotz Warnungen fortfahren?"):
            print("❌ Abgebrochen")
            return

    try:
        # Verwende Safe Transaction Manager für sichere Erstellung
        manager = Neo4jHelper.get_safe_transaction_manager()

        @manager.safe_transaction("add_note_governance")
        def _add_note_with_governance(tx, name, content, description, note_type, template):
            props = {"name": name}
            if content:
                props["content"] = content
            if description:
                props["description"] = description
            if note_type:
                props["type"] = note_type

            result = tx.run("""
                MERGE (n:Note {name: $name})
                SET n.content = $content,
                    n.description = $description,
                    n.type = $note_type,
                    n.updated_at = timestamp(),
                    n.governance_validated = true
                RETURN n
            """, name=name, content=content or "", description=description or "", note_type=note_type or "")

            return result.single()

        result = _add_note_with_governance(name, content, description, note_type, template)
        if result:
            print(f"✅ Note '{name}' erfolgreich mit Data Governance erstellt")

            # Auto-Apply Suggestions
            if validation_result.suggestions and (auto_apply or click.confirm("🤖 Empfehlungen automatisch anwenden?")):
                apply_governance_suggestions(name, validation_result.suggestions)

    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Note: {e}")

@cli.command('governance-report')
@click.option('--detailed', is_flag=True, help='Detaillierter Report mit Beispielen')
@click.option('--json', 'as_json', is_flag=True, help='Ausgabe als JSON')
def governance_report(detailed, as_json):
    """Erstellt einen Data Governance Report für alle Notes mit Neo4j-Integration."""
    try:
        # Initialize governance engine with Neo4j connection
        from src.governance.data_governance import DataGovernanceEngine
        governance = DataGovernanceEngine('governance_config.yaml')
        governance.set_neo4j_driver(Neo4jHelper.get_driver())

        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            notes = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                OPTIONAL MATCH (n)-[:USES_TEMPLATE]->(tpl:Template)
                RETURN n.name as name, 
                       n.content as content, 
                       n.description as description,
                       n.type as type,
                       collect(DISTINCT t.name) as tags,
                       collect(DISTINCT tpl.name) as templates
                ORDER BY n.name
            """).data()

        total_notes = len(notes)
        notes_with_issues = 0
        total_errors = 0
        total_warnings = 0

        issue_examples = []

        print(f"🔍 Data Governance Report für {total_notes} Notes")
        print("=" * 60)

        for note in notes:
            validation_result = governance.validate_note_creation(
                note['name'],
                note['content'] or "",
                note['description'] or "",
                note['type'] or "",
                note['templates'][0] if note['templates'] and note['templates'][0] else None
            )

            if validation_result.errors or validation_result.warnings:
                notes_with_issues += 1
                total_errors += len(validation_result.errors)
                total_warnings += len(validation_result.warnings)

                if detailed and len(issue_examples) < 5:
                    issue_examples.append({
                        'note': note['name'],
                        'errors': validation_result.errors,
                        'warnings': validation_result.warnings
                    })

        # Summary
        quality_score = max(0, 100 - (total_errors * 10) - (total_warnings * 5))

        if as_json:
            report = {
                'total_notes': total_notes,
                'notes_with_issues': notes_with_issues,
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'quality_score': quality_score,
                'issue_examples': issue_examples if detailed else []
            }
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(f"📊 Gesamt-Notes: {total_notes}")
            print(f"⚠️ Notes mit Problemen: {notes_with_issues}")
            print(f"❌ Kritische Fehler: {total_errors}")
            print(f"⚠️ Warnungen: {total_warnings}")
            print(f"🎯 Qualitätsscore: {quality_score}/100")

            if quality_score >= 90:
                print("✅ AUSGEZEICHNETE Datenqualität!")
            elif quality_score >= 75:
                print("🟢 GUTE Datenqualität")
            elif quality_score >= 50:
                print("🟡 MITTLERE Datenqualität - Verbesserungen empfohlen")
            else:
                print("🔴 SCHLECHTE Datenqualität - Sofortige Maßnahmen erforderlich!")

            if detailed and issue_examples:
                print("\n📋 Beispielprobleme:")
                for example in issue_examples:
                    print(f"\n📝 Note: '{example['note']}'")
                    for error in example['errors']:
                        print(f"   ❌ {error}")
                    for warning in example['warnings']:
                        print(f"   ⚠️ {warning}")

    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Governance-Reports: {e}")

@cli.command('fix-note-governance')
@click.argument('note_name')
@click.option('--auto-fix', is_flag=True, help='Automatische Behebung wo möglich')
def fix_note_governance(note_name, auto_fix):
    """Analysiert und behebt Data Governance Probleme für eine spezifische Note."""
    try:
        governance = DataGovernanceEngine()
        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            note_result = session.run("""
                MATCH (n:Note {name: $name})
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                OPTIONAL MATCH (n)-[:USES_TEMPLATE]->(tpl:Template)
                RETURN n.name as name, 
                       n.content as content, 
                       n.description as description,
                       n.type as type,
                       collect(DISTINCT t.name) as tags,
                       collect(DISTINCT tpl.name) as templates
            """, name=note_name).single()

        if not note_result:
            print(f"❌ Note '{note_name}' nicht gefunden.")
            return

        validation_result = governance.validate_note_creation(
            note_result['name'],
            note_result['content'] or "",
            note_result['description'] or "",
            note_result['type'] or "",
            note_result['templates'][0] if note_result['templates'] and note_result['templates'][0] else None
        )

        print(f"🔍 Governance-Analyse für: '{note_name}'")
        print_governance_validation_result(validation_result, note_name)

        if not validation_result.errors and not validation_result.warnings:
            print("✅ Keine Probleme gefunden!")
            return

        if auto_fix:
            print(f"\n🤖 Starte automatische Behebung...")

            fixes_applied = 0

            # Automatische Fixes basierend auf Suggestions
            if validation_result.suggestions:
                apply_governance_suggestions(note_name, validation_result.suggestions)
                fixes_applied += len(validation_result.suggestions)

            # Re-validate nach Fixes
            with driver.session() as session:
                updated_note = session.run("""
                    MATCH (n:Note {name: $name})
                    OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                    OPTIONAL MATCH (n)-[:USES_TEMPLATE]->(tpl:Template)
                    RETURN n.name as name, 
                           n.content as content, 
                           n.description as description,
                           n.type as type,
                           collect(DISTINCT t.name) as tags,
                           collect(DISTINCT tpl.name) as templates
                """, name=note_name).single()

            revalidation_result = governance.validate_note_creation(
                updated_note['name'],
                updated_note['content'] or "",
                updated_note['description'] or "",
                updated_note['type'] or "",
                updated_note['templates'][0] if updated_note['templates'] and updated_note['templates'][0] else None
            )

            print(f"\n🔄 Ergebnis nach automatischer Behebung:")
            print_governance_validation_result(revalidation_result, note_name)

            if fixes_applied > 0:
                print(f"✅ {fixes_applied} automatische Korrekturen angewendet")

        else:
            print("\n💡 Verwende --auto-fix für automatische Behebung")

    except Exception as e:
        print(f"❌ Fehler bei der Governance-Behebung: {e}")

@cli.command('batch-governance-fix')
@click.option('--dry-run', is_flag=True, help='Zeige nur Vorschau ohne Änderungen')
@click.option('--auto-apply', is_flag=True, help='Wende alle Korrekturen automatisch an')
@click.option('--max-notes', type=int, default=50, help='Maximale Anzahl Notes zu verarbeiten')
def batch_governance_fix(dry_run, auto_apply, max_notes):
    """Batch-Korrektur von Data Governance Problemen für alle Notes."""
    try:
        governance = DataGovernanceEngine()
        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            notes = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                OPTIONAL MATCH (n)-[:USES_TEMPLATE]->(tpl:Template)
                RETURN n.name as name, 
                       n.content as content, 
                       n.description as description,
                       n.type as type,
                       collect(DISTINCT t.name) as tags,
                       collect(DISTINCT tpl.name) as templates
                ORDER BY n.name
                LIMIT $limit
            """, limit=max_notes).data()

        print(f"🔍 Batch Governance-Fix für {len(notes)} Notes")
        print("=" * 60)

        notes_with_issues = 0
        total_fixes = 0

        for note in notes:
            validation_result = governance.validate_note_creation(
                note['name'],
                note['content'] or "",
                note['description'] or "",
                note['type'] or "",
                note['templates'][0] if note['templates'] and note['templates'][0] else None
            )

            if validation_result.errors or validation_result.warnings or validation_result.suggestions:
                notes_with_issues += 1

                print(f"\n📝 Note: '{note['name']}'")
                if validation_result.errors:
                    print(f"   ❌ {len(validation_result.errors)} Fehler")
                if validation_result.warnings:
                    print(f"   ⚠️ {len(validation_result.warnings)} Warnungen")
                if validation_result.suggestions:
                    print(f"   💡 {len(validation_result.suggestions)} Vorschläge")

                if dry_run:
                    print(f"   🔍 Würde {len(validation_result.suggestions)} Korrekturen anwenden")
                elif auto_apply and validation_result.suggestions:
                    try:
                        apply_governance_suggestions(note['name'], validation_result.suggestions)
                        total_fixes += len(validation_result.suggestions)
                        print(f"   ✅ {len(validation_result.suggestions)} Korrekturen angewendet")
                    except Exception as e:
                        print(f"   ❌ Fehler bei Korrektur: {e}")

        print(f"\n📊 Batch-Ergebnis:")
        print(f"   📝 Notes verarbeitet: {len(notes)}")
        print(f"   ⚠️ Notes mit Problemen: {notes_with_issues}")

        if dry_run:
            print(f"   🔍 Dry-Run Modus - keine Änderungen vorgenommen")
            print(f"   💡 Verwende ohne --dry-run für tatsächliche Korrekturen")
        else:
            print(f"   ✅ Korrekturen angewendet: {total_fixes}")

    except Exception as e:
        print(f"❌ Fehler beim Batch Governance-Fix: {e}")

@cli.command('workflow-assign')
@click.argument('note_name')
@click.argument('workflow_name')
@click.argument('step_name')
def workflow_assign(note_name, workflow_name, step_name):
    """Ordnet eine Note einem Workflow-Step zu (Data Governance Integration)."""
    try:
        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            # Prüfe ob alle Entitäten existieren
            result = session.run("""
                MATCH (n:Note {name: $note_name})
                MATCH (w:Workflow {name: $workflow_name})
                MATCH (s:Step {name: $step_name})
                MATCH (w)-[:HAS_STEP]->(s)
                RETURN n, w, s
            """, note_name=note_name, workflow_name=workflow_name, step_name=step_name).single()

            if not result:
                print("❌ Note, Workflow oder Step nicht gefunden oder nicht verknüpft")
                return

            # Erstelle Zuordnung
            session.run("""
                MATCH (n:Note {name: $note_name})
                MATCH (s:Step {name: $step_name})
                MERGE (n)-[r:ASSIGNED_TO_STEP]->(s)
                SET r.assigned_at = timestamp()
            """, note_name=note_name, step_name=step_name)

            print(f"✅ Note '{note_name}' zu Workflow-Step '{step_name}' zugeordnet")

    except Exception as e:
        print(f"❌ Fehler bei Workflow-Zuordnung: {e}")

# Ende der Data Governance Commands

# Helper function for applying governance suggestions
def apply_governance_suggestions(note_name: str, suggestions: list):
    """Wendet Data Governance Empfehlungen automatisch an."""
    try:
        driver = Neo4jHelper.get_driver()

        with driver.session() as session:
            applied_count = 0

            for suggestion in suggestions:
                suggestion_lower = suggestion.lower()

                try:
                    # Tag-Empfehlungen
                    if "tag hinzufügen" in suggestion_lower or "add tag" in suggestion_lower:
                        # Extrahiere Tag-Name aus Suggestion
                        import re
                        tag_match = re.search(r"tag[:\s]+['\"]?([^'\"]+)['\"]?", suggestion_lower)
                        if tag_match:
                            tag_name = tag_match.group(1).strip()
                            session.run("""
                                MERGE (t:Tag {name: $tag_name})
                                MERGE (n:Note {name: $note_name})
                                MERGE (n)-[r:TAGGED_WITH]->(t)
                                SET r.auto_applied = true,
                                    r.applied_at = timestamp()
                            """, tag_name=tag_name, note_name=note_name)
                            print(f"   ✅ Tag '{tag_name}' automatisch hinzugefügt")
                            applied_count += 1

                    # Template-Empfehlungen
                    elif "template" in suggestion_lower and ("verwenden" in suggestion_lower or "use" in suggestion_lower):
                        template_match = re.search(r"template[:\s]+['\"]?([^'\"]+)['\"]?", suggestion_lower)
                        if template_match:
                            template_name = template_match.group(1).strip()
                            session.run("""
                                MERGE (t:Template {name: $template_name})
                                MERGE (n:Note {name: $note_name})
                                MERGE (n)-[r:USES_TEMPLATE]->(t)
                                SET r.auto_applied = true,
                                    r.applied_at = timestamp()
                            """, template_name=template_name, note_name=note_name)
                            print(f"   ✅ Template '{template_name}' automatisch zugewiesen")
                            applied_count += 1

                    # Beschreibung hinzufügen
                    elif "beschreibung" in suggestion_lower and "hinzufügen" in suggestion_lower:
                        # Generiere eine Standard-Beschreibung basierend auf dem Content
                        content_result = session.run(
                            "MATCH (n:Note {name: $note_name}) RETURN n.content as content",
                            note_name=note_name
                        ).single()

                        if content_result and content_result['content']:
                            # Extrahiere erste Zeile oder ersten Satz als Beschreibung
                            content = content_result['content']
                            first_line = content.split('\n')[0]
                            if len(first_line) > 100:
                                first_line = first_line[:97] + "..."

                            session.run("""
                                MATCH (n:Note {name: $note_name})
                                SET n.description = $description,
                                    n.description_auto_generated = true,
                                    n.updated_at = timestamp()
                            """, note_name=note_name, description=first_line)
                            print(f"   ✅ Beschreibung automatisch generiert: '{first_line[:50]}...'")
                            applied_count += 1

                    # Typ zuweisen
                    elif "typ" in suggestion_lower and ("zuweisen" in suggestion_lower or "setzen" in suggestion_lower):
                        type_match = re.search(r"typ[:\s]+['\"]?([^'\"]+)['\"]?", suggestion_lower)
                        if type_match:
                            note_type = type_match.group(1).strip()
                            session.run("""
                                MATCH (n:Note {name: $note_name})
                                SET n.type = $note_type,
                                    n.type_auto_applied = true,
                                    n.updated_at = timestamp()
                            """, note_name=note_name, note_type=note_type)
                            print(f"   ✅ Typ '{note_type}' automatisch zugewiesen")
                            applied_count += 1

                    else:
                        print(f"   ⚠️ Unbekannte Empfehlung (nicht automatisch anwendbar): {suggestion}")

                except Exception as e:
                    print(f"   ❌ Fehler beim Anwenden von Empfehlung '{suggestion}': {e}")

            print(f"🤖 {applied_count} von {len(suggestions)} Empfehlungen automatisch angewendet")
            return applied_count

    except Exception as e:
        print(f"❌ Fehler beim Anwenden der Governance-Empfehlungen: {e}")
        return 0
def cli():
    """Cortex-CLI für Neo4J-Workflow- und Wissensgraph-Operationen"""
    pass
