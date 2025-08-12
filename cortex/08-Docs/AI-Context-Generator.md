# AI-Context-Generator

*Automatische Context-Erstellung für neue AI-Chats*

## 🎯 Quick-Export-Queries

### Für spezifisches Projekt
```dataview
TABLE status, confidence, file.ctime as "Datum"
FROM #projekt/auth-system
WHERE !contains(tags, "template")
SORT confidence DESC
LIMIT 5
```

### Hochwertige Entscheidungen
```dataview
LIST
FROM #cortex-decision 
WHERE confidence > 90
SORT confidence DESC
```

### Offene Probleme
```dataview
LIST 
FROM #problem AND #status/open
SORT file.ctime DESC
```

## 🔧 Context-Export-Tools

### Kompakt-Zusammenfassung (< 500 Tokens)
**Verwendung**: Für einfache Fragen, quick clarifications

**Template**:
```
Projekt: {{name}}
Status: {{status}} 
Hauptentscheidung: {{decision}} ({{confidence}}%)
Aktuelles Problem: {{current-issue}}
```

### Detail-Kontext (< 1500 Tokens)  
**Verwendung**: Für technische Diskussionen, Implementierungsfragen

**Enthält**:
- Projekt-Overview
- Top-3 Entscheidungen mit Reasoning
- Relevante Benchmarks
- Offene Fragen

### Full-Context (< 3000 Tokens)
**Verwendung**: Für komplexe Analysen, neue Entscheidungen

**Enthält**:
- Komplette Data-Repository-Zusammenfassung
- Alle relevanten Entscheidungen
- Benchmark-Daten
- Decision-History

## 🚀 Praktisches Vorgehen

### Vor neuem Chat:
1. **Context-Export** für relevantes Projekt erstellen
2. **Spezifischen Layer** je nach Frage wählen  
3. **Aktuelle Frage** formulieren
4. **In neuen Chat** einfügen

### Nach Chat:
1. **Erkenntnisse** in Neural-Link dokumentieren
2. **Entscheidungen** in Cortex-Decision festhalten
3. **Daten-Updates** in Repository eintragen

---
*Löst das Context-Limit-Problem durch intelligente Datenkuratierung*
