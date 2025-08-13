# Beispiel: Automatische Tag-Generierung durch KI in Neo4J

## 1. Python-Skript (mit Neo4J Python Driver)

```python
from neo4j import GraphDatabase

# Beispiel: Projekte, die von der KI als zusammengehörig erkannt wurden
gemeinsame_projekte = ["ProjektA", "ProjektB", "ProjektC"]
neuer_tag = "gemeinsames-projekt"

uri = "bolt://localhost:7687"
user = "neo4j"
password = "dein_passwort"

def tag_hinzufuegen(session, projekte, tag_name):
    cypher = """
    UNWIND $projekte AS pname
    MATCH (n:Note {name: pname})
    MERGE (t:Tag {name: $tag_name})
    MERGE (n)-[:TAGGED_WITH]->(t)
    """
    session.run(cypher, projekte=projekte, tag_name=tag_name)

with GraphDatabase.driver(uri, auth=(user, password)) as driver:
    with driver.session() as session:
        tag_hinzufuegen(session, gemeinsame_projekte, neuer_tag)
```

## 2. Cypher-Query (direkt im Neo4J-Browser)

```cypher
UNWIND ["ProjektA", "ProjektB", "ProjektC"] AS pname
MATCH (n:Note {name: pname})
MERGE (t:Tag {name: "gemeinsames-projekt"})
MERGE (n)-[:TAGGED_WITH]->(t);
```

---

**Erklärung:**
- Die KI liefert eine Liste von Notizen/Projekten, die einen neuen gemeinsamen Tag bekommen sollen.
- Das Skript/Query legt den Tag an (falls nicht vorhanden) und verknüpft alle betroffenen Notizen damit.
- Das Vorgehen ist sowohl für manuelle als auch für KI-gestützte Tag-Generierung geeignet.

---

*Dieses Beispiel kann direkt in das Konzept übernommen und bei Bedarf erweitert werden.*
