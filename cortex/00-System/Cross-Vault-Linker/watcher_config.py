#!/usr/bin/env python3
"""
Configuration file for Cortex File Watcher
Controls whether the file watcher is enabled or disabled globally
"""

# Global file watcher settings
FILE_WATCHER_ENABLED = False  # Set to True to enable file watching

# Watcher configuration options
WATCHER_CONFIG = {
    'enabled': FILE_WATCHER_ENABLED,
    'watch_patterns': ['*.md', '*.txt'],
    'ignore_patterns': ['.*', '*.tmp', '*~', '*.log', '*/.obsidian/*'],
    'debounce_seconds': 2,
    'batch_size': 5,
    'analysis_delay': 10,
    'max_file_size_mb': 10
}

def is_file_watcher_enabled() -> bool:
    """Check if file watcher is enabled"""
    return FILE_WATCHER_ENABLED

def get_watcher_config() -> dict:
    """Get the current watcher configuration"""
    return WATCHER_CONFIG.copy()

def enable_file_watcher():
    """Enable file watcher"""
    global FILE_WATCHER_ENABLED
    FILE_WATCHER_ENABLED = True
    WATCHER_CONFIG['enabled'] = True

def disable_file_watcher():
    """Disable file watcher"""
    global FILE_WATCHER_ENABLED
    FILE_WATCHER_ENABLED = False
    WATCHER_CONFIG['enabled'] = False