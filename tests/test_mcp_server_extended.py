#!/usr/bin/env python3
"""
Erweiterte MCP Server Tests

Diese Tests decken spezifische MCP Server Szenarien ab:
- Server-Lifecycle Management
- Protokoll-Compliance
- Performance-Tests
- Claude Desktop Integration
"""

import asyncio
import json
import pytest
import subprocess
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import os

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

# Try to import MCP server modules
try:
    import mcp_cortex_server
    import mcp_cortex_server_simple
except ImportError:
    mcp_cortex_server = None
    mcp_cortex_server_simple = None

@pytest.mark.asyncio
class TestMCPServerProtocol:
    """Tests für MCP Protokoll-Compliance"""

    async def test_server_capabilities(self):
        """Teste dass Server die richtigen Capabilities meldet"""
        try:
            import mcp_cortex_server
            server = mcp_cortex_server.server

            # Server sollte grundlegende MCP Capabilities haben
            assert hasattr(server, '_handlers')

            # Teste dass alle erforderlichen Handler registriert sind
            handlers = server._handlers
            expected_handlers = ['list_resources', 'read_resource', 'list_tools', 'call_tool']

            for handler in expected_handlers:
                assert any(handler in str(h) for h in handlers), f"Handler {handler} nicht gefunden"

        except ImportError:
            pytest.skip("MCP Server nicht verfügbar")

    async def test_resource_uri_format(self):
        """Teste dass Ressourcen-URIs dem korrekten Format entsprechen"""
        try:
            import mcp_cortex_server
            resources = await mcp_cortex_server.handle_list_resources()

            for resource in resources:
                # URIs sollten mit cortex:// beginnen
                assert resource.uri.startswith("cortex://"), f"Ungültiges URI Format: {resource.uri}"

                # URIs sollten keine Leerzeichen enthalten
                assert " " not in resource.uri, f"URI enthält Leerzeichen: {resource.uri}"

                # Basis-Felder sollten vorhanden sein
                assert resource.name, "Ressource hat keinen Namen"
                assert resource.description, "Ressource hat keine Beschreibung"
                assert resource.mimeType, "Ressource hat keinen mimeType"

        except ImportError:
            pytest.skip("MCP Server nicht verfügbar")

    async def test_tool_input_schemas(self):
        """Teste dass Tool Input Schemas JSON Schema konform sind"""
        try:
            import mcp_cortex_server
            tools = await mcp_cortex_server.handle_list_tools()

            for tool in tools:
                schema = tool.inputSchema

                # Basis JSON Schema Felder
                assert schema.get("type") == "object", f"Tool {tool.name} hat ungültigen Schema-Type"
                assert "properties" in schema, f"Tool {tool.name} hat keine properties"

                # Required fields sollten in properties definiert sein
                if "required" in schema:
                    for required_field in schema["required"]:
                        assert required_field in schema["properties"], \
                            f"Required field {required_field} nicht in properties für {tool.name}"

        except ImportError:
            pytest.skip("MCP Server nicht verfügbar")

@pytest.mark.asyncio
class TestMCPServerLifecycle:
    """Tests für Server Lifecycle Management"""

    async def test_server_startup_sequence(self):
        """Teste Server Startup Sequenz"""
        try:
            from mcp.server import Server

            # Erstelle neuen Test-Server
            test_server = Server("test-cortex-lifecycle")
            assert test_server is not None

            # Server sollte initial keine aktiven Verbindungen haben
            assert hasattr(test_server, '_handlers')

        except ImportError:
            pytest.skip("MCP Bibliothek nicht verfügbar")

    @patch('subprocess.run')
    async def test_resource_availability_check(self, mock_subprocess):
        """Teste dass Ressourcen verfügbar sind bevor sie gelesen werden"""
        try:
            import mcp_cortex_server

            # Mock verfügbares System
            mock_result = Mock()
            mock_result.stdout = "System verfügbar"
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result

            result = await mcp_cortex_server.handle_read_resource("cortex://status")
            assert result is not None
            assert len(result) > 0

        except ImportError:
            pytest.skip("MCP Server nicht verfügbar")

    @patch('subprocess.run')
    async def test_graceful_degradation(self, mock_subprocess):
        """Teste graceful degradation wenn Backend nicht verfügbar ist"""
        try:
            import mcp_cortex_server_simple

            # Mock nicht verfügbares System
            mock_subprocess.side_effect = subprocess.TimeoutExpired("python3", 10)

            result = await mcp_cortex_server_simple.handle_read_resource("cortex://status")

            # Server sollte trotzdem eine Antwort liefern
            assert result is not None
            assert "CLI nicht verfügbar" in result or "System bereit" in result

        except ImportError:
            pytest.skip("MCP Simple Server nicht verfügbar")

@pytest.mark.asyncio
class TestMCPServerPerformance:
    """Performance Tests für MCP Server"""

    @patch('subprocess.run')
    async def test_concurrent_tool_calls(self, mock_subprocess):
        """Teste gleichzeitige Tool-Aufrufe"""
        try:
            import mcp_cortex_server

            # Mock schnelle Antworten
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Quick response"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Führe mehrere gleichzeitige Tool-Aufrufe aus
            tasks = []
            for i in range(5):
                task = mcp_cortex_server.handle_call_tool(
                    "cortex_run_command",
                    {"command": f"test-command-{i}"}
                )
                tasks.append(task)

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # Alle Aufrufe sollten erfolgreich sein
            assert len(results) == 5
            for result in results:
                assert isinstance(result, list)
                assert len(result) > 0

            # Performance-Check: sollte unter 2 Sekunden dauern
            assert end_time - start_time < 2.0, "Concurrent calls zu langsam"

        except ImportError:
            pytest.skip("MCP Server nicht verfügbar")

    @patch('subprocess.run')
    async def test_large_response_handling(self, mock_subprocess):
        """Teste Handling großer Antworten"""
        try:
            import mcp_cortex_server

            # Mock große Antwort
            large_response = "A" * 10000  # 10KB Antwort
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = large_response
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            result = await mcp_cortex_server.handle_call_tool(
                "cortex_run_command",
                {"command": "large-output-command"}
            )

            assert isinstance(result, list)
            assert len(result) > 0
            assert len(result[0].text) > 5000  # Sollte große Antwort enthalten

        except ImportError:
            pytest.skip("MCP Server nicht verfügbar")

