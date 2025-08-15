"""
Integration Code für cortex_cli.py - Teil 2
Füge diese Funktionen zur bestehenden cortex_cli.py hinzu
"""

import click
from typing import Optional, List, Dict, Any


@cli.command('workflow-assign')
@click.argument('workflow_name')
@click.argument('note_name')
@click.argument('step_name')
def workflow_assign(workflow_name: str, note_name: str, step_name: str):
    """Ordnet eine Note einem Workflow-Step zu."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Check if workflow and step exist
            result = session.run("""
                MATCH (w:Workflow {name: $workflow_name})-[:HAS_STEP]->(s:Step {name: $step_name})
                RETURN w, s
            """, workflow_name=workflow_name, step_name=step_name)

            if not result.single():
                print(f"❌ Workflow '{workflow_name}' oder Step '{step_name}' nicht gefunden")
                return

            # Assign note to step
            session.run("""
                MATCH (n:Note {name: $note_name})
                MATCH (s:Step {name: $step_name})
                MERGE (n)-[:BELONGS_TO_STEP]->(s)
            """, note_name=note_name, step_name=step_name)
            
            print(f"✅ Note '{note_name}' dem Step '{step_name}' im Workflow '{workflow_name}' zugeordnet")
            
    except Exception as e:
        print(f"❌ Zuordnung fehlgeschlagen: {e}")


@cli.command('workflow-progress')
@click.argument('workflow_name')
def workflow_progress(workflow_name: str):
    """Zeigt Fortschritt eines Workflows mit zugeordneten Notes."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (w:Workflow {name: $workflow_name})-[:HAS_STEP]->(s:Step)
                OPTIONAL MATCH (n:Note)-[:BELONGS_TO_STEP]->(s)
                RETURN s.name as step_name, s.order as step_order, 
                       collect(n.name) as notes
                ORDER BY s.order
            """, workflow_name=workflow_name)
            
            print(f"📊 Workflow-Fortschritt: {workflow_name}")
            print("=" * 50)
            
            total_notes = 0
            step_count = 0
            
            for record in result:
                step_count += 1
                step_name = record['step_name']
                notes = [n for n in record['notes'] if n]  # Filter None
                note_count = len(notes)
                total_notes += note_count
                
                # Progress-Indikator
                if note_count == 0:
                    status = "⭕"
                elif note_count < 3:
                    status = "🟡"
                else:
                    status = "✅"
                
                print(f"{status} Step {record['step_order']}: {step_name}")
                print(f"   📝 {note_count} Notes zugeordnet")
                
                if notes:
                    for note in notes[:3]:  # Show max 3 notes
                        print(f"     - {note}")
                    if len(notes) > 3:
                        print(f"     ... und {len(notes) - 3} weitere")

            print(f"\n📋 Zusammenfassung:")
            print(f"   🔄 {step_count} Steps")
            print(f"   📝 {total_notes} Notes zugeordnet")

            if step_count > 0:
                completion = (total_notes / (step_count * 3)) * 100  # Assume 3 notes per step as target
                print(f"   📊 Geschätzter Fortschritt: {min(completion, 100):.1f}%")

    except Exception as e:
        print(f"❌ Workflow-Progress fehlgeschlagen: {e}")


@cli.command('template-apply')
@click.argument('note_name')
@click.argument('template_name')
def template_apply(note_name: str, template_name: str):
    """Wendet ein Template auf eine bestehende Note an."""
    try:
        from src.governance.data_governance import DataGovernanceEngine

        governance = DataGovernanceEngine()
        templates = governance.get_templates()

        if template_name not in templates:
            print(f"❌ Template '{template_name}' nicht gefunden")
            print(f"   Verfügbare Templates: {', '.join(templates.keys())}")
            return

        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Get note content
            result = session.run("""
                MATCH (n:Note {name: $note_name})
                RETURN n.content as content
            """, note_name=note_name)

            record = result.single()
            if not record:
                print(f"❌ Note '{note_name}' nicht gefunden")
                return

            content = record['content'] or ""

            # Validate against template
            validation_result = governance.validate_note_creation(
                name=note_name,
                content=content,
                description=f"Template-Validierung: {template_name}",
                note_type="validation",
                template=template_name
            )

            # Apply template suggestions
            template_config = templates[template_name]
            suggested_tags = template_config.get('suggested_tags', [])

            if suggested_tags:
                # Add suggested tags to note
                for tag in suggested_tags:
                    session.run("""
                        MATCH (n:Note {name: $note_name})
                        MERGE (t:Tag {name: $tag})
                        MERGE (n)-[:HAS_TAG]->(t)
                    """, note_name=note_name, tag=tag)

                print(f"✅ Template '{template_name}' auf Note '{note_name}' angewendet")
                print(f"   🏷️ Tags hinzugefügt: {', '.join(suggested_tags)}")

            # Show validation results
            if not validation_result.is_valid:
                print(f"⚠️  Validierungswarnungen:")
                for error in validation_result.errors:
                    print(f"     - {error}")

    except Exception as e:
        print(f"❌ Template-Anwendung fehlgeschlagen: {e}")


@cli.command('governance-status')
def governance_status():
    """Zeigt Status der Data Governance Integration."""
    try:
        from src.governance.data_governance import DataGovernanceEngine

        governance = DataGovernanceEngine()
        templates = governance.get_templates()
        workflows = governance.get_workflows()

        print("🛡️ Data Governance Status")
        print("=" * 50)
        print(f"📋 Templates geladen: {len(templates)}")
        print(f"🔄 Workflows geladen: {len(workflows)}")

        # Neo4j connection status
        try:
            driver = Neo4jHelper.get_driver()
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
                print("🔗 Neo4j-Verbindung: ✅ Aktiv")

                # Count governance-related nodes
                counts = session.run("""
                    MATCH (w:Workflow) 
                    OPTIONAL MATCH (w)-[:HAS_STEP]->(s:Step)
                    OPTIONAL MATCH (n:Note)-[:BELONGS_TO_STEP]->(s)
                    RETURN count(DISTINCT w) as workflows, 
                           count(DISTINCT s) as steps,
                           count(DISTINCT n) as assigned_notes
                """).single()

                print(f"   🔄 Workflows in Neo4j: {counts['workflows']}")
                print(f"   📋 Steps in Neo4j: {counts['steps']}")
                print(f"   📝 Zugeordnete Notes: {counts['assigned_notes']}")

        except Exception as e:
            print(f"🔗 Neo4j-Verbindung: ❌ Fehler ({e})")

        print("\n🎯 Verfügbare Governance-Befehle:")
        print("   • workflow-assign <workflow> <note> <step>")
        print("   • workflow-progress <workflow>")
        print("   • template-apply <note> <template>")
        print("   • governance-status")

    except Exception as e:
        print(f"❌ Governance-Status fehlgeschlagen: {e}")
