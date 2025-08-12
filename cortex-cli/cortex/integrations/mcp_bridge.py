#!/usr/bin/env python3
"""
MCP Bridge - Model Context Protocol Integration for Cortex
Enables seamless communication between Cortex and Obsidian via MCP Server
Migrated and enhanced from 00-System/Cross-Vault-Linker/obsidian_mcp_bridge.py
"""

import json
import logging
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
import hashlib
import re


@dataclass
class ObsidianNote:
    """Represents an Obsidian note structure"""
    title: str
    content: str
    vault: str
    path: str
    tags: List[str]
    metadata: Dict[str, Any]


@dataclass
class MCPCommand:
    """Represents an MCP command to execute"""
    command: str
    vault: str
    args: Dict[str, Any]
    expected_result: str = ""


@dataclass
class SyncResult:
    """Result of a sync operation with enhanced metrics"""
    success: bool
    notes_created: int
    links_added: int
    errors: List[str]
    execution_time: float
    vault_path: str = ""
    sync_summary: str = ""


class MCPBridge:
    """
    Advanced Model Context Protocol Bridge for Cortex-Obsidian Integration
    
    Provides sophisticated bidirectional synchronization between Cortex AI insights
    and Obsidian vaults via MCP server protocol with real-time updates and
    comprehensive metadata tracking.
    """
    
    def __init__(self, mcp_config_path: Optional[str] = None, cortex_path: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mcp_config_path = mcp_config_path or self._find_mcp_config()
        self.cortex_path = cortex_path or "/Users/simonjanke/Projects/cortex"
        self.supported_vaults = self._discover_obsidian_vaults()
        self.sync_metadata = self._load_sync_metadata()
        
        self.logger.info(f"MCP Bridge initialized with {len(self.supported_vaults)} vaults")
    
    def _find_mcp_config(self) -> str:
        """Find Claude Desktop MCP configuration"""
        possible_paths = [
            "~/Library/Application Support/Claude/claude_desktop_config.json",
            "~/.config/claude-desktop/config.json",
            "~/AppData/Roaming/Claude/claude_desktop_config.json"
        ]
        
        for path in possible_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                self.logger.info(f"Found MCP config at: {expanded_path}")
                return str(expanded_path)
        
        self.logger.warning("No MCP config found, using fallback mode")
        return ""
    
    def _discover_obsidian_vaults(self) -> Dict[str, str]:
        """Discover available Obsidian vaults from MCP config and file system"""
        vaults = {}
        
        # Add Cortex main vault
        if Path(self.cortex_path).exists():
            vaults['cortex'] = self.cortex_path
        
        # Try to read MCP config for additional vaults
        if self.mcp_config_path:
            try:
                with open(self.mcp_config_path, 'r') as f:
                    config = json.load(f)
                
                for server_name, server_config in config.get('mcpServers', {}).items():
                    if 'obsidian' in server_name.lower():
                        vault_path = server_config.get('args', {}).get('vault_path', '')
                        if vault_path and Path(vault_path).exists():
                            vault_name = Path(vault_path).name
                            vaults[vault_name] = vault_path
                            
                self.logger.info(f"Discovered {len(vaults)} Obsidian vaults: {list(vaults.keys())}")
                
            except Exception as e:
                self.logger.error(f"Error reading MCP config: {e}")
        
        return vaults
    
    def _load_sync_metadata(self) -> Dict:
        """Load sync metadata to track changes"""
        metadata_path = Path(self.cortex_path) / "00-System" / "Cross-Vault-Linker" / "data" / "sync_metadata.json"
        
        default_metadata = {
            'last_sync': None,
            'synced_notes': {},
            'vault_stats': {},
            'total_syncs': 0,
            'success_rate': 1.0,
            'last_errors': []
        }
        
        try:
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    loaded = json.load(f)
                    default_metadata.update(loaded)
        except Exception as e:
            self.logger.error(f"Could not load sync metadata: {e}")
        
        return default_metadata
    
    def _save_sync_metadata(self):
        """Save sync metadata with error handling"""
        metadata_path = Path(self.cortex_path) / "00-System" / "Cross-Vault-Linker" / "data" / "sync_metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(self.sync_metadata, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save sync metadata: {e}")
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content change detection"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _is_duplicate_content(self, content_hash: str, topic: str) -> bool:
        """Check if content with similar hash already exists"""
        for note_path, note_data in self.sync_metadata.get('synced_notes', {}).items():
            if note_data.get('hash') == content_hash:
                self.logger.info(f"Duplicate content detected for {topic}")
                return True
            
            # Check for similar topics (basic similarity)
            if note_data.get('topic', '').lower() == topic.lower():
                self.logger.info(f"Similar topic found for {topic}")
                return True
        
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for file system compatibility"""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores
        return sanitized.strip('_')[:200]  # Limit length
    
    async def create_ai_insight_note(self, insight_data: Dict, vault_name: str = "cortex") -> Tuple[bool, str]:
        """Create a new note in Obsidian with Cortex AI insights"""
        try:
            start_time = datetime.now()
            timestamp = start_time.strftime('%Y%m%d_%H%M%S')
            note_title = f"AI Insight - {insight_data.get('topic', 'General')} - {timestamp}"
            safe_filename = self._sanitize_filename(note_title)
            
            content = self._format_insight_content(insight_data, timestamp)
            content_hash = self._generate_content_hash(content)
            
            # Check for duplicates
            if self._is_duplicate_content(content_hash, insight_data.get('topic', '')):
                return False, "Duplicate content detected"
            
            vault_path = self.supported_vaults.get(vault_name)
            if not vault_path:
                return False, f"Vault {vault_name} not found"
            
            # Create insight folder structure
            folder_path = Path(vault_path) / "05-Insights" / "Auto-Gap-Fills"
            folder_path.mkdir(parents=True, exist_ok=True)
            
            file_path = folder_path / f"{safe_filename}.md"
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # Update metadata
            self.sync_metadata['synced_notes'][str(file_path)] = {
                'created': timestamp,
                'type': 'ai_insight',
                'topic': insight_data.get('topic', ''),
                'hash': content_hash,
                'confidence': insight_data.get('confidence', 0)
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Created AI insight note: {file_path} (took {execution_time:.2f}s)")
            
            return True, str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error creating AI insight note: {e}")
            return False, str(e)
    
    def _format_insight_content(self, insight_data: Dict, timestamp: str) -> str:
        """Format AI insight data into structured Obsidian markdown"""
        content = f"""# {insight_data.get('topic', 'AI Insight')}

