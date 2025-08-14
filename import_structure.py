from neo4j import GraphDatabase

# Connection details
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4jtest"  # Updated password
CYPHER_FILE = "create_structure.cypher"

# Read Cypher script
with open(CYPHER_FILE, "r", encoding="utf-8") as f:
    cypher_script = f.read()

# Split into individual statements by semicolon, ignore comments and blank lines
raw_statements = cypher_script.split(";")
statements = []
for stmt in raw_statements:
    stmt = stmt.strip()
    # Ignore comments and blank lines
    if not stmt or stmt.startswith("//"):
        continue
    statements.append(stmt)

# Connect and execute
print(f"Connecting to Neo4J at {NEO4J_URI}...")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
with driver.session() as session:
    for i, stmt in enumerate(statements, 1):
        try:
            session.run(stmt)
            print(f"[{i}/{len(statements)}] Executed:", stmt[:60], "...")
        except Exception as e:
            print(f"Error in statement {i}: {e}\n{stmt}")
print("Import completed.")
