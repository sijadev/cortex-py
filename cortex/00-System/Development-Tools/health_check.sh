#!/bin/bash
# Cortex System Health Check - Improved Error Detection
# Safe file searching with proper escaping

CORTEX_PATH="/Users/simonjanke/Projects/cortex"

echo "🔍 Cortex Error Detection & Health Check"
echo "========================================"

# 1. Check for empty files
echo ""
echo "📄 Checking for empty files..."
find "$CORTEX_PATH" -type f -name "*.md" -size 0 2>/dev/null | while read -r file; do
    echo "  ❌ Empty file: $(basename "$file")"
done

# 2. Check for Python scripts and test them
echo ""
echo "🐍 Testing Python scripts..."
find "$CORTEX_PATH" -type f -name "*.py" 2>/dev/null | while read -r script; do
    echo "  Testing: $(basename "$script")"
    if python3 -m py_compile "$script" 2>/dev/null; then
        echo "  ✅ Syntax OK: $(basename "$script")"
    else
        echo "  ❌ Syntax Error: $(basename "$script")"
    fi
done

# 3. Check for TODO/FIXME markers
echo ""
echo "📝 Checking for TODO/FIXME markers..."
find "$CORTEX_PATH" -type f -name "*.md" -exec grep -l "TODO\|FIXME\|BUG\|ISSUE" {} \; 2>/dev/null | while read -r file; do
    echo "  📌 Contains markers: $(basename "$file")"
    grep -n "TODO\|FIXME\|BUG\|ISSUE" "$file" 2>/dev/null | head -3
done

# 4. Check for broken internal links
echo ""
echo "🔗 Checking for potential broken links..."
find "$CORTEX_PATH" -type f -name "*.md" -exec grep -l "\[\[.*\]\]" {} \; 2>/dev/null | while read -r file; do
    # Extract [[links]] and check if target files exist
    grep -o "\[\[[^]]*\]\]" "$file" 2>/dev/null | while read -r link; do
        target=$(echo "$link" | sed 's/\[\[\(.*\)\]\]/\1/')
        if [[ ! -f "$CORTEX_PATH/$target.md" && ! -f "$CORTEX_PATH"/*/"$target.md" ]]; then
            echo "  ⚠️  Potential broken link in $(basename "$file"): $link"
        fi
    done
done

# 5. Check directory structure integrity
echo ""
echo "📁 Checking directory structure..."
required_dirs=("00-System" "00-Templates" "01-Projects" "02-Neural-Links" "03-Decisions" "05-Insights")
for dir in "${required_dirs[@]}"; do
    if [[ -d "$CORTEX_PATH/$dir" ]]; then
        echo "  ✅ $dir exists"
    else
        echo "  ❌ Missing directory: $dir"
    fi
done

# 6. Check file permissions
echo ""
echo "🔒 Checking file permissions..."
if [[ -x "$CORTEX_PATH/cortex-cmd" ]]; then
    echo "  ✅ cortex-cmd is executable"
else
    echo "  ❌ cortex-cmd is not executable"
fi

# 7. Check for large files that might cause performance issues
echo ""
echo "📊 Checking for large files..."
find "$CORTEX_PATH" -type f -size +1M 2>/dev/null | while read -r file; do
    size=$(du -h "$file" | cut -f1)
    echo "  📈 Large file: $(basename "$file") ($size)"
done

echo ""
echo "🎯 Health check completed!"
