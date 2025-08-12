# Cortex Performance Dashboard v2.0

*Real-time Monitoring und Analytics für das Cortex Decision-System*

## 🎯 **System-Health-Overview**

### Decision-Pipeline-Status
```dataview
TABLE 
    file.name as "Decision",
    confidence as "Confidence",
    status as "Status",
    date(file.ctime) as "Created"
FROM "03-Decisions"
WHERE contains(tags, "cortex-decision")
SORT confidence DESC
LIMIT 10
```

### Confidence-Distribution
```dataview
TABLE 
    length(rows) as "Count"
FROM "03-Decisions" 
WHERE contains(tags, "cortex-decision")
GROUP BY choice(confidence >= 90, "🟢 High (90%+)", choice(confidence >= 70, "🟡 Medium (70-89%)", choice(confidence >= 50, "🟠 Low (50-69%)", "🔴 Critical (<50%)"))) as "Confidence Level"
SORT "Confidence Level"
```

## 📊 **Performance-Metrics**

### Decision-Speed-Analytics
```dataview
TABLE 
    project,
    decision_time_hours as "Hours",
    research_quality,
    implementation_success
FROM "06-Monitoring"
WHERE decision_time_hours
SORT decision_time_hours ASC
```

### Data-Reuse-Tracking  
```dataview
TABLE 
    file.name as "Repository",
    length(file.outlinks) as "References",
    length(file.inlinks) as "Referenced By",
    choice(length(file.inlinks) > 3, "🟢 High Reuse", choice(length(file.inlinks) > 1, "🟡 Medium Reuse", "🔴 Low Reuse")) as "Reuse Level"
FROM "01-Projects"
WHERE contains(tags, "data-source")
SORT length(file.inlinks) DESC
```

## 🔄 **System-Activity**

### **Pattern-Recognition-Analytics**
```dataview
TABLE
    pattern_name,
    confidence as "Confidence",
    length(applicable_projects) as "Projects Applied",
    success_rate as "Success Rate"
FROM "05-Insights"
WHERE contains(tags, "pattern-detected")
SORT success_rate DESC
```

### **Best-Practice-Suggestions**
```dataview
TABLE
    solution_name,
    reuse_potential as "Reusability", 
    projects_used as "Usage Count",
    last_validated as "Last Used"
FROM "05-Insights"
WHERE contains(tags, "best-practice")
SORT reuse_potential DESC
LIMIT 5
```

### **Learning-Velocity-Tracking**
```dataview
TABLE
    date(file.ctime) as "Pattern Discovery",
    pattern_name,
    evidence_strength as "Evidence",
    cross_project_applicability as "Transferability"
FROM "05-Insights"
WHERE contains(tags, "pattern-detected")
SORT file.ctime DESC
LIMIT 10
```

### Latest Decisions
```dataview
TABLE 
    decision_title,
    confidence + "%" as "Confidence",
    status,
    review_date
FROM "03-Decisions"
WHERE contains(tags, "cortex-decision")
SORT file.ctime DESC
LIMIT 5
```

## 📈 **Quality-Metrics**

### Research-Quality-Assessment
```dataview
TABLE
    file.name as "Repository",
    source_count as "Sources",
    has_benchmarks as "Benchmarks",
    research_completeness + "%" as "Completeness"
FROM "01-Projects"
WHERE contains(tags, "data-source") AND source_count
SORT research_completeness DESC
```

### Decision-Success-Tracking
```dataview
TABLE
    decision_title,
    confidence as "Predicted",
    actual_outcome as "Actual",
    choice(actual_outcome = "success", "✅", choice(actual_outcome = "partial", "🟡", "❌")) as "Result",
    months_valid as "Validity"
FROM "06-Monitoring"
WHERE actual_outcome
SORT months_valid DESC
```

## 🎯 **Current KPIs**

### Targets vs Actuals
| Metric | Target | Current | Trend | Status |
|--------|--------|---------|-------|--------|
| **Decision Speed** | <45 min | `= this.avg_decision_time` min | `= this.speed_trend` | `= this.speed_status` |
| **Confidence Accuracy** | >90% | `= this.confidence_accuracy`% | `= this.accuracy_trend` | `= this.accuracy_status` |
| **Data Reuse Rate** | >80% | `= this.reuse_rate`% | `= this.reuse_trend` | `= this.reuse_status` |
| **Research Quality** | >85% | `= this.research_quality`% | `= this.quality_trend` | `= this.quality_status` |

### Weekly Performance Snapshot
```dataview
TABLE
    week_of,
    decisions_made as "Decisions",
    avg_confidence as "Avg Confidence",
    research_hours as "Research Time",
    implementation_rate as "Success Rate"
FROM "06-Monitoring"
WHERE contains(tags, "weekly-snapshot")
SORT week_of DESC
LIMIT 4
```

