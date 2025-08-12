#!/usr/bin/env python3
"""
Test suite for Obsidian MCP Integration
Tests the bridge between Cortex AI system and Obsidian via MCP server
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, List

# Add the Cross-Vault-Linker path to import our modules
import sys
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/Cross-Vault-Linker')

from obsidian_mcp_bridge import ObsidianMCPBridge, ObsidianNote, MCPCommand, SyncResult, integrate_with_obsidian
from chat_obsidian_sync import ChatContentExtractor, ChatObsidianSyncer, ChatMessage, ExtractedInsight, ChatAnalysisResult

class TestObsidianMCPBridge:
    """Test the Obsidian MCP Bridge functionality"""
    
    @pytest.fixture
    def temp_vault_path(self):
        """Create a temporary vault directory for testing"""
        temp_dir = tempfile.mkdtemp()
        vault_path = Path(temp_dir) / "test_vault"
        vault_path.mkdir(parents=True)
        
        # Create some basic structure
        (vault_path / "02-Neural-Links").mkdir(parents=True)
        (vault_path / "02-Neural-Links" / "AI-Generated").mkdir(parents=True)
        (vault_path / "02-Neural-Links" / "Summaries").mkdir(parents=True)
        (vault_path / "02-Neural-Links" / "Chat-Sessions").mkdir(parents=True)
        
        yield str(vault_path)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_bridge(self, temp_vault_path):
        """Create a mock bridge with test vault"""
        bridge = ObsidianMCPBridge()
        bridge.supported_vaults = {"test_vault": temp_vault_path}
        bridge.cortex_path = temp_vault_path
        return bridge
    
    @pytest.fixture
    def sample_insight_data(self):
        """Sample insight data for testing"""
        return {
            'topic': 'Test Insight',
            'summary': 'This is a test insight for unit testing',
            'findings': ['Finding 1', 'Finding 2'],
            'related_concepts': ['Concept A', 'Concept B'],
            'cross_vault_connections': [
                {'vault': 'test_vault', 'file': 'test.md', 'score': 0.85}
            ],
            'tags': ['test', 'unit-test', 'ai-insight'],
            'source_vaults': ['test_vault'],
            'correlation_count': 5,
            'confidence': 0.92,
            'pattern_types': ['test-pattern']
        }
    
    @pytest.fixture
    def sample_link_suggestions(self):
        """Sample link suggestions for testing"""
        return [
            {
                'source_file': 'source1.md',
                'target_file': 'target1.md',
                'target_vault': 'test_vault',
                'confidence': 0.85,
                'shared_tags': ['tag1', 'tag2'],
                'reason': 'Strong correlation detected',
                'link_type': 'strong'
            },
            {
                'source_file': 'source2.md',
                'target_file': 'target2.md',
                'target_vault': 'test_vault',
                'confidence': 0.65,
                'shared_tags': ['tag3'],
                'reason': 'Medium correlation detected',
                'link_type': 'medium'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_create_cortex_insight_note(self, mock_bridge, sample_insight_data, temp_vault_path):
        """Test creation of Cortex insight notes"""
        success, result = await mock_bridge.create_cortex_insight_note(sample_insight_data, "test_vault")
        
        assert success is True
        assert "AI-Generated" in result
        
        # Check if file was actually created
        file_path = Path(result)
        assert file_path.exists()
        
        # Check file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        assert "Test Insight" in content
        assert "This is a test insight" in content
        assert "Finding 1" in content
        assert "#test" in content
        assert "confidence: 0.92" in content
        assert "Generated with" in content or "Cortex AI Learning Engine" in content
    
    @pytest.mark.asyncio
    async def test_sync_cross_vault_links(self, mock_bridge, sample_link_suggestions, temp_vault_path):
        """Test syncing of cross-vault links"""
        result = await mock_bridge.sync_cross_vault_links(sample_link_suggestions, "test_vault")
        
        assert isinstance(result, SyncResult)
        assert result.notes_created >= 1  # At least summary note
        assert len(result.errors) == 0 or all('not found' in error.lower() for error in result.errors)
        assert result.execution_time > 0
        
        # Check if summary note was created
        summaries_path = Path(temp_vault_path) / "02-Neural-Links" / "Summaries"
        summary_files = list(summaries_path.glob("Cross-Vault Link Summary*.md"))
        assert len(summary_files) >= 1
        
        # Check summary content
        with open(summary_files[0], 'r') as f:
            content = f.read()
        
        assert "Cross-Vault Link Summary" in content
        assert "Strong Connections" in content
        assert "source1.md" in content
        assert "0.85" in content
    
    @pytest.mark.asyncio
    async def test_sync_chat_session(self, mock_bridge, temp_vault_path):
        """Test syncing of chat sessions"""
        chat_data = {
            'topic': 'Test Chat Session',
            'summary': 'A test conversation',
            'messages': [
                {'role': 'user', 'content': 'Hello, how are you?'},
                {'role': 'assistant', 'content': 'I am doing well, thank you!'}
            ],
            'extracted_insights': [],
            'decisions': [{'topic': 'Test Decision', 'description': 'Decided to test'}],
            'action_items': [{'description': 'Write tests', 'priority': 'high'}],
            'related_notes': ['Related Note'],
            'tags': ['chat', 'test'],
            'duration': '5 minutes',
            'word_count': 100,
            'session_id': 'test123',
            'model': 'Claude Test'
        }
        
        success, result = await mock_bridge.sync_chat_session(chat_data, "test_vault")
        
        assert success is True
        assert "Chat-Sessions" in result
        
        # Check if file was created
        file_path = Path(result)
        assert file_path.exists()
        
        # Check content
        with open(file_path, 'r') as f:
            content = f.read()
        
        assert "Test Chat Session" in content
        assert "Test Decision" in content
        assert "Write tests" in content
        assert "Related Note" in content
    
    def test_sanitize_filename(self, mock_bridge):
        """Test filename sanitization"""
        dangerous_filename = 'Test<>File:Name|With?Bad*Characters'
        sanitized = mock_bridge._sanitize_filename(dangerous_filename)
        
        assert '<' not in sanitized
        assert '>' not in sanitized
        assert ':' not in sanitized
        assert '|' not in sanitized
        assert '?' not in sanitized
        assert '*' not in sanitized
        assert len(sanitized) <= 200
    
    def test_generate_content_hash(self, mock_bridge):
        """Test content hash generation"""
        content1 = "This is test content"
        content2 = "This is test content"
        content3 = "This is different content"
        
        hash1 = mock_bridge._generate_content_hash(content1)
        hash2 = mock_bridge._generate_content_hash(content2)
        hash3 = mock_bridge._generate_content_hash(content3)
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 32  # MD5 hash length
    
    def test_discover_obsidian_vaults(self, temp_vault_path):
        """Test vault discovery functionality"""
        # Create a mock MCP config
        config_path = Path(temp_vault_path) / "test_config.json"
        config_data = {
            "mcpServers": {
                "obsidian-test": {
                    "args": {
                        "vault_path": temp_vault_path
                    }
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        bridge = ObsidianMCPBridge(mcp_config_path=str(config_path), cortex_path=temp_vault_path)
        
        assert "cortex" in bridge.supported_vaults
        assert len(bridge.supported_vaults) >= 1
    
    def test_sync_statistics(self, mock_bridge):
        """Test sync statistics functionality"""
        # Add some mock sync metadata
        mock_bridge.sync_metadata = {
            'synced_notes': {
                'note1.md': {'type': 'insight', 'created': '2025-01-01'},
                'note2.md': {'type': 'chat_session', 'created': '2025-01-01'},
                'note3.md': {'type': 'link_summary', 'created': '2025-01-01'}
            },
            'last_sync': '2025-01-01T12:00:00',
            'vault_stats': {'test_vault': {'links_processed': 10}}
        }
        
        stats = mock_bridge.get_sync_statistics()
        
        assert stats['total_notes_synced'] == 3
        assert stats['last_sync'] == '2025-01-01T12:00:00'
        assert 'notes_by_type' in stats
        assert stats['notes_by_type']['insight'] == 1
        assert stats['notes_by_type']['chat_session'] == 1
        assert stats['notes_by_type']['link_summary'] == 1

class TestChatContentExtractor:
    """Test the chat content extraction functionality"""
    
    @pytest.fixture
    def extractor(self):
        """Create a ChatContentExtractor instance"""
        return ChatContentExtractor()
    
    @pytest.fixture
    def sample_messages(self):
        """Sample chat messages for testing"""
        return [
            ChatMessage(
                role='user',
                content='I need to implement a new feature for user authentication. What approach should we take?',
                timestamp='2025-01-10T10:00:00'
            ),
            ChatMessage(
                role='assistant',
                content='For user authentication, I recommend using OAuth 2.0 with JWT tokens. This approach is secure and widely supported. We should implement it using the following steps:\n\n```python\ndef authenticate_user(username, password):\n    # Validate credentials\n    if validate_credentials(username, password):\n        return generate_jwt_token(username)\n    return None\n```\n\nThis is important to note that we need to hash passwords properly.',
                timestamp='2025-01-10T10:01:00'
            ),
            ChatMessage(
                role='user',
                content='That sounds good. I decided to go with OAuth 2.0. We need to implement this by next week.',
                timestamp='2025-01-10T10:02:00'
            )
        ]
    
    def test_extract_decisions(self, extractor, sample_messages):
        """Test decision extraction from messages"""
        decisions = extractor._extract_decisions(sample_messages)
        
        assert len(decisions) >= 1
        decision = decisions[0]
        assert 'OAuth 2.0' in decision['topic'] or 'OAuth 2.0' in decision['description']
        assert decision['confidence'] > 0
    
    def test_extract_action_items(self, extractor, sample_messages):
        """Test action item extraction"""
        action_items = extractor._extract_action_items(sample_messages)
        
        assert len(action_items) >= 1
        action = action_items[0]
        assert 'implement' in action['description'].lower()
        assert action['priority'] in ['low', 'medium', 'high']
        assert action['category'] in ['development', 'testing', 'research', 'documentation', 'general']
    
    def test_extract_code_snippets(self, extractor, sample_messages):
        """Test code snippet extraction"""
        code_snippets = extractor._extract_code_snippets(sample_messages)
        
        assert len(code_snippets) >= 1
        code = code_snippets[0]
        assert 'authenticate_user' in code['code']
        assert code['language'] == 'python'
        assert code['type'] == 'function'
    
    def test_extract_insights(self, extractor, sample_messages):
        """Test insight extraction"""
        insights = extractor._extract_insights(sample_messages)
        
        assert len(insights) >= 1
        insight = insights[0]
        assert insight.confidence > 0
        assert len(insight.content) > 0
        assert isinstance(insight.related_topics, list)
    
    def test_extract_obsidian_links(self, extractor):
        """Test Obsidian link extraction"""
        text = "This relates to [[Authentication]] and [[OAuth 2.0]] concepts."
        links = extractor._extract_obsidian_links(text)
        
        assert 'Authentication' in links
        assert 'OAuth 2.0' in links
        assert len(links) == 2
    
    def test_detect_language(self, extractor):
        """Test programming language detection"""
        python_code = "def hello():\n    print('Hello World')"
        js_code = "function hello() {\n    console.log('Hello World');\n}"
        sql_code = "SELECT * FROM users WHERE id = 1"
        
        assert extractor._detect_language(python_code) == 'python'
        assert extractor._detect_language(js_code) == 'javascript'
        assert extractor._detect_language(sql_code) == 'sql'
    
    def test_determine_topic(self, extractor, sample_messages):
        """Test topic determination"""
        topic = extractor._determine_topic(sample_messages, None)
        
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_generate_summary(self, extractor, sample_messages):
        """Test summary generation"""
        decisions = [{'topic': 'Auth', 'description': 'Use OAuth'}]
        action_items = [{'description': 'Implement auth'}]
        
        summary = extractor._generate_summary(sample_messages, decisions, action_items)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'decision' in summary.lower()
        assert 'action' in summary.lower()
    
    def test_extract_chat_content_full(self, extractor, sample_messages):
        """Test full chat content extraction"""
        result = extractor.extract_chat_content(sample_messages)
        
        assert isinstance(result, ChatAnalysisResult)
        assert result.word_count > 0
        assert len(result.tags) > 0
        assert isinstance(result.decisions, list)
        assert isinstance(result.action_items, list)
        assert isinstance(result.code_snippets, list)
        assert result.duration_estimate != "Unknown"

class TestChatObsidianSyncer:
    """Test the chat-to-Obsidian synchronization"""
    
    @pytest.fixture
    def syncer(self):
        """Create a ChatObsidianSyncer instance"""
        return ChatObsidianSyncer()
    
    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing"""
        return [
            ChatMessage(
                role='user',
                content='How do we test the MCP integration?',
                timestamp='2025-01-10T10:00:00'
            ),
            ChatMessage(
                role='assistant',
                content='We should create unit tests for the MCP bridge. This is important to ensure reliability.',
                timestamp='2025-01-10T10:01:00'
            )
        ]
    
    @pytest.mark.asyncio
    @patch('chat_obsidian_sync.ObsidianMCPBridge')
    async def test_sync_chat_session(self, mock_bridge_class, syncer, sample_messages):
        """Test chat session synchronization"""
        # Mock the bridge
        mock_bridge = Mock()
        mock_bridge.sync_chat_session = AsyncMock(return_value=(True, "test_path.md"))
        mock_bridge.create_cortex_insight_note = AsyncMock(return_value=(True, "insight.md"))
        mock_bridge_class.return_value = mock_bridge
        
        session_context = {'topic': 'Test Session', 'session_id': 'test123'}
        
        result = await syncer.sync_chat_session(sample_messages, session_context)
        
        assert result is True
        mock_bridge.sync_chat_session.assert_called_once()

