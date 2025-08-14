from __future__ import annotations
import os
import yaml
from typing import Any, Dict, List, Tuple
from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")


def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def reset_graph(session):
    """Clear only Note/Tag/Template graph and their relationships."""
    # Delete relationships first for safety, then nodes
    session.run("MATCH ()-[r:LINKS_TO]->() DELETE r")
    session.run("MATCH ()-[r:TAGGED_WITH]->() DELETE r")
    session.run("MATCH ()-[r:USES_TEMPLATE]->() DELETE r")
    session.run("MATCH (n:Note) DETACH DELETE n")
    session.run("MATCH (t:Tag) DETACH DELETE t")
    session.run("MATCH (t:Template) DETACH DELETE t")


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def apply_initial(session, initial: Dict[str, Any]):
    from ..migrate_structure import migrate_from_data  # fixed import
    # Standard parts via migrate
    std = {k: initial.get(k) for k in ["notes","tags","templates","links","assignments"] if k in initial}
    if std:
        migrate_from_data(std)
    # Self-links or duplicate links via raw cypher (optional)
    for name in initial.get("self_links", []) or []:
        session.run(
            """
            MERGE (n:Note {name: $name})
            CREATE (n)-[:LINKS_TO]->(n)
            """,
            name=name,
        )
    for dup in initial.get("duplicate_links", []) or []:
        a, b, count = dup.get("from"), dup.get("to"), int(dup.get("count", 2))
        if not a or not b or count < 2:
            continue
        session.run("MERGE (a:Note {name:$a}) MERGE (b:Note {name:$b})", a=a, b=b)
        # Create extra copies beyond MERGE baseline
        for _ in range(count):
            session.run(
                """
                MATCH (a:Note {name:$a}), (b:Note {name:$b})
                CREATE (a)-[:LINKS_TO]->(b)
                """,
                a=a, b=b,
            )
    for lp in initial.get("links_props", []) or []:
        a = lp.get("from"); b = lp.get("to"); props = lp.get("props", {}) or {}
        if not a or not b:
            continue
        session.run(
            """
            MERGE (a:Note {name:$a})
            MERGE (b:Note {name:$b})
            CREATE (a)-[r:LINKS_TO]->(b)
            SET r += $props
            """,
            a=a, b=b, props=props,
        )


def run_actions(session, actions: List[Dict[str, Any]]):
    """Execute a sequence of actions supported by cortex_cli logic via Cypher equivalents."""
    # We prefer to call the same cypher logic used in CLI.
    for act in actions or []:
        if "auto_link" in act:
            p = act["auto_link"] or {}
            by = p.get("by", "tag")
            min_shared = int(p.get("min_shared", 1))
            max_per_note = int(p.get("max_per_note", 50))
            if by in ("tag","all"):
                session.run(
                    """
                    MATCH (a:Note)-[:TAGGED_WITH]->(t:Tag)<-[:TAGGED_WITH]-(b:Note)
                    WHERE a.name < b.name
                    WITH a,b,count(t) AS shared
                    WHERE shared >= $min_shared
                    ORDER BY a.name, shared DESC
                    WITH a, collect({b:b, shared:shared}) AS pairs
                    UNWIND pairs[..$max_per_note] AS item
                    WITH a, item.b AS b, item.shared AS shared
                    MERGE (a)-[r:LINKS_TO]->(b)
                    SET r.auto = true,
                        r.tags_shared = shared,
                        r.weight = coalesce(r.templates_shared,0) + shared
                    """,
                    min_shared=min_shared, max_per_note=max_per_note,
                )
            if by in ("template","all"):
                session.run(
                    """
                    MATCH (a:Note)-[:USES_TEMPLATE]->(tpl:Template)<-[:USES_TEMPLATE]-(b:Note)
                    WHERE a.name < b.name
                    WITH a,b,count(tpl) AS shared
                    WHERE shared >= $min_shared
                    ORDER BY a.name, shared DESC
                    WITH a, collect({b:b, shared:shared}) AS pairs
                    UNWIND pairs[..$max_per_note] AS item
                    WITH a, item.b AS b, item.shared AS shared
                    MERGE (a)-[r:LINKS_TO]->(b)
                    SET r.auto = true,
                        r.templates_shared = shared,
                        r.weight = coalesce(r.tags_shared,0) + shared
                    """,
                    min_shared=min_shared, max_per_note=max_per_note,
                )
        if "link_fix" in act:
            p = act["link_fix"] or {}
            # remove self
            if p.get("remove_self", True):
                session.run("MATCH (n:Note)-[r:LINKS_TO]->(n) DELETE r")
            # dedupe
            if p.get("dedupe", True):
                session.run(
                    """
                    MATCH (a:Note)-[r:LINKS_TO]->(b:Note)
                    WITH a,b,collect(r) AS rels
                    WHERE size(rels) > 1
                    FOREACH (rr IN rels[1..] | DELETE rr)
                    """
                )
            # backfill shared, recompute weight
            if p.get("backfill_shared", True):
                session.run(
                    """
                    MATCH (a:Note)-[r:LINKS_TO]->(b:Note)
                    WHERE coalesce(r.auto,false)=true
                    OPTIONAL MATCH (a)-[:TAGGED_WITH]->(t:Tag)<-[:TAGGED_WITH]-(b)
                    WITH a,b,r, count(DISTINCT t) AS tags_shared
                    OPTIONAL MATCH (a)-[:USES_TEMPLATE]->(tpl:Template)<-[:USES_TEMPLATE]-(b)
                    WITH r, tags_shared, count(DISTINCT tpl) AS templates_shared
                    SET r.tags_shared = tags_shared,
                        r.templates_shared = templates_shared
                    """
                )
            if p.get("recompute_weight", True):
                session.run(
                    """
                    MATCH ()-[r:LINKS_TO]->()
                    WHERE coalesce(r.auto,false)=true
                    WITH r, coalesce(r.tags_shared,0) AS ts, coalesce(r.templates_shared,0) AS ps
                    SET r.weight = ts + ps
                    """
                )
            thr = p.get("remove_auto_below")
            if thr is not None:
                session.run(
                    "MATCH ()-[r:LINKS_TO]->() WHERE coalesce(r.auto,false)=true AND coalesce(r.weight,0) < $th DELETE r",
                    th=float(thr),
                )


