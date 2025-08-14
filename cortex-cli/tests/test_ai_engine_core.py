#!/usr/bin/env python3
"""
Test suite for AI Engine Core - Critical Risk Mitigation
Tests for cortex/core/ai_engine.py (currently 0% coverage)
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the critical AI Engine components
from cortex.core.ai_engine import (
    KnowledgeGap,
    ResearchResult,
    CortexAIEngine as AIEngine
)

# No longer skip tests, we will mock the DB connection
class TestAIEngineCore:
    """Test suite for critical AI Engine functionality"""
    
    def test_knowledge_gap_creation(self):
        """Test KnowledgeGap dataclass creation and validation"""
        gap = KnowledgeGap(
            gap_id="test_gap_001",
            gap_type="missing_benchmarks",
            title="Test Gap",
            description="Test description",
            context="test_context",
            priority="critical",
            confidence=0.85,
            research_queries=["query1", "query2"],
            detected_date=datetime.now().isoformat()
        )
        
        assert gap.gap_id == "test_gap_001"
        assert gap.gap_type == "missing_benchmarks"
        assert gap.priority == "critical"
        assert gap.confidence == 0.85
        assert len(gap.research_queries) == 2
        assert gap.filled_date is None  # Initially not filled
    
    def test_research_result_creation(self):
        """Test ResearchResult dataclass creation"""
        result = ResearchResult(
            query="test query",
            source_url="https://example.com",
            title="Test Result",
            content="Test content",
            relevance_score=0.9,
            authority_score=0.8,
            currency_score=0.7,
            extracted_data={"key": "value"},
            timestamp=datetime.now().isoformat()
        )
        
        assert result.query == "test query"
        assert result.relevance_score == 0.9
        assert result.authority_score == 0.8
        assert result.currency_score == 0.7
        assert result.extracted_data["key"] == "value"
    
    @patch('cortex.core.local_ai.Neo4jConnector')
    def test_ai_engine_initialization(self, MockNeo4jConnector):
        """Test AI Engine initialization - critical path"""
        # Mock the connector to prevent actual DB connection
        mock_instance = MockNeo4jConnector.return_value
        mock_instance.verify_connectivity.return_value = None # Simulate successful connection

        try:
            # Try to initialize AI Engine
            engine = AIEngine()
            assert engine is not None
            assert engine.local_ai is not None
            # Check that the mocked connector was used
            MockNeo4jConnector.assert_called_once()
        except Exception as e:
            pytest.fail(f"AI Engine initialization failed with mocked DB: {e}")

    def test_knowledge_gap_serialization(self):
        """Test that KnowledgeGap can be serialized/deserialized"""
        gap = KnowledgeGap(
            gap_id="serialize_test",
            gap_type="incomplete_research", 
            title="Serialization Test",
            description="Testing serialization",
            context="unit_test",
            priority="medium",
            confidence=0.75,
            research_queries=["serialize", "deserialize"],
            detected_date=datetime.now().isoformat()
        )
        
        # Test serialization
        gap_dict = gap.__dict__
        assert isinstance(gap_dict, dict)
        assert gap_dict["gap_id"] == "serialize_test"
        
        # Test that it can be JSON serialized
        json_str = json.dumps(gap_dict)
        assert isinstance(json_str, str)
        
        # Test deserialization
        loaded_dict = json.loads(json_str)
        assert loaded_dict["gap_id"] == "serialize_test"
    
    def test_research_result_scoring(self):
        """Test research result scoring validation"""
        # Test valid scores
        result = ResearchResult(
            query="scoring test",
            source_url="https://test.com",
            title="Scoring Test",
            content="Content",
            relevance_score=1.0,
            authority_score=0.0,
            currency_score=0.5,
            extracted_data={},
            timestamp=datetime.now().isoformat()
        )
        
        # All scores should be between 0.0 and 1.0
        assert 0.0 <= result.relevance_score <= 1.0
        assert 0.0 <= result.authority_score <= 1.0
        assert 0.0 <= result.currency_score <= 1.0
    
    def test_knowledge_gap_priority_validation(self):
        """Test that priority levels are valid"""
        valid_priorities = ["critical", "high", "medium", "low"]
        
        for priority in valid_priorities:
            gap = KnowledgeGap(
                gap_id=f"priority_test_{priority}",
                gap_type="missing_examples",
                title=f"Priority {priority}",
                description="Test",
                context="validation",
                priority=priority,
                confidence=0.5,
                research_queries=["test"],
                detected_date=datetime.now().isoformat()
            )
            assert gap.priority == priority
    
    @pytest.mark.asyncio
    @patch('cortex.core.ai_engine.CortexAIEngine.save_detected_gaps')
    async def test_research_gap_async_method(self, mock_save_gaps):
        """Test the research_gap async method with a mocked local_ai."""
        with patch('cortex.core.local_ai.Neo4jConnector'):
            engine = AIEngine()

            # Create a sample gap and add it to the engine
            gap = KnowledgeGap(
                gap_id="test_gap_001",
                gap_type="incomplete_research",
                title="Test Gap for 'Node1'",
                description="A test gap.",
                context="Some context about 'Node1'",
                priority="high",
                confidence=0.9,
                research_queries=[],
                detected_date=datetime.now().isoformat()
            )
            engine.detected_gaps.append(gap)

            # Mock the method that the engine's logic depends on
            with patch.object(engine.local_ai, 'suggest_links_for_node') as mock_suggest:
                mock_suggest.return_value = [{'potential_link': 'Node2', 'common_neighbors_score': 5}]

                # Call the method under test
                result_gap = await engine.research_gap("test_gap_001")

                # Assertions
                mock_suggest.assert_called_once_with('Node1')
                assert result_gap is not None
                assert result_gap.gap_id == "test_gap_001"

                # Check that a research result was added
                assert "test_gap_001" in engine.research_results
                research_result = engine.research_results["test_gap_001"][0]
                assert research_result.source_url == "local_ai_graph_analysis"
                assert "Node2" in research_result.content
                mock_save_gaps.assert_called_once()


# No longer skip tests
class TestAIEngineIntegration:
    """Integration tests for AI Engine with a mocked file system and DB"""

    @patch('cortex.core.local_ai.Neo4jConnector')
    def test_ai_engine_data_structures(self, MockNeo4jConnector):
        """Test that all required data structures are available"""
        # Test that classes can be imported and instantiated
        assert KnowledgeGap is not None
        assert ResearchResult is not None
        
        # Test basic instantiation doesn't crash
        try:
            gap = KnowledgeGap(
                gap_id="integration_test",
                gap_type="missing_benchmarks",
                title="Integration Test",
                description="Testing integration",
                context="integration",
                priority="low",
                confidence=0.1,
                research_queries=[],
                detected_date=datetime.now().isoformat()
            )
            assert gap.gap_id == "integration_test"
        except Exception as e:
            pytest.fail(f"Basic KnowledgeGap instantiation failed: {e}")
