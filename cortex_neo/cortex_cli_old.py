#!/usr/bin/env python3
"""
Cortex Neo4j CLI - Clean and Simple Interface
Erstellt: 2025-08-15
Zweck: Hauptinterface für Neo4j-Workflow- und Wissensgraph-Operationen
"""

import click
import os
import sys
from datetime import datetime
from neo4j import GraphDatabase
import logging

# Configuration
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")

# Enhanced logging configuration for better CLI output
def setup_logging(verbose=False):
    """Setup logging with proper CLI output handling"""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(message)s',  # Simple format for CLI
        stream=sys.stderr  # Send logs to stderr, leave stdout for CLI output
    )

logger = logging.getLogger(__name__)

# Force output flushing for immediate display
def echo_and_flush(message, err=False):
    """Enhanced echo with immediate output flushing"""
    click.echo(message, err=err)
    sys.stdout.flush()
    sys.stderr.flush()


class Neo4jHelper:
    """Helper class for Neo4j database operations"""
    _driver = None

    @classmethod
    def get_driver(cls):
        """Get or create Neo4j driver instance"""
        if cls._driver is None:
            try:
                cls._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
                echo_and_flush(f"🔗 Connected to Neo4j: {NEO4J_URI}")
            except Exception as e:
                echo_and_flush(f"❌ Neo4j connection failed: {e}", err=True)
                raise
        return cls._driver

    @classmethod
    def close(cls):
        """Close Neo4j driver connection"""
        if cls._driver:
            cls._driver.close()
            cls._driver = None
            echo_and_flush("🔌 Neo4j connection closed")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """Cortex-CLI für Neo4J-Workflow- und Wissensgraph-Operationen"""
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose

    # Setup logging based on verbosity
    setup_logging(verbose)

    if verbose:
        echo_and_flush("🚀 Cortex CLI gestartet (Verbose Mode)")
        echo_and_flush(f"   Neo4j URI: {NEO4J_URI}")
        echo_and_flush(f"   User: {NEO4J_USER}")


# === BASIC COMMANDS ===
@cli.command()
@click.pass_context
def list_workflows(ctx):
    """Zeigt alle Workflows in der Datenbank."""
    verbose = ctx.obj.get('verbose', False)

    try:
        echo_and_flush("📋 Lade Workflows...")

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("MATCH (w:Workflow) RETURN w ORDER BY w.name")
            workflows = [record["w"] for record in result]

            if workflows:
                echo_and_flush(f"📋 {len(workflows)} Workflows gefunden:")
                for workflow in workflows:
                    echo_and_flush(f"  - {workflow['name']}")
                    if verbose and workflow.get('description'):
                        echo_and_flush(f"    📝 {workflow['description']}")
            else:
                echo_and_flush("❌ Keine Workflows gefunden.")

    except Exception as e:
        echo_and_flush(f"❌ Fehler beim Abrufen der Workflows: {e}", err=True)
        if verbose:
            import traceback
            echo_and_flush(traceback.format_exc(), err=True)


@cli.command()
@click.pass_context
def list_notes(ctx):
    """Listet alle Notes."""
    verbose = ctx.obj.get('verbose', False)

    try:
        echo_and_flush("📝 Lade Notes...")

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("MATCH (n:Note) RETURN n ORDER BY n.name")
            notes = list(result)

            if notes:
                echo_and_flush(f"📝 {len(notes)} Notes gefunden:")
                for record in notes:
                    note = record["n"]
                    note_type = note.get('type', 'untyped')
                    description = note.get('description', '')
                    echo_and_flush(f"  - {note['name']} ({note_type})")
                    if description:
                        echo_and_flush(f"    📄 {description}")
            else:
                echo_and_flush("❌ Keine Notes gefunden.")

    except Exception as e:
        echo_and_flush(f"❌ Fehler beim Auflisten der Notes: {e}", err=True)
        if verbose:
            import traceback
            echo_and_flush(traceback.format_exc(), err=True)


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

        echo_and_flush(f"✅ Note '{name}' angelegt/aktualisiert.")
        if content:
            content_preview = content[:100] + "..." if len(content) > 100 else content
            echo_and_flush(f"   📄 Content: {content_preview}")
        if description:
            echo_and_flush(f"   📝 Beschreibung: {description}")
        if note_type:
            echo_and_flush(f"   🏷️ Typ: {note_type}")
        if url:
            echo_and_flush(f"   🔗 URL: {url}")

    except Exception as e:
        echo_and_flush(f"❌ Fehler beim Anlegen der Note: {e}", err=True)


