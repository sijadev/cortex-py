from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator, Optional
from neo4j import GraphDatabase, Driver, Session
try:
    from ..config import Settings
except ImportError:  # Support running without package context
    from config import Settings  # type: ignore


class Neo4jClient:
    """Thin wrapper around neo4j.Driver with simple lifecycle management."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._driver: Optional[Driver] = None

    def get_driver(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self._settings.uri,
                auth=(self._settings.user, self._settings.password),
            )
        return self._driver

    @contextmanager
    def session(self) -> Iterator[Session]:
        sess = self.get_driver().session()
        try:
            yield sess
        finally:
            sess.close()

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None
