"""
Linking und Vault-Management Befehle für Cortex CLI
Cross-Vault Linking, regelbasiertes Linking
"""
import json
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def linking():
    """Linking und Vault-Management Befehle"""
    pass

@linking.command(name='rule-linker')
@click.option('--cortex-path', type=click.Path(), 
              help='Pfad zum Cortex Workspace', default='.')
@click.option('--run', is_flag=True, help='Linking-Zyklus ausführen')
@click.option('--show-rules', is_flag=True, help='Aktuelle Linking-Regeln anzeigen')
@click.option('--json', 'output_json', is_flag=True, help='Ausgabe als JSON')
@click.pass_context
def rule_linker(ctx, cortex_path, run, show_rules, output_json):
    """Regelbasiertes Cross-Vault-Linking"""
    
    result = _rule_linker_impl(
        cortex_path=cortex_path,
        run=run,
        show_rules=show_rules,
        output_json=output_json,
        verbose=ctx.obj.get('verbose', False) if ctx.obj else False
    )
    
    # Im programmatischen Modus gibt die Funktion das Ergebnis zurück
    if ctx.obj and ctx.obj.get('programmatic'):
        return result

@linking.command(name='validate')
@click.option('--cortex-path', type=click.Path(), 
              help='Pfad zum Cortex Workspace', default='.')
@click.option('--fix', is_flag=True, help='Versuche, ungültige Links zu reparieren')
@click.option('--json', 'output_json', is_flag=True, help='Ausgabe als JSON')
@click.option('--report', type=click.Path(), help='Speichere Bericht in Datei')
@click.pass_context
def validate_links(ctx, cortex_path, fix, output_json, report):
    """Validiere Links im Cortex Workspace"""
    
    result = _validate_links_impl(
        cortex_path=cortex_path,
        fix=fix,
        output_json=output_json,
        report=report,
        verbose=ctx.obj.get('verbose', False) if ctx.obj else False
    )
    
    # Im programmatischen Modus gibt die Funktion das Ergebnis zurück
    if ctx.obj and ctx.obj.get('programmatic'):
        return result

# Implementierungsfunktionen für programmatischen Zugriff ohne Click-Abhängigkeit

def _rule_linker_impl(cortex_path='.', run=False, show_rules=False, output_json=False, verbose=False):
    """
    Implementierung des Rule-Linker, die sowohl von CLI als auch programmatisch aufgerufen werden kann
    
    Returns:
        dict: Ergebnis mit Status und Daten
    """
    try:
        from ..core.rule_based_linker import RuleBasedLinker
        
        cortex_root = Path(cortex_path).resolve()
        linker = RuleBasedLinker(cortex_root)
        
        result = {
            'success': True,
            'cortex_path': str(cortex_root)
        }
        
        if show_rules:
            rules = [rule.__dict__ for rule in linker.rules]
            result['rules'] = rules
            
            if not output_json:
                console.print("[blue]📋 Aktuelle Linking-Regeln[/blue]")
                table = Table(title="Linking-Regeln")
                table.add_column("Name", style="cyan")
                table.add_column("Beschreibung", style="white")
                table.add_column("Stärke", style="green")
                table.add_column("Aktiviert", style="yellow")
                
                for rule in linker.rules:
                    table.add_row(
                        rule.name,
                        rule.description[:50] + "..." if len(rule.description) > 50 else rule.description,
                        f"{rule.strength:.1f}",
                        "✅" if rule.enabled else "❌"
                    )
                
                console.print(table)
                
        elif run:
            if not output_json:
                console.print("[blue]🔗 Regelbasierter Linking-Zyklus wird ausgeführt...[/blue]")
            report = linker.run_linking_cycle()
            result.update(report)
            
            if not output_json:
                if report.get('success', False):
                    console.print("[green]✅ Linking erfolgreich abgeschlossen![/green]")
                    console.print(f"📊 Angewendete Regeln: {report['rules_applied']}")
                    console.print(f"🔍 Gefundene Übereinstimmungen: {report['matches_found']}")
                    console.print(f"🔗 Erstellte Links: {report['links_created']}")
                    console.print(f"📝 Geänderte Dateien: {report['files_modified']}")
                    console.print(f"⏱️  Dauer: {report['duration_seconds']:.1f}s")
                    
                    if report.get('errors'):
                        console.print(f"[yellow]⚠️  Fehler: {len(report['errors'])}[/yellow]")
                else:
                    console.print(f"[red]❌ Linking fehlgeschlagen: {report.get('error', 'Unbekannter Fehler')}[/red]")
        else:
            if not output_json:
                console.print("[yellow]Verwende --run zum Ausführen des Linkings oder --show-rules zum Anzeigen der Konfiguration[/yellow]")
            
        if output_json:
            console.print(json.dumps(result, indent=2))
            
        return result
            
    except Exception as e:
        error_msg = f"Fehler mit Rule-Linker: {str(e)}"
        result = {
            'success': False,
            'error': error_msg,
            'error_type': type(e).__name__
        }
        
        if not output_json:
            console.print(f"[red]{error_msg}[/red]")
            
        if verbose:
            import traceback
            trace = traceback.format_exc()
            result['traceback'] = trace
            if not output_json:
                console.print(trace)
                
        if output_json:
            console.print(json.dumps(result, indent=2))
            
        return result