def snapshot_graph(session) -> Dict[str, Any]:
    notes = [r["n"]["name"] for r in session.run("MATCH (n:Note) RETURN n ORDER BY n.name")]
    tags = [r["t"]["name"] for r in session.run("MATCH (t:Tag) RETURN t ORDER BY t.name")]
    templates = [r["t"]["name"] for r in session.run("MATCH (t:Template) RETURN t ORDER BY t.name")]
    links = []
    for r in session.run(
        """
        MATCH (a:Note)-[rel:LINKS_TO]->(b:Note)
        RETURN a,b,rel ORDER BY a.name,b.name
        """
    ):
        a = r["a"]["name"]
        b = r["b"]["name"]
        rel = r["rel"]
        entry = {"from": a, "to": b}
        # Capture known properties if present
        for key in ("weight","tags_shared","templates_shared","auto"):
            if key in rel:
                entry[key] = rel[key]
        links.append(entry)
    return {"notes": notes, "tags": tags, "templates": templates, "links": links}


def compare_graph(actual: Dict[str, Any], expected: Dict[str, Any]) -> Tuple[bool, str]:
    def norm_list(x):
        return sorted(set(x or []))
    def by_pair_map(links: List[Dict[str, Any]]):
        m: Dict[Tuple[str,str], Dict[str, Any]] = {}
        for d in (links or []):
            m[(d.get("from"), d.get("to"))] = d
        return m

    mismatches = []
    # Compare node label sets
    for key in ("notes","tags","templates"):
        a = norm_list(actual.get(key))
        e = norm_list(expected.get(key))
        if a != e:
            mismatches.append(f"Mismatch {key}: actual={a} expected={e}")
    # Compare link pairs (must match exactly)
    a_pairs = sorted({(d.get("from"), d.get("to")) for d in (actual.get("links") or [])})
    e_pairs = sorted({(d.get("from"), d.get("to")) for d in (expected.get("links") or [])})
    if a_pairs != e_pairs:
        mismatches.append(f"Mismatch links: actual={a_pairs} expected={e_pairs}")
    else:
        # If expected specifies properties for a given pair, assert subset equality
        a_map = by_pair_map(actual.get("links") or [])
        for ed in (expected.get("links") or []):
            pair = (ed.get("from"), ed.get("to"))
            ad = a_map.get(pair) or {}
            for prop in ("weight","tags_shared","templates_shared","auto"):
                if prop in ed:
                    if ad.get(prop) != ed.get(prop):
                        mismatches.append(f"Mismatch link prop {pair} {prop}: actual={ad.get(prop)} expected={ed.get(prop)}")
    ok = not mismatches
    return ok, "\n".join(mismatches)
