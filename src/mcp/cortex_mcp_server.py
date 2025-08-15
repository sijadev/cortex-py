#!/usr/bin/env python3
"""
Cortex MCP Server - Unified Model Context Protocol Server for Cortex-py
=====================================================================

This unified MCP server combines all MCP functionality for Cortex integration:
- Full-featured MCP server with all Cortex CLI functions
- Resource management for Cortex knowledge graph
- Tool execution for CLI commands
- Claude Desktop integration
- Neo4j database interaction

Usage:
    python src/mcp/cortex_mcp_server.py

For Claude Desktop, configure in claude_desktop_config.json:
{
  "mcpServers": {
    "cortex-py": {
      "command": "python",
      "args": ["src/mcp/cortex_mcp_server.py"],
      "cwd": "/path/to/cortex-py"
    }
  }
}
"""

import asyncio
import json
import subprocess
import sys
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

# Import MCP components with better error handling
MCP_AVAILABLE = False
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        ServerCapabilities,
    )
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MCP modules not available: {e}", file=sys.stderr)
    # Create mock classes for development/testing when MCP is not available
    class Server:
        def __init__(self, name):
            self.name = name
        def list_resources(self):
            def decorator(func): return func
            return decorator
        def read_resource(self):
            def decorator(func): return func
            return decorator
        def list_tools(self):
            def decorator(func): return func
            return decorator
        def call_tool(self):
            def decorator(func): return func
            return decorator
        def get_capabilities(self, notification_options=None, experimental_capabilities=None):
            return {}
        def run(self, *args, **kwargs):
            pass

    class Resource:
        def __init__(self, uri, name, description, mimeType):
            self.uri, self.name, self.description, self.mimeType = uri, name, description, mimeType

    class Tool:
        def __init__(self, name, description, inputSchema):
            self.name, self.description, self.inputSchema = name, description, inputSchema

    class TextContent:
        def __init__(self, type, text):
            self.type, self.text = type, text

    class InitializationOptions:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
                
    class NotificationOptions:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    async def stdio_server():
        # Mock stdio server for when MCP is not available
        class MockStream:
            async def read(self): return b""
            async def write(self, data): pass
        return MockStream(), MockStream()

# Initialize the unified MCP Server
server = Server("cortex-py-unified")

# Project configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
CORTEX_CLI_PATH = PROJECT_ROOT / "cortex_neo" / "cortex_cli.py"

