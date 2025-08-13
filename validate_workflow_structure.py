#!/usr/bin/env python3
"""
Validiert, ob der Decision-Workflow und seine Schritte korrekt in Neo4J angelegt sind.
Kann als CI-Job (z.B. in cortex-ci) ausgeführt werden.
"""
from neo4j import GraphDatabase
import os
import sys

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "test")

WORKFLOW_NAME = "Decision-Workflow"
EXPECTED_STEPS = [
    {"name": "Data-Repository", "order": 1},
    {"name": "Neural-Link", "order": 2},
    {"name": "Confidence", "order": 3},
    {"name": "ADR", "order": 4},
]

def validate_workflow_structure():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Prüfe, ob Workflow existiert
        result = session.run(
            """
            MATCH (w:Workflow {name: $workflow_name})
            RETURN w
            """, workflow_name=WORKFLOW_NAME
        )
        if not result.single():
            print(f"❌ Workflow '{WORKFLOW_NAME}' nicht gefunden.")
            sys.exit(1)
        print(f"✅ Workflow '{WORKFLOW_NAME}' gefunden.")

        # Prüfe Schritte
        for step in EXPECTED_STEPS:
            result = session.run(
                """
                MATCH (w:Workflow {name: $workflow_name})-[:HAS_STEP]->(s:Step {name: $step_name, order: $step_order})
                RETURN s
                """,
                workflow_name=WORKFLOW_NAME,
                step_name=step["name"],
                step_order=step["order"]
            )
            if not result.single():
                print(f"❌ Schritt '{step['name']}' (Order {step['order']}) fehlt.")
                sys.exit(1)
            print(f"✅ Schritt '{step['name']}' korrekt verknüpft.")

        # Prüfe Reihenfolge
        for i in range(len(EXPECTED_STEPS)-1):
            from_step = EXPECTED_STEPS[i]
            to_step = EXPECTED_STEPS[i+1]
            result = session.run(
                """
                MATCH (s1:Step {name: $from_name, order: $from_order})-[:NEXT]->(s2:Step {name: $to_name, order: $to_order})
                RETURN s1, s2
                """,
                from_name=from_step["name"],
                from_order=from_step["order"],
                to_name=to_step["name"],
                to_order=to_step["order"]
            )
            if not result.single():
                print(f"❌ Reihenfolge fehlt: {from_step['name']} -> {to_step['name']}")
                sys.exit(1)
            print(f"✅ Reihenfolge: {from_step['name']} -> {to_step['name']}")

    print("\n🎉 Workflow-Struktur in Neo4J ist korrekt!")

if __name__ == "__main__":
    validate_workflow_structure()
