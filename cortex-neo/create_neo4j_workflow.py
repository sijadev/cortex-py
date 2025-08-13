#!/usr/bin/env python3
"""
Beispiel-Skript: Erstellt die Grundstruktur für das Neo4J-Mapping gemäß Konzept.md
"""
from neo4j import GraphDatabase
import os

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")

WORKFLOW_NAME = "Decision-Workflow"
STEPS = [
    {"name": "Data-Repository", "order": 1},
    {"name": "Neural-Link", "order": 2},
    {"name": "Confidence", "order": 3},
    {"name": "ADR", "order": 4},
]

def create_workflow_structure():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Workflow-Knoten anlegen
        session.run(
            """
            MERGE (w:Workflow {name: $workflow_name, type: 'Standard', status: 'in progress'})
            """,
            workflow_name=WORKFLOW_NAME
        )
        # Schritte anlegen und verknüpfen
        for step in STEPS:
            session.run(
                """
                MATCH (w:Workflow {name: $workflow_name})
                MERGE (s:Step {name: $step_name, order: $step_order})
                MERGE (w)-[:HAS_STEP]->(s)
                """,
                workflow_name=WORKFLOW_NAME,
                step_name=step["name"],
                step_order=step["order"]
            )
        # Reihenfolge verknüpfen
        for i in range(len(STEPS)-1):
            from_step = STEPS[i]
            to_step = STEPS[i+1]
            session.run(
                """
                MATCH (s1:Step {name: $from_name, order: $from_order})
                MATCH (s2:Step {name: $to_name, order: $to_order})
                MERGE (s1)-[:NEXT]->(s2)
                """,
                from_name=from_step["name"],
                from_order=from_step["order"],
                to_name=to_step["name"],
                to_order=to_step["order"]
            )
    print("Neo4J-Workflow-Struktur erfolgreich erstellt.")

if __name__ == "__main__":
    create_workflow_structure()
