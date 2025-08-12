# Context-Export: {{project}}

*AI-Chat-Ready Zusammenfassung für {{project}}*

## 🎯 Projekt-Essentials
**Status**: {{status}}  
**Confidence-Level**: {{confidence}}  
**Key-Decision**: {{main-decision}}

## 📊 Wichtigste Daten
```dataview
TABLE confidence, tags
FROM "03-Decisions"
WHERE contains(tags, "projekt/{{project}}")
SORT confidence DESC
LIMIT 3
```

## 🔍 Letzte Erkenntnisse
```dataview
LIST
FROM "02-Neural-Links" 
WHERE contains(tags, "projekt/{{project}}")
SORT file.ctime DESC
LIMIT 2
```

## 🎪 Aktuelle Fragen
- [ ] {{question-1}}
- [ ] {{question-2}}

## 💾 Kompakt-Kontext für AI
**Projekt**: {{project}}
**Problem**: {{core-problem}}
**Gewählte-Lösung**: {{solution}} ({{confidence}}% Confidence)
**Basis-Daten**: {{data-summary}}
**Nächste-Schritte**: {{next-actions}}

---
*Generiert: {{date}} | Für AI-Context optimiert | Token-effizient*
