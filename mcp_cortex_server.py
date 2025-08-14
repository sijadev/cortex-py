#!/usr/bin/env python3
"""
Cortex MCP Server - Ein MCP Server für die Cortex-CLI Integration mit Claude Desktop
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

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
            description="Überblick über den Knowledge Graph",
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
            ], capture_output=True, text=True, cwd="/Users/simonjanke/Projects/cortex-py")
            return result.stdout or "Status nicht verfügbar"
        except Exception as e:
            return f"Fehler beim Abrufen des Status: {str(e)}"
    
    elif uri == "cortex://knowledge-graph":
        try:
            result = subprocess.run([
                "python3", "cortex_neo/cortex_cli.py", "graph-info"
            ], capture_output=True, text=True, cwd="/Users/simonjanke/Projects/cortex-py")
            return result.stdout or "Graph-Informationen nicht verfügbar"
        except Exception as e:
            return f"Fehler beim Abrufen der Graph-Informationen: {str(e)}"
    
    else:
        raise ValueError(f"Unbekannte Ressource: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Liste alle verfügbaren Cortex-Tools auf."""
    return [
        Tool(
            name="cortex_run_command",
            description="Führt einen Cortex CLI Befehl aus",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Der Cortex CLI Befehl (z.B. 'status', 'link-validate-ai')",
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
            name="cortex_add_knowledge",
            description="Fügt neues Wissen zum Cortex Knowledge Graph hinzu",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Titel des Wissenseintrags",
                    },
                    "content": {
                        "type": "string",
                        "description": "Inhalt des Wissenseintrags",
                    },
                    "category": {
                        "type": "string",
                        "description": "Kategorie des Wissenseintrags",
                        "default": "general",
                    },
                },
                "required": ["title", "content"],
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
                    "limit": {
                        "type": "integer",
                        "description": "Maximale Anzahl der Ergebnisse",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Behandelt Tool-Aufrufe."""
    
    if name == "cortex_run_command":
        command = arguments.get("command")
        args = arguments.get("args", [])
        
        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", command] + args
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py"
            )
            
            output = f"Befehl: {' '.join(cmd_list)}\n"
            output += f"Exit Code: {result.returncode}\n"
            output += f"Ausgabe:\n{result.stdout}"
            if result.stderr:
                output += f"\nFehler:\n{result.stderr}"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Fehler beim Ausführen des Befehls: {str(e)}")]
    
    elif name == "cortex_add_knowledge":
        title = arguments.get("title")
        content = arguments.get("content")
        category = arguments.get("category", "general")
        
        try:
            # Hier würden Sie den spezifischen Cortex-Befehl zum Hinzufügen von Wissen aufrufen
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "add-knowledge", 
                       "--title", title, "--content", content, "--category", category]
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py"
            )
            
            if result.returncode == 0:
                return [TextContent(type="text", text=f"Wissen erfolgreich hinzugefügt: {title}")]
            else:
                return [TextContent(type="text", text=f"Fehler beim Hinzufügen: {result.stderr}")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"Fehler: {str(e)}")]
    
    elif name == "cortex_search":
        query = arguments.get("query")
        limit = arguments.get("limit", 10)
        
        try:
            cmd_list = ["python3", "cortex_neo/cortex_cli.py", "search", 
                       "--query", query, "--limit", str(limit)]
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd="/Users/simonjanke/Projects/cortex-py"
            )
            
            return [TextContent(type="text", text=f"Suchergebnisse für '{query}':\n{result.stdout}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Fehler bei der Suche: {str(e)}")]
    
    else:
        raise ValueError(f"Unbekanntes Tool: {name}")

async def main():
    """Startet den MCP Server."""
    print("🚀 Starte Cortex MCP Server...", file=sys.stderr)

    # Erstelle eine einfache Datenstruktur für notification_options
    from types import SimpleNamespace
    notification_options = SimpleNamespace(
        resources_changed=False,
        tools_changed=False,
        prompts_changed=False
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cortex-py",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=notification_options,
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 MCP Server beendet", file=sys.stderr)
    except Exception as e:
        print(f"❌ MCP Server Fehler: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
