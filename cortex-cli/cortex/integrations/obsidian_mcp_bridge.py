#!/usr/bin/env python3
"""
Obsidian MCP Bridge Implementation
Provides Model Context Protocol integration with Obsidian
Implements missing components for test compatibility
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

@dataclass
class ChatMessage:
    """Represents a chat message for Obsidian sync"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    message_id: Optional[str] = None
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = f"{self.role}_{hash(self.content)}_{self.timestamp}"

@dataclass
class VaultConnection:
    """Represents a connection to an Obsidian vault"""
    name: str
    path: str
    active: bool = False
    last_sync: Optional[str] = None
    file_count: int = 0
    sync_enabled: bool = True

class ObsidianMCPBridge:
    """
    Model Context Protocol Bridge for Obsidian Integration
    Handles communication between Cortex and Obsidian vaults
    """
    
    def __init__(self, cortex_path: str, obsidian_config: Optional[Dict[str, Any]] = None):
        self.cortex_path = Path(cortex_path)
        self.config = obsidian_config or {}
        
        # Initialize bridge configuration
        self.bridge_config_path = self.cortex_path / ".cortex" / "obsidian_bridge.json"
        self.logs_path = self.cortex_path / ".cortex" / "logs" / "obsidian_bridge"
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Supported vault registry
        self.supported_vaults = {}
        
        # Connection status
        self.connections = {}
        
        # Load configuration
        self._load_bridge_config()
        
        self.logger.info(f"Obsidian MCP Bridge initialized for {cortex_path}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the MCP bridge"""
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger('ObsidianMCPBridge')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            log_file = self.logs_path / f"bridge_{datetime.now().strftime('%Y%m%d')}.log"
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_bridge_config(self):
        """Load bridge configuration"""
        default_config = {
            'mcp_settings': {
                'protocol_version': '1.0',
                'timeout': 30,
                'retry_attempts': 3,
                'batch_size': 50
            },
            'sync_settings': {
                'auto_sync': True,
                'sync_interval': 300,  # 5 minutes
                'conflict_resolution': 'timestamp',
                'backup_enabled': True
            },
            'vault_discovery': {
                'auto_discover': True,
                'search_paths': [
                    '~/Documents/Obsidian Vaults',
                    '~/Obsidian',
                    '~/Documents'
                ]
            }
        }
        
        if self.bridge_config_path.exists():
            try:
                with open(self.bridge_config_path, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in loaded_config[key]:
                                loaded_config[key][subkey] = subvalue
                self.config = loaded_config
            except Exception as e:
                self.logger.warning(f"Failed to load bridge config: {e}, using defaults")
                self.config = default_config
        else:
            self.config = default_config
            self._save_bridge_config()
    
    def _save_bridge_config(self):
        """Save bridge configuration"""
        try:
            self.bridge_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.bridge_config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save bridge config: {e}")
    
    def discover_vaults(self) -> List[VaultConnection]:
        """Discover available Obsidian vaults"""
        discovered_vaults = []
        
        if not self.config.get('vault_discovery', {}).get('auto_discover', True):
            return discovered_vaults
        
        search_paths = self.config.get('vault_discovery', {}).get('search_paths', [])
        
        for search_path_str in search_paths:
            search_path = Path(search_path_str).expanduser()
            if search_path.exists():
                try:
                    for vault_path in search_path.rglob('.obsidian'):
                        vault_root = vault_path.parent
                        vault_name = vault_root.name
                        
                        # Count markdown files
                        file_count = len(list(vault_root.rglob('*.md')))
                        
                        vault_connection = VaultConnection(
                            name=vault_name,
                            path=str(vault_root),
                            file_count=file_count
                        )
                        
                        discovered_vaults.append(vault_connection)
                        self.logger.info(f"Discovered vault: {vault_name} at {vault_root}")
                        
                except Exception as e:
                    self.logger.warning(f"Error discovering vaults in {search_path}: {e}")
        
        # Update connections registry
        for vault in discovered_vaults:
            self.connections[vault.name] = vault
        
        return discovered_vaults
    
    def connect_vault(self, vault_name: str, vault_path: str) -> bool:
        """Connect to a specific Obsidian vault"""
        try:
            vault_path_obj = Path(vault_path)
            
            # Check if vault exists and has .obsidian folder
            obsidian_config_path = vault_path_obj / '.obsidian'
            if not obsidian_config_path.exists():
                self.logger.error(f"Not a valid Obsidian vault: {vault_path}")
                return False
            
            # Create connection
            connection = VaultConnection(
                name=vault_name,
                path=vault_path,
                active=True,
                last_sync=datetime.now().isoformat(),
                file_count=len(list(vault_path_obj.rglob('*.md')))
            )
            
            self.connections[vault_name] = connection
            self.supported_vaults[vault_name] = vault_path
            
            self.logger.info(f"Connected to vault: {vault_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to vault {vault_name}: {e}")
            return False
    
    def disconnect_vault(self, vault_name: str) -> bool:
        """Disconnect from a vault"""
        try:
            if vault_name in self.connections:
                self.connections[vault_name].active = False
                self.logger.info(f"Disconnected from vault: {vault_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to disconnect from vault {vault_name}: {e}")
            return False
    
    def get_vault_status(self, vault_name: str) -> Dict[str, Any]:
        """Get status of a connected vault"""
        if vault_name not in self.connections:
            return {'error': f'Vault {vault_name} not connected'}
        
        connection = self.connections[vault_name]
        vault_path = Path(connection.path)
        
        status = {
            'name': vault_name,
            'path': connection.path,
            'active': connection.active,
            'last_sync': connection.last_sync,
            'file_count': len(list(vault_path.rglob('*.md'))) if vault_path.exists() else 0,
            'sync_enabled': connection.sync_enabled,
            'mcp_compatible': True,  # Assume compatibility
            'timestamp': datetime.now().isoformat()
        }
        
        return status
    
    async def sync_chat_to_obsidian(self, chat_messages: List[ChatMessage], vault_name: str) -> Dict[str, Any]:
        """Sync chat messages to an Obsidian vault"""
        try:
            if vault_name not in self.connections:
                return {'error': f'Vault {vault_name} not connected'}
            
            connection = self.connections[vault_name]
            vault_path = Path(connection.path)
            
            # Create chat sessions folder
            chat_folder = vault_path / "Chat Sessions"
            chat_folder.mkdir(exist_ok=True)
            
            # Generate chat session file
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            chat_file = chat_folder / f"Chat_Session_{timestamp}.md"
            
            # Convert chat messages to markdown
            markdown_content = self._format_chat_as_markdown(chat_messages)
            
            # Write to file
            chat_file.write_text(markdown_content, encoding='utf-8')
            
            # Update connection
            connection.last_sync = datetime.now().isoformat()
            
            result = {
                'status': 'success',
                'vault': vault_name,
                'file_created': str(chat_file),
                'messages_synced': len(chat_messages),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Synced {len(chat_messages)} messages to {vault_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to sync chat to Obsidian: {e}")
            return {'error': str(e)}
    
    def _format_chat_as_markdown(self, chat_messages: List[ChatMessage]) -> str:
        """Format chat messages as markdown"""
        lines = [
            "# Chat Session",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            ""
        ]
        
        for message in chat_messages:
            role_emoji = {
                'user': '👤',
                'assistant': '🤖',
                'system': '⚙️'
            }.get(message.role, '💬')
            
            lines.extend([
                f"## {role_emoji} {message.role.title()}",
                f"*{message.timestamp}*",
                "",
                message.content,
                "",
                "---",
                ""
            ])
        
        # Add tags
        lines.extend([
            "",
            "#chat-session #ai-conversation #cortex-sync"
        ])
        
        return "\n".join(lines)
    
    async def sync_notes_from_obsidian(self, vault_name: str, pattern: str = "*.md") -> Dict[str, Any]:
        """Sync notes from Obsidian vault to Cortex"""
        try:
            if vault_name not in self.connections:
                return {'error': f'Vault {vault_name} not connected'}
            
            connection = self.connections[vault_name]
            vault_path = Path(connection.path)
            
            # Find matching files
            md_files = list(vault_path.rglob(pattern))
            
            synced_files = []
            for md_file in md_files:
                try:
                    # Read content
                    content = md_file.read_text(encoding='utf-8')
                    
                    # Create corresponding file in Cortex
                    relative_path = md_file.relative_to(vault_path)
                    cortex_file = self.cortex_path / "02-Neural-Links" / "Obsidian-Sync" / relative_path
                    cortex_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Add sync metadata
                    sync_header = f"""<!-- Synced from Obsidian vault: {vault_name} -->
<!-- Original path: {md_file} -->
<!-- Sync timestamp: {datetime.now().isoformat()} -->

"""
                    cortex_file.write_text(sync_header + content, encoding='utf-8')
                    synced_files.append(str(cortex_file))
                    
                except Exception as e:
                    self.logger.warning(f"Failed to sync file {md_file}: {e}")
            
            # Update connection
            connection.last_sync = datetime.now().isoformat()
            
            result = {
                'status': 'success',
                'vault': vault_name,
                'files_synced': len(synced_files),
                'files': synced_files,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Synced {len(synced_files)} files from {vault_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to sync from Obsidian: {e}")
            return {'error': str(e)}
    
    def create_mcp_compatible_note(self, title: str, content: str, vault_name: str, 
                                  tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a note compatible with MCP protocol"""
        try:
            if vault_name not in self.connections:
                return {'error': f'Vault {vault_name} not connected'}
            
            connection = self.connections[vault_name]
            vault_path = Path(connection.path)
            
            # Sanitize filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            note_file = vault_path / f"{safe_title}.md"
            
            # Create note content with MCP metadata
            note_lines = [
                f"# {title}",
                "",
                f"*Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                f"*Source: Cortex MCP Bridge*",
                "",
                "---",
                "",
                content
            ]
            
            # Add tags
            if tags:
                note_lines.extend([
                    "",
                    "",
                    " ".join(f"#{tag}" for tag in tags)
                ])
            
            note_content = "\n".join(note_lines)
            note_file.write_text(note_content, encoding='utf-8')
            
            result = {
                'status': 'success',
                'vault': vault_name,
                'file_created': str(note_file),
                'title': title,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Created MCP note '{title}' in {vault_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create MCP note: {e}")
            return {'error': str(e)}
    
    def get_bridge_status(self) -> Dict[str, Any]:
        """Get overall bridge status"""
        return {
            'bridge_active': True,
            'cortex_path': str(self.cortex_path),
            'connected_vaults': len([c for c in self.connections.values() if c.active]),
            'total_vaults': len(self.connections),
            'last_activity': datetime.now().isoformat(),
            'mcp_version': self.config.get('mcp_settings', {}).get('protocol_version', '1.0'),
            'connections': {name: asdict(conn) for name, conn in self.connections.items()}
        }

# Async integration function
async def integrate_with_obsidian(cortex_path: str, vault_path: str, 
                                 sync_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """High-level integration function for Obsidian"""
    try:
        # Create bridge
        bridge = ObsidianMCPBridge(cortex_path)
        
        # Connect to vault
        vault_name = Path(vault_path).name
        connection_success = bridge.connect_vault(vault_name, vault_path)
        
        if not connection_success:
            return {'error': f'Failed to connect to vault at {vault_path}'}
        
        result = {
            'status': 'success',
            'bridge_created': True,
            'vault_connected': vault_name,
            'cortex_path': cortex_path,
            'vault_path': vault_path,
            'timestamp': datetime.now().isoformat()
        }
        
        # Perform initial sync if requested
        if sync_options and sync_options.get('initial_sync', False):
            sync_result = await bridge.sync_notes_from_obsidian(vault_name)
            result['initial_sync'] = sync_result
        
        return result
        
    except Exception as e:
        return {'error': f'Integration failed: {str(e)}'}


class ChatObsidianSyncer:
    """
    Synchronizes chat sessions with Obsidian vaults
    Handles the conversion and management of chat data
    """
    
    def __init__(self, bridge: Optional[ObsidianMCPBridge] = None):
        self.bridge = bridge
        self.logger = logging.getLogger('ChatObsidianSyncer')
    
    def set_bridge(self, bridge: ObsidianMCPBridge):
        """Set the MCP bridge for syncing"""
        self.bridge = bridge
    
    async def sync_chat_session(self, messages: List[ChatMessage], vault_name: str, 
                               session_title: Optional[str] = None) -> Dict[str, Any]:
        """Sync a chat session to Obsidian"""
        if not self.bridge:
            return {'error': 'No MCP bridge configured'}
        
        try:
            result = await self.bridge.sync_chat_to_obsidian(messages, vault_name)
            
            if session_title and result.get('status') == 'success':
                # Optionally rename the generated file
                pass
            
            return result
            
        except Exception as e:
            return {'error': f'Chat sync failed: {str(e)}'}
    
    def format_messages_for_sync(self, messages: List[Dict[str, Any]]) -> List[ChatMessage]:
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
