# 🆘 Cortex Emergency Recovery Guide

## Situationen und Lösungen

### 🚨 **SZENARIO 1: Kompletter Datenverlust**
**Symptome:** validate-graph zeigt 0 Notes
**Sofortmaßnahmen:**
```bash
cd /Users/simonjanke/Projects/cortex-py

# 1. Prüfe Container-Status
docker ps | grep neo4j

# 2. Prüfe verfügbare Backups
ls -la cortex_neo/backups/*.yaml | head -5

# 3. Stelle neuestes Backup wieder her
python cortex_neo/cortex_cli.py import-project cortex_neo/backups/[NEUESTES_BACKUP].yaml

# 4. Validiere Wiederherstellung
python cortex_neo/cortex_cli.py validate-graph
```

### ⚠️ **SZENARIO 2: Partielle Datenverlust**
**Symptome:** Weniger Notes als erwartet
**Diagnostik:**
```bash
# 1. Führe Integrity-Check aus
python3 check_integrity.py

# 2. Vergleiche mit letztem Export
diff export_structure.yaml cortex_neo/backups/[LETZTES_BACKUP].yaml

# 3. Selective Restore falls nötig
```

### 🔧 **SZENARIO 3: Container-Probleme**
**Symptome:** Connection-Fehler zu Neo4j
**Lösung:**
```bash
# 1. Container neu starten
cd /Users/simonjanke/Projects/cortex-py/cortex_neo
docker-compose down
docker-compose up -d

# 2. Warte auf Startup (30 Sekunden)
sleep 30

# 3. Teste Verbindung
python cortex_cli.py validate-graph
```

### 📊 **SZENARIO 4: Korrupte Datenbank**
**Symptome:** Inconsistente Daten, Errors bei Queries
**Recovery:**
```bash
# 1. Stop Container
docker-compose down

# 2. Backup der korrupten Daten
mv neo4j_data neo4j_data_corrupt_$(date +%Y%m%d)

# 3. Fresh Neo4j Start
docker-compose up -d

# 4. Restore aus Backup
python cortex_cli.py import-project cortex_neo/backups/[LETZTES_GUTES_BACKUP].yaml
```

## 🔍 **Diagnostik-Commands**

### Schnelle Gesundheitsprüfung:
```bash
# 1. Container-Status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Datenbestand
python cortex_neo/cortex_cli.py validate-graph

# 3. Backup-Verfügbarkeit
ls -la cortex_neo/backups/ | wc -l

# 4. Log-Analyse
docker logs neo4j | tail -20
```

### Detaillierte Analyse:
```bash
# 1. Führe Weekly Deep Check aus
./weekly_deep_check.sh

# 2. Integrity Check mit Baseline
python3 check_integrity.py

# 3. Link-Validierung
python cortex_neo/cortex_cli.py link-validate-ai
```

## 📞 **Escalation-Plan**

### Level 1: Selbst-Recovery (0-15 Min)
- Neuestes Backup wiederherstellen
- Container neu starten
- Integrity-Check ausführen

### Level 2: Deep Recovery (15-60 Min)
- Container-Logs analysieren
- Multiple Backups testen
- Manuelle Daten-Rekonstruktion

### Level 3: Expert Recovery (>60 Min)
- Neo4j-Experten kontaktieren
- Docker-Infrastruktur analysieren
- Custom Recovery-Scripts entwickeln

## 📋 **Recovery-Checkliste**

### Vor Recovery:
- [ ] Aktuellen Zustand dokumentieren
- [ ] Error-Logs sammeln
- [ ] Container-Status prüfen
- [ ] Backup-Verfügbarkeit validieren

### Während Recovery:
- [ ] Jeden Schritt dokumentieren
- [ ] Zwischenstände testen
- [ ] Nicht mehrere Methoden parallel
- [ ] Bei Unsicherheit stoppen

### Nach Recovery:
- [ ] Vollständigen Integrity-Check
- [ ] Neues Backup erstellen
- [ ] Root-Cause-Analyse
- [ ] Präventive Maßnahmen ableiten

## 🛡️ **Vorbeugende Wartung**

### Tägliche Routine:
```bash
# Morgens (5 Min)
python3 check_integrity.py && echo "✅ System OK"
```

### Wöchentliche Routine:
```bash
# Sonntags (15 Min)
./weekly_deep_check.sh
./backup_cortex.sh
```

### Monatliche Routine:
```bash
# Backup-Cleanup
find cortex_neo/backups -name "*.yaml" -mtime +30 -delete

# Recovery-Test
# (Restore oldest backup in test-environment)
```

## 📱 **Notfall-Kontakte**

- **Neo4j Support:** https://neo4j.com/support/
- **Docker Issues:** https://docs.docker.com/
- **Python Neo4j Driver:** https://neo4j.com/docs/python-manual/

## 🎯 **Success-Kriterien**

Recovery ist erfolgreich wenn:
- [ ] validate-graph zeigt erwartete Anzahl Notes (≥5)
- [ ] Alle wichtigen Notes vorhanden
- [ ] Links funktionieren
- [ ] Neue Notes können erstellt werden
- [ ] Backup-System funktioniert

---
**💡 Tipp:** Dieser Guide sollte immer griffbereit sein. Bei Panik: STOP → BREATHE → BACKUP → RECOVER**
