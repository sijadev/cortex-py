import unittest
from unittest.mock import patch
from click.testing import CliRunner

# Adjust the path to import from the cortex-cli package
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cortex.cli.main import cli

class TestAINeoCommands(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch('cortex.core.local_ai.LocalAI.suggest_links_for_node')
    def test_suggest_links_success(self, mock_suggest_links):
        # Mock the return value from the local, data-driven AI
        mock_suggest_links.return_value = [
            {'potential_link': 'Note2', 'common_neighbors_score': 3},
            {'potential_link': 'Note3', 'common_neighbors_score': 2}
        ]

        # The AIEngine now formats this data into a string, so we mock that output
        with patch('cortex.core.ai_engine.CortexAIEngine.suggest_links') as mock_engine_suggest:
            mock_engine_suggest.return_value = (
                "Found 2 potential links for 'Note1':\n"
                "  - Node: Note2 (Score: 3)\n"
                "  - Node: Note3 (Score: 2)"
            )

            result = self.runner.invoke(cli, ['ai', 'neo', 'suggest-links', 'Note1'])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("Found 2 potential links for 'Note1'", result.output)
            self.assertIn("- Node: Note2 (Score: 3)", result.output)
            self.assertIn("- Node: Note3 (Score: 2)", result.output)

            # Check if the engine method was called correctly
            mock_engine_suggest.assert_called_once_with(node_name='Note1')

    @patch('cortex.core.ai_engine.CortexAIEngine.suggest_links')
    def test_suggest_links_no_suggestions(self, mock_engine_suggest):
        mock_engine_suggest.return_value = "No new link suggestions found based on common neighbors."

        result = self.runner.invoke(cli, ['ai', 'neo', 'suggest-links', 'Note_Without_Links'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("No new link suggestions found", result.output)
        mock_engine_suggest.assert_called_once_with(node_name='Note_Without_Links')

    @patch('cortex.core.ai_engine.CortexAIEngine.suggest_links')
    def test_suggest_links_error(self, mock_engine_suggest):
        # Simulate an error message from the engine
        mock_engine_suggest.return_value = "[Local AI Error: Could not connect to database]"

        result = self.runner.invoke(cli, ['ai', 'neo', 'suggest-links', 'AnyNode'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("[Local AI Error: Could not connect to database]", result.output)

if __name__ == '__main__':
    unittest.main()
