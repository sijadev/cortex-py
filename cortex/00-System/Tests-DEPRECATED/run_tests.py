#!/usr/bin/env python3
"""
⚠️ DEPRECATED - DO NOT USE
Tests moved to external cortex-test-framework
"""

import sys
print("🚨 DEPRECATED TEST RUNNER")
print("Use external framework: cortex-test-framework/")
sys.exit(1)

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime
import time

class CortexTestRunner:
    """Main test runner for Cortex system"""
    
    def __init__(self, test_dir: str = "/Users/simonjanke/Projects/cortex/00-System/Tests"):
        self.test_dir = Path(test_dir)
        self.reports_dir = self.test_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Test suites
        self.test_suites = {
            'unit': 'test_cortex_system.py',
            'performance': 'test_performance.py',
            'integration': 'test_cortex_system.py::TestIntegration',
            'all': '.'
        }
    
    def install_dependencies(self):
        """Install test dependencies"""
        print("🔧 Installing test dependencies...")
        
        requirements_file = self.test_dir / "test_requirements.txt"
        if requirements_file.exists():
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True, capture_output=True, text=True, timeout=600)
                print("✅ Test dependencies installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install dependencies: {e}")
                print(f"Error output: {e.stderr}")
                return False
        else:
            print(f"❌ Requirements file not found: {requirements_file}")
            return False
    
    def run_test_suite(self, suite_name: str, verbose: bool = True, coverage: bool = True, max_workers: int = None):
        """Run a specific test suite"""
        if suite_name not in self.test_suites:
            print(f"❌ Unknown test suite: {suite_name}")
            return False
            
        test_target = self.test_suites[suite_name]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]
        # Test target
        cmd.append(str(self.test_dir / test_target) if test_target != '.' else str(self.test_dir))
        # Verbosity
        if verbose:
            cmd.extend(["-v", "-s"])
        # Parallel execution with resource limits to avoid pgrep EAGAIN errors
        if max_workers is None:
            # Conservative approach: limit to 2 workers max to avoid resource exhaustion
            max_workers = min(2, max(1, os.cpu_count() // 2))
        cmd.extend(["-n", str(max_workers), "--dist", "loadfile"])
        # Coverage
        if coverage:
            cmd.extend([
                "--cov=/Users/simonjanke/Projects/cortex/00-System",
                "--cov-report=html:" + str(self.reports_dir / f"coverage_{suite_name}_{timestamp}"),
                "--cov-report=term-missing"
            ])
        # HTML report
        html_report = self.reports_dir / f"report_{suite_name}_{timestamp}.html"
        cmd.extend(["--html=" + str(html_report), "--self-contained-html"])
        # JUnit XML for CI/CD
        junit_report = self.reports_dir / f"junit_{suite_name}_{timestamp}.xml"
        cmd.extend(["--junit-xml=" + str(junit_report)])
        # Execute tests with improved process handling
        start_time = time.time()
        try:
            # Set environment variables to improve subprocess stability
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTEST_DISABLE_PLUGIN_MANAGER'] = '0'
            
            result = subprocess.run(
                cmd, 
                cwd=self.test_dir, 
                capture_output=True, 
                text=True, 
                timeout=1800,
                env=env,
                # Prevent zombie processes and improve signal handling
                preexec_fn=None if sys.platform == 'win32' else os.setsid
            )
            end_time = time.time()
            # Generate test report
            test_report = {
                'suite': suite_name,
                'timestamp': timestamp,
                'duration_seconds': end_time - start_time,
                'return_code': result.returncode,
                'command': ' '.join(cmd),
                'stdout': result.stdout,
                'stderr': result.stderr,
                'reports': {
                    'html': str(html_report),
                    'junit': str(junit_report),
                    'coverage': str(self.reports_dir / f"coverage_{suite_name}_{timestamp}")
                }
            }
            # Save test report
            report_file = self.reports_dir / f"test_report_{suite_name}_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(test_report, f, indent=2)
            # Print results
            if result.returncode == 0:
                print(f"✅ {suite_name} tests PASSED ({end_time - start_time:.1f}s)")
            else:
                print(f"❌ {suite_name} tests FAILED ({end_time - start_time:.1f}s)")
            print(f"📊 HTML Report: {html_report}")
            if coverage:
                print(f"📈 Coverage Report: {self.reports_dir / f'coverage_{suite_name}_{timestamp}' / 'index.html'}")
            # Fix HTML accessibility issues in coverage reports
            if coverage:
                try:
                    print("🔧 Fixing HTML accessibility issues...")
                    fix_cmd = [sys.executable, str(self.test_dir / "fix_html_accessibility.py"), str(self.reports_dir)]
                    subprocess.run(fix_cmd, capture_output=True, text=True, check=True, timeout=300)
                    print("✅ HTML accessibility fixes applied")
                except Exception as e:
                    print(f"⚠️  Could not apply accessibility fixes: {e}")
            # Print stdout if there are failures or verbose mode
            if result.returncode != 0 or verbose:
                print("\n" + "="*50)
                print("TEST OUTPUT:")
                print("="*50)
                print(result.stdout)
                if result.stderr:
                    print("\nERRORS:")
                    print(result.stderr)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False
        finally:
            # Cleanup old reports after each test run
            self.cleanup_old_reports(keep=5)
    
    def cleanup_old_reports(self, keep: int = 5):
        """Remove old reports, keeping only the most recent 'keep' per report type"""
        patterns = [
            'report_unit_*.html', 'report_integration_*.html', 'report_performance_*.html',
            'test_report_unit_*.json', 'test_report_integration_*.json', 'test_report_performance_*.json',
            'junit_unit_*.xml', 'junit_integration_*.xml', 'junit_performance_*.xml',
            'coverage_unit_*', 'coverage_integration_*', 'coverage_performance_*'
        ]
        for pattern in patterns:
            files = sorted(self.reports_dir.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
            for old_file in files[keep:]:
                try:
                    if old_file.is_dir():
                        # Remove directory and its contents
                        import shutil
                        shutil.rmtree(old_file)
                    else:
                        old_file.unlink()
                except (OSError, PermissionError) as e:
                    print(f"⚠️  Could not remove {old_file}: {e}")
    
    def run_all_tests(self):
        """Run all test suites with improved error handling and resource management"""
        print("🚀 Running complete Cortex test suite...")
        
        # Clean reports first
        self.cleanup_old_reports(keep=3)
        
        # Run test suites sequentially to avoid resource conflicts
        test_results = []
        suites_to_run = ['unit', 'integration', 'performance']
        
        for suite in suites_to_run:
            print(f"\n🔧 Running {suite} tests...")
            try:
                # Run with conservative resource limits
                success = self.run_test_suite(
                    suite, 
                    verbose=False,  # Less verbose for batch runs
                    coverage=True,
                    max_workers=1   # Single worker to avoid resource conflicts
                )
                test_results.append((suite, success))
                
                # Small delay between test suites to allow cleanup
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error running {suite} tests: {e}")
                test_results.append((suite, False))
        
        # Summary
        all_passed = all(result[1] for result in test_results)
        
        print("\n📊 Test Suite Results:")
        print("-" * 40)
        for suite, passed in test_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{suite:12} | {status}")
        
        if all_passed:
            print("\n✅ All test suites passed!")
        else:
            print("\n❌ Some test suites failed. Check individual reports.")
        
        return all_passed
    
    def run_quick_smoke_test(self):
        """Run quick smoke test to verify basic functionality"""
        print("💨 Running quick smoke test...")
        
        # Just run a subset of critical tests without parallel execution
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "test_cortex_system.py::TestMultiVaultAILearningEngine::test_initialization"),
            str(self.test_dir / "test_cortex_system.py::TestCrossVaultLinker::test_initialization"),
            str(self.test_dir / "test_cortex_system.py::TestCortexManagementService::test_initialization"),
            "-v", "-s"  # No parallel execution for smoke test
        ]
        
        try:
            # Set environment for stability
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            result = subprocess.run(
                cmd, 
                cwd=self.test_dir, 
                capture_output=True, 
                text=True, 
                timeout=600,
                env=env,
                preexec_fn=None if sys.platform == 'win32' else os.setsid
            )
            
            if result.returncode == 0:
                print("✅ Smoke test PASSED - Basic functionality OK")
            else:
                print("❌ Smoke test FAILED - Basic functionality issues")
                print(result.stdout)
                print(result.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running smoke test: {e}")
            return False
    
    def generate_test_summary(self):
        """Generate summary of all test reports"""
        print("📊 Generating test summary...")
        
        report_files = list(self.reports_dir.glob("test_report_*.json"))
        
        if not report_files:
            print("No test reports found")
            return
        
        # Load all reports
        reports = []
        for report_file in sorted(report_files, reverse=True)[:10]:  # Last 10 reports
            try:
                with open(report_file, 'r') as f:
                    reports.append(json.load(f))
            except Exception as e:
                print(f"Error reading {report_file}: {e}")
        
        # Generate summary
        summary = {
            'generated_at': datetime.now().isoformat(),
            'total_reports': len(reports),
            'recent_reports': reports
        }
        
        summary_file = self.reports_dir / "test_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📋 Test summary saved to: {summary_file}")
        
        # Print recent results
        print("\nRecent Test Results:")
        print("-" * 80)
        for report in reports[:5]:
            status = "✅ PASS" if report['return_code'] == 0 else "❌ FAIL"
            suite = report['suite']
            duration = report['duration_seconds']
            timestamp = report['timestamp']
            print(f"{timestamp} | {suite:12} | {status} | {duration:6.1f}s")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Cortex Test Runner")
    parser.add_argument('action', nargs='?', default='smoke',
                       choices=['install', 'smoke', 'unit', 'integration', 'performance', 'all', 'summary'],
                       help='Test action to perform')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--no-coverage', action='store_true',
                       help='Skip coverage reporting')
    parser.add_argument('--workers', type=int, default=None,
                       help='Number of parallel test workers (default: auto-detect, max 2)')
    
    args = parser.parse_args()
    
    runner = CortexTestRunner()
    
    if args.action == 'install':
        success = runner.install_dependencies()
        sys.exit(0 if success else 1)
    
    elif args.action == 'smoke':
        success = runner.run_quick_smoke_test()
        sys.exit(0 if success else 1)
    
    elif args.action == 'summary':
        runner.generate_test_summary()
        sys.exit(0)
    
    elif args.action == 'all':
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
    
    elif args.action in ['unit', 'integration', 'performance']:
        success = runner.run_test_suite(
            args.action, 
            verbose=args.verbose, 
            coverage=not args.no_coverage,
            max_workers=args.workers
        )
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
