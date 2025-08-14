#!/usr/bin/env python3
"""
Test Suite für den Cortex MCP Server

Diese Tests validieren die MCP Server Funktionalität:
- Server-Initialisierung
- Ressourcen-Handling
- Tool-Funktionen
- Kommando-Ausführung
- Fehlerbehandlung
"""

import asyncio
import json
import pytest
import subprocess
import sys
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importiere MCP-spezifische Komponenten
try:
    from mcp.types import Resource, Tool, TextContent
    from mcp.server import Server
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Mock MCP types wenn nicht verfügbar
if not MCP_AVAILABLE:
    class Resource:
        def __init__(self, uri, name, description, mimeType):
            self.uri = uri
            self.name = name
            self.description = description
            self.mimeType = mimeType

    class Tool:
        def __init__(self, name, description, inputSchema):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema

    class TextContent:
        def __init__(self, type, text):
            self.type = type
            self.text = text

# Versuche MCP Server zu importieren
try:
    import mcp_cortex_server
    import mcp_cortex_server_simple
except ImportError:
    mcp_cortex_server = None
    mcp_cortex_server_simple = None

@pytest.mark.asyncio
class TestMCPServerCore:
    """Tests für grundlegende MCP Server Funktionalität"""

    async def test_mcp_library_available(self):
        """Teste ob MCP-Bibliothek verfügbar ist"""
        try:
            import mcp
            assert True, "MCP Bibliothek ist verfügbar"
        except ImportError:
            pytest.skip("MCP Bibliothek ist nicht installiert")

    async def test_server_initialization(self):
        """Teste MCP Server Initialisierung"""
        if not MCP_AVAILABLE:
            pytest.skip("MCP Bibliothek nicht verfügbar")

        server = Server("test-cortex")
        assert server is not None
        assert hasattr(server, 'list_resources')
        assert hasattr(server, 'read_resource')
        assert hasattr(server, 'list_tools')
        assert hasattr(server, 'call_tool')

@pytest.mark.asyncio
class TestMCPServerResources:
    """Tests für MCP Server Ressourcen-Management"""

    async def test_list_resources_structure(self):
        """Teste dass Ressourcen korrekt definiert sind"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        resources = await mcp_cortex_server.handle_list_resources()

        assert isinstance(resources, list)
        assert len(resources) >= 2

        # Teste Ressourcen-Struktur
        status_resource = next((r for r in resources if str(r.uri) == "cortex://status"), None)
        assert status_resource is not None
        assert status_resource.name == "Cortex Status"
        assert status_resource.mimeType == "text/plain"

        graph_resource = next((r for r in resources if str(r.uri) == "cortex://knowledge-graph"), None)
        assert graph_resource is not None
        assert graph_resource.name == "Knowledge Graph Overview"

    @patch('subprocess.run')
    async def test_read_status_resource(self, mock_subprocess):
        """Teste das Lesen der Status-Ressource"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        # Mock erfolgreiches Kommando
        mock_result = Mock()
        mock_result.stdout = "Cortex System: Aktiv\nNeo4j: Verbunden"
        mock_subprocess.return_value = mock_result

        result = await mcp_cortex_server.handle_read_resource("cortex://status")
        assert "Cortex System: Aktiv" in result
        mock_subprocess.assert_called_once()

    @patch('subprocess.run')
    async def test_read_knowledge_graph_resource(self, mock_subprocess):
        """Teste das Lesen der Knowledge Graph Ressource"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        # Mock erfolgreiches Kommando
        mock_result = Mock()
        mock_result.stdout = '{"nodes": 10, "relationships": 25}'
        mock_subprocess.return_value = mock_result

        result = await mcp_cortex_server.handle_read_resource("cortex://knowledge-graph")
        assert "nodes" in result
        mock_subprocess.assert_called_once()

    async def test_read_invalid_resource(self):
        """Teste Fehlerbehandlung bei ungültiger Ressource"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        with pytest.raises(ValueError) as excinfo:
            await mcp_cortex_server.handle_read_resource("cortex://invalid")
        assert "Unbekannte Ressource" in str(excinfo.value)

