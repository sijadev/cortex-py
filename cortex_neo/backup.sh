#!/usr/bin/env bash
set -euo pipefail

# Neo4j Docker backup/restore helper for the cortex-neo setup (Neo4j 5)
#
# Usage:
#   ./backup.sh backup [--name neo4j] [--db neo4j] [--out ./backups]
#   ./backup.sh restore [--name neo4j] [--db neo4j] [--file BACKUP_FILE] [--in ./backups] [--force]
#
# Notes:
# - Performs offline operations (stops the neo4j container) for data safety.
# - Uses a one-off neo4j:5 container with the container's /data volume mounted to run neo4j-admin.
# - Dump creates <db>.dump under the output directory by default with a timestamp suffix if --file is not provided.
# - Restore expects a .dump file and will load it into the target database (default 'neo4j').
# - Destructive restore requires --force.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_CONTAINER="neo4j"
DEFAULT_DB="neo4j"
DEFAULT_OUT_DIR="${SCRIPT_DIR}/backups"
DEFAULT_IN_DIR="${SCRIPT_DIR}/backups"
IMAGE_TAG="neo4j:5"
DATA_VOLUME=""  # auto-detected

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

log_info()  { echo -e "${COLOR_BLUE}ℹ️  $*${COLOR_RESET}"; }
log_warn()  { echo -e "${COLOR_YELLOW}⚠️  $*${COLOR_RESET}"; }
log_error() { echo -e "${COLOR_RED}❌ $*${COLOR_RESET}"; }
log_ok()    { echo -e "${COLOR_GREEN}✅ $*${COLOR_RESET}"; }

die() { log_error "$*"; exit 1; }

has_cmd() { command -v "$1" >/dev/null 2>&1; }

ensure_tools() {
  has_cmd docker || die "docker not found. Please install Docker."
  if has_cmd docker && docker compose version >/dev/null 2>&1; then
    export USE_COMPOSE_V2=1
  else
    if has_cmd docker-compose; then
      export USE_COMPOSE_V1=1
    else
      log_warn "docker compose not found; falling back to 'docker' container controls."
      export USE_DOCKER_ONLY=1
    fi
  fi
}

compose_stop() {
  local svc="$1"
  if [[ -n "${USE_COMPOSE_V2:-}" ]]; then
    (cd "$SCRIPT_DIR" && docker compose stop "$svc")
  elif [[ -n "${USE_COMPOSE_V1:-}" ]]; then
    (cd "$SCRIPT_DIR" && docker-compose stop "$svc")
  else
    docker stop "$svc" || true
  fi
}

compose_start() {
  local svc="$1"
  if [[ -n "${USE_COMPOSE_V2:-}" ]]; then
    (cd "$SCRIPT_DIR" && docker compose start "$svc")
  elif [[ -n "${USE_COMPOSE_V1:-}" ]]; then
    (cd "$SCRIPT_DIR" && docker-compose start "$svc")
  else
    docker start "$svc" || true
  fi
}

get_data_volume() {
  local container_name="$1"
  # Find the named volume mounted at /data for the container
  docker inspect -f '{{range .Mounts}}{{if and (eq .Destination "/data") (eq .Type "volume")}}{{.Name}}{{end}}{{end}}' "$container_name" 2>/dev/null || true
}

run_admin() {
  # Run neo4j-admin in a one-off container with the data volume mounted
  # $1... args to pass to neo4j-admin
  local args="$*"
  docker run --rm \
    -v ${DATA_VOLUME}:/data \
    -v "$WORK_DIR":/backups \
    -e NEO4J_HOME=/var/lib/neo4j \
    "$IMAGE_TAG" \
    bash -lc "/var/lib/neo4j/bin/neo4j-admin ${args}"
}

usage() {
  cat <<EOF
Usage:
  $0 backup [--name neo4j] [--db neo4j] [--out ./backups] [--file NAME.dump]
  $0 restore [--name neo4j] [--db neo4j] [--file NAME.dump] [--in ./backups] [--force]

Options:
  --name    Container/service name (default: ${DEFAULT_CONTAINER})
  --db      Database name (default: ${DEFAULT_DB})
  --out     Backup output directory (default: ${DEFAULT_OUT_DIR})
  --in      Backup input directory for restore (default: ${DEFAULT_IN_DIR})
  --file    Backup filename (.dump). If omitted on backup, a timestamped name is used.
  --force   Required for restore (destructive)

Details:
  The script auto-detects the Docker named volume mounted at /data for the container
  and mounts it into a one-off neo4j:5 admin container to perform offline dump/load.
EOF
}

