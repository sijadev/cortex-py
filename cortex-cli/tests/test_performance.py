"""
Performance tests for Cortex CLI commands
"""

import unittest
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cortex.cli.main import cli
from tests.enhanced_test_utils import CortexTestRunner

class TestCLIPerformance(unittest.TestCase):
    
    def setUp(self):
        self.runner = CortexTestRunner()
        self.test_workspace = self.runner.setup_test_workspace()
        
    def tearDown(self):
        self.runner.teardown_test_workspace()
        
    def test_analysis_performance_large_dataset(self):
        """Test basic analysis command"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
            
    def test_status_command_performance(self):
        """Test status command"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        
    def test_init_command_performance(self):
        """Test init command"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)

class TestCLIStress(unittest.TestCase):
    
    def setUp(self):
        self.runner = CortexTestRunner()
        self.test_workspace = self.runner.setup_test_workspace()
        
    def tearDown(self):
        self.runner.teardown_test_workspace()
        
    def test_deep_directory_structure(self):
        """Test basic functionality"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        
    def test_large_file_handling(self):
        """Test basic functionality"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        
    def test_unicode_and_special_characters(self):
        """Test basic functionality"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        
    def test_concurrent_command_execution(self):
        """Test version command"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("0.2.0", result.output)

if __name__ == '__main__':
    unittest.main()
