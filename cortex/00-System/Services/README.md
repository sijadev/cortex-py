# Cortex Learning Service - macOS Background Intelligence

Ein intelligenter macOS-Dienst für kontinuierliches Lernen und Pattern-Recognition in Ihrem Cortex-System.

## 🎯 **Was der Service macht**

### **Automatische Pattern-Erkennung**
- **Alle 30 Minuten**: Analysiert neue Cortex-Daten für wiederkehrende Muster
- **Entscheidungs-Patterns**: Erkennt erfolgreiche Decision-Making-Strategien
- **Projekt-Patterns**: Identifiziert Best-Practices zwischen Projekten
- **AI-Session-Patterns**: Optimiert AI-Interaktions-Strategien

### **Intelligente Insights**
- **Cross-Project-Learning**: Überträgt Lernerfolge zwischen Projekten
- **Success-Factor-Analysis**: Identifiziert Faktoren für Projekt-Erfolg
- **Quality-Monitoring**: Überwacht System-Health und Performance
- **Trend-Analysis**: Erkennt Performance-Trends über Zeit

### **Proaktive Benachrichtigungen**
- **High-Confidence-Patterns**: macOS-Notifications für wichtige Entdeckungen
- **Quality-Alerts**: Warnung bei System-Problemen
- **Learning-Milestones**: Benachrichtigung bei Learning-Fortschritten

## 🚀 **Installation**

### **Schritt 1: Service installieren**
```bash
cd /Users/simonjanke/Projects/cortex/00-System/Services
chmod +x install_service.sh manage_service.sh
./install_service.sh
```

### **Schritt 2: Service überprüfen**
```bash
./manage_service.sh status
```

### **Schritt 3: Logs überwachen (optional)**
```bash
./manage_service.sh logs
```

## 🔧 **Service-Management**

### **Basis-Befehle**
```bash
./manage_service.sh start      # Service starten
./manage_service.sh stop       # Service stoppen  
./manage_service.sh restart    # Service neustarten
./manage_service.sh status     # Status und Statistiken anzeigen
./manage_service.sh logs       # Live-Logs anzeigen
```

### **Konfiguration**
```bash
./manage_service.sh config     # Konfiguration bearbeiten
```

### **Deinstallation**
```bash
./manage_service.sh uninstall  # Service komplett entfernen
```

## ⚙️ **Konfiguration**

### **Haupt-Konfiguration** (`config/service_config.yaml`)
```yaml
# Lern-Verhalten
learning_interval_minutes: 30        # Wie oft Pattern-Detection läuft
pattern_detection_threshold: 0.7     # Minimum Confidence für Pattern
quality_check_interval_hours: 6      # Wie oft Quality-Checks laufen

# Benachrichtigungen  
notification_enabled: true           # macOS-Benachrichtigungen aktivieren
notify_high_confidence_patterns: true # Bei >80% Confidence benachrichtigen

# Performance
max_memory_usage_mb: 512             # Maximum RAM-Verbrauch
cpu_priority: 10                     # CPU-Priorität (niedriger = höher)
```

### **Erweiterte Regeln** (`config/learning_rules.json`)
- Pattern-Detection-Algorithmus-Parameter
- Quality-Monitoring-Thresholds
- Notification-Regeln
- Cross-Project-Learning-Einstellungen

## 📊 **Service-Features im Detail**

### **1. Pattern-Detection-Engine**
```python
# Automatische Erkennung von:
- Decision-Quality-Patterns     # Erfolgreiche Entscheidungs-Strategien
- Technology-Choice-Patterns    # Bewährte Tech-Stack-Entscheidungen  
- Project-Success-Patterns      # Erfolgs-Faktoren zwischen Projekten
- AI-Interaction-Patterns       # Optimale AI-Session-Strukturen
```

### **2. Learning-Intelligence**
```python
# Kontinuierliche Verbesserung durch:
- Confidence-Correlation-Analysis  # Confidence vs. Outcome-Tracking
- Performance-Trend-Analysis       # System-Performance über Zeit
- Success-Factor-Mining           # Was macht Projekte erfolgreich
- Meta-Learning-Optimization      # Lernt wie es besser lernen kann
```

### **3. Quality-Monitoring**
```python
# Proaktive Überwachung von:
- Link-Integrity                  # Broken-Links-Detection
- File-System-Health             # Missing-Files, Permission-Issues
- Performance-Degradation        # Slowdown-Detection
- Data-Consistency               # Metadata-Validation
```

## 🔔 **Notification-System**

### **Pattern-Discovery-Notifications**
```
🧠 Cortex: New Pattern Detected
Pattern 'Progressive-API-Complexity' detected with 85% confidence
```

### **Quality-Alert-Notifications**
```
⚠️ Cortex: Quality Alert  
Quality issue detected: 15% broken links in project references
```

### **Learning-Milestone-Notifications**
```
📈 Cortex: Learning Milestone
10 new patterns detected this month - System intelligence improved!
```

## 📁 **Generierte Dateien**

