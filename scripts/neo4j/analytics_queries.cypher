-- Neo4j Cortex_System Analytics Queries
-- Erstellt: 2025-08-15
-- Zweck: Performance-Analyse und Dashboard-Queries

-- ==============================================
-- PERFORMANCE ANALYSIS QUERIES
-- ==============================================

-- 1. Identifiziere problematische Commands
-- Quick System Health Check
MATCH (c:Command)
WHERE c.timeout_rate > 0.5 OR c.success_rate < 0.8
RETURN c.name as command_name,
       c.category,
       c.timeout_rate * 100 as timeout_percentage,
       c.success_rate * 100 as success_percentage,
       c.avg_execution_time as avg_time_seconds,
       c.issues as known_issues
ORDER BY c.timeout_rate DESC;

-- 2. Berechne ROI für Mega-Workflows
MATCH (w:MegaWorkflow)-[:COMBINES|REPLACES]->(c:Command)
WITH w, collect(c) as commands,
     sum(c.avg_execution_time) as total_current_time,
     avg(c.success_rate) as avg_success_rate
RETURN w.name as workflow_name,
       w.description,
       total_current_time as current_time_seconds,
       w.estimated_time_saving as time_saved_seconds,
       round((w.estimated_time_saving / total_current_time) * 100, 2) as efficiency_gain_percent,
       w.roi_score,
       w.priority,
       w.implementation_status,
       avg_success_rate * 100 as combined_success_rate
ORDER BY w.roi_score DESC;

-- 3. Priorisierung für Implementation
MATCH (w:MegaWorkflow)
WHERE w.implementation_status IN ["ready", "planned"]
RETURN w.name as workflow_name,
       w.description,
       w.priority,
       w.roi_score,
       w.estimated_time_saving as time_saving_seconds,
       w.estimated_success_rate * 100 as expected_success_rate,
       w.implementation_status as status
ORDER BY
    CASE w.priority
        WHEN "critical" THEN 1
        WHEN "high" THEN 2
        WHEN "medium" THEN 3
        ELSE 4
    END,
    w.roi_score DESC;

-- 4. System Health Overview
MATCH (c:Command)
WITH avg(c.success_rate) as avg_success_rate,
     avg(c.timeout_rate) as avg_timeout_rate,
     count(c) as total_commands,
     count(CASE WHEN c.timeout_rate > 0.5 THEN 1 END) as critical_commands,
     count(CASE WHEN c.timeout_rate > 0.2 AND c.timeout_rate <= 0.5 THEN 1 END) as warning_commands
RETURN avg_success_rate * 100 as system_success_rate,
       avg_timeout_rate * 100 as system_timeout_rate,
       total_commands,
       critical_commands,
       warning_commands,
       total_commands - critical_commands - warning_commands as healthy_commands,
       CASE
         WHEN avg_success_rate > 0.9 THEN "Excellent"
         WHEN avg_success_rate > 0.8 THEN "Good"
         WHEN avg_success_rate > 0.6 THEN "Warning"
         ELSE "Critical"
       END as overall_system_health;

-- ==============================================
-- TREND ANALYSIS QUERIES
-- ==============================================

-- 5. Performance-Trends über Zeit (letzte 7 Tage)
MATCH (p:PerformanceMetric)-[:MEASURES]->(c:Command)
WHERE p.timestamp > datetime() - duration('P7D')
WITH c.name as command_name,
     date(p.timestamp) as day,
     avg(p.execution_time) as avg_time,
     sum(CASE WHEN p.success THEN 1 ELSE 0 END) * 1.0 / count(p) as daily_success_rate,
     count(p) as execution_count
RETURN command_name,
       day,
       round(avg_time, 2) as avg_execution_time,
       round(daily_success_rate * 100, 2) as success_rate_percent,
       execution_count
ORDER BY command_name, day;

-- 6. System-Performance-Entwicklung
MATCH (s:SystemSnapshot)
WHERE s.timestamp > datetime() - duration('P30D')
RETURN s.timestamp as snapshot_time,
       s.governance_score,
       s.total_notes,
       s.system_status,
       s.active_commands,
       s.critical_issues
ORDER BY s.timestamp DESC;

-- ==============================================
-- DASHBOARD QUERIES FÜR NEUE CHATS
-- ==============================================

-- 7. Quick System Status für neue Claude-Chats
MATCH (c:Command)
OPTIONAL MATCH (c)<-[:MEASURES]-(p:PerformanceMetric)
WHERE p.timestamp > datetime() - duration('P1D')
WITH c,
     avg(p.execution_time) as recent_avg_time,
     sum(CASE WHEN p.success THEN 1 ELSE 0 END) * 1.0 / count(p) as recent_success_rate,
     count(p) as recent_executions
RETURN c.name as command_name,
       c.category,
       c.description,
       coalesce(recent_avg_time, c.avg_execution_time) as avg_time_seconds,
       coalesce(recent_success_rate * 100, c.success_rate * 100) as success_rate_percent,
       coalesce(recent_executions, 0) as executions_last_24h,
       CASE
         WHEN c.timeout_rate > 0.5 THEN "🔴 CRITICAL"
         WHEN c.timeout_rate > 0.2 THEN "🟡 WARNING"
         ELSE "🟢 OK"
       END as health_status,
       c.user_frequency as usage_frequency
