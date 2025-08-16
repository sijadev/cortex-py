#!/usr/bin/env python3
"""
Cortex Smoke Tests Runner
Simple smoke tests to verify basic system functionality
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_main_script():
    """Test main.py execution"""
    print("🧪 Testing main.py...")
    try:
        result = subprocess.run([sys.executable, "main.py"],
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ main.py executed successfully")
            return True
        else:
            print(f"❌ main.py failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Exception running main.py: {e}")
        return False

def test_cortex_direct():
    """Test cortex_direct.py execution"""
    print("🧪 Testing cortex_direct.py...")
    try:
        result = subprocess.run([sys.executable, "cortex_direct.py"],
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ cortex_direct.py executed successfully")
            if result.stdout:
                print(f"Output preview: {result.stdout[:100]}...")
            return True
        else:
            print(f"❌ cortex_direct.py failed with return code {result.returncode}")
            return False
    except Exception as e:
        print(f"❌ Exception running cortex_direct.py: {e}")
        return False

def test_imports():
    """Test basic imports"""
    print("🧪 Testing core imports...")

    tests = [
        ("src.cortex_system_config", "CortexSystemConfig"),
        ("src.safe_transactions", "SafeTransactionManager"),
    ]

    passed = 0
    for module_name, class_name in tests:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name} imported successfully")
            passed += 1
        except Exception as e:
            print(f"❌ Failed to import {module_name}.{class_name}: {e}")

    return passed == len(tests)

def test_file_structure():
    """Test critical files exist"""
    print("🧪 Testing file structure...")

    critical_files = [
        "main.py",
        "cortex_direct.py",
        "src/cortex_system_config.py",
        "src/safe_transactions.py",
        "requirements.txt"
    ]

    passed = 0
    for file_path in critical_files:
        if (project_root / file_path).exists():
            print(f"✅ {file_path} exists")
            passed += 1
        else:
            print(f"❌ {file_path} missing")

    return passed == len(critical_files)

def run_smoke_tests():
    """Run all smoke tests"""
    print("🚀 Cortex Smoke Tests")
    print("=" * 50)

    # Change to project directory
    os.chdir(project_root)

    results = {}

    # Run tests
    results["File Structure"] = test_file_structure()
    results["Core Imports"] = test_imports()
    results["Main Script"] = test_main_script()
    results["Direct CLI"] = test_cortex_direct()

    # Summary
    print("\n" + "=" * 50)
    print("📊 SMOKE TEST RESULTS")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All smoke tests passed!")
        return True
    else:
        print("⚠️  Some smoke tests failed - check output above")
        return False

if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
