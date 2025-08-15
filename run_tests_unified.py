#!/usr/bin/env python3
"""
Unified Cortex-py Test Runner
============================

Zentraler Test-Runner der alle Tests ausführt und EINEN einzigen HTML-Report generiert.
Verhindert doppelte Test-Result-Seiten.
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path
import time
from datetime import datetime

# Projekt-Root hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

def cleanup_old_reports():
    """Löscht alte Test-Reports um Konflikte zu vermeiden"""
    reports_dir = project_root / "tests" / "reports"
    if reports_dir.exists():
        for file in reports_dir.glob("*.html"):
            try:
                file.unlink()
                print(f"🗑️  Alte Report-Datei gelöscht: {file.name}")
            except Exception as e:
                print(f"⚠️  Konnte {file.name} nicht löschen: {e}")

def setup_environment():
    """Bereitet die Test-Umgebung vor"""
    print("🔧 Bereite Test-Umgebung vor...")

    # Stelle sicher dass alle notwendigen Verzeichnisse existieren
    reports_dir = project_root / "tests" / "reports"
    logs_dir = project_root / "logs" / "tests"
    reports_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Bereinige alte Reports
    cleanup_old_reports()

    # Setze Umgebungsvariablen für Tests
    os.environ["PYTHONPATH"] = f"{project_root}:{project_root / 'src'}"
    os.environ["NEO4J_DISABLED"] = "1"  # Deaktiviere Neo4j für Tests

    print("✅ Test-Umgebung vorbereitet")

def run_tests_with_single_report():
    """Führt alle Tests aus und generiert EINEN einzigen HTML-Report"""
    print("🧪 Starte Test-Suite (Unified Runner)...")
    print("=" * 60)

    # Eindeutiger HTML-Report Pfad mit Zeitstempel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = project_root / "tests" / "reports" / f"test_report_{timestamp}.html"

    print(f"📊 HTML-Report wird erstellt: {report_path.name}")

    # Pytest Kommando - NUR EIN Report!
    pytest_cmd = [
        "python", "-m", "pytest",
        "tests/",  # Explizit nur tests/ Verzeichnis
        "--html", str(report_path),
        "--self-contained-html",
        "--verbose",
        "--tb=short",
        "--durations=10",
        "--cov=src",
        "--cov-report=html:tests/reports/coverage",
        "--maxfail=5",  # Stop nach 5 Fehlern
        "--disable-warnings"
    ]

    print(f"🚀 Führe Tests aus: {' '.join(pytest_cmd[2:])}")
    print("-" * 60)

    try:
        # Führe Tests aus
        result = subprocess.run(
            pytest_cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 Minuten Timeout
        )

        print(f"\n📋 Test-Ergebnis:")
        print(f"   Exit Code: {result.returncode}")

        if result.stdout:
            print("📤 Standard Output:")
            print(result.stdout[-1000:])  # Zeige letzten 1000 Zeichen

        if result.stderr and result.stderr.strip():
            print("⚠️  Standard Error:")
            print(result.stderr[-500:])  # Zeige letzten 500 Zeichen

        # Prüfe ob HTML-Report erstellt wurde
        if report_path.exists():
            print(f"\n✅ HTML-Report erfolgreich erstellt: {report_path}")

            # Öffne Report automatisch im Browser
            try:
                webbrowser.open(f"file://{report_path.absolute()}")
                print("🌐 Report im Browser geöffnet")
            except Exception as e:
                print(f"⚠️  Konnte Report nicht automatisch öffnen: {e}")
                print(f"💡 Öffnen Sie manuell: file://{report_path.absolute()}")
        else:
            print("❌ HTML-Report wurde nicht erstellt")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("⏰ Test-Ausführung nach 5 Minuten abgebrochen (Timeout)")
        return False
    except Exception as e:
        print(f"❌ Fehler bei Test-Ausführung: {e}")
        return False

def print_summary():
    """Zeigt eine Zusammenfassung"""
    print("\n" + "=" * 60)
    print("📊 UNIFIED TEST RUNNER - ZUSAMMENFASSUNG")
    print("=" * 60)

    reports_dir = project_root / "tests" / "reports"
    if reports_dir.exists():
        html_reports = list(reports_dir.glob("*.html"))
        print(f"📄 HTML-Reports erstellt: {len(html_reports)}")

        if len(html_reports) == 1:
            print("✅ ERFOLG: Nur ein einziger HTML-Report erstellt (keine Duplikate)")
        elif len(html_reports) > 1:
            print("⚠️  WARNUNG: Mehrere HTML-Reports gefunden:")
            for report in html_reports:
                print(f"   - {report.name}")
        else:
            print("❌ Kein HTML-Report gefunden")

def main():
    """Hauptfunktion des Unified Test Runners"""
    print("🚀 Cortex-py Unified Test Runner")
    print("=" * 60)
    print(f"⏰ Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Ziel: Ein einziger HTML-Report (keine Duplikate)")
    print()

    # Setup
    setup_environment()

    # Tests ausführen
    success = run_tests_with_single_report()

    # Zusammenfassung
    print_summary()

    if success:
        print("\n🎉 Tests erfolgreich abgeschlossen!")
        return 0
    else:
        print("\n❌ Tests mit Fehlern beendet")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
