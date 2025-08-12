#!/bin/bash
# Cortex Learning Service Management Script

SERVICE_NAME="com.cortex.learning.service"
CORTEX_PATH="/Users/simonjanke/Projects/cortex"
SERVICE_PATH="$CORTEX_PATH/00-System/Services"

case "$1" in
    start)
        echo "🚀 Starting Cortex Learning Service..."
        launchctl start "$SERVICE_NAME"
        echo "✅ Service started"
        ;;
    stop)
        echo "🛑 Stopping Cortex Learning Service..."
        launchctl stop "$SERVICE_NAME"
        echo "✅ Service stopped"
        ;;
    restart)
        echo "🔄 Restarting Cortex Learning Service..."
        launchctl kickstart -k "gui/$(id -u)/$SERVICE_NAME"
        echo "✅ Service restarted"
        ;;
    status)
        echo "📊 Cortex Learning Service Status:"
        if launchctl list | grep -q "$SERVICE_NAME"; then
            echo "✅ Service is running"
            
            # Show recent activity
            if [ -f "$SERVICE_PATH/logs/cortex_learning.log" ]; then
                echo ""
                echo "📝 Recent Activity (last 10 lines):"
                tail -10 "$SERVICE_PATH/logs/cortex_learning.log"
            fi
            
            # Show learning stats
            if [ -f "$SERVICE_PATH/data/learning_stats.json" ]; then
                echo ""
                echo "📈 Learning Statistics:"
                python3 -c "
import json
with open('$SERVICE_PATH/data/learning_stats.json', 'r') as f:
    stats = json.load(f)
print(f\"  Patterns Detected: {stats.get('patterns_detected', 0)}\")
print(f\"  Insights Generated: {stats.get('insights_generated', 0)}\")
print(f\"  Quality Alerts: {stats.get('quality_alerts', 0)}\")
print(f\"  Uptime: {stats.get('uptime_hours', 0):.1f} hours\")
print(f\"  Last Cycle: {stats.get('last_learning_cycle', 'Never')}\")
"
            fi
        else
            echo "❌ Service is not running"
        fi
        ;;
    logs)
        echo "📝 Cortex Learning Service Logs:"
        if [ -f "$SERVICE_PATH/logs/cortex_learning.log" ]; then
            tail -f "$SERVICE_PATH/logs/cortex_learning.log"
        else
            echo "❌ No log file found"
        fi
        ;;
    install)
        bash "$SERVICE_PATH/install_service.sh"
        ;;
    uninstall)
        echo "🗑️  Uninstalling Cortex Learning Service..."
        launchctl stop "$SERVICE_NAME" 2>/dev/null || true
        launchctl unload "$HOME/Library/LaunchAgents/$SERVICE_NAME.plist" 2>/dev/null || true
        rm -f "$HOME/Library/LaunchAgents/$SERVICE_NAME.plist"
        echo "✅ Service uninstalled"
        ;;
    config)
        echo "⚙️  Opening service configuration..."
        if command -v code >/dev/null 2>&1; then
            code "$SERVICE_PATH/config/service_config.yaml"
        elif command -v nano >/dev/null 2>&1; then
            nano "$SERVICE_PATH/config/service_config.yaml"
        else
            echo "📁 Config file: $SERVICE_PATH/config/service_config.yaml"
        fi
        ;;
    *)
        echo "🤖 Cortex Learning Service Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|install|uninstall|config}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the learning service"
        echo "  stop      - Stop the learning service"
        echo "  restart   - Restart the learning service"
        echo "  status    - Show service status and statistics"
        echo "  logs      - View live service logs"
        echo "  install   - Install the service"
        echo "  uninstall - Remove the service"
        echo "  config    - Edit service configuration"
        echo ""
        echo "📊 Service Features:"
        echo "  - Automatic pattern detection every 30 minutes"
        echo "  - Quality monitoring and alerts"
        echo "  - Cross-project learning and insights"
        echo "  - macOS notifications for important discoveries"
        echo "  - Continuous improvement of Cortex intelligence"
        ;;
esac