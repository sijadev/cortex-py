# Klassen-Metriken (automatisch generiert)

Stand: 12.08.2025

## Kurzfazit

- Größte Klasse: RuleBasedLinker (410 LOC), zweitgrößte: CrossVaultLinker (317 LOC)
- Höchste maximale Komplexität: CrossVaultLinker (11), knapp gefolgt von RuleBasedLinker (10)
- Methodenanzahl: RuleBasedLinker (16) > CrossVaultLinker (14); kaum private Methoden (1 je Klasse)
- Alle Klassen mit Docstrings (4/4)

## Top-Kennzahlen

| Kategorie | Klasse(n) | Wert |
|---|---|---|
| Größte Klasse (LOC) | RuleBasedLinker | 410 |
| Höchste max. Komplexität | CrossVaultLinker | 11 |
| Meiste Methoden | RuleBasedLinker | 16 |
| ⌀ Komplexität (höchste) | RuleBasedLinker | 5.25 |
| Docstrings vorhanden | Alle | 4/4 ✅ |
| Public/Private gesamt | Alle | 28/2 |

## Details je Klasse

| Klasse | Datei | LOC | Methoden | pub/prv | static | class | ⌀ LOC/Meth | ⌀ Kompl. | max Kompl. | Attrs (class/instance) | Doku |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| LinkRule | cortex-cli/cortex/core/rule_based_linker.py | 9 | 0 | 0/0 | 0 | 0 | 0.0 | 0.0 | 0 | action,description,enabled,name,strength,target,trigger / - | ✅ |
| LinkMatch | cortex-cli/cortex/core/rule_based_linker.py | 8 | 0 | 0/0 | 0 | 0 | 0.0 | 0.0 | 0 | action,reason,rule_name,source_file,strength,target_file / - | ✅ |
| RuleBasedLinker | cortex-cli/cortex/core/rule_based_linker.py | 410 | 16 | 15/1 | 0 | 0 | 24.5 | 5.25 | 10 | - / config,cortex_path,file_cache,logger,rules,rules_file,tag_cache | ✅ |
| CrossVaultLinker | cortex-cli/cortex/core/cross_vault_linker.py | 317 | 14 | 13/1 | 0 | 0 | 21.5 | 5.0 | 11 | - / cache_path,data_path,link_suggestions,logs_path,tag_suggestions,vault_connections,vault_registry,workspace_path | ✅ |

## Hinweise

- LOC und Komplexität sind AST-basierte Näherungen; sie dienen als Trend-/Vergleichswerte.
- Komplexität > 10 deutet auf Kandidaten für Zerlegung oder Vereinfachung hin (CrossVaultLinker max 11, RuleBasedLinker max 10).

## Empfehlungen (leichtgewichtig)

- RuleBasedLinker: Split in Teilkomponenten (z. B. RuleIO, Matcher, MarkdownUpdater) zur Senkung der Komplexität und besseren Testbarkeit.
- CrossVaultLinker: Heuristiken/Parser modularisieren; gezielte Unit-Tests für komplexeste Methoden.
- Fortlaufend messen (Skript erneut ausführen) und Grenzwerte definieren (z. B. max Komplexität ≤ 10).

## Generiert mit

- Script: cortex-ai/suggestions/generate_class_metrics.py