@pytest.mark.asyncio
class TestMCPServerTools:
    """Tests für MCP Server Tool-Funktionalität"""

    async def test_list_tools_structure(self):
        """Teste dass Tools korrekt definiert sind"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        tools = await mcp_cortex_server.handle_list_tools()

        assert isinstance(tools, list)
        assert len(tools) >= 3

        tool_names = [tool.name for tool in tools]
        assert "cortex_run_command" in tool_names
        assert "cortex_add_knowledge" in tool_names
        assert "cortex_search" in tool_names

    async def test_tool_schemas_valid(self):
        """Teste dass Tool-Schemas gültig sind"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        tools = await mcp_cortex_server.handle_list_tools()

        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')

            schema = tool.inputSchema
            assert isinstance(schema, dict)
            assert 'type' in schema
            assert 'properties' in schema
            assert schema['type'] == 'object'

    @patch('subprocess.run')
    async def test_cortex_run_command_tool(self, mock_subprocess):
        """Teste das cortex_run_command Tool"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        # Mock erfolgreiches Kommando
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Command executed successfully"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        result = await mcp_cortex_server.handle_call_tool(
            "cortex_run_command",
            {"command": "status", "args": []}
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Command executed successfully" in result[0].text
        mock_subprocess.assert_called_once()

    @patch('subprocess.run')
    async def test_cortex_add_knowledge_tool(self, mock_subprocess):
        """Teste das cortex_add_knowledge Tool"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        # Mock erfolgreiches Kommando
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Knowledge added successfully"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        result = await mcp_cortex_server.handle_call_tool(
            "cortex_add_knowledge",
            {
                "title": "Test Knowledge",
                "content": "This is test content",
                "category": "test"
            }
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Test Knowledge" in result[0].text
        mock_subprocess.assert_called_once()

    @patch('subprocess.run')
    async def test_cortex_search_tool(self, mock_subprocess):
        """Teste das cortex_search Tool"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        # Mock erfolgreiches Kommando
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Search results: Found 3 items"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        result = await mcp_cortex_server.handle_call_tool(
            "cortex_search",
            {"query": "test query", "limit": 5}
        )

        assert isinstance(result, list)
        assert len(result) > 0
        mock_subprocess.assert_called_once()

@pytest.mark.asyncio
class TestMCPServerErrorHandling:
    """Tests für MCP Server Fehlerbehandlung"""

    @patch('subprocess.run')
    async def test_command_execution_failure(self, mock_subprocess):
        """Teste Verhalten bei fehlgeschlagenen Kommandos"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        # Mock fehlgeschlagenes Kommando
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Command failed with error"
        mock_subprocess.return_value = mock_result

        result = await mcp_cortex_server.handle_call_tool(
            "cortex_run_command",
            {"command": "invalid-command"}
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Command failed with error" in result[0].text

    @patch('subprocess.run')
    async def test_subprocess_exception_handling(self, mock_subprocess):
        """Teste Verhalten bei subprocess Exceptions"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        # Mock Exception
        mock_subprocess.side_effect = Exception("Subprocess error")

        result = await mcp_cortex_server.handle_call_tool(
            "cortex_run_command",
            {"command": "status"}
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Fehler beim Ausführen des Befehls" in result[0].text

    async def test_invalid_tool_name(self):
        """Teste Verhalten bei ungültigen Tool-Namen"""
        if not mcp_cortex_server:
            pytest.skip("MCP Server Modul nicht verfügbar")

        # Test should expect a ValueError for unknown tools
        with pytest.raises(ValueError) as excinfo:
            await mcp_cortex_server.handle_call_tool(
                "invalid_tool",
                {"some": "argument"}
            )
        assert "Unbekanntes Tool" in str(excinfo.value)

@pytest.mark.asyncio
class TestMCPSimpleServer:
    """Tests für den vereinfachten MCP Server"""

    async def test_simple_server_resources(self):
        """Teste Ressourcen des vereinfachten Servers"""
        if not mcp_cortex_server_simple:
            pytest.skip("MCP Simple Server Modul nicht verfügbar")

        resources = await mcp_cortex_server_simple.handle_list_resources()

        assert isinstance(resources, list)
        assert len(resources) >= 2

        # Convert URIs to strings to handle AnyUrl types
        uris = [str(r.uri) for r in resources]
        assert "cortex://status" in uris
        assert "cortex://knowledge-graph" in uris

    @patch('subprocess.run')
    async def test_simple_server_status_with_timeout(self, mock_subprocess):
        """Teste Status-Abfrage mit Timeout im vereinfachten Server"""
        if not mcp_cortex_server_simple:
            pytest.skip("MCP Simple Server Modul nicht verfügbar")

        # Mock erfolgreiches Kommando mit Timeout
        mock_result = Mock()
        mock_result.stdout = "Simple server status"
        mock_subprocess.return_value = mock_result

        result = await mcp_cortex_server_simple.handle_read_resource("cortex://status")

        assert isinstance(result, str)
        assert len(result) > 0

        # Verifiziere dass timeout Parameter gesetzt wurde
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert 'timeout' in call_args.kwargs
        assert call_args.kwargs['timeout'] == 10

class TestMCPServerIntegration:
    """Integration Tests für MCP Server"""

    def test_mcp_server_importable(self):
        """Teste ob MCP Server Module importierbar sind"""
        try:
            import mcp_cortex_server
            assert hasattr(mcp_cortex_server, 'server')
            assert hasattr(mcp_cortex_server, 'handle_list_resources')
        except ImportError:
            pytest.skip("MCP Server Modul nicht importierbar")

    def test_mcp_simple_server_importable(self):
        """Teste ob vereinfachter MCP Server importierbar ist"""
        try:
            import mcp_cortex_server_simple
            assert hasattr(mcp_cortex_server_simple, 'server')
            assert hasattr(mcp_cortex_server_simple, 'handle_list_resources')
        except ImportError:
            pytest.skip("MCP Simple Server Modul nicht importierbar")

    def test_subprocess_commands_available(self):
        """Teste ob benötigte Subprocess-Kommandos verfügbar sind"""
        project_root = Path(__file__).parent.parent
        cortex_cli_path = project_root / "cortex_neo" / "cortex_cli.py"

        assert cortex_cli_path.exists(), f"Cortex CLI nicht gefunden: {cortex_cli_path}"

        # Teste ob Python verfügbar ist
        try:
            result = subprocess.run(["python3", "--version"],
                                  capture_output=True, text=True, timeout=5)
            assert result.returncode == 0
        except Exception as e:
            pytest.fail(f"Python3 nicht verfügbar: {e}")

# Test Runner Utilities
def run_mcp_server_tests():
    """Führe alle MCP Server Tests aus"""
    print("🧠 Starte MCP Server Tests...")

    # Führe Tests aus
    test_result = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])

    if test_result == 0:
        print("✅ Alle MCP Server Tests erfolgreich!")
    else:
        print("❌ Einige MCP Server Tests fehlgeschlagen!")

    return test_result

if __name__ == "__main__":
    run_mcp_server_tests()