@cli.command()
@click.argument('name')
def show_note(name):
    """Zeigt eine Note mit Content, Tags, Template und Links."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (n:Note {name: $name})
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(tag:Tag)
                OPTIONAL MATCH (n)-[:USES_TEMPLATE]->(template:Template)
                OPTIONAL MATCH (n)-[:LINKS_TO]->(linked:Note)
                OPTIONAL MATCH (incoming:Note)-[:LINKS_TO]->(n)
                RETURN n, 
                       collect(DISTINCT tag) AS tags, 
                       collect(DISTINCT template) AS templates, 
                       collect(DISTINCT linked) AS outgoing_links, 
                       collect(DISTINCT incoming) AS incoming_links
                """,
                name=name
            )

            record = result.single()
            if not record:
                echo_and_flush(f"❌ Note '{name}' nicht gefunden.")
                return

            note = record["n"]
            tags = [t for t in record["tags"] if t]
            templates = [t for t in record["templates"] if t]
            outgoing_links = [l for l in record["outgoing_links"] if l]
            incoming_links = [l for l in record["incoming_links"] if l]

            # Header mit Metadaten
            echo_and_flush(f"📝 Note: {note['name']}")
            if note.get('type'):
                echo_and_flush(f"   🏷️ Typ: {note['type']}")
            if note.get('description'):
                echo_and_flush(f"   📄 Beschreibung: {note['description']}")
            if note.get('url'):
                echo_and_flush(f"   🔗 URL: {note['url']}")
            if note.get('updated_at'):
                echo_and_flush(f"   🕒 Aktualisiert: {note['updated_at']}")

            # Content
            if note.get('content'):
                content = note['content']
                echo_and_flush("\n📄 Content:")
                echo_and_flush(content)

            # Tags
            if tags:
                echo_and_flush(f"\n🏷️ Tags ({len(tags)}):")
                for tag in tags:
                    echo_and_flush(f"  - {tag['name']}")

            # Templates
            if templates:
                echo_and_flush(f"\n🏗️ Templates ({len(templates)}):")
                for template in templates:
                    echo_and_flush(f"  - {template['name']}")

            # Links
            if outgoing_links:
                echo_and_flush(f"\n🔗 Ausgehende Links ({len(outgoing_links)}):")
                for link in outgoing_links:
                    echo_and_flush(f"  → {link['name']}")

            if incoming_links:
                echo_and_flush(f"\n🔙 Eingehende Links ({len(incoming_links)}):")
                for link in incoming_links:
                    echo_and_flush(f"  ← {link['name']}")

    except Exception as e:
        echo_and_flush(f"❌ Fehler beim Anzeigen der Note: {e}", err=True)


# === STATUS COMMANDS ===
@cli.command()
def cortex_status():
    """Zeigt umfassenden Cortex-System-Status"""
    try:
        echo_and_flush("🎯 CORTEX SYSTEM STATUS OVERVIEW")
        echo_and_flush("=" * 50)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Connection Test
            server_info = session.run("RETURN timestamp() as time").single()
            echo_and_flush(f"🔗 NEO4J CONNECTION: ✅ Connected")
            echo_and_flush(f"   Server Time: {server_info['time']}")

            # Data Statistics
            stats = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (w:Workflow)
                OPTIONAL MATCH (t:Tag)
                OPTIONAL MATCH ()-[r:LINKS_TO]->()
                RETURN count(DISTINCT n) as notes,
                       count(DISTINCT w) as workflows,
                       count(DISTINCT t) as tags,
                       count(r) as links
            """).single()

            echo_and_flush(f"\n📈 DATA STATISTICS:")
            echo_and_flush(f"   📝 Notes: {stats['notes']}")
            echo_and_flush(f"   🔄 Workflows: {stats['workflows']}")
            echo_and_flush(f"   🏷️ Tags: {stats['tags']}")
            echo_and_flush(f"   🔗 Links: {stats['links']}")

            echo_and_flush(f"\n🎯 OVERALL STATUS: 🟢 Operational")

    except Exception as e:
        echo_and_flush(f"❌ Status query failed: {e}", err=True)


@cli.command()
def smart_overview():
    """Smart Overview - Kombiniert mehrere Status-Abfragen"""
    try:
        echo_and_flush("🧠 SMART OVERVIEW - Intelligent System Summary")
        echo_and_flush("=" * 60)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Single optimized query
            result = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                OPTIONAL MATCH (w:Workflow)
                WITH count(DISTINCT n) as note_count,
                     count(DISTINCT t) as tag_count,
                     count(DISTINCT w) as workflow_count,
                     collect(DISTINCT n.type)[0..5] as sample_types
                RETURN note_count, tag_count, workflow_count, sample_types
            """).single()

            echo_and_flush(f"📊 QUICK STATS:")
            echo_and_flush(f"   📝 Notes: {result['note_count']}")
            echo_and_flush(f"   🏷️ Tags: {result['tag_count']}")
            echo_and_flush(f"   🔄 Workflows: {result['workflow_count']}")

            if result['sample_types']:
                types = [t for t in result['sample_types'] if t]
                if types:
                    echo_and_flush(f"   📋 Note Types: {', '.join(types[:3])}")

            echo_and_flush(f"\n✨ Smart Overview completed successfully")

    except Exception as e:
        echo_and_flush(f"❌ Smart Overview failed: {e}", err=True)


