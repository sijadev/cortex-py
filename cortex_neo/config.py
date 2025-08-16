from __future__ import annotations
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    uri: str
    user: str
    password: str
    verbose: bool = False

    @classmethod
    def from_env(cls, verbose: bool = False) -> "Settings":
        return cls(
            uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            user=os.environ.get("NEO4J_USER", "neo4j"),
            password=os.environ.get("NEO4J_PASSWORD", "neo4jtest"),
            verbose=verbose,
        )

