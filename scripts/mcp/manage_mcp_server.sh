#!/bin/bash
# MCP Server Management Script
# Provides utilities for managing the Cortex MCP server

set -e

PROJECT_ROOT="/Users/simonjanke/Projects/cortex-py"
MCP_SERVER_PATH="$PROJECT_ROOT/src/mcp/cortex_mcp_server.py"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

case "$1" in
    "start")
        echo -e "${GREEN}Starting MCP server...${NC}"
        exec "$PROJECT_ROOT/scripts/mcp/start_mcp_cortex_server.sh"
        ;;
    "stop")
        echo -e "${YELLOW}Stopping MCP server...${NC}"
        pkill -f "cortex_mcp_server.py" || true
        echo -e "${GREEN}MCP server stopped${NC}"
        ;;
    "status")
        echo -e "${YELLOW}Checking MCP server status...${NC}"
        if pgrep -f "cortex_mcp_server.py" > /dev/null; then
            echo -e "${GREEN}✅ MCP server is running${NC}"
        else
            echo -e "${RED}❌ MCP server is not running${NC}"
        fi
        ;;
    "test")
        echo -e "${YELLOW}Testing MCP server functionality...${NC}"
        python3 -c "import src.mcp.cortex_mcp_server; print('✅ MCP server module loads successfully')" 2>/dev/null || echo "❌ MCP server module failed to load"
        ;;
    *)
        echo "Usage: $0 {start|stop|status|test}"
        exit 1
        ;;
esac
