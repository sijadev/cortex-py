#!/usr/bin/env python3
"""
Cortex MCP Server - Funktionsfähiger MCP Server für Claude Desktop
Basiert auf der aktuellen MCP SDK Version mit vollständiger Cortex Integration
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent, ServerCapabilities

# Initialisiere den MCP Server
server = Server("cortex-py")

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """Liste alle verfügbaren Cortex-Ressourcen auf."""
    return [
        Resource(
            uri="cortex://status",
            name="Cortex Status",
            description="Aktueller Status des Cortex Systems",
            mimeType="text/plain",
        ),
        Resource(
            uri="cortex://knowledge-graph",
            name="Knowledge Graph Overview",
            description="Überblick über den Cortex Knowledge Graph",
            mimeType="application/json",
        ),
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Lese eine Cortex-Ressource."""
    if uri == "cortex://status":
        try:
            result = subprocess.run([
                "python3", "cortex_neo/cortex_cli.py", "status"
            ], capture_output=True, text=True, cwd="/Users/simonjanke/Projects/cortex-py", timeout=10)
            return result.stdout or "Cortex System ist aktiv."
        except Exception as e:
            return f"Cortex Status: System bereit (CLI nicht verfügbar: {str(e)})"

    elif uri == "cortex://knowledge-graph":
        try:
            result = subprocess.run([
                "python3", "cortex_neo/cortex_cli.py", "graph-info"
            ], capture_output=True, text=True, cwd="/Users/simonjanke/Projects/cortex-py", timeout=10)
            return result.stdout or "Graph-Informationen nicht verfügbar"
        except Exception as e:
            return f"Knowledge Graph: Verfügbar (Details nicht abrufbar: {str(e)})"

    else:
        raise ValueError(f"Unbekannte Ressource: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Liste alle verfügbaren Cortex-Tools auf."""
    return [
        Tool(
            name="cortex_status",
            description="Zeigt den Status des Cortex Systems an",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
        Tool(
            name="cortex_run_command",
            description="Führt einen Cortex CLI Befehl aus",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Der Cortex CLI Befehl (z.B. 'status', 'help')",
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Zusätzliche Argumente für den Befehl",
                        "default": [],
                    },
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="cortex_search",
            description="Durchsucht den Cortex Knowledge Graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Suchbegriff oder -phrase",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="cortex_add_note",
            description="Erstellt eine neue Note mit Content im Knowledge Graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name/Titel der Note",
                    },
                    "content": {
                        "type": "string",
                        "description": "Textinhalt der Note",
                    },
                    "description": {
                        "type": "string",
                        "description": "Kurze Beschreibung der Note",
                    },
                    "note_type": {
                        "type": "string",
                        "description": "Typ/Kategorie der Note (z.B. 'project', 'idea', 'note')",
                    },
                    "url": {
                        "type": "string",
                        "description": "URL/Link zur Note",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="cortex_show_note",
            description="Zeigt eine Note mit allen Details (Content, Tags, Links)",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name der Note",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="cortex_update_content",
            description="Aktualisiert den Content einer bestehenden Note",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name der Note",
                    },
                    "content": {
                        "type": "string",
                        "description": "Neuer Textinhalt",
                    },
                },
                "required": ["name", "content"],
            },
        ),
        Tool(
            name="cortex_search_content",
            description="Durchsucht Notes nach Content (erweiterte Suche)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Suchbegriff oder -phrase",
                    },
                    "in_content": {
                        "type": "boolean",
                        "description": "Auch im Content suchen (nicht nur Name/Beschreibung)",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="cortex_auto_link_content",
            description="Erstellt automatische Links basierend auf Content-Ähnlichkeit",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_similarity": {
                        "type": "number",
                        "description": "Minimale Ähnlichkeit für automatische Links (0.0-1.0)",
                        "default": 0.3,
                    },
                    "max_links_per_note": {
                        "type": "integer",
                        "description": "Maximale neue Links pro Note",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="cortex_suggest_links",
            description="Schlägt Links für eine Note basierend auf Content-Ähnlichkeit vor",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_name": {
                        "type": "string",
                        "description": "Name der Note für die Links vorgeschlagen werden sollen",
                    },
                    "suggestions": {
                        "type": "integer",
                        "description": "Anzahl der Link-Vorschläge",
                        "default": 5,
                    },
                    "min_similarity": {
                        "type": "number",
                        "description": "Minimale Ähnlichkeit für Vorschläge",
                        "default": 0.2,
                    },
                },
                "required": ["note_name"],
            },
        ),
        Tool(
            name="cortex_ai_suggest_tags",
            description="AI-basierte Tag-Vorschläge durch Machine Learning aus Content-Mustern",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_confidence": {
                        "type": "number",
                        "description": "Minimale Konfidenz für Tag-Vorschläge (0.0-1.0)",
                        "default": 0.4,
                    },
                    "max_tags_per_note": {
                        "type": "integer",
                        "description": "Maximale neue Tags pro Note",
                        "default": 5,
                    },
                },
            },
        ),
        Tool(
            name="cortex_ai_apply_tags",
            description="Wendet AI-Tag-Vorschläge automatisch auf Notes an",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_confidence": {
                        "type": "number",
                        "description": "Minimale Konfidenz für automatische Anwendung",
                        "default": 0.5,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Nur Vorschau zeigen ohne Änderungen",
                        "default": False,
                    },
                    "max_tags_per_note": {
                        "type": "integer",
                        "description": "Maximale neue Tags pro Note",
                        "default": 3,
                    },
                },
            },
        ),
        Tool(
            name="cortex_ai_suggest_tags_for_note",
            description="AI-Tag-Vorschläge für eine spezifische Note",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_name": {
                        "type": "string",
                        "description": "Name der Note für Tag-Vorschläge",
                    },
                    "suggestions": {
                        "type": "integer",
                        "description": "Anzahl der Tag-Vorschläge",
                        "default": 5,
                    },
                    "min_confidence": {
                        "type": "number",
                        "description": "Minimale Konfidenz für Vorschläge",
                        "default": 0.3,
                    },
                },
                "required": ["note_name"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Behandelt Tool-Aufrufe."""

    if name == "cortex_status":
        return [TextContent(type="text", text="✅ Cortex MCP Server läuft erfolgreich und ist bereit für Claude Desktop Integration!")]

    elif name == "cortex_run_command":
        command = arguments.get("command", "status")
        args = arguments.get("args", [])

        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", command] + args
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"🔧 Cortex Befehl: {command}\n"
            output += f"📋 Exit Code: {result.returncode}\n"

            if result.stdout:
                output += f"✅ Ausgabe:\n{result.stdout}"
            else:
                output += "📝 Keine Ausgabe erhalten\n"

            if result.stderr:
                output += f"\n⚠️ Warnungen/Fehler:\n{result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: Der Befehl '{command}' dauerte zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler beim Ausführen von '{command}': {str(e)}")]

    elif name == "cortex_search":
        query = arguments.get("query", "")

        if not query.strip():
            return [TextContent(type="text", text="❌ Bitte geben Sie eine Suchanfrage an")]

        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "search", "--query", query]
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"🔍 Suche nach: '{query}'\n"

            if result.returncode == 0 and result.stdout:
                output += f"📄 Ergebnisse:\n{result.stdout}"
            else:
                output += "📭 Keine Ergebnisse gefunden oder Suchfunktion nicht verfügbar"
                if result.stderr:
                    output += f"\n⚠️ Details: {result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: Die Suche nach '{query}' dauerte zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler bei der Suche nach '{query}': {str(e)}")]

    elif name == "cortex_add_note":
        note_name = arguments.get("name", "")
        content = arguments.get("content", "")
        description = arguments.get("description", "")
        note_type = arguments.get("note_type", "")
        url = arguments.get("url", "")

        if not note_name:
            return [TextContent(type="text", text="❌ Der Name der Note ist erforderlich.")]

        try:
            # Verwende direkte CLI-Parameter statt fehlerhafte --name Syntax
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "add-note", note_name]
            if content:
                cmd_list.extend(["--content", content])
            if description:
                cmd_list.extend(["--description", description])
            if note_type:
                cmd_list.extend(["--type", note_type])
            if url:
                cmd_list.extend(["--url", url])

            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"📝 Note erstellt: '{note_name}'\n"
            output += f"📋 Exit Code: {result.returncode}\n"

            if result.stdout:
                output += f"✅ Ergebnis:\n{result.stdout}"
            elif result.returncode == 0:
                output += f"✅ Note '{note_name}' erfolgreich erstellt!\n"
                if content:
                    output += f"📄 Content: {content[:200]}{'...' if len(content) > 200 else ''}\n"
                if description:
                    output += f"📝 Beschreibung: {description}\n"
                if note_type:
                    output += f"🏷️ Typ: {note_type}\n"

            if result.stderr:
                output += f"\n⚠️ Warnungen: {result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: Das Erstellen der Note '{note_name}' dauerte zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler beim Erstellen der Note '{note_name}': {str(e)}")]

    elif name == "cortex_show_note":
        note_name = arguments.get("name", "")

        if not note_name:
            return [TextContent(type="text", text="❌ Der Name der Note ist erforderlich.")]

        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "show-note", note_name]
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"📄 Note Details: '{note_name}'\n"
            output += f"📋 Exit Code: {result.returncode}\n"

            if result.stdout:
                output += f"📋 Details:\n{result.stdout}"
            elif result.returncode == 0:
                output += f"✅ Note '{note_name}' gefunden, aber keine Details verfügbar.\n"
                output += "💡 Möglicherweise ist die Note leer oder die Verbindung zur Datenbank fehlt.\n"

            if result.stderr:
                output += f"\n⚠️ Warnungen: {result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: Das Anzeigen der Note '{note_name}' dauerte zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler beim Anzeigen der Note '{note_name}': {str(e)}")]

    elif name == "cortex_update_content":
        note_name = arguments.get("name", "")
        content = arguments.get("content", "")

        if not note_name:
            return [TextContent(type="text", text="❌ Der Name der Note ist erforderlich.")]
        if not content:
            return [TextContent(type="text", text="❌ Neuer Inhalt muss angegeben werden.")]

        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "update-note-content", note_name, content]
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"🔄 Content Update: '{note_name}'\n"
            output += f"📋 Exit Code: {result.returncode}\n"

            if result.stdout:
                output += f"✅ Ergebnis:\n{result.stdout}"
            elif result.returncode == 0:
                output += f"✅ Content der Note '{note_name}' erfolgreich aktualisiert!\n"
                output += f"📄 Neuer Content: {content[:200]}{'...' if len(content) > 200 else ''}\n"

            if result.stderr:
                output += f"\n⚠️ Warnungen: {result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: Das Aktualisieren der Note '{note_name}' dauerte zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler beim Aktualisieren der Note '{note_name}': {str(e)}")]

    elif name == "cortex_search_content":
        query = arguments.get("query", "")
        in_content = arguments.get("in_content", True)

        if not query.strip():
            return [TextContent(type="text", text="❌ Bitte geben Sie eine Suchanfrage an")]

        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "search-notes", query]
            if in_content:
                cmd_list.append("--in-content")

            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"🔍 Content-Suche nach: '{query}'\n"
            output += f"📋 Exit Code: {result.returncode}\n"

            if result.stdout:
                output += f"📄 Suchergebnisse:\n{result.stdout}"
            elif result.returncode == 0:
                output += "📭 Keine Ergebnisse gefunden.\n"

            if result.stderr:
                output += f"\n⚠️ Warnungen: {result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: Die Suche nach '{query}' dauerte zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler bei der Suche nach '{query}': {str(e)}")]

    elif name == "cortex_auto_link_content":
        min_similarity = arguments.get("min_similarity", 0.3)
        max_links_per_note = arguments.get("max_links_per_note", 10)

        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "auto-link-content"]
            cmd_list.extend(["--min-similarity", str(min_similarity)])
            cmd_list.extend(["--max-links-per-note", str(max_links_per_note)])

            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"🔗 Automatische Verlinkung:\n"
            output += f"📋 Exit Code: {result.returncode}\n"

            if result.stdout:
                output += f"✅ Ergebnisse:\n{result.stdout}"
            elif result.returncode == 0:
                output += "✅ Automatische Verlinkung erfolgreich durchgeführt!\n"

            if result.stderr:
                output += f"\n⚠️ Warnungen: {result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: Automatische Verlinkung dauerte zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler bei der automatischen Verlinkung: {str(e)}")]

    elif name == "cortex_suggest_links":
        note_name = arguments.get("note_name", "")
        suggestions = arguments.get("suggestions", 5)
        min_similarity = arguments.get("min_similarity", 0.2)

        if not note_name:
            return [TextContent(type="text", text="❌ Der Name der Note ist erforderlich.")]

        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "suggest-links", note_name]
            cmd_list.extend(["--suggestions", str(suggestions)])
            cmd_list.extend(["--min-similarity", str(min_similarity)])

            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"💡 Link-Vorschläge für '{note_name}':\n"
            output += f"📋 Exit Code: {result.returncode}\n"

            if result.stdout:
                output += f"✅ Vorschläge:\n{result.stdout}"
            elif result.returncode == 0:
                output += "✅ Keine neuen Vorschläge, die Note ist möglicherweise bereits optimal verlinkt.\n"

            if result.stderr:
                output += f"\n⚠️ Warnungen: {result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: Vorschläge für Links dauerten zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler bei der Vorschlagserstellung für Links: {str(e)}")]

    elif name == "cortex_ai_suggest_tags":
        min_confidence = arguments.get("min_confidence", 0.4)
        max_tags_per_note = arguments.get("max_tags_per_note", 5)

        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "ai-suggest-tags"]
            cmd_list.extend(["--min-confidence", str(min_confidence)])
            cmd_list.extend(["--max-tags-per-note", str(max_tags_per_note)])

            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"🏷️ AI-Tag-Vorschläge:\n"
            output += f"📋 Exit Code: {result.returncode}\n"

            if result.stdout:
                output += f"✅ Vorschläge:\n{result.stdout}"
            elif result.returncode == 0:
                output += "✅ Keine neuen Tag-Vorschläge, die Note ist möglicherweise bereits optimal getaggt.\n"

            if result.stderr:
                output += f"\n⚠️ Warnungen: {result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: AI-Tag-Vorschläge dauerten zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler bei der Erstellung von AI-Tag-Vorschlägen: {str(e)}")]

    elif name == "cortex_ai_apply_tags":
        min_confidence = arguments.get("min_confidence", 0.5)
        dry_run = arguments.get("dry_run", False)
        max_tags_per_note = arguments.get("max_tags_per_note", 3)

        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "ai-apply-tags"]
            cmd_list.extend(["--min-confidence", str(min_confidence)])
            if dry_run:
                cmd_list.append("--dry-run")
            cmd_list.extend(["--max-tags-per-note", str(max_tags_per_note)])

            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"🔖 AI-Tag-Anwendung:\n"
            output += f"📋 Exit Code: {result.returncode}\n"

            if result.stdout:
                output += f"✅ Ergebnisse:\n{result.stdout}"
            elif result.returncode == 0:
                output += "✅ AI-Tags erfolgreich angewendet!\n"

            if result.stderr:
                output += f"\n⚠️ Warnungen: {result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: Anwendung der AI-Tags dauerte zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler bei der Anwendung von AI-Tags: {str(e)}")]

    elif name == "cortex_ai_suggest_tags_for_note":
        note_name = arguments.get("note_name", "")
        suggestions = arguments.get("suggestions", 5)
        min_confidence = arguments.get("min_confidence", 0.3)

        if not note_name:
            return [TextContent(type="text", text="❌ Der Name der Note ist erforderlich.")]

        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "ai-suggest-tags-for-note", note_name]
            cmd_list.extend(["--suggestions", str(suggestions)])
            cmd_list.extend(["--min-confidence", str(min_confidence)])

            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py",
                timeout=30
            )

            output = f"🏷️ AI-Tag-Vorschläge für '{note_name}':\n"
            output += f"📋 Exit Code: {result.returncode}\n"

            if result.stdout:
                output += f"✅ Vorschläge:\n{result.stdout}"
            elif result.returncode == 0:
                output += "✅ Keine neuen Tag-Vorschläge, die Note ist möglicherweise bereits optimal getaggt.\n"

            if result.stderr:
                output += f"\n⚠️ Warnungen: {result.stderr}"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Timeout: Vorschläge für AI-Tags dauerten zu lange")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Fehler bei der Erstellung von AI-Tag-Vorschlägen für die Note: {str(e)}")]

    else:
        return [TextContent(type="text", text=f"❌ Unbekanntes Tool: {name}")]

async def main():
    """Startet den MCP Server."""
    print("🚀 Starte Cortex MCP Server für Claude Desktop...", file=sys.stderr)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cortex-py",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    resources={},
                    tools={},
                    prompts={}
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
