#!/bin/bash

# Cortex MCP Server Port Management Script
# Dieses Skript prüft und bereinigt Port-Konflikte vor dem Start des MCP Servers

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Standardport für MCP Server
DEFAULT_PORT=8000

# Funktion: Port-Status prüfen
check_port() {
    local port=$1
    local result=$(lsof -i :$port 2>/dev/null)

    if [ -n "$result" ]; then
        echo -e "${YELLOW}⚠️ Port $port ist belegt:${NC}"
        echo "$result"
        return 1
    else
        echo -e "${GREEN}✅ Port $port ist verfügbar${NC}"
        return 0
    fi
}

# Funktion: Prozesse auf Port beenden
kill_port_processes() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null)

    if [ -n "$pids" ]; then
        echo -e "${YELLOW}🔄 Beende Prozesse auf Port $port...${NC}"
        for pid in $pids; do
            local process_info=$(ps -p $pid -o comm= 2>/dev/null)
            echo -e "${BLUE}   Beende Prozess: $pid ($process_info)${NC}"
            kill -TERM $pid 2>/dev/null

            # Warte kurz und prüfe ob Prozess noch läuft
            sleep 2
            if kill -0 $pid 2>/dev/null; then
                echo -e "${RED}   Forciere Beendigung: $pid${NC}"
                kill -KILL $pid 2>/dev/null
            fi
        done

        # Kurz warten und erneut prüfen
        sleep 1
        if check_port $port; then
            echo -e "${GREEN}✅ Port $port erfolgreich freigegeben${NC}"
            return 0
        else
            echo -e "${RED}❌ Port $port konnte nicht freigegeben werden${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}✅ Keine Prozesse auf Port $port gefunden${NC}"
        return 0
    fi
}

# Funktion: Verfügbaren Port finden
find_available_port() {
    local start_port=$1
    local end_port=${2:-$((start_port + 100))}

    for ((port=start_port; port<=end_port; port++)); do
        if check_port $port >/dev/null 2>&1; then
            echo $port
            return 0
        fi
    done

    return 1
}

# Funktion: MCP Server mit Port-Management starten
start_mcp_server() {
    local port=${1:-$DEFAULT_PORT}
    local server_script="/Users/simonjanke/Projects/cortex-py/mcp_cortex_server.py"

    echo -e "${BLUE}🚀 Starte Cortex MCP Server...${NC}"

    # Prüfe ob Server-Script existiert
    if [ ! -f "$server_script" ]; then
        echo -e "${RED}❌ MCP Server Script nicht gefunden: $server_script${NC}"
        return 1
    fi

    # Port-Status prüfen und ggf. freigeben
    if ! check_port $port >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ Port $port ist belegt. Versuche Freigabe...${NC}"
        if ! kill_port_processes $port; then
            echo -e "${YELLOW}⚠️ Suche alternativen Port...${NC}"
            port=$(find_available_port $((port + 1)))
            if [ -z "$port" ]; then
                echo -e "${RED}❌ Kein verfügbarer Port gefunden${NC}"
                return 1
            fi
            echo -e "${GREEN}✅ Verwende alternativen Port: $port${NC}"
        fi
    fi

    # MCP Server starten
    echo -e "${GREEN}🎯 Starte MCP Server auf Port $port...${NC}"
    cd "/Users/simonjanke/Projects/cortex-py"

    # Setze Umgebungsvariablen
    export PYTHONPATH="/Users/simonjanke/Projects/cortex-py:$PYTHONPATH"
    export MCP_SERVER_PORT=$port

    # Starte Server
    python3 "$server_script" &
    local server_pid=$!

    # Kurz warten und prüfen ob Server gestartet ist
    sleep 3
    if kill -0 $server_pid 2>/dev/null; then
        echo -e "${GREEN}✅ MCP Server erfolgreich gestartet (PID: $server_pid)${NC}"
        echo -e "${BLUE}📍 Server läuft auf Port: $port${NC}"
        echo -e "${YELLOW}💡 Verwende Strg+C zum Beenden${NC}"

        # Server-PID für cleanup speichern
        echo $server_pid > /tmp/cortex_mcp_server.pid

        # Trap für sauberes Beenden
        trap "echo -e '${BLUE}🛑 Beende MCP Server...${NC}'; kill $server_pid 2>/dev/null; rm -f /tmp/cortex_mcp_server.pid; exit 0" INT TERM

        # Warten bis Server beendet wird
        wait $server_pid
    else
        echo -e "${RED}❌ MCP Server konnte nicht gestartet werden${NC}"
        return 1
    fi
}

