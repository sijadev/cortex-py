#!/bin/bash
# Führt alle Tests aus und öffnet das HTML-Test-Report im Browser

set -e

REPORT_FILE="report.html"

if [ "$1" == "neo4j" ]; then
    echo "Starte nur Neo4J-Tests (cortex_neo/tests/test_profiles.py)..."
    pytest cortex_neo/tests/test_profiles.py --maxfail=5 --disable-warnings --tb=short --html=$REPORT_FILE || true
else
    # Tests ausführen und HTML-Report generieren
    pytest --maxfail=5 --disable-warnings --tb=short --html=$REPORT_FILE || true
fi

# Prüfe, ob der Report existiert
if [ -f "$REPORT_FILE" ]; then
    echo "Öffne Test-Report im Browser: $REPORT_FILE"
    if which open >/dev/null; then
        open "$REPORT_FILE"
    elif which xdg-open >/dev/null; then
        xdg-open "$REPORT_FILE"
    else
        echo "Bitte öffne die Datei manuell: $REPORT_FILE"
    fi
else
    echo "Test-Report wurde nicht gefunden: $REPORT_FILE"
    exit 1
fi
