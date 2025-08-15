// Neo4j Cortex_System Performance Database Initialization
// Erstellt: 2025-08-15
// Zweck: Persistente Performance-Analyse für CLI-Workflows

// 1. Database Setup
CREATE DATABASE cortex_system IF NOT EXISTS;
:USE cortex_system;

// 2. Constraints und Indizes
CREATE CONSTRAINT command_name_unique IF NOT EXISTS FOR (c:Command) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT workflow_name_unique IF NOT EXISTS FOR (w:MegaWorkflow) REQUIRE w.name IS UNIQUE;
CREATE INDEX performance_timestamp IF NOT EXISTS FOR (p:PerformanceMetric) ON (p.timestamp);
CREATE INDEX system_snapshot_timestamp IF NOT EXISTS FOR (s:SystemSnapshot) ON (s.timestamp);
CREATE INDEX command_category IF NOT EXISTS FOR (c:Command) ON (c.category);
CREATE INDEX workflow_priority IF NOT EXISTS FOR (w:MegaWorkflow) ON (w.priority);

// 3. Initial Command Data Population
// Schnelle Commands
CREATE (:Command {
    name: "list-notes",
    category: "simple",
    avg_execution_time: 1.0,
    success_rate: 0.98,
    timeout_rate: 0.02,
    last_updated: datetime(),
    complexity_score: 1,
    user_frequency: "high",
    description: "Lists all notes in the system"
});

CREATE (:Command {
    name: "cortex_status",
    category: "simple",
    avg_execution_time: 1.0,
    success_rate: 0.99,
    timeout_rate: 0.01,
    last_updated: datetime(),
    complexity_score: 1,
    user_frequency: "high",
    description: "Shows current cortex system status"
});

CREATE (:Command {
    name: "governance-report",
    category: "medium",
    avg_execution_time: 3.0,
    success_rate: 0.95,
    timeout_rate: 0.05,
    last_updated: datetime(),
    complexity_score: 3,
    user_frequency: "medium",
    description: "Generates governance compliance report"
});

// Problematische Commands
CREATE (:Command {
    name: "batch-governance-fix",
    category: "complex",
    avg_execution_time: 30.0,
    success_rate: 0.20,
    timeout_rate: 0.80,
    last_updated: datetime(),
    complexity_score: 8,
    user_frequency: "low",
    issues: ["timeout", "high_memory_usage"],
    description: "Fixes governance issues in batch mode"
});

CREATE (:Command {
    name: "ai-apply-tag-suggestions",
    category: "mega",
    avg_execution_time: 45.0,
    success_rate: 0.25,
    timeout_rate: 0.75,
    last_updated: datetime(),
    complexity_score: 9,
    user_frequency: "medium",
    issues: ["timeout", "ai_processing_heavy"],
    description: "Applies AI-generated tag suggestions"
});

CREATE (:Command {
    name: "show-workflow",
    category: "medium",
    avg_execution_time: 15.0,
    success_rate: 0.40,
    timeout_rate: 0.60,
    last_updated: datetime(),
    complexity_score: 5,
    user_frequency: "low",
    issues: ["timeout", "data_complexity"],
    description: "Displays workflow visualization"
});

// 4. Mega-Workflow Definitions
CREATE (:MegaWorkflow {
    name: "smart-overview",
    description: "Kombiniert Status-Abfragen für schnellen Überblick",
    estimated_time_saving: 5.0,
    estimated_success_rate: 0.98,
    priority: "high",
    implementation_status: "ready",
    roi_score: 7.5,
    created: datetime()
});

CREATE (:MegaWorkflow {
    name: "ai-batch-optimize",
    description: "Löst Timeout-Probleme bei AI-Befehlen",
    estimated_time_saving: 40.0,
    estimated_success_rate: 0.95,
    priority: "critical",
    implementation_status: "planned",
    roi_score: 9.2,
    created: datetime()
});

CREATE (:MegaWorkflow {
    name: "smart-note-creation",
    description: "Vollständige Note-Erstellung mit AI-Enhancement in einem Schritt",
    estimated_time_saving: 12.0,
    estimated_success_rate: 0.93,
    priority: "high",
    implementation_status: "design",
    roi_score: 8.7,
    created: datetime()
});

// 5. Optimization Recommendations
CREATE (:OptimizationRecommendation {
    name: "timeout-reduction-strategy",
    description: "Implementiere Batch-Processing für AI-Commands",
    estimated_impact: "60% timeout reduction",
    confidence: 0.95,
    priority: "critical",
    roi_score: 9.5,
    target_commands: ["ai-apply-tag-suggestions", "batch-governance-fix"],
    created: datetime()
});

CREATE (:OptimizationRecommendation {
    name: "caching-layer",
    description: "Implementiere intelligente Caching-Schicht für häufige Abfragen",
    estimated_impact: "40% speed improvement",
    confidence: 0.85,
    priority: "high",
    roi_score: 8.2,
    target_commands: ["governance-report", "show-workflow"],
    created: datetime()
});

// 6. Initial System Snapshot
CREATE (:SystemSnapshot {
    timestamp: datetime(),
    total_notes: 6,
    governance_score: 40,
    system_status: "operational",
    neo4j_version: "5.x",
    cortex_version: "latest",
    active_commands: 6,
    critical_issues: 2
});

// 7. Relationships Setup
// Workflow Combinations
MATCH (w:MegaWorkflow {name: "smart-overview"}),
      (c1:Command {name: "list-notes"}),
      (c2:Command {name: "governance-report"}),
      (c3:Command {name: "cortex_status"})
CREATE (w)-[:COMBINES]->(c1),
       (w)-[:COMBINES]->(c2),
       (w)-[:COMBINES]->(c3);

MATCH (w:MegaWorkflow {name: "ai-batch-optimize"}),
      (c1:Command {name: "batch-governance-fix"}),
      (c2:Command {name: "ai-apply-tag-suggestions"})
CREATE (w)-[:REPLACES]->(c1),
       (w)-[:REPLACES]->(c2);

// Recommendations
MATCH (r:OptimizationRecommendation {name: "timeout-reduction-strategy"}),
      (w:MegaWorkflow {name: "ai-batch-optimize"})
CREATE (r)-[:SUGGESTS]->(w);

MATCH (r:OptimizationRecommendation {name: "caching-layer"}),
      (c1:Command {name: "governance-report"}),
      (c2:Command {name: "show-workflow"})
CREATE (r)-[:IMPROVES]->(c1),
       (r)-[:IMPROVES]->(c2);

// Initial Performance Data (Sample)
MATCH (c:Command)
CREATE (:PerformanceMetric {
    command_name: c.name,
    execution_time: c.avg_execution_time * (0.8 + rand() * 0.4),
    success: rand() > c.timeout_rate,
    timestamp: datetime() - duration('PT' + toString(toInteger(rand() * 24)) + 'H'),
    system_load: rand(),
    memory_usage: 200 + rand() * 300
})-[:MEASURES]->(c);
