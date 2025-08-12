#!/usr/bin/env python3
"""
Test runner for Cortex CLI
Runs all test suites and provides comprehensive test results
"""

import sys
import unittest
import subprocess
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_unittest_suite():
    """Run the unittest test suite"""
    print("🧪 Running Unit Tests...")
    print("=" * 50)
    
    # Discover and run all unit tests
    loader = unittest.TestLoader()
    start_dir = str(Path(__file__).parent)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_pytest_suite():
    """Run pytest tests if pytest is available"""
    print("\n🔬 Running Pytest Suite...")
    print("=" * 50)
    
    try:
        # Try to run pytest
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            str(Path(__file__).parent),
            '-v', '--tb=short'
        ], capture_output=True, text=True, cwd=project_root)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print("⚠️  pytest not found - install with: pip install pytest")
        return True  # Don't fail if pytest is not available


def run_specific_test_categories():
    """Run specific test categories"""
    categories = [
        ("CLI Commands", "test_cli_commands.py"),
        ("Integration", "test_integration.py"), 
        ("Performance", "test_performance.py")
    ]
    
    results = {}
    
    for category_name, test_file in categories:
        print(f"\n🎯 Running {category_name} Tests...")
        print("=" * 50)
        
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'unittest', 
                    f'tests.{test_file[:-3]}', '-v'
                ], capture_output=True, text=True, cwd=project_root)
                
                print(result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
                
                results[category_name] = result.returncode == 0
                
            except Exception as e:
                print(f"❌ Error running {category_name} tests: {e}")
                results[category_name] = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results[category_name] = False
    
    return results


def run_cli_smoke_tests():
    """Run basic smoke tests on the CLI"""
    print("\n💨 Running CLI Smoke Tests...")
    print("=" * 50)
    
    # Import CLI for testing
    try:
        from cortex.cli.main import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        smoke_tests = [
            (['--help'], "Should show help"),
            (['--version'], "Should show version"),
            (['analysis', '--help'], "Should show analysis help"),
            (['test', '--help'], "Should show test help"),
            (['linking', '--help'], "Should show linking help"),
        ]
        
        passed = 0
        failed = 0
        
        for cmd, description in smoke_tests:
            try:
                result = runner.invoke(cli, cmd)
                if result.exit_code == 0:
                    print(f"✅ {' '.join(cmd)}: {description}")
                    passed += 1
                else:
                    print(f"❌ {' '.join(cmd)}: Failed with exit code {result.exit_code}")
                    failed += 1
            except Exception as e:
                print(f"❌ {' '.join(cmd)}: Exception - {e}")
                failed += 1
        
        print(f"\nSmoke Test Results: {passed} passed, {failed} failed")
        return failed == 0
        
    except ImportError as e:
        print(f"❌ Could not import CLI for smoke tests: {e}")
        return False


def generate_test_report(results):
    """Generate a comprehensive test report"""
    print("\n📊 Test Report Summary")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Test Categories: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
    
    print("\nDetailed Results:")
    for category, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {category}")
    
    return failed_tests == 0


def main():
    """Main test runner function"""
    print("🚀 Cortex CLI Test Suite")
    print("=" * 50)
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Project Root: {project_root}")
    
    # Run smoke tests first
    smoke_passed = run_cli_smoke_tests()
    
    # Run specific test categories
    category_results = run_specific_test_categories()
    
    # Try pytest if available
    pytest_passed = run_pytest_suite()
    
    # Compile all results
    all_results = {
        "Smoke Tests": smoke_passed,
        "Pytest Suite": pytest_passed,
        **category_results
    }
    
    # Generate final report
    overall_success = generate_test_report(all_results)
    
    if overall_success:
        print("\n🎉 All tests completed successfully!")
        return 0
    else:
        print("\n💥 Some tests failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
