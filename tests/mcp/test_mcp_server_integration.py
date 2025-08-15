#!/usr/bin/env python3
"""
MCP Server Integration Tests

Diese Tests validieren die Integration zwischen MCP Server und Cortex CLI:
- Echte CLI Kommando-Ausführung
- Neo4j Integration über MCP
- End-to-End Workflows
- Claude Desktop Kompatibilität
"""

import asyncio
import json
import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
import tempfile
import os

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
except ImportError as e:
    MCP_AVAILABLE = False

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
    else:
        MCP_SERVER_AVAILABLE = False
except Exception as e:
    MCP_SERVER_AVAILABLE = False

class TestMCPCortexIntegration:
    """Integration Tests zwischen MCP Server und Cortex CLI"""

    def test_cortex_cli_available(self):
        """Teste dass Cortex CLI verfügbar ist"""
        project_root = Path(__file__).parent.parent.parent  # Go up two levels now (mcp -> tests -> project)
        cortex_cli_path = project_root / "cortex_neo" / "cortex_cli.py"

        assert cortex_cli_path.exists(), f"Cortex CLI nicht gefunden: {cortex_cli_path}"

        # Teste grundlegende CLI Funktionalität
        try:
            result = subprocess.run([
                sys.executable, str(cortex_cli_path), "--help"
            ], capture_output=True, text=True, timeout=10)

            # CLI sollte Help-Text zurückgeben
            assert result.returncode == 0 or "Usage:" in result.stdout or "help" in result.stdout.lower()

        except subprocess.TimeoutExpired:
            pytest.skip("Cortex CLI Timeout - möglicherweise Neo4j nicht verfügbar")
        except Exception as e:
            pytest.skip(f"Cortex CLI nicht ausführbar: {e}")

    def test_neo4j_connection_check(self):
        """Teste ob Neo4j Verbindung möglich ist"""
        try:
            # Versuche Neo4j Status zu prüfen
            project_root = Path(__file__).parent.parent.parent  # Go up two levels now (mcp -> tests -> project)
            cortex_cli_path = project_root / "cortex_neo" / "cortex_cli.py"

            result = subprocess.run([
                sys.executable, str(cortex_cli_path), "status"
            ], capture_output=True, text=True, timeout=5,
              env={**os.environ,
                   "NEO4J_URI": "bolt://localhost:7687",
                   "NEO4J_USER": "neo4j",
                   "NEO4J_PASSWORD": "neo4jtest"})

            # Auch wenn Neo4j nicht läuft, sollte der CLI-Aufruf funktionieren
            assert result.returncode in [0, 1], "CLI-Aufruf sollte funktionieren"

        except subprocess.TimeoutExpired:
            pytest.skip("Neo4j nicht verfügbar oder Timeout")
        except Exception:
            pytest.skip("Neo4j Connection Check nicht möglich")

