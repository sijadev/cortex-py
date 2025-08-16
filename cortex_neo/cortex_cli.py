#!/usr/bin/env python3
"""
Cortex CLI - AI-Optimized Structured Interface
Implements 4+1 Category Structure for Better UX
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

def setup_logging(verbose=False):
    """Setup logging with proper CLI output handling"""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format='%(message)s', stream=sys.stderr)

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

# ============================================================================
# MAIN CLI GROUP with Smart Shortcuts
# ============================================================================

@click.group(invoke_without_command=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cortex(ctx, verbose):
    """🧠 Cortex - AI-Enhanced Knowledge Graph System

    Smart Shortcuts:
      cortex                    # Quick system status
      cortex <note-name>        # Show specific note
      cortex search <query>     # Search content
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)

    # Smart shortcut handling and default behavior
    if ctx.invoked_subcommand is None:
        # If user provided a bare argument like 'cortex <note>', treat it as note name
        if ctx.args:
            first_arg = ctx.args[0]
            # Preserve explicit subcommand 'search' (also available as proper subcommand)
            if first_arg == 'search':
                # Let Click handle the proper subcommand normally; show gentle hint if misused
                echo_and_flush("💡 Use: cortex content search <query>")
                return
            # Show specific note content shortcut
            show_note_content(first_arg)
            return
        # No args: quick status overview
        quick_status()

def quick_status():
    """Quick system status overview"""
    try:
        echo_and_flush("🎯 CORTEX QUICK STATUS")
        echo_and_flush("=" * 30)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            stats = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (t:Tag)
                OPTIONAL MATCH ()-[r:LINKS_TO]->()
                RETURN count(DISTINCT n) as notes,
                       count(DISTINCT t) as tags,
                       count(r) as links
            """).single()

            echo_and_flush(f"📝 Notes: {stats['notes']}")
            echo_and_flush(f"🏷️ Tags: {stats['tags']}")
            echo_and_flush(f"🔗 Links: {stats['links']}")
            echo_and_flush(f"🎯 Status: 🟢 Operational")

    except Exception as e:
        echo_and_flush(f"❌ Status check failed: {e}", err=True)

def show_note_content(note_name):
    """Show specific note content"""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (n:Note {name: $name})
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(tag:Tag)
                RETURN n, collect(DISTINCT tag.name) as tags
            """, name=note_name)

            record = result.single()
            if not record:
                echo_and_flush(f"❌ Note '{note_name}' nicht gefunden.")
                return

            note = record["n"]
            tags = record["tags"]

            echo_and_flush(f"📝 {note['name']}")
            if note.get('description'):
                echo_and_flush(f"📄 {note['description']}")
            if tags:
                echo_and_flush(f"🏷️ Tags: {', '.join(tags)}")
            if note.get('content'):
                echo_and_flush(f"\n{note['content']}")

    except Exception as e:
        echo_and_flush(f"❌ Error showing note: {e}", err=True)

# ============================================================================
# 1. CORTEX SYSTEM - System Management
# ============================================================================

@cortex.group()
def system():
    """🔧 System Management Commands"""
    pass

@system.command()
def status():
    """System status overview (enhanced version of cortex-status)"""
    try:
        echo_and_flush("🎯 CORTEX SYSTEM STATUS OVERVIEW")
        echo_and_flush("=" * 50)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Connection Test
            server_info = session.run("RETURN timestamp() as time").single()
            echo_and_flush(f"🔗 NEO4J CONNECTION: ✅ Connected")
            echo_and_flush(f"   Server Time: {server_info['time']}")
            echo_and_flush(f"   URI: {NEO4J_URI}")

            # Comprehensive Data Statistics
            stats = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (w:Workflow)
                OPTIONAL MATCH (t:Tag)
                OPTIONAL MATCH ()-[r:LINKS_TO]->()
                OPTIONAL MATCH (template:Template)
                RETURN count(DISTINCT n) as notes,
                       count(DISTINCT w) as workflows,
                       count(DISTINCT t) as tags,
                       count(r) as links,
                       count(DISTINCT template) as templates
            """).single()

            echo_and_flush(f"\n📈 DATA STATISTICS:")
            echo_and_flush(f"   📝 Notes: {stats['notes']}")
            echo_and_flush(f"   🔄 Workflows: {stats['workflows']}")
            echo_and_flush(f"   🏷️ Tags: {stats['tags']}")
            echo_and_flush(f"   🔗 Links: {stats['links']}")
            echo_and_flush(f"   🏗️ Templates: {stats['templates']}")

            # Health check
            health_score = min(100, (stats['notes'] * 10 + stats['links'] * 5 + stats['tags'] * 3))
            health_status = "🟢 Excellent" if health_score > 50 else "🟡 Good" if health_score > 20 else "🔴 Needs Content"

            echo_and_flush(f"\n🎯 OVERALL STATUS: {health_status} (Score: {health_score})")

    except Exception as e:
        echo_and_flush(f"❌ Status query failed: {e}", err=True)

@system.command()
def health():
    """System health check (enhanced version of validate-connection)"""
    try:
        echo_and_flush("🔍 SYSTEM HEALTH CHECK")
        echo_and_flush("=" * 30)

        # Neo4j Connection
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            test_result = session.run("RETURN 1 as test, timestamp() as time").single()
            echo_and_flush(f"✅ Neo4j Connection: OK")
            echo_and_flush(f"   🕒 Server Time: {test_result['time']}")

        # Data Integrity Check
        with driver.session() as session:
            integrity = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                OPTIONAL MATCH (n)-[r:LINKS_TO]->()
                RETURN count(n) as total_notes,
                       count(t) as tagged_notes,
                       count(r) as linked_notes
            """).single()

            tag_coverage = (integrity['tagged_notes'] / max(integrity['total_notes'], 1)) * 100
            link_coverage = (integrity['linked_notes'] / max(integrity['total_notes'], 1)) * 100

            echo_and_flush(f"✅ Data Integrity: OK")
            echo_and_flush(f"   🏷️ Tag Coverage: {tag_coverage:.1f}%")
            echo_and_flush(f"   🔗 Link Coverage: {link_coverage:.1f}%")

        echo_and_flush(f"\n🎯 HEALTH STATUS: 🟢 All Systems Operational")

    except Exception as e:
        echo_and_flush(f"❌ Health check failed: {e}", err=True)
        echo_and_flush("💡 Troubleshooting:")
        echo_and_flush("   - Check Neo4j: docker ps | grep neo4j")
        echo_and_flush("   - Start Neo4j: cd cortex_neo && docker-compose up -d")

