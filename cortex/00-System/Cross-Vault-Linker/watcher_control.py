#!/usr/bin/env python3
"""
File Watcher Control Tool
Simple CLI to enable/disable the Cortex file watcher
"""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Control Cortex File Watcher")
    parser.add_argument('action', choices=['status', 'enable', 'disable'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    try:
        from watcher_config import (
            is_file_watcher_enabled, 
            enable_file_watcher, 
            disable_file_watcher
        )
    except ImportError:
        print("Error: watcher_config.py not found")
        sys.exit(1)
    
    if args.action == 'status':
        status = "enabled" if is_file_watcher_enabled() else "disabled"
        print(f"File watcher is currently: {status}")
    
    elif args.action == 'enable':
        enable_file_watcher()
        print("File watcher has been enabled")
        print("Note: This change only affects new instances. Restart any running processes.")
    
    elif args.action == 'disable':
        disable_file_watcher()
        print("File watcher has been disabled")
        print("Note: This change only affects new instances. Restart any running processes.")

if __name__ == "__main__":
    main()