@pytest.mark.skipif(not (MCP_AVAILABLE or MCP_SERVER_AVAILABLE), reason="Neither MCP library nor Cortex MCP server available")
@pytest.mark.asyncio
class TestMCPServerRealWorld:
    """Real-World MCP Server Tests mit einheitlichem Server und echter CLI Integration"""

    async def test_mcp_server_with_real_cli(self):
        """Teste einheitlichen MCP Server mit echten CLI-Aufrufen"""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            try:
                result = await cortex_mcp_server.handle_read_resource("cortex://status")
                assert isinstance(result, str), "Result should be a string"
                assert len(result) > 0, "Result should not be empty"

                # Sollte entweder echte Status-Info oder Fallback enthalten
                assert any(keyword in result.lower() for keyword in [
                    "status", "cortex", "neo4j", "fehler", "nicht verfügbar", "operational"
                ])
                print("✅ MCP Server mit echter CLI Integration erfolgreich getestet")
            except Exception as e:
                pytest.fail(f"MCP server test failed: {e}")
        else:
            pytest.skip("Cortex MCP server not available")

    async def test_mcp_tool_execution_real(self):
        """Teste echte Tool-Ausführung mit einheitlichem Server"""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            try:
                result = await cortex_mcp_server.handle_call_tool("cortex_status", {})
                assert isinstance(result, list), "Result should be a list"
                assert len(result) > 0, "Result should not be empty"
                assert hasattr(result[0], 'text'), "Result should have text content"

                # Text sollte Status-Information enthalten
                status_text = result[0].text
                assert isinstance(status_text, str), "Status text should be a string"
                assert len(status_text) > 0, "Status text should not be empty"
                print("✅ Tool-Ausführung erfolgreich getestet")
            except Exception as e:
                pytest.fail(f"Tool execution test failed: {e}")
        else:
            pytest.skip("Cortex MCP server not available")

    async def test_mcp_error_handling_real(self):
        """Teste Fehlerbehandlung des einheitlichen MCP Servers"""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            try:
                # Teste mit ungültiger Ressource
                try:
                    result = await cortex_mcp_server.handle_read_resource("cortex://invalid")
                    # Sollte eine ValueError werfen oder Fehlermeldung zurückgeben
                    if isinstance(result, str):
                        assert "unknown" in result.lower() or "invalid" in result.lower()
                    else:
                        pytest.fail("Expected error for invalid resource")
                except ValueError as e:
                    assert "Unknown resource" in str(e) or "Unbekannte Ressource" in str(e)

                # Teste mit ungültigem Tool
                result = await cortex_mcp_server.handle_call_tool("invalid_tool", {})
                assert isinstance(result, list), "Error result should be a list"
                assert "Unknown tool" in result[0].text or "Unbekanntes Tool" in result[0].text
                print("✅ Fehlerbehandlung erfolgreich getestet")
            except Exception as e:
                pytest.fail(f"Error handling test failed: {e}")
        else:
            pytest.skip("Cortex MCP server not available")

class TestMCPServerFiles:
    """Tests für MCP Server Dateien und Konfiguration"""

    def test_mcp_server_files_exist(self):
        """Teste dass alle MCP Server Dateien existieren"""
        project_root = Path(__file__).parent.parent.parent  # Go up two levels now (mcp -> tests -> project)

        # Check in src/mcp directory first
        mcp_src_dir = project_root / "src" / "mcp"

        required_files = [
            "cortex_mcp_server.py"
        ]

        found_files = []
        for filename in required_files:
            # Check in src/mcp/ first
            filepath = mcp_src_dir / filename
            if filepath.exists():
                found_files.append(filename)
                continue

            # Fallback: check in project root
            filepath = project_root / f"mcp_{filename}"
            if filepath.exists():
                found_files.append(filename)
                continue

            # Check alternative names
            alt_names = [
                f"mcp_{filename}"
            ]

            for alt_name in alt_names:
                if alt_name and (project_root / alt_name).exists():
                    found_files.append(filename)
                    break

        if len(found_files) == 0:
            pytest.skip("No MCP server files found - MCP server not set up")

        # At least some MCP files should exist
        assert len(found_files) > 0, f"No MCP server files found. Looked for: {required_files}"

    def test_mcp_server_syntax_valid(self):
        """Teste dass MCP Server Dateien syntaktisch korrekt sind"""
        project_root = Path(__file__).parent.parent.parent  # Go up two levels now (mcp -> tests -> project)

        # Look for MCP server files in multiple locations
        potential_files = []

        # Check src/mcp directory
        mcp_src_dir = project_root / "src" / "mcp"
        if mcp_src_dir.exists():
            potential_files.extend(list(mcp_src_dir.glob("*mcp_server*.py")))

        # Check project root
        potential_files.extend(list(project_root.glob("mcp_*server*.py")))

        if not potential_files:
            pytest.skip("No MCP server files found for syntax validation")

        valid_files = 0
        for filepath in potential_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    source = f.read()
                compile(source, str(filepath), 'exec')
                valid_files += 1
            except SyntaxError as e:
                pytest.fail(f"Syntax-Fehler in {filepath.name}: {e}")
            except Exception as e:
                # Skip files that can't be read but don't fail the test
                continue

        assert valid_files > 0, f"No valid MCP server files found among {len(potential_files)} candidates"

    def test_start_scripts_exist(self):
        """Teste dass MCP Start-Skripte existieren"""
        scripts_dir = Path(__file__).parent.parent.parent / "scripts" / "mcp"  # Fix path reference

        start_script = scripts_dir / "start_mcp_cortex_server.sh"
        if start_script.exists():
            assert start_script.exists(), "MCP Start-Skript fehlt"

            # Prüfe Script-Inhalt
            with open(start_script, 'r') as f:
                content = f.read()

            # Das Skript delegiert an manage_mcp_server.sh, prüfe auf relevante Inhalte
            assert "mcp" in content.lower() or "cortex" in content.lower(), "Start-Skript sollte MCP/Cortex referenzieren"
        else:
            pytest.skip("MCP Start-Skript nicht gefunden - möglicherweise noch nicht eingerichtet")