def _validate_links_impl(cortex_path='.', fix=False, output_json=False, report=None, verbose=False):
    """
    Implementierung der Link-Validierung, die sowohl von CLI als auch programmatisch aufgerufen werden kann
    
    Returns:
        dict: Validierungsergebnis mit Status und Statistiken
    """
    try:
        from ..core.cross_vault_linker import CrossVaultLinker
        
        cortex_root = Path(cortex_path).resolve()
        if not output_json:
            console.print("[blue]🔍 Validiere Links im Cortex Workspace...[/blue]")
        
        linker = CrossVaultLinker(cortex_root)
        validation_result = linker.validate_links()
        
        # Verarbeite Validierungsergebnisse
        total_links = validation_result.get('total_links', 0)
        valid_links = validation_result.get('valid_links', 0)
        invalid_links = validation_result.get('invalid_links', [])
        
        result = {
            'success': True,
            'cortex_path': str(cortex_root),
            'total_links': total_links,
            'valid_links': valid_links,
            'invalid_links': invalid_links,
            'invalid_count': len(invalid_links)
        }
        
        if output_json:
            if report:
                with open(report, 'w') as f:
                    json.dump(validation_result, f, indent=2)
                console.print(f"[green]Bericht gespeichert in {report}[/green]")
            else:
                console.print(json.dumps(result, indent=2))
        else:
            console.print(f"[blue]Gesamtzahl Links: {total_links}[/blue]")
            console.print(f"[green]Gültige Links: {valid_links}[/green]")
            console.print(f"[yellow]Ungültige Links: {len(invalid_links)}[/yellow]")
            
            if invalid_links:
                table = Table(title="Ungültige Links")
                table.add_column("Quelle", style="cyan")
                table.add_column("Ziel", style="yellow")
                table.add_column("Grund", style="red")
                
                for link in invalid_links:
                    table.add_row(
                        str(link.get('source', 'Unbekannt')),
                        str(link.get('target', 'Unbekannt')),
                        link.get('reason', 'Unbekannter Fehler')
                    )
                
                console.print(table)
                
                if fix:
                    console.print("[blue]🔧 Versuche, ungültige Links zu reparieren...[/blue]")
                    fix_result = linker.fix_invalid_links(invalid_links)
                    fixed_count = fix_result.get('fixed_links', 0)
                    console.print(f"[green]✅ {fixed_count} Links repariert[/green]")
                    result['fixed_links'] = fixed_count
                    
                    unfixable = fix_result.get('unfixable_links', [])
                    if unfixable:
                        console.print(f"[yellow]⚠️ {len(unfixable)} Links konnten nicht repariert werden[/yellow]")
                        result['unfixable_links'] = unfixable
            else:
                console.print("[green]✅ Alle Links sind gültig![/green]")
                
            if report:
                with open(report, 'w') as f:
                    json.dump(validation_result, f, indent=2)
                console.print(f"[green]Bericht gespeichert in {report}[/green]")
                result['report_path'] = str(report)
                
        return result
                
    except Exception as e:
        error_msg = f"Fehler bei der Link-Validierung: {str(e)}"
        result = {
            'success': False,
            'error': error_msg,
            'error_type': type(e).__name__
        }
        
        if not output_json:
            console.print(f"[red]{error_msg}[/red]")
            
        if verbose:
            import traceback
            trace = traceback.format_exc()
            result['traceback'] = trace
            if not output_json:
                console.print(trace)
                
        if output_json:
            console.print(json.dumps(result, indent=2))
            
        return result

# Programmatische Zugriffsfunktionen

def rule_linker_command(**kwargs):
    """Programmatischer Zugriff auf Rule-Linker"""
    return _rule_linker_impl(**kwargs)

def validate_command(**kwargs):
    """Programmatischer Zugriff auf Link-Validierung"""
    return _validate_links_impl(**kwargs)