### **Auto-Detected-Patterns** (`05-Insights/Auto-Detected-*.md`)
```markdown
# Pattern: High-Confidence-Decision-Factors
*Auto-detected by Cortex Learning Service*

## Evidence
1. **benchmark_data_availability**: 85% correlation with high confidence
2. **quantitative_evidence**: 92% correlation with decision success
3. **multiple_options_considered**: Average 3.2 options improves quality
```

### **Quality-Reports** (`00-System/Services/logs/quality_report_*.json`)
```json
{
  "timestamp": "2025-08-09T15:30:00",
  "performance": {
    "avg_decision_time": "2.3 hours",
    "confidence_accuracy": "87%",
    "link_health": "94% valid"
  },
  "recommendations": [
    "Consider pattern 'Progressive-API-Complexity' for next API decision"
  ]
}
```

### **Learning-Statistics** (`00-System/Services/data/learning_stats.json`)
```json
{
  "patterns_detected": 12,
  "insights_generated": 28,
  "quality_alerts": 3,
  "uptime_hours": 168.5,
  "last_learning_cycle": "2025-08-09T15:45:00"
}
```

## 🧪 **Entwicklung & Testing**

### **Service lokal testen**
```bash
# Service im Foreground-Modus für Testing
cd /Users/simonjanke/Projects/cortex/00-System/Services
python3 cortex_learner.py
```

### **Pattern-Detection testen**
```bash
# Nur Pattern-Detection ausführen
python3 pattern_detector.py
```

### **Logs analysieren**
```bash
# Live-Logs verfolgen
tail -f logs/cortex_learning.log

# Fehler-Logs suchen
grep ERROR logs/cortex_learning.log

# Performance-Logs
grep "Learning cycle completed" logs/cortex_learning.log
```

## 🔍 **Troubleshooting**

### **Service startet nicht**
```bash
# Prüfen ob Python-Dependencies installiert sind
pip3 install schedule pyyaml --user

# Permissions prüfen
chmod +x cortex_learner.py

# LaunchAgent-Status prüfen
launchctl list | grep cortex
```

### **Keine Patterns erkannt**
```bash
# Minimum-Daten prüfen
# - Mindestens 3 ADR-Dateien für Decision-Patterns
# - Mindestens 2 Projekte für Cross-Project-Patterns  
# - Mindestens 5 Neural-Links für AI-Patterns

# Confidence-Threshold senken (in config/service_config.yaml)
pattern_detection_threshold: 0.5  # Statt 0.7
```

### **Zu viele Notifications**
```bash
# Notification-Frequenz reduzieren (in config/learning_rules.json)
"max_notifications_per_day": 2  # Statt 5
"min_confidence": 0.9          # Statt 0.8
```

### **Performance-Probleme**
```bash
# Memory-Limit reduzieren (in config/service_config.yaml)
max_memory_usage_mb: 256         # Statt 512

# Lern-Intervall erhöhen
learning_interval_minutes: 60    # Statt 30

# CPU-Priorität senken
cpu_priority: 15                 # Statt 10
```

## 📈 **Erwartete Ergebnisse**

### **Nach 1 Woche**
- 3-5 automatisch erkannte Patterns
- Erste Quality-Reports verfügbar
- Learning-Statistics zeigen Trends

### **Nach 1 Monat**
- 10-15 validierte Patterns
- Merkbare Verbesserung der Decision-Quality
- Cross-Project-Learning-Effekte sichtbar
- Proaktive Qualitäts-Warnungen

### **Nach 3 Monaten**
- 20+ hochwertige Patterns
- Deutlich schnellere Decision-Making
- Automatische Best-Practice-Suggestions
- Selbst-optimierendes Learning-System

## 🔗 **Integration mit Cortex-Workflow**

### **Dashboard-Integration**
Der Service erweitert das Performance-Dashboard automatisch:
```dataview
TABLE pattern_name, confidence, reuse_potential
FROM "05-Insights" 
WHERE contains(tags, "auto-generated")
SORT confidence DESC
```

### **Decision-Support**
Bei neuen Entscheidungen schlägt das System automatisch vor:
- Ähnliche erfolgreiche Patterns
- Relevante Best-Practices  
- Quality-Gates basierend auf Lernerfahrungen

### **Cross-Project-Learning**
Automatische Übertragung von:
- Erfolgreichen Decision-Frameworks
- Technology-Choice-Patterns
- Project-Structure-Best-Practices
- AI-Interaction-Optimizations

---

## 🎯 **Nächste Schritte**

1. **Service installieren**: `./install_service.sh`
2. **24h laufen lassen**: Erste Patterns sammeln
3. **Dashboard prüfen**: Neue Insights im Performance-Dashboard
4. **Patterns validieren**: Auto-generierte Patterns manuell überprüfen
5. **Configuration tunen**: Service-Parameter nach Bedarf anpassen

**Der Service macht Ihr Cortex-System kontinuierlich intelligenter! 🧠✨**

---
*Cortex Learning Service v1.0 | Kontinuierliche Intelligence | Auto-Learning-System*