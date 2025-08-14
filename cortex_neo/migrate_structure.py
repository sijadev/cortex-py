#!/usr/bin/env python3
"""
Migration script to map Obsidian-like structure (Notes, Tags, Templates, Links) into Neo4j.
Idempotent: uses MERGE for nodes and relationships.

Input file formats: YAML or JSON with keys: notes, tags, templates, links, assignments

Example (YAML):
---
notes:
  - Home
  - ProjectA
  - ProjectB

templates:
  - Project
  - Decision

tags:
  - important
  - research

links:
  - from: Home
    to: ProjectA
  - from: ProjectA
    to: ProjectB

assignments:
  uses_template:
    - note: ProjectA
      template: Project
  tagged_with:
    - note: ProjectA
      tag: important
    - note: ProjectB
      tag: research
"""
from __future__ import annotations
import os
import json
from typing import Any, Dict
from neo4j import GraphDatabase

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dep
    yaml = None

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")


def _load_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if path.lower().endswith(('.yaml', '.yml')):
        if yaml is None:
            raise RuntimeError("PyYAML not installed. Install pyyaml or provide a .json file.")
        return yaml.safe_load(text) or {}
    return json.loads(text or '{}')


def _ensure_note(session, name: str):
    session.run("MERGE (n:Note {name: $name})", name=name)


def _ensure_template(session, name: str):
    session.run("MERGE (t:Template {name: $name})", name=name)


def _ensure_tag(session, name: str):
    session.run("MERGE (t:Tag {name: $name})", name=name)


def _link_notes(session, from_note: str, to_note: str):
    session.run(
        """
        MERGE (a:Note {name: $from})
        MERGE (b:Note {name: $to})
        MERGE (a)-[:LINKS_TO]->(b)
        """,
        **{"from": from_note, "to": to_note},
    )


def _use_template(session, note: str, template: str):
    session.run(
        """
        MERGE (n:Note {name: $note})
        MERGE (t:Template {name: $template})
        MERGE (n)-[:USES_TEMPLATE]->(t)
        """,
        note=note, template=template,
    )


def _tag_note(session, note: str, tag: str):
    session.run(
        """
        MERGE (n:Note {name: $note})
        MERGE (t:Tag {name: $tag})
        MERGE (n)-[:TAGGED_WITH]->(t)
        """,
        note=note, tag=tag,
    )


def migrate_from_data(data: Dict[str, Any]) -> None:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    notes = data.get('notes') or []
    templates = data.get('templates') or []
    tags = data.get('tags') or []
    links = data.get('links') or []
    assignments = data.get('assignments') or {}

    with driver.session() as session:
        for n in notes:
            if isinstance(n, str) and n:
                _ensure_note(session, n)
        for t in templates:
            if isinstance(t, str) and t:
                _ensure_template(session, t)
        for t in tags:
            if isinstance(t, str) and t:
                _ensure_tag(session, t)
        for l in links:
            if isinstance(l, dict) and l.get('from') and l.get('to'):
                _link_notes(session, l['from'], l['to'])

        for u in (assignments.get('uses_template') or []):
            if isinstance(u, dict) and u.get('note') and u.get('template'):
                _use_template(session, u['note'], u['template'])
        for tg in (assignments.get('tagged_with') or []):
            if isinstance(tg, dict) and tg.get('note') and tg.get('tag'):
                _tag_note(session, tg['note'], tg['tag'])


def migrate_from_file(path: str) -> None:
    data = _load_file(path)
    migrate_from_data(data)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Migrate Notes/Tags/Templates/Links into Neo4j")
    p.add_argument("file", help="Path to YAML or JSON structure file")
    args = p.parse_args()
    migrate_from_file(args.file)
    print("Migration complete.")

