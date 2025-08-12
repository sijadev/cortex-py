#!/usr/bin/env python3
"""
File Watcher for Real-time Obsidian Sync
Monitors Obsidian vault changes and triggers automatic AI analysis and sync
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

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logging.warning("Watchdog not available. Install with: pip install watchdog")

try:
    from watcher_config import is_file_watcher_enabled, get_watcher_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logging.warning("Watcher configuration not available")

@dataclass
class FileChangeEvent:
    """Represents a file change event"""
    event_type: str  # 'created', 'modified', 'deleted'
    file_path: str
    vault_name: str
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

class ObsidianFileWatcher:
    """Watches Obsidian vault files for changes and triggers sync operations"""
    
    def __init__(self, cortex_path: str, config: Optional[WatcherConfig] = None, enabled: bool = None):
        self.cortex_path = Path(cortex_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Check configuration file first, then use parameter, default to False
        if enabled is None and CONFIG_AVAILABLE:
            self.enabled = is_file_watcher_enabled()
        else:
            self.enabled = enabled if enabled is not None else False
        
        # Default configuration
        self.config = config or WatcherConfig(
            watch_patterns=['*.md', '*.txt'],
            ignore_patterns=['.*', '*.tmp', '*~', '*.log', '*/.obsidian/*'],
            debounce_seconds=2,
            batch_size=5,
            analysis_delay=10,
            max_file_size_mb=10
        )
        
        # State management
        self.watched_vaults: Dict[str, str] = {}
        self.observers: List[Observer] = []
        self.change_queue: asyncio.Queue = asyncio.Queue()
        self.pending_changes: Dict[str, FileChangeEvent] = {}
        self.last_analysis_time = datetime.now()
        self.is_running = False
        
        # Callbacks
        self.on_change_callback: Optional[Callable] = None
        self.on_analysis_trigger_callback: Optional[Callable] = None
        
        # Statistics
        self.stats = {
            'files_watched': 0,
            'changes_detected': 0,
            'analyses_triggered': 0,
            'sync_operations': 0,
            'last_change': None,
            'uptime_start': datetime.now()
        }
        
        if not self.enabled:
            self.logger.info("File watcher is disabled by configuration")
            return
        
        self._discover_vaults()
        
        if not WATCHDOG_AVAILABLE:
            self.logger.error("Watchdog library not available. File watching disabled.")
    
    def _discover_vaults(self):
        """Discover vaults to watch"""
        # Always watch the main cortex vault
        if self.cortex_path.exists():
            self.watched_vaults['cortex'] = str(self.cortex_path)
        
        # Look for other vaults in the cortex structure
        possible_vault_dirs = ['01-Projects', '03-Decisions', '04-Code-Fragments', '05-Insights']
        
        for vault_dir in possible_vault_dirs:
            vault_path = self.cortex_path / vault_dir
            if vault_path.exists() and vault_path.is_dir():
                self.watched_vaults[vault_dir] = str(vault_path)
        
        self.logger.info(f"Discovered {len(self.watched_vaults)} vaults to watch: {list(self.watched_vaults.keys())}")
    
    def set_change_callback(self, callback: Callable[[List[FileChangeEvent]], None]):
        """Set callback for file changes"""
        self.on_change_callback = callback
    
    def set_analysis_trigger_callback(self, callback: Callable[[List[FileChangeEvent]], None]):
        """Set callback for analysis triggers"""
        self.on_analysis_trigger_callback = callback
    
    async def start_watching(self):
        """Start watching vault files"""
        if not self.enabled:
            self.logger.info("File watcher is disabled, not starting")
            return False
            
        if not WATCHDOG_AVAILABLE:
            self.logger.error("Cannot start watching: watchdog library not available")
            return False
        
        try:
            self.is_running = True
            self.stats['uptime_start'] = datetime.now()
            
            # Start file system observers
            for vault_name, vault_path in self.watched_vaults.items():
                handler = VaultFileHandler(self, vault_name)
                observer = Observer()
                observer.schedule(handler, vault_path, recursive=True)
                observer.start()
                self.observers.append(observer)
                self.logger.info(f"Started watching vault: {vault_name} at {vault_path}")
            
            # Start change processing task
            asyncio.create_task(self._process_changes())
            
            # Start periodic analysis task
            asyncio.create_task(self._periodic_analysis())
            
            self.logger.info(f"File watcher started successfully. Watching {len(self.watched_vaults)} vaults.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting file watcher: {e}")
            await self.stop_watching()
            return False
    
    async def stop_watching(self):
        """Stop watching vault files"""
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
                    file_key = f"{change.vault_name}:{change.file_path}"
                    self.pending_changes[file_key] = change
                    
                    # Check if we should process pending changes
                    if len(self.pending_changes) >= self.config.batch_size:
                        await self._process_pending_changes()
                    
                except asyncio.TimeoutError:
                    # Process pending changes if any exist and debounce period has passed
                    if self.pending_changes:
                        oldest_change = min(
                            self.pending_changes.values(),
                            key=lambda c: c.timestamp
                        )
                        
                        change_time = datetime.fromisoformat(oldest_change.timestamp)
                        if (datetime.now() - change_time).total_seconds() >= self.config.debounce_seconds:
                            await self._process_pending_changes()
                    
            except Exception as e:
                self.logger.error(f"Error processing changes: {e}")
    
    async def _process_pending_changes(self):
        """Process all pending changes"""
        if not self.pending_changes:
            return
        
        changes = list(self.pending_changes.values())
        self.pending_changes.clear()
        
        self.logger.info(f"Processing {len(changes)} file changes")
        
        # Call change callback if set
        if self.on_change_callback:
            try:
                if asyncio.iscoroutinefunction(self.on_change_callback):
                    await self.on_change_callback(changes)
                else:
                    self.on_change_callback(changes)
            except Exception as e:
                self.logger.error(f"Error in change callback: {e}")
        
        # Update statistics
        self.stats['changes_detected'] += len(changes)
        self.stats['last_change'] = datetime.now().isoformat()
        
        # Check if we should trigger analysis
        await self._maybe_trigger_analysis(changes)
    
    async def _maybe_trigger_analysis(self, changes: List[FileChangeEvent]):
        """Determine if changes should trigger AI analysis"""
        now = datetime.now()
        time_since_last_analysis = (now - self.last_analysis_time).total_seconds()
        
        # Trigger analysis if:
        # 1. Enough time has passed since last analysis
        # 2. Significant number of markdown files changed
        # 3. Important files were modified
        
        should_trigger = False
        trigger_reason = ""
        
        if time_since_last_analysis >= self.config.analysis_delay:
            markdown_changes = [c for c in changes if c.is_markdown]
            
            if len(markdown_changes) >= 3:
                should_trigger = True
                trigger_reason = f"{len(markdown_changes)} markdown files changed"
            
            elif any(self._is_important_file(c.file_path) for c in changes):
                should_trigger = True
                trigger_reason = "Important file modified"
            
            elif len(changes) >= self.config.batch_size:
                should_trigger = True
                trigger_reason = f"Large batch of changes ({len(changes)} files)"
        
        if should_trigger:
            self.logger.info(f"Triggering AI analysis: {trigger_reason}")
            self.last_analysis_time = now
            self.stats['analyses_triggered'] += 1
            
            if self.on_analysis_trigger_callback:
                try:
                    if asyncio.iscoroutinefunction(self.on_analysis_trigger_callback):
                        await self.on_analysis_trigger_callback(changes)
                    else:
                        self.on_analysis_trigger_callback(changes)
                except Exception as e:
                    self.logger.error(f"Error in analysis trigger callback: {e}")
    
    async def _periodic_analysis(self):
        """Periodic analysis trigger for long-running operations"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Trigger analysis if it's been a while and we have any pending changes
                time_since_last = (datetime.now() - self.last_analysis_time).total_seconds()
                
                if time_since_last >= 1800:  # 30 minutes
                    self.logger.info("Triggering periodic analysis check")
                    self.stats['analyses_triggered'] += 1
                    
                    if self.on_analysis_trigger_callback:
                        try:
                            # Pass empty changes list for periodic trigger
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
            'specification'
        ]
        
        file_name = Path(file_path).name.lower()
        return any(pattern.lower() in file_name for pattern in important_patterns)
    
    def _should_watch_file(self, file_path: str) -> bool:
        """Check if a file should be watched"""
        path = Path(file_path)
        
        # Check file size
        try:
            if path.stat().st_size > self.config.max_file_size_mb * 1024 * 1024:
                return False
        except (OSError, FileNotFoundError):
            return False
        
        # Check patterns
        file_name = path.name
        
        # Check ignore patterns
        for ignore_pattern in self.config.ignore_patterns:
            if self._matches_pattern(file_name, ignore_pattern):
                return False
        
        # Check watch patterns
        for watch_pattern in self.config.watch_patterns:
            if self._matches_pattern(file_name, watch_pattern):
                return True
        
        return False
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching"""
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
            
            # Simple tag extraction (tags starting with #)
            import re
            tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
            return list(set(tags))  # Remove duplicates
            
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
            'vaults_watched': len(self.watched_vaults),
            'is_running': self.is_running,
            'pending_changes': len(self.pending_changes),
            'queue_size': self.change_queue.qsize()
        }

class VaultFileHandler(FileSystemEventHandler):
    """Handles file system events for a specific vault"""
    
    def __init__(self, watcher: ObsidianFileWatcher, vault_name: str):
        super().__init__()
        self.watcher = watcher
        self.vault_name = vault_name
        self.logger = logging.getLogger(f"{self.__class__.__name__}:{vault_name}")
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and self.watcher._should_watch_file(event.src_path):
            self._queue_change_event('modified', event.src_path)
    
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and self.watcher._should_watch_file(event.src_path):
            self._queue_change_event('created', event.src_path)
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory:
            # For deleted files, we can't check if we should watch them,
            # so we queue the event anyway
            self._queue_change_event('deleted', event.src_path)
    
    def _queue_change_event(self, event_type: str, file_path: str):
        """Queue a change event for processing"""
        try:
            is_markdown = file_path.lower().endswith('.md')
            file_hash = None
            tags = []
            
            if event_type != 'deleted':
                file_hash = self.watcher._calculate_file_hash(file_path)
                if is_markdown:
                    tags = self.watcher._extract_tags_from_content(file_path)
            
            change_event = FileChangeEvent(
                event_type=event_type,
                file_path=file_path,
                vault_name=self.vault_name,
                timestamp=datetime.now().isoformat(),
                file_hash=file_hash,
                is_markdown=is_markdown,
                tags_detected=tags
            )
            
            # Queue the event (non-blocking)
            try:
                self.watcher.change_queue.put_nowait(change_event)
                self.logger.debug(f"Queued {event_type} event for {file_path}")
            except asyncio.QueueFull:
                self.logger.warning(f"Change queue full, dropping event for {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error queuing change event for {file_path}: {e}")

class WatcherIntegration:
    """Integration between file watcher and Cortex AI system"""
    
    def __init__(self, cortex_path: str, enabled: bool = None):
        self.cortex_path = cortex_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.watcher = ObsidianFileWatcher(cortex_path, enabled=enabled)
        
        # Set up callbacks
        self.watcher.set_change_callback(self._on_file_changes)
        self.watcher.set_analysis_trigger_callback(self._on_analysis_trigger)
        
        # Integration state
        self.last_sync_time = datetime.now()
        self.sync_in_progress = False
    
    async def start(self):
        """Start the integrated watcher system"""
        success = await self.watcher.start_watching()
        if success:
            self.logger.info("Watcher integration started successfully")
        return success
    
    async def stop(self):
        """Stop the integrated watcher system"""
        await self.watcher.stop_watching()
        self.logger.info("Watcher integration stopped")
    
    async def _on_file_changes(self, changes: List[FileChangeEvent]):
        """Handle file change events"""
        self.logger.info(f"Processing {len(changes)} file changes")
        
        # Log interesting changes
        markdown_changes = [c for c in changes if c.is_markdown]
        if markdown_changes:
            self.logger.info(f"Markdown files changed: {[Path(c.file_path).name for c in markdown_changes[:5]]}")
        
        # Extract tags from changes
        all_tags = []
        for change in changes:
            if change.tags_detected:
                all_tags.extend(change.tags_detected)
        
        if all_tags:
            from collections import Counter
            tag_counts = Counter(all_tags)
            self.logger.info(f"Most common tags in changes: {dict(tag_counts.most_common(5))}")
    
    async def _on_analysis_trigger(self, changes: List[FileChangeEvent]):
        """Handle analysis trigger events"""
        if self.sync_in_progress:
            self.logger.info("Sync already in progress, skipping trigger")
            return
        
        try:
            self.sync_in_progress = True
            self.logger.info(f"Analysis triggered by {len(changes)} changes")
            
            # Import and run Cortex analysis
            await self._run_cortex_analysis(changes)
            
            # Trigger Obsidian sync
            await self._trigger_obsidian_sync()
            
            self.last_sync_time = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error in analysis trigger: {e}")
        finally:
            self.sync_in_progress = False
    
    async def _run_cortex_analysis(self, changes: List[FileChangeEvent]):
        """Run Cortex AI analysis on changed files"""
        try:
            # Import Cortex components
            from cross_vault_linker import CrossVaultLinker
            
            self.logger.info("Running Cortex AI analysis...")
            
            # Run cross-vault linking with Obsidian sync
            linker = CrossVaultLinker(cortex_hub_path=self.cortex_path)
            
            # Run async analysis
            report = await linker.run_full_linking_cycle_async(sync_to_obsidian=True)
            
            if report:
                self.logger.info(f"Analysis complete: {report['summary']}")
            else:
                self.logger.warning("Analysis failed")
                
        except ImportError as e:
            self.logger.error(f"Could not import Cortex components: {e}")
        except Exception as e:
            self.logger.error(f"Error running Cortex analysis: {e}")
    
    async def _trigger_obsidian_sync(self):
        """Trigger additional Obsidian sync operations"""
        try:
            from obsidian_mcp_bridge import ObsidianMCPBridge
            
            self.logger.info("Triggering additional Obsidian sync...")
            
            bridge = ObsidianMCPBridge(cortex_path=self.cortex_path)
            stats = bridge.get_sync_statistics()
            
            self.logger.info(f"Obsidian sync stats: {stats}")
            
        except Exception as e:
            self.logger.error(f"Error in Obsidian sync: {e}")
    
    def get_status(self) -> Dict:
        """Get integration status"""
        return {
            'watcher_running': self.watcher.is_running,
            'sync_in_progress': self.sync_in_progress,
            'last_sync_time': self.last_sync_time.isoformat(),
            'watcher_stats': self.watcher.get_statistics()
        }

# CLI interface for testing and management
async def main():
    """Main entry point for testing the file watcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cortex File Watcher for Obsidian Integration")
    parser.add_argument("--cortex-path", default="/Users/simonjanke/Projects/cortex", 
                       help="Path to Cortex hub")
    parser.add_argument("--test-mode", action="store_true", 
                       help="Run in test mode with verbose logging")
    parser.add_argument("--duration", type=int, default=60,
                       help="How long to run in seconds (test mode)")
    parser.add_argument("--enable-watcher", action="store_true",
                       help="Enable file watcher (disabled by default)")
    
    args = parser.parse_args()
    
    if args.test_mode:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    logger = logging.getLogger("FileWatcherCLI")
    
    if not WATCHDOG_AVAILABLE:
        logger.error("Watchdog library not available. Install with: pip install watchdog")
        return
    
    # Test the integration  
    enabled = args.enable_watcher if hasattr(args, 'enable_watcher') else None
    integration = WatcherIntegration(args.cortex_path, enabled=enabled)
    
    try:
        logger.info(f"Starting file watcher integration for: {args.cortex_path}")
        
        success = await integration.start()
        if not success:
            logger.error("Failed to start watcher integration")
            return
        
        if args.test_mode:
            logger.info(f"Running in test mode for {args.duration} seconds...")
            logger.info("Try modifying some .md files in the vault to see events")
            
            await asyncio.sleep(args.duration)
            
            # Print final statistics
            status = integration.get_status()
            logger.info(f"Final status: {json.dumps(status, indent=2, default=str)}")
        else:
            logger.info("Running continuously. Press Ctrl+C to stop.")
            
            # Run until interrupted
            while True:
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
    except Exception as e:
        logger.error(f"Error in file watcher: {e}")
    finally:
        await integration.stop()

if __name__ == "__main__":
    if not WATCHDOG_AVAILABLE:
        print("Error: watchdog library not available.")
        print("Install with: pip install watchdog")
        exit(1)
    
    asyncio.run(main())