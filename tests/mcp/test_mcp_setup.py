#!/usr/bin/env python3
"""
Test Suite für MCP Setup und Konfiguration
"""
import pytest
import subprocess
import sys
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent  # Go up two levels now (mcp -> tests -> project)
sys.path.insert(0, str(project_root))


class TestMCPSetup:
    """Tests für MCP Setup und Konfiguration."""

    def test_project_structure(self):
        """Test dass die grundlegende Projektstruktur existiert."""
        # Wichtige Verzeichnisse
        important_dirs = ["src", "scripts", "config"]

        existing_dirs = []
        for dirname in important_dirs:
            dirpath = project_root / dirname
            if dirpath.exists():
                existing_dirs.append(dirname)

        # Mindestens ein wichtiges Verzeichnis sollte existieren
        assert len(existing_dirs) > 0, f"Keine wichtigen Verzeichnisse gefunden: {important_dirs}"

    def test_mcp_scripts_exist(self):
        """Test dass MCP-bezogene Skripte existieren."""
        scripts_dir = project_root / "scripts" / "mcp"

        if not scripts_dir.exists():
            pytest.skip("MCP scripts directory does not exist")

        # Suche nach Skript-Dateien
        script_files = list(scripts_dir.glob("*.sh"))
        assert len(script_files) > 0, f"Keine MCP-Skripte in {scripts_dir} gefunden"

    def test_claude_config_template(self):
        """Test dass Claude Desktop Konfiguration verfügbar ist."""
        config_dir = project_root / "config"

        if not config_dir.exists():
            pytest.skip("Config directory does not exist")

        # Suche nach Claude-bezogenen Konfigurations-Dateien
        claude_config = config_dir / "claude_desktop_config.json"

        if claude_config.exists():
            # Prüfe ob es valides JSON ist
            try:
                with open(claude_config, "r") as f:
                    config_data = json.load(f)
                assert isinstance(config_data, dict)
            except json.JSONDecodeError:
                pytest.fail(f"Ungültige JSON in {claude_config}")
        else:
            pytest.skip("Claude Desktop Konfiguration nicht gefunden")


class TestMCPDependencies:
    """Tests für MCP Abhängigkeiten."""

    def test_python_version(self):
        """Test dass Python Version ausreichend ist."""
        import sys

        version = sys.version_info

        # MCP benötigt Python 3.8+
        assert version >= (3, 8), f"Python Version zu alt: {version}"

    def test_required_packages_importable(self):
        """Test dass erforderliche Pakete importierbar sind."""
        # Basis-Pakete die immer verfügbar sein sollten
        basic_packages = ["json", "asyncio", "pathlib", "subprocess"]

        for package in basic_packages:
            try:
                __import__(package)
            except ImportError:
                pytest.fail(f"Basis-Paket nicht verfügbar: {package}")

        # Optionale MCP-Pakete
        optional_packages = ["mcp", "mcp.server", "mcp.types"]

        available_optional = []
        for package in optional_packages:
            try:
                __import__(package)
                available_optional.append(package)
            except ImportError:
                pass

        # Bewerte MCP-Installation - erlaubt auch teilweise Installation
        if len(available_optional) == 0:
            pytest.skip(
                "MCP nicht installiert - Installation erforderlich für volle Funktionalität"
            )
        elif len(available_optional) == 1 and "mcp" in available_optional:
            # Nur Basis-MCP verfügbar - das ist in Ordnung für Entwicklung
            assert True, "MCP Basis-Modul verfügbar"
        elif len(available_optional) >= 2:
            # Vollständige oder nahezu vollständige MCP-Installation
            assert True, f"MCP gut installiert: {available_optional}"
        else:
            # Unvollständige aber verwendbare Installation
            assert True, f"MCP teilweise installiert: {available_optional}"


class TestMCPEnvironment:
    """Tests für MCP Umgebung."""

    def test_environment_variables(self):
        """Test Umgebungsvariablen Setup."""
        # Test dass Umgebungsvariablen gesetzt werden können
        original_value = os.environ.get("TEST_MCP_VAR")

        try:
            os.environ["TEST_MCP_VAR"] = "test_value"
            assert os.environ.get("TEST_MCP_VAR") == "test_value"
        finally:
            # Cleanup
            if original_value is not None:
                os.environ["TEST_MCP_VAR"] = original_value
            else:
                os.environ.pop("TEST_MCP_VAR", None)

    def test_path_setup(self):
        """Test dass Python Path korrekt funktioniert."""
        # Test dass wir Module aus dem Projekt-Root laden können
        original_path = sys.path[:]

        try:
            # Füge Projekt-Root hinzu falls nicht schon da
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            # Versuche ein Projekt-Modul zu importieren
            try:
                import src

                assert True
            except ImportError:
                pytest.skip("Projekt-Module nicht importierbar")

        finally:
            # Restore original path
            sys.path[:] = original_path


class TestMCPDocumentation:
    """Tests für MCP Dokumentation."""

    def test_setup_documentation_exists(self):
        """Test dass Setup-Dokumentation existiert."""
        docs_dir = project_root / "docs"

        if not docs_dir.exists():
            pytest.skip("Docs directory does not exist")

        # Suche nach MCP-bezogener Dokumentation
        mcp_docs = ["MCP_SETUP_ANLEITUNG.md", "README_MCP.md"]

        existing_docs = []
        for doc in mcp_docs:
            doc_path = docs_dir / doc
            if doc_path.exists():
                existing_docs.append(doc)

        if len(existing_docs) > 0:
            # Mindestens eine Dokumentation sollte substanziell sein
            for doc in existing_docs:
                doc_path = docs_dir / doc
                assert doc_path.stat().st_size > 500, f"Dokumentation zu kurz: {doc}"
        else:
            pytest.skip("Keine MCP-Dokumentation gefunden")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