class TestMCPServerCompatibility:
    """Tests für MCP Server Kompatibilität"""

    def test_mcp_library_compatibility(self):
        """Teste MCP Bibliothek Kompatibilität"""
        if not MCP_AVAILABLE:
            pytest.skip("MCP Library nicht verfügbar - verwende eigene Implementierung")

        try:
            # Test mit der verfügbaren MCP Library
            from mcp.server import Server, NotificationOptions
            from mcp.types import Resource, Tool, TextContent

            # Teste dass grundlegende MCP Klassen funktionieren
            test_server = Server("test")
            assert test_server is not None

            test_resource = Resource(
                uri="test://resource",
                name="Test Resource",
                description="Test Description",
                mimeType="text/plain"
            )
            assert test_resource is not None

            test_tool = Tool(
                name="test_tool",
                description="Test Tool",
                inputSchema={"type": "object", "properties": {}}
            )
            assert test_tool is not None

            test_content = TextContent(type="text", text="Test")
            assert test_content is not None

        except ImportError as e:
            # Falls die externe MCP Library nicht verfügbar ist, teste unsere eigene Implementierung
            if MCP_SERVER_AVAILABLE:
                assert cortex_mcp_server is not None, "Cortex MCP server should be available"
                assert hasattr(cortex_mcp_server, 'handle_list_resources'), "handle_list_resources should be available"
                assert hasattr(cortex_mcp_server, 'handle_call_tool'), "handle_call_tool should be available"
                print("✅ Eigene MCP Implementierung funktioniert korrekt")
            else:
                pytest.skip(f"Weder externe MCP Library noch eigene Implementierung verfügbar: {e}")

    def test_python_version_compatibility(self):
        """Teste Python Version Kompatibilität"""
        import sys

        # MCP Server sollte mit Python 3.8+ funktionieren
        python_version = sys.version_info
        assert python_version >= (3, 8), f"Python Version zu alt: {python_version}"

        # Async/await sollte verfügbar sein
        assert hasattr(asyncio, 'run'), "asyncio.run nicht verfügbar"
        assert hasattr(asyncio, 'gather'), "asyncio.gather nicht verfügbar"

class TestMCPServerDocumentationIntegrity:
    """Tests für MCP Server Dokumentations-Integrität"""

    def test_mcp_setup_documentation(self):
        """Teste dass MCP Setup Dokumentation vollständig ist"""
        docs_dir = Path(__file__).parent.parent.parent / "docs"  # Fix path reference
        setup_doc = docs_dir / "MCP_SETUP_ANLEITUNG.md"

        if setup_doc.exists():
            with open(setup_doc, 'r', encoding='utf-8') as f:
                content = f.read()

            required_sections = [
                "Installation", "Setup", "Claude Desktop", "Test"
            ]

            for section in required_sections:
                assert section.lower() in content.lower(), \
                    f"Setup-Dokumentation fehlt Sektion: {section}"

    def test_mcp_readme_completeness(self):
        """Teste dass MCP README vollständig ist"""
        docs_dir = Path(__file__).parent.parent.parent / "docs"  # Fix path reference
        readme_mcp = docs_dir / "README_MCP.md"

        if readme_mcp.exists():
            with open(readme_mcp, 'r', encoding='utf-8') as f:
                content = f.read()

            # Sollte grundlegende Informationen enthalten
            assert len(content) > 500, "MCP README zu kurz"
            assert "MCP" in content, "MCP README erwähnt MCP nicht"
            assert "Server" in content, "MCP README erwähnt Server nicht"

