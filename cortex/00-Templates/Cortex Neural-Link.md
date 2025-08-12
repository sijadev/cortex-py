# Neural-Link: {{SESSION_TITLE}}

*AI-assisted Analysis Session für [[{{PROJECT_NAME}}]] Project-Workspace*

## 📋 **Session-Metadata**
**Project**: [[{{PROJECT_NAME}}]] - {{PROJECT_DESCRIPTION}}  
**Session-Date**: {{SESSION_DATE}}  
**Session-Focus**: {{SESSION_FOCUS}} (Research | Analysis | Decision-Support | Pattern-Recognition)  
**AI-Role**: {{AI_ROLE}} (Analyst | Advisor | Researcher | Problem-Solver)  
**Session-Duration**: {{SESSION_DURATION}} minutes  
**Session-Quality**: {{SESSION_QUALITY}} (Low | Medium | High | Excellent)

## 🎯 **Session-Objectives**

### **Primary-Objective**
{{PRIMARY_SESSION_OBJECTIVE}}

### **Secondary-Objectives**
- {{SECONDARY_OBJECTIVE_1}}
- {{SECONDARY_OBJECTIVE_2}}
- {{SECONDARY_OBJECTIVE_3}}

### **Expected-Outcomes**
- {{EXPECTED_OUTCOME_1}}
- {{EXPECTED_OUTCOME_2}}
- {{EXPECTED_OUTCOME_3}}

## 📁 **Project-Context-Auto-Export**

### **Related-Project-Data**
```dataview
TABLE file.name, status, research_completeness
FROM "01-Projects"
WHERE contains(file.path, "{{PROJECT_NAME}}")
AND contains(tags, "data-source")
SORT file.ctime DESC
```

### **Project-Decisions-Context**
```dataview
TABLE confidence, status, decision_type
FROM "03-Decisions"
WHERE contains(projekt, "{{PROJECT_NAME}}")
OR contains(file.path, "{{PROJECT_NAME}}")
SORT confidence DESC
```

### **Recent-Project-Activity**
```dataview
TABLE file.name, date(file.ctime) as "Date"
FROM "02-Neural-Links" OR "04-Code-Fragments" OR "01-Projects"
WHERE contains(projekt, "{{PROJECT_NAME}}")
OR contains(file.path, "{{PROJECT_NAME}}")
SORT file.ctime DESC
LIMIT 5
```

## 🤖 **AI-Query-Sequence & Analysis**

### **Query 1: {{QUERY_1_TOPIC}}**
**Human**: "{{HUMAN_QUERY_1}}"

**AI-Response-Summary**:
{{AI_RESPONSE_1_SUMMARY}}

**Key-Insights**:
- {{INSIGHT_1_1}}
- {{INSIGHT_1_2}}
- {{INSIGHT_1_3}}

### **Query 2: {{QUERY_2_TOPIC}}**
**Human**: "{{HUMAN_QUERY_2}}"

**AI-Response-Summary**:
{{AI_RESPONSE_2_SUMMARY}}

**Key-Insights**:
- {{INSIGHT_2_1}}
- {{INSIGHT_2_2}}
- {{INSIGHT_2_3}}

### **Query 3: {{QUERY_3_TOPIC}}** (if applicable)
**Human**: "{{HUMAN_QUERY_3}}"

**AI-Response-Summary**:
{{AI_RESPONSE_3_SUMMARY}}

**Key-Insights**:
- {{INSIGHT_3_1}}
- {{INSIGHT_3_2}}

## 💡 **AI-Synthesized-Insights**

### **Primary-Insights**
1. **{{PRIMARY_INSIGHT_1}}**: {{INSIGHT_EXPLANATION_1}}
2. **{{PRIMARY_INSIGHT_2}}**: {{INSIGHT_EXPLANATION_2}}
3. **{{PRIMARY_INSIGHT_3}}**: {{INSIGHT_EXPLANATION_3}}

### **Pattern-Recognition**
- **Pattern-Identified**: {{PATTERN_NAME}}
- **Pattern-Confidence**: {{PATTERN_CONFIDENCE}}%
- **Cross-Project-Applicability**: {{CROSS_PROJECT_APPLICABILITY}}
- **Reuse-Potential**: {{REUSE_POTENTIAL}}

### **Risk-Assessment**
- **Risk-1**: {{RISK_DESCRIPTION_1}} | *Severity*: {{RISK_SEVERITY_1}} | *Mitigation*: {{RISK_MITIGATION_1}}
- **Risk-2**: {{RISK_DESCRIPTION_2}} | *Severity*: {{RISK_SEVERITY_2}} | *Mitigation*: {{RISK_MITIGATION_2}}

### **Opportunity-Identification**
- **Opportunity-1**: {{OPPORTUNITY_DESCRIPTION_1}} | *Impact*: {{OPPORTUNITY_IMPACT_1}}
- **Opportunity-2**: {{OPPORTUNITY_DESCRIPTION_2}} | *Impact*: {{OPPORTUNITY_IMPACT_2}}

## 📈 **Decision-Readiness-Assessment**

