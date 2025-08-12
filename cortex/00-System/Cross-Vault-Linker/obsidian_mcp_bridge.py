#!/usr/bin/env python3
"""
Obsidian MCP Bridge - Integration between Cortex Cross-Vault-Linker and Obsidian via MCP Server
Enables real-time synchronization of AI insights directly into Obsidian notes
"""

import json
import logging
import subprocess
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import hashlib
import re

@dataclass
class ObsidianNote:
    """Represents an Obsidian note structure"""
    title: str
    content: str
    tags: List[str]
    links: List[str]
    vault_path: str
    created_date: str
    modified_date: str

@dataclass
class MCPCommand:
    """Represents an MCP command to execute"""
    action: str  # 'create_note', 'update_note', 'add_link', 'add_tag'
    params: Dict[str, Any]
    vault_name: str

@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    notes_created: int
    links_added: int
    errors: List[str]
    execution_time: float

class ObsidianMCPBridge:
    """Bridge between Cortex AI insights and Obsidian via MCP Server"""
    
    def __init__(self, mcp_config_path: Optional[str] = None, cortex_path: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mcp_config_path = mcp_config_path or self._find_mcp_config()
        self.cortex_path = cortex_path or "/Users/simonjanke/Projects/cortex"
        self.supported_vaults = self._discover_obsidian_vaults()
        self.sync_metadata = self._load_sync_metadata()
        
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
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load sync metadata: {e}")
        
        return {
            'last_sync': None,
            'synced_notes': {},
            'note_hashes': {},
            'vault_stats': {}
        }
    
    def _save_sync_metadata(self):
        """Save sync metadata"""
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
    
    async def create_cortex_insight_note(self, insight_data: Dict, vault_name: str = "cortex") -> Tuple[bool, str]:
        """Create a new note in Obsidian with Cortex AI insights"""
        start_time = datetime.now()
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            note_title = f"Cortex Insight - {insight_data.get('topic', 'General')} - {timestamp}"
            safe_filename = self._sanitize_filename(note_title)
            
            content = self._format_insight_content(insight_data, timestamp)
            content_hash = self._generate_content_hash(content)
            
            # Check if similar content already exists
            if self._is_duplicate_content(content_hash, insight_data.get('topic', '')):
                self.logger.info(f"Skipping duplicate insight: {note_title}")
                return False, "Duplicate content detected"
            
            vault_path = self.supported_vaults.get(vault_name)
            if not vault_path:
                return False, f"Vault {vault_name} not found"
            
            # Create note file
            folder_path = Path(vault_path) / "02-Neural-Links" / "AI-Generated"
            folder_path.mkdir(parents=True, exist_ok=True)
            file_path = folder_path / f"{safe_filename}.md"
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # Update metadata
            self.sync_metadata['synced_notes'][str(file_path)] = {
                'created': timestamp,
                'type': 'insight',
                'topic': insight_data.get('topic', ''),
                'hash': content_hash
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Created insight note: {file_path} (took {execution_time:.2f}s)")
            
            return True, str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error creating insight note: {e}")
            return False, str(e)
    
    def _is_duplicate_content(self, content_hash: str, topic: str) -> bool:
        """Check if content with similar hash already exists"""
        for note_path, metadata in self.sync_metadata.get('synced_notes', {}).items():
            if (metadata.get('hash') == content_hash or 
                (metadata.get('topic') == topic and metadata.get('type') == 'insight')):
                # Check if file still exists
                if Path(note_path).exists():
                    return True
                else:
                    # Clean up orphaned metadata
                    del self.sync_metadata['synced_notes'][note_path]
        
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for file system compatibility"""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '-', filename)
        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        return sanitized
    
    def _format_insight_content(self, insight_data: Dict, timestamp: str) -> str:
        """Format AI insight data into Obsidian markdown"""
        content = f"""# {insight_data.get('topic', 'AI Insight')}

> 🧠 **Cortex AI Generated Insight**  
> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> Confidence: {insight_data.get('confidence', 0):.2f}

## Summary
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
                # Create proper wiki links
                content += f"- [[{concept}]]\n"
        
        if insight_data.get('cross_vault_connections'):
            content += f"""
## Cross-Vault Connections
"""
            for connection in insight_data.get('cross_vault_connections', []):
                vault = connection.get('vault', '')
                file = connection.get('file', '')
                score = connection.get('score', 0)
                # Create relative path links for cross-vault references
                content += f"- **{vault}**: [[{vault}/{file}]] (confidence: {score:.2f})\n"
        
        # Add tags section
        tags = insight_data.get('tags', []) + ['cortex-ai', 'auto-generated']
        content += f"""
## Tags
{' '.join([f'#{tag}' for tag in tags])}

## Metadata
- **Source Vaults**: {', '.join(insight_data.get('source_vaults', []))}
- **Correlation Count**: {insight_data.get('correlation_count', 0)}
- **Confidence Score**: {insight_data.get('confidence', 0):.2f}
- **Generated**: {timestamp}
- **Pattern Types**: {', '.join(insight_data.get('pattern_types', []))}

## Source Data
```json
{json.dumps(insight_data, indent=2)}
```

---
*This note was automatically generated by Cortex AI Learning Engine*  
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return content
    
    async def sync_cross_vault_links(self, link_suggestions: List[Dict], target_vault: str = "cortex") -> SyncResult:
        """Sync cross-vault link suggestions directly into Obsidian notes"""
        start_time = datetime.now()
        notes_created = 0
        links_added = 0
        errors = []
        
        try:
            vault_path = self.supported_vaults.get(target_vault)
            if not vault_path:
                errors.append(f"Vault {target_vault} not found")
                return SyncResult(False, 0, 0, errors, 0)
            
            # Check if we have multiple real vaults (not single vault or test data)
            real_vaults = self._get_real_vault_count(link_suggestions)
            if real_vaults < 2:
                self.logger.info(f"Skipping summary creation: only {real_vaults} real vaults detected")
                return SyncResult(True, 0, 0, [], 0)
            
            # Group suggestions by strength
            strong_links = [s for s in link_suggestions if s.get('confidence', 0) >= 0.8]
            medium_links = [s for s in link_suggestions if 0.6 <= s.get('confidence', 0) < 0.8]
            weak_links = [s for s in link_suggestions if s.get('confidence', 0) < 0.6]
            
            # Filter out fake/test data
            strong_links = self._filter_fake_suggestions(strong_links)
            medium_links = self._filter_fake_suggestions(medium_links)
            weak_links = self._filter_fake_suggestions(weak_links)
            
            # Only proceed if we have real connections
            total_real_suggestions = len(strong_links) + len(medium_links) + len(weak_links)
            if total_real_suggestions == 0:
                self.logger.info("No real cross-vault connections found, skipping summary creation")
                return SyncResult(True, 0, 0, [], 0)
            
            # Create bidirectional links for strong connections
            for suggestion in strong_links:
                success = await self._add_bidirectional_link(suggestion, target_vault)
                if success:
                    links_added += 1
                else:
                    errors.append(f"Failed to create link for {suggestion.get('source_file', 'unknown')}")
            
            # Create summary note only if we have meaningful connections
            summary_created, summary_path = await self._create_link_summary_note(
                strong_links + medium_links + weak_links, target_vault, strong_links, medium_links, weak_links
            )
            
            if summary_created:
                notes_created += 1
            else:
                errors.append("Failed to create link summary note")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Synced {len(link_suggestions)} link suggestions: {notes_created} notes, {links_added} links (took {execution_time:.2f}s)")
            
            # Update sync metadata
            self.sync_metadata['last_sync'] = datetime.now().isoformat()
            self.sync_metadata['vault_stats'][target_vault] = {
                'last_link_sync': datetime.now().isoformat(),
                'links_processed': len(link_suggestions),
                'strong_links': len(strong_links),
                'medium_links': len(medium_links),
                'weak_links': len(weak_links)
            }
            self._save_sync_metadata()
            
            return SyncResult(True, notes_created, links_added, errors, execution_time)
            
        except Exception as e:
            errors.append(str(e))
            self.logger.error(f"Error syncing cross-vault links: {e}")
            return SyncResult(False, notes_created, links_added, errors, (datetime.now() - start_time).total_seconds())
    
    async def _add_bidirectional_link(self, suggestion: Dict, vault_name: str) -> bool:
        """Add bidirectional links between suggested files"""
        try:
            source_file = suggestion.get('source_file', '')
            target_file = suggestion.get('target_file', '')
            target_vault = suggestion.get('target_vault', '')
            confidence = suggestion.get('confidence', 0)
            shared_tags = suggestion.get('shared_tags', [])
            
            vault_path = self.supported_vaults.get(vault_name)
            if not vault_path:
                return False
            
            # Create link section to add
            link_section = f"""

## 🔗 Cross-Vault Connection
**Related**: [[{target_vault}/{target_file}]] (confidence: {confidence:.2f})  
**Shared concepts**: {', '.join(shared_tags)}  
**Auto-linked**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
"""
            
            # Find source file and add link
            source_path = Path(vault_path) / source_file
            if source_path.exists():
                async with aiofiles.open(source_path, 'a', encoding='utf-8') as f:
                    await f.write(link_section)
                
                self.logger.info(f"Added cross-vault link to: {source_path}")
                return True
            else:
                self.logger.warning(f"Source file not found: {source_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding bidirectional link: {e}")
            return False
    
    async def _create_link_summary_note(self, suggestions: List[Dict], vault_name: str, 
                                      strong_links: List[Dict], medium_links: List[Dict], 
                                      weak_links: List[Dict]) -> Tuple[bool, str]:
        """Create a summary note with all cross-vault link suggestions"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            note_title = f"Cross-Vault Link Summary - {timestamp}"
            
            content = f"""# Cross-Vault Link Summary

> 🔗 **Automatically Generated Cross-Vault Connections**  
> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> Total Suggestions: {len(suggestions)}

## Overview
- **Strong Connections** (≥0.8): {len(strong_links)}
- **Medium Connections** (0.6-0.8): {len(medium_links)}  
- **Weak Connections** (<0.6): {len(weak_links)}

## Strong Connections (≥0.8)
"""
            
            for suggestion in strong_links:
                source = suggestion.get('source_file', '')
                target_vault = suggestion.get('target_vault', '')
                target = suggestion.get('target_file', '')
                confidence = suggestion.get('confidence', 0)
                shared_tags = suggestion.get('shared_tags', [])
                
                content += f"""
### [[{source}]] ↔ [[{target_vault}/{target}]]
- **Confidence**: {confidence:.2f}
- **Shared Tags**: {', '.join([f'#{tag}' for tag in shared_tags])}
- **Reason**: {suggestion.get('reason', 'AI correlation detected')}
"""
            
            if medium_links:
                content += f"""

## Medium Connections (0.6-0.8)
"""
                for suggestion in medium_links:
                    content += f"- [[{suggestion.get('source_file', '')}]] ↔ [[{suggestion.get('target_vault', '')}/{suggestion.get('target_file', '')}]] ({suggestion.get('confidence', 0):.2f})\n"
            
            if weak_links:
                content += f"""

## Weak Connections (<0.6)
"""
                for suggestion in weak_links:
                    content += f"- [[{suggestion.get('source_file', '')}]] ↔ [[{suggestion.get('target_vault', '')}/{suggestion.get('target_file', '')}]] ({suggestion.get('confidence', 0):.2f})\n"
            
            # Add tag analysis
            content += f"""

## Tag Correlation Analysis
"""
            
            all_tags = []
            for suggestion in suggestions:
                all_tags.extend(suggestion.get('shared_tags', []))
            
            from collections import Counter
            tag_counts = Counter(all_tags)
            for tag, count in tag_counts.most_common(10):
                content += f"- **#{tag}** ({count} connections)\n"
            
            # Add actionable insights
            content += f"""

## Actionable Insights
"""
            
            if len(strong_links) > 0:
                content += f"- ✅ {len(strong_links)} strong connections have been automatically linked\n"
            
            if len(medium_links) > 3:
                content += f"- 📝 Consider reviewing {len(medium_links)} medium-strength connections for manual linking\n"
            
            most_connected_tags = [tag for tag, count in tag_counts.most_common(3)]
            if most_connected_tags:
                content += f"- 🏷️ Focus areas: {', '.join([f'#{tag}' for tag in most_connected_tags])}\n"
            
            content += f"""

## Statistics
- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Vaults Analyzed**: {len(set(s.get('target_vault', '') for s in suggestions))}
- **Average Confidence**: {sum(s.get('confidence', 0) for s in suggestions) / len(suggestions) if suggestions else 0:.2f}
- **Unique Tags**: {len(tag_counts)}

---
*Generated by Cortex Cross-Vault Linker*  
#cortex-ai #cross-vault-links #auto-generated #summary
"""
            
            vault_path = self.supported_vaults.get(vault_name)
            if not vault_path:
                return False, "Vault not found"
            
            folder_path = Path(vault_path) / "02-Neural-Links" / "Summaries"
            folder_path.mkdir(parents=True, exist_ok=True)
            file_path = folder_path / f"{note_title}.md"
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # Update metadata
            content_hash = self._generate_content_hash(content)
            self.sync_metadata['synced_notes'][str(file_path)] = {
                'created': timestamp,
                'type': 'link_summary',
                'hash': content_hash,
                'suggestions_count': len(suggestions)
            }
            
            self.logger.info(f"Created link summary note: {file_path}")
            return True, str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error creating link summary note: {e}")
            return False, str(e)
    
    async def sync_chat_session(self, chat_data: Dict, vault_name: str = "cortex") -> Tuple[bool, str]:
        """Sync a chat session to Obsidian as a structured note"""
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
                'hash': content_hash
            }
            
            self.logger.info(f"Synced chat session: {file_path}")
            return True, str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error syncing chat session: {e}")
            return False, str(e)
    
    def _format_chat_content(self, chat_data: Dict, timestamp: str) -> str:
        """Format chat data into Obsidian markdown"""
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

## Summary
{chat_data.get('summary', 'No summary available')}
"""
        
        if insights:
            content += """
## Key Insights
"""
            for insight in insights:
                content += f"- {insight}\n"
        
        if decisions:
            content += """
## Decisions Made
"""
            for decision in decisions:
                content += f"- **{decision.get('topic', 'Decision')}**: {decision.get('description', '')}\n"
                if decision.get('rationale'):
                    content += f"  - *Rationale*: {decision.get('rationale')}\n"
        
        if action_items:
            content += """
## Action Items
"""
            for item in action_items:
                status = "- [ ]" if not item.get('completed') else "- [x]"
                content += f"{status} {item.get('description', '')}\n"
        
        if related_notes:
            content += """
## Related Notes
"""
            for note in related_notes:
                content += f"- [[{note}]]\n"
        
        # Add conversation excerpt (last few messages)
        if messages and len(messages) > 0:
            content += """
## Conversation Excerpt
"""
            # Show last 5 messages as example
            recent_messages = messages[-5:] if len(messages) > 5 else messages
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                text = msg.get('content', '')[:200] + ('...' if len(msg.get('content', '')) > 200 else '')
                content += f"**{role.capitalize()}**: {text}\n\n"
        
        # Add tags
        tags = chat_data.get('tags', []) + ['chat-session', 'claude', 'cortex-ai']
        content += f"""
## Tags
{' '.join([f'#{tag}' for tag in tags])}

## Metadata
- **Session ID**: {chat_data.get('session_id', 'unknown')}
- **Model**: {chat_data.get('model', 'Claude')}
- **Generated**: {timestamp}
- **Word Count**: {chat_data.get('word_count', 0)}

---
*This note was automatically generated from a Claude chat session*  
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def get_sync_statistics(self) -> Dict:
        """Get statistics about sync operations"""
        stats = {
            'total_notes_synced': len(self.sync_metadata.get('synced_notes', {})),
            'last_sync': self.sync_metadata.get('last_sync'),
            'vault_count': len(self.supported_vaults),
            'supported_vaults': list(self.supported_vaults.keys())
        }
        
        # Count by type
        note_types = {}
        for note_data in self.sync_metadata.get('synced_notes', {}).values():
            note_type = note_data.get('type', 'unknown')
            note_types[note_type] = note_types.get(note_type, 0) + 1
        
        stats['notes_by_type'] = note_types
        stats['vault_stats'] = self.sync_metadata.get('vault_stats', {})
        
        return stats
    
    def _get_real_vault_count(self, link_suggestions: List[Dict]) -> int:
        """Count the number of real (non-test) vaults in suggestions"""
        vaults = set()
        for suggestion in link_suggestions:
            source_vault = suggestion.get('source_vault', '')
            target_vault = suggestion.get('target_vault', '')
            
            # Filter out test/performance data patterns
            if not self._is_fake_vault(source_vault):
                vaults.add(source_vault)
            if not self._is_fake_vault(target_vault):
                vaults.add(target_vault)
                
        return len(vaults)
    
    def _is_fake_vault(self, vault_name: str) -> bool:
        """Check if a vault name indicates test/performance data"""
        fake_patterns = [
            'project-0',  # Performance test projects
            'test-',      # Test vaults
            'temp',       # Temporary vaults
            'performance',
            'benchmark'
        ]
        
        vault_lower = vault_name.lower()
        return any(pattern in vault_lower for pattern in fake_patterns)
    
    def _filter_fake_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """Filter out suggestions that involve fake/test data"""
        real_suggestions = []
        
        for suggestion in suggestions:
            source_file = suggestion.get('source_file', '')
            target_file = suggestion.get('target_file', '')
            source_vault = suggestion.get('source_vault', '')
            target_vault = suggestion.get('target_vault', '')
            
            # Check for fake file patterns
            fake_file_patterns = [
                'category-',    # Performance test categories
                'file-',        # Performance test files
                'project-0'     # Performance test projects
            ]
            
            is_fake = False
            for pattern in fake_file_patterns:
                if (pattern in source_file or pattern in target_file or 
                    self._is_fake_vault(source_vault) or self._is_fake_vault(target_vault)):
                    is_fake = True
                    break
            
            if not is_fake:
                real_suggestions.append(suggestion)
            else:
                self.logger.debug(f"Filtered out fake suggestion: {source_file} -> {target_file}")
        
        return real_suggestions

# Main integration functions
async def integrate_with_obsidian(ai_insights: List[Dict], cross_vault_links: List[Dict], 
                                chat_data: Optional[Dict] = None, target_vault: str = "cortex") -> SyncResult:
    """Main integration function to sync Cortex results with Obsidian"""
    
    bridge = ObsidianMCPBridge()
    start_time = datetime.now()
    total_notes = 0
    total_links = 0
    all_errors = []
    
    try:
        # Sync AI insights
        for insight in ai_insights:
            success, result = await bridge.create_cortex_insight_note(insight, target_vault)
            if success:
                total_notes += 1
            else:
                all_errors.append(f"Insight sync failed: {result}")
        
        # Sync cross-vault links
        link_result = await bridge.sync_cross_vault_links(cross_vault_links, target_vault)
        total_notes += link_result.notes_created
        total_links += link_result.links_added
        all_errors.extend(link_result.errors)
        
        # Sync chat session if provided
        if chat_data:
            success, result = await bridge.sync_chat_session(chat_data, target_vault)
            if success:
                total_notes += 1
            else:
                all_errors.append(f"Chat sync failed: {result}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logging.info(f"Integration complete: {total_notes} notes, {total_links} links, {len(all_errors)} errors (took {execution_time:.2f}s)")
        
        return SyncResult(
            success=len(all_errors) == 0,
            notes_created=total_notes,
            links_added=total_links,
            errors=all_errors,
            execution_time=execution_time
        )
        
    except Exception as e:
        all_errors.append(str(e))
        logging.error(f"Error in Obsidian integration: {e}")
        return SyncResult(
            success=False,
            notes_created=total_notes,
            links_added=total_links,
            errors=all_errors,
            execution_time=(datetime.now() - start_time).total_seconds()
        )