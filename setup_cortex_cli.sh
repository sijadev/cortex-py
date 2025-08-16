#!/bin/bash
# Cortex CLI Setup für macOS
# Installiert die neue strukturierte CLI und macht sie systemweit verfügbar

echo "🚀 Setting up Cortex CLI for macOS..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip3 install click neo4j

# Make cortex executable
chmod +x /Users/simonjanke/Projects/cortex-py/bin/cortex

# Add to PATH if not already there
if ! echo $PATH | grep -q "/Users/simonjanke/Projects/cortex-py/bin"; then
    echo "🔧 Adding Cortex CLI to PATH..."
    echo 'export PATH="/Users/simonjanke/Projects/cortex-py/bin:$PATH"' >> ~/.zshrc
    echo 'export PATH="/Users/simonjanke/Projects/cortex-py/bin:$PATH"' >> ~/.bash_profile
    echo "✅ PATH updated. Restart your terminal or run: source ~/.zshrc"
fi

echo "🎯 Testing Cortex CLI..."
cd /Users/simonjanke/Projects/cortex-py
python bin/cortex --help

echo ""
echo "✨ Cortex CLI Setup Complete!"
echo ""
echo "📋 Available Commands:"
echo "   cortex                    # Quick system status"
echo "   cortex system status      # System overview"
echo "   cortex content create     # Create content"
echo "   cortex tags list          # List tags"
echo "   cortex graph network      # Network analysis"
echo "   cortex ai enhance         # AI enhancement"
echo ""
echo "💡 For full command list: cortex --help"
