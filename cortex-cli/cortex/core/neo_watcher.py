#!/usr/bin/env python3
"""
Neo Watcher for Real-time Obsidian Sync - Cortex CLI Edition
Monitors workspace changes and triggers automatic AI analysis and sync
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

try:
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    class FileSystemEventHandler:
        pass
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
class NeoWatcherConfig:
    """Configuration for the neo watcher"""
    watch_patterns: List[str]  # File patterns to watch
    ignore_patterns: List[str]  # Patterns to ignore
    debounce_seconds: int  # Debounce delay for rapid changes
    batch_size: int  # Number of changes to batch before processing
    analysis_delay: int  # Delay before triggering AI analysis
    max_file_size_mb: int  # Maximum file size to process

class WorkspaceNeoHandler(FileSystemEventHandler):
    """Handler for file system events in workspace areas (NeoWatcher)"""
    # ...existing code...

class WorkspaceNeoWatcher:
    """Main watcher for workspace areas (NeoWatcher)"""
    def __init__(self, workspace_path: str = None, config: NeoWatcherConfig = None, enabled: bool = True):
        self.workspace_path = workspace_path
        self.config = config
        self.enabled = enabled
    # ...existing code...
