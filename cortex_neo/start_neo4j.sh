#!/bin/bash
# Start or create Neo4j Docker container only if not already running and port is free

CONTAINER_NAME="neo4j-test-default"
NEO4J_IMAGE="neo4j"
PORT=7474
BOLT_PORT=7687

# Check if port is already in use
if lsof -i :$PORT | grep LISTEN; then
  echo "Error: Port $PORT is already in use. Please stop the process using it before starting Neo4j."
  exit 1
fi

# Check if container exists
if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
  # Check if container is running
  if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    echo "Container $CONTAINER_NAME is already running."
  else
    echo "Starting existing container $CONTAINER_NAME..."
    docker start $CONTAINER_NAME
  fi
else
  echo "Creating and starting new Neo4j container $CONTAINER_NAME..."
  docker run -d --name $CONTAINER_NAME -p $PORT:7474 -p $BOLT_PORT:7687 -e NEO4J_AUTH=neo4j/neo4jtest $NEO4J_IMAGE
fi

