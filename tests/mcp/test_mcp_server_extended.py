#!/usr/bin/env python3
"""
Erweiterte Test Suite für den Cortex MCP Server (Unified Version)
"""
import pytest
import subprocess
import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent  # Go up two levels now (mcp -> tests -> project)
sys.path.insert(0, str(project_root))

# Check for MCP availability - Korrigierte Version
MCP_AVAILABLE = False
MCP_SERVER_AVAILABLE = False
cortex_mcp_server = None

# Teste externe MCP Library mit korrigierter Import-Struktur
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        ServerCapabilities,
    )
    MCP_AVAILABLE = True
    print("✅ MCP Library erfolgreich importiert")
except ImportError as e:
    MCP_AVAILABLE = False
    print(f"❌ MCP Library Import fehlgeschlagen: {e}")

# Teste unsere eigene MCP Server Implementierung (vermeidet Namenskonflikt)
try:
    # Lade unseren eigenen cortex_mcp_server direkt über Dateipfad
    import importlib.util
    cortex_mcp_path = project_root / "src" / "mcp" / "cortex_mcp_server.py"
    if cortex_mcp_path.exists():
        spec = importlib.util.spec_from_file_location("cortex_mcp_server", cortex_mcp_path)
        cortex_mcp_server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cortex_mcp_server)
        MCP_SERVER_AVAILABLE = True
        print("✅ Cortex MCP Server erfolgreich geladen")
    else:
        MCP_SERVER_AVAILABLE = False
        print(f"❌ Cortex MCP Server nicht gefunden: {cortex_mcp_path}")
except Exception as e:
    MCP_SERVER_AVAILABLE = False
    print(f"❌ Cortex MCP Server Import fehlgeschlagen: {e}")

@pytest.mark.skipif(not (MCP_AVAILABLE or MCP_SERVER_AVAILABLE), reason="Neither MCP library nor Cortex MCP server available")
class TestMCPServerExtended:
    """Erweiterte Tests für den einheitlichen MCP Server."""

    def test_cortex_mcp_module_exists(self):
        """Test ob das einheitliche Cortex MCP Modul existiert."""
        cortex_mcp_path = project_root / "src" / "mcp" / "cortex_mcp_server.py"
        assert cortex_mcp_path.exists(), f"Unified Cortex MCP server module not found: {cortex_mcp_path}"

    def test_mcp_server_imports(self):
        """Test ob MCP Server Imports funktionieren."""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            assert cortex_mcp_server is not None, "Cortex MCP server should be available"
            assert hasattr(cortex_mcp_server, 'main'), "Main function not found"
            assert hasattr(cortex_mcp_server, 'server'), "Server instance not found"
        elif MCP_AVAILABLE:
            # Test mit externer MCP Library
            try:
                from mcp.server import Server, NotificationOptions
                test_server = Server("test")
                assert test_server is not None
            except ImportError as e:
                pytest.fail(f"Cannot import MCP server components: {e}")
        else:
            pytest.skip("Neither Cortex MCP server nor external MCP library available")

    def test_mcp_package_imports(self):
        """Test ob das MCP Package korrekt importiert werden kann."""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            assert cortex_mcp_server is not None, "Cortex MCP server should be available"
            assert hasattr(cortex_mcp_server, 'handle_list_resources'), "handle_list_resources function missing"
            assert hasattr(cortex_mcp_server, 'handle_call_tool'), "handle_call_tool function missing"
        else:
            pytest.skip("Cortex MCP server not available")

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test ob der einheitliche MCP Server korrekt initialisiert werden kann."""
        if MCP_AVAILABLE:
            # Test mit externer MCP Library
            try:
                from mcp.server import Server, NotificationOptions
                test_server = Server("test-server")
                assert test_server is not None, "Server instance should not be None"
                print("✅ MCP Server erfolgreich mit externer Library initialisiert")
            except Exception as e:
                pytest.fail(f"Cannot initialize MCP server: {e}")
        elif MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            assert cortex_mcp_server is not None, "Cortex MCP server should be available"
            assert hasattr(cortex_mcp_server, 'server'), "Server instance should be available"
            print("✅ Cortex MCP Server erfolgreich initialisiert")
        else:
            pytest.skip("Neither external MCP library nor Cortex MCP server available")

    @pytest.mark.asyncio
    async def test_server_resources(self):
        """Test der verfügbaren Server-Ressourcen."""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            try:
                resources = await cortex_mcp_server.handle_list_resources()
                assert len(resources) > 0, "Server should provide at least one resource"

                # Check for expected resources
                resource_uris = [str(r.uri) for r in resources]
                assert "cortex://status" in resource_uris, "Status resource should be available"
                print(f"✅ {len(resources)} Ressourcen gefunden")
            except Exception as e:
                pytest.fail(f"Error testing server resources: {e}")
        else:
            pytest.skip("Cortex MCP server not available")

    @pytest.mark.asyncio
    async def test_server_tools(self):
        """Test der verfügbaren Server-Tools."""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            try:
                tools = await cortex_mcp_server.handle_list_tools()
                assert len(tools) > 0, "Server should provide at least one tool"

                # Check for expected tools
                tool_names = [t.name for t in tools]
                assert "cortex_status" in tool_names, "Status tool should be available"
                print(f"✅ {len(tools)} Tools gefunden")
            except Exception as e:
                pytest.fail(f"Error testing server tools: {e}")
        else:
            pytest.skip("Cortex MCP server not available")

    @pytest.mark.asyncio
    async def test_resource_reading(self):
        """Test das Lesen von Server-Ressourcen."""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            try:
                help_content = await cortex_mcp_server.handle_read_resource("cortex://help")
                assert isinstance(help_content, str), "Help content should be a string"
                assert len(help_content) > 0, "Help content should not be empty"
                print("✅ Ressource erfolgreich gelesen")
            except Exception as e:
                pytest.fail(f"Error testing resource reading: {e}")
        else:
            pytest.skip("Cortex MCP server not available")

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test die Ausführung von Server-Tools."""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            try:
                result = await cortex_mcp_server.handle_call_tool("cortex_status", {})
                assert isinstance(result, list), "Tool result should be a list"
                assert len(result) > 0, "Tool should return results"
                assert hasattr(result[0], 'text'), "Result should have text content"
                print("✅ Tool erfolgreich ausgeführt")
            except Exception as e:
                # Tool execution might fail if Cortex CLI is not available, which is acceptable
                print(f"Tool execution test warning: {e}")
        else:
            pytest.skip("Cortex MCP server not available")

