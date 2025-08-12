# Decision Tracking: {{DECISION_NAME}}

*Monitoring und Success-Tracking für Cortex-Entscheidungen*

## 📋 **Decision-Reference**
**Related-ADR**: [[ADR-{{ADR_NUMBER}}-{{DECISION_NAME}}]]  
**Decision-Date**: {{DECISION_DATE}}  
**Original-Confidence**: {{ORIGINAL_CONFIDENCE}}%  
**Decision-Owner**: {{DECISION_OWNER}}

## 📊 **Predicted-vs-Actual-Performance**

### Success-Metrics-Tracking
| Metric | Predicted | Actual | Variance | Status |
|--------|-----------|--------|----------|---------|
| **Performance** | {{PREDICTED_PERFORMANCE}} | {{ACTUAL_PERFORMANCE}} | {{PERFORMANCE_VARIANCE}} | {{PERFORMANCE_STATUS}} |
| **Cost** | {{PREDICTED_COST}} | {{ACTUAL_COST}} | {{COST_VARIANCE}} | {{COST_STATUS}} |
| **Timeline** | {{PREDICTED_TIMELINE}} | {{ACTUAL_TIMELINE}} | {{TIMELINE_VARIANCE}} | {{TIMELINE_STATUS}} |
| **User-Satisfaction** | {{PREDICTED_SATISFACTION}} | {{ACTUAL_SATISFACTION}} | {{SATISFACTION_VARIANCE}} | {{SATISFACTION_STATUS}} |

### Implementation-Progress
- [x] **Phase 1**: {{PHASE_1_DESCRIPTION}} ({{PHASE_1_DATE}})
- [x] **Phase 2**: {{PHASE_2_DESCRIPTION}} ({{PHASE_2_DATE}})  
- [ ] **Phase 3**: {{PHASE_3_DESCRIPTION}} ({{PHASE_3_TARGET_DATE}})

## 🎯 **Confidence-Validation**

### Predicted-Confidence-Breakdown
```python
# Original Cortex-Calculation
original_confidence = {
    'data_coverage': {{ORIGINAL_DATA_COVERAGE}},      # {{DATA_COVERAGE_SCORE}}%
    'source_quality': {{ORIGINAL_SOURCE_QUALITY}},   # {{SOURCE_QUALITY_SCORE}}%
    'expert_consensus': {{ORIGINAL_CONSENSUS}},       # {{CONSENSUS_SCORE}}%
    'time_sensitivity': {{ORIGINAL_TIME_SENS}},      # {{TIME_SENS_SCORE}}%
    'implementation_risk': {{ORIGINAL_IMPL_RISK}}    # {{IMPL_RISK_SCORE}}%
}
# Total: {{ORIGINAL_CONFIDENCE}}%
```

### Actual-Reality-Check
```python
# Post-Implementation-Assessment
actual_factors = {
    'data_accuracy': {{ACTUAL_DATA_ACCURACY}},        # How accurate was our data?
    'unforeseen_factors': {{UNFORESEEN_IMPACT}},      # What did we miss?
    'implementation_complexity': {{ACTUAL_COMPLEXITY}}, # Was it as complex as expected?
    'external_changes': {{EXTERNAL_IMPACT}},          # Environmental changes
    'team_execution': {{EXECUTION_QUALITY}}           # How well did we execute?
}
# Confidence-Accuracy: {{CONFIDENCE_ACCURACY}}%
```

## ⏱️ **Timeline-Tracking**

### Key-Milestones
| Milestone | Planned Date | Actual Date | Variance | Notes |
|-----------|--------------|-------------|----------|--------|
| **Research Complete** | {{RESEARCH_PLANNED}} | {{RESEARCH_ACTUAL}} | {{RESEARCH_VARIANCE}} | {{RESEARCH_NOTES}} |
| **Decision Made** | {{DECISION_PLANNED}} | {{DECISION_ACTUAL}} | {{DECISION_VARIANCE}} | {{DECISION_NOTES}} |
| **Implementation Start** | {{IMPL_START_PLANNED}} | {{IMPL_START_ACTUAL}} | {{IMPL_START_VARIANCE}} | {{IMPL_START_NOTES}} |
| **Go-Live** | {{GOLIVE_PLANNED}} | {{GOLIVE_ACTUAL}} | {{GOLIVE_VARIANCE}} | {{GOLIVE_NOTES}} |
| **First Review** | {{REVIEW_PLANNED}} | {{REVIEW_ACTUAL}} | {{REVIEW_VARIANCE}} | {{REVIEW_NOTES}} |

## 📈 **Lessons-Learned**

### What-Worked-Well ✅
1. **{{SUCCESS_FACTOR_1}}**: {{SUCCESS_DESCRIPTION_1}}
2. **{{SUCCESS_FACTOR_2}}**: {{SUCCESS_DESCRIPTION_2}}
3. **{{SUCCESS_FACTOR_3}}**: {{SUCCESS_DESCRIPTION_3}}

### What-Could-Be-Improved ⚠️
1. **{{IMPROVEMENT_AREA_1}}**: {{IMPROVEMENT_DESCRIPTION_1}}
2. **{{IMPROVEMENT_AREA_2}}**: {{IMPROVEMENT_DESCRIPTION_2}}
3. **{{IMPROVEMENT_AREA_3}}**: {{IMPROVEMENT_DESCRIPTION_3}}

