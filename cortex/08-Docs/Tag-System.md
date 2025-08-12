# Tag-System

*Zentrale Dokumentation aller Tag-Konventionen in Cortex*

## Hierarchische Tag-Struktur

### Projekt-Tags
```
#projekt/[projektname]
#projekt/auth-system     ← [[Auth-System]]
#projekt/user-dashboard
#projekt/api-redesign
```

### Status-Tags
```
#status/planning      ← Ideenfindung, Konzeption
#status/development   ← Aktive Entwicklung
#status/testing      ← Code-Review, Testing
#status/implemented  ← Live/Produktiv
#status/blocked      ← Wartet auf externe Abhängigkeiten
#status/deprecated   ← Nicht mehr relevant
```

### Technologie-Tags
```
#tech/frontend    ← React, Vue, HTML/CSS
#tech/backend     ← Python, Node.js, APIs
#tech/database    ← SQL, NoSQL, Schemas
#tech/security    ← Auth, Encryption, Compliance
#tech/devops      ← Docker, CI/CD, Deployment
```

### Cortex-System-Tags
```
#cortex-generated     ← Von AI erstellt
#cortex-reviewed      ← Human-reviewed
#needs-human-review   ← Braucht Überprüfung
#neural-export        ← Für AI-Kontext vorbereitet
#prompt-template      ← Wiederverwendbare Prompts
```

### Problem/Lösung-Tags
```
#problem/performance  ← Performance-Issues
#problem/security     ← Sicherheitsprobleme  
#problem/architecture ← Design-Probleme
#solution/caching     ← Cache-Lösungen
#solution/refactoring ← Code-Verbesserungen
#question/open        ← Offene Fragen
#question/resolved    ← Gelöste Fragen
```

## Tag-Kombinationen (Best Practices)

### Für Projekte:
```
#projekt/auth-system #tech/backend #tech/security #status/development
```

### Für Neural-Links:
```
#neural-export #cortex-generated #projekt/auth-system
```

### Für Code-Fragments:
```
#cortex-generated #tech/python #projekt/auth-system #solution/caching
```

## Verwandte Seiten
- [[Cortex-Hub]] - Hauptnavigation
- [[00-Templates/New Project]] - Projekt-Template mit Tags
- [[00-Templates/Cortex Neural-Link]] - Neural-Link Template

---
*Aktualisiert: 2025-08-09*
