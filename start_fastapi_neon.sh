#!/bin/bash
# Start script for FastAPI app with Neon DB

# Exit on error
set -e

# Set your Neon DB connection string here or ensure it's set in the environment
# export DATABASE_URL="postgresql://<username>:<password>@<neon-host>/<database>"

# Optionally, print the DB URL for debugging (remove in production)
echo "Using DATABASE_URL=$DATABASE_URL"

# Start FastAPI app using uvicorn
uvicorn cortex_ai.app.main:app --host localhost --port 8000
