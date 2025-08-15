#!/usr/bin/env python3
"""
Test the imports directly for the MCP server
"""

# Test if MCP imports work when run directly 
try:
    from mcp.server import Server
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
    print("✅ All MCP imports successful when run directly!")
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"❌ MCP imports failed when run directly: {e}")
    MCP_AVAILABLE = False

print(f"MCP_AVAILABLE = {MCP_AVAILABLE}")