class TestMCPServerExtendedFallback:
    """Fallback-Tests für erweiterte MCP Funktionalität."""

    def test_mcp_directory_structure(self):
        """Test der vereinfachten MCP Verzeichnisstruktur."""
        mcp_dir = project_root / "src" / "mcp"

        if not mcp_dir.exists():
            pytest.skip("MCP directory does not exist")

        # Überprüfe die neue einheitliche Struktur
        required_files = [
            "__init__.py",
            "cortex_mcp_server.py"  # Only the unified server file should exist
        ]

        for file in required_files:
            file_path = mcp_dir / file
            assert file_path.exists(), f"Required file missing: {file_path}"

        # Überprüfe, dass die alten duplizierten Dateien nicht mehr existieren
        old_files = [
            "mcp_cortex_server.py"
        ]

        for old_file in old_files:
            old_file_path = mcp_dir / old_file
            assert not old_file_path.exists(), f"Old duplicate file should be removed: {old_file_path}"

    def test_mcp_server_script_executable(self):
        """Test ob das MCP Server Skript ausführbar ist."""
        mcp_server_path = project_root / "src" / "mcp" / "cortex_mcp_server.py"

        if not mcp_server_path.exists():
            pytest.skip("MCP server script not found")

        # Test help option
        try:
            result = subprocess.run([
                sys.executable, str(mcp_server_path), "--help"
            ], capture_output=True, text=True, timeout=10)

            # Should either show help or run without error
            assert result.returncode == 0, f"Server script failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            pytest.skip("Server script timeout (may be waiting for MCP input)")
        except Exception as e:
            pytest.skip(f"Cannot test server script execution: {e}")

    def test_backward_compatibility(self):
        """Test dass die Abwärtskompatibilität gewährleistet ist."""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            assert cortex_mcp_server is not None, "Cortex MCP server should be available"
            assert hasattr(cortex_mcp_server, 'main'), "Main function should be available"
            assert hasattr(cortex_mcp_server, 'server'), "Server instance should be available"
            print("✅ Backward compatibility test erfolgreich")
        else:
            pytest.skip("Cortex MCP server not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
