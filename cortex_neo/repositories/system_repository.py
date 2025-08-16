from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
try:
    from ..infra.neo4j_client import Neo4jClient
except ImportError:  # Support running without package context
    from infra.neo4j_client import Neo4jClient  # type: ignore


@dataclass
class SystemRepository:
    client: Neo4jClient

    def connection_ok(self) -> bool:
        try:
            with self.client.session() as session:
                session.run("RETURN 1 AS ok").single()
            return True
        except Exception:
            return False

    def server_time(self) -> int:
        with self.client.session() as session:
            rec = session.run("RETURN timestamp() AS time").single()
            return int(rec["time"]) if rec else 0

    def quick_stats(self) -> Dict[str, int]:
        query = (
            "MATCH (n:Note) "
            "OPTIONAL MATCH (w:Workflow) "
            "OPTIONAL MATCH (t:Tag) "
            "OPTIONAL MATCH ()-[r:LINKS_TO]->() "
            "OPTIONAL MATCH (template:Template) "
            "RETURN count(DISTINCT n) as notes, "
            "       count(DISTINCT w) as workflows, "
            "       count(DISTINCT t) as tags, "
            "       count(r) as links, "
            "       count(DISTINCT template) as templates"
        )
        with self.client.session() as session:
            rec = session.run(query).single()
            return {
                "notes": rec["notes"],
                "workflows": rec["workflows"],
                "tags": rec["tags"],
                "links": rec["links"],
                "templates": rec["templates"],
            }

    def integrity(self) -> Dict[str, int]:
        query = (
            "MATCH (n:Note) "
            "OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag) "
            "OPTIONAL MATCH (n)-[r:LINKS_TO]->() "
            "RETURN count(n) as total_notes, "
            "       count(t) as tagged_notes, "
            "       count(r) as linked_notes"
        )
        with self.client.session() as session:
            rec = session.run(query).single()
            return {
                "total_notes": rec["total_notes"],
                "tagged_notes": rec["tagged_notes"],
                "linked_notes": rec["linked_notes"],
            }
