"""
Cortex Local AI - Graphen-basierte Intelligenz direkt aus Neo4j.
"""
import os
from neo4j import GraphDatabase, Driver
from typing import List, Dict, Any

class Neo4jConnector:
    """
    Stellt eine Verbindung zur Neo4j-Datenbank her und bietet Methoden
    zum Abrufen von Graphendaten.
    """
    def __init__(self):
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "neo4jtest")

        try:
            self._driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
            self._driver.verify_connectivity()
        except Exception as e:
            raise ConnectionError(f"Could not connect to Neo4j database at {uri}. Error: {e}")

    def close(self):
        """Schließt die Datenbankverbindung."""
        if self._driver:
            self._driver.close()

    def get_common_neighbors_for_node(self, node_name: str, node_label: str = "Note") -> List[Dict[str, Any]]:
        """
        Findet Knoten, die gemeinsame Nachbarn mit einem gegebenen Knoten haben,
        und bewertet sie nach der Anzahl der gemeinsamen Nachbarn.
        Dies ist ein fundamentaler Algorithmus für Link-Vorhersagen.

        Args:
            node_name: Der Name des Startknotens.
            node_label: Das Label des Knotens (Standard: "Note").

        Returns:
            Eine Liste von Dictionaries, die potenzielle neue Links und deren Score enthalten.
        """
        query = f"""
        MATCH (n1:{node_label} {{name: $node_name}})-[:LINKS_TO]->(common_neighbor)<-[:LINKS_TO]-(n2:{node_label})
        WHERE n1 <> n2 AND NOT (n1)-[:LINKS_TO]->(n2)
        RETURN n2.name AS potential_link, count(common_neighbor) AS common_neighbors_score
        ORDER BY common_neighbors_score DESC
        LIMIT 10
        """
        with self._driver.session() as session:
            result = session.run(query, node_name=node_name)
            return [record.data() for record in result]

class LocalAI:
    """
    Implementiert die Logik für die interne, datengetriebene AI.
    Nutzt den Neo4jConnector, um Graphenanalysen durchzuführen.
    """
    def __init__(self):
        self.connector = Neo4jConnector()

    def suggest_links_for_node(self, node_name: str) -> List[Dict[str, Any]]:
        """
        Schlägt neue Links für einen bestimmten Knoten vor, basierend auf
        Graphenalgorithmen wie "Common Neighbors".
        """
        return self.connector.get_common_neighbors_for_node(node_name)

    def __del__(self):
        self.connector.close()

