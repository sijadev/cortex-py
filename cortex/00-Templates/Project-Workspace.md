# {{PROJECT_NAME}} - Project Workspace

*Cortex v2.0 Hybrid-Workspace für isolierte Projekt-Organisation*

## 📋 **Project-Metadata**
**Project-Name**: {{PROJECT_NAME}}  
**Project-Type**: {{PROJECT_TYPE}} (Technical | Business | Research | Personal)  
**Start-Date**: {{START_DATE}}  
**Status**: {{STATUS}} (Planning | Active | On-Hold | Completed | Archived)  
**Owner**: {{OWNER}}  
**Priority**: {{PRIORITY}} (Low | Medium | High | Critical)

## 🎯 **Project-Scope & Objectives**

### **Primary-Objective**
{{PRIMARY_OBJECTIVE_DESCRIPTION}}

### **Success-Criteria**
- [ ] **Criterion 1**: {{SUCCESS_CRITERION_1}}
- [ ] **Criterion 2**: {{SUCCESS_CRITERION_2}}
- [ ] **Criterion 3**: {{SUCCESS_CRITERION_3}}

### **Project-Boundaries**
**In-Scope**:
- {{IN_SCOPE_ITEM_1}}
- {{IN_SCOPE_ITEM_2}}

**Out-of-Scope**:
- {{OUT_OF_SCOPE_ITEM_1}}
- {{OUT_OF_SCOPE_ITEM_2}}

## 📊 **Project-Structure**

### **Data-Repositories** (Research & Analysis)
```dataview
TABLE status, research_completeness, source_count
FROM "01-Projects"
WHERE contains(file.path, "{{PROJECT_NAME}}")
AND contains(tags, "data-source")
SORT file.ctime DESC
```

### **Decisions** (Architecture & Design)
```dataview
TABLE confidence, status, decision_type, date(file.ctime) as "Date"
FROM "03-Decisions"
WHERE contains(file.path, "{{PROJECT_NAME}}")
OR contains(projekt, "{{PROJECT_NAME}}")
SORT confidence DESC
```

### **Neural-Links** (AI-Sessions)
```dataview
TABLE ai_insights_quality, session_focus, date(file.ctime) as "Date"
FROM "02-Neural-Links"
WHERE contains(file.path, "{{PROJECT_NAME}}")
OR contains(project, "{{PROJECT_NAME}}")
SORT file.ctime DESC
LIMIT 5
```

### **Code-Fragments** (Implementation)
```dataview
TABLE language, functionality, reuse_potential
FROM "04-Code-Fragments"
WHERE contains(file.path, "{{PROJECT_NAME}}")
OR contains(project, "{{PROJECT_NAME}}")
SORT file.ctime DESC
```

## 🔄 **Project-Workflow-Status**

### **Current-Phase**: {{CURRENT_PHASE}}
- **Phase 1**: Research & Analysis ({{PHASE_1_STATUS}})
- **Phase 2**: Decision-Making ({{PHASE_2_STATUS}})
- **Phase 3**: Implementation ({{PHASE_3_STATUS}})
- **Phase 4**: Monitoring & Review ({{PHASE_4_STATUS}})

### **Active-Tasks**
- [ ] **{{ACTIVE_TASK_1}}** ({{TASK_1_ASSIGNEE}}, {{TASK_1_DUE}})
- [ ] **{{ACTIVE_TASK_2}}** ({{TASK_2_ASSIGNEE}}, {{TASK_2_DUE}})
- [ ] **{{ACTIVE_TASK_3}}** ({{TASK_3_ASSIGNEE}}, {{TASK_3_DUE}})

### **Blockers & Dependencies**
- **Blocker 1**: {{BLOCKER_DESCRIPTION_1}} | *Resolution*: {{BLOCKER_RESOLUTION_1}}
- **Dependency 1**: {{DEPENDENCY_DESCRIPTION_1}} | *Status*: {{DEPENDENCY_STATUS_1}}

## 📈 **Project-Performance-Metrics**

### **Cortex-Decision-Quality**
```dataview
TABLE 
    confidence as "Avg Confidence",
    count(rows) as "Decisions Made",
    length(filter(rows, (r) => r.confidence > 80)) as "High Confidence"
FROM "03-Decisions"
WHERE contains(projekt, "{{PROJECT_NAME}}")
GROUP BY true
```

### **Research-Coverage**
- **Data-Sources**: `= length(filter(split(this.file.inlinks, ","), (link) => contains(link, "01-Projects")))` repositories
- **Research-Hours**: {{RESEARCH_HOURS_INVESTED}}
- **Benchmark-Data**: {{BENCHMARK_AVAILABILITY}} (Available | Partial | Missing)
- **Expert-Input**: {{EXPERT_CONSULTATIONS}} consultations

### **Implementation-Progress**
- **Code-Coverage**: {{CODE_COVERAGE_PERCENTAGE}}%
- **Test-Coverage**: {{TEST_COVERAGE_PERCENTAGE}}%
- **Documentation**: {{DOCUMENTATION_COMPLETENESS}}%
- **Performance-Targets**: {{PERFORMANCE_TARGETS_MET}}/{{TOTAL_PERFORMANCE_TARGETS}} met

## 🔗 **Cross-Project-Connections**

### **Related-Projects**
- [[{{RELATED_PROJECT_1}}]]: {{RELATIONSHIP_DESCRIPTION_1}}
- [[{{RELATED_PROJECT_2}}]]: {{RELATIONSHIP_DESCRIPTION_2}}

### **Shared-Patterns**
```dataview
TABLE pattern_name, confidence, reuse_potential
FROM "05-Insights"
WHERE contains(applicable_projects, "{{PROJECT_NAME}}")
SORT confidence DESC
```

