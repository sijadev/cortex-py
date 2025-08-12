"""
Cortex CLI Package
AI-powered knowledge management and cross-vault linking tool
"""

__version__ = "0.2.0"
__author__ = "Simon Janke"
__email__ = "simon@sijadev.com"

from .core import ai_engine, cross_vault_linker
from .utils import yaml_utils, file_utils

__all__ = [
    "ai_engine",
    "cross_vault_linker", 
    "yaml_utils",
    "file_utils"
]
