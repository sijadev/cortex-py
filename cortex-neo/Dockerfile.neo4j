# Minimaler Dockerfile für Neo4J Standalone (empfohlen: nutze das offizielle Image)
FROM neo4j:5

# Setze Standard-Auth (kann per ENV überschrieben werden)
ENV NEO4J_AUTH=neo4j/neo4jtest

# Exponiere Ports für HTTP und Bolt
EXPOSE 7474 7687

# Optional: Volumes für Datenpersistenz (wird meist in docker-compose.yml geregelt)
VOLUME /data

# Startbefehl (wird vom Base-Image übernommen)