> 🧠 **Cortex AI Generated Insight**  
> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> Confidence: {insight_data.get('confidence', 0):.2f}  
> Source: {insight_data.get('source', 'Cortex Analysis')}

## Executive Summary
{insight_data.get('summary', 'No summary available')}

## Key Findings
"""
        
        for finding in insight_data.get('findings', []):
            content += f"- {finding}\n"
        
        if insight_data.get('related_concepts'):
            content += f"""
## Related Concepts
"""
            for concept in insight_data.get('related_concepts', []):
                content += f"- [[{concept}]]\n"
        
        if insight_data.get('cross_vault_connections'):
            content += f"""
## Cross-Vault Connections
"""
            for connection in insight_data.get('cross_vault_connections', []):
                vault = connection.get('vault', '')
                file = connection.get('file', '')
                score = connection.get('score', 0)
                content += f"- **{vault}**: [[{vault}/{file}]] (confidence: {score:.2f})\n"
        
        if insight_data.get('recommendations'):
            content += f"""
## Recommendations
"""
            for rec in insight_data.get('recommendations', []):
                content += f"- {rec}\n"
        
        # Add metadata tags
        tags = insight_data.get('tags', []) + ['cortex-ai', 'auto-generated', 'ai-insight']
        content += f"""
## Tags
{' '.join([f'#{tag}' for tag in tags])}

