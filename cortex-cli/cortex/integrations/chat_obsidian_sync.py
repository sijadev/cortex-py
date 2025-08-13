#!/usr/bin/env python3
"""
Chat to Obsidian Synchronization
Handles synchronization of chat sessions with Obsidian vaults
Part of the Cortex MCP integration system
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

# Import the components from obsidian_mcp_bridge
from .obsidian_mcp_bridge import ChatMessage, ObsidianMCPBridge

@dataclass
class ChatSession:
    """Represents a complete chat session"""
    session_id: str
    title: str
    messages: List[ChatMessage]
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class ChatObsidianSyncer:
    """
    Enhanced Chat to Obsidian synchronization service
    Manages chat session storage and sync with Obsidian vaults
    """
    
    def __init__(self, cortex_path: str, bridge: Optional[ObsidianMCPBridge] = None):
        self.cortex_path = Path(cortex_path)
        self.bridge = bridge
        self.sessions_path = self.cortex_path / "02-Neural-Links" / "Chat-Sessions"
        self.sessions_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger('ChatObsidianSyncer')
        
        # Session registry
        self.sessions = {}
        
        self.logger.info(f"Chat Obsidian Syncer initialized for {cortex_path}")
    
    def set_bridge(self, bridge: ObsidianMCPBridge):
        """Set the MCP bridge for syncing"""
        self.bridge = bridge
        self.logger.info("MCP bridge configured for chat sync")
    
    def create_session(self, title: str, session_id: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        if session_id is None:
            session_id = f"session_{int(datetime.now().timestamp())}"
        
        session = ChatSession(
            session_id=session_id,
            title=title,
            messages=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            tags=["chat-session", "cortex"]
        )
        
        self.sessions[session_id] = session
        self._save_session(session)
        
        self.logger.info(f"Created chat session: {title} ({session_id})")
        return session
    
    def add_message_to_session(self, session_id: str, role: str, content: str, 
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a message to an existing session"""
        if session_id not in self.sessions:
            self.logger.error(f"Session {session_id} not found")
            return False
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        
        self.sessions[session_id].messages.append(message)
        self.sessions[session_id].updated_at = datetime.now().isoformat()
        
        self._save_session(self.sessions[session_id])
        return True
    
    def _save_session(self, session: ChatSession):
        """Save session to disk"""
        try:
            session_file = self.sessions_path / f"{session.session_id}.json"
            session_data = {
                'session_id': session.session_id,
                'title': session.title,
                'created_at': session.created_at,
                'updated_at': session.updated_at,
                'metadata': session.metadata,
                'tags': session.tags,
                'messages': [
                    {
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp,
                        'metadata': msg.metadata,
                        'message_id': msg.message_id
                    } for msg in session.messages
                ]
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save session {session.session_id}: {e}")
    
    def load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load session from disk"""
        try:
            session_file = self.sessions_path / f"{session_id}.json"
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            messages = [
                ChatMessage(
                    role=msg['role'],
                    content=msg['content'],
                    timestamp=msg['timestamp'],
                    metadata=msg.get('metadata'),
                    message_id=msg.get('message_id')
                ) for msg in session_data['messages']
            ]
            
            session = ChatSession(
                session_id=session_data['session_id'],
                title=session_data['title'],
                messages=messages,
                created_at=session_data['created_at'],
                updated_at=session_data['updated_at'],
                metadata=session_data.get('metadata'),
                tags=session_data.get('tags')
            )
            
            self.sessions[session_id] = session
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    async def sync_session_to_obsidian(self, session_id: str, vault_name: str, 
                                      format_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Sync a specific session to Obsidian"""
        if not self.bridge:
            return {'error': 'No MCP bridge configured'}
        
        if session_id not in self.sessions:
            # Try to load from disk
            session = self.load_session(session_id)
            if not session:
                return {'error': f'Session {session_id} not found'}
        else:
            session = self.sessions[session_id]
        
        try:
            # Use the bridge to sync
            result = await self.bridge.sync_chat_to_obsidian(session.messages, vault_name)
            
            if result.get('status') == 'success':
                # Update session metadata
                if not session.metadata:
                    session.metadata = {}
                session.metadata['last_obsidian_sync'] = datetime.now().isoformat()
                session.metadata['synced_to_vault'] = vault_name
                self._save_session(session)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to sync session to Obsidian: {e}")
            return {'error': str(e)}
    
    async def sync_all_sessions(self, vault_name: str) -> Dict[str, Any]:
        """Sync all sessions to Obsidian"""
        if not self.bridge:
            return {'error': 'No MCP bridge configured'}
        
        results = {
            'total_sessions': len(self.sessions),
            'synced': 0,
            'failed': 0,
            'errors': []
        }
        
        for session_id in self.sessions:
            try:
                sync_result = await self.sync_session_to_obsidian(session_id, vault_name)
                if sync_result.get('status') == 'success':
                    results['synced'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"{session_id}: {sync_result.get('error', 'Unknown error')}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{session_id}: {str(e)}")
        
        return results
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a session"""
        if session_id not in self.sessions:
            session = self.load_session(session_id)
            if not session:
                return {'error': f'Session {session_id} not found'}
        else:
            session = self.sessions[session_id]
        
        return {
            'session_id': session.session_id,
            'title': session.title,
            'message_count': len(session.messages),
            'created_at': session.created_at,
            'updated_at': session.updated_at,
            'tags': session.tags or [],
            'has_metadata': bool(session.metadata),
            'last_sync': session.metadata.get('last_obsidian_sync') if session.metadata else None
        }
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions"""
        # Load sessions from disk
        for session_file in self.sessions_path.glob("*.json"):
            session_id = session_file.stem
            if session_id not in self.sessions:
                self.load_session(session_id)
        
        return [self.get_session_summary(session_id) for session_id in self.sessions]
    
    def create_sample_chat_data(self) -> List[ChatMessage]:
        """Create sample chat data for testing"""
        sample_messages = [
            ChatMessage(
                role='user',
                content='How can I improve my note-taking workflow with Obsidian?',
                timestamp=datetime.now().isoformat()
            ),
            ChatMessage(
                role='assistant',
                content='Here are some effective strategies for improving your Obsidian workflow:\n\n1. **Use consistent tagging**: Develop a tagging system that makes sense for your needs\n2. **Create templates**: Set up note templates for recurring content types\n3. **Leverage linking**: Use [[double brackets]] to create connections between ideas\n4. **Regular reviews**: Schedule time to review and reorganize your notes',
                timestamp=datetime.now().isoformat()
            ),
            ChatMessage(
                role='user',
                content='What about integrating with external tools?',
                timestamp=datetime.now().isoformat()
            ),
            ChatMessage(
                role='assistant',
                content='Great question! Integration options include:\n\n- **Readwise**: Import highlights from books and articles\n- **Zotero**: Manage academic references\n- **GitHub**: Sync with code repositories\n- **Calendar apps**: Create meeting notes automatically\n- **Task managers**: Connect with Todoist or other apps',
                timestamp=datetime.now().isoformat()
            )
        ]
        
        return sample_messages

# Utility functions for message formatting
def format_messages_for_sync(messages: List[Dict[str, Any]]) -> List[ChatMessage]:
    """Convert message dictionaries to ChatMessage objects"""
    chat_messages = []
    
    for msg in messages:
        chat_message = ChatMessage(
            role=msg.get('role', 'user'),
            content=msg.get('content', ''),
            timestamp=msg.get('timestamp', datetime.now().isoformat()),
            metadata=msg.get('metadata'),
            message_id=msg.get('id')
        )
        chat_messages.append(chat_message)
    
    return chat_messages

def create_chat_message(role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> ChatMessage:
    """Helper function to create a ChatMessage"""
    return ChatMessage(
        role=role,
        content=content,
        timestamp=datetime.now().isoformat(),
        metadata=metadata
    )
