#!/usr/bin/env python3
"""
Safe Transactions Manager für Cortex Neo4j System
Erstellt: 2025-08-15
Zweck: Sichere Neo4j-Transaktionen mit automatischen Backups
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Callable
from functools import wraps
import yaml

logger = logging.getLogger(__name__)

class SafeTransactionManager:
    """
    Manager für sichere Neo4j-Transaktionen mit automatischen Backups
    """

    def __init__(self, driver, backup_dir: str = "cortex_neo/backups/auto"):
        self.driver = driver
        self.backup_dir = backup_dir
        self.ensure_backup_dir()

    def ensure_backup_dir(self):
        """Stelle sicher, dass das Backup-Verzeichnis existiert"""
        os.makedirs(self.backup_dir, exist_ok=True)

    def _create_backup(self, operation_name: str = None) -> str:
        """Erstellt ein Backup vor der Operation"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{operation_name}_{timestamp}.yaml" if operation_name else f"backup_{timestamp}.yaml"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        try:
            with self.driver.session() as session:
                # Sichere alle Daten
                backup_data = {
                    'timestamp': timestamp,
                    'operation': operation_name,
                    'nodes': {},
                    'relationships': []
                }

                # Sichere alle Nodes
                node_types = ['Note', 'Workflow', 'Step', 'Tag', 'Template']
                for node_type in node_types:
                    result = session.run(f"MATCH (n:{node_type}) RETURN n")
                    backup_data['nodes'][node_type] = []
                    for record in result:
                        node = dict(record['n'])
                        backup_data['nodes'][node_type].append(node)

                # Sichere alle Relationships
                result = session.run("""
                    MATCH (a)-[r]->(b) 
                    RETURN type(r) as rel_type, 
                           labels(a) as source_labels, 
                           a.name as source_name,
                           labels(b) as target_labels,
                           b.name as target_name,
                           properties(r) as rel_props
                """)

                for record in result:
                    backup_data['relationships'].append({
                        'type': record['rel_type'],
                        'source_labels': record['source_labels'],
                        'source_name': record['source_name'],
                        'target_labels': record['target_labels'],
                        'target_name': record['target_name'],
                        'properties': dict(record['rel_props']) if record['rel_props'] else {}
                    })

                # Schreibe Backup
                with open(backup_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(backup_data, f, allow_unicode=True, default_flow_style=False)

                logger.info(f"Backup created: {backup_path}")
                return backup_path

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return ""

    def safe_transaction(self, operation_name: str):
        """Decorator für sichere Transaktionen mit automatischem Backup"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Erstelle Backup vor der Operation
                backup_path = self._create_backup(operation_name)

                try:
                    with self.driver.session() as session:
                        with session.begin_transaction() as tx:
                            result = func(tx, *args, **kwargs)
                            # Transaction wird automatisch committed
                            logger.info(f"Transaction '{operation_name}' completed successfully")
                            return result

                except Exception as e:
                    logger.error(f"Transaction '{operation_name}' failed: {e}")
                    logger.error(f"Backup available at: {backup_path}")
                    raise e

            return wrapper
        return decorator


class DataIntegrityValidator:
    """
    Validator für Datenintegrität und Anomalie-Detection
    """

    def __init__(self, driver, baseline_file: str = "monitoring/baseline_stats.json"):
        self.driver = driver
        self.baseline_file = baseline_file
        self.ensure_baseline_dir()

    def ensure_baseline_dir(self):
        """Stelle sicher, dass das Monitoring-Verzeichnis existiert"""
        baseline_dir = os.path.dirname(self.baseline_file)
        if baseline_dir:
            os.makedirs(baseline_dir, exist_ok=True)

    def get_current_stats(self) -> Dict[str, Any]:
        """Sammelt aktuelle Datenbank-Statistiken"""
        try:
            with self.driver.session() as session:
                stats = {}

                # Node counts
                for node_type in ['Note', 'Workflow', 'Step', 'Tag', 'Template']:
                    result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count").single()
                    stats[node_type.lower() + 's'] = result['count'] if result else 0

                # Relationship counts
                rel_result = session.run("""
                    MATCH ()-[r:LINKS_TO]->() RETURN count(r) as note_links
                    UNION ALL
                    MATCH ()-[r:HAS_STEP]->() RETURN count(r) as workflow_links
                    UNION ALL
                    MATCH ()-[r:TAGGED_WITH]->() RETURN count(r) as tag_links
                    UNION ALL  
                    MATCH ()-[r:USES_TEMPLATE]->() RETURN count(r) as template_links
                """)

                stats['note_links'] = 0
                stats['workflow_links'] = 0
                stats['tag_links'] = 0
                stats['template_links'] = 0

                for record in rel_result:
                    for key, value in record.items():
                        if key in stats:
                            stats[key] = value

                # Health metrics
                stats['timestamp'] = datetime.now().isoformat()
                stats['total_nodes'] = sum(v for k, v in stats.items() if k.endswith('s') and k != 'links')
                stats['total_relationships'] = sum(v for k, v in stats.items() if k.endswith('_links'))

                return stats

        except Exception as e:
            logger.error(f"Failed to collect current stats: {e}")
            return {}

    def save_baseline(self):
        """Speichert aktuelle Statistiken als Baseline"""
        stats = self.get_current_stats()
        try:
            with open(self.baseline_file, 'w') as f:
                json.dump(stats, f, indent=2)
            logger.info(f"Baseline saved to {self.baseline_file}")
        except Exception as e:
            logger.error(f"Failed to save baseline: {e}")

    def load_baseline(self) -> Dict[str, Any]:
        """Lädt Baseline-Statistiken"""
        try:
            if os.path.exists(self.baseline_file):
                with open(self.baseline_file, 'r') as f:
                    return json.load(f)
            else:
                # Erstelle neue Baseline wenn keine existiert
                logger.info("No baseline found, creating new one...")
                self.save_baseline()
                return self.get_current_stats()
        except Exception as e:
            logger.error(f"Failed to load baseline: {e}")
            return {}

    def validate_integrity(self) -> bool:
        """Validiert Datenintegrität gegen Baseline"""
        try:
            current = self.get_current_stats()
            baseline = self.load_baseline()

            if not baseline:
                logger.warning("No baseline available for comparison")
                return True

            issues = []

            # Überprüfe auf signifikante Änderungen
            for key in ['notes', 'workflows', 'tags', 'templates']:
                current_val = current.get(key, 0)
                baseline_val = baseline.get(key, 0)

                if baseline_val > 0:
                    change_pct = abs(current_val - baseline_val) / baseline_val
                    if change_pct > 0.5:  # Mehr als 50% Änderung
                        issues.append(f"{key}: {baseline_val} -> {current_val} ({change_pct:.1%} change)")

            # Überprüfe auf verwaiste Daten
            orphan_checks = self._check_orphaned_data()
            issues.extend(orphan_checks)

            if issues:
                logger.warning(f"Data integrity issues found: {issues}")
                return False

            logger.info("Data integrity validation passed")
            return True

        except Exception as e:
            logger.error(f"Integrity validation failed: {e}")
            return False

    def _check_orphaned_data(self) -> List[str]:
        """Überprüft auf verwaiste Daten"""
        issues = []

        try:
            with self.driver.session() as session:
                # Verwaiste Tags (ohne Notes)
                result = session.run("""
                    MATCH (t:Tag)
                    WHERE NOT EXISTS((:Note)-[:TAGGED_WITH]->(t))
                    RETURN count(t) as orphaned_tags
                """).single()

                if result and result['orphaned_tags'] > 0:
                    issues.append(f"Found {result['orphaned_tags']} orphaned tags")

                # Verwaiste Templates
                result = session.run("""
                    MATCH (t:Template)
                    WHERE NOT EXISTS((:Note)-[:USES_TEMPLATE]->(t))
                    RETURN count(t) as orphaned_templates
                """).single()

                if result and result['orphaned_templates'] > 0:
                    issues.append(f"Found {result['orphaned_templates']} orphaned templates")

        except Exception as e:
            logger.error(f"Orphaned data check failed: {e}")
            issues.append("Could not check for orphaned data")

        return issues

    def emergency_restore_check(self) -> bool:
        """Überprüft ob ein Notfall-Restore nötig ist (kritischer Datenverlust)"""
        try:
            current = self.get_current_stats()
            baseline = self.load_baseline()

            # Kritische Schwellenwerte
            critical_loss_threshold = 0.8  # 80% Datenverlust

            for key in ['notes', 'workflows']:
                current_val = current.get(key, 0)
                baseline_val = baseline.get(key, 0)

                if baseline_val > 5:  # Nur wenn relevante Datenmenge vorhanden war
                    loss_pct = 1 - (current_val / baseline_val) if baseline_val > 0 else 0
                    if loss_pct > critical_loss_threshold:
                        logger.critical(f"CRITICAL DATA LOSS DETECTED: {key} - {loss_pct:.1%} loss")
                        return True

            return False

        except Exception as e:
            logger.error(f"Emergency restore check failed: {e}")
            return True  # Vorsichtshalber True zurückgeben bei Fehlern


# Utility functions
def ensure_safe_environment():
    """Stellt sicher, dass die sichere Umgebung initialisiert ist"""
    directories = [
        "cortex_neo/backups/auto",
        "cortex_neo/backups/pre",
        "cortex_neo/monitoring",
        "logs/safety"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # Erstelle Standard-Konfiguration wenn nicht vorhanden
    config_path = "cortex_neo/safety_config.yaml"
    if not os.path.exists(config_path):
        default_config = {
            'safety': {
                'auto_backup': True,
                'backup_retention_days': 30,
                'auto_restore_on_critical': False,
                'integrity_check_interval': 3600
            },
            'monitoring': {
                'baseline_update_interval': 86400,
                'alert_thresholds': {
                    'data_loss_pct': 0.1,
                    'orphaned_data_count': 10
                }
            }
        }

        with open(config_path, 'w') as f:
            yaml.safe_dump(default_config, f, default_flow_style=False)

        logger.info(f"Created default safety config: {config_path}")

if __name__ == "__main__":
    # Test und Setup
    ensure_safe_environment()
    print("✅ Safe transactions module initialized successfully")
