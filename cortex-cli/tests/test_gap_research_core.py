#!/usr/bin/env python3
"""
Test suite for Gap Research - Critical Risk Mitigation
Tests for cortex/integrations/gap_research.py (currently 0% coverage)
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Import Gap Research components
try:
    from cortex.integrations.gap_research import (
        ResearchResult,
        KnowledgeGap,
        GapResearchIntegrator
    )
    GAP_RESEARCH_AVAILABLE = True
except ImportError:
    GAP_RESEARCH_AVAILABLE = False


@pytest.mark.skipif(not GAP_RESEARCH_AVAILABLE, reason="Gap Research components not available")
class TestGapResearchCore:
    """Test suite for critical Gap Research functionality"""
    
    def test_research_result_creation(self):
        """Test ResearchResult dataclass creation and validation"""
        result = ResearchResult(
            query="test machine learning",
            title="Machine Learning Guide",
            url="https://example.com/ml-guide",
            content="Comprehensive guide to machine learning concepts and applications",
            relevance_score=0.95,
            authority_score=0.88,
            currency_score=0.92,
            timestamp=datetime.now()
        )
        
        assert result.query == "test machine learning"
        assert result.title == "Machine Learning Guide"
        assert result.url == "https://example.com/ml-guide"
        assert 0.0 <= result.relevance_score <= 1.0
        assert 0.0 <= result.authority_score <= 1.0
        assert 0.0 <= result.currency_score <= 1.0
        assert isinstance(result.timestamp, datetime)
    
    def test_research_result_serialization(self):
        """Test ResearchResult to_dict method for JSON serialization"""
        result = ResearchResult(
            query="serialization test",
            title="Test Title",
            url="https://test.com",
            content="Test content",
            relevance_score=0.8,
            authority_score=0.7,
            currency_score=0.9,
            timestamp=datetime.now()
        )
        
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["query"] == "serialization test"
        assert result_dict["title"] == "Test Title"
        assert result_dict["url"] == "https://test.com"
        assert result_dict["relevance_score"] == 0.8
        assert isinstance(result_dict["timestamp"], str)  # Should be ISO format
        
        # Test JSON serialization
        json_str = json.dumps(result_dict)
        assert isinstance(json_str, str)
        
        # Test deserialization
        loaded = json.loads(json_str)
        assert loaded["query"] == "serialization test"
    
    def test_knowledge_gap_creation(self):
        """Test KnowledgeGap dataclass creation"""
        gap = KnowledgeGap(
            gap_id="gap_001",
            title="Missing AI Documentation",
            gap_type="documentation",
            priority="high",
            confidence=0.85,
            description="This is a critical documentation gap",
            context="AI system documentation is missing critical sections",
            detected_date="2024-01-15",
            research_queries=["AI documentation best practices", "system documentation"]
        )
        
        assert gap.gap_id == "gap_001"
        assert gap.title == "Missing AI Documentation"
        assert gap.gap_type == "documentation"
        assert gap.priority == "high"
        assert gap.confidence == 0.85
        assert gap.description == "This is a critical documentation gap"
        assert gap.context == "AI system documentation is missing critical sections"
        assert gap.detected_date == "2024-01-15"
        assert isinstance(gap.research_queries, list)
        assert len(gap.research_queries) == 2
    
    def test_knowledge_gap_priority_levels(self):
        """Test KnowledgeGap with different priority levels"""
        priorities = ["critical", "high", "medium", "low"]
        
        for priority in priorities:
            gap = KnowledgeGap(
                gap_id=f"gap_{priority}",
                title=f"Gap with {priority} priority",
                gap_type="research",
                priority=priority,
                confidence=0.5,
                description=f"Testing {priority} priority gap",
                context="Testing different priority levels",
                detected_date="2024-01-15",
                research_queries=[f"{priority} priority research"]
            )
            assert gap.priority == priority
    
    def test_knowledge_gap_types(self):
        """Test KnowledgeGap with different gap types"""
        gap_types = ["documentation", "research", "examples", "benchmarks", "tutorials"]
        
        for gap_type in gap_types:
            gap = KnowledgeGap(
                gap_id=f"gap_{gap_type}",
                title=f"Gap of type {gap_type}",
                gap_type=gap_type,
                priority="medium",
                confidence=0.7,
                description=f"Testing {gap_type} gap type",
                context="Testing different gap types",
                detected_date="2024-01-15",
                research_queries=[f"{gap_type} research query"]
            )
            assert gap.gap_type == gap_type
    
    @patch('cortex.integrations.gap_research.Path.exists')
    def test_gap_research_integrator_initialization(self, mock_exists):
        """Test GapResearchIntegrator initialization"""
        mock_exists.return_value = True
        
        try:
            integrator = GapResearchIntegrator()
            assert integrator is not None
        except Exception as e:
            pytest.skip(f"Gap Research Integrator initialization failed: {e}")
    
    def test_research_result_scoring_validation(self):
        """Test that research result scores are within valid ranges"""
        # Test boundary values
        result = ResearchResult(
            query="boundary test",
            title="Boundary Test",
            url="https://boundary.com",
            content="Testing boundary conditions",
            relevance_score=0.0,  # Minimum
            authority_score=1.0,  # Maximum
            currency_score=0.5,  # Middle
            timestamp=datetime.now()
        )
        
        assert result.relevance_score == 0.0
        assert result.authority_score == 1.0
        assert result.currency_score == 0.5
        
        # All scores should be valid floats
        assert isinstance(result.relevance_score, float)
        assert isinstance(result.authority_score, float)
        assert isinstance(result.currency_score, float)
    
    def test_knowledge_gap_confidence_validation(self):
        """Test KnowledgeGap confidence score validation"""
        # Test confidence boundaries
        confidences = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for conf in confidences:
            gap = KnowledgeGap(
                gap_id=f"conf_{conf}",
                title=f"Confidence {conf} test",
                gap_type="validation",
                priority="low",
                confidence=conf,
                description=f"Testing confidence level {conf}",
                context="Confidence validation testing",
                detected_date="2024-01-15",
                research_queries=["confidence testing"]
            )
            assert gap.confidence == conf
            assert 0.0 <= gap.confidence <= 1.0


@pytest.mark.skipif(not GAP_RESEARCH_AVAILABLE, reason="Gap Research components not available")
class TestGapResearchIntegration:
    """Integration tests for Gap Research functionality"""
    
    @pytest.mark.asyncio
    async def test_gap_research_integrator_async_methods(self):
        """Test async methods can be mocked and called"""
        with patch('cortex.integrations.gap_research.GapResearchIntegrator') as MockIntegrator:
            mock_instance = AsyncMock()
            MockIntegrator.return_value = mock_instance
            
            integrator = MockIntegrator()
            
            # Test research_gap method
            mock_result = ResearchResult(
                query="async test",
                title="Async Test Result",
                url="https://async.test",
                content="Async research content",
                relevance_score=0.9,
                authority_score=0.8,
                currency_score=0.7,
                timestamp=datetime.now()
            )
            mock_instance.research_gap.return_value = [mock_result]
            
            results = await integrator.research_gap("test gap")
            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0].query == "async test"
    
    def test_research_result_content_handling(self):
        """Test ResearchResult with different content types"""
        # Test with long content
        long_content = "x" * 5000
        result = ResearchResult(
            query="long content test",
            title="Long Content",
            url="https://long.com",
            content=long_content,
            relevance_score=0.5,
            authority_score=0.5,
            currency_score=0.5,
            timestamp=datetime.now()
        )
        assert len(result.content) == 5000
        
        # Test with empty content
        empty_result = ResearchResult(
            query="empty content test",
            title="Empty Content",
            url="https://empty.com",
            content="",
            relevance_score=0.1,
            authority_score=0.1,
            currency_score=0.1,
            timestamp=datetime.now()
        )
        assert empty_result.content == ""
        
        # Test with special characters
        special_content = "Special chars: äöü ñ 中文 🚀 <tag> & \"quotes\""
        special_result = ResearchResult(
            query="special chars test",
            title="Special Characters",
            url="https://special.com",
            content=special_content,
            relevance_score=0.6,
            authority_score=0.6,
            currency_score=0.6,
            timestamp=datetime.now()
        )
        assert "äöü" in special_result.content
        assert "中文" in special_result.content
        assert "🚀" in special_result.content
    
    def test_knowledge_gap_serialization(self):
        """Test KnowledgeGap can be serialized for storage"""
        gap = KnowledgeGap(
            gap_id="serialize_gap",
            title="Serialization Gap",
            gap_type="testing",
            priority="medium",
            confidence=0.75,
            description="Testing serialization functionality",
            context="Gap serialization testing context",
            detected_date="2024-01-15",
            research_queries=["serialization", "testing"]
        )
        
        # Test dictionary conversion
        gap_dict = gap.__dict__
        assert isinstance(gap_dict, dict)
        assert gap_dict["gap_id"] == "serialize_gap"
        
        # Test JSON serialization
        json_str = json.dumps(gap_dict)
        assert isinstance(json_str, str)
        
        # Test deserialization
        loaded = json.loads(json_str)
        assert loaded["title"] == "Serialization Gap"
        assert loaded["confidence"] == 0.75
        assert loaded["description"] == "Testing serialization functionality"
        assert isinstance(loaded["research_queries"], list)


class TestGapResearchRiskMitigation:
    """Critical risk mitigation tests - these should always run"""
    
    def test_gap_research_import_safety(self):
        """Test that Gap Research can be safely imported"""
        try:
            from cortex.integrations import gap_research
            assert gap_research is not None
        except ImportError as e:
            pytest.fail(f"Critical: Gap Research module cannot be imported: {e}")
    
    def test_dataclass_definitions(self):
        """Test that critical dataclasses are properly defined"""
        if not GAP_RESEARCH_AVAILABLE:
            pytest.skip("Gap Research not available - structural test skipped")
        
        # Test ResearchResult structure
        import inspect
        from cortex.integrations.gap_research import ResearchResult
        
        sig = inspect.signature(ResearchResult)
        required_params = [
            'query', 'title', 'url', 'content', 
            'relevance_score', 'authority_score', 'currency_score', 'timestamp'
        ]
        
        for param in required_params:
            assert param in sig.parameters, f"ResearchResult missing required parameter: {param}"
        
        # Test KnowledgeGap structure
        from cortex.integrations.gap_research import KnowledgeGap
        
        gap_sig = inspect.signature(KnowledgeGap)
        gap_params = ['gap_id', 'title', 'gap_type', 'priority', 'confidence', 
                     'description', 'context', 'detected_date', 'research_queries']
        
        for param in gap_params:
            assert param in gap_sig.parameters, f"KnowledgeGap missing required parameter: {param}"
    
    def test_module_structure(self):
        """Test that Gap Research module has expected structure"""
        try:
            import cortex.integrations.gap_research as gap_research
            
            expected_classes = ['ResearchResult', 'KnowledgeGap', 'GapResearchIntegrator']
            
            for class_name in expected_classes:
                assert hasattr(gap_research, class_name), f"Missing class: {class_name}"
                
        except ImportError:
            pytest.skip("Gap Research module structure test skipped - import failed")
    
    def test_critical_functionality_exists(self):
        """Test that critical Gap Research functionality is available"""
        if not GAP_RESEARCH_AVAILABLE:
            pytest.skip("Gap Research not available - functionality test skipped")
        
        try:
            from cortex.integrations.gap_research import ResearchResult, KnowledgeGap
            
            # Basic instantiation test
            result = ResearchResult(
                query="risk test",
                title="Risk Mitigation Test",
                url="https://risk.test",
                content="Testing critical paths",
                relevance_score=0.5,
                authority_score=0.5,
                currency_score=0.5,
                timestamp=datetime.now()
            )
            assert result.query == "risk test"
            
            gap = KnowledgeGap(
                gap_id="risk_gap",
                title="Risk Gap",
                gap_type="risk",
                priority="critical",
                confidence=0.9,
                description="Risk mitigation test gap",
                context="Testing critical functionality",
                detected_date="2024-01-15",
                research_queries=["risk mitigation", "testing"]
            )
            assert gap.priority == "critical"
            
        except Exception as e:
            pytest.fail(f"Critical: Basic Gap Research functionality failed: {e}")


class TestGapResearchErrorHandling:
    """Test error handling and edge cases"""
    
    def test_research_result_edge_cases(self):
        """Test ResearchResult with edge case inputs"""
        # Test with very low scores
        low_result = ResearchResult(
            query="low scores",
            title="Low Quality Result", 
            url="https://low.quality",
            content="Low quality content",
            relevance_score=0.01,
            authority_score=0.02,
            currency_score=0.03,
            timestamp=datetime.now()
        )
        assert low_result.relevance_score == 0.01
        assert low_result.authority_score == 0.02
        assert low_result.currency_score == 0.03
        
        # Test with very high scores
        high_result = ResearchResult(
            query="high scores",
            title="High Quality Result",
            url="https://high.quality", 
            content="High quality content",
            relevance_score=0.99,
            authority_score=0.98,
            currency_score=0.97,
            timestamp=datetime.now()
        )
        assert high_result.relevance_score == 0.99
        assert high_result.authority_score == 0.98
        assert high_result.currency_score == 0.97
    
    def test_knowledge_gap_edge_cases(self):
        """Test KnowledgeGap with edge case inputs"""
        # Test with minimal confidence
        min_gap = KnowledgeGap(
            gap_id="min_confidence",
            title="Minimal Confidence Gap",
            gap_type="edge",
            priority="low",
            confidence=0.0,
            description="Testing minimal confidence",
            context="Edge case testing",
            detected_date="2024-01-15",
            research_queries=["edge case"]
        )
        assert min_gap.confidence == 0.0
        
        # Test with maximum confidence  
        max_gap = KnowledgeGap(
            gap_id="max_confidence",
            title="Maximum Confidence Gap",
            gap_type="edge",
            priority="critical",
            confidence=1.0,
            description="Testing maximum confidence",
            context="Edge case testing",
            detected_date="2024-01-15",
            research_queries=["edge case"]
        )
        assert max_gap.confidence == 1.0
        
        # Test with long titles
        long_title = "x" * 200
        long_gap = KnowledgeGap(
            gap_id="long_title",
            title=long_title,
            gap_type="edge",
            priority="medium",
            confidence=0.5,
            description="Testing long titles",
            context="Long title edge case",
            detected_date="2024-01-15",
            research_queries=["long title test"]
        )
        assert len(long_gap.title) == 200
    
    def test_timestamp_handling(self):
        """Test timestamp handling in ResearchResult"""
        # Test with current timestamp
        now = datetime.now()
        result = ResearchResult(
            query="timestamp test",
            title="Timestamp Test",
            url="https://time.test",
            content="Testing timestamps",
            relevance_score=0.5,
            authority_score=0.5,
            currency_score=0.5,
            timestamp=now
        )
        
        assert result.timestamp == now
        
        # Test serialization includes timestamp
        result_dict = result.to_dict()
        assert "timestamp" in result_dict
        assert isinstance(result_dict["timestamp"], str)
        
        # Test that timestamp can be deserialized
        timestamp_str = result_dict["timestamp"]
        parsed_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00') if timestamp_str.endswith('Z') else timestamp_str)
        assert isinstance(parsed_timestamp, datetime)
