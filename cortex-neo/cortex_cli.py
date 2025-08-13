import click
from neo4j import GraphDatabase
import os

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")

@click.group()
def cli():
    """Cortex-CLI für Neo4J-Workflow-Operationen"""
    pass

@cli.command()
def list_workflows():
    """Zeigt alle Workflows in der Datenbank."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run("MATCH (w:Workflow) RETURN w")
        for record in result:
            print(record["w"])

@cli.command()
def list_steps():
    """Zeigt alle Steps aller Workflows."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run("MATCH (s:Step) RETURN s ORDER BY s.order")
        for record in result:
            print(record["s"])

@cli.command()
@click.argument('workflow_name')
def show_workflow(workflow_name):
    """Zeigt Details und Steps eines bestimmten Workflows."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run(
            """
            MATCH (w:Workflow {name: $workflow_name})-[:HAS_STEP]->(s:Step)
            RETURN w, s ORDER BY s.order
            """,
            workflow_name=workflow_name
        )
        steps = []
        workflow = None
        for record in result:
            workflow = record["w"]
            steps.append(record["s"])
        if workflow:
            print(f"Workflow: {workflow['name']} (Status: {workflow.get('status','')})")
            for step in steps:
                print(f"  Step {step['order']}: {step['name']}")
        else:
            print(f"Kein Workflow mit Namen '{workflow_name}' gefunden.")

# --- Erweiterte Methoden ---
@cli.command()
@click.argument('workflow_name')
def create_workflow(workflow_name):
    """Legt einen neuen Workflow an."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run(
            "MERGE (w:Workflow {name: $workflow_name, type: 'Standard', status: 'in progress'})",
            workflow_name=workflow_name
        )
    print(f"Workflow '{workflow_name}' wurde angelegt.")

@cli.command()
@click.argument('workflow_name')
@click.argument('step_name')
@click.argument('order', type=int)
def add_step(workflow_name, step_name, order):
    """Fügt einem Workflow einen Step hinzu."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run(
            """
            MATCH (w:Workflow {name: $workflow_name})
            MERGE (s:Step {name: $step_name, order: $order})
            MERGE (w)-[:HAS_STEP]->(s)
            """,
            workflow_name=workflow_name,
            step_name=step_name,
            order=order
        )
    print(f"Step '{step_name}' (Order {order}) zu Workflow '{workflow_name}' hinzugefügt.")

@cli.command()
@click.argument('workflow_name')
def delete_workflow(workflow_name):
    """Löscht einen Workflow und alle zugehörigen Steps."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run(
            """
            MATCH (w:Workflow {name: $workflow_name})-[r:HAS_STEP]->(s:Step)
            DETACH DELETE w, s
            """,
            workflow_name=workflow_name
        )
    print(f"Workflow '{workflow_name}' und zugehörige Steps gelöscht.")

@cli.command()
@click.argument('step_name')
def delete_step(step_name):
    """Löscht einen Step (unabhängig vom Workflow)."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run(
            "MATCH (s:Step {name: $step_name}) DETACH DELETE s",
            step_name=step_name
        )
    print(f"Step '{step_name}' gelöscht.")

@cli.command()
@click.argument('workflow_name')
@click.argument('status')
def set_status(workflow_name, status):
    """Setzt den Status eines Workflows."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run(
            "MATCH (w:Workflow {name: $workflow_name}) SET w.status = $status",
            workflow_name=workflow_name,
            status=status
        )
    print(f"Status von Workflow '{workflow_name}' auf '{status}' gesetzt.")


if __name__ == "__main__":
    cli()