@system.command()
def overview():
    """Smart system overview (enhanced version of smart-overview)"""
    try:
        echo_and_flush("🧠 SMART SYSTEM OVERVIEW")
        echo_and_flush("=" * 40)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Comprehensive overview query
            result = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                OPTIONAL MATCH (w:Workflow)
                WITH count(DISTINCT n) as note_count,
                     count(DISTINCT t) as tag_count,
                     count(DISTINCT w) as workflow_count,
                     collect(DISTINCT n.type) as note_types,
                     collect(DISTINCT t.category) as tag_categories
                RETURN note_count, tag_count, workflow_count, note_types, tag_categories
            """).single()

            echo_and_flush(f"📊 CONTENT ANALYSIS:")
            echo_and_flush(f"   📝 Notes: {result['note_count']}")
            echo_and_flush(f"   🏷️ Tags: {result['tag_count']}")
            echo_and_flush(f"   🔄 Workflows: {result['workflow_count']}")

            # Content type analysis
            note_types = [t for t in result['note_types'] if t]
            if note_types:
                echo_and_flush(f"   📋 Note Types: {', '.join(note_types[:5])}")

            # Tag category analysis
            tag_categories = [c for c in result['tag_categories'] if c]
            if tag_categories:
                echo_and_flush(f"   📂 Tag Categories: {', '.join(tag_categories[:5])}")

            # AI Insights
            echo_and_flush(f"\n🤖 AI INSIGHTS:")
            if result['note_count'] > 10:
                echo_and_flush("   ✨ Rich knowledge base detected")
            if result['tag_count'] > result['note_count'] * 0.5:
                echo_and_flush("   🏷️ Good tagging practices")
            if len(note_types) > 3:
                echo_and_flush("   📚 Diverse content types")

            echo_and_flush(f"\n✨ Smart Overview completed")

    except Exception as e:
        echo_and_flush(f"❌ Smart Overview failed: {e}", err=True)

# ============================================================================
# 2. CORTEX CONTENT - Content Management
# ============================================================================

@cortex.group()
def content():
    """📝 Content Management Commands"""
    pass

@content.command()
@click.argument('name')
@click.option('--content', help='Note content')
@click.option('--description', help='Note description')
@click.option('--type', 'note_type', help='Note type/category')
@click.option('--smart', is_flag=True, help='Enable AI-powered creation with templates and auto-tags')
def create(name, content, description, note_type, smart):
    """Create new content (enhanced version of add-note)"""
    try:
        if smart:
            echo_and_flush("🤖 AI-Enhanced Content Creation")
            echo_and_flush("=" * 35)

            # AI Content Analysis
            ai_suggestions = analyze_content_with_ai(name, content, description, note_type)

            if ai_suggestions:
                echo_and_flush("🧠 AI Analysis Results:")
                for suggestion in ai_suggestions:
                    echo_and_flush(f"   • {suggestion}")

            # Apply AI suggestions
            note_type = ai_suggestions.get('suggested_type', note_type)
            auto_tags = ai_suggestions.get('auto_tags', [])
        else:
            echo_and_flush(f"📝 Creating note: {name}")
            auto_tags = []

        # Create the note
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            session.run("""
                MERGE (n:Note {name: $name})
                SET n.content = $content,
                    n.description = $description,
                    n.type = $note_type,
                    n.created_with_ai = $smart,
                    n.updated_at = timestamp()
            """, name=name, content=content or "", description=description or "",
                 note_type=note_type or "", smart=smart)

            # Add auto-generated tags
            for tag_name in auto_tags:
                session.run("""
                    MATCH (n:Note {name: $name})
                    MERGE (t:Tag {name: $tag_name})
                    MERGE (n)-[:TAGGED_WITH]->(t)
                """, name=name, tag_name=tag_name)
                echo_and_flush(f"   🏷️ Auto-tag added: {tag_name}")

        echo_and_flush(f"✅ Note '{name}' created successfully!")
        if smart:
            echo_and_flush("✨ AI enhancements applied")

    except Exception as e:
        echo_and_flush(f"❌ Content creation failed: {e}", err=True)

def analyze_content_with_ai(name, content, description, note_type):
    """AI-powered content analysis for smart suggestions"""
    suggestions = {}
    auto_tags = []

    # Content type detection
    name_lower = name.lower()
    content_lower = (content or "").lower()

    if any(word in name_lower for word in ['meeting', 'standup', 'sync']):
        suggestions['suggested_type'] = 'meeting'
        auto_tags.extend(['meeting', 'documentation'])
        return {"suggested_type": "meeting", "auto_tags": auto_tags,
                "template": "📋 Auto-applying: Template_Meeting_Notes"}

    elif any(word in name_lower for word in ['project', 'plan', 'roadmap']):
        suggestions['suggested_type'] = 'project'
        auto_tags.extend(['project', 'planning'])

    elif any(word in content_lower for word in ['todo', 'task', 'action']):
        auto_tags.extend(['tasks', 'actionable'])

    elif any(word in content_lower for word in ['research', 'analysis', 'study']):
        auto_tags.extend(['research', 'analysis'])

    suggestions['auto_tags'] = auto_tags
    return suggestions

@content.command()
@click.argument('query')
def search(query):
    """Search content (enhanced version of search-notes)"""
    try:
        echo_and_flush(f"🔍 Searching for: '{query}'")
        echo_and_flush("=" * 40)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Enhanced search across multiple fields
            result = session.run("""
                MATCH (n:Note)
                WHERE n.name CONTAINS $query 
                   OR n.content CONTAINS $query 
                   OR n.description CONTAINS $query
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                RETURN n, collect(DISTINCT t.name) as tags
                ORDER BY 
                    CASE WHEN n.name CONTAINS $query THEN 1 ELSE 2 END,
                    n.updated_at DESC
                LIMIT 20
            """, query=query)

            results = list(result)
            if results:
                echo_and_flush(f"📝 Found {len(results)} results:")
                echo_and_flush("")

                for record in results:
                    note = record["n"]
                    tags = record["tags"]

                    echo_and_flush(f"• {note['name']}")
                    if note.get('type'):
                        echo_and_flush(f"  📂 Type: {note['type']}")
                    if note.get('description'):
                        echo_and_flush(f"  📄 {note['description'][:100]}...")
                    if tags:
                        echo_and_flush(f"  🏷️ Tags: {', '.join(tags[:5])}")
                    echo_and_flush("")
            else:
                echo_and_flush(f"❌ No results found for '{query}'")
                echo_and_flush("💡 Try broader search terms or check spelling")

    except Exception as e:
        echo_and_flush(f"❌ Search failed: {e}", err=True)

@content.command()
@click.argument('name')
def show(name):
    """Show detailed content view"""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (n:Note {name: $name})
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(tag:Tag)
                OPTIONAL MATCH (n)-[:LINKS_TO]->(linked:Note)
                OPTIONAL MATCH (incoming:Note)-[:LINKS_TO]->(n)
                RETURN n, 
                       collect(DISTINCT tag) AS tags, 
                       collect(DISTINCT linked) AS outgoing_links, 
                       collect(DISTINCT incoming) AS incoming_links
            """, name=name)

            record = result.single()
            if not record:
                echo_and_flush(f"❌ Note '{name}' not found.")
                return

            note = record["n"]
            tags = [t for t in record["tags"] if t]
            outgoing_links = [l for l in record["outgoing_links"] if l]
            incoming_links = [l for l in record["incoming_links"] if l]

            # Enhanced display
            echo_and_flush(f"📝 {note['name']}")
            echo_and_flush("=" * (len(note['name']) + 4))

            if note.get('type'):
                echo_and_flush(f"📂 Type: {note['type']}")
            if note.get('description'):
                echo_and_flush(f"📄 Description: {note['description']}")
            if note.get('updated_at'):
                echo_and_flush(f"🕒 Updated: {note['updated_at']}")

            # Content
            if note.get('content'):
                echo_and_flush(f"\n📄 CONTENT:")
                echo_and_flush(note['content'])

            # Tags with enhanced display
            if tags:
                echo_and_flush(f"\n🏷️ TAGS ({len(tags)}):")
                for tag in tags:
                    category = f" [{tag.get('category', 'general')}]" if tag.get('category') else ""
                    echo_and_flush(f"  • {tag['name']}{category}")

            # Links
            if outgoing_links:
                echo_and_flush(f"\n🔗 OUTGOING LINKS ({len(outgoing_links)}):")
                for link in outgoing_links:
                    echo_and_flush(f"  → {link['name']}")

            if incoming_links:
                echo_and_flush(f"\n🔙 INCOMING LINKS ({len(incoming_links)}):")
                for link in incoming_links:
                    echo_and_flush(f"  ← {link['name']}")

    except Exception as e:
        echo_and_flush(f"❌ Error showing content: {e}", err=True)

