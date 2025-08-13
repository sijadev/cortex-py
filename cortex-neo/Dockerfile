# Dockerfile für cortex-neo CLI-Projekt
FROM python:3.12-slim

WORKDIR /app

# Systemabhängigkeiten (optional, falls benötigt)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Projektdateien kopieren
COPY requirements.txt ./
COPY cortex_cli.py ./

# Abhängigkeiten installieren
RUN pip install --no-cache-dir -r requirements.txt

# Standard-Entrypoint für die CLI
ENTRYPOINT ["python", "cortex_cli.py"]
CMD ["--help"]
