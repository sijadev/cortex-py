#!/usr/bin/env python3
"""
Integration tests for the complete Obsidian MCP integration workflow
Tests the full pipeline from Cortex AI analysis to Obsidian note creation
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import logging

# Add paths for imports
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/AI-Learning-Engine')
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/Cross-Vault-Linker')
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/Management-Service')

# Set up logging for tests
logging.basicConfig(level=logging.INFO)

class TestFullWorkflowIntegration:
    """Test the complete workflow from AI analysis to Obsidian sync"""
    
    @pytest.fixture
    def temp_cortex_environment(self):
        """Create a complete temporary Cortex environment"""
        temp_dir = tempfile.mkdtemp()
        cortex_path = Path(temp_dir) / "cortex"
        
        # Create full directory structure
        directories = [
            "00-System/AI-Learning-Engine/data",
            "00-System/AI-Learning-Engine/logs",
            "00-System/Cross-Vault-Linker/data",
            "00-System/Cross-Vault-Linker/logs",
            "00-System/Management-Service/data",
            "00-System/Management-Service/logs",
            "01-Projects/TEST-PROJECT",
            "02-Neural-Links/AI-Generated",
            "02-Neural-Links/Summaries", 
            "02-Neural-Links/Chat-Sessions",
            "03-Decisions",
            "04-Code-Fragments",
            "05-Insights"
        ]
        
        for directory in directories:
            (cortex_path / directory).mkdir(parents=True, exist_ok=True)
        
        # Create sample files for AI analysis
        sample_files = {
            "01-Projects/TEST-PROJECT/project-overview.md": """# Test Project Overview

This project demonstrates #ai-learning and #pattern-recognition capabilities.

## Goals
- Implement intelligent linking
- Test cross-vault connections
- Validate AI insights

#project #testing #cortex-ai
""",
            "03-Decisions/ADR-001-Test-Decision.md": """# ADR-001: Test Decision Architecture

## Status
Accepted

## Context
We need to test the decision linking patterns in the #cortex-ai system.

## Decision
Use pattern-recognition for automated decision tracking.

## Consequences
- Better #ai-learning integration
- Improved #cross-vault connections

#adr #decision #testing
""",
            "04-Code-Fragments/test-patterns.md": """# Test Code Patterns

## Authentication Pattern
```python
def authenticate_user(credentials):
    # AI-generated authentication logic
    return validate_and_return_token(credentials)
```

This pattern is used across #multiple-projects for #authentication.

#code-pattern #python #authentication
""",
            "05-Insights/previous-insight.md": """# Previous AI Insight

Generated insight about #cross-vault patterns and #ai-learning.

The system shows strong correlation between #project documentation and #decisions.

