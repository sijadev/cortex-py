#!/bin/bash
# Cortex Learning Service Installation Script

set -e

echo "🚀 Installing Cortex Learning Service..."

# Configuration
SERVICE_NAME="com.cortex.learning.service"
CORTEX_PATH="/Users/simonjanke/Projects/cortex"
SERVICE_PATH="$CORTEX_PATH/00-System/Services"
PLIST_FILE="$SERVICE_PATH/$SERVICE_NAME.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p "$SERVICE_PATH/logs"
mkdir -p "$SERVICE_PATH/data"
mkdir -p "$LAUNCH_AGENTS_DIR"

# Install required Python packages
echo "🐍 Installing Python dependencies..."
pip3 install schedule pyyaml --user

# Make the Python script executable
echo "🔧 Setting permissions..."
chmod +x "$SERVICE_PATH/cortex_learner.py"

# Copy plist file to LaunchAgents
echo "📋 Installing LaunchAgent..."
cp "$PLIST_FILE" "$LAUNCH_AGENTS_DIR/"

# Load the service
echo "⚡ Loading service..."
launchctl unload "$LAUNCH_AGENTS_DIR/$SERVICE_NAME.plist" 2>/dev/null || true
launchctl load "$LAUNCH_AGENTS_DIR/$SERVICE_NAME.plist"

# Start the service
echo "🎯 Starting service..."
launchctl start "$SERVICE_NAME"

# Verify installation
sleep 2
if launchctl list | grep -q "$SERVICE_NAME"; then
    echo "✅ Cortex Learning Service installed and started successfully!"
    echo ""
    echo "📊 Service Status:"
    echo "   - Service: $SERVICE_NAME"
    echo "   - Logs: $SERVICE_PATH/logs/"
    echo "   - Config: $SERVICE_PATH/config/"
    echo ""
    echo "🔧 Management Commands:"
    echo "   - Stop:    launchctl stop $SERVICE_NAME"
    echo "   - Start:   launchctl start $SERVICE_NAME"
    echo "   - Restart: launchctl kickstart -k gui/\$(id -u)/$SERVICE_NAME"
    echo "   - Logs:    tail -f $SERVICE_PATH/logs/cortex_learning.log"
    echo ""
    echo "🔔 The service will now continuously learn from your Cortex data!"
else
    echo "❌ Service installation failed. Check logs for details."
    exit 1
fi