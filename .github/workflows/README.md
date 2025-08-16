# 🚀 Cortex GitHub Workflows - Funktionale Restrukturierung

## Übersicht der neuen Workflow-Architektur

Die GitHub Workflows wurden vollständig nach ihren spezifischen Funktionen restrukturiert, um bessere Modularität, Parallelisierung und Wartbarkeit zu erreichen.

## 📁 Workflow-Dateien und ihre Funktionen

### 1. 🧪 **smoke-tests.yml** - Schnelle Basis-Validierung
- **Zweck**: Schnelle Überprüfung der Grundfunktionalität
- **Trigger**: Push auf alle Branches, PRs, manuell
- **Laufzeit**: ~10 Minuten
- **Features**:
  - Minimal Setup für schnelle Ausführung
  - Basis-Systemvalidierung
  - Sofortige Fehlererkennung bei kritischen Problemen

### 2. 🔬 **unit-tests.yml** - Code-Qualität und Coverage
- **Zweck**: Unit Tests mit Coverage-Analyse
- **Trigger**: Push auf main/develop, PRs
- **Laufzeit**: ~20 Minuten
- **Features**:
  - Coverage-Reporting mit Codecov Integration
  - Konfigurierbare Coverage-Schwellenwerte
  - Automatische PR-Kommentare für Coverage
  - HTML und XML Coverage Reports

### 3. 🔗 **integration-tests.yml** - Neo4j & System Integration
- **Zweck**: Integration Tests mit echter Neo4j Datenbank
- **Trigger**: Push auf main/develop, PRs, täglich
- **Laufzeit**: ~30 Minuten
- **Features**:
  - Neo4j 5.11 Service Container
  - APOC Plugin Support
  - Datenbank-Gesundheitsprüfungen
  - Vollständige System-Integration Tests

### 4. ⚡ **cli-tests.yml** - Cortex CLI Funktionalität
- **Zweck**: Tests der Cortex CLI Komponenten
- **Trigger**: Push auf CLI-relevante Pfade, PRs
- **Laufzeit**: ~20 Minuten
- **Features**:
  - CLI Installation Tests
  - Cross-Platform Testing (Ubuntu, macOS)
  - Multi-Python Version Support (3.9, 3.11, 3.12)
  - CLI Command Validation

### 5. 🤖 **mcp-tests.yml** - Model Context Protocol
- **Zweck**: MCP System Validierung
- **Trigger**: Push auf MCP-relevante Pfade, PRs
- **Laufzeit**: ~15 Minuten
- **Features**:
  - MCP Konfiguration Validierung
  - Claude Desktop Config Check
  - Debug Script Testing
  - JSON Configuration Validation

### 6. 🔒 **security-quality.yml** - Sicherheit und Code-Qualität
- **Zweck**: Sicherheitsanalyse und Code-Qualität
- **Trigger**: Push auf main/develop, PRs, wöchentlich
- **Laufzeit**: ~15 Minuten
- **Features**:
  - Bandit Security Scanning
  - Safety Vulnerability Checks
  - Semgrep Security Analysis
  - Code Quality Tools (Black, isort, Flake8, MyPy, Pylint)

### 7. 🚀 **release.yml** - Release & Deployment
- **Zweck**: Automatisierte Release-Erstellung
- **Trigger**: Git Tags, Releases, manuell
- **Laufzeit**: ~30 Minuten
- **Features**:
  - Automatische Versionierung
  - Package Building und Validierung
  - GitHub Release Creation
  - Artifact Management

### 8. 🎯 **ci-pipeline.yml** - Vollständige CI Pipeline
- **Zweck**: Orchestrierung aller Tests
- **Trigger**: Push auf main, PRs, täglich
- **Laufzeit**: ~60 Minuten (parallelisiert)
- **Features**:
  - Koordination aller Test-Workflows
  - Intelligente Job-Abhängigkeiten
  - Comprehensive Status Reporting
  - Parallel Execution wo möglich

### 9. ⚡ **quick-test.yml** - Schnelle Entwicklungszyklen
- **Zweck**: Schnelle Tests für Feature-Branches
- **Trigger**: Push auf feature/*/bugfix/*/hotfix/* Branches
- **Laufzeit**: ~8 Minuten
- **Features**:
  - Minimal Setup für Geschwindigkeit
  - Syntax und Import Checks
  - Konfigurierbare Test-Level
  - Shallow Git Clones

## 🔄 Workflow-Abhängigkeiten und Orchestrierung

```
ci-pipeline.yml (Haupt-Orchestrator)
├── smoke-tests.yml (Basis-Validierung)
├── unit-tests.yml (nach smoke-tests)
├── integration-tests.yml (nach unit-tests)
├── cli-tests.yml (parallel zu unit-tests)
├── mcp-tests.yml (parallel zu unit-tests)
└── security-quality.yml (für main/PRs)
```

## 🎯 Trigger-Strategien

### Für Entwicklung (Feature Branches):
- **quick-test.yml**: Sofortige Validierung
- **smoke-tests.yml**: Basis-Funktionalität

### Für Pull Requests:
- **ci-pipeline.yml**: Vollständige Test-Suite
- **security-quality.yml**: Sicherheits-Analyse

### Für Main Branch:
- **ci-pipeline.yml**: Vollständige Validierung
- **integration-tests.yml**: Täglich
- **security-quality.yml**: Wöchentlich

### Für Releases:
- **release.yml**: Automatische Release-Erstellung

## 🚀 Vorteile der neuen Struktur

1. **Modularität**: Jeder Workflow hat einen klaren, spezifischen Zweck
2. **Parallelisierung**: Unabhängige Tests laufen parallel
3. **Effizienz**: Entwickler können spezifische Tests gezielt ausführen
4. **Wartbarkeit**: Einfachere Wartung und Debugging
5. **Skalierbarkeit**: Neue Test-Kategorien können einfach hinzugefügt werden
6. **Feedback-Geschwindigkeit**: Schnelle Tests geben sofortiges Feedback

## 📊 Empfohlene Nutzung

- **Während Entwicklung**: `quick-test.yml` für schnelles Feedback
- **Vor Pull Request**: `ci-pipeline.yml` für vollständige Validierung
- **Spezifische Tests**: Individuelle Workflows nach Bedarf
- **Release-Vorbereitung**: `release.yml` für Deployment

## 🔧 Migration von der alten test.yml

Die alte monolithische `test.yml` wurde durch einen Migrations-Hinweis ersetzt und ist nun deprecated. Alle Funktionalität wurde auf die neuen spezifischen Workflows aufgeteilt.

## 🎉 Nächste Schritte

1. **Validierung**: Tests der neuen Workflows
2. **Dokumentation**: Team-Schulung zur neuen Struktur  
3. **Überwachung**: Performance-Monitoring der Workflows
4. **Optimierung**: Weitere Verbesserungen basierend auf Feedback
