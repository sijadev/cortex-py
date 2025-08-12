#!/bin/bash

# Verzeichnis wechseln und Pfade konfigurieren
cd /workspaces/cortex-py/cortex-cli
CORTEX_CMD="./bin/cortex-cmd"
PYTHON_MODULE="cortex.cli.main"

echo "Überprüfe verfügbare Befehle..."

# Sicherstellen, dass cortex-cmd ausführbar ist
if [ -f "bin/cortex-cmd" ]; then
    chmod +x bin/cortex-cmd
    echo "cortex-cmd gefunden und ausführbar gemacht."
    
    # Hilfe anzeigen, um verfügbare Befehle zu sehen
    echo -e "\nVerfügbare Cortex-Befehle:"
    $CORTEX_CMD
    
    # Versuche Link-Validierung mit cortex-cmd
    echo -e "\nVersuche Link-Validierung mit cortex-cmd..."
    $CORTEX_CMD linking validate
    
    if [ $? -ne 0 ]; then
        echo "Link-Validierung schlug fehl, versuche alternative Befehle..."
        
        # Versuche andere mögliche Unterbefehle
        for subcmd in "test analyze" "validate" "link-vaults"; do
            echo "Versuche: $CORTEX_CMD $subcmd"
            $CORTEX_CMD $subcmd
        done
    fi
else
    echo "bin/cortex-cmd nicht gefunden."
fi

# Fallback auf direkten Python-Modulaufruf
echo -e "\nVersuche Python-Modul direkt..."
python -m $PYTHON_MODULE linking validate 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Python-Modulaufruf schlug fehl, versuche andere Module..."
    
    # Finde alle verfügbaren Python-Module in cortex.cli
    echo -e "\nVerfügbare Cortex CLI Module:"
    find cortex/cli -name "*.py" | grep -v "__pycache__" | sort
    
    # Versuche mit jedem Modul, das "link" im Namen hat
    for module in $(find cortex/cli -name "*link*.py" | grep -v "__pycache__"); do
        module_name=$(echo $module | sed 's/\.py$//' | tr '/' '.')
        echo -e "\nVersuche Modul: $module_name"
        python -m $module_name validate 2>/dev/null
        python -m $module_name --help 2>/dev/null
    done
fi

# Zeige Diagnose-Informationen an
echo -e "\nDiagnose-Informationen:"
echo "Cortex-CLI Pfad: $(pwd)"
echo "Python Version: $(python --version)"
echo "Installierte Pakete:"
pip list | grep -i "cortex\|click"

# Öffne optional die Cortex-AI Webanwendung
echo -e "\nMöchtest du stattdessen die Cortex-AI-Webanwendung öffnen? (y/n)"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    "$BROWSER" http://localhost:8000
fi