#!/usr/bin/env python3
"""
Cortex CLI - AI-Optimized Structured Interface
Implements 4+1 Category Structure for Better UX
"""

import click
import os
import sys
from neo4j import GraphDatabase
import logging
from typing import cast as _cast
# New structured imports with fallback for direct execution
try:
    from .config import Settings
    from .infra.neo4j_client import Neo4jClient
    from .repositories.system_repository import SystemRepository
    from .repositories.content_repository import ContentRepository
    from .repositories.tag_repository import TagRepository
    from .repositories.note_repository import NoteRepository
    from .services.system_service import SystemService
    from .services.content_service import ContentService
    from .services.tag_service import TagService
    from .services.note_service import NoteService
except ImportError:  # support running as a script: python cortex_neo/cortex_cli.py
    import os as _os
    _HERE = _os.path.dirname(__file__)
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    from config import Settings  # type: ignore
    from infra.neo4j_client import Neo4jClient  # type: ignore
    from repositories.system_repository import SystemRepository  # type: ignore
    from repositories.content_repository import ContentRepository  # type: ignore
    from repositories.tag_repository import TagRepository  # type: ignore
    from repositories.note_repository import NoteRepository  # type: ignore
    from services.system_service import SystemService  # type: ignore
    from services.content_service import ContentService  # type: ignore
    from services.tag_service import TagService  # type: ignore
    from services.note_service import NoteService  # type: ignore

# Configuration
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")

# Track latest client for clean shutdown
_LAST_CLIENT: Neo4jClient | None = None

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

# Add helper to support shortcut 'cortex <note-name>'
# Reuses the existing content.show command to preserve output formatting

def show_note_content(note_name: str) -> None:
    try:
        ctx = click.get_current_context()
        # Invoke the registered content 'show' command for consistent behavior
        ctx.invoke(_cast(click.Group, content).get_command(ctx, 'show'), name=note_name)
    except SystemExit:
        # Propagate clean exits from Click
        raise
    except Exception as e:
        echo_and_flush(f"❌ Error showing content: {e}", err=True)

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

    # Initialize structured services once and store on context
    settings = Settings.from_env(verbose=verbose)
    client = Neo4jClient(settings)
    sys_repo = SystemRepository(client)
    sys_service = SystemService(sys_repo)
    # Initialize additional services
    content_repo = ContentRepository(client)
    tag_repo = TagRepository(client)
    note_repo = NoteRepository()
    content_service = ContentService(content_repo)
    tag_service = TagService(tag_repo)
    note_service = NoteService(note_repo)
    ctx.obj['settings'] = settings
    ctx.obj['client'] = client
    ctx.obj['system_service'] = sys_service
    ctx.obj['content_service'] = content_service
    ctx.obj['tag_service'] = tag_service
    ctx.obj['note_service'] = note_service

    global _LAST_CLIENT
    _LAST_CLIENT = client

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
        quick_status(ctx)

def quick_status(ctx):
    """Quick system status overview using SystemService"""
    try:
        svc: SystemService = ctx.obj.get('system_service')
        settings: Settings = ctx.obj.get('settings')
        echo_and_flush("🎯 CORTEX QUICK STATUS")
        echo_and_flush("=" * 30)

        overview = svc.status_overview()
        stats = overview['stats']
        echo_and_flush(f"📝 Notes: {stats['notes']}")
        echo_and_flush(f"🏷️ Tags: {stats['tags']}")
        echo_and_flush(f"🔗 Links: {stats['links']}")
        echo_and_flush(f"🔗 URI: {settings.uri}")
        echo_and_flush(f"🎯 Status: {overview['health_status']}")

    except Exception as e:
        echo_and_flush(f"❌ Status check failed: {e}", err=True)

# ============================================================================
# 1. CORTEX SYSTEM - System Management
# ============================================================================

@cortex.group()
def system():
    """🔧 System Management Commands"""
    pass

@system.command()
@click.pass_context
def status(ctx):
    """System status overview (enhanced version of cortex-status)"""
    try:
        svc: SystemService = ctx.obj.get('system_service')
        settings: Settings = ctx.obj.get('settings')
        echo_and_flush("🎯 CORTEX SYSTEM STATUS OVERVIEW")
        echo_and_flush("=" * 50)

        # Connection Test & Server Time
        echo_and_flush(f"🔗 NEO4J CONNECTION: {'✅ Connected' if svc.connection_ok() else '❌ Not Connected'}")
        echo_and_flush(f"   Server Time: {svc.get_server_time()}")
        echo_and_flush(f"   URI: {settings.uri}")

        # Comprehensive Data Statistics
        stats = svc.get_quick_stats()
        echo_and_flush(f"\n📈 DATA STATISTICS:")
        echo_and_flush(f"   📝 Notes: {stats['notes']}")
        echo_and_flush(f"   🔄 Workflows: {stats['workflows']}")
        echo_and_flush(f"   🏷️ Tags: {stats['tags']}")
        echo_and_flush(f"   🔗 Links: {stats['links']}")
        echo_and_flush(f"   🏗️ Templates: {stats['templates']}")

        overview = svc.status_overview()
        echo_and_flush(f"\n🎯 OVERALL STATUS: {overview['health_status']} (Score: {overview['health_score']})")

    except Exception as e:
        echo_and_flush(f"❌ Status query failed: {e}", err=True)

