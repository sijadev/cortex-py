#!/bin/bash
# Cortex-CLI Installationsskript

# Farben für bessere Ausgabe
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Keine Farbe

# Fehlerbehebungsfunktion
handle_error() {
    echo -e "${RED}❌ Fehler: $1${NC}"
    exit 1
}

# Optionen
INSTALL_DEV=0
INSTALL_AI=0

# Befehlszeilenargumente verarbeiten
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dev)
            INSTALL_DEV=1
            ;;
        --ai)
            INSTALL_AI=1
            ;;
        --help)
            echo "Cortex-CLI Installationsskript"
            echo ""
            echo "Optionen:"
            echo "  --dev    Installiert auch Entwicklungsabhängigkeiten"
            echo "  --ai     Installiert auch Cortex-AI Abhängigkeiten"
            echo "  --help   Zeigt diese Hilfe an"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}⚠️ Unbekannte Option: $1${NC}"
            ;;
    esac
    shift
done

# Basis-Installation
echo -e "${BLUE}🔧 Installiere Kern-Abhängigkeiten...${NC}"
pip install -r requirements.txt || handle_error "Kern-Abhängigkeiten konnten nicht installiert werden"

# Entwicklungsabhängigkeiten
if [ $INSTALL_DEV -eq 1 ]; then
    echo -e "${BLUE}🔧 Installiere Entwicklungsabhängigkeiten...${NC}"
    pip install -r requirements-dev.txt || handle_error "Entwicklungsabhängigkeiten konnten nicht installiert werden"
fi

# Cortex-AI Abhängigkeiten
if [ $INSTALL_AI -eq 1 ]; then
    echo -e "${BLUE}🔧 Installiere Cortex-AI Abhängigkeiten...${NC}"
    pip install mcp neo4j || handle_error "Cortex-AI Abhängigkeiten konnten nicht installiert werden"
fi

# Ausführungsrechte setzen
echo -e "${BLUE}🔧 Setze Ausführungsrechte...${NC}"
chmod +x bin/cortex-cmd
chmod +x bin/cortex-ai

# Symbolische Links erstellen
echo -e "${BLUE}🔧 Erstelle symbolische Links...${NC}"
mkdir -p ~/.local/bin

if [ -f ~/.local/bin/cortex ]; then
    echo -e "${YELLOW}⚠️ ~/.local/bin/cortex existiert bereits. Überschreiben? (j/n)${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        ln -sf "$(pwd)/bin/cortex-cmd" ~/.local/bin/cortex
    fi
else
    ln -sf "$(pwd)/bin/cortex-cmd" ~/.local/bin/cortex
fi

if [ $INSTALL_AI -eq 1 ]; then
    ln -sf "$(pwd)/bin/cortex-ai" ~/.local/bin/cortex-ai
fi

echo -e "${GREEN}✅ Installation abgeschlossen!${NC}"
echo -e "${BLUE}Führe 'cortex --help' aus, um zu beginnen.${NC}"

# Überprüfe, ob ~/.local/bin im PATH ist
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}⚠️ $HOME/.local/bin ist nicht im PATH.${NC}"
    echo -e "${YELLOW}   Füge die folgende Zeile zu deiner Shell-Konfiguration hinzu:${NC}"
    echo -e "${BLUE}   export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
fi
