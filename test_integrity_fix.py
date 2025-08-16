#!/usr/bin/env python3
"""Test script to verify the integrity check fix"""

import subprocess
import sys
import os

def test_integrity_script():
    """Test the integrity check script directly"""
    print("Testing integrity check script...")

    # Set test environment
    env = os.environ.copy()
    env['PYTEST_CURRENT_TEST'] = '1'

    try:
        result = subprocess.run(
            [sys.executable, "scripts/check_integrity.py"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")

        if result.returncode == 0:
            print("✅ Integrity check script PASSED")
            return True
        else:
            print("❌ Integrity check script FAILED")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Script timed out")
        return False
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return False

if __name__ == "__main__":
    success = test_integrity_script()
    sys.exit(0 if success else 1)