@system.command()
@click.pass_context
def health(ctx):
    """System health check (enhanced version of validate-connection)"""
    try:
        svc: SystemService = ctx.obj.get('system_service')
        echo_and_flush("🔍 SYSTEM HEALTH CHECK")
        echo_and_flush("=" * 30)

        # Neo4j Connection
        if svc.connection_ok():
            echo_and_flush(f"✅ Neo4j Connection: OK")
            echo_and_flush(f"   🕒 Server Time: {svc.get_server_time()}")
        else:
            echo_and_flush("❌ Neo4j Connection: Failed", err=True)
            raise click.ClickException("connection failed")

        # Data Integrity Check
        hc = svc.health_check()
        echo_and_flush(f"✅ Data Integrity: OK")
        echo_and_flush(f"   🏷️ Tag Coverage: {hc['tag_coverage']:.1f}%")
        echo_and_flush(f"   🔗 Link Coverage: {hc['link_coverage']:.1f}%")

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
            echo_and_flush(f"   ���️ Tags: {result['tag_count']}")
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
@click.pass_context
def create(ctx, name, content, description, note_type, smart):
    """Create new content (enhanced version of add-note)"""
    try:
        svc: ContentService = ctx.obj.get('content_service')
        if smart:
            echo_and_flush("🤖 AI-Enhanced Content Creation")
            echo_and_flush("=" * 35)

            # AI Content Analysis
            ai_suggestions = analyze_content_with_ai(name, content, description, note_type)

            if ai_suggestions:
                echo_and_flush("🧠 AI Analysis Results:")
                # ai_suggestions may be dict; print user-facing messages if list-like keys present
                for k, v in ai_suggestions.items():
                    if isinstance(v, list):
                        for item in v:
                            echo_and_flush(f"   • {item}")

            # Apply AI suggestions
            note_type = ai_suggestions.get('suggested_type', note_type)
            auto_tags = ai_suggestions.get('auto_tags', [])
        else:
            echo_and_flush(f"📝 Creating note: {name}")
            auto_tags = []

        # Use service to create note and add tags
        svc.create_note(name, content or "", description or "", note_type or "", smart, auto_tags)
        for tag_name in auto_tags:
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
@click.pass_context
def search(ctx, query):
    """Search content (enhanced version of search-notes)"""
    try:
        svc: ContentService = ctx.obj.get('content_service')
        echo_and_flush(f"🔍 Searching for: '{query}'")
        echo_and_flush("=" * 40)

        results = svc.search(query)
        if results:
            echo_and_flush(f"📝 Found {len(results)} results:")
            echo_and_flush("")

            for record in results:
                note = record["note"]
                tags = record.get("tags") or []

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
@click.pass_context
def show(ctx, name):
    """Show detailed content view"""
    try:
        svc: ContentService = ctx.obj.get('content_service')
        detail = svc.get_detail(name)
        if not detail:
            echo_and_flush(f"❌ Note '{name}' not found.")
            return

        note = detail["note"]
        tags = detail["tags"]
        outgoing_links = detail["outgoing"]
        incoming_links = detail["incoming"]

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
@click.pass_context
def list(ctx):
    """List all content with enhanced filtering"""
    try:
        echo_and_flush("📝 CONTENT OVERVIEW")
        echo_and_flush("=" * 30)

        svc: ContentService = ctx.obj.get('content_service')
        rows = svc.list_with_tag_count()

        notes_by_type = {}
        for row in rows:
            note = row["note"]
            tag_count = row["tag_count"]
            note_type = note.get('type', 'untyped')
            notes_by_type.setdefault(note_type, []).append({"note": note, "tag_count": tag_count})

        if notes_by_type:
            total_notes = sum(len(notes) for notes in notes_by_type.values())
            echo_and_flush(f"📊 Total: {total_notes} notes")
            echo_and_flush("")

            for note_type, notes in notes_by_type.items():
                echo_and_flush(f"📂 {note_type.upper()} ({len(notes)} notes):")
                for item in notes[:10]:
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
@click.pass_context
def add(ctx, note_name, tag_name):
    """Add tag to note (enhanced version of add-tag)"""
    try:
        svc: TagService = ctx.obj.get('tag_service')
        svc.add(note_name, tag_name)
        echo_and_flush(f"✅ Tag '{tag_name}' added to note '{note_name}'")

        # Show smart suggestions for related tags
        related_tags = get_related_tag_suggestions(tag_name)
        if related_tags:
            echo_and_flush("💡 Related tag suggestions:")
            for related_tag in related_tags[:3]:
                echo_and_flush(f"   • {related_tag}")
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
@click.pass_context
def list(ctx):
    """List all tags with enhanced categorization (enhanced version of list-tags)"""
    try:
        svc: TagService = ctx.obj.get('tag_service')
        rows = svc.list_with_usage()

        tags_by_category = {}
        total_tags = 0
        for r in rows:
            total_tags += 1
            category = r.get('category') or 'uncategorized'
            tags_by_category.setdefault(category, []).append({
                'name': r.get('name'),
                'description': r.get('description') or 'No description',
                'usage_count': r.get('usage_count'),
                'created_at': r.get('created_at'),
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
            most_used_category = max(tags_by_category.keys(), key=lambda k: sum(t['usage_count'] for t in tags_by_category[k]))
            echo_and_flush(f"   📈 Most active category: {most_used_category}")

            unused_tags = [tag['name'] for tags in tags_by_category.values() for tag in tags if tag['usage_count'] == 0]
            if unused_tags:
                echo_and_flush(f"   🔍 Unused tags: {len(unused_tags)} (consider cleanup)")
        else:
            echo_and_flush("❌ No tags found.")
    except Exception as e:
        echo_and_flush(f"❌ Error listing tags: {e}", err=True)
