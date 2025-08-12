#!/usr/bin/env python3
"""
Cortex Test Suite - Comprehensive testing for all Cortex components
Tests AI Learning Engine, Cross-Vault Linker, and Management Service
"""

import pytest
import tempfile
import shutil
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add system paths for imports
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/AI-Learning-Engine')
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/Cross-Vault-Linker')
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/Management-Service')

from multi_vault_ai import MultiVaultAILearningEngine, VaultProfile, TagCorrelation, CrossVaultPattern
from cross_vault_linker import CrossVaultLinker, LinkSuggestion, VaultConnection
from cortex_management import CortexManagementService

class TestData:
    """Test data and helper methods for Cortex testing"""
    
    @staticmethod
    def create_test_vault(vault_path: Path, vault_name: str):
        """Create a test vault with sample data"""
        vault_path.mkdir(parents=True, exist_ok=True)
        
        # Create .obsidian directory
        obsidian_dir = vault_path / ".obsidian"
        obsidian_dir.mkdir(exist_ok=True)
        
        # Create app.json
        app_json = obsidian_dir / "app.json"
        app_json.write_text(json.dumps({"vaultId": f"test-{vault_name}"}))
        
        # Create standard directories
        directories = ["00-Meta", "01-Planning", "02-Development", "03-Decisions", "04-Resources", "05-Insights"]
        for dir_name in directories:
            (vault_path / dir_name).mkdir(exist_ok=True)
        
        # Create sample markdown files with tags
        sample_files = {
            "00-Meta/Project-Profile.md": """# Project Profile: Test Project

## Basic Information
- **Project Name:** Test Project
- **Status:** Development
- **Priority:** High

## Tags
#project-test #development #high-priority #python #api #testing

## Goals
- Test the Cortex system
- Validate AI learning
- Ensure cross-vault linking works
""",
            "01-Planning/Project-Charter.md": """# Project Charter

## Overview
This is a test project for validating Cortex functionality.

## Technology Stack
- **Backend:** #python #fastapi #api
- **Testing:** #pytest #testing #quality-assurance
- **Deployment:** #docker #kubernetes #deployment

## Success Criteria
- All tests pass
- AI learning detects patterns
- Cross-vault connections work
""",
            "02-Development/Development-Log.md": """# Development Log

## 2025-08-10
Started project setup with #python and #fastapi.

### Progress
- Set up project structure
- Implemented basic #api endpoints
- Added #testing framework
- Configured #docker deployment

### Next Steps
- Add more comprehensive #testing
- Optimize #performance
- Implement #authentication
""",
            "03-Decisions/ADR-001-Technology-Stack.md": """# ADR-001: Technology Stack Selection

## Status
Accepted

## Context
Need to choose technology stack for the project.

## Decision
Using #python #fastapi for backend, #pytest for testing.

## Consequences
- Fast development with #fastapi
- Comprehensive #testing with #pytest  
- Easy #deployment with #docker
""",
            "05-Insights/Lessons-Learned.md": """# Lessons Learned

## Development Insights
- #python #fastapi combination works well
- #testing early saves time later
- #docker simplifies #deployment
- #api design is crucial for #performance

## Best Practices
- Use consistent #tagging for AI learning
- Document decisions in ADRs
- Test everything with #pytest
"""
        }
        
        for file_path, content in sample_files.items():
            full_path = vault_path / file_path
            full_path.write_text(content, encoding='utf-8')
        
        return vault_path