### **Information-Completeness**
- **Research-Coverage**: {{RESEARCH_COVERAGE_ASSESSMENT}}%
- **Data-Quality**: {{DATA_QUALITY_ASSESSMENT}}/10
- **Source-Diversity**: {{SOURCE_DIVERSITY_ASSESSMENT}}
- **Expert-Input**: {{EXPERT_INPUT_ASSESSMENT}}

### **Confidence-Factors-for-Calculator**
```python
# Input for Cortex Confidence Calculator
session_insights = {
    'research_gaps_identified': {{RESEARCH_GAPS_IDENTIFIED}},
    'contradictions_found': {{CONTRADICTIONS_FOUND}},
    'expert_consensus_level': {{EXPERT_CONSENSUS_ESTIMATE}},
    'implementation_complexity': {{IMPLEMENTATION_COMPLEXITY_ESTIMATE}},
    'time_sensitivity': {{TIME_SENSITIVITY_ESTIMATE}},
    'decision_readiness': {{DECISION_READINESS_PERCENTAGE}}
}
```

### **Next-Steps-Recommendation**
1. **Immediate**: {{IMMEDIATE_NEXT_STEP}}
2. **Short-Term**: {{SHORT_TERM_NEXT_STEP}}
3. **Before-Decision**: {{PRE_DECISION_REQUIREMENT}}

## 🔗 **Cross-Project-Learning**

### **Applicable-to-Other-Projects**
- **{{OTHER_PROJECT_1}}**: {{APPLICABILITY_DESCRIPTION_1}}
- **{{OTHER_PROJECT_2}}**: {{APPLICABILITY_DESCRIPTION_2}}

### **Pattern-Library-Contribution**
- **New-Pattern**: {{NEW_PATTERN_NAME}} (if discovered)
- **Pattern-Documentation**: [[{{PATTERN_DOCUMENTATION_LINK}}]]
- **Reusable-Components**: {{REUSABLE_COMPONENTS_IDENTIFIED}}

### **Template-Improvements-Suggested**
- **{{TEMPLATE_1}}**: {{IMPROVEMENT_SUGGESTION_1}}
- **{{TEMPLATE_2}}**: {{IMPROVEMENT_SUGGESTION_2}}

## 📋 **Session-Outcomes & Deliverables**

### **Concrete-Outputs**
- [ ] **Research-Repository**: {{RESEARCH_REPOSITORY_CREATED}}
- [ ] **Decision-Draft**: {{DECISION_DRAFT_STATUS}}
- [ ] **Code-Fragment**: {{CODE_FRAGMENT_GENERATED}}
- [ ] **Pattern-Documentation**: {{PATTERN_DOCUMENTATION_CREATED}}

### **Action-Items-Generated**
- [ ] **{{ACTION_ITEM_1}}** ({{ASSIGNEE_1}}, {{DUE_DATE_1}})
- [ ] **{{ACTION_ITEM_2}}** ({{ASSIGNEE_2}}, {{DUE_DATE_2}})
- [ ] **{{ACTION_ITEM_3}}** ({{ASSIGNEE_3}}, {{DUE_DATE_3}})

### **Quality-Assessment**
- **Objective-Achievement**: {{OBJECTIVE_ACHIEVEMENT_PERCENTAGE}}%
- **Insight-Quality**: {{INSIGHT_QUALITY_RATING}}/10
- **Actionability**: {{ACTIONABILITY_RATING}}/10
- **Cross-Project-Value**: {{CROSS_PROJECT_VALUE_RATING}}/10

## 🏷️ **Session-Tags & Metadata**

**Primary-Tags**: #neural-export #projekt/{{PROJECT_NAME}} #ai-session #{{SESSION_FOCUS}}  
**Quality-Tags**: #quality/{{SESSION_QUALITY}} #insights/{{INSIGHT_QUALITY_RATING}}  
**Domain-Tags**: #domain/{{DOMAIN_AREA}} #complexity/{{COMPLEXITY_LEVEL}}

**Cortex-Integration**:
- **Decision-Input**: {{DECISION_INPUT_READY}} (Ready | Partial | Insufficient)
- **Pattern-Detected**: {{PATTERN_DETECTION_SUCCESS}}
- **Cross-Project-Applicable**: {{CROSS_PROJECT_APPLICABILITY}}
- **Next-Session-Recommended**: {{NEXT_SESSION_RECOMMENDED}}

---

## 📋 **Session-Archive**

| Timestamp | Query-Type | Insight-Generated | Quality-Score |
|-----------|------------|-------------------|---------------|
| {{TIME_1}} | {{QUERY_TYPE_1}} | {{INSIGHT_1}} | {{QUALITY_1}}/10 |
| {{TIME_2}} | {{QUERY_TYPE_2}} | {{INSIGHT_2}} | {{QUALITY_2}}/10 |
| {{TIME_3}} | {{QUERY_TYPE_3}} | {{INSIGHT_3}} | {{QUALITY_3}}/10 |

---
*Enhanced Neural-Link Template v2.0 | Project-Workspace-Integrated | AI-Session-Optimization*