@pytest.mark.asyncio
class TestMCPServerErrorScenarios:
    """Tests für verschiedene Fehlerszenarien"""

    @patch('subprocess.run')
    async def test_command_timeout_handling(self, mock_subprocess):
        """Teste Timeout-Handling bei langsamen Kommandos"""
        try:
            import mcp_cortex_server_simple

            # Mock Timeout
            mock_subprocess.side_effect = subprocess.TimeoutExpired("python3", 10)

            result = await mcp_cortex_server_simple.handle_read_resource("cortex://status")

            # Sollte graceful mit Timeout umgehen
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0

        except ImportError:
            pytest.skip("MCP Simple Server nicht verfügbar")

    async def test_malformed_tool_arguments(self):
        """Teste Verhalten bei fehlerhaften Tool-Argumenten"""
        try:
            import mcp_cortex_server

            # Test mit fehlenden required arguments
            result = await mcp_cortex_server.handle_call_tool(
                "cortex_add_knowledge",
                {"title": "Test"}  # content fehlt
            )

            # Server sollte nicht crashen
            assert result is not None

            # Test mit ungültigen Argument-Typen
            result = await mcp_cortex_server.handle_call_tool(
                "cortex_search",
                {"query": 123, "limit": "invalid"}  # Falsche Typen
            )

            assert result is not None

        except ImportError:
            pytest.skip("MCP Server nicht verfügbar")

    @patch('subprocess.run')
    async def test_system_resource_exhaustion(self, mock_subprocess):
        """Teste Verhalten bei Systemressourcen-Erschöpfung"""
        try:
            import mcp_cortex_server

            # Mock System-Fehler
            mock_subprocess.side_effect = OSError("Resource temporarily unavailable")

            result = await mcp_cortex_server.handle_call_tool(
                "cortex_run_command",
                {"command": "status"}
            )

            assert isinstance(result, list)
            assert len(result) > 0
            assert "Fehler" in result[0].text

        except ImportError:
            pytest.skip("MCP Server nicht verfügbar")

class TestMCPServerConfiguration:
    """Tests für MCP Server Konfiguration"""

    def test_claude_desktop_config_valid(self):
        """Teste dass Claude Desktop Konfiguration gültig ist"""
        config_path = Path(__file__).parent.parent / "config" / "claude_desktop_config.json"

        if not config_path.exists():
            pytest.skip("Claude Desktop Config nicht gefunden")

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Basis-Struktur prüfen
            assert "mcpServers" in config, "mcpServers Sektion fehlt"

            mcp_servers = config["mcpServers"]
            assert isinstance(mcp_servers, dict), "mcpServers sollte ein Dict sein"

            # Cortex Server Konfiguration prüfen
            cortex_configs = [name for name in mcp_servers.keys() if "cortex" in name.lower()]
            assert len(cortex_configs) > 0, "Keine Cortex MCP Server Konfiguration gefunden"

            for server_name in cortex_configs:
                server_config = mcp_servers[server_name]
                assert "command" in server_config, f"Command fehlt für {server_name}"
                assert "args" in server_config, f"Args fehlen für {server_name}"

        except json.JSONDecodeError as e:
            pytest.fail(f"Ungültiges JSON in Claude Desktop Config: {e}")

    def test_start_script_executable(self):
        """Teste dass Start-Skripte ausführbar sind"""
        scripts_dir = Path(__file__).parent.parent / "scripts"

        start_scripts = list(scripts_dir.glob("start_mcp_*.sh"))
        assert len(start_scripts) > 0, "Keine MCP Start-Skripte gefunden"

        for script in start_scripts:
            # Prüfe dass Skript existiert und ausführbar ist
            assert script.exists(), f"Start-Skript nicht gefunden: {script}"
            assert os.access(script, os.X_OK), f"Start-Skript nicht ausführbar: {script}"

class TestMCPServerDocumentation:
    """Tests für MCP Server Dokumentation"""

    def test_mcp_documentation_exists(self):
        """Teste dass MCP Dokumentation vorhanden ist"""
        docs_dir = Path(__file__).parent.parent / "docs"

        mcp_docs = list(docs_dir.glob("*MCP*.md"))
        assert len(mcp_docs) > 0, "Keine MCP Dokumentation gefunden"

        for doc in mcp_docs:
            assert doc.stat().st_size > 100, f"Dokumentation zu kurz: {doc}"

    def test_readme_mentions_mcp(self):
        """Teste dass README MCP Server erwähnt"""
        readme_path = Path(__file__).parent.parent / "README.md"

        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Sollte MCP erwähnen
            assert any(term in content.lower() for term in ["mcp", "model context protocol"]), \
                "README erwähnt MCP nicht"

# Integration Test Runner
def run_extended_mcp_tests():
    """Führe erweiterte MCP Tests aus"""
    print("🔧 Starte erweiterte MCP Server Tests...")

    test_result = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
        "--durations=10"
    ])

    if test_result == 0:
        print("✅ Alle erweiterten MCP Tests erfolgreich!")
    else:
        print("❌ Einige erweiterte MCP Tests fehlgeschlagen!")

    return test_result

if __name__ == "__main__":
    run_extended_mcp_tests()
