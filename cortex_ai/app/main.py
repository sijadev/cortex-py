from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import os
from neo4j import GraphDatabase, basic_auth

app = FastAPI()

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")

WORKFLOW_NAME = "Decision-Workflow"

# Service-Funktion für Neo4J-Abfrage
def get_workflow_status() -> Dict[str, Any]:
    driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Workflow-Knoten abfragen
        workflow_result = session.run(
            """
            MATCH (w:Workflow {name: $workflow_name})
            RETURN w
            """, workflow_name=WORKFLOW_NAME
        )
        workflow_node = workflow_result.single()
        if not workflow_node:
            raise HTTPException(status_code=404, detail="Workflow nicht gefunden")
        workflow = dict(workflow_node["w"])

        # Schritte abfragen
        steps_result = session.run(
            """
            MATCH (w:Workflow {name: $workflow_name})-[:HAS_STEP]->(s:Step)
            OPTIONAL MATCH (s)-[:NEXT]->(next:Step)
            RETURN s, next
            ORDER BY s.order
            """, workflow_name=WORKFLOW_NAME
        )
        steps = []
        for record in steps_result:
            step = dict(record["s"])
            next_step = dict(record["next"]) if record["next"] else None
            step["next"] = next_step["name"] if next_step else None
            steps.append(step)

        return {"workflow": workflow, "steps": steps}

@app.get("/workflow/status", response_model=Dict[str, Any])
def workflow_status():
    """Gibt den Status und die Schritte des Decision-Workflows zurück."""
    return get_workflow_status()
