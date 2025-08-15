"""
Integration Code für cortex_cli.py - Teil 2
Füge diese Funktionen zur bestehenden cortex_cli.py hinzu
"""

            """, note_name=note_name, step_name=step_name)
            
            print(f"✅ Note '{note_name}' dem Step '{step_name}' im Workflow '{workflow_name}' zugeordnet")
            
    except Exception as e:
        print(f"❌ Zuordnung fehlgeschlagen: {e}")

@cli.command('workflow-progress')
@click.argument('workflow_name')
def workflow_progress(workflow_name):
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
                    for note in notes[:3]:  # Zeige max 3 Notes
                        print(f"      • {note}")
                    if len(notes) > 3:
                        print(f"      • ... und {len(notes)-3} weitere")
                print()
            
            # Gesamt-Statistiken
            completion = (total_notes / (step_count * 3)) * 100 if step_count > 0 else 0
            print(f"📊 Gesamt: {total_notes} Notes in {step_count} Steps")
            print(f"📈 Completion: {completion:.1f}% (angenommen 3 Notes/Step als Ziel)")
            
    except Exception as e:
        print(f"❌ Fehler beim Anzeigen des Workflow-Fortschritts: {e}")

@cli.command('governance-report')
def governance_report():
    """Erstellt einen Data-Governance-Bericht über alle Notes."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Hole alle Notes für Analyse
            notes_result = session.run("""
                MATCH (n:Note)
                OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t:Tag)
                OPTIONAL MATCH (n)-[:USES_TEMPLATE]->(tmp:Template)
                OPTIONAL MATCH (n)-[:BELONGS_TO_STEP]->(s:Step)
                RETURN n.name as name, 
                       n.content as content,
                       n.description as description,
                       n.type as note_type,
                       collect(DISTINCT t.name) as tags,
                       collect(DISTINCT tmp.name) as templates,
                       collect(DISTINCT s.name) as steps
            """)
            
            print("📋 Data Governance Report")
            print("=" * 50)
            
            governance = DataGovernanceEngine()
            
            total_notes = 0
            good_notes = 0
            warning_notes = 0
            error_notes = 0
            
            notes_by_category = {
                'mit_template': 0,
                'mit_tags': 0,
                'mit_workflow': 0,
                'vollständig': 0
            }
            
            for record in notes_result:
                total_notes += 1
                name = record['name']
                content = record['content'] or ""
                description = record['description'] or ""
                note_type = record['note_type'] or ""
                tags = [t for t in record['tags'] if t]
                templates = [t for t in record['templates'] if t]
                steps = [s for s in record['steps'] if s]
                
                # Validiere Note
                validation_result = governance.validate_note_creation(
                    name, content, description, note_type
                )
                
                # Kategorisiere Note
                if not validation_result.errors:
                    if not validation_result.warnings:
                        good_notes += 1
                    else:
                        warning_notes += 1
                else:
                    error_notes += 1
                
                # Analysiere Strukturierung
                if templates:
                    notes_by_category['mit_template'] += 1
                if tags:
                    notes_by_category['mit_tags'] += 1
                if steps:
                    notes_by_category['mit_workflow'] += 1
                if templates and tags and steps:
                    notes_by_category['vollständig'] += 1
            
            # Erstelle Report
            print(f"📊 Gesamt-Statistiken:")
            print(f"   📝 Notes insgesamt: {total_notes}")
            print(f"   ✅ Ohne Probleme: {good_notes} ({good_notes/total_notes*100:.1f}%)")
            print(f"   ⚠️  Mit Warnungen: {warning_notes} ({warning_notes/total_notes*100:.1f}%)")
            print(f"   ❌ Mit Fehlern: {error_notes} ({error_notes/total_notes*100:.1f}%)")
            print()
            
            print(f"🏗️ Strukturierungs-Status:")
            print(f"   📋 Mit Template: {notes_by_category['mit_template']} ({notes_by_category['mit_template']/total_notes*100:.1f}%)")
            print(f"   🏷️  Mit Tags: {notes_by_category['mit_tags']} ({notes_by_category['mit_tags']/total_notes*100:.1f}%)")
            print(f"   🔄 In Workflow: {notes_by_category['mit_workflow']} ({notes_by_category['mit_workflow']/total_notes*100:.1f}%)")
            print(f"   🎯 Vollständig: {notes_by_category['vollständig']} ({notes_by_category['vollständig']/total_notes*100:.1f}%)")
            print()
            
            # Empfehlungen
            print(f"💡 Empfehlungen:")
            if error_notes > 0:
                print(f"   🚨 {error_notes} Notes haben kritische Probleme und sollten überarbeitet werden")
            if notes_by_category['mit_template'] < total_notes * 0.5:
                print(f"   📋 Mehr Notes sollten Templates verwenden ({notes_by_category['mit_template']}/{total_notes})")
            if notes_by_category['mit_tags'] < total_notes * 0.8:
                print(f"   🏷️  Mehr Notes benötigen Tags ({notes_by_category['mit_tags']}/{total_notes})")
            if notes_by_category['vollständig'] < total_notes * 0.3:
                print(f"   🎯 Mehr Notes sollten vollständig strukturiert sein")
            
            if error_notes == 0 and warning_notes < total_notes * 0.2:
                print(f"   🎉 Excellent! Sehr gute Data Governance!")
            
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Governance-Reports: {e}")