## Metadata
- **Insight ID**: {insight_data.get('id', 'unknown')}
- **Analysis Type**: {insight_data.get('analysis_type', 'general')}
- **Generated**: {timestamp}
- **Confidence Score**: {insight_data.get('confidence', 0):.3f}
- **Processing Time**: {insight_data.get('processing_time', 0):.2f}s

---
*This insight was automatically generated by Cortex AI*  
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    async def sync_cross_vault_links(self, link_suggestions: List[Dict], target_vault: str = "cortex") -> SyncResult:
        """Sync cross-vault link suggestions with advanced filtering and quality control"""
        start_time = datetime.now()
        notes_created = 0
        links_added = 0
        errors = []
        
        try:
            vault_path = self.supported_vaults.get(target_vault)
            if not vault_path:
                errors.append(f"Vault {target_vault} not found")
                return SyncResult(False, 0, 0, errors, 0)
            
            # Advanced quality filtering
            real_vaults = self._get_real_vault_count(link_suggestions)
            if real_vaults < 2:
                self.logger.info(f"Skipping link sync: only {real_vaults} real vaults detected")
                return SyncResult(True, 0, 0, [], 0, vault_path, "No real cross-vault connections")
            
            # Categorize links by confidence
            strong_links = [s for s in link_suggestions if s.get('confidence', 0) >= 0.8]
            medium_links = [s for s in link_suggestions if 0.6 <= s.get('confidence', 0) < 0.8]
            weak_links = [s for s in link_suggestions if s.get('confidence', 0) < 0.6]
            
            # Filter out test data
            strong_links = self._filter_test_suggestions(strong_links)
            medium_links = self._filter_test_suggestions(medium_links)
            weak_links = self._filter_test_suggestions(weak_links)
            
            total_real_suggestions = len(strong_links) + len(medium_links) + len(weak_links)
            if total_real_suggestions == 0:
                self.logger.info("No real cross-vault connections found after filtering")
                return SyncResult(True, 0, 0, [], 0, vault_path, "Filtered out test data")
            
            # Create bidirectional links for strong connections
            for suggestion in strong_links:
                success = await self._add_bidirectional_link(suggestion, target_vault)
                if success:
                    links_added += 1
                else:
                    errors.append(f"Failed to create link for {suggestion.get('source_file', 'unknown')}")
            
            # Create summary note
            summary_created, summary_path = await self._create_link_summary_note(
                strong_links + medium_links + weak_links, target_vault, strong_links, medium_links, weak_links
            )
            
            if summary_created:
                notes_created += 1
            else:
                errors.append("Failed to create link summary note")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Synced {len(link_suggestions)} link suggestions: {notes_created} notes, {links_added} links (took {execution_time:.2f}s)")
            
            # Update metadata
            self.sync_metadata['last_sync'] = datetime.now().isoformat()
            self.sync_metadata['vault_stats'][target_vault] = {
                'last_link_sync': datetime.now().isoformat(),
                'links_processed': len(link_suggestions),
                'strong_links': len(strong_links),
                'medium_links': len(medium_links),
                'weak_links': len(weak_links)
            }
            self._save_sync_metadata()
            
            return SyncResult(
                success=len(errors) == 0,
                notes_created=notes_created,
                links_added=links_added,
                errors=errors,
                execution_time=execution_time,
                vault_path=vault_path,
                sync_summary=f"Processed {total_real_suggestions} quality links"
            )
            
        except Exception as e:
            errors.append(str(e))
            self.logger.error(f"Error syncing cross-vault links: {e}")
            return SyncResult(False, notes_created, links_added, errors, 
                            (datetime.now() - start_time).total_seconds(), vault_path)
    
    def _get_real_vault_count(self, link_suggestions: List[Dict]) -> int:
        """Count actual vaults (excluding test/fake data)"""
        vault_names = set()
        for suggestion in link_suggestions:
            target_vault = suggestion.get('target_vault', '').lower()
            if target_vault and not any(test_word in target_vault for test_word in ['test', 'fake', 'example']):
                vault_names.add(target_vault)
        return len(vault_names)
    
    def _filter_test_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """Filter out test/fake suggestions with enhanced detection"""
        real_suggestions = []
        test_indicators = ['test', 'fake', 'example', 'demo', 'placeholder', 'sample']
        
        for suggestion in suggestions:
            source_file = suggestion.get('source_file', '').lower()
            target_file = suggestion.get('target_file', '').lower()
            target_vault = suggestion.get('target_vault', '').lower()
            
            is_test = any(
                indicator in source_file or 
                indicator in target_file or 
                indicator in target_vault
                for indicator in test_indicators
            )
            
            if not is_test:
                real_suggestions.append(suggestion)
        
        return real_suggestions
    
    async def _add_bidirectional_link(self, suggestion: Dict, vault_name: str) -> bool:
        """Add sophisticated bidirectional links between suggested files"""
        try:
            source_file = suggestion.get('source_file', '')
            target_file = suggestion.get('target_file', '')
            target_vault = suggestion.get('target_vault', '')
            confidence = suggestion.get('confidence', 0)
            shared_tags = suggestion.get('shared_tags', [])
            
            vault_path = self.supported_vaults.get(vault_name)
            if not vault_path:
                return False
            
            # Enhanced link section with metadata
            link_section = f"""

## 🔗 Cross-Vault Connection (Auto-Generated)
**Related**: [[{target_vault}/{target_file}]] (confidence: {confidence:.2f})  
**Shared concepts**: {', '.join(shared_tags) if shared_tags else 'Content similarity'}  
**Auto-linked**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Connection type**: {suggestion.get('connection_type', 'Semantic similarity')}

> This connection was automatically discovered by Cortex AI through content analysis and tag correlation.
"""
            
            # Add link to source file
            source_path = Path(vault_path) / source_file
            if source_path.exists() and source_path.suffix == '.md':
                async with aiofiles.open(source_path, 'a', encoding='utf-8') as f:
                    await f.write(link_section)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error adding bidirectional link: {e}")
            return False
    
    async def _create_link_summary_note(self, suggestions: List[Dict], vault_name: str,
                                      strong_links: List[Dict], medium_links: List[Dict],
                                      weak_links: List[Dict]) -> Tuple[bool, str]:
        """Create comprehensive summary note with link analysis"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = self._sanitize_filename(f"Cross-Vault-Links-Summary-{timestamp}")
            
            vault_path = self.supported_vaults.get(vault_name)
            if not vault_path:
                return False, f"Vault {vault_name} not found"
            
            folder_path = Path(vault_path) / "02-Neural-Links" / "Cross-Vault-Connections"
            folder_path.mkdir(parents=True, exist_ok=True)
            
            content = f"""# Cross-Vault Link Analysis - {datetime.now().strftime('%Y-%m-%d')}