# === VALIDATION COMMANDS ===
@cli.command()
def validate_connection():
    """Validiert Neo4j-Verbindung"""
    try:
        echo_and_flush("🔍 Starting connection validation...")

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            test_result = session.run("RETURN 1 as test, timestamp() as time").single()
            echo_and_flush(f"✅ Neo4j connection successful")
            echo_and_flush(f"   🔗 URI: {NEO4J_URI}")
            echo_and_flush(f"   🕒 Server time: {test_result['time']}")
            echo_and_flush(f"   ✅ All validations successful")
            return True

    except Exception as e:
        echo_and_flush(f"❌ Validation failed: {e}", err=True)
        echo_and_flush("💡 Possible solutions:")
        echo_and_flush("   - Check Neo4j container: docker ps | grep neo4j")
        echo_and_flush("   - Start Neo4j: cd cortex_neo && docker-compose up -d")
        echo_and_flush("   - Check environment variables")
        return False


# === TAG MANAGEMENT COMMANDS ===
@cli.command()
def list_tags():
    """Zeigt alle Tags mit deren Kategorien und Beschreibungen."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)
                OPTIONAL MATCH (n:Note)-[:TAGGED_WITH]->(t)
                RETURN t.name as name, 
                       t.description as description,
                       t.category as category,
                       count(n) as usage_count
                ORDER BY t.category, t.name
            """)

            tags_by_category = {}
            for record in result:
                category = record['category'] or 'uncategorized'
                if category not in tags_by_category:
                    tags_by_category[category] = []
                tags_by_category[category].append({
                    'name': record['name'],
                    'description': record['description'] or 'No description',
                    'usage_count': record['usage_count']
                })

            if tags_by_category:
                echo_and_flush(f"🏷️  Tags Overview ({sum(len(tags) for tags in tags_by_category.values())} total):")
                echo_and_flush("=" * 50)

                for category, tags in tags_by_category.items():
                    echo_and_flush(f"\n📂 {category.upper()} ({len(tags)} tags):")
                    for tag in tags:
                        echo_and_flush(f"   • {tag['name']} (used {tag['usage_count']}x)")
                        echo_and_flush(f"     ├─ {tag['description']}")
            else:
                echo_and_flush("❌ Keine Tags gefunden.")

    except Exception as e:
        echo_and_flush(f"❌ Fehler beim Auflisten der Tags: {e}", err=True)


@cli.command()
@click.argument('note_name')
@click.argument('tag_name')
def add_tag(note_name, tag_name):
    """Fügt einem Note einen Tag hinzu."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (n:Note {name: $note_name})
                MERGE (t:Tag {name: $tag_name})
                MERGE (n)-[:TAGGED_WITH]->(t)
                RETURN n.name as note, t.name as tag
            """, note_name=note_name, tag_name=tag_name)

            record = result.single()
            if record:
                echo_and_flush(f"✅ Tag '{tag_name}' zu Note '{note_name}' hinzugefügt.")
            else:
                echo_and_flush(f"❌ Note '{note_name}' nicht gefunden.")

    except Exception as e:
        echo_and_flush(f"❌ Fehler beim Hinzufügen des Tags: {e}", err=True)


