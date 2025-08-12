#!/usr/bin/env python3
"""
Test Disabler - Prevents accidental execution of deprecated tests
"""

import sys
import os

print("🚨 DEPRECATED TEST SUITE - DO NOT RUN")
print("=" * 50)
print("These tests are incompatible with the new rule-based linking system.")
print("")
print("API Changes:")
print("- CrossVaultLinker now uses AdaptiveRuleEngine")
print("- LinkSuggestion and VaultConnection classes removed") 
print("- run_full_linking_cycle() returns different data structure")
print("")
print("Migration Required:")
print("- Use external test framework: cortex-test-framework/")
print("- Update imports and test expectations")
print("- Add link_rules.yaml configuration")
print("")
print("Last working version: 2025-08-10 21:05:00")
print("Coverage: 77% (24 tests passed)")
print("")
print("❌ TESTS DISABLED TO PREVENT BROKEN BUILDS")
print("=" * 50)

sys.exit(1)  # Fail fast to prevent execution