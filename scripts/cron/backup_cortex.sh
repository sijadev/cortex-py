#!/bin/bash

# 🛡️ Cortex Neo4j Backup Script
# Comprehensive backup strategy for data loss prevention

set -e  # Exit on any error

# Configuration
BACKUP_DIR="/Users/simonjanke/Projects/cortex-py/cortex_neo/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NEO4J_CONTAINER="cortex-neo4j"
PROJECT_DIR="/Users/simonjanke/Projects/cortex-py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Starting Cortex Backup Process...${NC}"

# Create backup directory structure
mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/auto"
mkdir -p "$BACKUP_DIR/pre"
mkdir -p "$BACKUP_DIR/emergency"

# Function to log with timestamp
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if Neo4j is running
check_neo4j() {
    log "${BLUE}📊 Checking Neo4j status...${NC}"

    if docker ps | grep -q "$NEO4J_CONTAINER"; then
        log "${GREEN}✅ Neo4j container is running${NC}"
        return 0
    else
        log "${YELLOW}⚠️  Neo4j container not found, checking local instance...${NC}"

        # Check if Neo4j is running locally
        if curl -s http://localhost:7474 > /dev/null 2>&1; then
            log "${GREEN}✅ Local Neo4j instance detected${NC}"
            return 0
        else
            log "${RED}❌ Neo4j not accessible${NC}"
            return 1
        fi
    fi
}

# Function to create structure export backup
create_structure_backup() {
    log "${BLUE}🔄 Creating Cortex structure backup...${NC}"

    cd "$PROJECT_DIR"

    # Try to export structure using cortex CLI
    if python3 cortex_neo/cortex_cli.py export-structure > "$BACKUP_DIR/structure-backup-$TIMESTAMP.yaml" 2>/dev/null; then
        log "${GREEN}✅ Structure backup created: structure-backup-$TIMESTAMP.yaml${NC}"
    else
        log "${YELLOW}⚠️  Structure export failed, creating manual backup...${NC}"

        # Create manual backup using Python
        python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from safe_transactions import SafeTransactionManager, DataIntegrityValidator
from neo4j import GraphDatabase
import os

NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'neo4jtest')

try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    backup_manager = SafeTransactionManager(driver, '$BACKUP_DIR/emergency')
    backup_file = backup_manager._create_backup('emergency-$TIMESTAMP')
    print(f'Manual backup created: {backup_file}')
    driver.close()
except Exception as e:
    print(f'Manual backup failed: {e}')
"
    fi
}

# Function to create Docker container backup (if applicable)
create_docker_backup() {
    if docker ps | grep -q "$NEO4J_CONTAINER"; then
        log "${BLUE}🔄 Creating Docker container backup...${NC}"

        # Create data directory backup
        if docker exec "$NEO4J_CONTAINER" tar -czf "/tmp/neo4j-data-$TIMESTAMP.tar.gz" /data 2>/dev/null; then
            docker cp "$NEO4J_CONTAINER:/tmp/neo4j-data-$TIMESTAMP.tar.gz" "$BACKUP_DIR/"
            docker exec "$NEO4J_CONTAINER" rm "/tmp/neo4j-data-$TIMESTAMP.tar.gz"
            log "${GREEN}✅ Docker data backup created: neo4j-data-$TIMESTAMP.tar.gz${NC}"
        else
            log "${YELLOW}⚠️  Docker data backup failed${NC}"
        fi

        # Create database dump (if neo4j-admin is available)
        if docker exec "$NEO4J_CONTAINER" which neo4j-admin > /dev/null 2>&1; then
            if docker exec "$NEO4J_CONTAINER" neo4j-admin database dump neo4j --to-path=/tmp/neo4j-dump-$TIMESTAMP.dump 2>/dev/null; then
                docker cp "$NEO4J_CONTAINER:/tmp/neo4j-dump-$TIMESTAMP.dump" "$BACKUP_DIR/"
                docker exec "$NEO4J_CONTAINER" rm "/tmp/neo4j-dump-$TIMESTAMP.dump"
                log "${GREEN}✅ Database dump created: neo4j-dump-$TIMESTAMP.dump${NC}"
            else
                log "${YELLOW}⚠️  Database dump failed${NC}"
            fi
        fi
    else
        log "${BLUE}ℹ️  No Docker container found, skipping container backup${NC}"
    fi
}