#ai-insight #correlation #pattern-analysis
"""
        }
        
        for file_path, content in sample_files.items():
            full_path = cortex_path / file_path
            with open(full_path, 'w') as f:
                f.write(content)
        
        # Create sample AI learning data
        ai_data = {
            "vault_profiles": [
                {
                    "vault_name": "cortex",
                    "file_count": 4,
                    "unique_tags": ["ai-learning", "pattern-recognition", "project", "testing", "cortex-ai"],
                    "last_analyzed": datetime.now().isoformat()
                }
            ],
            "tag_correlations": [
                {
                    "tag1": "ai-learning",
                    "tag2": "pattern-recognition",
                    "correlation_score": 0.85,
                    "shared_files": ["project-overview.md", "previous-insight.md"]
                },
                {
                    "tag1": "project",
                    "tag2": "testing", 
                    "correlation_score": 0.92,
                    "shared_files": ["project-overview.md", "ADR-001-Test-Decision.md"]
                }
            ],
            "cross_vault_patterns": [],
            "insights": [
                {
                    "insight_type": "Cross-Vault Pattern",
                    "description": "Strong correlation between project documentation and decision records",
                    "pattern": "Projects with detailed documentation tend to have more structured decisions",
                    "related_tags": ["project", "decision", "documentation"],
                    "related_vaults": ["cortex"],
                    "confidence": 0.88,
                    "strength": 15
                }
            ]
        }
        
        ai_data_path = cortex_path / "00-System/AI-Learning-Engine/data"
        with open(ai_data_path / "vault_profiles.json", 'w') as f:
            json.dump(ai_data["vault_profiles"], f, indent=2)
        with open(ai_data_path / "tag_correlations.json", 'w') as f:
            json.dump(ai_data["tag_correlations"], f, indent=2)
        with open(ai_data_path / "cross_vault_patterns.json", 'w') as f:
            json.dump(ai_data["cross_vault_patterns"], f, indent=2)
        
        # Create sample cross-vault linking data
        link_data = {
            "link_suggestions": [
                {
                    "source_vault": "cortex",
                    "source_file": "01-Projects/TEST-PROJECT/project-overview.md",
                    "target_vault": "cortex", 
                    "target_file": "03-Decisions/ADR-001-Test-Decision.md",
                    "correlation_score": 0.89,
                    "shared_tags": ["testing", "cortex-ai"],
                    "confidence": 0.89,
                    "reason": "Strong tag correlation and semantic similarity",
                    "link_type": "strong",
                    "created_date": datetime.now().isoformat()
                }
            ],
            "vault_connections": [
                {
                    "vault1": "cortex",
                    "vault2": "cortex", 
                    "connection_strength": 0.85,
                    "shared_tags": ["ai-learning", "testing"],
                    "common_files": 4,
                    "last_updated": datetime.now().isoformat()
                }
            ]
        }
        
        linker_data_path = cortex_path / "00-System/Cross-Vault-Linker/data"
        with open(linker_data_path / "link_suggestions.json", 'w') as f:
            json.dump(link_data["link_suggestions"], f, indent=2, default=str)
        with open(linker_data_path / "vault_connections.json", 'w') as f:
            json.dump(link_data["vault_connections"], f, indent=2, default=str)
        
        yield str(cortex_path), ai_data, link_data
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_ai_to_obsidian_workflow(self, temp_cortex_environment):
        """Test the complete workflow from AI analysis to Obsidian sync"""
        cortex_path, ai_data, link_data = temp_cortex_environment
        
        # Import modules with the test environment
        from obsidian_mcp_bridge import ObsidianMCPBridge, integrate_with_obsidian
        
        # Create bridge with test environment
        bridge = ObsidianMCPBridge(cortex_path=cortex_path)
        bridge.supported_vaults["cortex"] = cortex_path
        
        # Prepare AI insights from the sample data
        ai_insights = []
        for insight in ai_data["insights"]:
            ai_insights.append({
                'topic': insight["insight_type"],
                'summary': insight["description"],
                'findings': [insight["pattern"]],
                'related_concepts': insight["related_tags"],
                'cross_vault_connections': [],
                'tags': insight["related_tags"] + ['integration-test', 'ai-generated'],
                'source_vaults': insight["related_vaults"],
                'correlation_count': insight["strength"],
                'confidence': insight["confidence"],
                'pattern_types': ['cross-vault-analysis']
            })
        
        # Prepare cross-vault links
        cross_vault_links = []
        for suggestion in link_data["link_suggestions"]:
            cross_vault_links.append({
                'source_file': suggestion["source_file"],
                'target_file': suggestion["target_file"],
                'target_vault': suggestion["target_vault"],
                'confidence': suggestion["confidence"],
                'shared_tags': suggestion["shared_tags"],
                'reason': suggestion["reason"],
                'link_type': suggestion["link_type"]
            })
        
        # Test full integration
        result = await integrate_with_obsidian(
            ai_insights=ai_insights,
            cross_vault_links=cross_vault_links,
            target_vault="cortex"
        )
        
        # Verify integration results
        assert result.success is True
        assert result.notes_created >= 2  # At least insight note and link summary
        assert result.execution_time > 0
        
        # Verify files were created in correct locations
        ai_generated_path = Path(cortex_path) / "02-Neural-Links" / "AI-Generated"
        summaries_path = Path(cortex_path) / "02-Neural-Links" / "Summaries"
        
        # Check AI insight notes
        insight_files = list(ai_generated_path.glob("Cortex Insight*.md"))
        assert len(insight_files) >= 1
        
        # Verify insight note content
        with open(insight_files[0], 'r') as f:
            insight_content = f.read()
        
        assert "Cross-Vault Pattern" in insight_content
        assert "Strong correlation between project documentation" in insight_content
        assert "#integration-test" in insight_content
        assert "Confidence: 0.88" in insight_content
        
        # Check link summary notes
        summary_files = list(summaries_path.glob("Cross-Vault Link Summary*.md"))
        assert len(summary_files) >= 1
        
        # Verify summary content
        with open(summary_files[0], 'r') as f:
            summary_content = f.read()
        
        assert "Cross-Vault Link Summary" in summary_content
        assert "Strong Connections" in summary_content
        assert "project-overview.md" in summary_content
        assert "ADR-001-Test-Decision.md" in summary_content
        assert "0.89" in summary_content
    
    @pytest.mark.asyncio
    async def test_chat_to_obsidian_integration(self, temp_cortex_environment):
        """Test chat session integration with Obsidian"""
        cortex_path, _, _ = temp_cortex_environment
        
        from chat_obsidian_sync import ChatObsidianSyncer, ChatMessage
        from obsidian_mcp_bridge import ObsidianMCPBridge
        
        # Create test chat session
        messages = [
            ChatMessage(
                role='user',
                content='We need to implement MCP integration for Obsidian. How should we structure the tests?',
                timestamp='2025-01-10T10:00:00'
            ),
            ChatMessage(
                role='assistant', 
                content='For MCP integration testing, I recommend creating unit tests for the bridge functionality and integration tests for the full workflow. We should test:\n\n```python\ndef test_mcp_bridge():\n    # Test bridge creation and sync\n    bridge = ObsidianMCPBridge()\n    result = bridge.sync_insights()\n    assert result.success\n```\n\nThis approach ensures comprehensive coverage. The decision is to use pytest with async support.',
                timestamp='2025-01-10T10:01:00'
            ),
            ChatMessage(
                role='user',
                content='Perfect! I decided to implement the testing framework as suggested. We need to create comprehensive test coverage by tomorrow.',
                timestamp='2025-01-10T10:02:00'
            )
        ]
        
        # Create syncer with test environment
        syncer = ChatObsidianSyncer()
        
        # Mock the bridge to use our test environment
        with patch('chat_obsidian_sync.ObsidianMCPBridge') as mock_bridge_class:
            mock_bridge = ObsidianMCPBridge(cortex_path=cortex_path)
            mock_bridge.supported_vaults["cortex"] = cortex_path
            mock_bridge_class.return_value = mock_bridge
            
            # Test the sync
            session_context = {
                'topic': 'MCP Integration Testing',
                'session_id': 'integration_test_123'
            }
            
            result = await syncer.sync_chat_session(messages, session_context)
            
            assert result is True
            
            # Verify chat session file was created
            chat_sessions_path = Path(cortex_path) / "02-Neural-Links" / "Chat-Sessions"
            chat_files = list(chat_sessions_path.glob("Claude Chat*.md"))
            assert len(chat_files) >= 1
            
            # Verify content
            with open(chat_files[0], 'r') as f:
                chat_content = f.read()
            
            assert "MCP Integration Testing" in chat_content
            assert "implement MCP integration" in chat_content
            assert "pytest with async support" in chat_content
            assert "def test_mcp_bridge" in chat_content
            assert "Decision" in chat_content
            assert "Action Items" in chat_content
    
    @pytest.mark.asyncio
    async def test_cross_vault_linker_obsidian_integration(self, temp_cortex_environment):
        """Test the Cross-Vault-Linker integration with Obsidian"""
        cortex_path, _, _ = temp_cortex_environment
        
        from cross_vault_linker import CrossVaultLinker
        
        # Create linker with test environment
        linker = CrossVaultLinker(cortex_hub_path=cortex_path)
        
        # Mock the obsidian integration in the linker
        with patch.object(linker, 'sync_to_obsidian') as mock_sync:
            mock_sync.return_value = None  # Successful async return
            
            # Run full linking cycle with Obsidian sync
            report = linker.run_full_linking_cycle(sync_to_obsidian=True)
            
            # Verify linker ran successfully
            assert report is not None
            assert 'summary' in report
            
            # Verify sync was called
            mock_sync.assert_called_once()
    
    def test_file_watcher_integration_setup(self, temp_cortex_environment):
        """Test file watcher setup for real-time sync"""
        cortex_path, _, _ = temp_cortex_environment
        
        # Test that we can set up file watching on the vault
        from pathlib import Path
        
        vault_path = Path(cortex_path)
        
        # Verify all expected directories exist for watching
        expected_dirs = [
            "01-Projects",
            "03-Decisions", 
            "04-Code-Fragments",
            "05-Insights"
        ]
        
        for dir_name in expected_dirs:
            dir_path = vault_path / dir_name
            assert dir_path.exists()
            assert dir_path.is_dir()
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience(self, temp_cortex_environment):
        """Test error recovery and system resilience"""
        cortex_path, _, _ = temp_cortex_environment
        
        from obsidian_mcp_bridge import ObsidianMCPBridge, integrate_with_obsidian
        
        # Test with malformed data
        malformed_insights = [
            {
                'topic': None,  # Invalid topic
                'summary': '',   # Empty summary
                'tags': [],     # No tags
                'confidence': 'invalid'  # Invalid confidence type
            }
        ]
        
        malformed_links = [
            {
                'source_file': '',  # Empty file
                'confidence': 2.0,  # Invalid confidence range
                'shared_tags': None  # Invalid tags
            }
        ]
        
        # Test that integration handles errors gracefully
        result = await integrate_with_obsidian(
            ai_insights=malformed_insights,
            cross_vault_links=malformed_links,
            target_vault="nonexistent_vault"
        )
        
        # Should not crash, but may have errors
        assert isinstance(result.errors, list)
        # Should still return a valid result structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'execution_time')
    
    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, temp_cortex_environment):
        """Test performance with large amounts of data"""
        cortex_path, _, _ = temp_cortex_environment
        
        from obsidian_mcp_bridge import integrate_with_obsidian
        
        # Create large dataset
        large_insights = []
        for i in range(20):  # 20 insights
            large_insights.append({
                'topic': f'Performance Test Insight {i}',
                'summary': f'This is test insight {i} for performance testing. ' * 10,
                'findings': [f'Finding {j}' for j in range(10)],
                'related_concepts': [f'Concept {j}' for j in range(15)],
                'tags': [f'perf-test-{i}', f'insight-{i}', 'performance'],
                'confidence': 0.7 + (i * 0.01),  # Varying confidence
                'correlation_count': i * 2
            })
        
        large_links = []
        for i in range(50):  # 50 link suggestions
            large_links.append({
                'source_file': f'source-{i}.md',
                'target_file': f'target-{i}.md',
                'target_vault': 'cortex',
                'confidence': 0.5 + (i * 0.01),
                'shared_tags': [f'tag-{i}', f'shared-{i%5}'],
                'reason': f'Performance test link {i}',
                'link_type': 'medium' if i % 2 else 'strong'
            })
        
        start_time = datetime.now()
        
        result = await integrate_with_obsidian(
            ai_insights=large_insights,
            cross_vault_links=large_links,
            target_vault="cortex"
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        assert execution_time < 30.0  # Should complete within 30 seconds
        assert result.notes_created >= 20  # Should create notes for insights
        assert result.execution_time > 0
        
        # Verify file system impact
        ai_generated_path = Path(cortex_path) / "02-Neural-Links" / "AI-Generated"
        created_files = list(ai_generated_path.glob("*.md"))
        
        # Should have created multiple files efficiently
        assert len(created_files) > 0
        
        # Check that files have reasonable sizes (not too large)
        for file_path in created_files[:5]:  # Check first 5 files
            file_size = file_path.stat().st_size
            assert 100 < file_size < 100000  # Reasonable file size range
    
    def test_data_consistency_and_integrity(self, temp_cortex_environment):
        """Test data consistency and integrity across operations"""
        cortex_path, _, _ = temp_cortex_environment
        
        from obsidian_mcp_bridge import ObsidianMCPBridge
        
        bridge = ObsidianMCPBridge(cortex_path=cortex_path)
        bridge.supported_vaults["cortex"] = cortex_path
        
        # Test metadata consistency
        initial_metadata = bridge.sync_metadata.copy()
        
        # Simulate some operations
        bridge.sync_metadata['synced_notes']['test.md'] = {
            'created': datetime.now().isoformat(),
            'type': 'test',
            'hash': 'test_hash'
        }
        
        bridge._save_sync_metadata()
        
        # Create new bridge instance and verify metadata persisted
        new_bridge = ObsidianMCPBridge(cortex_path=cortex_path)
        new_bridge.supported_vaults["cortex"] = cortex_path
        
        assert 'test.md' in new_bridge.sync_metadata['synced_notes']
        assert new_bridge.sync_metadata['synced_notes']['test.md']['type'] == 'test'
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, temp_cortex_environment):
        """Test concurrent operations and thread safety"""
        cortex_path, ai_data, _ = temp_cortex_environment
        
        from obsidian_mcp_bridge import ObsidianMCPBridge
        
        bridge = ObsidianMCPBridge(cortex_path=cortex_path)
        bridge.supported_vaults["cortex"] = cortex_path
        
        # Prepare multiple insights for concurrent creation
        insights = []
        for i in range(5):
            insights.append({
                'topic': f'Concurrent Test Insight {i}',
                'summary': f'Concurrent test insight {i}',
                'tags': [f'concurrent-{i}', 'test'],
                'confidence': 0.8
            })
        
        # Create insights concurrently
        tasks = [
            bridge.create_cortex_insight_note(insight, "cortex")
            for insight in insights
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all operations succeeded
        for success, result in results:
            assert success is True
            assert isinstance(result, str)  # File path
        
        # Verify all files were created
        ai_generated_path = Path(cortex_path) / "02-Neural-Links" / "AI-Generated"
        concurrent_files = list(ai_generated_path.glob("Concurrent Test Insight*.md"))
        assert len(concurrent_files) == 5

class TestSystemIntegrationScenarios:
    """Test realistic usage scenarios end-to-end"""
    
    @pytest.mark.asyncio
    async def test_developer_workflow_scenario(self, temp_cortex_environment):
        """Test a realistic developer workflow scenario"""
        cortex_path, _, _ = temp_cortex_environment
        
        # Scenario: Developer works on a project, has discussions, makes decisions
        
        # 1. Chat session about implementation
        from chat_obsidian_sync import ChatMessage, ChatObsidianSyncer
        from obsidian_mcp_bridge import ObsidianMCPBridge
        
        chat_messages = [
            ChatMessage(
                role='user',
                content='I need to refactor the authentication system. Should we use OAuth 2.0 or implement custom tokens?'
            ),
            ChatMessage(
                role='assistant', 
                content='For authentication refactoring, I recommend OAuth 2.0. Here\'s why:\n\n1. Industry standard\n2. Better security\n3. Third-party integration support\n\nDecision: Implement OAuth 2.0 with PKCE flow.\n\n```python\nclass OAuthHandler:\n    def __init__(self):\n        self.client_id = settings.OAUTH_CLIENT_ID\n        \n    def authenticate(self, code):\n        # OAuth implementation\n        return self.exchange_code_for_token(code)\n```'
            ),
            ChatMessage(
                role='user',
                content='Perfect! I\'ll implement OAuth 2.0. Need to update the API documentation and create migration scripts.'
            )
        ]
        
        # Mock bridge setup
        with patch('chat_obsidian_sync.ObsidianMCPBridge') as mock_bridge_class:
            bridge = ObsidianMCPBridge(cortex_path=cortex_path)
            bridge.supported_vaults["cortex"] = cortex_path
            mock_bridge_class.return_value = bridge
            
            syncer = ChatObsidianSyncer()
            
            # 2. Sync chat session
            chat_result = await syncer.sync_chat_session(
                chat_messages, 
                {'topic': 'Authentication System Refactoring', 'session_id': 'auth_refactor_001'}
            )
            
            assert chat_result is True
            
            # 3. Verify comprehensive note creation
            chat_path = Path(cortex_path) / "02-Neural-Links" / "Chat-Sessions"
            chat_files = list(chat_path.glob("*.md"))
            assert len(chat_files) >= 1
            
            # Verify rich content extraction
            with open(chat_files[0], 'r') as f:
                content = f.read()
            
            # Should contain decisions
            assert "Decision" in content
            assert "OAuth 2.0" in content
            
            # Should contain code snippets
            assert "OAuthHandler" in content
            assert "python" in content.lower()
            
            # Should contain action items
            assert "Action Items" in content
            assert "API documentation" in content or "migration scripts" in content
    
    @pytest.mark.asyncio
    async def test_knowledge_discovery_scenario(self, temp_cortex_environment):
        """Test knowledge discovery and cross-referencing scenario"""
        cortex_path, ai_data, link_data = temp_cortex_environment
        
        from obsidian_mcp_bridge import integrate_with_obsidian
        
        # Scenario: AI discovers patterns across project documentation
        
        # Enhanced AI insights with cross-references
        discovery_insights = [
            {
                'topic': 'API Design Pattern Discovery',
                'summary': 'Discovered consistent API design patterns across multiple projects',
                'findings': [
                    'All authentication endpoints follow RESTful conventions',
                    'Error handling uses consistent HTTP status codes',
                    'Request/response models are well-documented'
                ],
                'related_concepts': ['API Design', 'REST', 'Authentication', 'Error Handling'],
                'cross_vault_connections': [
                    {'vault': '01-Projects', 'file': 'api-standards.md', 'score': 0.95},
                    {'vault': '04-Code-Fragments', 'file': 'rest-patterns.md', 'score': 0.88}
                ],
                'tags': ['api-design', 'patterns', 'cross-project', 'discovery'],
                'source_vaults': ['01-Projects', '04-Code-Fragments'],
                'correlation_count': 12,
                'confidence': 0.94,
                'pattern_types': ['consistency-pattern', 'cross-vault-correlation']
            },
            {
                'topic': 'Decision Impact Analysis',
                'summary': 'Analysis of how architectural decisions impact multiple project areas',
                'findings': [
                    'Database choice affects performance metrics across 5 projects',
                    'Authentication strategy influences security posture',
                    'Testing frameworks correlate with deployment success rates'
                ],
                'related_concepts': ['Architecture', 'Decision Impact', 'Performance', 'Security'],
                'cross_vault_connections': [
                    {'vault': '03-Decisions', 'file': 'database-selection.md', 'score': 0.91},
                    {'vault': '05-Insights', 'file': 'performance-analysis.md', 'score': 0.87}
                ],
                'tags': ['decision-analysis', 'impact-assessment', 'architecture'],
                'source_vaults': ['03-Decisions', '05-Insights'],
                'correlation_count': 8,
                'confidence': 0.89,
                'pattern_types': ['impact-analysis', 'decision-correlation']
            }
        ]
        
        # Rich cross-vault links
        discovery_links = [
            {
                'source_file': '01-Projects/api-gateway-project.md',
                'target_file': '04-Code-Fragments/authentication-patterns.md',
                'target_vault': 'cortex',
                'confidence': 0.93,
                'shared_tags': ['authentication', 'api', 'security'],
                'reason': 'Strong semantic similarity in authentication implementation patterns',
                'link_type': 'strong'
            },
            {
                'source_file': '03-Decisions/ADR-003-Database-Choice.md',
                'target_file': '05-Insights/performance-correlation.md',
                'target_vault': 'cortex',
                'confidence': 0.87,
                'shared_tags': ['database', 'performance', 'analysis'],
                'reason': 'Decision directly impacts performance insights',
                'link_type': 'strong'
            }
        ]
        
        # Execute discovery integration
        result = await integrate_with_obsidian(
            ai_insights=discovery_insights,
            cross_vault_links=discovery_links,
            target_vault="cortex"
        )
        
        assert result.success is True
        assert result.notes_created >= 3  # 2 insights + 1 summary
        
        # Verify rich insight notes
        insights_path = Path(cortex_path) / "02-Neural-Links" / "AI-Generated"
        insight_files = list(insights_path.glob("*.md"))
        
        # Find and verify the API design pattern note
        api_insight_file = None
        for file in insight_files:
            if "API Design Pattern" in file.name:
                api_insight_file = file
                break
        
        assert api_insight_file is not None
        
        with open(api_insight_file, 'r') as f:
            api_content = f.read()
        
        # Verify rich content
        assert "API Design Pattern Discovery" in api_content
        assert "Cross-Vault Connections" in api_content
        assert "api-standards.md" in api_content
        assert "confidence: 0.95" in api_content
        assert "#api-design" in api_content
        assert "Pattern Types" in api_content

if __name__ == "__main__":
    # Run integration tests
    pytest.main([
        __file__,
        "-v",
        "-x",  # Stop on first failure
        "--tb=short",
        "--asyncio-mode=auto"
    ])