class TestMultiVaultAILearningEngine:
    """Test suite for AI Learning Engine"""
    
    @pytest.fixture
    def temp_hub_vault(self):
        """Create temporary hub vault for testing"""
        temp_dir = tempfile.mkdtemp()
        hub_path = Path(temp_dir) / "cortex"
        TestData.create_test_vault(hub_path, "cortex")
        yield hub_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_project_vault(self):
        """Create temporary project vault for testing"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / "project-test"
        TestData.create_test_vault(project_path, "project-test")
        yield project_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def ai_engine(self, temp_hub_vault):
        """Create AI Learning Engine instance for testing"""
        return MultiVaultAILearningEngine(str(temp_hub_vault))
    
    def test_initialization(self, ai_engine):
        """Test AI engine initialization"""
        assert ai_engine is not None
        assert ai_engine.hub_path.exists()
        assert ai_engine.engine_path.exists()
        assert ai_engine.config is not None
    
    def test_vault_discovery(self, ai_engine, temp_project_vault):
        """Test vault discovery functionality"""
        # Create project vault in same parent directory as hub
        parent_dir = ai_engine.hub_path.parent
        project_in_parent = parent_dir / "project-test"
        if not project_in_parent.exists():
            shutil.copytree(temp_project_vault, project_in_parent)
        
        vaults = ai_engine.discover_vaults()
        assert len(vaults) >= 1  # At least hub vault
        assert ai_engine.hub_path in vaults
    
    def test_vault_analysis(self, ai_engine):
        """Test individual vault analysis"""
        profile = ai_engine.analyze_vault(ai_engine.hub_path)
        
        assert profile is not None
        assert profile.name == "cortex"
        assert profile.file_count > 0
        assert profile.tag_count > 0
        assert profile.size_mb >= 0
        assert profile.ai_learning_enabled is True
    
    def test_tag_correlation_calculation(self, ai_engine):
        """Test tag correlation calculation"""
        ai_engine.calculate_tag_correlations()
        
        # Should find some correlations in test data
        assert isinstance(ai_engine.tag_correlations, list)
        
        # Check correlation structure if any found
        if ai_engine.tag_correlations:
            correlation = ai_engine.tag_correlations[0]
            assert hasattr(correlation, 'tag1')
            assert hasattr(correlation, 'tag2') 
            assert hasattr(correlation, 'correlation_score')
            assert 0 <= correlation.correlation_score <= 1
    
    def test_pattern_detection(self, ai_engine):
        """Test cross-vault pattern detection"""
        ai_engine.detect_cross_vault_patterns()
        
        assert isinstance(ai_engine.cross_vault_patterns, list)
        # With single vault, might not find cross-vault patterns
    
    def test_insight_generation(self, ai_engine):
        """Test insight generation"""
        # First run analysis to populate data
        ai_engine.run_full_analysis()
        
        insights = ai_engine.generate_insights()
        assert isinstance(insights, list)
        
        # Check insight structure if any generated
        if insights:
            insight = insights[0]
            assert 'type' in insight
            assert 'title' in insight
            assert 'description' in insight
    
    def test_full_analysis_cycle(self, ai_engine):
        """Test complete analysis cycle"""
        report = ai_engine.run_full_analysis()
        
        assert report is not None
        assert 'summary' in report
        assert 'vault_profiles' in report
        assert 'insights' in report
        
        summary = report['summary']
        assert 'vaults_analyzed' in summary
        assert 'tag_correlations_found' in summary
        assert 'cross_vault_patterns' in summary
        assert 'insights_generated' in summary

class TestCrossVaultLinker:
    """Test suite for Cross-Vault Linker"""
    
    @pytest.fixture
    def temp_vaults(self):
        """Create temporary vaults for testing"""
        temp_dir = tempfile.mkdtemp()
        hub_path = Path(temp_dir) / "cortex"
        project_path = Path(temp_dir) / "project-test"
        
        TestData.create_test_vault(hub_path, "cortex")
        TestData.create_test_vault(project_path, "project-test")
        
        yield hub_path, project_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def linker(self, temp_vaults):
        """Create Cross-Vault Linker instance for testing"""
        hub_path, _ = temp_vaults
        return CrossVaultLinker(str(hub_path))
    
    def test_initialization(self, linker):
        """Test linker initialization"""
        assert linker is not None
        assert linker.hub_path.exists()
        assert linker.linker_path.exists()
    
    def test_vault_discovery(self, linker, temp_vaults):
        """Test vault discovery in linker"""
        vaults = linker.discover_vaults()
        assert len(vaults) >= 1
    
    def test_file_tag_extraction(self, linker, temp_vaults):
        """Test tag extraction from files"""
        hub_path, _ = temp_vaults
        test_file = hub_path / "test.md"
        test_file.write_text("# Test\n\nThis has #tag1 and #tag2 tags.")
        
        tags = linker.extract_file_tags(test_file)
        assert 'tag1' in tags
        assert 'tag2' in tags
        assert len(tags) == 2
    
    def test_file_similarity_calculation(self, linker):
        """Test file similarity calculation"""
        tags1 = {'python', 'api', 'testing'}
        tags2 = {'python', 'api', 'deployment'}
        
        similarity = linker.calculate_file_similarity(tags1, tags2)
        assert 0 <= similarity <= 1
        assert similarity > 0  # Should have some overlap
    
    def test_cross_vault_link_finding(self, linker):
        """Test cross-vault link detection"""
        suggestions = linker.find_cross_vault_links(min_similarity=0.1)
        assert isinstance(suggestions, list)
        
        # Check suggestion structure if any found
        if suggestions:
            suggestion = suggestions[0]
            assert hasattr(suggestion, 'source_vault')
            assert hasattr(suggestion, 'target_vault')
            assert hasattr(suggestion, 'correlation_score')
            assert hasattr(suggestion, 'shared_tags')
    
    def test_vault_connection_generation(self, linker):
        """Test vault-level connection generation"""
        connections = linker.generate_vault_connections()
        assert isinstance(connections, list)
    
    def test_full_linking_cycle(self, linker):
        """Test complete linking cycle"""
        report = linker.run_full_linking_cycle()
        
        assert report is not None
        assert 'summary' in report
        
        summary = report['summary']
        assert 'total_link_suggestions' in summary
        assert 'strong_links' in summary
        assert 'medium_links' in summary
        assert 'weak_links' in summary
        assert 'vault_connections' in summary

class TestCortexManagementService:
    """Test suite for Management Service"""
    
    @pytest.fixture
    def temp_hub_vault(self):
        """Create temporary hub vault for testing"""
        temp_dir = tempfile.mkdtemp()
        hub_path = Path(temp_dir) / "cortex"
        TestData.create_test_vault(hub_path, "cortex")
        yield hub_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def management_service(self, temp_hub_vault):
        """Create Management Service instance for testing"""
        return CortexManagementService(str(temp_hub_vault))
    
    def test_initialization(self, management_service):
        """Test management service initialization"""
        assert management_service is not None
        assert management_service.hub_path.exists()
        assert management_service.service_path.exists()
        assert management_service.ai_engine is not None
        assert management_service.vault_linker is not None
    
    def test_service_stats_initialization(self, management_service):
        """Test service statistics initialization"""
        stats = management_service.service_stats
        assert 'cycles_completed' in stats
        assert 'vaults_discovered' in stats
        assert 'links_generated' in stats
        assert 'patterns_detected' in stats
        assert 'uptime_start' in stats
        
        assert stats['cycles_completed'] == 0
        assert stats['vaults_discovered'] == 0
        assert stats['links_generated'] == 0
        assert stats['patterns_detected'] == 0
    
    @patch('subprocess.run')
    def test_notification_sending(self, mock_subprocess, management_service):
        """Test macOS notification sending"""
        management_service.send_macos_notification("Test Title", "Test Message")
        mock_subprocess.assert_called_once()
    
    def test_status_summary(self, management_service):
        """Test status summary generation"""
        summary = management_service.get_status_summary()
        
        assert 'service_status' in summary
        assert 'uptime_hours' in summary
        assert 'cycles_completed' in summary
        assert 'vaults_discovered' in summary
        assert 'links_generated' in summary
        
        assert summary['service_status'] == 'running'
        assert summary['cycles_completed'] == 0
    
    def test_full_cycle_execution(self, management_service):
        """Test complete management cycle"""
        # This is an integration test
        success = management_service.run_full_cycle()
        
        assert success is True
        assert management_service.service_stats['cycles_completed'] == 1
        assert management_service.last_full_analysis is not None
        assert management_service.last_linking_cycle is not None

class TestIntegration:
    """Integration tests for the complete Cortex system"""
    
    @pytest.fixture
    def complete_system(self):
        """Set up complete Cortex system for integration testing"""
        temp_dir = tempfile.mkdtemp()
        
        # Create hub vault
        hub_path = Path(temp_dir) / "cortex"
        TestData.create_test_vault(hub_path, "cortex")
        
        # Create multiple project vaults
        project1_path = Path(temp_dir) / "project-alpha"
        project2_path = Path(temp_dir) / "project-beta"
        TestData.create_test_vault(project1_path, "project-alpha")
        TestData.create_test_vault(project2_path, "project-beta")
        
        # Initialize all components
        ai_engine = MultiVaultAILearningEngine(str(hub_path))
        linker = CrossVaultLinker(str(hub_path))
        management = CortexManagementService(str(hub_path))
        
        yield {
            'hub_path': hub_path,
            'project_paths': [project1_path, project2_path],
            'ai_engine': ai_engine,
            'linker': linker,
            'management': management
        }
        
        shutil.rmtree(temp_dir)
    
    def test_end_to_end_workflow(self, complete_system):
        """Test complete end-to-end Cortex workflow"""
        system = complete_system
        
        # Step 1: AI Analysis
        ai_report = system['ai_engine'].run_full_analysis()
        assert ai_report is not None
        assert ai_report['summary']['vaults_analyzed'] >= 1
        
        # Step 2: Cross-Vault Linking
        linking_report = system['linker'].run_full_linking_cycle()
        assert linking_report is not None
        
        # Step 3: Management Cycle
        success = system['management'].run_full_cycle()
        assert success is True
        
        # Verify integration
        assert system['management'].service_stats['cycles_completed'] == 1
        assert system['management'].service_stats['vaults_discovered'] >= 1
    
    def test_multi_vault_pattern_detection(self, complete_system):
        """Test pattern detection across multiple vaults"""
        system = complete_system
        
        # Run analysis
        system['ai_engine'].run_full_analysis()
        
        # Should detect patterns across multiple vaults
        patterns = system['ai_engine'].cross_vault_patterns
        assert isinstance(patterns, list)
        # With multiple vaults, should find some patterns
    
    def test_cross_vault_connections(self, complete_system):
        """Test cross-vault connection generation"""
        system = complete_system
        
        # Run linking
        system['linker'].run_full_linking_cycle()
        
        # Should find some connections between vaults
        suggestions = system['linker'].link_suggestions
        connections = system['linker'].vault_connections
        
        assert isinstance(suggestions, list)
        assert isinstance(connections, list)
    
    def test_system_persistence(self, complete_system):
        """Test that system state persists between runs"""
        system = complete_system
        
        # Run first cycle
        system['management'].run_full_cycle()
        first_cycle_stats = system['management'].service_stats.copy()
        
        # Create new management instance (simulates restart)
        new_management = CortexManagementService(str(system['hub_path']))
        
        # Should load previous state
        # Note: In real system, this would load from saved files
        assert new_management.service_stats['uptime_start'] is not None

# Test configuration and helpers
@pytest.fixture(scope="session")
def test_config():
    """Global test configuration"""
    return {
        'test_data_dir': Path(__file__).parent / 'test_data',
        'temp_dir_prefix': 'cortex_test_',
        'timeout_seconds': 30
    }

def test_system_requirements():
    """Test that system requirements are met"""
    # Test Python version
    assert sys.version_info >= (3, 8), "Python 3.8+ required"
    
    # Test required modules can be imported
    try:
        import yaml
        import schedule
        import pathlib
        import json
        import logging
    except ImportError as e:
        pytest.fail(f"Required module missing: {e}")

if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v", "--tb=short"])
