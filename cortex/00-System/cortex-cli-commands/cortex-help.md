# Cortex Commands - Übersicht

*Alle verfügbaren Befehle für Claude Desktop Integration*

## 🚀 **HAUPT-BEFEHLE**

### **`/cortex`** - Vollzugriff
- **Zweck**: Lädt komplettes Cortex-System mit vollem Context
- **Verwendet**: Cortex-Hub + State-Management + aktueller Status
- **Wann**: Für komplexe Aufgaben, neue Projekte, System-Änderungen

### **`/cortex-resume`** - Session-Fortsetzung  
- **Zweck**: Zero-Context-Loss Resume, sofort implementation-ready
- **Verwendet**: Quick-Resume + State-Management (current task)
- **Wann**: Nach Chat-Unterbrechung, um direkt weiterzumachen

### **`/cortex-status`** - Status-Check
- **Zweck**: Quick-Overview ohne Full-Context-Load
- **Verwendet**: State-Management (progress section only)
- **Wann**: Für schnelle Updates, Progress-Checks

## 🔧 **WORKFLOW-BEFEHLE**

### **`/cortex-decide [topic]`** - Neue Entscheidung
- **Zweck**: Startet vollständigen Cortex v2.0 Decision-Workflow
- **Workflow**: Data-Repository → Neural-Link → Confidence → ADR
- **Wann**: Für neue technische/architektonische Entscheidungen

### **`/cortex-templates`** - Template-Zugriff
- **Zweck**: Zeigt verfügbare Templates und deren Verwendung
- **Pfad**: `/00-Templates/` directory
- **Wann**: Für neue Dokumente, Standards-Setup

### **`/cortex-dashboard`** - Performance-Monitoring
- **Zweck**: Real-time System-Health und Metrics
- **Datei**: `00-System/Dashboards/Performance-Dashboard.md`
- **Wann**: Für System-Health-Checks, Performance-Analysis

## 📁 **DIREKT-ZUGRIFF**

### **Haupt-Navigation:**
- `/cortex-hub` → `Cortex-Hub.md` (central navigation)
- `/cortex-state` → `State-Management.md` (complete session-state)
- `/cortex-quick` → `Quick-Resume.md` (copy-paste resume-context)

### **System-Komponenten:**
- `/cortex-algorithm` → `00-System/Algorithms/confidence_calculator.py`
- `/cortex-decisions` → `03-Decisions/` (all ADRs)
- `/cortex-projects` → `01-Projects/` (active repositories)

## 🎯 **USAGE-PATTERNS**

### **Neuer Chat starten:**
```
1. "/cortex-resume" → Sofort arbeitsfähig
2. Direkte Implementation ohne Research
```

### **Neue Entscheidung treffen:**
```
1. "/cortex-decide [topic]" → Workflow starten
2. Cortex führt durch Data → Analysis → Decision
```

### **System-Check:**
```
1. "/cortex-status" → Quick-Health-Check
2. Zeigt Progress und nächste Actions
```

### **Vollständiger System-Zugriff:**
```  
1. "/cortex" → Kompletter Context
2. Für komplexe System-Änderungen
```

## 📋 **Claude Desktop Integration**

### **File-Access-Pattern:**
```markdown
Wenn User schreibt: "/cortex-resume"
→ Claude lädt: commands/cortex-resume.md
→ Sofort implementation-ready ohne weitere Context-Requests
```

### **Context-Loading-Strategy:**
- **Quick-Commands**: Verwenden vorbereitete command-files
- **Full-Context**: Laden relevante Cortex-files nach Bedarf
- **Zero-Setup**: Keine manuelle File-Navigation nötig

### **Integration-Benefits:**
- ✅ Sofortiger Zugriff auf Cortex-System
- ✅ Keine Zeit-Verschwendung mit Context-Rebuilding  
- ✅ Standardisierte Workflows für wiederkehrende Tasks
- ✅ Session-continuity auch bei Chat-Limits

---
**Tipp**: Starte immer mit `/cortex-resume` nach Unterbrechungen  
**Hilfe**: Diese Datei mit `/cortex-help` jederzeit abrufen

---
*Cortex Desktop-Integration | Efficient-Workflows | Zero-Setup-Time*