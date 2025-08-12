#!/bin/bash

cd /workspaces/cortex-py/cortex-cli

# Versuche den vollständigen Befehlspfad
echo "Versuche Link-Validierung mit vollständigem Befehlspfad..."
if [ -f "bin/cortex-cmd" ]; then
    chmod +x bin/cortex-cmd
    ./bin/cortex-cmd linking validate
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "Link-Validierung erfolgreich ausgeführt."
        exit 0
    else
        echo "Link-Validierung mit bin/cortex-cmd linking validate fehlgeschlagen (Exit-Code: $exit_code)."
    fi
else
    echo "Warnung: bin/cortex-cmd nicht gefunden."
fi

# Falls das fehlschlägt, zeige Hilfe an
echo "Zeige verfügbare Befehle:"
if [ -f "bin/cortex-cmd" ]; then
    ./bin/cortex-cmd --help
    echo ""
    echo "Zeige Unterbefehle für linking:"
    ./bin/cortex-cmd linking --help
fi

# Wenn alles fehlschlägt, führe das Python-Skript aus
echo "Führe eigenständiges Python-Skript aus..."
cd /workspaces/cortex-py
chmod +x run_link_validation.py
./run_link_validation.py

# Öffne Cortex-AI im Browser, wenn gewünscht
echo -e "\nMöchtest du die Cortex-AI-Webanwendung öffnen? (y/n)"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    "$BROWSER" http://localhost:8000
fi