# Funktion: Laufende MCP Server beenden
stop_mcp_server() {
    echo -e "${BLUE}🛑 Beende laufende MCP Server...${NC}"

    # Suche nach MCP Server Prozessen
    local pids=$(pgrep -f "mcp_cortex_server.py" 2>/dev/null)

    if [ -n "$pids" ]; then
        for pid in $pids; do
            echo -e "${YELLOW}   Beende MCP Server: $pid${NC}"
            kill -TERM $pid 2>/dev/null
            sleep 2
            if kill -0 $pid 2>/dev/null; then
                kill -KILL $pid 2>/dev/null
            fi
        done
    fi

    # PID-Datei aufräumen
    rm -f /tmp/cortex_mcp_server.pid

    # Port-spezifische Bereinigung
    kill_port_processes 8000
    kill_port_processes 8001
    kill_port_processes 8002

    echo -e "${GREEN}✅ MCP Server bereinigt${NC}"
}

# Funktion: Server-Status anzeigen
show_status() {
    echo -e "${BLUE}📊 Cortex MCP Server Status:${NC}"
    echo ""

    # Port-Status prüfen
    for port in 8000 8001 8002; do
        echo -e "${YELLOW}Port $port:${NC}"
        if check_port $port >/dev/null 2>&1; then
            echo -e "  ${GREEN}✅ Verfügbar${NC}"
        else
            echo -e "  ${RED}❌ Belegt${NC}"
            lsof -i :$port 2>/dev/null | grep -v COMMAND | while read line; do
                echo -e "  ${BLUE}   $line${NC}"
            done
        fi
    done

    echo ""

    # MCP Server Prozesse
    local mcp_pids=$(pgrep -f "mcp_cortex_server.py" 2>/dev/null)
    if [ -n "$mcp_pids" ]; then
        echo -e "${GREEN}🟢 Laufende MCP Server:${NC}"
        for pid in $mcp_pids; do
            local process_info=$(ps -p $pid -o pid,ppid,comm,args --no-headers 2>/dev/null)
            echo -e "  ${BLUE}$process_info${NC}"
        done
    else
        echo -e "${YELLOW}⚪ Keine MCP Server Prozesse gefunden${NC}"
    fi

    # PID-Datei Status
    if [ -f "/tmp/cortex_mcp_server.pid" ]; then
        local stored_pid=$(cat /tmp/cortex_mcp_server.pid)
        if kill -0 $stored_pid 2>/dev/null; then
            echo -e "${GREEN}📝 Gespeicherte PID: $stored_pid (aktiv)${NC}"
        else
            echo -e "${RED}📝 Gespeicherte PID: $stored_pid (inaktiv)${NC}"
            rm -f /tmp/cortex_mcp_server.pid
        fi
    fi
}

# Hauptfunktion
main() {
    case "${1:-start}" in
        "start")
            start_mcp_server ${2:-$DEFAULT_PORT}
            ;;
        "stop")
            stop_mcp_server
            ;;
        "restart")
            stop_mcp_server
            sleep 2
            start_mcp_server ${2:-$DEFAULT_PORT}
            ;;
        "status")
            show_status
            ;;
        "check-port")
            check_port ${2:-$DEFAULT_PORT}
            ;;
        "kill-port")
            kill_port_processes ${2:-$DEFAULT_PORT}
            ;;
        "cleanup")
            stop_mcp_server
            echo -e "${GREEN}✅ Vollständige Bereinigung abgeschlossen${NC}"
            ;;
        "--help"|"help")
            echo -e "${BLUE}Cortex MCP Server Port Management${NC}"
            echo ""
            echo -e "${GREEN}Verwendung:${NC} $0 [BEFEHL] [PORT]"
            echo ""
            echo -e "${YELLOW}Befehle:${NC}"
            echo "  start [PORT]     Startet MCP Server (Standard: Port 8000)"
            echo "  stop             Beendet alle MCP Server"
            echo "  restart [PORT]   Neustart des MCP Servers"
            echo "  status           Zeigt Server-Status"
            echo "  check-port PORT  Prüft Port-Verfügbarkeit"
            echo "  kill-port PORT   Beendet Prozesse auf Port"
            echo "  cleanup          Vollständige Server-Bereinigung"
            echo "  help             Zeigt diese Hilfe"
            echo ""
            echo -e "${BLUE}Beispiele:${NC}"
            echo "  $0 start         # Startet auf Port 8000"
            echo "  $0 start 8001    # Startet auf Port 8001"
            echo "  $0 status        # Zeigt Status"
            echo "  $0 cleanup       # Bereinigt alles"
            ;;
        *)
            echo -e "${RED}❌ Unbekannter Befehl: $1${NC}"
            echo -e "${YELLOW}Verwende '$0 help' für Hilfe${NC}"
            exit 1
            ;;
    esac
}

# Script ausführen
main "$@"