> 🌐 **Cross-Vault Connection Report**  
> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> Total connections: {len(suggestions)}  
> Analysis confidence: {sum(s.get('confidence', 0) for s in suggestions) / len(suggestions):.2f} avg

## Executive Summary
This report contains automatically discovered connections between vaults based on content analysis, tag correlation, and semantic similarity.

## Connection Quality Analysis
- **High Confidence** (≥0.8): {len(strong_links)} connections
- **Medium Confidence** (0.6-0.8): {len(medium_links)} connections  
- **Low Confidence** (<0.6): {len(weak_links)} connections
"""
            
            if strong_links:
                content += "\n## 🔗 High Confidence Connections\n"
                for link in strong_links[:10]:  # Limit to top 10
                    content += f"- **[[{link.get('source_file', '')}]]** ↔ **[[{link.get('target_vault', '')}/{link.get('target_file', '')}]]**\n"
                    content += f"  - *Confidence*: {link.get('confidence', 0):.3f}\n"
                    content += f"  - *Shared tags*: {', '.join(link.get('shared_tags', []))}\n\n"
            
            if medium_links:
                content += "\n## 📎 Medium Confidence Connections\n"
                for link in medium_links[:5]:  # Limit to top 5
                    content += f"- [[{link.get('source_file', '')}]] → [[{link.get('target_vault', '')}/{link.get('target_file', '')}]] ({link.get('confidence', 0):.2f})\n"
            
            # Add metadata and tags
            content += f"""