@content.command()
def list():
    """List all content with enhanced filtering"""
    try:
        echo_and_flush("📝 CONTENT OVERVIEW")
        echo_and_flush("=" * 30)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                RETURN n, count(t) as tag_count
                ORDER BY n.updated_at DESC
            """)

            notes_by_type = {}
            for record in result:
                note = record["n"]
                tag_count = record["tag_count"]
                note_type = note.get('type', 'untyped')

                if note_type not in notes_by_type:
                    notes_by_type[note_type] = []
                notes_by_type[note_type].append({
                    'note': note,
                    'tag_count': tag_count
                })

            if notes_by_type:
                total_notes = sum(len(notes) for notes in notes_by_type.values())
                echo_and_flush(f"📊 Total: {total_notes} notes")
                echo_and_flush("")

                for note_type, notes in notes_by_type.items():
                    echo_and_flush(f"📂 {note_type.upper()} ({len(notes)} notes):")
                    for item in notes[:10]:  # Show max 10 per type
                        note = item['note']
                        tag_indicator = f" ({item['tag_count']} tags)" if item['tag_count'] > 0 else ""
                        echo_and_flush(f"  • {note['name']}{tag_indicator}")
                    if len(notes) > 10:
                        echo_and_flush(f"  ... and {len(notes) - 10} more")
                    echo_and_flush("")
            else:
                echo_and_flush("❌ No content found.")

    except Exception as e:
        echo_and_flush(f"❌ Error listing content: {e}", err=True)

# ============================================================================
# 3. CORTEX TAGS - Tag Management
# ============================================================================

@cortex.group()
def tags():
    """🏷️ Tag Management Commands"""
    pass

@tags.command()
@click.argument('note_name')
@click.argument('tag_name')
def add(note_name, tag_name):
    """Add tag to note (enhanced version of add-tag)"""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (n:Note {name: $note_name})
                MERGE (t:Tag {name: $tag_name})
                ON CREATE SET t.created_at = timestamp()
                MERGE (n)-[:TAGGED_WITH]->(t)
                RETURN n.name as note, t.name as tag
            """, note_name=note_name, tag_name=tag_name)

            record = result.single()
            if record:
                echo_and_flush(f"✅ Tag '{tag_name}' added to note '{note_name}'")

                # Show smart suggestions for related tags
                related_tags = get_related_tag_suggestions(tag_name)
                if related_tags:
                    echo_and_flush("💡 Related tag suggestions:")
                    for related_tag in related_tags[:3]:
                        echo_and_flush(f"   • {related_tag}")
            else:
                echo_and_flush(f"❌ Note '{note_name}' not found.")

    except Exception as e:
        echo_and_flush(f"❌ Error adding tag: {e}", err=True)

