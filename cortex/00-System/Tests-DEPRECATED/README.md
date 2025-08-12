# 🧪 Cortex Test Suite Documentation

*Comprehensive testing framework for Cortex Multi-Vault System*

## 🎯 **Test Suite Overview**

### **Test Categories:**
- **🔧 Unit Tests** - Individual component testing
- **🔗 Integration Tests** - Multi-component interaction testing  
- **⚡ Performance Tests** - Scalability and performance validation
- **💨 Smoke Tests** - Quick basic functionality verification

### **Coverage Areas:**
- ✅ AI Learning Engine (tag correlation, pattern detection, insights)
- ✅ Cross-Vault Linker (connection generation, similarity calculation)
- ✅ Management Service (orchestration, reporting, statistics)
- ✅ System Integration (end-to-end workflows)
- ✅ Performance & Scalability (memory usage, execution time)

## 🚀 **Quick Start**

### **1. Install Test Dependencies:**
```bash
cd /Users/simonjanke/Projects/cortex/00-System/Tests
python3 run_tests.py install
```

### **2. Run Quick Smoke Test:**
```bash
python3 run_tests.py smoke
```

### **3. Run All Tests:**
```bash
python3 run_tests.py all
```

## 🧪 **Test Commands**

### **Individual Test Suites:**
```bash
# Unit tests only
python3 run_tests.py unit

# Integration tests only  
python3 run_tests.py integration

# Performance tests only
python3 run_tests.py performance

# All tests with full coverage
python3 run_tests.py all
```

### **Test Options:**
```bash
# Verbose output
python3 run_tests.py unit --verbose

# Skip coverage reporting
python3 run_tests.py unit --no-coverage

# Generate test summary
python3 run_tests.py summary
```

## 📊 **Test Reports**

### **Generated Reports:**
- **HTML Test Report** - Detailed test results with pass/fail status
- **Coverage Report** - Code coverage analysis with line-by-line details
- **JUnit XML** - For CI/CD integration
- **Performance Metrics** - Memory usage and execution time analysis

### **Report Locations:**
```
/Users/simonjanke/Projects/cortex/00-System/Tests/reports/
├── report_unit_[timestamp].html           # Test results
├── coverage_unit_[timestamp]/index.html   # Coverage report
├── junit_unit_[timestamp].xml             # CI/CD integration
└── test_report_unit_[timestamp].json      # Machine-readable results
```

## 🧩 **Test Structure**

### **Core Test Files:**
```
00-System/Tests/
├── test_cortex_system.py      # Main system tests
├── test_performance.py        # Performance & scalability tests
├── run_tests.py              # Test runner and CLI
├── test_requirements.txt     # Test dependencies
├── pytest.ini               # Test configuration
└── reports/                  # Generated test reports
```

### **Test Classes:**

#### **test_cortex_system.py:**
- `TestMultiVaultAILearningEngine` - AI engine functionality
- `TestCrossVaultLinker` - Cross-vault linking system
- `TestCortexManagementService` - Management and orchestration
- `TestIntegration` - End-to-end system testing

#### **test_performance.py:**
- `TestPerformanceAIEngine` - AI engine performance
- `TestPerformanceCrossVaultLinker` - Linking performance
- `TestPerformanceManagement` - Management service performance
- `TestStressTests` - System limits and stress testing

## 🔧 **Test Configuration**

### **Key Test Settings:**
```ini
# pytest.ini configuration
testpaths = /Users/simonjanke/Projects/cortex/00-System/Tests
python_files = test_*.py
addopts = --strict-markers --tb=short --maxfail=5

# Coverage settings
source = /Users/simonjanke/Projects/cortex/00-System/Tests
branch = true
show_missing = true
```

### **Performance Thresholds:**
```python
# Performance assertions
assert duration < 30 seconds      # AI analysis
assert memory_usage < 500 MB      # Peak memory
assert vault_count >= 1           # Vault discovery
assert correlation_score <= 1.0   # Tag correlations
```

## 🎯 **Test Scenarios**

### **Unit Test Scenarios:**
```python
# AI Learning Engine Tests
test_initialization()              # Component setup
test_vault_discovery()             # Vault detection
test_vault_analysis()              # Individual vault analysis
test_tag_correlation_calculation() # Tag relationship detection
test_pattern_detection()           # Cross-vault pattern finding
test_insight_generation()          # Actionable insight creation

# Cross-Vault Linker Tests  
test_file_tag_extraction()         # Tag extraction from files
test_file_similarity_calculation() # Similarity scoring
test_cross_vault_link_finding()    # Connection detection
test_vault_connection_generation() # Vault-level relationships

# Management Service Tests
test_service_stats_initialization() # Statistics tracking
test_status_summary()              # Status reporting
test_full_cycle_execution()        # Complete workflow
```

