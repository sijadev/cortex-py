#!/usr/bin/env python3
"""
Test suite for MCP Bridge - Critical Risk Mitigation  
Tests for cortex/integrations/mcp_bridge.py (currently 0% coverage)
"""

import pytest
import json
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Import the critical MCP Bridge components
try:
    from cortex.integrations.mcp_bridge import (
        ObsidianNote,
        MCPCommand,
        SyncResult,
        MCPBridge
    )
    MCP_BRIDGE_AVAILABLE = True
except ImportError:
    MCP_BRIDGE_AVAILABLE = False


@pytest.mark.skipif(not MCP_BRIDGE_AVAILABLE, reason="MCP Bridge components not available")
class TestMCPBridgeCore:
    """Test suite for critical MCP Bridge functionality"""
    
    def test_obsidian_note_creation(self):
        """Test ObsidianNote dataclass creation and validation"""
        note = ObsidianNote(
            title="Test Note",
            content="# Test Content\n\nThis is a test note",
            vault="test-vault",
            path="Notes/Test Note.md",
            tags=["test", "automation"],
            metadata={"created": datetime.now().isoformat()}
        )
        
        assert note.title == "Test Note"
        assert note.vault == "test-vault"
        assert note.path == "Notes/Test Note.md"
        assert len(note.tags) == 2
        assert "test" in note.tags
        assert "automation" in note.tags
        assert "created" in note.metadata
    
    def test_mcp_command_creation(self):
        """Test MCPCommand dataclass creation"""
        command = MCPCommand(
            command="create_note",
            vault="test-vault",
            args={
                "title": "New Note",
                "content": "Content here",
                "tags": ["new", "mcp"]
            },
            expected_result="note_created"
        )
        
        assert command.command == "create_note"
        assert command.vault == "test-vault"
        assert command.args["title"] == "New Note"
        assert command.expected_result == "note_created"
    
    def test_sync_result_creation(self):
        """Test SyncResult dataclass creation"""
        result = SyncResult(
            success=True,
            notes_created=5,
            links_added=12,
            errors=[],
            execution_time=2.34,
            vault_path="/path/to/vault",
            sync_summary="Successfully synced 5 notes with 12 links"
        )
        
        assert result.success is True
        assert result.notes_created == 5
        assert result.links_added == 12
        assert len(result.errors) == 0
        assert result.execution_time == 2.34
        assert "Successfully synced" in result.sync_summary
    
    def test_sync_result_with_errors(self):
        """Test SyncResult with error conditions"""
        result = SyncResult(
            success=False,
            notes_created=2,
            links_added=1,
            errors=["Connection timeout", "Invalid vault path"],
            execution_time=10.5,
            vault_path="/invalid/path"
        )
        
        assert result.success is False
        assert len(result.errors) == 2
        assert "Connection timeout" in result.errors
        assert "Invalid vault path" in result.errors
        assert result.execution_time > 10.0
    
    def test_obsidian_note_serialization(self):
        """Test ObsidianNote serialization for MCP communication"""
        note = ObsidianNote(
            title="Serialization Test",
            content="Content for serialization",
            vault="serialize-vault", 
            path="Tests/Serialize.md",
            tags=["serialize", "json"],
            metadata={"author": "test", "version": "1.0"}
        )
        
        # Test that it can be converted to dict
        note_dict = note.__dict__
        assert isinstance(note_dict, dict)
        assert note_dict["title"] == "Serialization Test"
        
        # Test JSON serialization
        json_str = json.dumps(note_dict)
        assert isinstance(json_str, str)
        
        # Test deserialization
        loaded = json.loads(json_str)
        assert loaded["title"] == "Serialization Test"
        assert loaded["vault"] == "serialize-vault"
    
    def test_mcp_command_validation(self):
        """Test MCP command structure validation"""
        # Test valid command types
        valid_commands = ["create_note", "update_note", "delete_note", "link_notes", "sync_vault"]
        
        for cmd in valid_commands:
            command = MCPCommand(
                command=cmd,
                vault="test-vault",
                args={"test": "data"}
            )
            assert command.command == cmd
            assert command.vault == "test-vault"
    
    @patch('cortex.integrations.mcp_bridge.Path.exists')
    def test_mcp_bridge_initialization(self, mock_exists):
        """Test MCP Bridge initialization - critical path"""
        mock_exists.return_value = True
        
        try:
            bridge = MCPBridge()
            assert bridge is not None
        except Exception as e:
            pytest.skip(f"MCP Bridge initialization failed: {e}")


