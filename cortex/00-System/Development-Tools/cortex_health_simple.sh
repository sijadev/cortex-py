#!/bin/bash
# Cortex Health Check Command
# Simple health check function for cortex-cmd

CORTEX_PATH="/Users/simonjanke/Projects/cortex"

echo "🔍 Cortex Health Check"
echo "====================="

# Check critical files
echo ""
echo "📄 Checking critical files..."

critical_files=(
    "Cortex-Hub.md"
    "State-Management.md" 
    "00-System/Algorithms/confidence_calculator.py"
    "cortex-cmd"
)

for file in "${critical_files[@]}"; do
    if [[ -f "$CORTEX_PATH/$file" ]]; then
        if [[ -s "$CORTEX_PATH/$file" ]]; then
            echo "  ✅ $file ($(du -h "$CORTEX_PATH/$file" | cut -f1))"
        else
            echo "  ⚠️  $file (empty file)"
        fi
    else
        echo "  ❌ $file (missing)"
    fi
done

# Check directories
echo ""
echo "📁 Checking directory structure..."
required_dirs=("00-System" "00-Templates" "01-Projects" "02-Neural-Links" "03-Decisions" "05-Insights")
for dir in "${required_dirs[@]}"; do
    if [[ -d "$CORTEX_PATH/$dir" ]]; then
        count=$(find "$CORTEX_PATH/$dir" -name "*.md" 2>/dev/null | wc -l)
        echo "  ✅ $dir ($count files)"
    else
        echo "  ❌ Missing: $dir"
    fi
done

# Test Python script
echo ""
echo "🐍 Testing Python components..."
if python3 -c "import sys; print('Python', sys.version.split()[0], 'available')" 2>/dev/null; then
    echo "  ✅ Python 3 available"
    if python3 "$CORTEX_PATH/00-System/Algorithms/confidence_calculator.py" >/dev/null 2>&1; then
        echo "  ✅ Confidence calculator working"
    else
        echo "  ⚠️  Confidence calculator has issues"
    fi
else
    echo "  ❌ Python 3 not available"
fi

# Check services
echo ""
echo "🤖 Checking services..."
if [[ -f "$CORTEX_PATH/00-System/Services/manage_service.sh" ]]; then
    echo "  ✅ Learning service manager available"
else
    echo "  ⚠️  Learning service manager missing"
fi

echo ""
echo "🎯 Health check completed!"
