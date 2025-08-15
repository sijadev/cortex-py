# Konzept: Migration der Obsidian-Struktur nach Neo4J (ohne Datenübernahme)

## Ziel
Die bestehende Obsidian-Wissensstruktur (Notizen, Links, Tags, Templates) soll als leeres, aber logisch identisches Netzwerk in Neo4J abgebildet werden. Es werden keine Inhalte übernommen, sondern nur die Struktur, Verlinkungen und Metadaten.

---

## 1. Grundprinzipien
- **Notizen**: Jede Obsidian-Notiz wird ein Knoten (Node) in Neo4J (`:Note`).
- **Verlinkungen**: Jeder interne Link (`[[Zielnotiz]]`) wird eine Beziehung `(:Note)-[:LINKS_TO]->(:Note)`.
- **Tags**: Jeder Tag wird ein Knoten (`:Tag`). Notizen werden über `(:Note)-[:TAGGED_WITH]->(:Tag)` verknüpft.
- **Templates**: Jedes Template wird ein Knoten (`:Template`). Notizen, die auf einem Template basieren, werden über `(:Note)-[:USES_TEMPLATE]->(:Template)` verknüpft.
- **Keine Inhalte**: Es werden keine Textinhalte, sondern nur Namen, Strukturen und Beziehungen übernommen.

---

## 2. Tag-Management und Einfluss
- Tags dienen als Gruppierung und Filter, nicht als direkte Links zwischen Notizen.
- Optional können Tags als "virtuelle Links" interpretiert werden (z.B. alle Notizen mit demselben Tag sind indirekt verbunden).
- Tag-Knoten ermöglichen flexible Abfragen und Visualisierungen in Neo4J.

---

## 3. Migrationsschritte (ohne Daten)
1. **Analyse**: Erfasse alle Notiznamen, Links, Tags und Templates aus Obsidian.
2. **Mapping**: Lege für jede Notiz, jeden Tag und jedes Template einen Knoten in Neo4J an.
3. **Beziehungen**: Erzeuge für jede Verlinkung und Tag-Zuordnung eine Beziehung.
4. **Validierung**: Prüfe, ob die Struktur und Verlinkungen logisch korrekt übernommen wurden.

---

## 4. Erweiterbarkeit
- Das Konzept kann um weitere Metadaten (z.B. Ordnerstruktur, Aliasnamen, Custom Properties) ergänzt werden.
- Die Tag-Logik kann angepasst werden (z.B. Tag-Hierarchien, Tag-Gruppen).
- Templates können mit weiteren Eigenschaften versehen werden.
- Spätere Datenübernahme (z.B. Inhalte, Versionierung) ist möglich, aber nicht Teil dieses Konzepts.

---

## 5. Nächste Schritte / ToDos
- [ ] Beispielskript für die Extraktion der Struktur aus Obsidian erstellen
- [ ] Beispiel für Cypher-Importskripte bereitstellen
- [ ] Mapping für spezielle Obsidian-Features (z.B. YAML-Frontmatter, Alias, Ordner) definieren
- [ ] Validierung und Visualisierung der Neo4J-Struktur
- [ ] Erweiterungen und Anpassungen nach Chatverlauf dokumentieren

---

## 6. Beispiel: Automatische Tag-Generierung durch KI

Die KI kann Zusammenhänge zwischen Notizen/Projekten erkennen und neue Tags vorschlagen oder automatisch vergeben. Beispiel:

### Python-Skript (mit Neo4J Python Driver)

```python
from neo4j import GraphDatabase

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

### Cypher-Query (direkt im Neo4J-Browser)

```cypher
UNWIND ["ProjektA", "ProjektB", "ProjektC"] AS pname
MATCH (n:Note {name: pname})
MERGE (t:Tag {name: "gemeinsames-projekt"})
MERGE (n)-[:TAGGED_WITH]->(t);
```

**Erklärung:**
- Die KI liefert eine Liste von Notizen/Projekten, die einen neuen gemeinsamen Tag bekommen sollen.
- Das Skript/Query legt den Tag an (falls nicht vorhanden) und verknüpft alle betroffenen Notizen damit.
- Das Vorgehen ist sowohl für manuelle als auch für KI-gestützte Tag-Generierung geeignet.

---

*Dieses Dokument wird im weiteren Chatverlauf fortlaufend aktualisiert und erweitert.*

---

## 7. Mapping-Beispiel: Workflow aus Cortex-Dokumentation nach Neo4J

### Beispiel: Decision-Workflow als Graph-Modell

**Beschreibung:**
Der Decision-Workflow aus der Cortex-Dokumentation besteht aus mehreren klar definierten Schritten (z.B. Data-Repository, Neural-Link, Confidence, ADR). Diese lassen sich als Workflow-Node mit zugehörigen Step-Nodes und Beziehungen in Neo4J abbilden.

**Graph-Modell:**

```cypher
// Workflow-Knoten anlegen
MERGE (w:Workflow {name: "Decision-Workflow", type: "Standard", status: "in progress"})

// Schritte als Step-Nodes anlegen und mit Workflow verknüpfen
WITH w
UNWIND [
    {name: "Data-Repository", order: 1},
    {name: "Neural-Link", order: 2},
    {name: "Confidence", order: 3},
    {name: "ADR", order: 4}
] AS step
MERGE (s:Step {name: step.name, order: step.order})
MERGE (w)-[:HAS_STEP]->(s)

// Schritte miteinander verketten (Reihenfolge)
WITH collect(s) AS steps
UNWIND range(0, size(steps)-2) AS idx
WITH steps[idx] AS fromStep, steps[idx+1] AS toStep
MERGE (fromStep)-[:NEXT]->(toStep)
```

**Erweiterung:**
- Jeder Step kann mit weiteren Metadaten (z.B. Status, Verantwortlicher, Start-/Endzeit) versehen werden.
- Workflows können beliebig viele Schritte enthalten und verschachtelt werden.
- Über die Beziehungen `HAS_STEP` und `NEXT` ist die Reihenfolge und Zugehörigkeit eindeutig abbildbar.

**Visualisierung:**
- In Neo4J kann so jeder Workflow als Knoten mit verknüpften Schritten und deren Reihenfolge dargestellt werden.
- Über weitere Beziehungen (z.B. zu Templates, Tasks, Akteuren) kann das Modell flexibel erweitert werden.

---