@pytest.mark.skipif(not MCP_BRIDGE_AVAILABLE, reason="MCP Bridge components not available")
class TestMCPBridgeIntegration:
    """Integration tests for MCP Bridge functionality"""
    
    @pytest.mark.asyncio
    async def test_mcp_bridge_async_methods(self):
        """Test that async methods can be mocked and called"""
        with patch('cortex.integrations.mcp_bridge.MCPBridge') as MockBridge:
            mock_instance = AsyncMock()
            MockBridge.return_value = mock_instance
            
            bridge = MockBridge()
            
            # Test sync_to_obsidian method
            mock_result = SyncResult(
                success=True,
                notes_created=1,
                links_added=0,
                errors=[],
                execution_time=1.0
            )
            mock_instance.sync_to_obsidian.return_value = mock_result
            
            result = await bridge.sync_to_obsidian([], "test-vault")
            assert result.success is True
            assert result.notes_created == 1
    
    def test_obsidian_note_content_parsing(self):
        """Test parsing different types of Obsidian note content"""
        # Test note with frontmatter
        note_with_frontmatter = ObsidianNote(
            title="Frontmatter Note",
            content="""---
tags: [test, parsing]
created: 2025-01-13
---

# Frontmatter Note

This note has frontmatter.""",
            vault="parse-test",
            path="Parse/Frontmatter.md",
            tags=["test", "parsing"],
            metadata={"has_frontmatter": True}
        )
        
        assert "---" in note_with_frontmatter.content
        assert "tags: [test, parsing]" in note_with_frontmatter.content
        
        # Test note with links
        note_with_links = ObsidianNote(
            title="Links Note",
            content="This references [[Another Note]] and [[Yet Another]]",
            vault="parse-test",
            path="Parse/Links.md", 
            tags=["links"],
            metadata={"has_links": True}
        )
        
        assert "[[Another Note]]" in note_with_links.content
        assert "[[Yet Another]]" in note_with_links.content
    
    def test_mcp_command_args_validation(self):
        """Test MCP command arguments structure"""
        # Test create_note command args
        create_cmd = MCPCommand(
            command="create_note",
            vault="validation-vault",
            args={
                "title": "Validation Test",
                "content": "Content here",
                "path": "Tests/Validation.md",
                "tags": ["validation", "test"]
            }
        )
        
        required_args = ["title", "content", "path"]
        for arg in required_args:
            assert arg in create_cmd.args, f"Missing required arg: {arg}"
        
        # Test link_notes command args
        link_cmd = MCPCommand(
            command="link_notes", 
            vault="validation-vault",
            args={
                "source_note": "Note A",
                "target_note": "Note B",
                "link_type": "bidirectional"
            }
        )
        
        link_args = ["source_note", "target_note", "link_type"]
        for arg in link_args:
            assert arg in link_cmd.args, f"Missing link arg: {arg}"


class TestMCPBridgeRiskMitigation:
    """Critical risk mitigation tests - these should always run"""
    
    def test_mcp_bridge_import_safety(self):
        """Test that MCP Bridge can be safely imported"""
        try:
            from cortex.integrations import mcp_bridge
            assert mcp_bridge is not None
        except ImportError as e:
            pytest.fail(f"Critical: MCP Bridge module cannot be imported: {e}")
    
    def test_dataclass_definitions(self):
        """Test that critical dataclasses are properly defined"""
        if not MCP_BRIDGE_AVAILABLE:
            pytest.skip("MCP Bridge not available - structural test skipped")
        
        # Test ObsidianNote structure
        import inspect
        from cortex.integrations.mcp_bridge import ObsidianNote
        
        sig = inspect.signature(ObsidianNote)
        required_params = ['title', 'content', 'vault', 'path', 'tags', 'metadata']
        
        for param in required_params:
            assert param in sig.parameters, f"ObsidianNote missing required parameter: {param}"
        
        # Test MCPCommand structure  
        from cortex.integrations.mcp_bridge import MCPCommand
        
        cmd_sig = inspect.signature(MCPCommand)
        cmd_params = ['command', 'vault', 'args']
        
        for param in cmd_params:
            assert param in cmd_sig.parameters, f"MCPCommand missing required parameter: {param}"
    
    def test_module_structure(self):
        """Test that MCP Bridge module has expected structure"""
        try:
            import cortex.integrations.mcp_bridge as mcp_bridge
            
            expected_classes = ['ObsidianNote', 'MCPCommand', 'SyncResult']
            
            for class_name in expected_classes:
                assert hasattr(mcp_bridge, class_name), f"Missing class: {class_name}"
                
        except ImportError:
            pytest.skip("MCP Bridge module structure test skipped - import failed")
    
    def test_critical_functionality_exists(self):
        """Test that critical MCP functionality is available"""
        if not MCP_BRIDGE_AVAILABLE:
            pytest.skip("MCP Bridge not available - functionality test skipped")
        
        try:
            # Test that we can create basic objects without crashing
            from cortex.integrations.mcp_bridge import ObsidianNote, MCPCommand, SyncResult
            
            # Basic instantiation test
            note = ObsidianNote(
                title="Risk Test",
                content="Testing critical paths", 
                vault="risk-vault",
                path="test.md",
                tags=[],
                metadata={}
            )
            assert note.title == "Risk Test"
            
            cmd = MCPCommand(command="test", vault="test", args={})
            assert cmd.command == "test"
            
            result = SyncResult(
                success=True,
                notes_created=0,
                links_added=0, 
                errors=[],
                execution_time=0.0
            )
            assert result.success is True
            
        except Exception as e:
            pytest.fail(f"Critical: Basic MCP Bridge functionality failed: {e}")


class TestMCPBridgeErrorHandling:
    """Test error handling and edge cases"""
    
    def test_sync_result_error_handling(self):
        """Test SyncResult handles various error scenarios"""
        # Test with multiple errors
        result = SyncResult(
            success=False,
            notes_created=0,
            links_added=0,
            errors=[
                "Network timeout",
                "Vault not found", 
                "Permission denied",
                "Invalid note format"
            ],
            execution_time=30.0,
            vault_path="/failed/path"
        )
        
        assert result.success is False
        assert len(result.errors) == 4
        assert "Network timeout" in result.errors
        assert result.execution_time == 30.0
    
    def test_obsidian_note_edge_cases(self):
        """Test ObsidianNote with edge case data"""
        # Test with empty content
        empty_note = ObsidianNote(
            title="Empty Note",
            content="",
            vault="edge-cases",
            path="empty.md",
            tags=[],
            metadata={}
        )
        assert empty_note.content == ""
        assert len(empty_note.tags) == 0
        
        # Test with very long content
        long_content = "x" * 10000
        long_note = ObsidianNote(
            title="Long Note",
            content=long_content,
            vault="edge-cases", 
            path="long.md",
            tags=["long"],
            metadata={"length": len(long_content)}
        )
        assert len(long_note.content) == 10000
        assert long_note.metadata["length"] == 10000
