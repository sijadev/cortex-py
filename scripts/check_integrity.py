#!/usr/bin/env python3
"""
Cortex Data Integrity Check
Überwacht und warnt vor Datenverlust
"""

import os
import sys
import json
import subprocess
from datetime import datetime

def run_cortex_command(command):
    """Führt Cortex CLI-Befehl aus und gibt Ergebnis zurück."""
    try:
        result = subprocess.run([
            'python', 'cortex_neo/cortex_cli.py'
        ] + command.split(), 
        capture_output=True, text=True, cwd='/Users/simonjanke/Projects/cortex-py')
        return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)

def get_current_stats():
    """Holt aktuelle Datenbank-Statistiken."""
    stdout, stderr = run_cortex_command('validate-graph')
    
    if stderr:
        print(f"❌ Fehler beim Abrufen der Stats: {stderr}")
        return None
        
    try:
        # Parse die JSON-Ausgabe aus validate-graph
        lines = stdout.strip().split('\n')
        json_line = lines[-1]  # Letzte Zeile sollte JSON sein
        stats = json.loads(json_line)
        return stats
    except Exception as e:
        print(f"❌ Parsing-Fehler: {e}")
        return None

def check_data_integrity():
    """Prüft Datenintegrität und warnt vor Anomalien."""
    print("🔍 Cortex Data Integrity Check")
    print("=" * 40)
    
    # Hole aktuelle Statistiken
    current_stats = get_current_stats()
    if not current_stats:
        print("❌ Konnte aktuelle Statistiken nicht abrufen!")
        return False
        
    # Zeige aktuelle Stats
    print(f"📊 Aktuelle Datenbank:")
    print(f"   📝 Notes: {current_stats.get('notes', 0)}")
    print(f"   🏷️  Tags: {current_stats.get('orphan_tags', 0)}")
    print(f"   🔗 Links: {current_stats.get('links', 0)}")
    
    # Baseline laden (falls vorhanden)
    baseline_file = "/Users/simonjanke/Projects/cortex-py/monitoring/baseline_stats.json"
    
    if os.path.exists(baseline_file):
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
            
        print(f"\n📈 Vergleich mit Baseline:")
        print(f"   📝 Notes: {baseline.get('notes', 0)} → {current_stats.get('notes', 0)}")
        
        # Prüfe auf kritischen Datenverlust
        note_diff = current_stats.get('notes', 0) - baseline.get('notes', 0)
        
        if note_diff < -5:
            print(f"🚨 KRITISCHER DATENVERLUST: {abs(note_diff)} Notes verloren!")
            return False
        elif note_diff < -2:
            print(f"⚠️  WARNUNG: {abs(note_diff)} Notes verloren")
        elif note_diff > 0:
            print(f"✅ Positive Entwicklung: +{note_diff} Notes hinzugefügt")
    else:
        print(f"\n💡 Erstelle Baseline für zukünftige Vergleiche...")
        
    # Update/Erstelle Baseline
    os.makedirs(os.path.dirname(baseline_file), exist_ok=True)
    with open(baseline_file, 'w') as f:
        json.dump(current_stats, f, indent=2)
        
    # Minimale Datenbestand-Prüfung
    if current_stats.get('notes', 0) < 3:
        print(f"⚠️  WARNUNG: Sehr wenige Notes ({current_stats.get('notes', 0)}) - möglicherweise Datenverlust!")
        return False
        
    print(f"✅ Datenintegrität OK")
    return True

def create_emergency_backup():
    """Erstellt Notfall-Backup bei erkannten Problemen."""
    print("🆘 Erstelle Notfall-Backup...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"/Users/simonjanke/Projects/cortex-py/cortex_neo/backups/emergency-backup-{timestamp}.yaml"
    
    stdout, stderr = run_cortex_command('export-structure')
    
    if stderr:
        print(f"❌ Backup fehlgeschlagen: {stderr}")
        return False
        
    # Kopiere das exportierte File
    import shutil
    try:
        shutil.copy('/Users/simonjanke/Projects/cortex-py/export_structure.yaml', backup_file)
        print(f"✅ Notfall-Backup erstellt: {backup_file}")
        return True
    except Exception as e:
        print(f"❌ Backup-Kopie fehlgeschlagen: {e}")
        return False

if __name__ == "__main__":
    integrity_ok = check_data_integrity()
    
    if not integrity_ok:
        print(f"\n🆘 Datenintegrität kompromittiert!")
        create_emergency_backup()
        print(f"\n💡 Empfohlene Maßnahmen:")
        print(f"   1. Neueste Backup wiederherstellen")
        print(f"   2. Neo4j Container-Status prüfen") 
        print(f"   3. Logs analysieren")
        sys.exit(1)
    else:
        print(f"\n🎉 Alles in Ordnung!")
        sys.exit(0)
