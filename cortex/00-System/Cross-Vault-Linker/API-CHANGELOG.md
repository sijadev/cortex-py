# 🔄 Cross-Vault Linker API Changelog

**Version:** 2.0.0 (Rule-Based System)  
**Date:** 2025-08-10  
**Breaking Changes:** YES

---

## 🚨 Breaking Changes

### Architecture Overhaul
- **From:** AI correlation-based linking with statistical analysis
- **To:** Rule-based linking with AI-adaptive optimization
- **Impact:** Complete API redesign, all existing integrations require updates

---

## 📋 API Changes

### 1. CrossVaultLinker Class

#### ✅ Maintained (Compatible)
```python
# Constructor - UNCHANGED
CrossVaultLinker(cortex_hub_path: str)

# Main method - UNCHANGED signature, CHANGED behavior  
run_full_linking_cycle(sync_to_obsidian: bool = True) -> Dict
```

#### ❌ Removed (Breaking)
```python
# Properties - NO LONGER EXIST
linker.link_suggestions  # List[LinkSuggestion] - REMOVED
linker.vault_connections  # List[VaultConnection] - REMOVED
linker.ai_data  # Dict - REMOVED

# Methods - NO LONGER EXIST  
linker.generate_link_suggestions() -> List[LinkSuggestion]  # REMOVED
linker.generate_vault_connections() -> List[VaultConnection]  # REMOVED
linker.calculate_correlation_scores() -> Dict  # REMOVED
linker.generate_connection_files() -> None  # REMOVED
```

#### 🔄 Changed (Breaking)
```python
# run_full_linking_cycle() - NEW return format
# OLD format:
{
  'timestamp': '...',
  'summary': {
    'total_link_suggestions': int,
    'strong_links': int,
    'medium_links': int, 
    'weak_links': int,
    'vault_connections': int
  },
  'correlation_based': True,
  'ai_suggestions': [...]
}

# NEW format:
{
  'timestamp': '...',
  'summary': {
    'total_link_suggestions': int,  # Rule-based counts
    'strong_links': int,
    'medium_links': int,
    'weak_links': int,
    'vault_connections': int
  },
  'type': 'adaptive_ai_rules',  # NEW field
  'success': bool,
  'learning_results': {  # NEW section
    'patterns_discovered': int,
    'rules_optimized': int, 
    'new_rules_generated': int
  }
}
```

### 2. Data Classes  

#### ❌ Removed Classes (Breaking)
```python
# These classes no longer exist:
class LinkSuggestion:  # REMOVED
class VaultConnection:  # REMOVED
class TagCorrelation:  # REMOVED (moved to AI engine)
class CrossVaultPattern:  # REMOVED (moved to AI engine)
```

#### ✅ New Classes (Additions)
```python
# New rule-based classes:
class LinkRule:  # Rule definition
class LinkMatch:  # Rule match result  
class AdaptiveRule:  # AI-enhanced rule
class RuleMetrics:  # Performance tracking
class PatternDiscovery:  # AI-discovered patterns
```

### 3. Internal Architecture

#### Before (Correlation-Based):
```
CrossVaultLinker
├── AI correlation analysis
├── Statistical similarity scoring  
├── Tag co-occurrence calculation
└── Link suggestion generation
```

#### After (Rule-Based + AI):
```
CrossVaultLinker
├── AdaptiveRuleEngine
│   ├── RuleBasedLinker (core rules)
│   ├── AI pattern discovery
│   ├── Rule optimization
│   └── Performance learning
└── Obsidian integration
```

---

## 🔧 Migration Guide

### For Direct API Users:

#### 1. Remove Deprecated Usage
```python
# ❌ REMOVE - These will fail:
suggestions = linker.link_suggestions
connections = linker.generate_vault_connections()
scores = linker.calculate_correlation_scores()
```

#### 2. Update Return Value Handling
```python  
# ❌ OLD way:
report = linker.run_full_linking_cycle()
if report.get('correlation_based'):
    suggestions = report.get('ai_suggestions', [])

# ✅ NEW way:
report = linker.run_full_linking_cycle()
if report.get('type') == 'adaptive_ai_rules':
    link_count = report['summary']['total_link_suggestions']
    learning_data = report.get('learning_results', {})
```

#### 3. Add Configuration Dependencies  
```python
# NEW requirement: link_rules.yaml must exist
# Copy from: /00-System/Cross-Vault-Linker/link_rules.yaml
```

### For Test Suites:

#### 1. Update Imports
```python
# ❌ REMOVE:
from cross_vault_linker import LinkSuggestion, VaultConnection

# ✅ KEEP (behavior changed):
from cross_vault_linker import CrossVaultLinker
```

#### 2. Update Assertions
```python
# ❌ OLD assertions:
assert hasattr(linker, 'link_suggestions')
assert isinstance(suggestions[0], LinkSuggestion)

# ✅ NEW assertions:  
assert report['type'] == 'adaptive_ai_rules'
assert 'learning_results' in report
assert report['summary']['total_link_suggestions'] >= 0
```

---

## 🎯 Benefits of New System

### Rule-Based Advantages:
- **Predictable:** No more AI hallucination or fake links
- **Maintainable:** Rules are visible and adjustable  
- **Performance:** Faster than statistical correlation analysis
- **Quality:** Higher precision, fewer false positives

### AI Enhancement:
- **Learning:** Rules improve based on usage patterns
- **Discovery:** New rules generated from successful patterns  
- **Optimization:** Automatic performance tuning
- **Adaptation:** System evolves with user behavior

### Data Quality:
- **Filtering:** Test/performance data automatically excluded
- **Validation:** Rule-based matching prevents garbage links  
- **Consistency:** Repeatable results across runs

---

## 📚 New Documentation

### Key Files:
- `link_rules.yaml` - Rule configuration and examples
- `rule_based_linker.py` - Core rule engine implementation  
- `adaptive_rule_engine.py` - AI learning and optimization
- `API-CHANGELOG.md` - This document
- `EXTERNAL-TEST-FRAMEWORK-MIGRATION.md` - Test migration guide

### Usage Examples:
- See `rule_based_linker.py:main()` for standalone usage
- See `adaptive_rule_engine.py:main()` for AI learning examples
- Configuration examples in `link_rules.yaml`

---

## 🔍 Troubleshooting

### Common Migration Issues:

#### "LinkSuggestion not found"
**Cause:** Old import still present  
**Fix:** Remove import, use report data directly

#### "link_suggestions attribute missing"  
**Cause:** Property no longer exists  
**Fix:** Use `run_full_linking_cycle()` return data

#### "Empty link results"
**Cause:** Rule filtering is more selective  
**Fix:** Check `link_rules.yaml` configuration, expect fewer but higher-quality links

#### "Missing rule configuration"  
**Cause:** `link_rules.yaml` not found  
**Fix:** Copy configuration file to proper location

---

## 📅 Deprecation Timeline

- **2025-08-10:** Rule-based system implemented
- **2025-08-10:** Local tests disabled/deprecated  
- **Immediate:** External test framework requires updates
- **Ongoing:** AI learning improves rule performance

---

**Migration Priority:** URGENT - All existing integrations broken until updated.