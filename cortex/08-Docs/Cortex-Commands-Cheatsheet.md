# 🚀 Cortex Commands Cheatsheet

*Sofort verfügbare Befehle für neue Claude-Sessions*

## ⚡ **SCHNELLSTART-COMMANDS**

### **System Connection Check:**
```bash
# Cortex-System testen
obsidian:search_notes → query: "cortex"
filesystem:list_directory → path: "/Users/simonjanke/Projects/cortex"

# Service Status prüfen  
super-shell:execute_command → command: "launchctl" args: ["list", "com.cortex.learning.service"]
```

### **Sofort-Navigation:**
```bash
# Hauptdokumente lesen
obsidian:read_notes → paths: ["/Cortex-Hub.md", "/Quick-Resume.md"]

# Aktueller Status
obsidian:read_notes → paths: ["/State-Management.md"]

# Commands verfügbar
obsidian:read_notes → paths: ["/commands/cortex-resume.md"]
```

## 📁 **WICHTIGE PFADE**

### **Cortex Core:**
- **Hub**: `/Cortex-Hub.md`
- **Resume**: `/Quick-Resume.md` 
- **State**: `/State-Management.md`
- **Auto-Connect**: `/Cortex-Auto-Connect.md`

### **Commands:**
- **Resume**: `/commands/cortex-resume.md`
- **Status**: `/commands/cortex-status.md`
- **Help**: `/commands/cortex-help.md`

### **System:**
- **Service Config**: `/00-System/Services/config/service_config.yaml`
- **Service Logs**: `/00-System/Services/logs/`
- **Algorithms**: `/00-System/Algorithms/`

## 🤖 **SERVICE COMMANDS**

### **Service Management:**
```bash
# Status prüfen
launchctl list com.cortex.learning.service

# Service starten
launchctl start com.cortex.learning.service

# Service stoppen  
launchctl stop com.cortex.learning.service

# Logs anzeigen
filesystem:read_text_file → path: "/Users/simonjanke/Projects/cortex/00-System/Services/logs/service_stdout.log" tail: 10
```

### **Learning Stats:**
```bash
# Aktuelle Statistiken
filesystem:read_text_file → path: "/Users/simonjanke/Projects/cortex/00-System/Services/data/learning_stats.json"
```

## 📊 **PROJEKT-NAVIGATION**

### **Aktuelle Projekte:**
```bash
obsidian:search_notes → query: "01-Projects"
filesystem:list_directory → path: "/Users/simonjanke/Projects/cortex/01-Projects"
```

### **Decisions & Neural-Links:**
```bash
obsidian:search_notes → query: "03-Decisions"
obsidian:search_notes → query: "02-Neural-Links"
```

### **Templates:**
```bash
filesystem:list_directory → path: "/Users/simonjanke/Projects/cortex/00-Templates"
```

## 🎯 **CURRENT TASK SHORTCUTS**

### **Phase 1 Implementation:**
```bash
# Aktueller Task Status
obsidian:read_notes → paths: ["/commands/cortex-resume.md"]

# Decision Context
obsidian:read_notes → paths: ["/03-Decisions/ADR-003-Projekt-Kapselung.md"]

# Template Target
filesystem:read_text_file → path: "/Users/simonjanke/Projects/cortex/00-Templates"
```

## 🔧 **TROUBLESHOOTING**

### **Connection Issues:**
```bash
# Obsidian Port Check
obsidian:search_notes → query: "test"

# Service nicht läuft
launchctl start com.cortex.learning.service

# File System Access
filesystem:list_directory → path: "/Users/simonjanke/Projects/cortex"
```

### **Service Problems:**
```bash
# Error Logs
filesystem:read_text_file → path: "/Users/simonjanke/Projects/cortex/00-System/Services/logs/service_stderr.log" tail: 10

# Service neu starten
launchctl stop com.cortex.learning.service
launchctl start com.cortex.learning.service
```

---

## 📋 **NEW SESSION CHECKLIST**

Für eine neue Claude-Session:

1. ✅ **Teste Obsidian**: `obsidian:search_notes → "cortex"`
2. ✅ **Prüfe Service**: `launchctl list com.cortex.learning.service`  
3. ✅ **Lade Context**: `obsidian:read_notes → ["/Quick-Resume.md"]`
4. ✅ **Check Status**: `obsidian:read_notes → ["/State-Management.md"]`
5. ✅ **Ready**: Alle Cortex-Befehle verfügbar

---
*Cortex Ready | Zero-Setup-Time | Alle Commands verfügbar*