ORDER BY
    CASE c.user_frequency
        WHEN "high" THEN 1
        WHEN "medium" THEN 2
        ELSE 3
    END,
    c.timeout_rate DESC;

-- 8. Top Optimization Opportunities
MATCH (w:MegaWorkflow)
WHERE w.implementation_status IN ["ready", "planned"]
OPTIONAL MATCH (w)-[:COMBINES|REPLACES]->(c:Command)
WITH w, collect(c.name) as affected_commands
RETURN w.name as optimization_name,
       w.description,
       w.estimated_time_saving as time_saved_seconds,
       w.roi_score,
       w.priority,
       w.implementation_status as status,
       affected_commands
ORDER BY w.roi_score DESC
LIMIT 3;

-- 9. Current System Metrics Summary
MATCH (s:SystemSnapshot)
WITH s ORDER BY s.timestamp DESC LIMIT 1
MATCH (c:Command)
WITH s,
     count(c) as total_commands,
     count(CASE WHEN c.timeout_rate > 0.5 THEN 1 END) as critical_commands,
     avg(c.success_rate) as avg_success_rate
RETURN "=== CORTEX SYSTEM STATUS ===" as title,
       s.timestamp as last_updated,
       s.system_status as overall_status,
       s.total_notes as total_notes,
       s.governance_score as governance_score,
       total_commands as total_commands,
       critical_commands as critical_commands,
       round(avg_success_rate * 100, 2) as system_success_rate,
       CASE
         WHEN critical_commands = 0 THEN "🟢 All systems operational"
         WHEN critical_commands <= 2 THEN "🟡 Minor issues detected"
         ELSE "🔴 Critical issues require attention"
       END as alert_status;

-- ==============================================
-- OPTIMIZATION RECOMMENDATIONS
-- ==============================================

-- 10. Smart Recommendations basierend auf Performance-Daten
MATCH (c:Command)
WHERE c.timeout_rate > 0.3 OR c.avg_execution_time > 10
OPTIONAL MATCH (r:OptimizationRecommendation)-[:IMPROVES]->(c)
WITH c, collect(r) as existing_recommendations
WHERE size(existing_recommendations) = 0  -- Noch keine Empfehlungen vorhanden
RETURN c.name as command_needing_optimization,
       c.timeout_rate * 100 as timeout_rate_percent,
       c.avg_execution_time as execution_time_seconds,
       c.issues as known_issues,
       CASE
         WHEN c.timeout_rate > 0.7 THEN "Implement async processing + timeout handling"
         WHEN c.avg_execution_time > 20 THEN "Add progress indicators + chunked processing"
         WHEN "ai_processing_heavy" IN c.issues THEN "Implement AI request batching"
         ELSE "General performance optimization needed"
       END as suggested_solution,
       CASE
         WHEN c.timeout_rate > 0.7 THEN 9.0
         WHEN c.avg_execution_time > 20 THEN 7.5
         ELSE 6.0
       END as estimated_roi_score
ORDER BY c.timeout_rate DESC, c.avg_execution_time DESC;

-- ==============================================
-- PERFORMANCE MONITORING QUERIES
-- ==============================================

-- 11. Detect Performance Degradation
MATCH (c:Command)<-[:MEASURES]-(p:PerformanceMetric)
WHERE p.timestamp > datetime() - duration('P7D')
WITH c.name as command_name,
     c.avg_execution_time as baseline_time,
     avg(p.execution_time) as recent_avg_time,
     c.success_rate as baseline_success,
     sum(CASE WHEN p.success THEN 1 ELSE 0 END) * 1.0 / count(p) as recent_success_rate
WHERE recent_avg_time > baseline_time * 1.5 OR recent_success_rate < baseline_success * 0.8
RETURN command_name,
       round(baseline_time, 2) as baseline_time_seconds,
       round(recent_avg_time, 2) as recent_avg_time_seconds,
       round(((recent_avg_time - baseline_time) / baseline_time) * 100, 2) as performance_degradation_percent,
       round(baseline_success * 100, 2) as baseline_success_rate,
       round(recent_success_rate * 100, 2) as recent_success_rate,
       "⚠️ Performance degradation detected" as alert
ORDER BY performance_degradation_percent DESC;

-- 12. Usage Pattern Analysis
MATCH (c:Command)<-[:MEASURES]-(p:PerformanceMetric)
WHERE p.timestamp > datetime() - duration('P30D')
WITH c.name as command_name,
     c.user_frequency as declared_frequency,
     count(p) as actual_executions,
     avg(p.execution_time) as avg_time
RETURN command_name,
       declared_frequency,
       actual_executions,
       CASE
         WHEN actual_executions > 50 THEN "high"
         WHEN actual_executions > 20 THEN "medium"
         ELSE "low"
       END as actual_frequency,
       round(avg_time, 2) as avg_execution_time,
       CASE
         WHEN declared_frequency != CASE
             WHEN actual_executions > 50 THEN "high"
             WHEN actual_executions > 20 THEN "medium"
             ELSE "low"
           END THEN "📊 Usage pattern changed"
         ELSE "✅ Usage as expected"
       END as frequency_analysis
ORDER BY actual_executions DESC;
