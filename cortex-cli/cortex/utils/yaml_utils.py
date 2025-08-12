#!/usr/bin/env python3
"""
Cortex YAML Utilities - CLI version
Safe YAML functions for the Cortex CLI package
"""

import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def is_valid_yaml_file(file_path):
    """
    Check if a file is actually a valid YAML file
    
    Args:
        file_path: Path to file to check
        
    Returns:
        bool: True if file is valid YAML
    """
    file_path = Path(file_path)
    
    # 1. Ignore virtual environment and package files
    if '.venv' in str(file_path) or 'site-packages' in str(file_path):
        return False
    
    # 2. Check file extension
    if file_path.suffix.lower() not in ['.yaml', '.yml']:
        return False
    
    # 3. Check if file exists
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Empty files are not YAML
        if not content:
            return False
            
        # Files that start with certain patterns are not YAML
        non_yaml_patterns = [
            'Metadata-Version:',
            'Name:',
            'Version:',
            'Summary:',
            'Author:',
            'License:',
            'Location:',
            '<!DOCTYPE html>',
            '<html',
            'pass',  # Simple Python pass statements
            'return',  # Function returns
        ]
        
        for pattern in non_yaml_patterns:
            if content.startswith(pattern):
                return False
        
        # Try to parse as YAML
        yaml.safe_load(content)
        return True
        
    except (yaml.YAMLError, UnicodeDecodeError, Exception):
        return False

def safe_load_yaml(file_path):
    """
    Safely load YAML file with validation
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        dict: Parsed YAML data or empty dict if invalid
    """
    if not is_valid_yaml_file(file_path):
        logger.warning("Skipping invalid YAML file: %s", str(file_path))
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            return {}
            
        return data
        
    except Exception as e:
        logger.error("Error loading YAML file %s: %s", str(file_path), str(e))
        return {}

def safe_dump_yaml(data, file_path, **kwargs):
    """
    Safely dump data to YAML file
    
    Args:
        data: Data to dump
        file_path: Target file path
        **kwargs: Additional yaml.dump arguments
    """
    file_path = Path(file_path)
    
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, **kwargs)
        logger.info("Successfully saved YAML to %s", str(file_path))
        
    except Exception as e:
        logger.error("Error saving YAML file %s: %s", str(file_path), str(e))
        raise

def load_yaml_config(config_path, default_config=None):
    """
    Load YAML configuration with defaults
    
    Args:
        config_path: Path to config file
        default_config: Default configuration dict
        
    Returns:
        dict: Merged configuration
    """
    if default_config is None:
        default_config = {}
    
    config = default_config.copy()
    
    if Path(config_path).exists():
        user_config = safe_load_yaml(config_path)
        if isinstance(user_config, dict):
            config.update(user_config)
    
    return config

def validate_yaml_schema(data, required_fields):
    """
    Validate YAML data against required schema
    
    Args:
        data: Parsed YAML data
        required_fields: List of required field names
        
    Returns:
        tuple: (is_valid, missing_fields)
    """
    if not isinstance(data, dict):
        return False, ["Data is not a dictionary"]
    
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    return len(missing_fields) == 0, missing_fields

def find_yaml_files(directory, recursive=True):
    """
    Find all valid YAML files in directory
    
    Args:
        directory: Directory to search
        recursive: Search recursively
        
    Returns:
        list: List of valid YAML file paths
    """
    directory = Path(directory)
    
    if not directory.exists():
        return []
    
    pattern = "**/*.y*ml" if recursive else "*.y*ml"
    yaml_files = []
    
    for file_path in directory.glob(pattern):
        if is_valid_yaml_file(file_path):
            yaml_files.append(file_path)
    
    return yaml_files

def merge_yaml_configs(*config_paths):
    """
    Merge multiple YAML configuration files
    
    Args:
        *config_paths: Paths to YAML config files
        
    Returns:
        dict: Merged configuration
    """
    merged_config = {}
    
    for config_path in config_paths:
        config = safe_load_yaml(config_path)
        if isinstance(config, dict):
            deep_merge(merged_config, config)
    
    return merged_config

def deep_merge(dict1, dict2):
    """
    Deep merge two dictionaries
    
    Args:
        dict1: Target dictionary (modified in place)
        dict2: Source dictionary
    """
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
            deep_merge(dict1[key], value)
        else:
            dict1[key] = value

# Convenience functions for common Cortex configurations
def load_cortex_config(workspace_path):
    """Load Cortex-specific configuration"""
    workspace_path = Path(workspace_path)
    
    default_config = {
        "ai_engine": {
            "enabled": True,
            "analysis_depth": "standard",
            "cache_duration": 24
        },
        "cross_vault_linker": {
            "enabled": True,
            "auto_link": False,
            "confidence_threshold": 0.7
        },
        "scheduler": {
            "enabled": False,
            "default_interval": "1h"
        }
    }
    
    config_file = workspace_path / ".cortex" / "config.yaml"
    return load_yaml_config(config_file, default_config)