@cli.command()
@click.argument('tag_name')
def show_tag(tag_name):
    """Zeigt Details eines Tags und alle zugeordneten Notes."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (t:Tag {name: $tag_name})
                OPTIONAL MATCH (n:Note)-[:TAGGED_WITH]->(t)
                RETURN t, collect(n) as notes
            """, tag_name=tag_name)

            record = result.single()
            if not record:
                echo_and_flush(f"❌ Tag '{tag_name}' nicht gefunden.")
                return

            tag = record['t']
            notes = [n for n in record['notes'] if n]

            echo_and_flush(f"🏷️  Tag: {tag['name']}")
            if tag.get('description'):
                echo_and_flush(f"   📝 Beschreibung: {tag['description']}")
            if tag.get('category'):
                echo_and_flush(f"   📂 Kategorie: {tag['category']}")

            if notes:
                echo_and_flush(f"\n📝 Zugeordnete Notes ({len(notes)}):")
                for note in notes:
                    note_type = f" ({note.get('type', 'untyped')})" if note.get('type') else ""
                    echo_and_flush(f"   • {note['name']}{note_type}")
            else:
                echo_and_flush("\n❌ Keine Notes mit diesem Tag gefunden.")

    except Exception as e:
        echo_and_flush(f"❌ Fehler beim Anzeigen des Tags: {e}", err=True)


# === GOVERNANCE COMMANDS ===
@cli.command()
@click.argument('name')
@click.option('--content', help='Textinhalt der Note')
@click.option('--description', help='Kurze Beschreibung der Note')
@click.option('--type', 'note_type', help='Typ/Kategorie der Note')
@click.option('--project-type', help='Projekt-Typ für intelligente Template-Auswahl')
def add_note_smart(name, content, description, note_type, project_type):
    """Erstellt Note mit intelligenter Governance-Unterstützung (Auto-Tags, Templates)."""
    try:
        # Import here to avoid circular imports
        from src.governance.data_governance import DataGovernanceEngine

        echo_and_flush("🧠 Intelligente Note-Erstellung mit Governance...")

        # Initialize governance engine
        governance = DataGovernanceEngine()

        # Validate and get suggestions
        if project_type:
            result = governance.validate_note_creation_with_context(
                name=name,
                content=content or "",
                description=description or "",
                note_type=note_type or "",
                project_type=project_type
            )
        else:
            result = governance.validate_note_creation(
                name=name,
                content=content or "",
                description=description or "",
                note_type=note_type or ""
            )

        # Show validation results
        if result.errors:
            echo_and_flush("❌ Validierungsfehler:")
            for error in result.errors:
                echo_and_flush(f"   • {error}")
            return

        if result.warnings:
            echo_and_flush("⚠️  Warnungen:")
            for warning in result.warnings:
                echo_and_flush(f"   • {warning}")

        if result.suggestions:
            echo_and_flush("💡 Empfehlungen:")
            for suggestion in result.suggestions:
                echo_and_flush(f"   • {suggestion}")

        # Create the note if validation passes
        if result.passed:
            driver = Neo4jHelper.get_driver()
            with driver.session() as session:
                # Create note
                session.run("""
                    MERGE (n:Note {name: $name})
                    SET n.content = $content,
                        n.description = $description,
                        n.type = $note_type,
                        n.created_with_governance = true,
                        n.updated_at = timestamp()
                """, name=name, content=content or "", description=description or "", note_type=note_type or "")

                # Auto-assign suggested tags if any
                for suggestion in result.suggestions:
                    if "Empfohlene Tags:" in suggestion:
                        tags = suggestion.replace("Empfohlene Tags: ", "").split(", ")
                        for tag_name in tags:
                            tag_name = tag_name.strip()
                            session.run("""
                                MATCH (n:Note {name: $name})
                                MERGE (t:Tag {name: $tag_name})
                                MERGE (n)-[:TAGGED_WITH]->(t)
                            """, name=name, tag_name=tag_name)
                            echo_and_flush(f"   🏷️  Auto-Tag hinzugefügt: {tag_name}")

            echo_and_flush(f"✅ Smart Note '{name}' erfolgreich erstellt!")

    except Exception as e:
        echo_and_flush(f"❌ Fehler bei der intelligenten Note-Erstellung: {e}", err=True)


@cli.command()
def create_performance_tags():
    """Erstellt die Performance-Tags für das System."""
    try:
        echo_and_flush("🚀 Erstelle Performance-Tags...")

        performance_tags = [
            {
                "name": "performance-metrics",
                "description": "Tag for notes related to performance measurements and metrics",
                "category": "performance"
            },
            {
                "name": "system-optimization",
                "description": "Tag for notes about system optimization techniques and improvements",
                "category": "performance"
            },
            {
                "name": "command-tracking",
                "description": "Tag for notes related to command execution tracking and monitoring",
                "category": "performance"
            }
        ]

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            for tag_info in performance_tags:
                session.run("""
                    MERGE (t:Tag {name: $name})
                    SET t.description = $description,
                        t.category = $category,
                        t.created_at = datetime(),
                        t.created_by = 'cli_command'
                """, **tag_info)

                echo_and_flush(f"✅ Performance Tag erstellt: '{tag_info['name']}'")

        echo_and_flush("🎯 Alle Performance-Tags erfolgreich erstellt!")

    except Exception as e:
        echo_and_flush(f"❌ Fehler beim Erstellen der Performance-Tags: {e}", err=True)