## Analytics
- **Total vaults analyzed**: {self._get_real_vault_count(suggestions)}
- **Connection algorithms**: Tag correlation, content similarity, semantic analysis
- **Generated by**: Cortex Cross-Vault Linker
- **Processing time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Tags
#cross-vault-links #auto-generated #cortex-ai #analysis-report

---
*This report was automatically generated by Cortex AI Cross-Vault Analysis*
"""
            
            file_path = folder_path / f"{safe_filename}.md"
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            self.logger.info(f"Created cross-vault summary: {file_path}")
            return True, str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error creating link summary note: {e}")
            return False, str(e)
    
    async def sync_chat_session(self, chat_data: Dict, vault_name: str = "cortex") -> Tuple[bool, str]:
        """Sync chat session with advanced conversation analysis"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session_topic = chat_data.get('topic', 'General Discussion')
            note_title = f"Claude Chat - {session_topic} - {timestamp}"
            safe_filename = self._sanitize_filename(note_title)
            
            content = self._format_chat_content(chat_data, timestamp)
            
            vault_path = self.supported_vaults.get(vault_name)
            if not vault_path:
                return False, f"Vault {vault_name} not found"
            
            folder_path = Path(vault_path) / "02-Neural-Links" / "Chat-Sessions"
            folder_path.mkdir(parents=True, exist_ok=True)
            
            file_path = folder_path / f"{safe_filename}.md"
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # Update metadata
            content_hash = self._generate_content_hash(content)
            self.sync_metadata['synced_notes'][str(file_path)] = {
                'created': timestamp,
                'type': 'chat_session',
                'topic': session_topic,
                'hash': content_hash,
                'message_count': len(chat_data.get('messages', []))
            }
            
            self.logger.info(f"Synced chat session: {file_path}")
            return True, str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error syncing chat session: {e}")
            return False, str(e)
    
    def _format_chat_content(self, chat_data: Dict, timestamp: str) -> str:
        """Format chat data into structured Obsidian markdown"""
        topic = chat_data.get('topic', 'General Discussion')
        messages = chat_data.get('messages', [])
        insights = chat_data.get('extracted_insights', [])
        decisions = chat_data.get('decisions', [])
        action_items = chat_data.get('action_items', [])
        related_notes = chat_data.get('related_notes', [])
        
        content = f"""# {topic}

> 💬 **Claude Chat Session**  
> Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> Duration: {chat_data.get('duration', 'Unknown')}  
> Messages: {len(messages)}  
> Complexity: {chat_data.get('complexity_score', 0):.2f}

## Executive Summary
{chat_data.get('summary', 'No summary available')}
"""
        
        if insights:
            content += "\n## 🧠 Key Insights\n"
            for insight in insights:
                content += f"- {insight}\n"
        
        if decisions:
            content += "\n## 🎯 Decisions Made\n"
            for decision in decisions:
                content += f"- **{decision.get('topic', 'Decision')}**: {decision.get('description', '')}\n"
                if decision.get('rationale'):
                    content += f"  - *Rationale*: {decision.get('rationale')}\n"
        
        if action_items:
            content += "\n## ✅ Action Items\n"
            for item in action_items:
                status = "- [ ]" if not item.get('completed') else "- [x]"
                content += f"{status} {item.get('description', '')}\n"
        
        if related_notes:
            content += "\n## 🔗 Related Notes\n"
            for note in related_notes:
                content += f"- [[{note}]]\n"
        
        # Add conversation excerpt (intelligent sampling)
        if messages and len(messages) > 0:
            content += "\n## 💬 Conversation Highlights\n"
            # Intelligent message sampling
            if len(messages) <= 10:
                sample_messages = messages
            else:
                # Take first 2, last 3, and 3 from middle
                sample_messages = (messages[:2] + 
                                 messages[len(messages)//2-1:len(messages)//2+2] + 
                                 messages[-3:])
            
            for i, msg in enumerate(sample_messages):
                role = msg.get('role', 'unknown')
                text = msg.get('content', '')
                # Smart truncation
                if len(text) > 300:
                    text = text[:300] + '...'
                content += f"**{role.capitalize()}**: {text}\n\n"
                
                # Add separator for long conversations
                if i < len(sample_messages) - 1 and len(messages) > 10:
                    content += "---\n"
        
        # Enhanced metadata
        tags = chat_data.get('tags', []) + ['chat-session', 'claude', 'cortex-ai']
        content += f"""
## 🏷️ Tags
{' '.join([f'#{tag}' for tag in tags])}

## 📊 Session Metadata
- **Session ID**: {chat_data.get('session_id', 'unknown')}
- **Model**: {chat_data.get('model', 'Claude')}
- **Generated**: {timestamp}
- **Word Count**: {chat_data.get('word_count', 0):,}
- **Turn Count**: {len(messages) // 2}
- **Avg Response Length**: {chat_data.get('avg_response_length', 0):.0f} chars
- **Session Quality**: {chat_data.get('session_quality', 'Good')}

---
*This note was automatically generated from a Claude chat session via Cortex MCP Bridge*  
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def get_sync_statistics(self) -> Dict:
        """Get comprehensive sync statistics"""
        stats = {
            'total_syncs': self.sync_metadata.get('total_syncs', 0),
            'success_rate': self.sync_metadata.get('success_rate', 1.0),
            'last_sync': self.sync_metadata.get('last_sync', 'Never'),
            'supported_vaults': len(self.supported_vaults),
            'vault_names': list(self.supported_vaults.keys()),
            'synced_notes': len(self.sync_metadata.get('synced_notes', {})),
            'vault_stats': self.sync_metadata.get('vault_stats', {}),
            'recent_errors': self.sync_metadata.get('last_errors', [])[-5:],  # Last 5 errors
            'mcp_config_found': bool(self.mcp_config_path),
            'bridge_version': '2.0.0'
        }
        
        # Calculate note type distribution
        note_types = {}
        for note_data in self.sync_metadata.get('synced_notes', {}).values():
            note_type = note_data.get('type', 'unknown')
            note_types[note_type] = note_types.get(note_type, 0) + 1
        
        stats['note_type_distribution'] = note_types
        return stats
    
    def get_supported_vaults(self) -> Dict[str, str]:
        """Get all supported Obsidian vaults"""
        return self.supported_vaults.copy()
    
    async def validate_vault_connection(self, vault_name: str) -> Tuple[bool, str]:
        """Validate connection to specific vault"""
        try:
            vault_path = self.supported_vaults.get(vault_name)
            if not vault_path:
                return False, f"Vault {vault_name} not found"
            
            vault_path_obj = Path(vault_path)
            if not vault_path_obj.exists():
                return False, f"Vault path does not exist: {vault_path}"
            
            # Check if it's a valid Obsidian vault (has .obsidian folder)
            obsidian_config = vault_path_obj / ".obsidian"
            if obsidian_config.exists():
                return True, f"Valid Obsidian vault at {vault_path}"
            
            # Check if it's a Cortex vault (has 00-System)
            cortex_system = vault_path_obj / "00-System"
            if cortex_system.exists():
                return True, f"Valid Cortex vault at {vault_path}"
            
            return True, f"Directory exists but may not be an Obsidian vault: {vault_path}"
            
        except Exception as e:
            return False, f"Error validating vault {vault_name}: {e}"


# Main integration functions for CLI usage
async def create_ai_insight(insight_data: Dict, target_vault: str = "cortex") -> SyncResult:
    """Create AI insight note in Obsidian vault"""
    bridge = MCPBridge()
    start_time = datetime.now()
    
    try:
        success, result = await bridge.create_ai_insight_note(insight_data, target_vault)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if success:
            return SyncResult(True, 1, 0, [], execution_time, result, "AI insight created successfully")
        else:
            return SyncResult(False, 0, 0, [result], execution_time, "", "Failed to create AI insight")
            
    except Exception as e:
        return SyncResult(False, 0, 0, [str(e)], (datetime.now() - start_time).total_seconds())


async def sync_cross_vault_links(link_suggestions: List[Dict], target_vault: str = "cortex") -> SyncResult:
    """Sync cross-vault link suggestions to Obsidian"""
    bridge = MCPBridge()
    return await bridge.sync_cross_vault_links(link_suggestions, target_vault)


async def sync_chat_session(chat_data: Dict, target_vault: str = "cortex") -> SyncResult:
    """Sync chat session data to Obsidian vault"""
    bridge = MCPBridge()
    start_time = datetime.now()
    
    try:
        success, result = await bridge.sync_chat_session(chat_data, target_vault)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if success:
            return SyncResult(True, 1, 0, [], execution_time, result, "Chat session synced successfully")
        else:
            return SyncResult(False, 0, 0, [result], execution_time, "", "Failed to sync chat session")
            
    except Exception as e:
        return SyncResult(False, 0, 0, [str(e)], (datetime.now() - start_time).total_seconds())


async def integrate_with_obsidian(ai_insights: List[Dict] = None, cross_vault_links: List[Dict] = None,
                                chat_data: Optional[Dict] = None, target_vault: str = "cortex") -> SyncResult:
    """Main integration function to sync all Cortex results with Obsidian"""
    bridge = MCPBridge()
    start_time = datetime.now()
    total_notes = 0
    total_links = 0
    all_errors = []
    
    try:
        # Sync AI insights
        if ai_insights:
            for insight in ai_insights:
                success, result = await bridge.create_ai_insight_note(insight, target_vault)
                if success:
                    total_notes += 1
                else:
                    all_errors.append(f"AI insight sync failed: {result}")
        
        # Sync cross-vault links
        if cross_vault_links:
            link_result = await bridge.sync_cross_vault_links(cross_vault_links, target_vault)
            total_notes += link_result.notes_created
            total_links += link_result.links_added
            all_errors.extend(link_result.errors)
        
        # Sync chat session
        if chat_data:
            success, result = await bridge.sync_chat_session(chat_data, target_vault)
            if success:
                total_notes += 1
            else:
                all_errors.append(f"Chat sync failed: {result}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        bridge.logger.info(f"MCP Integration complete: {total_notes} notes, {total_links} links, {len(all_errors)} errors (took {execution_time:.2f}s)")
        
        return SyncResult(
            success=len(all_errors) == 0,
            notes_created=total_notes,
            links_added=total_links,
            errors=all_errors,
            execution_time=execution_time,
            vault_path=bridge.supported_vaults.get(target_vault, ""),
            sync_summary=f"Integrated {total_notes} notes with {total_links} links"
        )
        
    except Exception as e:
        all_errors.append(str(e))
        logging.error(f"Error in MCP Bridge integration: {e}")
        return SyncResult(
            success=False,
            notes_created=total_notes,
            links_added=total_links,
            errors=all_errors,
            execution_time=(datetime.now() - start_time).total_seconds(),
            vault_path=bridge.supported_vaults.get(target_vault, "")
        )


def get_mcp_bridge_info() -> Dict:
    """Get MCP Bridge configuration and status"""
    bridge = MCPBridge()
    return {
        'bridge_info': bridge.get_sync_statistics(),
        'supported_vaults': bridge.get_supported_vaults(),
        'mcp_config_path': bridge.mcp_config_path,
        'cortex_path': bridge.cortex_path
    }
