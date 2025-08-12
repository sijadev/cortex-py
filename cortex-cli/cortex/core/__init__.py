"""
Core modules for Cortex CLI.

Expose symbols via lazy imports to avoid importing optional dependencies
on package import.
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
    "CortexAIEngine",
    "CrossVaultLinker",
    "storage_provider",
]


def __getattr__(name: str) -> Any:  # PEP 562 lazy imports
    if name == "CortexAIEngine":
        return getattr(
            importlib.import_module(".ai_engine", __name__), "CortexAIEngine"
        )
    if name == "CrossVaultLinker":
        return getattr(
            importlib.import_module(".cross_vault_linker", __name__),
            "CrossVaultLinker",
        )
    if name == "storage_provider":
        return importlib.import_module(".storage_provider", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