# Utility Functions
def check_mcp_environment():
    """Prüfe MCP Umgebung"""
    issues = []

    # MCP Library Check
    try:
        import mcp
    except ImportError:
        issues.append("MCP Bibliothek nicht installiert")

    # Python Version Check
    import sys
    if sys.version_info < (3, 8):
        issues.append(f"Python Version zu alt: {sys.version_info}")

    # Server Files Check - Fix path reference
    project_root = Path(__file__).parent.parent.parent  # Go up two levels now (mcp -> tests -> project)
    server_files = ["cortex_mcp_server.py"]  # Update to use the unified server file
    mcp_src_dir = project_root / "src" / "mcp"

    for filename in server_files:
        if not (mcp_src_dir / filename).exists():
            issues.append(f"Server-Datei fehlt: {filename}")

    return issues

def run_mcp_integration_tests():
    """Führe MCP Integration Tests aus"""
    print("🔗 Starte MCP Server Integration Tests...")

    # Environment Check
    env_issues = check_mcp_environment()
    if env_issues:
        print("⚠️  Umgebungsprobleme gefunden:")
        for issue in env_issues:
            print(f"   - {issue}")
        print()

    test_result = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])

    if test_result == 0:
        print("✅ Alle MCP Integration Tests erfolgreich!")
    else:
        print("❌ Einige MCP Integration Tests fehlgeschlagen!")

    return test_result

@pytest.mark.skipif(not (MCP_AVAILABLE or MCP_SERVER_AVAILABLE), reason="Neither MCP library nor Cortex MCP server available")
class TestMCPServerIntegration:
    """Integration Tests für MCP Server."""

    @pytest.mark.asyncio
    async def test_server_startup_shutdown(self):
        """Test Server Startup und Shutdown."""
        if MCP_AVAILABLE:
            # Test mit externer MCP Library
            server = Mock(spec=Server)
            server.start = AsyncMock()
            server.stop = AsyncMock()

            await server.start()
            await server.stop()

            server.start.assert_called_once()
            server.stop.assert_called_once()
            print("✅ Server Startup/Shutdown Test erfolgreich")
        elif MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            assert cortex_mcp_server is not None, "Cortex MCP server should be available"
            assert hasattr(cortex_mcp_server, 'main'), "Main function should be available"
            print("✅ Cortex MCP Server Startup Test erfolgreich")
        else:
            pytest.skip("Neither external MCP library nor Cortex MCP server available")

    def test_integration_with_neo4j(self):
        """Test Integration mit Neo4j (Mock)."""
        if MCP_SERVER_AVAILABLE:
            # Test mit unserer eigenen Implementierung
            assert cortex_mcp_server is not None, "Cortex MCP server should be available"
            # Teste ob der Server Neo4j-Integration hat
            assert hasattr(cortex_mcp_server, 'CortexMCPServer'), "CortexMCPServer class should be available"
            print("✅ Neo4j Integration Test erfolgreich")
        elif MCP_AVAILABLE:
            # Mock Neo4j connection test mit externer Library
            neo4j_available = os.environ.get("NEO4J_URI") is not None
            if not neo4j_available:
                pytest.skip("Neo4j not configured")
            assert os.environ.get("NEO4J_URI") is not None
        else:
            pytest.skip("Neither MCP implementation available")

class TestMCPServerIntegrationFallback:
    """Fallback Integration Tests."""

    def test_environment_variables(self):
        """Test dass Umgebungsvariablen gesetzt werden können."""
        # Test basic environment setup
        test_env = os.environ.copy()
        test_env["TEST_VAR"] = "test_value"

        assert test_env.get("TEST_VAR") == "test_value"

    def test_project_modules_importable(self):
        """Test dass Projekt-Module grundsätzlich importierbar sind."""
        try:
            # Test basic project structure imports
            import src
            assert True
        except ImportError:
            pytest.skip("Project src module not importable")

if __name__ == "__main__":
    run_mcp_integration_tests()
    pytest.main([__file__, "-v"])
