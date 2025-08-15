#!/usr/bin/env python3
"""
Cortex System Configuration für Neo4j Datenbank 'cortex-system'
Konfiguriert das System für die neue Neo4j-Datenbank
"""

import os
from data_governance import DataGovernanceEngine, Neo4jTemplateManager

class CortexSystemConfig:
    """Konfiguration für das neue cortex-system"""

    def __init__(self):
        self.neo4j_uri = "bolt://localhost:7687"
        self.neo4j_user = "neo4j"
        self.neo4j_password = "neo4jtest"  # In Produktion über Umgebungsvariable
        self.database_name = "cortex-system"

    def create_cortex_system_engine(self):
        """Erstellt eine DataGovernanceEngine für das cortex-system"""
        # Erstelle Template Manager mit cortex-system Konfiguration
        template_manager = Neo4jTemplateManager(
            uri=self.neo4j_uri,
            user=self.neo4j_user,
            password=self.neo4j_password
        )

        # Erstelle Governance Engine
        engine = DataGovernanceEngine()
        engine.neo4j_manager = template_manager

        return engine

    def setup_cortex_system_templates(self, engine):
        """Richtet Standard-Templates für cortex-system ein"""

        # Cortex-spezifische Templates
        cortex_templates = [
            {
                'name': 'Cortex Knowledge Base Entry',
                'project_type': 'knowledge',
                'required_sections': ['concept', 'explanation', 'examples', 'relationships'],
                'suggested_tags': ['knowledge', 'cortex', 'learning'],
                'workflow_step': 'knowledge_capture',
                'keywords': ['knowledge', 'learning', 'concept']
            },
            {
                'name': 'Cortex Analysis Report',
                'project_type': 'analysis',
                'required_sections': ['objective', 'methodology', 'findings', 'recommendations'],
                'suggested_tags': ['analysis', 'report', 'insights'],
                'workflow_step': 'analysis',
                'keywords': ['analysis', 'data', 'insights']
            },
            {
                'name': 'Cortex Development Task',
                'project_type': 'development',
                'required_sections': ['requirements', 'implementation', 'testing', 'deployment'],
                'suggested_tags': ['development', 'task', 'implementation'],
                'workflow_step': 'development',
                'keywords': ['development', 'implementation', 'code']
            },
            {
                'name': 'Cortex Research Project',
                'project_type': 'research',
                'required_sections': ['hypothesis', 'methodology', 'experiments', 'conclusions'],
                'suggested_tags': ['research', 'investigation', 'discovery'],
                'workflow_step': 'research',
                'keywords': ['research', 'hypothesis', 'experiment']
            }
        ]

        # Templates im System registrieren
        for template_config in cortex_templates:
            if engine.neo4j_manager.is_connected():
                # Versuche Template in Neo4j zu erstellen
                engine.neo4j_manager.create_template_if_missing(
                    template_config['project_type'],
                    template_config['name'],
                    template_config['keywords']
                )

            # Auch lokal registrieren als Fallback
            engine.add_template(
                name=template_config['name'],
                required_sections=template_config['required_sections'],
                suggested_tags=template_config['suggested_tags'],
                workflow_step=template_config['workflow_step'],
                content_standards={
                    'min_length': 200,
                    'required_keywords': template_config['keywords']
                }
            )

    def setup_cortex_system_workflows(self, engine):
        """Richtet Standard-Workflows für cortex-system ein"""

        cortex_workflows = [
            {
                'name': 'Cortex Knowledge Management',
                'steps': ['Capture', 'Structure', 'Validate', 'Integrate', 'Share'],
                'templates': ['Cortex Knowledge Base Entry'],
                'auto_assign': True
            },
            {
                'name': 'Cortex Research & Development',
                'steps': ['Research', 'Design', 'Prototype', 'Test', 'Deploy'],
                'templates': ['Cortex Research Project', 'Cortex Development Task'],
                'auto_assign': True
            },
            {
                'name': 'Cortex Analysis Pipeline',
                'steps': ['Data Collection', 'Processing', 'Analysis', 'Reporting', 'Action'],
                'templates': ['Cortex Analysis Report'],
                'auto_assign': True
            }
        ]

        for workflow_config in cortex_workflows:
            engine.add_workflow(
                name=workflow_config['name'],
                steps=workflow_config['steps'],
                templates=workflow_config['templates'],
                auto_assign=workflow_config['auto_assign']
            )

def initialize_cortex_system():
    """Initialisiert das komplette cortex-system"""
    print("🚀 Initialisiere Cortex System...")

    # Erstelle Konfiguration
    config = CortexSystemConfig()

    # Erstelle Engine
    engine = config.create_cortex_system_engine()

    print("📋 Richte Templates ein...")
    config.setup_cortex_system_templates(engine)

    print("⚡ Richte Workflows ein...")
    config.setup_cortex_system_workflows(engine)

    print("✅ Cortex System erfolgreich initialisiert!")

    # Teste das System
    print("\n🧪 Teste System...")
    test_result = engine.validate_note_creation_with_context(
        name="Test Knowledge Entry",
        content="This is a test knowledge entry about machine learning concepts in artificial intelligence development. It covers the fundamental understanding of neural networks and their implementation in modern software systems.",
        description="Test entry for cortex system validation",
        project_type="knowledge",
        project_name="Cortex System Test"
    )

    print(f"Test Result: {'✅ Passed' if test_result.passed else '❌ Failed'}")
    if test_result.errors:
        print("Errors:", test_result.errors)
    if test_result.suggestions:
        print("Suggestions:", test_result.suggestions[:2])  # Zeige nur erste 2

    return engine

if __name__ == "__main__":
    # Initialisiere das cortex-system
    cortex_engine = initialize_cortex_system()

    print(f"\n📊 System Status:")
    print(f"Neo4j Connected: {cortex_engine.neo4j_manager.is_connected()}")
    print(f"Templates Available: {len(cortex_engine.get_templates())}")
    print(f"Workflows Available: {len(cortex_engine.get_workflows())}")
