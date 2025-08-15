#!/bin/bash
# MCP Cortex Server Start Script
# This script starts the unified Cortex MCP server for Claude Desktop integration

set -e

# Configuration
PROJECT_ROOT="/Users/simonjanke/Projects/cortex-py"
MCP_SERVER_PATH="$PROJECT_ROOT/src/mcp/cortex_mcp_server.py"
PYTHON_EXEC=${PYTHON_EXEC:-python3}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Cortex MCP Server..."

# Check if MCP server file exists
if [ ! -f "$MCP_SERVER_PATH" ]; then
    echo -e "${RED}❌ Error: MCP server file not found at $MCP_SERVER_PATH${NC}"
    exit 1
fi

# Check if Python is available
if ! command -v $PYTHON_EXEC &> /dev/null; then
    echo -e "${RED}❌ Error: Python not found. Please ensure Python 3.8+ is installed.${NC}"
    exit 1
fi

# Set up environment
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export NEO4J_URI=${NEO4J_URI:-"bolt://localhost:7687"}
export NEO4J_USER=${NEO4J_USER:-"neo4j"}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-"neo4jtest"}

echo -e "${GREEN}✅ Environment configured${NC}"
echo "   - Project root: $PROJECT_ROOT"
echo "   - Python: $PYTHON_EXEC"
echo "   - Neo4j URI: $NEO4J_URI"

# Start the MCP server
echo -e "${YELLOW}🔄 Starting MCP server...${NC}"
cd "$PROJECT_ROOT"

exec $PYTHON_EXEC "$MCP_SERVER_PATH" "$@"