## 🔍 **Deep-Dive-Analytics**

### Cross-Project-Pattern-Detection
```dataview
TABLE
    pattern_name,
    frequency as "Occurrences", 
    confidence_improvement as "Confidence Boost",
    reuse_potential as "Reusability"
FROM "05-Insights"
WHERE contains(tags, "pattern-detected")
SORT frequency DESC
```

### Decision-Accuracy-Analysis
```dataview
TABLE
    months_elapsed,
    total_decisions,
    still_valid,
    round((still_valid / total_decisions) * 100, 1) + "%" as "Accuracy Rate"
FROM "06-Monitoring"
WHERE contains(tags, "accuracy-analysis")
SORT months_elapsed ASC
```

## ⚠️ **Health-Alerts**

### Review-Required
```dataview
TABLE
    file.name as "Decision",
    review_date as "Due Date",
    confidence as "Original Confidence",
    datediff(review_date, date(today), "days") as "Days Overdue"
FROM "03-Decisions"
WHERE review_date < date(today) AND status != "superseded"
SORT review_date ASC
```

### Low-Confidence-Decisions
```dataview
TABLE
    file.name as "Decision",
    confidence as "Confidence",
    status,
    implementation_risk as "Risk Level"
FROM "03-Decisions"
WHERE confidence < 70 AND status = "accepted"
SORT confidence ASC
```

### Data-Quality-Issues
```dataview
TABLE
    file.name as "Repository",
    source_count as "Sources",
    research_completeness as "Completeness",
    last_updated
FROM "01-Projects"
WHERE (source_count < 2 OR research_completeness < 50) AND contains(tags, "data-source")
SORT research_completeness ASC
```

## 🚀 **Optimization-Opportunities**

### Underutilized-Repositories
```dataview
TABLE
    file.name as "Repository",
    length(file.inlinks) as "References",
    research_effort_hours as "Effort",
    round(length(file.inlinks) / research_effort_hours, 2) as "ROI"
FROM "01-Projects"
WHERE research_effort_hours > 0 AND contains(tags, "data-source")
SORT round(length(file.inlinks) / research_effort_hours, 2) ASC
LIMIT 5
```

### Template-Effectiveness
```dataview
TABLE
    template_name,
    usage_count as "Uses",
    avg_completion_time as "Avg Time",
    user_satisfaction as "Satisfaction"
FROM "06-Monitoring"
WHERE contains(tags, "template-metrics")
SORT user_satisfaction DESC
```

## 📋 **Action-Items**

### High-Priority-Actions
- [ ] **Review overdue decisions**: `= length(filter(flatten(map(split(this.file.inlinks, ","), (x) => x)), (x) => x.review_date < date(today)))` items
- [ ] **Improve low-confidence decisions**: `= length(filter(flatten(map(split(this.file.inlinks, ","), (x) => x)), (x) => x.confidence < 70))` items
- [ ] **Update stale repositories**: `= length(filter(flatten(map(split(this.file.inlinks, ","), (x) => x)), (x) => x.research_completeness < 50))` items

### Optimization-Tasks
- [ ] **Enhance underperforming templates**
- [ ] **Create patterns for frequent decision-types**
- [ ] **Improve data-reuse workflows**
- [ ] **Automate confidence-calculation-integration**

## 🔗 **Quick-Links**

- [[Cortex-Hub]] - Main navigation
- [[Confidence Calculator]] - Algorithm documentation
- [[Template-Index]] - All available templates
- [[System-Workflows]] - Process documentation

---

## 📊 **Dashboard-Configuration**

### Auto-Refresh
```javascript
// Auto-refresh every 5 minutes for real-time monitoring
setInterval(() => {
    app.workspace.getActiveFile()?.parent?.children
        ?.filter(f => f.name.includes('Performance-Dashboard'))
        ?.forEach(f => app.vault.read(f).then(() => {}));
}, 300000);
```

### Custom-CSS-Classes
```css
.performance-green { color: #10b981; font-weight: bold; }
.performance-yellow { color: #f59e0b; font-weight: bold; }
.performance-red { color: #ef4444; font-weight: bold; }
```

---
**Tags**: #cortex-dashboard #system-monitoring #performance-analytics #real-time-data

**Last-Updated**: `= this.file.mtime`  
**Auto-Refresh**: Enabled  
**Data-Sources**: 6 directories, 4+ table queries

---
*Cortex v2.0 Performance Dashboard | Real-time Decision-Intelligence-Monitoring*