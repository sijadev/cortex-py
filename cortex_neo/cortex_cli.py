import click
from neo4j import GraphDatabase
import os
import json
import re
import requests

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")
CORTEX_AI_URL = os.environ.get("CORTEX_AI_URL", "http://127.0.0.1:8000")

# Helper for Neo4j driver/session
class Neo4jHelper:
    @staticmethod
    def get_driver():
        return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

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
def add_note(name):
    """Legt eine Note an (MERGE)."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run("MERGE (n:Note {name: $name})", name=name)
        print(f"Note '{name}' angelegt (oder bereits vorhanden).")
    except Exception as e:
        print(f"Fehler beim Anlegen der Note: {e}")

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
    """Zeigt eine Note mit Tags, Template und Links."""
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
                RETURN n, collect(DISTINCT tg) AS tags, collect(DISTINCT tpl) AS templates, collect(DISTINCT out) AS outgoing, collect(DISTINCT in) AS incoming
                """,
                name=name
            )
            rec = res.single()
            if not rec:
                print(f"Note '{name}' nicht gefunden.")
                return
            n = rec["n"]; tags = rec["tags"]; templates = rec["templates"]; outgoing = rec["outgoing"]; incoming = rec["incoming"]
            print(f"Note: {n['name']}")
            if templates:
                for t in templates:
                    if t: print(f"  Template: {t['name']}")
            if tags:
                print("  Tags:")
                for t in tags:
                    if t: print(f"    - {t['name']}")
            if outgoing:
                print("  Links →:")
                for o in outgoing:
                    if o: print(f"    - {o['name']}")
            if incoming:
                print("  Links ←:")
                for i in incoming:
                    if i: print(f"    - {i['name']}")
    except Exception as e:
        print(f"Fehler beim Anzeigen der Note: {e}")

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
    """Validiert Links mit Hilfe des Cortex-AI-Services (Proxy auf /ai/validate-links)."""
    try:
        import requests  # type: ignore
    except Exception as e:
        raise click.ClickException("'requests' nicht installiert. Bitte 'pip install requests' ausführen.")
    url = f"{CORTEX_AI_URL.rstrip('/')}/ai/validate-links"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise click.ClickException(f"AI-Validierung fehlgeschlagen: {e}")
    data = resp.json()
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("AI-Link-Validierung:")
        print(f"  Total Links: {data.get('total_links')}")
        print(f"  Invalid Links: {data.get('invalid_links')}")
        if data.get("suggestions"):
            print("  Vorschläge:")
            for s in data["suggestions"]:
                print(f"    - {s}")

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

if __name__ == '__main__':
    cli()