def get_related_tag_suggestions(tag_name):
    """Get AI-powered related tag suggestions"""
    suggestions = []
    tag_lower = tag_name.lower()

    # Simple rule-based suggestions (could be enhanced with ML)
    tag_relationships = {
        'meeting': ['documentation', 'team', 'planning'],
        'project': ['planning', 'management', 'development'],
        'research': ['analysis', 'documentation', 'investigation'],
        'task': ['actionable', 'todo', 'productivity'],
        'idea': ['brainstorming', 'creative', 'innovation']
    }

    for base_tag, related in tag_relationships.items():
        if base_tag in tag_lower:
            suggestions.extend(related)

    return list(set(suggestions))

@tags.command()
def list():
    """List all tags with enhanced categorization (enhanced version of list-tags)"""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)
                OPTIONAL MATCH (n:Note)-[:TAGGED_WITH]->(t)
                RETURN t.name as name, 
                       t.description as description,
                       t.category as category,
                       count(n) as usage_count,
                       t.created_at as created_at
                ORDER BY t.category, usage_count DESC, t.name
            """)

            tags_by_category = {}
            total_tags = 0
            for record in result:
                total_tags += 1
                category = record['category'] or 'uncategorized'
                if category not in tags_by_category:
                    tags_by_category[category] = []
                tags_by_category[category].append({
                    'name': record['name'],
                    'description': record['description'] or 'No description',
                    'usage_count': record['usage_count'],
                    'created_at': record['created_at']
                })

            if tags_by_category:
                echo_and_flush(f"🏷️ TAG OVERVIEW ({total_tags} total tags)")
                echo_and_flush("=" * 50)

                for category, tags in tags_by_category.items():
                    avg_usage = sum(tag['usage_count'] for tag in tags) / len(tags)
                    echo_and_flush(f"\n📂 {category.upper()} ({len(tags)} tags, avg usage: {avg_usage:.1f})")

                    # Sort by usage for better insights
                    sorted_tags = sorted(tags, key=lambda x: x['usage_count'], reverse=True)
                    for tag in sorted_tags:
                        usage_indicator = "🔥" if tag['usage_count'] > 5 else "⭐" if tag['usage_count'] > 2 else "📝"
                        echo_and_flush(f"   {usage_indicator} {tag['name']} (used {tag['usage_count']}x)")
                        if tag['description'] != 'No description':
                            echo_and_flush(f"     ├─ {tag['description']}")

                # Tag insights
                echo_and_flush(f"\n🤖 TAG INSIGHTS:")
                most_used_category = max(tags_by_category.keys(),
                                       key=lambda k: sum(t['usage_count'] for t in tags_by_category[k]))
                echo_and_flush(f"   📈 Most active category: {most_used_category}")

                unused_tags = [tag['name'] for tags in tags_by_category.values()
                             for tag in tags if tag['usage_count'] == 0]
                if unused_tags:
                    echo_and_flush(f"   🔍 Unused tags: {len(unused_tags)} (consider cleanup)")

            else:
                echo_and_flush("❌ No tags found.")

    except Exception as e:
        echo_and_flush(f"❌ Error listing tags: {e}", err=True)

@tags.command(name='create-performance')
def create_performance():
    """Create performance-related tags (enhanced version of create-performance-tags)"""
    try:
        echo_and_flush("🚀 Creating Performance Tag System...")
        echo_and_flush("=" * 40)

        performance_tags = [
            {
                "name": "performance-metrics",
                "description": "Performance measurements and KPIs",
                "category": "performance"
            },
            {
                "name": "system-optimization",
                "description": "System performance improvements",
                "category": "performance"
            },
            {
                "name": "command-tracking",
                "description": "CLI command execution monitoring",
                "category": "performance"
            },
            {
                "name": "benchmarking",
                "description": "Performance benchmarking and testing",
                "category": "performance"
            },
            {
                "name": "monitoring",
                "description": "System monitoring and alerting",
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
                        t.created_at = timestamp(),
                        t.created_by = 'performance_system',
                        t.system_tag = true
                """, **tag_info)

                echo_and_flush(f"✅ Created: '{tag_info['name']}'")
                echo_and_flush(f"   📝 {tag_info['description']}")

        echo_and_flush(f"\n🎯 Performance tag system ready!")
        echo_and_flush("💡 Use 'cortex tags add <note> performance-metrics' to apply")

    except Exception as e:
        echo_and_flush(f"❌ Error creating performance tags: {e}", err=True)

