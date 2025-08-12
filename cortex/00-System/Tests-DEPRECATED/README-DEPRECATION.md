# ⚠️ DEPRECATED TEST SUITE

**Status:** DEPRECATED as of 2025-08-10  
**Reason:** Tests moved to external cortex-test-framework  
**Replacement:** `/Users/simonjanke/Projects/cortex-test-framework/`

## Why Deprecated?

This local test suite has been **replaced by external test framework** to:

1. **Clean Separation** - Tests don't interfere with production system
2. **API Changes** - Rule-based linking system requires new test approach  
3. **Better Isolation** - External framework prevents test data pollution

## What Changed?

### 🚨 Breaking API Changes:
- `CrossVaultLinker` now uses `AdaptiveRuleEngine` 
- `LinkSuggestion` and `VaultConnection` classes removed
- `run_full_linking_cycle()` returns different data structure
- Rule-based approach replaces AI correlation-based linking

### 🔄 New Architecture:
```python
# OLD (deprecated):
from cross_vault_linker import CrossVaultLinker, LinkSuggestion
linker = CrossVaultLinker(hub_path)
report = linker.run_full_linking_cycle()
suggestions = linker.link_suggestions  # ❌ No longer exists

# NEW (rule-based):
from cross_vault_linker import CrossVaultLinker
linker = CrossVaultLinker(hub_path)  # Now uses AdaptiveRuleEngine internally
report = linker.run_full_linking_cycle()
# report['type'] == 'adaptive_ai_rules'
# report['learning_results'] contains AI optimization data
```

## Migration Required

**For External Test Framework:**

1. Update imports - remove `LinkSuggestion`, `VaultConnection`
2. Update test expectations for new return formats
3. Add `link_rules.yaml` configuration dependency  
4. Test against rule-based outputs instead of correlation-based

## Last Working Version

**Final test run:** 2025-08-10 21:05:00  
**Coverage:** 77% (24 tests passed)  
**Reports:** Available in `/reports/` directory

## Next Steps

1. ✅ **Local tests disabled** to prevent broken builds
2. 🔄 **External framework** needs API migration  
3. 📋 **Migration guide** created for test maintainers
4. 🧹 **Cleanup** of old test artifacts scheduled

---

**Do not run these tests** - they are incompatible with the new rule-based system.  
Use the external test framework instead: `cortex-test-framework/`