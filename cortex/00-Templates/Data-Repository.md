# {{TITLE}} - Data Repository

*Strukturierte Faktensammlung für {{DOMAIN}} im Projekt [[{{PROJECT_NAME}}]]*

## 📋 **Repository-Metadata**
**Project**: [[{{PROJECT_NAME}}]] - {{PROJECT_DESCRIPTION}}  
**Repository-Type**: Data-Repository  
**Research-Domain**: {{DOMAIN}}  
**Status**: #status/{{RESEARCH_STATUS}}  
**Research-Priority**: {{PRIORITY}} (Low | Medium | High | Critical)  
**Assigned-Researcher**: {{RESEARCHER}}  
**Target-Decision**: [[{{TARGET_DECISION_ADR}}]] (if applicable)

## 🎯 **Research-Scope & Objectives**

### **Primary-Research-Question**
{{PRIMARY_RESEARCH_QUESTION}}

### **Secondary-Questions**
- {{SECONDARY_QUESTION_1}}
- {{SECONDARY_QUESTION_2}}
- {{SECONDARY_QUESTION_3}}

### **Research-Boundaries**
**In-Scope**: {{RESEARCH_IN_SCOPE}}  
**Out-of-Scope**: {{RESEARCH_OUT_OF_SCOPE}}  
**Time-Constraint**: {{RESEARCH_DEADLINE}}

## 📊 Web-Recherche & Standards

### {{Tech-Area-1}}
**Offizielle Spezifikation**: 
- 

**Benchmark-Daten**:
```
Performance-Metriken:
- 
- 

Skalierungs-Limits:
- 
```

**Security-Considerations**:
- 
- 

### {{Tech-Area-2}}
**Performance-Metriken**:
```
Vergleichende Benchmarks:
- Option A: 
- Option B: 
- Option C: 
```

**Storage-Requirements**:
```
Ressourcen-Verbrauch:
- 
```

## 📈 Marktanalyse & Standards

### Industry-Practices
**Top-Companies verwendung**:
- Company A: 
- Company B: 
- Company C: 

**Compliance-Requirements**:
- **Standard 1**: 
- **Standard 2**: 
- **Standard 3**: 

### Technology-Adoption
**Survey-Data** (Jahr):
- Technology A: XX% adoption
- Technology B: XX% adoption  
- Technology C: XX% adoption

## 🔍 API-Dokumentation & Specs

### Libraries & Tools
**Primary Language**:
- Library 1: X stars, features
- Library 2: X stars, features

**Performance-Benchmarks**:
```
Library-Performance:
- Operation A: Xms
- Operation B: Xms
- Memory-Usage: XMB
```

### Infrastructure-Options
**Option 1**:
- Pros: 
- Cons: 
- Use-Cases: 

**Option 2**:
- Pros: 
- Cons: 
- Use-Cases: 

## 🔗 **Project-Integration**

### **Cross-Project-Patterns**
```dataview
TABLE pattern_name, confidence, applicable_projects
FROM "05-Insights"
WHERE contains(applicable_projects, "{{PROJECT_NAME}}")
OR contains(research_domain, "{{DOMAIN}}")
SORT confidence DESC
```

### **Related-Repositories**
- [[{{RELATED_REPO_1}}]]: {{RELATIONSHIP_DESCRIPTION_1}}
- [[{{RELATED_REPO_2}}]]: {{RELATIONSHIP_DESCRIPTION_2}}

### **Dependencies-From-Other-Projects**
- **{{DEPENDENCY_PROJECT_1}}**: {{DEPENDENCY_DESCRIPTION_1}}
- **{{DEPENDENCY_PROJECT_2}}**: {{DEPENDENCY_DESCRIPTION_2}}

### **Project-Specific-Context**
**Architecture-Constraints**: {{ARCHITECTURE_CONSTRAINTS}}  
**Performance-Requirements**: {{PERFORMANCE_REQUIREMENTS}}  
**Budget-Constraints**: {{BUDGET_CONSTRAINTS}}  
**Timeline-Constraints**: {{TIMELINE_CONSTRAINTS}}

## 📋 **Research-Quality-Assessment**

### **Source-Quality-Matrix**
| Source | Authority | Currency | Relevance | Bias-Level | Weight |
|--------|-----------|----------|-----------|------------|--------|
| {{SOURCE_1}} | {{AUTH_1}}/10 | {{CURR_1}}/10 | {{REL_1}}/10 | {{BIAS_1}}/10 | {{WEIGHT_1}} |
| {{SOURCE_2}} | {{AUTH_2}}/10 | {{CURR_2}}/10 | {{REL_2}}/10 | {{BIAS_2}}/10 | {{WEIGHT_2}} |
| {{SOURCE_3}} | {{AUTH_3}}/10 | {{CURR_3}}/10 | {{REL_3}}/10 | {{BIAS_3}}/10 | {{WEIGHT_3}} |

### **Research-Completeness**
- **Primary-Question-Coverage**: {{PRIMARY_COVERAGE}}% 
- **Secondary-Questions-Coverage**: {{SECONDARY_COVERAGE}}%
- **Quantitative-Data-Availability**: {{QUANTITATIVE_AVAILABILITY}}
- **Benchmark-Data-Quality**: {{BENCHMARK_QUALITY}}
- **Expert-Validation**: {{EXPERT_VALIDATION_STATUS}}

### **Confidence-Input-Data**
```python
# For Cortex Confidence Calculator
research_data = {
    'source_count': {{SOURCE_COUNT}},
    'avg_authority': {{AVG_AUTHORITY}},
    'avg_currency': {{AVG_CURRENCY}}, 
    'avg_relevance': {{AVG_RELEVANCE}},
    'avg_bias_level': {{AVG_BIAS_LEVEL}},
    'has_benchmarks': {{HAS_BENCHMARKS}},
    'has_quantitative_data': {{HAS_QUANTITATIVE_DATA}},
    'expert_consensus_level': {{EXPERT_CONSENSUS_LEVEL}},
    'contradictory_evidence': {{CONTRADICTORY_EVIDENCE_LEVEL}}
}
```

---
**Tags**: #data-source #projekt/{{PROJECT_NAME}} #domain/{{DOMAIN}} #research-complete  
**Cortex-Integration**: Ready for quantitative confidence-calculation  
**Project-Context**: [[{{PROJECT_NAME}}]] workspace-integrated  
**Last-Updated**: {{LAST_UPDATE_DATE}}

---
*Enhanced Data-Repository Template v2.0 | Project-Aware | Cortex-Confidence-Ready*
