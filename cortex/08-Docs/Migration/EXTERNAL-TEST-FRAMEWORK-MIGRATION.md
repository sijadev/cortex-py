# 🔄 External Test Framework Migration Guide

**Target:** `cortex-test-framework` maintainers  
**Date:** 2025-08-10  
**Change:** Rule-based linking system implementation

---

## 🚨 Breaking Changes Summary

The Cortex system has migrated from **AI correlation-based linking** to **rule-based adaptive linking**. This requires **significant test framework updates**.

### Major API Changes:

1. **CrossVaultLinker Architecture:**
   - Now uses `AdaptiveRuleEngine` internally
   - Removed `LinkSuggestion` and `VaultConnection` classes
   - Changed return data structures
   - Added rule configuration dependencies

2. **New Components:**
   - `RuleBasedLinker` - Core rule engine
   - `AdaptiveRuleEngine` - AI-enhanced rule optimization
   - `link_rules.yaml` - Rule configuration file

3. **Test Data Filtering:**
   - Performance test data now filtered out automatically
   - `project-0XX`, `category-XX`, `file-XX` patterns excluded
   - AI learning ignores test/fake data

---

## 📋 Required Test Updates

### 1. Import Changes

```python
# ❌ OLD - These will fail:
from cross_vault_linker import CrossVaultLinker, LinkSuggestion, VaultConnection

# ✅ NEW - Updated imports:
from cross_vault_linker import CrossVaultLinker  
# Note: CrossVaultLinker now uses AdaptiveRuleEngine internally
# LinkSuggestion and VaultConnection classes no longer exist
```

### 2. API Usage Changes

```python
# ❌ OLD API:
linker = CrossVaultLinker(hub_path)
report = linker.run_full_linking_cycle()
suggestions = linker.link_suggestions  # Property no longer exists
connections = linker.generate_vault_connections()  # Method removed

# ✅ NEW API:
linker = CrossVaultLinker(hub_path)
report = linker.run_full_linking_cycle()
# report now contains:
# - report['type'] == 'adaptive_ai_rules'
# - report['learning_results'] with AI optimization data
# - Different summary structure
```

### 3. Return Data Structure Changes

```python
# ❌ OLD report format:
{
  'summary': {
    'total_link_suggestions': 42,
    'strong_links': 8,
    'correlation_based': True
  }
}

# ✅ NEW report format:
{
  'summary': {
    'total_link_suggestions': 15,  # Different numbers due to rule-based approach
    'strong_links': 12,
    'medium_links': 0,
    'weak_links': 0,
    'vault_connections': 0
  },
  'type': 'adaptive_ai_rules',
  'learning_results': {
    'patterns_discovered': 3,
    'rules_optimized': 2,
    'new_rules_generated': 0
  }
}
```

### 4. Test Configuration Requirements

**New dependency:** Tests must provide `link_rules.yaml` configuration:

```yaml
# Required in test setup - copy from:
# /Users/simonjanke/Projects/cortex/00-System/Cross-Vault-Linker/link_rules.yaml
```

### 5. Test Data Isolation

**Important:** Performance tests creating `project-0XX` fake data will be **automatically filtered out** by the new system. Update test expectations accordingly.

---

## 🔧 Specific Test Fixes

### TestCrossVaultLinker Class

```python
# ❌ OLD test patterns:
def test_link_suggestions(self, linker):
    """Test link suggestion generation"""
    suggestions = linker.link_suggestions  # Property doesn't exist
    assert isinstance(suggestions, list)
    if suggestions:
        suggestion = suggestions[0]
        assert hasattr(suggestion, 'source_vault')  # LinkSuggestion class removed
        assert hasattr(suggestion, 'correlation_score')  # Property changed

# ✅ NEW test patterns:  
def test_adaptive_linking_cycle(self, linker):
    """Test rule-based linking cycle"""
    report = linker.run_full_linking_cycle()
    assert report is not None
    assert report['type'] == 'adaptive_ai_rules'
    assert 'learning_results' in report
    assert 'summary' in report
    
    summary = report['summary']
    assert 'total_link_suggestions' in summary
    # Note: Numbers will be different due to rule-based approach
```

### Performance Test Updates

```python
# ❌ OLD - Creates fake data that interferes:
TestDataGenerator.create_large_vault(project_path, file_count=200, tags_per_file=15)

# ✅ NEW - Use realistic test data that won't be filtered:
TestDataGenerator.create_realistic_vault(project_path, realistic_content=True)
```

### Integration Test Changes

```python
# ❌ OLD assertions:
assert ai_report['summary']['vaults_analyzed'] >= 2  # Fake vaults were counted
assert linking_report['summary']['total_link_suggestions'] > 50  # Fake links

# ✅ NEW assertions:
assert ai_report['summary']['vaults_analyzed'] >= 1  # Only real vaults
assert linking_report['type'] == 'adaptive_ai_rules'
assert 'learning_results' in linking_report
# Expect lower but higher-quality link counts
```

---

## 🛠️ Migration Checklist

### Phase 1: Core API Migration
- [ ] Remove `LinkSuggestion`, `VaultConnection` imports
- [ ] Update `run_full_linking_cycle()` return value handling  
- [ ] Add `link_rules.yaml` to test configuration
- [ ] Update assertion expectations for new data structures

### Phase 2: Test Data Cleanup  
- [ ] Replace fake performance data with realistic test content
- [ ] Update test expectations for filtered results
- [ ] Verify AI learning doesn't pollute from test data

### Phase 3: New Feature Tests
- [ ] Add tests for `AdaptiveRuleEngine` functionality
- [ ] Test rule optimization and learning cycles
- [ ] Validate rule performance tracking
- [ ] Test automatic rule generation from patterns

### Phase 4: Integration Validation
- [ ] End-to-end testing with rule-based system
- [ ] Performance benchmarking vs. old correlation approach
- [ ] Verify external framework isolation from production data

---

## 📞 Support & Questions

**Local test suite status:** ✅ Disabled/Deprecated (as of 2025-08-10)  
**Migration support:** Available in Cortex main repository  
**Test examples:** See `link_rules.yaml` and `adaptive_rule_engine.py`

### Key Files for Reference:
- `/00-System/Cross-Vault-Linker/link_rules.yaml` - Rule configuration
- `/00-System/Cross-Vault-Linker/rule_based_linker.py` - Core rule engine  
- `/00-System/Cross-Vault-Linker/adaptive_rule_engine.py` - AI enhancement
- `/00-System/Tests-DEPRECATED/README-DEPRECATION.md` - Local test deprecation

---

**Migration Timeline:** ASAP - Local tests are broken until external framework is updated.

**Priority:** HIGH - Current test runs will fail due to API incompatibility.