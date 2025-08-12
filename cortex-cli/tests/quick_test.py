#!/usr/bin/env python3
"""
Quick test runner for Cortex CLI
Runs essential tests without external dependencies
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_core_tests():
    """Run core CLI command tests"""
    print("🧪 Running Core CLI Tests...")
    print("=" * 50)
    
    # Import test modules
    from tests.test_cli_commands import (
        TestMainCommands, TestAnalysisCommands, 
        TestTestCommands, TestLinkingCommands,
        TestCommandIntegration, TestCommandValidation
    )
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestMainCommands,
        TestAnalysisCommands, 
        TestTestCommands,
        TestLinkingCommands,
        TestCommandIntegration,
        TestCommandValidation
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def test_cli_functionality():
    """Test basic CLI functionality"""
    print("\n💨 Testing CLI Functionality...")
    print("=" * 50)
    
    try:
        from cortex.cli.main import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        # Test basic commands
        tests = [
            (['--help'], "Help system"),
            (['--version'], "Version info"),
            (['status'], "Status command"),
            (['analysis', '--help'], "Analysis help"),
            (['test', '--help'], "Test help"),
            (['linking', '--help'], "Linking help")
        ]
        
        passed = 0
        total = len(tests)
        
        for cmd, desc in tests:
            result = runner.invoke(cli, cmd)
            if result.exit_code == 0:
                print(f"✅ {desc}: PASSED")
                passed += 1
            else:
                print(f"❌ {desc}: FAILED (exit code: {result.exit_code})")
        
        print(f"\nFunctionality Tests: {passed}/{total} passed")
        return passed == total
        
    except ImportError as e:
        print(f"❌ Could not import CLI: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Cortex CLI Quick Test Suite")
    print("=" * 50)
    
    # Run core tests
    result = run_core_tests()
    
    # Test CLI functionality 
    cli_passed = test_cli_functionality()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    unittest_passed = result.wasSuccessful()
    
    print(f"Unit Tests: {'✅ PASSED' if unittest_passed else '❌ FAILED'}")
    print(f"CLI Tests: {'✅ PASSED' if cli_passed else '❌ FAILED'}")
    
    if unittest_passed and cli_passed:
        print("\n🎉 All core tests passed!")
        return 0
    else:
        print("\n💥 Some tests failed.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
