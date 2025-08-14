#!/bin/bash

# Cortex MCP Server Starter mit Port-Management
# Verwendet das robuste Port-Management System

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANAGE_SCRIPT="$SCRIPT_DIR/manage_mcp_server.sh"

# Prüfe ob das Management-Script existiert
if [ ! -f "$MANAGE_SCRIPT" ]; then
    echo "❌ Port-Management Script nicht gefunden: $MANAGE_SCRIPT"
    exit 1
fi

# Verwende das Port-Management System
echo "🚀 Starte Cortex MCP Server mit Port-Management..."
exec "$MANAGE_SCRIPT" start "$@"
