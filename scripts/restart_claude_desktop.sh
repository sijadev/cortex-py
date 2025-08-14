#!/bin/bash
# Restart Claude Desktop to load new MCP configuration

echo "🔄 Restarting Claude Desktop to load new MCP configuration..."

# Kill Claude Desktop if running
pkill -f "Claude"

# Wait a moment
sleep 2

# Start Claude Desktop
echo "🚀 Starting Claude Desktop..."
open -a "Claude"

echo "✅ Claude Desktop should now be running with the updated Cortex MCP Server configuration"
echo "📝 The MCP server is configured at: mcp_cortex_server_simple.py"
echo "🔧 You can now use Cortex tools directly in Claude Desktop!"
