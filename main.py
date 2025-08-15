#!/usr/bin/env python3
"""
Cortex-py Main Entry Point
=========================

Clean, organized entry point for the cortex-py knowledge management system.
"""

import sys
import os

# Add src to Python path for clean imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main entry point for cortex-py"""
    print("🧠 Cortex-py Knowledge Management System")
    print("=" * 40)
    print("Available modules:")
    print("  • src/mcp/ - MCP Server integration")
    print("  • src/governance/ - Data governance engine")
    print("  • cortex_neo/ - Neo4j knowledge graph")
    print("  • cortex-cli/ - CLI tools")
    print("\nFor detailed usage, see docs/")

if __name__ == "__main__":
    main()
