from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List
try:
    from ..infra.neo4j_client import Neo4jClient
except ImportError:  # Support running without package context
    from infra.neo4j_client import Neo4jClient  # type: ignore


@dataclass
class ContentRepository:
    client: Neo4jClient

    def create_note(self, name: str, content: str, description: str, note_type: str, smart: bool) -> None:
        with self.client.session() as session:
            session.run(
                """
                MERGE (n:Note {name: $name})
                SET n.content = $content,
                    n.description = $description,
                    n.type = $note_type,
                    n.created_with_ai = $smart,
                    n.updated_at = timestamp()
                """,
                name=name,
                content=content or "",
                description=description or "",
                note_type=note_type or "",
                smart=smart,
            )

    def add_tag(self, note_name: str, tag_name: str) -> None:
        with self.client.session() as session:
            session.run(
                """
                MATCH (n:Note {name: $name})
                MERGE (t:Tag {name: $tag_name})
                MERGE (n)-[:TAGGED_WITH]->(t)
                """,
                name=note_name,
                tag_name=tag_name,
            )

    def search(self, query: str) -> List[Dict[str, Any]]:
        cypher = (
            """
            MATCH (n:Note)
            WHERE n.name CONTAINS $query OR n.content CONTAINS $query OR n.description CONTAINS $query
            OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
            RETURN n as note, collect(DISTINCT t.name) as tags
            ORDER BY CASE WHEN n.name CONTAINS $query THEN 1 ELSE 2 END, n.updated_at DESC
            LIMIT 20
            """
        )
        with self.client.session() as session:
            return [{"note": r["note"], "tags": r["tags"]} for r in session.run(cypher, query=query)]

    def get_note_detail(self, name: str) -> Dict[str, Any] | None:
        cypher = (
            """
            MATCH (n:Note {name: $name})
            OPTIONAL MATCH (n)-[:TAGGED_WITH]->(tag:Tag)
            OPTIONAL MATCH (n)-[:LINKS_TO]->(linked:Note)
            OPTIONAL MATCH (incoming:Note)-[:LINKS_TO]->(n)
            RETURN n as note,
                   collect(DISTINCT tag) AS tags,
                   collect(DISTINCT linked) AS outgoing_links,
                   collect(DISTINCT incoming) AS incoming_links
            """
        )
        with self.client.session() as session:
            rec = session.run(cypher, name=name).single()
            if not rec:
                return None
            return {
                "note": rec["note"],
                "tags": [t for t in rec["tags"] if t],
                "outgoing": [n for n in rec["outgoing_links"] if n],
                "incoming": [n for n in rec["incoming_links"] if n],
            }

    def list_notes_with_tag_count(self) -> List[Dict[str, Any]]:
        cypher = (
            """
            MATCH (n:Note)
            OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
            RETURN n as note, count(t) as tag_count
            ORDER BY n.updated_at DESC
            """
        )
        with self.client.session() as session:
            return [{"note": r["note"], "tag_count": r["tag_count"]} for r in session.run(cypher)]