# Parse arguments
ACTION="${1:-}"
shift || true
CONTAINER="$DEFAULT_CONTAINER"
DB_NAME="$DEFAULT_DB"
OUT_DIR="$DEFAULT_OUT_DIR"
IN_DIR="$DEFAULT_IN_DIR"
FILE_NAME=""
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) CONTAINER="$2"; shift 2;;
    --db) DB_NAME="$2"; shift 2;;
    --out) OUT_DIR="$2"; shift 2;;
    --in) IN_DIR="$2"; shift 2;;
    --file) FILE_NAME="$2"; shift 2;;
    --force) FORCE=1; shift;;
    -h|--help) usage; exit 0;;
    *) log_warn "Unknown option: $1"; usage; exit 1;;
  esac
done

[[ -z "$ACTION" ]] && { usage; exit 1; }

ensure_tools

# Determine the data volume used by the container
DATA_VOLUME="$(get_data_volume "$CONTAINER")"
[[ -n "$DATA_VOLUME" ]] || die "Could not detect /data named volume for container '$CONTAINER'. Is it running or created via docker-compose?"

case "$ACTION" in
  backup)
    mkdir -p "$OUT_DIR"
    TS=$(date +%Y%m%d-%H%M%S)
    if [[ -z "$FILE_NAME" ]]; then
      FILE_NAME="${DB_NAME}-${TS}.dump"
    fi
    WORK_DIR="$OUT_DIR"
    log_info "Stopping container '$CONTAINER' for offline backup..."
    compose_stop "$CONTAINER"

    log_info "Creating dump for database '$DB_NAME' into $OUT_DIR/$FILE_NAME ..."
    # neo4j-admin database dump <db> --to-path=/backups
    run_admin "database dump '$DB_NAME' --to-path=/backups"

    # neo4j-admin always writes <db>.dump; rename if a custom name was requested
    if [[ "$FILE_NAME" != "${DB_NAME}.dump" ]]; then
      if [[ -f "$OUT_DIR/${DB_NAME}.dump" ]]; then
        mv -f "$OUT_DIR/${DB_NAME}.dump" "$OUT_DIR/$FILE_NAME"
      fi
    fi

    log_info "Starting container '$CONTAINER' again..."
    compose_start "$CONTAINER"

    log_ok "Backup complete: $OUT_DIR/$FILE_NAME"
    ;;

  restore)
    [[ $FORCE -eq 1 ]] || die "Restore is destructive. Re-run with --force to proceed."
    [[ -n "$FILE_NAME" ]] || die "--file <NAME.dump> is required for restore."
    [[ -f "$IN_DIR/$FILE_NAME" ]] || die "Dump file not found: $IN_DIR/$FILE_NAME"
    WORK_DIR="$IN_DIR"

    log_warn "Stopping container '$CONTAINER' for restore..."
    compose_stop "$CONTAINER"

    log_warn "Restoring database '$DB_NAME' from $IN_DIR/$FILE_NAME ..."
    # neo4j-admin database load <db> --from-path=/backups --overwrite-destination
    # Ensure the dump file has the expected name <db>.dump inside /backups
    docker run --rm \
      -v ${DATA_VOLUME}:/data \
      -v "$WORK_DIR":/backups \
      -e NEO4J_HOME=/var/lib/neo4j \
      "$IMAGE_TAG" \
      bash -lc "cp -f /backups/'$FILE_NAME' /backups/'$DB_NAME'.dump && /var/lib/neo4j/bin/neo4j-admin database load '$DB_NAME' --from-path=/backups --overwrite-destination"

    log_info "Starting container '$CONTAINER' again..."
    compose_start "$CONTAINER"

    log_ok "Restore complete for database '$DB_NAME' from $FILE_NAME"
    ;;

  *)
    usage
    exit 1
    ;;

esac