@cli.command('fix-note-governance')
@click.argument('note_name')
@click.option('--auto-fix', is_flag=True, help='Automatische Korrekturen anwenden')
def fix_note_governance(note_name, auto_fix):
    """Analysiert und behebt Governance-Probleme einer Note."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Hole aktuelle Note-Daten
            note_result = session.run("""
                MATCH (n:Note {name: $name})
                RETURN n.name as name, n.content as content, 
                       n.description as description, n.type as note_type
            """, name=note_name).single()
            
            if not note_result:
                print(f"❌ Note '{note_name}' nicht gefunden")
                return
            
            # Validiere aktuelle Note
            governance = DataGovernanceEngine()
            validation_result = governance.validate_note_creation(
                note_result['name'],
                note_result['content'] or "",
                note_result['description'] or "",
                note_result['note_type'] or ""
            )
            
            print(f"🔧 Governance-Fix für Note: '{note_name}'")
            print("=" * 50)
            
            # Zeige aktuelle Probleme
            print_validation_result(validation_result, note_name)
            
            if not validation_result.errors and not validation_result.warnings:
                print("✅ Note hat keine Governance-Probleme!")
                return
            
            # Auto-Fix oder manuelle Bestätigung
            if auto_fix or click.confirm("🔧 Empfohlene Verbesserungen anwenden?"):
                
                # Wende Empfehlungen an
                if validation_result.suggestions:
                    apply_suggestions(note_name, validation_result.suggestions)
                
                # Validiere erneut
                validation_result_after = governance.validate_note_creation(
                    note_result['name'],
                    note_result['content'] or "",
                    note_result['description'] or "",
                    note_result['note_type'] or ""
                )
                
                print("\n🔍 Nach Korrekturen:")
                print_validation_result(validation_result_after, note_name)
                
                if len(validation_result_after.errors) < len(validation_result.errors):
                    print("✅ Verbesserungen erfolgreich angewendet!")
                else:
                    print("⚠️ Manuelle Nacharbeit erforderlich")
            
    except Exception as e:
        print(f"❌ Fehler beim Governance-Fix: {e}")

@cli.command('batch-governance-fix')
@click.option('--dry-run', is_flag=True, help='Nur Analyse, keine Änderungen')
@click.option('--auto-apply', is_flag=True, help='Automatische Korrekturen ohne Nachfrage')
def batch_governance_fix(dry_run, auto_apply):
    """Behebt Governance-Probleme aller Notes im Batch."""
    try:
        driver = Neo4jHelper.get_driver()
        with driver.session() as session:
            # Hole alle Notes
            notes_result = session.run("""
                MATCH (n:Note)
                RETURN n.name as name, n.content as content, 
                       n.description as description, n.type as note_type
            """)
            
            print("🔧 Batch Governance Fix")
            print("=" * 30)
            
            governance = DataGovernanceEngine()
            
            fixed_count = 0
            total_count = 0
            
            for record in notes_result:
                total_count += 1
                name = record['name']
                content = record['content'] or ""
                description = record['description'] or ""
                note_type = record['note_type'] or ""
                
                # Validiere Note
                validation_result = governance.validate_note_creation(
                    name, content, description, note_type
                )
                
                # Nur Notes mit Empfehlungen bearbeiten
                if validation_result.suggestions:
                    print(f"\n🔧 Bearbeite '{name}':")
                    
                    if not dry_run and (auto_apply or click.confirm(f"Fix '{name}'?")):
                        try:
                            apply_suggestions(name, validation_result.suggestions)
                            fixed_count += 1
                            print(f"✅ '{name}' verbessert")
                        except Exception as e:
                            print(f"❌ Fehler bei '{name}': {e}")
                    elif dry_run:
                        print(f"💡 Würde '{name}' verbessern: {len(validation_result.suggestions)} Empfehlungen")
                        fixed_count += 1
            
            print(f"\n📊 Batch-Ergebnis:")
            print(f"   📝 Notes analysiert: {total_count}")
            
            if dry_run:
                print(f"   🔧 Notes mit Verbesserungspotential: {fixed_count}")
                print(f"   💡 Verwende ohne --dry-run um Änderungen anzuwenden")
            else:
                print(f"   ✅ Notes verbessert: {fixed_count}")
            
    except Exception as e:
        print(f"❌ Fehler beim Batch-Fix: {e}")

# Füge diese Funktionen zu cli.py hinzu, indem du sie am Ende vor "if __name__ == '__main__':" einfügst