class CortexMCPServer:
    """Unified Cortex MCP Server implementation"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.cortex_cli_path = CORTEX_CLI_PATH

    def get_cortex_cli_path(self) -> Path:
        """Get the path to the Cortex CLI"""
        return self.cortex_cli_path

    def is_cortex_cli_available(self) -> bool:
        """Check if Cortex CLI is available"""
        return self.cortex_cli_path.exists()

    async def run_cortex_command(self, command: str, args: List[str] = None, timeout: int = 30) -> Dict[str, Any]:
        """Run a Cortex CLI command and return the result"""
        if args is None:
            args = []

        try:
            cmd_args = [sys.executable, str(self.cortex_cli_path), command] + args

            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=timeout
            )

            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timeout after {timeout} seconds",
                "success": False
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command execution error: {str(e)}",
                "success": False
            }

# Create server instance
cortex_server = CortexMCPServer()

# Define handler functions
async def handle_list_resources() -> List[Resource]:
    """List all available Cortex resources"""
    return [
        Resource(
            uri="cortex://status",
            name="Cortex System Status",
            description="Current status of the Cortex system and Neo4j database",
            mimeType="text/plain",
        ),
        Resource(
            uri="cortex://knowledge-graph",
            name="Knowledge Graph Overview",
            description="Overview of the Cortex knowledge graph structure and content",
            mimeType="application/json",
        ),
        Resource(
            uri="cortex://templates",
            name="Available Templates",
            description="List of available knowledge templates",
            mimeType="application/json",
        ),
        Resource(
            uri="cortex://links",
            name="Knowledge Links",
            description="Overview of knowledge links and relationships",
            mimeType="application/json",
        ),
        Resource(
            uri="cortex://help",
            name="Cortex Help",
            description="Available commands and usage information",
            mimeType="text/plain",
        ),
        Resource(
            uri="cortex://config",
            name="System Configuration",
            description="Current system configuration and settings",
            mimeType="application/json",
        ),
    ]

async def handle_read_resource(uri: str) -> str:
    """Read a specific Cortex resource"""

    if uri == "cortex://status":
        if not cortex_server.is_cortex_cli_available():
            return "Cortex CLI not available - please check installation"

        result = await cortex_server.run_cortex_command("status")
        if result["success"]:
            return result["stdout"] or "Cortex system is operational"
        else:
            return f"Status check failed: {result['stderr']}"

    elif uri == "cortex://knowledge-graph":
        result = await cortex_server.run_cortex_command("graph-info")
        if result["success"]:
            return result["stdout"] or '{"status": "Graph information not available"}'
        else:
            return f'{{"error": "Failed to get graph info", "details": "{result["stderr"]}"}}'

    elif uri == "cortex://templates":
        result = await cortex_server.run_cortex_command("template-list")
        if result["success"]:
            return result["stdout"] or '{"templates": []}'
        else:
            return f'{{"error": "Failed to list templates", "details": "{result["stderr"]}"}}'

    elif uri == "cortex://links":
        result = await cortex_server.run_cortex_command("link-list")
        if result["success"]:
            return result["stdout"] or '{"links": []}'
        else:
            return f'{{"error": "Failed to list links", "details": "{result["stderr"]}"}}'

    elif uri == "cortex://help":
        help_text = """
Cortex MCP Server - Available Commands and Resources

Resources:
- cortex://status - System status and health check
- cortex://knowledge-graph - Knowledge graph overview
- cortex://templates - Available knowledge templates
- cortex://links - Knowledge links and relationships
- cortex://help - This help information
- cortex://config - System configuration

Tools:
- cortex_run_command - Execute any Cortex CLI command
- cortex_status - Quick system status check
- cortex_add_knowledge - Add new knowledge to the graph
- cortex_search_knowledge - Search existing knowledge
- cortex_create_template - Create a new knowledge template
- cortex_link_knowledge - Create links between knowledge items
- cortex_export_data - Export knowledge data
- cortex_import_data - Import knowledge data
- cortex_backup_system - Create system backup
- cortex_validate_links - Validate knowledge links

