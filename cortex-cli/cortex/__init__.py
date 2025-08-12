"""
Cortex CLI Package
AI-powered knowledge management and cross-vault linking tool.

This package exposes common submodules via lazy attribute access to
avoid importing heavy optional dependencies at package import time.
"""

from __future__ import annotations

import importlib
from typing import Any

__version__ = "0.2.0"
__author__ = "Simon Janke"
__email__ = "simon@sijadev.com"

__all__ = [
    "ai_engine",
    "cross_vault_linker",
    "yaml_utils",
    "file_utils",
]


def __getattr__(name: str) -> Any:  # PEP 562 lazy imports
    if name == "ai_engine":
        return importlib.import_module(".core.ai_engine", __name__)
    if name == "cross_vault_linker":
        return importlib.import_module(".core.cross_vault_linker", __name__)
    if name == "yaml_utils":
        return importlib.import_module(".utils.yaml_utils", __name__)
    if name == "file_utils":
        return importlib.import_module(".utils.file_utils", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
