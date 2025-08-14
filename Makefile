# Cortex-py Knowledge Management System Makefile

.PHONY: help install test status claude-restart cleanup

help:
	@echo "🧠 Cortex-py Knowledge Management System"
	@echo ""
	@echo "Verfügbare Befehle:"
	@echo "  make install       - Installiert alle Dependencies"
	@echo "  make test          - Testet den MCP Server"
	@echo "  make status        - Zeigt System-Status"
	@echo "  make claude-restart - Startet Claude Desktop neu für MCP Integration"
	@echo "  make cleanup       - Bereinigt temporäre Dateien"
	@echo ""
	@echo "🔧 Content Management (CLI):"
	@echo "  python3 cortex_neo/cortex_cli.py --help"
	@echo ""
	@echo "🤖 AI Features:"
	@echo "  python3 cortex_neo/cortex_cli.py ai-suggest-tags"
	@echo "  python3 cortex_neo/cortex_cli.py auto-link-by-content"
	@echo ""

install:
	@echo "📦 Installiere Cortex-py Dependencies..."
	pip install -r requirements.txt
	@echo "✅ Installation abgeschlossen"

test:
	@echo "🧪 Teste MCP Server..."
	python3 -m py_compile mcp_cortex_server_simple.py
	@echo "✅ MCP Server Syntax ist korrekt"

status:
	@echo "📊 Cortex-py System Status:"
	@echo "📁 MCP Server: mcp_cortex_server_simple.py"
	@if [ -f ~/Library/Application\ Support/Claude/claude_desktop_config.json ]; then \
		echo "✅ Claude Desktop Konfiguration gefunden"; \
	else \
		echo "❌ Claude Desktop Konfiguration fehlt"; \
	fi
	@echo "🔧 Integration: STDIO-basiert (MCP)"
	@echo "💡 MCP Server wird automatisch von Claude Desktop gestartet"

claude-restart:
	@echo "🔄 Starte Claude Desktop neu für MCP Integration..."
	./restart_claude_desktop.sh

cleanup:
	@echo "🧹 Bereinige temporäre Dateien..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Bereinigung abgeschlossen"
