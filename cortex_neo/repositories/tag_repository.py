from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
try:
    from ..infra.neo4j_client import Neo4jClient
except ImportError:  # Support running without package context
    from infra.neo4j_client import Neo4jClient  # type: ignore


@dataclass
class TagRepository:
    client: Neo4jClient

    def add_tag(self, note_name: str, tag_name: str) -> None:
        with self.client.session() as session:
            session.run(
                """
                MATCH (n:Note {name: $note_name})
                MERGE (t:Tag {name: $tag_name})
                ON CREATE SET t.created_at = timestamp()
                MERGE (n)-[:TAGGED_WITH]->(t)
                """,
                note_name=note_name,
                tag_name=tag_name,
            )

    def list_tags_with_usage(self) -> List[Dict[str, Any]]:
        cypher = (
            """
            MATCH (t:Tag)
            OPTIONAL MATCH (n:Note)-[:TAGGED_WITH]->(t)
            RETURN t.name as name,
                   t.description as description,
                   t.category as category,
                   count(n) as usage_count,
                   t.created_at as created_at
            ORDER BY t.category, usage_count DESC, t.name
            """
        )
        with self.client.session() as session:
            return [
                {
                    "name": r["name"],
                    "description": r["description"],
                    "category": r["category"],
                    "usage_count": r["usage_count"],
                    "created_at": r["created_at"],
                }
                for r in session.run(cypher)
            ]

    def get_tag_details(self, tag_name: str) -> Optional[Dict[str, Any]]:
        cypher = (
            """
            MATCH (t:Tag {name: $tag_name})
            OPTIONAL MATCH (n:Note)-[:TAGGED_WITH]->(t)
            RETURN t as tag, collect(n) as notes, count(n) as usage_count
            """
        )
        with self.client.session() as session:
            rec = session.run(cypher, tag_name=tag_name).single()
            if not rec:
                return None
            return {
                "tag": rec["tag"],
                "notes": [n for n in rec["notes"] if n],
                "usage_count": rec["usage_count"],
            }

    def create_performance_tags(self) -> List[Dict[str, str]]:
        performance_tags = [
            {"name": "performance-metrics", "description": "Performance measurements and KPIs", "category": "performance"},
            {"name": "system-optimization", "description": "System performance improvements", "category": "performance"},
            {"name": "command-tracking", "description": "CLI command execution monitoring", "category": "performance"},
            {"name": "benchmarking", "description": "Performance benchmarking and testing", "category": "performance"},
            {"name": "monitoring", "description": "System monitoring and alerting", "category": "performance"},
        ]
        with self.client.session() as session:
            for tag_info in performance_tags:
                session.run(
                    """
                    MERGE (t:Tag {name: $name})
                    SET t.description = $description,
                        t.category = $category,
                        t.created_at = coalesce(t.created_at, timestamp()),
                        t.created_by = 'performance_system',
                        t.system_tag = true
                    """,
                    **tag_info,
                )
        return performance_tags
