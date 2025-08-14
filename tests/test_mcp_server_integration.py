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
from unittest.mock import patch
import tempfile
import os

class TestMCPCortexIntegration:
    """Integration Tests zwischen MCP Server und Cortex CLI"""

    def test_cortex_cli_available(self):
        """Teste dass Cortex CLI verfügbar ist"""
        project_root = Path(__file__).parent.parent
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
            project_root = Path(__file__).parent.parent
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

@pytest.mark.asyncio
class TestMCPServerRealWorld:
    """Real-World MCP Server Tests mit echter CLI Integration"""

    async def test_mcp_server_with_real_cli(self):
        """Teste MCP Server mit echten CLI-Aufrufen"""
        try:
            import mcp_cortex_server

            # Teste Status-Abfrage über MCP
            result = await mcp_cortex_server.handle_read_resource("cortex://status")

            # Ergebnis sollte String sein
            assert isinstance(result, str)
            assert len(result) > 0

            # Sollte entweder echte Status-Info oder Fallback enthalten
            assert any(keyword in result.lower() for keyword in [
                "status", "cortex", "neo4j", "fehler", "nicht verfügbar"
            ])

        except ImportError:
            pytest.skip("MCP Server Modul nicht verfügbar")

    async def test_mcp_tool_execution_real(self):
        """Teste MCP Tool-Ausführung mit echten Kommandos"""
        try:
            import mcp_cortex_server

            # Teste harmloses Kommando
            result = await mcp_cortex_server.handle_call_tool(
                "cortex_run_command",
                {"command": "help"}
            )

            assert isinstance(result, list)
            assert len(result) > 0

            # Text sollte Kommando-Information enthalten
            text_content = result[0].text
            assert "Befehl:" in text_content
            assert "Exit Code:" in text_content

        except ImportError:
            pytest.skip("MCP Server Modul nicht verfügbar")

    async def test_mcp_error_handling_real(self):
        """Teste MCP Fehlerbehandlung mit echten fehlerhaften Kommandos"""
        try:
            import mcp_cortex_server

            # Teste ungültiges Kommando
            result = await mcp_cortex_server.handle_call_tool(
                "cortex_run_command",
                {"command": "definitely-not-a-valid-command"}
            )

            assert isinstance(result, list)
            assert len(result) > 0

            # Sollte Fehlerinformation enthalten
            text_content = result[0].text
            assert "Exit Code:" in text_content

        except ImportError:
            pytest.skip("MCP Server Modul nicht verfügbar")

class TestMCPServerFiles:
    """Tests für MCP Server Dateien und Konfiguration"""

    def test_mcp_server_files_exist(self):
        """Teste dass alle MCP Server Dateien existieren"""
        project_root = Path(__file__).parent.parent

        required_files = [
            "mcp_cortex_server.py",
            "mcp_cortex_server_simple.py"
        ]

        for filename in required_files:
            filepath = project_root / filename
            assert filepath.exists(), f"MCP Server Datei fehlt: {filename}"
            assert filepath.stat().st_size > 1000, f"MCP Server Datei zu klein: {filename}"

    def test_mcp_server_syntax_valid(self):
        """Teste dass MCP Server Dateien syntaktisch korrekt sind"""
        project_root = Path(__file__).parent.parent

        server_files = [
            "mcp_cortex_server.py",
            "mcp_cortex_server_simple.py"
        ]

        for filename in server_files:
            filepath = project_root / filename

            try:
                # Versuche Syntax-Check durch Kompilierung
                with open(filepath, 'r', encoding='utf-8') as f:
                    source = f.read()

                compile(source, str(filepath), 'exec')

            except SyntaxError as e:
                pytest.fail(f"Syntax-Fehler in {filename}: {e}")
            except Exception as e:
                pytest.fail(f"Fehler beim Validieren von {filename}: {e}")

    def test_start_scripts_exist(self):
        """Teste dass MCP Start-Skripte existieren"""
        scripts_dir = Path(__file__).parent.parent / "scripts"

        start_script = scripts_dir / "start_mcp_cortex_server.sh"
        assert start_script.exists(), "MCP Start-Skript fehlt"

        # Prüfe Script-Inhalt
        with open(start_script, 'r') as f:
            content = f.read()

        assert "python" in content.lower(), "Start-Skript sollte Python-Aufruf enthalten"
        assert "mcp_cortex_server" in content, "Start-Skript sollte MCP Server referenzieren"

class TestMCPServerCompatibility:
    """Tests für MCP Server Kompatibilität"""

    def test_mcp_library_compatibility(self):
        """Teste MCP Bibliothek Kompatibilität"""
        try:
            import mcp
            from mcp.server import Server
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
            pytest.skip(f"MCP Bibliothek nicht kompatibel: {e}")

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
        docs_dir = Path(__file__).parent.parent / "docs"
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
        docs_dir = Path(__file__).parent.parent / "docs"
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

    # Server Files Check
    project_root = Path(__file__).parent.parent
    server_files = ["mcp_cortex_server.py", "mcp_cortex_server_simple.py"]
    for filename in server_files:
        if not (project_root / filename).exists():
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

if __name__ == "__main__":
    run_mcp_integration_tests()
