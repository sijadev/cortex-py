# Cortex-py Cron Jobs
**Automatisierte Wartungsaufgaben für das Cortex-System**

## 📋 Verfügbare Cron Jobs

### 1. **backup_cortex.sh**
- **Zweck**: Automatische Sicherung des Cortex-Systems
- **Häufigkeit**: Empfohlen täglich um 2:00 Uhr
- **Funktion**: Erstellt Backups von Neo4j-Daten und Konfigurationen

### 2. **weekly_deep_check.sh** 
- **Zweck**: Wöchentliche Tiefenprüfung des Systems
- **Häufigkeit**: Sonntags um 3:00 Uhr
- **Funktion**: Integritätsprüfung, Performance-Analyse, Cleanup

### 3. **cortex_cron.txt**
- **Zweck**: Crontab-Konfigurationsdatei
- **Inhalt**: Vordefinierte Cron-Einträge für alle Wartungsaufgaben

## 🕒 Installation der Cron Jobs

```bash
# Crontab installieren
crontab scripts/cron/cortex_cron.txt

# Oder manuell einzelne Jobs hinzufügen:
crontab -e

# Beispiel-Einträge:
# 0 2 * * * /Users/simonjanke/Projects/cortex-py/scripts/cron/backup_cortex.sh
# 0 3 * * 0 /Users/simonjanke/Projects/cortex-py/scripts/cron/weekly_deep_check.sh
```

## 📊 Monitoring

- **Logs**: Cron Job Outputs werden in `logs/cron/` gespeichert
- **Status**: Verwende `crontab -l` um aktive Jobs zu prüfen
- **Debugging**: Prüfe `/var/log/cron` für Cron-spezifische Logs

## 🔧 Wartung

Alle Scripts sind ausführbar und enthalten entsprechende Fehlerbehandlung. Bei Problemen:

1. Prüfe Script-Berechtigungen: `chmod +x scripts/cron/*.sh`
2. Teste Scripts manuell vor Cron-Installation
3. Überwache Log-Dateien für Fehlermeldungen