# Function to validate data integrity
validate_data_integrity() {
    log "${BLUE}🔍 Validating data integrity...${NC}"

    cd "$PROJECT_DIR"
    python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from safe_transactions import DataIntegrityValidator
from neo4j import GraphDatabase
import os

NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'neo4jtest')

try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    validator = DataIntegrityValidator(driver)

    # Get current stats
    stats = validator.get_current_stats()
    print(f'📊 Current data: {stats[\"notes\"]} notes, {stats[\"workflows\"]} workflows, {stats[\"tags\"]} tags')

    # Validate integrity
    is_healthy = validator.validate_integrity()

    # Check for emergency situations
    needs_emergency_restore = validator.emergency_restore_check()

    if needs_emergency_restore:
        print('🚨 EMERGENCY RESTORE NEEDED!')
        exit(2)
    elif not is_healthy:
        print('⚠️  Data integrity issues detected')
        exit(1)
    else:
        print('✅ Data integrity validation passed')
        exit(0)

    driver.close()

except Exception as e:
    print(f'❌ Integrity validation failed: {e}')
    exit(1)
"

    validation_result=$?
    case $validation_result in
        0)
            log "${GREEN}✅ Data integrity validation passed${NC}"
            ;;
        1)
            log "${YELLOW}⚠️  Data integrity issues detected${NC}"
            ;;
        2)
            log "${RED}🚨 EMERGENCY: Critical data loss detected!${NC}"
            log "${BLUE}💡 Run manual recovery: python3 cortex_neo/emergency_recovery.py${NC}"
            ;;
    esac
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "${BLUE}🗑️  Cleaning up old backups...${NC}"

    # Keep last 7 days of structure backups
    find "$BACKUP_DIR" -name "structure-backup-*.yaml" -mtime +7 -delete 2>/dev/null || true

    # Keep last 3 days of data backups (larger files)
    find "$BACKUP_DIR" -name "neo4j-data-*.tar.gz" -mtime +3 -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "neo4j-dump-*.dump" -mtime +3 -delete 2>/dev/null || true

    # Keep last 24 hours of auto backups
    find "$BACKUP_DIR/auto" -name "auto-backup-*.yaml" -mtime +1 -delete 2>/dev/null || true

    log "${GREEN}✅ Backup cleanup completed${NC}"
}

# Function to create backup summary
create_backup_summary() {
    log "${BLUE}📋 Creating backup summary...${NC}"

    summary_file="$BACKUP_DIR/backup-summary-$TIMESTAMP.txt"

    cat > "$summary_file" << EOF
# Cortex Backup Summary
Date: $(date)
Timestamp: $TIMESTAMP

## Backup Files Created:
$(ls -la "$BACKUP_DIR" | grep "$TIMESTAMP" | awk '{print "- " $9 " (" $5 " bytes)"}')

## Current Directory Contents:
Total backup files: $(find "$BACKUP_DIR" -type f | wc -l)
Total size: $(du -sh "$BACKUP_DIR" | cut -f1)

## Auto Backup Directory:
Auto backups: $(find "$BACKUP_DIR/auto" -type f | wc -l)
Auto backup size: $(du -sh "$BACKUP_DIR/auto" 2>/dev/null | cut -f1 || echo "0B")

## Status:
Backup process completed at: $(date)
Next scheduled backup: $(date -d "+1 day")
EOF

    log "${GREEN}✅ Backup summary created: $summary_file${NC}"
}

# Main backup execution
main() {
    log "${BLUE}🛡️  Starting Cortex Data Protection Backup${NC}"

    # Check Neo4j availability
    if ! check_neo4j; then
        log "${RED}❌ Cannot proceed without Neo4j access${NC}"
        exit 1
    fi

    # Create all backup types
    create_structure_backup
    create_docker_backup

    # Validate data integrity
    validate_data_integrity

    # Cleanup old files
    cleanup_old_backups

    # Create summary
    create_backup_summary

    log "${GREEN}✅ Backup process completed successfully!${NC}"
    log "${BLUE}📁 Backups location: $BACKUP_DIR${NC}"

    # Display summary
    echo ""
    echo -e "${GREEN}📊 Backup Summary:${NC}"
    find "$BACKUP_DIR" -name "*$TIMESTAMP*" -exec ls -lh {} \; | awk '{print "   📁 " $9 " (" $5 ")"}'
}

# Handle script interruption
trap 'log "${RED}❌ Backup interrupted${NC}"; exit 1' INT TERM

# Execute main function
main "$@"
