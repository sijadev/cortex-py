#!/usr/bin/env python3
"""
Requirements Checker for Cortex-py
==================================

Validates all requirements files and checks for problematic dependencies.
"""

import os
import sys
from pathlib import Path
import subprocess
import pkg_resources

def check_requirements_file(file_path):
    """Check a single requirements file for issues."""
    print(f"\n📁 Checking: {file_path}")
    print("=" * 50)

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        if not lines:
            print("⚠️  File is empty")
            return True

        print(f"📄 Found {len(lines)} lines")

        problematic_deps = []
        valid_deps = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Check for known problematic dependencies
            if 'unittest-mock' in line:
                problematic_deps.append(f"Line {line_num}: {line} (obsolete - part of stdlib)")
            elif line:
                valid_deps.append(f"Line {line_num}: {line}")

        if problematic_deps:
            print("❌ Problematic dependencies found:")
            for dep in problematic_deps:
                print(f"   {dep}")
            return False

        if valid_deps:
            print("✅ Valid dependencies:")
            for dep in valid_deps[:10]:  # Show first 10
                print(f"   {dep}")
            if len(valid_deps) > 10:
                print(f"   ... and {len(valid_deps) - 10} more")

        return True

    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def main():
    """Main function to check all requirements files."""
    print("🔍 Cortex-py Requirements Checker")
    print("=" * 50)

    # Find all requirements files
    requirements_files = []

    # Main project requirements
    for pattern in ['requirements.txt', 'requirements-dev.txt']:
        file_path = Path(pattern)
        if file_path.exists():
            requirements_files.append(str(file_path))

    # Subproject requirements
    for subdir in ['cortex_neo', 'cortex-cli']:
        subdir_path = Path(subdir)
        if subdir_path.exists():
            for pattern in ['requirements.txt', 'requirements-dev.txt']:
                file_path = subdir_path / pattern
                if file_path.exists():
                    requirements_files.append(str(file_path))

    if not requirements_files:
        print("❌ No requirements files found!")
        return 1

    print(f"📋 Found {len(requirements_files)} requirements files:")
    for f in requirements_files:
        print(f"   - {f}")

    # Check each file
    all_valid = True
    for req_file in requirements_files:
        is_valid = check_requirements_file(req_file)
        if not is_valid:
            all_valid = False

    # Summary
    print(f"\n🎯 Summary:")
    if all_valid:
        print("✅ All requirements files are valid!")
        print("📦 Dependencies should install without issues")
        return 0
    else:
        print("❌ Some requirements files have issues")
        print("🔧 Please fix the problematic dependencies")
        return 1

if __name__ == "__main__":
    sys.exit(main())
