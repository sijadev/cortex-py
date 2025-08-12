#!/usr/bin/env python3
"""
File utilities for Cortex CLI
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if necessary"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def find_files(directory: Path, pattern: str, recursive: bool = True) -> List[Path]:
    """Find files matching pattern"""
    directory = Path(directory)
    
    if not directory.exists():
        return []
    
    if recursive:
        return list(directory.rglob(pattern))
    else:
        return list(directory.glob(pattern))

def copy_file_safely(source: Path, destination: Path) -> bool:
    """Safely copy file with error handling"""
    try:
        source = Path(source)
        destination = Path(destination)
        
        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source, destination)
        logger.info("Copied %s to %s", str(source), str(destination))
        return True
        
    except Exception as e:
        logger.error("Error copying file: %s", str(e))
        return False

def read_file_safely(file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
    """Safely read file content"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.warning("Could not read file %s: %s", str(file_path), str(e))
        return None

def write_file_safely(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """Safely write content to file"""
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        logger.info("Written content to %s", str(file_path))
        return True
        
    except Exception as e:
        logger.error("Error writing file %s: %s", str(file_path), str(e))
        return False

def get_file_stats(file_path: Path) -> dict:
    """Get file statistics"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {}
    
    stat = file_path.stat()
    
    return {
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "created": stat.st_ctime,
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
        "name": file_path.name,
        "extension": file_path.suffix
    }

def clean_directory(directory: Path, keep_patterns: List[str] = None) -> int:
    """Clean directory, optionally keeping files matching patterns"""
    directory = Path(directory)
    
    if not directory.exists():
        return 0
    
    keep_patterns = keep_patterns or []
    removed_count = 0
    
    for item in directory.iterdir():
        should_keep = False
        
        for pattern in keep_patterns:
            if item.match(pattern):
                should_keep = True
                break
        
        if not should_keep:
            try:
                if item.is_file():
                    item.unlink()
                    removed_count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    removed_count += 1
            except Exception as e:
                logger.warning("Could not remove %s: %s", str(item), str(e))
    
    return removed_count

def create_workspace_structure(workspace_path: Path) -> bool:
    """Create standard Cortex workspace structure"""
    workspace_path = Path(workspace_path)
    
    directories = [
        ".cortex",
        ".cortex/data",
        ".cortex/cache", 
        ".cortex/logs",
        ".cortex/templates",
        "projects",
        "docs",
        "notes"
    ]
    
    try:
        for directory in directories:
            (workspace_path / directory).mkdir(parents=True, exist_ok=True)
        
        # Create basic config file
        config_content = """# Cortex Workspace Configuration
ai_engine:
  enabled: true
  analysis_depth: standard
  
cross_vault_linker:
  enabled: true
  auto_link: false
  
scheduler:
  enabled: false
"""
        
        config_file = workspace_path / ".cortex" / "config.yaml"
        if not config_file.exists():
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
        
        # Create README
        readme_content = f"""# Cortex Workspace

This is a Cortex AI-powered knowledge workspace.

## Structure

- `.cortex/` - Cortex system files and configuration
- `projects/` - Your projects and research
- `docs/` - Documentation
- `notes/` - General notes and observations

## Getting Started

Run `cortex status` to see workspace information.
Run `cortex detect-gaps` to analyze knowledge gaps.
Run `cortex link-vaults` to find cross-references.

Created: {workspace_path.name}
"""
        
        readme_file = workspace_path / "README.md"
        if not readme_file.exists():
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
        
        logger.info("Created Cortex workspace at %s", str(workspace_path))
        return True
        
    except Exception as e:
        logger.error("Error creating workspace: %s", str(e))
        return False
