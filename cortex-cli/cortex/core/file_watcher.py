#!/usr/bin/env python3
"""
File Watcher for Real-time Obsidian Sync - Cortex CLI Edition
Monitors workspace changes and triggers automatic AI analysis and sync
"""

import asyncio
import logging
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import re

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logging.warning("Watchdog not available. Install with: pip install watchdog")

@dataclass
class FileChangeEvent:
    """Represents a file change event"""
    event_type: str  # 'created', 'modified', 'deleted'
    file_path: str
    workspace_area: str  # Instead of vault_name
    timestamp: str
    file_hash: Optional[str] = None
    is_markdown: bool = False
    tags_detected: List[str] = None

@dataclass
class WatcherConfig:
    """Configuration for the file watcher"""
    watch_patterns: List[str]  # File patterns to watch
    ignore_patterns: List[str]  # Patterns to ignore
    debounce_seconds: int  # Debounce delay for rapid changes
    batch_size: int  # Number of changes to batch before processing
    analysis_delay: int  # Delay before triggering AI analysis
    max_file_size_mb: int  # Maximum file size to process

class WorkspaceFileHandler(FileSystemEventHandler):
    """Handler for file system events in workspace areas"""
    
    def __init__(self, watcher: 'WorkspaceFileWatcher', area_name: str):
        self.watcher = watcher
        self.area_name = area_name
        self.logger = logging.getLogger(f'FileHandler.{area_name}')
    
    def on_created(self, event):
        if not event.is_directory:
            self._handle_file_event('created', event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file_event('modified', event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._handle_file_event('deleted', event.src_path)
    
    def _handle_file_event(self, event_type: str, file_path: str):
        """Handle a file system event"""
        if not self.watcher._should_watch_file(file_path):
            return
        
        try:
            # Create file change event
            file_hash = None
            tags = []
            is_markdown = file_path.lower().endswith('.md')
            
            if event_type != 'deleted' and is_markdown:
                file_hash = self.watcher._calculate_file_hash(file_path)
                tags = self.watcher._extract_tags_from_content(file_path)
            
            change_event = FileChangeEvent(
                event_type=event_type,
                file_path=file_path,
                workspace_area=self.area_name,
                timestamp=datetime.now().isoformat(),
                file_hash=file_hash,
                is_markdown=is_markdown,
                tags_detected=tags
            )
            
            # Queue the event for processing
            asyncio.run_coroutine_threadsafe(
                self.watcher.change_queue.put(change_event),
                self.watcher.loop
            )
            
            # Update statistics
            self.watcher.stats['changes_detected'] += 1
            self.watcher.stats['last_change'] = datetime.now().isoformat()
            
            self.logger.debug(f"{event_type}: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error handling file event {event_type} for {file_path}: {e}")

class WorkspaceFileWatcher:
    """Watches workspace files for changes and triggers sync operations"""
    
    def __init__(self, workspace_path: str = None, config: Optional[WatcherConfig] = None, enabled: bool = True):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = enabled
        
        # Default configuration
        self.config = config or WatcherConfig(
            watch_patterns=['*.md', '*.txt', '*.py', '*.yaml', '*.yml', '*.json'],
            ignore_patterns=['.*', '*.tmp', '*~', '*.log', '*/__pycache__/*', '*/.venv/*', '*/.git/*'],
            debounce_seconds=2,
            batch_size=5,
            analysis_delay=10,
            max_file_size_mb=10
        )
        
        # State management
        self.watched_areas: Dict[str, str] = {}
        self.observers: List = []
        self.change_queue: asyncio.Queue = asyncio.Queue()
        self.pending_changes: Dict[str, FileChangeEvent] = {}
        self.last_analysis_time = datetime.now()
        self.is_running = False
        self.loop = None
        
        # Callbacks
        self.on_change_callback: Optional[Callable] = None
        self.on_analysis_trigger_callback: Optional[Callable] = None
        
        # Statistics
        self.stats = {
            'areas_watched': 0,
            'changes_detected': 0,
            'analyses_triggered': 0,
            'sync_operations': 0,
            'last_change': None,
            'uptime_start': datetime.now()
        }
        
        if not self.enabled:
            self.logger.info("File watcher is disabled")
            # Still discover areas for status reporting
            self._discover_workspace_areas()
            return
        
        self._discover_workspace_areas()
        
        if not WATCHDOG_AVAILABLE:
            self.logger.error("Watchdog library not available. File watching disabled.")
            self.enabled = False
    
    def _discover_workspace_areas(self):
        """Discover workspace areas to watch"""
        # Always watch the main workspace
        if self.workspace_path.exists():
            self.watched_areas['workspace'] = str(self.workspace_path)
        
        # Look for specific workspace areas
        possible_areas = [
            '00-System', '00-Templates', '01-Projects', '02-Neural-Links', 
            '03-Decisions', '04-Code-Fragments', '05-Insights', '07-Reports', '08-Docs'
        ]
        
        for area_name in possible_areas:
            area_path = self.workspace_path / area_name
            if area_path.exists() and area_path.is_dir():
                self.watched_areas[area_name] = str(area_path)
        
        # Also watch CLI directory if it exists
        cli_path = self.workspace_path / 'cortex-cli'
        if cli_path.exists():
            self.watched_areas['cortex-cli'] = str(cli_path)
        
        self.stats['areas_watched'] = len(self.watched_areas)
        self.logger.info(f"Discovered {len(self.watched_areas)} areas to watch: {list(self.watched_areas.keys())}")
    
    def set_change_callback(self, callback: Callable[[List[FileChangeEvent]], None]):
        """Set callback for file changes"""
        self.on_change_callback = callback
    
    def set_analysis_trigger_callback(self, callback: Callable[[List[FileChangeEvent]], None]):
        """Set callback for analysis triggers"""
        self.on_analysis_trigger_callback = callback
    
    async def start_watching(self):
        """Start watching workspace files"""
        if not self.enabled:
            self.logger.info("File watcher is disabled, not starting")
            return False
            
        if not WATCHDOG_AVAILABLE:
            self.logger.error("Cannot start watching: watchdog library not available")
            return False
        
        try:
            self.is_running = True
            self.loop = asyncio.get_event_loop()
            self.stats['uptime_start'] = datetime.now()
            
            # Start file system observers
            for area_name, area_path in self.watched_areas.items():
                handler = WorkspaceFileHandler(self, area_name)
                observer = Observer()
                observer.schedule(handler, area_path, recursive=True)
                observer.start()
                self.observers.append(observer)
                self.logger.info(f"Started watching area: {area_name} at {area_path}")
            
            # Start change processing task
            asyncio.create_task(self._process_changes())
            
            # Start periodic analysis task
            asyncio.create_task(self._periodic_analysis())
            
            self.logger.info(f"File watcher started successfully. Watching {len(self.watched_areas)} areas.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting file watcher: {e}")
            await self.stop_watching()
            return False
    
    async def stop_watching(self):
        """Stop watching workspace files"""
        self.is_running = False
        
        # Stop all observers
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        self.observers.clear()
        self.logger.info("File watcher stopped")
    
    async def _process_changes(self):
        """Process queued file changes"""
        while self.is_running:
            try:
                # Wait for changes or timeout
                try:
                    change = await asyncio.wait_for(
                        self.change_queue.get(), 
                        timeout=1.0
                    )
                    
                    # Add to pending changes (debouncing)
                    file_key = f"{change.workspace_area}:{change.file_path}"
                    self.pending_changes[file_key] = change
                    
                    # Check if we should process pending changes
                    if len(self.pending_changes) >= self.config.batch_size:
                        await self._process_pending_changes()
                    
                except asyncio.TimeoutError:
                    # Process pending changes even on timeout (debounce)
                    if self.pending_changes:
                        await self._process_pending_changes()
                    
            except Exception as e:
                self.logger.error(f"Error in change processing: {e}")
                await asyncio.sleep(1)  # Avoid tight error loop
    
    async def _process_pending_changes(self):
        """Process batched pending changes"""
        if not self.pending_changes:
            return
        
        changes = list(self.pending_changes.values())
        self.pending_changes.clear()
        
        self.logger.info(f"Processing {len(changes)} file changes")
        
        # Trigger change callback
        if self.on_change_callback:
            try:
                if asyncio.iscoroutinefunction(self.on_change_callback):
                    await self.on_change_callback(changes)
                else:
                    self.on_change_callback(changes)
            except Exception as e:
                self.logger.error(f"Error in change callback: {e}")
        
        # Check if we should trigger analysis
        important_changes = [c for c in changes if self._is_important_file(c.file_path)]
        
        if important_changes:
            await self._trigger_analysis(important_changes)
    
    async def _trigger_analysis(self, changes: List[FileChangeEvent]):
        """Trigger AI analysis for important changes"""
        self.stats['analyses_triggered'] += 1
        self.logger.info(f"Triggering analysis for {len(changes)} important changes")
        
        if self.on_analysis_trigger_callback:
            try:
                if asyncio.iscoroutinefunction(self.on_analysis_trigger_callback):
                    await self.on_analysis_trigger_callback(changes)
                else:
                    self.on_analysis_trigger_callback(changes)
            except Exception as e:
                self.logger.error(f"Error in analysis trigger callback: {e}")
    
    async def _periodic_analysis(self):
        """Trigger periodic analysis based on configuration"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.analysis_delay)
                
                # Check if enough time has passed since last analysis
                time_since_analysis = (datetime.now() - self.last_analysis_time).total_seconds()
                
                if time_since_analysis >= self.config.analysis_delay:
                    self.logger.debug("Triggering periodic analysis")
                    
                    if self.on_analysis_trigger_callback:
                        try:
                            if asyncio.iscoroutinefunction(self.on_analysis_trigger_callback):
                                await self.on_analysis_trigger_callback([])
                            else:
                                self.on_analysis_trigger_callback([])
                        except Exception as e:
                            self.logger.error(f"Error in periodic analysis trigger: {e}")
                    
                    self.last_analysis_time = datetime.now()
                    
            except Exception as e:
                self.logger.error(f"Error in periodic analysis: {e}")
    
    def _is_important_file(self, file_path: str) -> bool:
        """Check if a file is considered important for triggering analysis"""
        important_patterns = [
            'ADR-',  # Architecture Decision Records
            'README',
            'index.md',
            'overview.md',
            'architecture',
            'design',
            'specification',
            'cortex',  # Cortex-specific files
            'neural-link',
            'decision',
            'pattern'
        ]
        
        file_name = Path(file_path).name.lower()
        return any(pattern.lower() in file_name for pattern in important_patterns)
    
    def _should_watch_file(self, file_path: str) -> bool:
        """Check if a file should be watched"""
        path = Path(file_path)
        
        # Check file size
        try:
            if path.exists() and path.stat().st_size > self.config.max_file_size_mb * 1024 * 1024:
                return False
        except (OSError, FileNotFoundError):
            return False
        
        # Check patterns
        file_name = path.name
        file_path_str = str(path)
        
        # Check ignore patterns
        for ignore_pattern in self.config.ignore_patterns:
            if self._matches_pattern(file_name, ignore_pattern) or self._matches_pattern(file_path_str, ignore_pattern):
                return False
        
        # Check watch patterns
        for watch_pattern in self.config.watch_patterns:
            if self._matches_pattern(file_name, watch_pattern):
                return True
        
        return False
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching with basic wildcards"""
        if '*' not in pattern:
            return pattern in filename
        
        # Simple wildcard matching
        if pattern.startswith('*') and pattern.endswith('*'):
            return pattern[1:-1] in filename
        elif pattern.startswith('*'):
            return filename.endswith(pattern[1:])
        elif pattern.endswith('*'):
            return filename.startswith(pattern[:-1])
        else:
            return filename == pattern
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            self.logger.warning(f"Could not calculate hash for {file_path}: {e}")
            return None
    
    def _extract_tags_from_content(self, file_path: str) -> List[str]:
        """Extract tags from markdown content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract hashtags (#tag)
            hashtags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
            
            # Extract YAML frontmatter tags
            yaml_tags = []
            if content.startswith('---'):
                try:
                    yaml_end = content.find('---', 3)
                    if yaml_end != -1:
                        yaml_content = content[3:yaml_end]
                        # Simple tag extraction from YAML (tags: [tag1, tag2])
                        tag_matches = re.findall(r'tags:\s*\[(.*?)\]', yaml_content, re.MULTILINE)
                        for match in tag_matches:
                            yaml_tags.extend([tag.strip().strip('"\'') for tag in match.split(',')])
                except Exception:
                    pass
            
            return list(set(hashtags + yaml_tags))  # Remove duplicates
            
        except Exception as e:
            self.logger.warning(f"Could not extract tags from {file_path}: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get watcher statistics"""
        uptime = (datetime.now() - self.stats['uptime_start']).total_seconds()
        
        return {
            **self.stats,
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'is_running': self.is_running,
            'areas_configured': list(self.watched_areas.keys()),
            'config': asdict(self.config)
        }
    
    def get_recent_changes(self, limit: int = 10) -> List[Dict]:
        """Get recent file changes"""
        # This would be implemented with a proper change history
        # For now, return empty list
        return []
    
    async def trigger_manual_analysis(self):
        """Manually trigger analysis"""
        if not self.is_running:
            self.logger.warning("Cannot trigger manual analysis: watcher not running")
            return False
        
        try:
            self.logger.info("Manually triggering analysis")
            
            if self.on_analysis_trigger_callback:
                if asyncio.iscoroutinefunction(self.on_analysis_trigger_callback):
                    await self.on_analysis_trigger_callback([])
                else:
                    self.on_analysis_trigger_callback([])
            
            self.stats['analyses_triggered'] += 1
            self.last_analysis_time = datetime.now()
            return True
            
        except Exception as e:
            self.logger.error(f"Error in manual analysis trigger: {e}")
            return False
    
    def update_config(self, new_config: WatcherConfig):
        """Update watcher configuration"""
        self.config = new_config
        self.logger.info("Watcher configuration updated")
        
        # If running, restart with new config
        if self.is_running:
            self.logger.info("Restarting watcher with new configuration")
            # This would require a restart mechanism
    
    def add_watch_area(self, area_name: str, area_path: str):
        """Add a new area to watch"""
        if area_name not in self.watched_areas:
            self.watched_areas[area_name] = area_path
            self.stats['areas_watched'] = len(self.watched_areas)
            self.logger.info(f"Added watch area: {area_name} at {area_path}")
            
            # If already running, start watching the new area
            if self.is_running and WATCHDOG_AVAILABLE:
                try:
                    handler = WorkspaceFileHandler(self, area_name)
                    observer = Observer()
                    observer.schedule(handler, area_path, recursive=True)
                    observer.start()
                    self.observers.append(observer)
                    self.logger.info(f"Started watching new area: {area_name}")
                except Exception as e:
                    self.logger.error(f"Error adding watch area {area_name}: {e}")
    
    def remove_watch_area(self, area_name: str):
        """Remove an area from watching"""
        if area_name in self.watched_areas:
            del self.watched_areas[area_name]
            self.stats['areas_watched'] = len(self.watched_areas)
            self.logger.info(f"Removed watch area: {area_name}")
            
            # If running, would need to stop the specific observer
            # This requires tracking observer-to-area mapping
