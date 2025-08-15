"""
Cortex MCP Server Package - Unified Model Context Protocol integration for Cortex
===============================================================================

This package provides a unified MCP server implementation that combines all
MCP functionality for Cortex integration with Claude Desktop.

The unified server provides:
- Complete Cortex CLI integration
- Knowledge graph resource management
- Template and link management tools
- Export/import functionality
- System backup and validation tools
"""

# Import the unified server implementation
try:
    from .cortex_mcp_server import server, main, CortexMCPServer

    # Export the main components
    __all__ = ["server", "main", "CortexMCPServer"]

    # Version information
    __version__ = "1.0.0"

    # Default server is now the unified implementation
    default_server = server

    # Backward compatibility aliases
    main_server = server
    simple_server = server  # Both point to the same unified server

except ImportError as e:
    # Fallback if MCP modules are not available
    print(f"Warning: MCP modules not fully available: {e}")
    __all__ = []
    __version__ = "1.0.0"
    server = None
    main = None