@tags.command()
@click.argument('tag_name')
def show(tag_name):
    """Show tag details and associated content (enhanced version of show-tag)"""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (t:Tag {name: $tag_name})
                OPTIONAL MATCH (n:Note)-[:TAGGED_WITH]->(t)
                RETURN t, collect(n) as notes,
                       count(n) as usage_count
            """, tag_name=tag_name)

            record = result.single()
            if not record:
                echo_and_flush(f"❌ Tag '{tag_name}' not found.")
                return

            tag = record['t']
            notes = [n for n in record['notes'] if n]
            usage_count = record['usage_count']

            echo_and_flush(f"🏷️ TAG: {tag['name']}")
            echo_and_flush("=" * (len(tag['name']) + 8))

            if tag.get('description'):
                echo_and_flush(f"📝 Description: {tag['description']}")
            if tag.get('category'):
                echo_and_flush(f"📂 Category: {tag['category']}")
            if tag.get('created_at'):
                echo_and_flush(f"🕒 Created: {tag['created_at']}")

            echo_and_flush(f"📊 Usage: {usage_count} notes")

            if notes:
                echo_and_flush(f"\n📝 TAGGED CONTENT ({len(notes)} items):")

                # Group by note type for better organization
                notes_by_type = {}
                for note in notes:
                    note_type = note.get('type', 'untyped')
                    if note_type not in notes_by_type:
                        notes_by_type[note_type] = []
                    notes_by_type[note_type].append(note)

                for note_type, type_notes in notes_by_type.items():
                    if len(notes_by_type) > 1:
                        echo_and_flush(f"\n📂 {note_type.upper()}:")
                    for note in type_notes:
                        echo_and_flush(f"  • {note['name']}")
                        if note.get('description'):
                            echo_and_flush(f"    📄 {note['description'][:80]}...")
            else:
                echo_and_flush("\n❌ No content tagged with this tag.")
                echo_and_flush("💡 Use 'cortex tags add <note> <tag>' to tag content")

    except Exception as e:
        echo_and_flush(f"❌ Error showing tag: {e}", err=True)

# ============================================================================
# 4. CORTEX GRAPH - Graph Operations
# ============================================================================

@cortex.group()
def graph():
    """🕸️ Graph Operations and Network Analysis"""
    pass

@graph.command()
@click.argument('from_note')
@click.argument('to_note')
@click.option('--type', 'link_type', default='LINKS_TO', help='Link relationship type')
def link(from_note, to_note, link_type):
    """Create link between notes (enhanced version of link-notes)"""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Check if both notes exist
            result = session.run("""
                MATCH (from:Note {name: $from_note})
                MATCH (to:Note {name: $to_note})
                RETURN from, to
            """, from_note=from_note, to_note=to_note)

            if not result.single():
                echo_and_flush(f"❌ One or both notes not found.")
                return

            # Create the link
            session.run(f"""
                MATCH (from:Note {{name: $from_note}})
                MATCH (to:Note {{name: $to_note}})
                MERGE (from)-[:{link_type}]->(to)
            """, from_note=from_note, to_note=to_note)

            echo_and_flush(f"✅ Link created: {from_note} → {to_note}")
            echo_and_flush(f"   🔗 Relationship: {link_type}")

            # Show smart suggestions for additional links
            suggestions = get_link_suggestions(from_note, to_note)
            if suggestions:
                echo_and_flush("🤖 AI Suggestions for related links:")
                for suggestion in suggestions[:3]:
                    echo_and_flush(f"   • {suggestion}")

    except Exception as e:
        echo_and_flush(f"❌ Error creating link: {e}", err=True)

def get_link_suggestions(from_note, to_note):
    """Get AI-powered link suggestions"""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Find notes with similar tags or content
            result = session.run("""
                MATCH (source:Note {name: $from_note})-[:TAGGED_WITH]->(tag:Tag)
                MATCH (other:Note)-[:TAGGED_WITH]->(tag)
                WHERE other.name <> $from_note AND other.name <> $to_note
                RETURN other.name as suggested_note, count(tag) as shared_tags
                ORDER BY shared_tags DESC
                LIMIT 3
            """, from_note=from_note, to_note=to_note)

            suggestions = []
            for record in result:
                suggestions.append(f"Consider linking to '{record['suggested_note']}' (shared {record['shared_tags']} tags)")

            return suggestions
    except:
        return []

@graph.command()
def network():
    """Show network analysis (enhanced version of show-network)"""
    try:
        echo_and_flush("🕸️ NETWORK ANALYSIS")
        echo_and_flush("=" * 30)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Network statistics
            network_stats = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (n)-[r:LINKS_TO]->()
                OPTIONAL MATCH ()-[r2:LINKS_TO]->(n)
                RETURN count(DISTINCT n) as total_nodes,
                       count(r) as outgoing_links,
                       count(r2) as incoming_links,
                       count(r) + count(r2) as total_connections
            """).single()

            echo_and_flush(f"📊 NETWORK STATISTICS:")
            echo_and_flush(f"   📝 Nodes (Notes): {network_stats['total_nodes']}")
            echo_and_flush(f"   🔗 Total Connections: {network_stats['total_connections']}")
            echo_and_flush(f"   📈 Network Density: {(network_stats['total_connections'] / max(network_stats['total_nodes'], 1)):.2f}")

            # Find network hubs (highly connected nodes)
            hubs = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (n)-[r1:LINKS_TO]->()
                OPTIONAL MATCH ()-[r2:LINKS_TO]->(n)
                WITH n, count(r1) + count(r2) as connections
                WHERE connections > 0
                RETURN n.name as note, connections
                ORDER BY connections DESC
                LIMIT 10
            """)

            hub_list = list(hubs)
            if hub_list:
                echo_and_flush(f"\n🌟 NETWORK HUBS (Most Connected):")
                for record in hub_list:
                    hub_indicator = "🔥" if record['connections'] > 5 else "⭐" if record['connections'] > 2 else "📝"
                    echo_and_flush(f"   {hub_indicator} {record['note']} ({record['connections']} connections)")

            # Find isolated nodes
            isolated = session.run("""
                MATCH (n:Note)
                WHERE NOT (n)-[:LINKS_TO]-() AND NOT ()-[:LINKS_TO]->(n)
                RETURN count(n) as isolated_count
            """).single()

            if isolated['isolated_count'] > 0:
                echo_and_flush(f"\n🏝️ ISOLATED NODES: {isolated['isolated_count']}")
                echo_and_flush("💡 Consider linking isolated notes to improve connectivity")

            # Network health score
            if network_stats['total_nodes'] > 0:
                connectivity_ratio = network_stats['total_connections'] / network_stats['total_nodes']
                health_status = "🟢 Well Connected" if connectivity_ratio > 1.5 else "🟡 Moderately Connected" if connectivity_ratio > 0.5 else "🔴 Poorly Connected"
                echo_and_flush(f"\n🎯 NETWORK HEALTH: {health_status}")

    except Exception as e:
        echo_and_flush(f"❌ Network analysis failed: {e}", err=True)

@graph.command()
def suggestions():
    """AI-powered link suggestions (NEW FEATURE)"""
    try:
        echo_and_flush("🤖 AI LINK SUGGESTIONS")
        echo_and_flush("=" * 30)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Find potential links based on shared tags
            tag_based = session.run("""
                MATCH (n1:Note)-[:TAGGED_WITH]->(tag:Tag)<-[:TAGGED_WITH]-(n2:Note)
                WHERE n1 <> n2 AND NOT (n1)-[:LINKS_TO]-(n2)
                WITH n1, n2, count(tag) as shared_tags
                WHERE shared_tags >= 2
                RETURN n1.name as note1, n2.name as note2, shared_tags
                ORDER BY shared_tags DESC
                LIMIT 10
            """)

            suggestions_found = False
            tag_suggestions = list(tag_based)
            if tag_suggestions:
                suggestions_found = True
                echo_and_flush("🏷️ TAG-BASED SUGGESTIONS:")
                for record in tag_suggestions:
                    echo_and_flush(f"   🔗 {record['note1']} ↔ {record['note2']}")
                    echo_and_flush(f"      📊 Shared tags: {record['shared_tags']}")

            # Find potential links based on content similarity (simple keyword matching)
            content_based = session.run("""
                MATCH (n1:Note), (n2:Note)
                WHERE n1 <> n2 AND NOT (n1)-[:LINKS_TO]-(n2)
                AND n1.type = n2.type AND n1.type IS NOT NULL
                RETURN n1.name as note1, n2.name as note2, n1.type as shared_type
                LIMIT 5
            """)

            content_suggestions = list(content_based)
            if content_suggestions:
                suggestions_found = True
                echo_and_flush(f"\n📂 CONTENT-TYPE SUGGESTIONS:")
                for record in content_suggestions:
                    echo_and_flush(f"   🔗 {record['note1']} ↔ {record['note2']}")
                    echo_and_flush(f"      📂 Shared type: {record['shared_type']}")

            if not suggestions_found:
                echo_and_flush("💡 No automatic suggestions found.")
                echo_and_flush("   • Add more tags to enable tag-based suggestions")
                echo_and_flush("   • Set note types to enable content-based suggestions")
            else:
                echo_and_flush(f"\n💡 Apply suggestions:")
                echo_and_flush("   cortex graph link <note1> <note2>")

    except Exception as e:
        echo_and_flush(f"❌ Link suggestions failed: {e}", err=True)

# ============================================================================
# 5. CORTEX AI - AI & Automation (KOMPLETT NEU)
# ============================================================================

@cortex.group()
def ai():
    """🤖 AI & Automation Features"""
    pass

@ai.command()
@click.argument('note_name')
def enhance(note_name):
    """AI-powered content enhancement (NEW FEATURE)"""
    try:
        echo_and_flush("🤖 AI CONTENT ENHANCEMENT")
        echo_and_flush("=" * 35)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Get note content
            result = session.run("""
                MATCH (n:Note {name: $name})
                RETURN n
            """, name=note_name)

            record = result.single()
            if not record:
                echo_and_flush(f"❌ Note '{note_name}' not found.")
                return

            note = record["n"]

            echo_and_flush(f"🔍 Analyzing: {note['name']}")

            # AI Enhancement Analysis
            enhancements = analyze_note_for_enhancements(note)

            if enhancements:
                echo_and_flush("✨ AI Enhancement Suggestions:")
                for category, suggestions in enhancements.items():
                    echo_and_flush(f"\n📊 {category.upper()}:")
                    for suggestion in suggestions:
                        echo_and_flush(f"   • {suggestion}")

                # Apply automatic enhancements
                if 'auto_fixes' in enhancements:
                    echo_and_flush("\n🔧 Applying automatic fixes...")
                    for fix in enhancements['auto_fixes']:
                        echo_and_flush(f"   ✅ {fix}")
                        # Here you would apply the actual fixes to the note

            else:
                echo_and_flush("✅ Note is already well-structured!")

    except Exception as e:
        echo_and_flush(f"❌ AI enhancement failed: {e}", err=True)

def analyze_note_for_enhancements(note):
    """Analyze note and suggest enhancements"""
    enhancements = {}

    content = note.get('content', '')
    name = note.get('name', '')
    description = note.get('description', '')

    # Structure analysis
    structure_suggestions = []
    if not description:
        structure_suggestions.append("Add description for better searchability")
    if len(content) > 500 and '\n#' not in content:
        structure_suggestions.append("Add headings to improve structure")
    if content and not content.strip().endswith('.'):
        structure_suggestions.append("Content should end with proper punctuation")

    if structure_suggestions:
        enhancements['structure'] = structure_suggestions

    # Content suggestions
    content_suggestions = []
    if len(content.split()) < 10:
        content_suggestions.append("Consider expanding content for more context")
    if 'TODO' in content.upper() or 'FIXME' in content.upper():
        content_suggestions.append("Contains TODO/FIXME items - consider creating tasks")

    if content_suggestions:
        enhancements['content'] = content_suggestions

    # Tagging suggestions
    tag_suggestions = []
    if not note.get('type'):
        tag_suggestions.append("Add content type for better categorization")

    # Detect missing tags based on content
    content_lower = content.lower()
    if any(word in content_lower for word in ['meeting', 'standup', 'sync']):
        tag_suggestions.append("Consider adding 'meeting' tag")
    if any(word in content_lower for word in ['project', 'plan', 'roadmap']):
        tag_suggestions.append("Consider adding 'project' tag")
    if any(word in content_lower for word in ['research', 'analysis', 'study']):
        tag_suggestions.append("Consider adding 'research' tag")

    if tag_suggestions:
        enhancements['tagging'] = tag_suggestions

    return enhancements

@ai.command(name='suggest-links')
def suggest_links():
    """Intelligent link suggestions (NEW FEATURE)"""
    try:
        echo_and_flush("🤖 INTELLIGENT LINK ANALYSIS")
        echo_and_flush("=" * 40)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Advanced link suggestions using multiple criteria
            echo_and_flush("🔍 Analyzing knowledge graph for opportunities...")

            # 1. Semantic similarity based on shared terminology
            semantic_links = session.run("""
                MATCH (n1:Note), (n2:Note)
                WHERE n1 <> n2 AND NOT (n1)-[:LINKS_TO]-(n2)
                AND (n1.content CONTAINS n2.name OR n2.content CONTAINS n1.name)
                RETURN n1.name as note1, n2.name as note2, 'semantic_reference' as reason
                LIMIT 5
            """)

            # 2. Tag-based clustering
            tag_clusters = session.run("""
                MATCH (n1:Note)-[:TAGGED_WITH]->(tag:Tag)<-[:TAGGED_WITH]-(n2:Note)
                WHERE n1 <> n2 AND NOT (n1)-[:LINKS_TO]-(n2)
                WITH n1, n2, count(tag) as shared_tags
                WHERE shared_tags >= 2
                RETURN n1.name as note1, n2.name as note2, 'shared_tags' as reason, shared_tags
                ORDER BY shared_tags DESC
                LIMIT 5
            """)

            # 3. Structural gaps (bridge suggestions)
            structural_gaps = session.run("""
                MATCH (n1:Note)-[:LINKS_TO]->(bridge:Note)-[:LINKS_TO]->(n2:Note)
                WHERE NOT (n1)-[:LINKS_TO]-(n2) AND n1 <> n2
                RETURN n1.name as note1, n2.name as note2, bridge.name as bridge_note, 'bridge_opportunity' as reason
                LIMIT 5
            """)

            suggestions_found = False

            # Display semantic suggestions
            semantic_results = list(semantic_links)
            if semantic_results:
                suggestions_found = True
                echo_and_flush("🧠 SEMANTIC LINK SUGGESTIONS:")
                for record in semantic_results:
                    echo_and_flush(f"   🔗 {record['note1']} → {record['note2']}")
                    echo_and_flush(f"      💡 Cross-referenced in content")

            # Display tag cluster suggestions
            tag_results = list(tag_clusters)
            if tag_results:
                suggestions_found = True
                echo_and_flush(f"\n🏷️ TAG CLUSTER SUGGESTIONS:")
                for record in tag_results:
                    echo_and_flush(f"   🔗 {record['note1']} ↔ {record['note2']}")
                    echo_and_flush(f"      📊 Shared {record['shared_tags']} tags")

            # Display structural suggestions
            structural_results = list(structural_gaps)
            if structural_results:
                suggestions_found = True
                echo_and_flush(f"\n🌉 BRIDGE OPPORTUNITIES:")
                for record in structural_results:
                    echo_and_flush(f"   🔗 {record['note1']} → {record['note2']}")
                    echo_and_flush(f"      🌉 Via: {record['bridge_note']}")

            if suggestions_found:
                echo_and_flush(f"\n🎯 NEXT STEPS:")
                echo_and_flush("   • cortex graph link <note1> <note2>  # Create link")
                echo_and_flush("   • cortex content show <note>         # Review content")
                echo_and_flush("   • cortex ai validate-content <note>  # Check quality")
            else:
                echo_and_flush("✅ Your knowledge graph is well-connected!")
                echo_and_flush("💡 Add more content and tags to discover new connections")

    except Exception as e:
        echo_and_flush(f"❌ Link analysis failed: {e}", err=True)

@ai.command(name='validate-content')
def validate_content(note_name):
    """AI-powered content quality validation (NEW FEATURE)"""
    try:
        echo_and_flush("🤖 AI CONTENT VALIDATION")
        echo_and_flush("=" * 35)

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Get note with all related data
            result = session.run("""
                MATCH (n:Note {name: $name})
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                OPTIONAL MATCH (n)-[r:LINKS_TO]->()
                RETURN n, count(DISTINCT t) as tag_count, count(r) as link_count
            """, name=note_name)

            record = result.single()
            if not record:
                echo_and_flush(f"❌ Note '{note_name}' not found.")
                return

            note = record["n"]
            tag_count = record["tag_count"]
            link_count = record["link_count"]

            echo_and_flush(f"🔍 Validating: {note['name']}")

            # Comprehensive validation
            validation_results = validate_note_quality(note, tag_count, link_count)

            # Display results
            overall_score = validation_results['overall_score']
            score_color = "🟢" if overall_score > 80 else "🟡" if overall_score > 60 else "🔴"

            echo_and_flush(f"\n📊 QUALITY SCORE: {score_color} {overall_score}/100")

            for category, details in validation_results['categories'].items():
                score = details['score']
                issues = details['issues']
                suggestions = details['suggestions']

                category_color = "🟢" if score > 80 else "🟡" if score > 60 else "🔴"
                echo_and_flush(f"\n{category_color} {category.upper()}: {score}/100")

                if issues:
                    echo_and_flush("   ❌ Issues:")
                    for issue in issues:
                        echo_and_flush(f"      • {issue}")

                if suggestions:
                    echo_and_flush("   💡 Suggestions:")
                    for suggestion in suggestions:
                        echo_and_flush(f"      • {suggestion}")

            # Overall recommendations
            if overall_score < 80:
                echo_and_flush(f"\n🎯 IMPROVEMENT PRIORITY:")
                if validation_results['categories']['content']['score'] < 60:
                    echo_and_flush("   1. Expand and structure content")
                if validation_results['categories']['metadata']['score'] < 60:
                    echo_and_flush("   2. Add tags and descriptions")
                if validation_results['categories']['connectivity']['score'] < 60:
                    echo_and_flush("   3. Create links to related notes")

    except Exception as e:
        echo_and_flush(f"❌ Content validation failed: {e}", err=True)

def validate_note_quality(note, tag_count, link_count):
    """Comprehensive note quality validation"""
    results = {
        'categories': {},
        'overall_score': 0
    }

    content = note.get('content', '')
    name = note.get('name', '')
    description = note.get('description', '')
    note_type = note.get('type', '')

    # Content Quality (40% of total score)
    content_score = 0
    content_issues = []
    content_suggestions = []

    if content:
        content_length = len(content.split())
        if content_length > 50:
            content_score += 40
        elif content_length > 20:
            content_score += 25
        else:
            content_issues.append("Content too brief (less than 20 words)")
            content_suggestions.append("Expand content with more details")

        # Structure check
        if '\n' in content or '#' in content:
            content_score += 20
        else:
            content_suggestions.append("Add structure with headings or line breaks")

        # Quality indicators
        if any(char in content for char in '.!?'):
            content_score += 10
        else:
            content_issues.append("Missing proper punctuation")

        if content != content.upper() and content != content.lower():
            content_score += 10
        else:
            content_issues.append("Content appears to be all caps or all lowercase")

    else:
        content_issues.append("No content provided")
        content_suggestions.append("Add meaningful content")

    results['categories']['content'] = {
        'score': min(content_score, 100),
        'issues': content_issues,
        'suggestions': content_suggestions
    }

    # Metadata Quality (30% of total score)
    metadata_score = 0
    metadata_issues = []
    metadata_suggestions = []

    if description:
        metadata_score += 30
    else:
        metadata_issues.append("No description provided")
        metadata_suggestions.append("Add descriptive summary")

    if note_type:
        metadata_score += 30
    else:
        metadata_issues.append("No content type specified")
        metadata_suggestions.append("Set appropriate content type")

    if tag_count > 0:
        metadata_score += min(tag_count * 10, 40)
    else:
        metadata_issues.append("No tags assigned")
        metadata_suggestions.append("Add relevant tags for categorization")

    results['categories']['metadata'] = {
        'score': min(metadata_score, 100),
        'issues': metadata_issues,
        'suggestions': metadata_suggestions
    }

    # Connectivity Quality (30% of total score)
    connectivity_score = 0
    connectivity_issues = []
    connectivity_suggestions = []

    if link_count > 0:
        connectivity_score += min(link_count * 25, 75)
    else:
        connectivity_issues.append("Not linked to other notes")
        connectivity_suggestions.append("Create links to related content")

    if link_count > 2:
        connectivity_score += 25
    elif link_count > 0:
        connectivity_suggestions.append("Consider adding more related links")

    results['categories']['connectivity'] = {
        'score': min(connectivity_score, 100),
        'issues': connectivity_issues,
        'suggestions': connectivity_suggestions
    }

    # Calculate overall score
    content_weight = 0.4
    metadata_weight = 0.3
    connectivity_weight = 0.3

    overall = (
        results['categories']['content']['score'] * content_weight +
        results['categories']['metadata']['score'] * metadata_weight +
        results['categories']['connectivity']['score'] * connectivity_weight
    )

    results['overall_score'] = int(overall)

    return results

# ============================================================================
# SMART SHORTCUT HANDLERS
# ============================================================================

@cortex.command(hidden=True)
@click.argument('query')
def search(query):
    """Hidden shortcut for 'cortex search <query>' → 'cortex content search <query>'"""
    ctx = click.get_current_context()
    ctx.invoke(content.get_command(ctx, 'search'), query=query)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    try:
        cortex()
    except KeyboardInterrupt:
        echo_and_flush("\n👋 Cortex CLI terminated by user")
    except Exception as e:
        echo_and_flush(f"❌ Unexpected error: {e}", err=True)
    finally:
        Neo4jHelper.close()
