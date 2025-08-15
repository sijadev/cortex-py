#!/usr/bin/env python3
import mcp
print("MCP module location:", mcp.__file__)
print("MCP module contents:", dir(mcp))

try:
    import mcp.server
    print("mcp.server available")
    print("mcp.server contents:", dir(mcp.server))
except ImportError as e:
    print("mcp.server not available:", e)

try:
    from mcp.server import Server
    print("Server class available")
except ImportError as e:
    print("Server class not available:", e)
