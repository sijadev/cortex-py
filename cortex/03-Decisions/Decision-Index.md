# Decision Records Index

*Zentrale Übersicht aller Architektur- und Design-Entscheidungen*

## 🎯 Aktive Entscheidungen

```dataview
TABLE status, file.ctime as "Entschieden am"
FROM "03-Decisions"
WHERE status = "ENTSCHIEDEN"
SORT file.ctime DESC
```

## 📋 Entscheidungs-Kategorien

### 🔐 Security-Entscheidungen

- [[ADR-002-Password-Hashing]] - Argon2id für Password-Sicherheit
- **Anstehend**: MFA-Strategy, Session-Security

### 🏗️ Architektur-Entscheidungen  

- [[ADR-001-JWT-vs-Sessions]] - Hybrid Auth-Strategie
- **Anstehend**: Database-Choice, API-Design-Patterns

### 🎨 Frontend-Entscheidungen

- **Anstehend**: Framework-Choice, State-Management

### 📊 Data-Entscheidungen

- **Anstehend**: User-Schema, Analytics-Strategy

## 🔄 Entscheidungs-Pipeline

### 🤔 Zur Entscheidung (Open)

```dataview
LIST
FROM "03-Decisions"
WHERE status = "OFFEN" OR status = "DISKUSSION"
```

### ⏳ In Review

```dataview  
LIST
FROM "03-Decisions"
WHERE status = "REVIEW"
```

### ❌ Verworfene Optionen

```dataview
LIST
FROM "03-Decisions" 
WHERE status = "VERWORFEN"
```

## 📈 Decision-Metriken

- **Gesamt-Entscheidungen**: `$= dv.pages('"03-Decisions"').length`
- **Diesen Monat**: `$= dv.pages('"03-Decisions"').where(p => p.file.ctime > dv.date("2025-08-01")).length`
- **Implementiert**: `$= dv.pages('"03-Decisions"').where(p => p.status == "ENTSCHIEDEN").length`

## 🔗 Verwandte Systeme

- [[Cortex-Hub]] - Hauptnavigation
- [[Auth-System]] - Projekt-Kontext
- [[05-Insights]] - Lessons Learned aus Entscheidungen

## 📝 Decision-Templates

- [[00-Templates/ADR-Enhanced]] - Standard Architecture Decision Record
- Decision Process - Wie treffen wir Entscheidungen? (see system workflows)

---
*Aktualisiert: 2025-08-09 | Decisions: Transparent & Nachvollziehbar*