### **Reusable-Components**
- **Template**: [[{{REUSABLE_TEMPLATE_1}}]] - {{TEMPLATE_DESCRIPTION_1}}
- **Algorithm**: [[{{REUSABLE_ALGORITHM_1}}]] - {{ALGORITHM_DESCRIPTION_1}}
- **Decision-Pattern**: [[{{REUSABLE_DECISION_1}}]] - {{DECISION_DESCRIPTION_1}}

## 🎯 **Project-Specific-Templates**

### **Quick-Actions** (Project-Context)
- **New-Data-Repository**: Use [[Data-Repository]] template with project-context
- **Project-Decision**: Use [[ADR-Enhanced]] template with project-assignment
- **Neural-Link-Session**: Use [[Cortex Neural-Link]] template with project-focus
- **Code-Fragment**: Use [[Code-Fragment]] template with project-tagging

### **Project-Lifecycle-Actions**
- **Archive-Project**: Move to 99-Archive/, update cross-references
- **Pause-Project**: Set status to On-Hold, document restart-conditions
- **Complete-Project**: Final-review, lessons-learned, pattern-extraction

## 🔍 **Project-Health-Indicators**

### **Quality-Gates**
- [ ] **Research-Quality**: >3 authoritative sources per major decision
- [ ] **Decision-Confidence**: >70% average confidence-score
- [ ] **Cross-References**: Proper linking to related-projects maintained
- [ ] **Documentation**: All major decisions documented with reasoning

### **Performance-Thresholds**
- **Response-Time**: Project-navigation <3 clicks from Cortex-Hub
- **Search-Efficiency**: Project-specific search-results >90% relevant
- **Context-Switching**: <30 seconds to full project-context
- **Link-Health**: <5% broken internal-links

### **Review-Schedule**
- **Weekly-Review**: {{WEEKLY_REVIEW_DAY}} - Progress, blockers, next-actions
- **Monthly-Review**: {{MONTHLY_REVIEW_DATE}} - Performance-metrics, course-correction
- **Quarterly-Review**: {{QUARTERLY_REVIEW_DATE}} - Strategic-alignment, lessons-learned

## 🚨 **Project-Alerts & Triggers**

### **Automatic-Triggers**
- [ ] **Stale-Decision**: No decisions made in >30 days
- [ ] **Low-Confidence**: Average confidence drops below 60%
- [ ] **Broken-Links**: >10% of project-links broken
- [ ] **Performance-Degradation**: Metrics below thresholds for >1 week

### **Manual-Reviews-Needed**
- [ ] **Scope-Creep**: Project-boundaries need re-evaluation
- [ ] **Resource-Constraints**: Timeline or budget-pressure
- [ ] **External-Changes**: Technology or market-shifts impact project
- [ ] **Team-Changes**: Key-personnel changes affecting project

## 📚 **Project-Knowledge-Base**

### **Key-Documents**
- **Project-Charter**: {{PROJECT_CHARTER_LINK}}
- **Technical-Specifications**: {{TECH_SPECS_LINK}}
- **Architecture-Overview**: {{ARCHITECTURE_LINK}}
- **Testing-Strategy**: {{TESTING_STRATEGY_LINK}}

### **External-Resources**
- **Official-Documentation**: {{OFFICIAL_DOCS_LINK}}
- **Industry-Standards**: {{STANDARDS_LINK}}
- **Best-Practices**: {{BEST_PRACTICES_LINK}}
- **Community-Resources**: {{COMMUNITY_LINK}}

## 🏷️ **Project-Tags & Metadata**

**Primary-Tags**: #projekt/{{PROJECT_NAME}} #{{PROJECT_TYPE}} #status/{{STATUS}}  
**Technology-Tags**: #tech/{{TECH_STACK_1}} #tech/{{TECH_STACK_2}}  
**Domain-Tags**: #domain/{{DOMAIN_AREA}} #complexity/{{COMPLEXITY_LEVEL}}

**Cortex-Metadata**:
- **Workspace-Version**: v2.0
- **Template-Type**: Hybrid-Workspace
- **Project-ID**: {{PROJECT_ID}}
- **Created**: {{CREATION_DATE}}
- **Last-Updated**: {{LAST_UPDATE_DATE}}

---

## 📝 **Project-Log**

| Date | Event | Impact | Notes |
|------|--------|--------|--------|
| {{DATE_1}} | {{EVENT_1}} | {{IMPACT_1}} | {{NOTES_1}} |
| {{DATE_2}} | {{EVENT_2}} | {{IMPACT_2}} | {{NOTES_2}} |

---

## 🔄 **Next-Actions**

### **Immediate** (This Week)
1. **{{IMMEDIATE_ACTION_1}}** - {{ACTION_1_DESCRIPTION}}
2. **{{IMMEDIATE_ACTION_2}}** - {{ACTION_2_DESCRIPTION}}

### **Short-Term** (Next 2-4 Weeks)
1. **{{SHORT_TERM_ACTION_1}}** - {{ACTION_1_DESCRIPTION}}
2. **{{SHORT_TERM_ACTION_2}}** - {{ACTION_2_DESCRIPTION}}

### **Long-Term** (Next Quarter)
1. **{{LONG_TERM_ACTION_1}}** - {{ACTION_1_DESCRIPTION}}
2. **{{LONG_TERM_ACTION_2}}** - {{ACTION_2_DESCRIPTION}}

---
*Project-Workspace Template v2.0 | Cortex Hybrid-Workspace | Controlled-Boundaries + Cross-Project-Learning*