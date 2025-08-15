#!/usr/bin/env python3
"""
Safe Transaction Wrapper for Neo4j Operations
Provides robust transaction handling with automatic rollback and commit safety
"""

import time
import json
import os
import yaml
from datetime import datetime
from functools import wraps
from neo4j import GraphDatabase
import logging

# Setup logging for transaction safety
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SafeTransactionManager:
    """
    Manages safe transactions with automatic backup and rollback capabilities
    """

    def __init__(self, driver, backup_dir="backups/auto"):
        self.driver = driver
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    def safe_transaction(self, operation_name="unknown"):
        """
        Decorator for safe transaction handling with auto-backup
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create pre-operation backup
                backup_file = self._create_backup(f"pre-{operation_name}")

                with self.driver.session() as session:
                    with session.begin_transaction() as tx:
                        try:
                            # Execute the operation
                            result = func(tx, *args, **kwargs)

                            # Explicit commit
                            tx.commit()
                            logger.info(f"✅ Transaction committed successfully: {operation_name}")

                            # Create post-operation backup
                            self._create_backup(f"post-{operation_name}")

                            return result

                        except Exception as e:
                            # Automatic rollback
                            tx.rollback()
                            logger.error(
                                f"❌ Transaction rolled back due to error in {operation_name}: {e}"
                            )

                            # Offer to restore from backup
                            print(
                                f"⚠️  Operation '{operation_name}' failed. Backup available: {backup_file}"
                            )

                            raise e

            return wrapper

        return decorator

    def _create_backup(self, operation_suffix=""):
        """Creates automatic backup of current database state"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"auto-backup-{operation_suffix}-{timestamp}.yaml"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            # Export current database structure
            with self.driver.session() as session:
                # Get all nodes and relationships
                result = session.run(
                    """
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]->(m)
                    RETURN 
                        collect(distinct {
                            id: id(n),
                            labels: labels(n),
                            properties: properties(n)
                        }) as nodes,
                        collect(distinct {
                            start_id: id(startNode(r)),
                            end_id: id(endNode(r)),
                            type: type(r),
                            properties: properties(r)
                        }) as relationships
                """
                )

                data = result.single()
                backup_data = {
                    "timestamp": timestamp,
                    "operation": operation_suffix,
                    "nodes": data["nodes"] if data["nodes"][0] else [],
                    "relationships": data["relationships"] if data["relationships"][0] else [],
                }

                # Save backup
                with open(backup_path, "w", encoding="utf-8") as f:
                    yaml.dump(backup_data, f, default_flow_style=False, allow_unicode=True)

                logger.info(f"🔄 Backup created: {backup_path}")

                # Cleanup old backups (keep last 10)
                self._cleanup_old_backups()

                return backup_path

        except Exception as e:
            logger.error(f"⚠️ Backup creation failed: {e}")
            return None

    def _cleanup_old_backups(self, keep_count=10):
        """Remove old backup files, keeping only the most recent ones"""
        try:
            backup_files = [
                f
                for f in os.listdir(self.backup_dir)
                if f.startswith("auto-backup-") and f.endswith(".yaml")
            ]

            # Sort by modification time (newest first)
            backup_files.sort(
                key=lambda x: os.path.getmtime(os.path.join(self.backup_dir, x)), reverse=True
            )

            # Remove files beyond keep_count
            for old_file in backup_files[keep_count:]:
                os.remove(os.path.join(self.backup_dir, old_file))
                logger.info(f"🗑️ Removed old backup: {old_file}")

        except Exception as e:
            logger.error(f"⚠️ Backup cleanup failed: {e}")


class DataIntegrityValidator:
    """
    Validates data integrity and detects anomalies
    """

    def __init__(self, driver, baseline_file="monitoring/baseline_stats.json"):
        self.driver = driver
        self.baseline_file = baseline_file
        os.makedirs(os.path.dirname(baseline_file), exist_ok=True)

    def get_current_stats(self):
        """Get current database statistics"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n:Note) 
                OPTIONAL MATCH (t:Tag)
                OPTIONAL MATCH (w:Workflow)
                OPTIONAL MATCH ()-[r:LINKS_TO]->()
                OPTIONAL MATCH ()-[r2:HAS_STEP]->()
                RETURN 
                    count(distinct n) as notes,
                    count(distinct t) as tags,
                    count(distinct w) as workflows,
                    count(r) as note_links,
                    count(r2) as workflow_links,
                    timestamp() as check_time
            """
            ).single()

            return {
                "notes": result["notes"],
                "tags": result["tags"],
                "workflows": result["workflows"],
                "note_links": result["note_links"],
                "workflow_links": result["workflow_links"],
                "check_time": result["check_time"],
                "timestamp": datetime.now().isoformat(),
            }

    def validate_integrity(self, alert_threshold=5):
        """
        Validate data integrity against baseline
        Returns True if data looks healthy, False if critical issues detected
        """
        try:
            current_stats = self.get_current_stats()

            # Load baseline if exists
            if os.path.exists(self.baseline_file):
                with open(self.baseline_file, "r") as f:
                    baseline = json.load(f)

                # Check for critical data loss
                note_diff = current_stats["notes"] - baseline["notes"]
                workflow_diff = current_stats["workflows"] - baseline["workflows"]

                # Critical alerts
                if current_stats["notes"] == 0 and baseline["notes"] > 0:
                    print("🚨 KRITISCHER DATENVERLUST: Alle Notes verschwunden!")
                    return False

                if note_diff < -alert_threshold:
                    print(f"🚨 WARNUNG: {abs(note_diff)} Notes verloren seit letzter Prüfung!")
                    return False

                if workflow_diff < -3:
                    print(f"⚠️ WARNUNG: {abs(workflow_diff)} Workflows verloren!")

            # Update baseline
            with open(self.baseline_file, "w") as f:
                json.dump(current_stats, f, indent=2)

            print(
                f"📊 Datenbestand: {current_stats['notes']} Notes, {current_stats['workflows']} Workflows, {current_stats['tags']} Tags"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Integrity validation failed: {e}")
            return False

    def emergency_restore_check(self):
        """Check if emergency restore is needed and suggest actions"""
        current_stats = self.get_current_stats()

        if current_stats["notes"] == 0:
            print("🚨 NOTFALL: Keine Notes gefunden!")
            print("💡 Verfügbare Wiederherstellungsoptionen:")

            # List available backups
            backup_dir = "backups/auto"
            if os.path.exists(backup_dir):
                backups = [f for f in os.listdir(backup_dir) if f.endswith(".yaml")]
                backups.sort(reverse=True)  # Newest first

                print(f"   📁 {len(backups)} automatische Backups verfügbar")
                for i, backup in enumerate(backups[:5]):  # Show last 5
                    print(f"   {i+1}. {backup}")

            # Check for baseline backup
            baseline_backup = "backups/neo4j-default-backup-snapshot.tar.gz"
            if os.path.exists(baseline_backup):
                print(f"   📁 Baseline-Backup verfügbar: {baseline_backup}")

            return True

        return False