# === SEARCH AND FILTER COMMANDS ===
@cli.command()
@click.argument('query')
@click.option('--tag', help='Filtere nach Tag')
@click.option('--type', 'note_type', help='Filtere nach Note-Typ')
def search_notes(query, tag, note_type):
    """Durchsucht Notes nach Inhalt, Namen oder Eigenschaften."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            cypher_query = """
                MATCH (n:Note)
                WHERE (toLower(n.name) CONTAINS toLower($query) 
                       OR toLower(n.content) CONTAINS toLower($query)
                       OR toLower(n.description) CONTAINS toLower($query))
            """
            params = {"query": query}

            # Add tag filter
            if tag:
                cypher_query += """
                    AND EXISTS {
                        MATCH (n)-[:TAGGED_WITH]->(t:Tag {name: $tag})
                    }
                """
                params["tag"] = tag

            # Add type filter
            if note_type:
                cypher_query += " AND n.type = $note_type"
                params["note_type"] = note_type

            cypher_query += """
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                RETURN n, collect(t.name) as tags
                ORDER BY n.name
                LIMIT 20
            """

            result = session.run(cypher_query, params)
            notes = list(result)

            if notes:
                echo_and_flush(f"🔍 Suchergebnisse für '{query}' ({len(notes)} gefunden):")
                echo_and_flush("=" * 50)

                for record in notes:
                    note = record['n']
                    tags = [t for t in record['tags'] if t]

                    echo_and_flush(f"\n📝 {note['name']}")
                    if note.get('type'):
                        echo_and_flush(f"   🏷️  Typ: {note['type']}")
                    if note.get('description'):
                        echo_and_flush(f"   📄 {note['description']}")
                    if tags:
                        echo_and_flush(f"   🏷️  Tags: {', '.join(tags[:3])}")
            else:
                echo_and_flush(f"❌ Keine Notes gefunden für '{query}'")

    except Exception as e:
        echo_and_flush(f"❌ Fehler bei der Suche: {e}", err=True)


# === LINK MANAGEMENT COMMANDS ===
@cli.command()
@click.argument('from_note')
@click.argument('to_note')
def link_notes(from_note, to_note):
    """Erstellt einen Link zwischen zwei Notes."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (from:Note {name: $from_note}), (to:Note {name: $to_note})
                MERGE (from)-[:LINKS_TO]->(to)
                RETURN from.name as from_name, to.name as to_name
            """, from_note=from_note, to_note=to_note)

            record = result.single()
            if record:
                echo_and_flush(f"✅ Link erstellt: '{from_note}' → '{to_note}'")
            else:
                echo_and_flush(f"❌ Eine oder beide Notes nicht gefunden.")

    except Exception as e:
        echo_and_flush(f"❌ Fehler beim Erstellen des Links: {e}", err=True)


@cli.command()
def show_network():
    """Zeigt das Netzwerk aller Notes und deren Verbindungen."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (n)-[:LINKS_TO]->(linked:Note)
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                RETURN n.name as note,
                       n.type as type,
                       collect(DISTINCT linked.name) as links,
                       collect(DISTINCT t.name) as tags
                ORDER BY size(links) DESC, n.name
                LIMIT 20
            """)

            echo_and_flush("🌐 Notes-Netzwerk (Top 20 nach Verlinkung):")
            echo_and_flush("=" * 50)

            for record in result:
                note = record['note']
                note_type = record['type'] or 'untyped'
                links = [l for l in record['links'] if l]
                tags = [t for t in record['tags'] if t]

                echo_and_flush(f"\n📝 {note} ({note_type})")
                if links:
                    echo_and_flush(f"   🔗 Links zu: {', '.join(links[:3])}")
                if tags:
                    echo_and_flush(f"   🏷️  Tags: {', '.join(tags[:3])}")

    except Exception as e:
        echo_and_flush(f"❌ Fehler beim Anzeigen des Netzwerks: {e}", err=True)


if __name__ == '__main__':
    try:
        cli()
    finally:
        Neo4jHelper.close()