### **Integration Test Scenarios:**
```python
# End-to-End Workflows
test_end_to_end_workflow()         # Complete system flow
test_multi_vault_pattern_detection() # Cross-vault analysis
test_cross_vault_connections()     # Inter-vault linking
test_system_persistence()          # State preservation
```

### **Performance Test Scenarios:**
```python
# Scalability Testing
test_large_vault_analysis_performance()  # Big vault handling
test_cross_vault_linking_performance()   # Multi-vault performance
test_memory_usage_stability()            # Memory leak detection
test_concurrent_operations()              # Parallel processing
test_maximum_vault_count()               # Scale limits
```

## 📈 **Performance Benchmarks**

### **Expected Performance:**
```
AI Analysis (200 files):     < 30 seconds
Cross-Vault Linking:         < 60 seconds  
Memory Usage (peak):         < 500 MB
Full Management Cycle:       < 120 seconds
Vault Discovery:             < 5 seconds
Tag Correlation (1000 tags): < 10 seconds
```

### **Scalability Limits:**
```
Maximum Vaults:              20+ vaults tested
Maximum Files per Vault:     200+ files tested
Maximum Tags per File:       50+ tags tested
Maximum Memory Usage:        < 2GB system-wide
Concurrent Operations:       3+ parallel cycles
```

## 🛠️ **VS Code Integration**

### **Test Tasks (Ctrl+Shift+P → Tasks):**
```json
"🧪 Run Unit Tests"
"⚡ Run Performance Tests" 
"🔗 Run Integration Tests"
"💨 Run Smoke Test"
"📊 Generate Test Report"
```

### **Debug Configurations:**
```json
"🧪 Debug Unit Tests"
"⚡ Debug Performance Tests"
"🔍 Debug Specific Test"
```

## 🚦 **CI/CD Integration**

### **GitHub Actions Example:**
```yaml
name: Cortex Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: python3 run_tests.py install
      - name: Run tests
        run: python3 run_tests.py all
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### **Test Result Artifacts:**
- JUnit XML files for test result reporting
- HTML coverage reports for analysis
- Performance benchmark data
- Test execution logs and metrics

## 🔍 **Debugging Failed Tests**

### **Common Issues:**
```bash
# Import path issues
export PYTHONPATH="/Users/simonjanke/Projects/cortex/00-System"

# Permission issues
chmod +x run_tests.py

# Missing dependencies
python3 run_tests.py install

# Temporary file cleanup
rm -rf /tmp/cortex_test_*
```

### **Debug Commands:**
```bash
# Run single test with verbose output
pytest test_cortex_system.py::TestMultiVaultAILearningEngine::test_initialization -v -s

# Run tests with debugger
pytest --pdb test_cortex_system.py

# Run tests with coverage details
pytest --cov-report=term-missing --cov=/Users/simonjanke/Projects/cortex/00-System
```

## 📋 **Test Checklist**

### **Before Release:**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Performance tests within thresholds
- [ ] Code coverage > 80%
- [ ] No memory leaks detected
- [ ] Stress tests complete successfully

### **Regular Testing:**
- [ ] Daily smoke tests
- [ ] Weekly full test suite
- [ ] Monthly performance benchmarks
- [ ] Quarterly stress tests

## 💡 **Best Practices**

### **Writing Tests:**
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies
- Use fixtures for test data setup
- Assert specific conditions, not just "no errors"

### **Performance Testing:**
- Set realistic performance thresholds
- Test with production-like data sizes
- Monitor memory usage throughout tests
- Test concurrent operations
- Validate scalability assumptions

### **Maintenance:**
- Review and update tests with code changes
- Keep test data current and realistic
- Clean up generated test files
- Monitor test execution times
- Update performance thresholds as system improves

---

## 🎯 **Test Execution Examples**

### **Quick Development Test:**
```bash
# Fast feedback during development
python3 run_tests.py smoke
```

### **Pre-Commit Testing:**
```bash
# Before committing changes
python3 run_tests.py unit
```

### **Release Testing:**
```bash
# Complete validation before release
python3 run_tests.py all
```

### **Performance Validation:**
```bash
# Performance regression testing
python3 run_tests.py performance --verbose
```

**🎉 Complete test coverage for bulletproof Cortex system reliability!** 🚀

---

**Last Updated:** 2025-08-10  
**Test Framework Version:** v1.0  
**Compatible with:** Cortex v3.0 Multi-Vault System