class TestIntegrationFunctions:
    """Test the main integration functions"""
    
    @pytest.mark.asyncio
    @patch('obsidian_mcp_bridge.ObsidianMCPBridge')
    async def test_integrate_with_obsidian(self, mock_bridge_class):
        """Test the main integration function"""
        # Mock bridge
        mock_bridge = Mock()
        mock_bridge.create_cortex_insight_note = AsyncMock(return_value=(True, "insight.md"))
        mock_bridge.sync_cross_vault_links = AsyncMock(return_value=SyncResult(
            success=True,
            notes_created=2,
            links_added=3,
            errors=[],
            execution_time=1.5
        ))
        mock_bridge.sync_chat_session = AsyncMock(return_value=(True, "chat.md"))
        mock_bridge_class.return_value = mock_bridge
        
        ai_insights = [{'topic': 'Test Insight', 'summary': 'Test summary'}]
        cross_vault_links = [{'source_file': 'test.md', 'confidence': 0.8}]
        chat_data = {'topic': 'Test Chat', 'summary': 'Test chat'}
        
        result = await integrate_with_obsidian(ai_insights, cross_vault_links, chat_data)
        
        assert isinstance(result, SyncResult)
        assert result.success is True
        assert result.notes_created >= 3  # insight + links + chat
        assert result.links_added >= 3
        
        # Verify all methods were called
        mock_bridge.create_cortex_insight_note.assert_called()
        mock_bridge.sync_cross_vault_links.assert_called()
        mock_bridge.sync_chat_session.assert_called()

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_bridge_with_invalid_vault(self):
        """Test bridge behavior with invalid vault"""
        bridge = ObsidianMCPBridge()
        bridge.supported_vaults = {}  # No vaults
        
        insight_data = {'topic': 'Test', 'summary': 'Test summary'}
        success, result = await bridge.create_cortex_insight_note(insight_data, "invalid_vault")
        
        assert success is False
        assert "not found" in result.lower()
    
    @pytest.mark.asyncio
    async def test_sync_with_empty_data(self):
        """Test sync with empty data"""
        bridge = ObsidianMCPBridge()
        
        result = await bridge.sync_cross_vault_links([], "test_vault")
        
        assert isinstance(result, SyncResult)
        # Should handle empty data gracefully
    
    def test_extractor_with_empty_messages(self):
        """Test extractor with empty message list"""
        extractor = ChatContentExtractor()
        result = extractor.extract_chat_content([])
        
        assert isinstance(result, ChatAnalysisResult)
        assert result.word_count == 0
        assert result.topic == "Chat Session"

class TestPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_large_insight_creation_performance(self, tmp_path):
        """Test performance with large insight data"""
        bridge = ObsidianMCPBridge()
        bridge.supported_vaults = {"test": str(tmp_path)}
        
        # Create large insight data
        large_insight = {
            'topic': 'Large Test Insight',
            'summary': 'Large summary ' * 100,
            'findings': [f'Finding {i}' for i in range(50)],
            'related_concepts': [f'Concept {i}' for i in range(100)],
            'tags': [f'tag{i}' for i in range(20)],
            'confidence': 0.8
        }
        
        start_time = datetime.now()
        success, result = await bridge.create_cortex_insight_note(large_insight, "test")
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        assert success is True
        assert execution_time < 5.0  # Should complete within 5 seconds
        
        # Verify file was created and is reasonable size
        file_path = Path(result)
        assert file_path.exists()
        assert file_path.stat().st_size > 1000  # Should have substantial content
    
    def test_large_message_extraction_performance(self):
        """Test performance with large number of messages"""
        extractor = ChatContentExtractor()
        
        # Create many messages
        messages = []
        for i in range(100):
            messages.append(ChatMessage(
                role='user' if i % 2 == 0 else 'assistant',
                content=f'This is test message {i} with some content about testing and development.',
                timestamp=datetime.now().isoformat()
            ))
        
        start_time = datetime.now()
        result = extractor.extract_chat_content(messages)
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        assert isinstance(result, ChatAnalysisResult)
        assert execution_time < 10.0  # Should complete within 10 seconds
        assert result.word_count > 0

# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=obsidian_mcp_bridge",
        "--cov=chat_obsidian_sync",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])