### Unforeseen-Challenges 🚨
1. **{{CHALLENGE_1}}**: {{CHALLENGE_IMPACT_1}} | *Resolution*: {{RESOLUTION_1}}
2. **{{CHALLENGE_2}}**: {{CHALLENGE_IMPACT_2}} | *Resolution*: {{RESOLUTION_2}}

## 🔄 **Cortex-Algorithm-Feedback**

### Confidence-Accuracy-Analysis
**Original-Confidence**: {{ORIGINAL_CONFIDENCE}}%  
**Actual-Success-Level**: {{ACTUAL_SUCCESS_LEVEL}}%  
**Accuracy-Score**: {{CONFIDENCE_ACCURACY}}%

### Algorithm-Improvement-Insights
- **Data-Factor-Accuracy**: {{DATA_FACTOR_FEEDBACK}}
- **Risk-Assessment-Accuracy**: {{RISK_ASSESSMENT_FEEDBACK}}
- **Time-Sensitivity-Impact**: {{TIME_SENSITIVITY_FEEDBACK}}
- **Source-Quality-Validation**: {{SOURCE_QUALITY_FEEDBACK}}

### Recommended-Algorithm-Adjustments
1. **{{ALGORITHM_ADJUSTMENT_1}}**: {{ADJUSTMENT_REASONING_1}}
2. **{{ALGORITHM_ADJUSTMENT_2}}**: {{ADJUSTMENT_REASONING_2}}

## 🔗 **Cross-Decision-Patterns**

### Similar-Decisions
- [[ADR-{{SIMILAR_ADR_1}}]]: {{SIMILARITY_DESCRIPTION_1}}
- [[ADR-{{SIMILAR_ADR_2}}]]: {{SIMILARITY_DESCRIPTION_2}}

### Pattern-Emergence
**Pattern-Type**: {{PATTERN_TYPE}}  
**Pattern-Confidence**: {{PATTERN_CONFIDENCE}}%  
**Reuse-Potential**: {{REUSE_ASSESSMENT}}

### Template-Improvements
Based on this tracking, suggest improvements to:
- [[ADR-Enhanced]] template
- [[Data-Repository]] template  
- [[Confidence Calculator]] algorithm

## 📊 **Quantitative-Data**

### Performance-Metrics
```yaml
decision_tracking_data:
  decision_id: "{{DECISION_ID}}"
  original_confidence: {{ORIGINAL_CONFIDENCE}}
  actual_outcome: "{{ACTUAL_OUTCOME}}"  # success/partial/failure
  confidence_accuracy: {{CONFIDENCE_ACCURACY}}
  
  timeline_metrics:
    research_hours: {{RESEARCH_HOURS}}
    decision_time_hours: {{DECISION_TIME_HOURS}}
    implementation_weeks: {{IMPLEMENTATION_WEEKS}}
    
  quality_metrics:
    data_sources_used: {{DATA_SOURCES_COUNT}}
    expert_consultations: {{EXPERT_CONSULTATIONS}}
    benchmark_data_points: {{BENCHMARK_COUNT}}
    
  outcome_metrics:
    performance_variance: {{PERFORMANCE_VARIANCE}}%
    cost_variance: {{COST_VARIANCE}}%
    timeline_variance: {{TIMELINE_VARIANCE}}%
    satisfaction_score: {{SATISFACTION_SCORE}}/10
```

## 🎯 **Future-Review-Schedule**

### Scheduled-Reviews
- **3-Month-Review**: {{THREE_MONTH_DATE}} - Quick health-check
- **6-Month-Review**: {{SIX_MONTH_DATE}} - Performance assessment  
- **12-Month-Review**: {{TWELVE_MONTH_DATE}} - Full retropsective
- **End-of-Life-Review**: {{EOL_DATE}} - Final lessons learned

### Review-Triggers
- [ ] Performance drops below {{PERFORMANCE_THRESHOLD}}
- [ ] Cost exceeds {{COST_THRESHOLD}}
- [ ] User satisfaction below {{SATISFACTION_THRESHOLD}}
- [ ] External technology changes impact decision
- [ ] New requirements emerge that contradict decision

## 🏷️ **Metadata**

**Tags**: #decision-tracking #adr-{{ADR_NUMBER}} #{{PROJECT_TAG}} #monitoring #cortex-feedback

**Tracking-Status**: Active | Completed | Superseded  
**Data-Quality**: {{DATA_QUALITY_SCORE}}/10  
**Template-Version**: v2.0  
**Last-Updated**: {{LAST_UPDATE_DATE}}

---

## 📝 **Change-Log**

| Date | Update | Impact | Confidence-Adjustment |
|------|--------|--------|----------------------|
| {{DATE_1}} | {{UPDATE_1}} | {{IMPACT_1}} | {{CONF_ADJ_1}} |
| {{DATE_2}} | {{UPDATE_2}} | {{IMPACT_2}} | {{CONF_ADJ_2}} |

---
*Decision-Tracking Template v2.0 | Cortex-Learning-Loop | Continuous-Algorithm-Improvement*