Usage Examples:
- Ask Claude: "What's the current status of Cortex?"
- Ask Claude: "Add new knowledge about machine learning"
- Ask Claude: "Search for information about Python"
- Ask Claude: "Create a backup of the knowledge graph"
        """.strip()
        return help_text

    elif uri == "cortex://config":
        try:
            config_data = {
                "project_root": str(cortex_server.project_root),
                "cortex_cli_available": cortex_server.is_cortex_cli_available(),
                "cortex_cli_path": str(cortex_server.cortex_cli_path),
                "mcp_server_version": "1.0.0",
                "mcp_available": MCP_AVAILABLE,
                "features": {
                    "knowledge_graph": True,
                    "templates": True,
                    "links": True,
                    "export_import": True,
                    "backup": True,
                    "ai_integration": True
                }
            }
            return json.dumps(config_data, indent=2)
        except Exception as e:
            return f'{{"error": "Failed to get configuration", "details": "{str(e)}"}}'

    else:
        raise ValueError(f"Unknown resource: {uri}")

async def handle_list_tools() -> List[Tool]:
    """List all available Cortex tools"""
    return [
        Tool(
            name="cortex_run_command",
            description="Execute any Cortex CLI command with arguments",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The Cortex CLI command to execute (e.g., 'status', 'graph-info', 'template-list')",
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional arguments for the command",
                        "default": [],
                    },
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="cortex_status",
            description="Get current system status and health information",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="cortex_add_knowledge",
            description="Add new knowledge to the Cortex knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the knowledge item",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content of the knowledge item",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category for the knowledge item",
                        "default": "general",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for the knowledge item",
                        "default": [],
                    },
                },
                "required": ["title", "content"],
            },
        ),
        Tool(
            name="cortex_search_knowledge",
            description="Search for existing knowledge in the graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category (optional)",
                        "default": "",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="cortex_create_template",
            description="Create a new knowledge template",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Template name",
                    },
                    "structure": {
                        "type": "object",
                        "description": "Template structure definition",
                    },
                },
                "required": ["name", "structure"],
            },
        ),
        Tool(
            name="cortex_link_knowledge",
            description="Create links between knowledge items",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_id": {
                        "type": "string",
                        "description": "ID of the source knowledge item",
                    },
                    "target_id": {
                        "type": "string",
                        "description": "ID of the target knowledge item",
                    },
                    "relationship": {
                        "type": "string",
                        "description": "Type of relationship",
                        "default": "related_to",
                    },
                },
                "required": ["source_id", "target_id"],
            },
        ),
        Tool(
            name="cortex_export_data",
            description="Export knowledge data in various formats",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["json", "yaml", "csv"],
                        "description": "Export format",
                        "default": "json",
                    },
                    "filter": {
                        "type": "string",
                        "description": "Filter criteria (optional)",
                        "default": "",
                    },
                },
            },
        ),
        Tool(
            name="cortex_import_data",
            description="Import knowledge data from files",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the import file",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "yaml", "csv"],
                        "description": "Import format",
                        "default": "json",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="cortex_backup_system",
            description="Create a backup of the Cortex system",
            inputSchema={
                "type": "object",
                "properties": {
                    "backup_name": {
                        "type": "string",
                        "description": "Name for the backup (optional)",
                        "default": "",
                    },
                },
            },
        ),
        Tool(
            name="cortex_validate_links",
            description="Validate knowledge links and relationships",
            inputSchema={
                "type": "object",
                "properties": {
                    "fix_errors": {
                        "type": "boolean",
                        "description": "Attempt to fix validation errors",
                        "default": False,
                    },
                },
            },
        ),
    ]

async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a Cortex tool"""

    if name == "cortex_run_command":
        command = arguments.get("command", "")
        args = arguments.get("args", [])

        if not command:
            return [TextContent(type="text", text="Error: Command is required")]

        result = await cortex_server.run_cortex_command(command, args)

        if result["success"]:
            output = result["stdout"] or "Command executed successfully"
        else:
            output = f"Command failed: {result['stderr']}"

        return [TextContent(type="text", text=output)]

    elif name == "cortex_status":
        result = await cortex_server.run_cortex_command("status")

        if result["success"]:
            status = result["stdout"] or "Cortex system is operational"
        else:
            status = f"Status check failed: {result['stderr']}"

        return [TextContent(type="text", text=status)]

    elif name == "cortex_add_knowledge":
        title = arguments.get("title", "")
        content = arguments.get("content", "")
        category = arguments.get("category", "general")
        tags = arguments.get("tags", [])

        if not title or not content:
            return [TextContent(type="text", text="Error: Title and content are required")]

        # Use the knowledge-add CLI command
        args = ["--title", title, "--content", content, "--category", category]
        if tags:
            args.extend(["--tags", ",".join(tags)])

        result = await cortex_server.run_cortex_command("knowledge-add", args)

        if result["success"]:
            output = f"Knowledge added successfully: '{title}'"
        else:
            output = f"Failed to add knowledge: {result['stderr']}"

        return [TextContent(type="text", text=output)]

    elif name == "cortex_search_knowledge":
        query = arguments.get("query", "")
        category = arguments.get("category", "")
        limit = arguments.get("limit", 10)

        if not query:
            return [TextContent(type="text", text="Error: Query is required")]

        args = ["--query", query, "--limit", str(limit)]
        if category:
            args.extend(["--category", category])

        result = await cortex_server.run_cortex_command("knowledge-search", args)

        if result["success"]:
            output = result["stdout"] or "No results found"
        else:
            output = f"Search failed: {result['stderr']}"

        return [TextContent(type="text", text=output)]

    elif name == "cortex_create_template":
        name = arguments.get("name", "")
        structure = arguments.get("structure", {})

        if not name or not structure:
            return [TextContent(type="text", text="Error: Name and structure are required")]

        # Convert structure to JSON string
        import json
        structure_json = json.dumps(structure)

        result = await cortex_server.run_cortex_command("template-create", ["--name", name, "--structure", structure_json])

        if result["success"]:
            output = f"Template created successfully: '{name}'"
        else:
            output = f"Failed to create template: {result['stderr']}"

        return [TextContent(type="text", text=output)]

    elif name == "cortex_link_knowledge":
        source_id = arguments.get("source_id", "")
        target_id = arguments.get("target_id", "")
        relationship = arguments.get("relationship", "related_to")

        if not source_id or not target_id:
            return [TextContent(type="text", text="Error: Source and target IDs are required")]

        result = await cortex_server.run_cortex_command("link-create", ["--source", source_id, "--target", target_id, "--relationship", relationship])

        if result["success"]:
            output = f"Link created successfully between '{source_id}' and '{target_id}'"
        else:
            output = f"Failed to create link: {result['stderr']}"

        return [TextContent(type="text", text=output)]

    elif name == "cortex_export_data":
        format = arguments.get("format", "json")
        filter = arguments.get("filter", "")

        result = await cortex_server.run_cortex_command("data-export", ["--format", format, "--filter", filter])

        if result["success"]:
            output = f"Data exported successfully in {format} format"
        else:
            output = f"Failed to export data: {result['stderr']}"

        return [TextContent(type="text", text=output)]

    elif name == "cortex_import_data":
        file_path = arguments.get("file_path", "")
        format = arguments.get("format", "json")

        if not file_path:
            return [TextContent(type="text", text="Error: File path is required")]

        result = await cortex_server.run_cortex_command("data-import", ["--file", file_path, "--format", format])

        if result["success"]:
            output = f"Data imported successfully from '{file_path}'"
        else:
            output = f"Failed to import data: {result['stderr']}"

        return [TextContent(type="text", text=output)]

    elif name == "cortex_backup_system":
        backup_name = arguments.get("backup_name", "")

        result = await cortex_server.run_cortex_command("system-backup", ["--name", backup_name])

        if result["success"]:
            output = f"System backup created successfully"
        else:
            output = f"Failed to create backup: {result['stderr']}"

        return [TextContent(type="text", text=output)]

    elif name == "cortex_validate_links":
        fix_errors = arguments.get("fix_errors", False)

        result = await cortex_server.run_cortex_command("links-validate", ["--fix-errors" if fix_errors else "--dry-run"])

        if result["success"]:
            output = "Links validated successfully"
        else:
            output = f"Failed to validate links: {result['stderr']}"

        return [TextContent(type="text", text=output)]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

# Register handlers with server if MCP is available
if MCP_AVAILABLE:
    server.list_resources()(handle_list_resources)
    server.read_resource()(handle_read_resource)
    server.list_tools()(handle_list_tools)
    server.call_tool()(handle_call_tool)

async def main():
    """Main function to start the unified MCP server"""
    if not MCP_AVAILABLE:
        print("Error: MCP modules are not available. Please install with: pip install mcp", file=sys.stderr)
        sys.exit(1)

    try:
        # Use stdio transport for MCP communication
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="cortex-py-unified",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    except KeyboardInterrupt:
        print("\nMCP Server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"MCP Server error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            print(__doc__)
            sys.exit(0)
        elif sys.argv[1] in ["--version", "-v"]:
            print("Cortex MCP Server v1.0.0")
            sys.exit(0)

    # Start the server
    asyncio.run(main())
