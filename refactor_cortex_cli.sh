#!/bin/bash
# filepath: /workspaces/cortex-py/refactor_cortex_cli.sh

set -e  # Exit on any error

echo "=== Cortex-CLI Refactoring ==="
echo "Basierend auf den Empfehlungen in improvement_suggestions.md"
echo ""

# Definiere wichtige Pfade
CORTEX_CLI_DIR="/workspaces/cortex-py/cortex-cli"
BACKUP_DIR="${CORTEX_CLI_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
TEMP_DIR="/tmp/cortex_refactor"

# Erstelle Backup des original Projekts
echo "1. Erstelle Backup des originalen Projekts in ${BACKUP_DIR}..."
cp -r "$CORTEX_CLI_DIR" "$BACKUP_DIR"
mkdir -p "$TEMP_DIR"

# Wechsle zum Projektverzeichnis
cd "$CORTEX_CLI_DIR"

echo "2. Verbessere Befehlsstruktur und Fehlerbehandlung..."

# Verbessere die Hauptmodule für CLI
cat > cortex/cli/main.py << 'EOF'
"""
Hauptmodul für die Cortex CLI - Refactored Version
Verbesserte Befehlsstruktur und Fehlerbehandlung
"""
import sys
import click
from pathlib import Path
from rich.console import Console

from cortex.cli import linking, analysis, testing
from cortex.cli.ai_commands import ai

console = Console()

# Gemeinsame Kontextvariablen
pass_context = click.make_pass_decorator(dict, ensure=True)

@click.group()
@click.option('--cortex-path', type=click.Path(exists=True), 
              help='Pfad zum Cortex Workspace', default='.')
@click.option('--verbose', '-v', is_flag=True, help='Ausführliche Ausgabe aktivieren')
@click.option('--json', is_flag=True, help='Ausgabe als JSON')
@click.option('--programmatic', is_flag=True, hidden=True, 
              help='Programmatischer Modus (keine Konsolen-Ausgabe)')
@click.version_option(version='0.2.0')
@pass_context
def cli(ctx, cortex_path, verbose, json, programmatic):
    """Cortex Command Line Interface - Werkzeuge zur Verwaltung und Analyse von Cortex Workspaces"""
    ctx['cortex_path'] = Path(cortex_path).resolve()
    ctx['verbose'] = verbose
    ctx['json_output'] = json
    ctx['programmatic'] = programmatic
    
    # Konfiguriere Rich Console basierend auf Parametern
    if programmatic:
        console.quiet = True  # Unterdrücke Rich-Ausgaben im programmatischen Modus

# Registriere Unterbefehlsgruppen
cli.add_command(linking.linking)
cli.add_command(analysis.analysis)
cli.add_command(testing.testing)
cli.add_command(ai)  # Neue AI-Befehle

if __name__ == '__main__':
    try:
        cli()  # pylint: disable=no-value-for-parameter
    except Exception as e:
        console.print(f"[red]Fehler: {str(e)}[/red]")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            console.print_exception()
        sys.exit(1)
EOF

# Verbessere linking.py mit besserer Fehlerbehandlung und programmatischem Zugriff
cat > cortex/cli/linking.py << 'EOF'
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
EOF

# Erstelle neue Datei für AI-Befehle
mkdir -p cortex/cli
cat > cortex/cli/ai_commands.py << 'EOF'
"""
Cortex AI Integration Befehle
"""
import json
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

console = Console()

@click.group(name="ai")
def ai():
    """Cortex-AI Befehle für Chat und Analyse"""
    pass

@ai.command(name='chat')
@click.option('--vault-id', type=int, default=1, help='ID des Vaults (Standard: 1)')
@click.option('-i', '--interactive', is_flag=True, help='Interaktiver Chat-Modus')
@click.option('-m', '--message', help='Einmalige Nachricht senden')
@click.option('--json', 'output_json', is_flag=True, help='Ausgabe als JSON')
@click.pass_context
def chat_command(ctx, vault_id, interactive, message, output_json):
    """Chat mit Cortex-AI"""
    
    result = _chat_impl(
        vault_id=vault_id,
        interactive=interactive,
        message=message,
        output_json=output_json,
        verbose=ctx.obj.get('verbose', False) if ctx.obj else False
    )
    
    # Im programmatischen Modus gibt die Funktion das Ergebnis zurück
    if ctx.obj and ctx.obj.get('programmatic'):
        return result

@ai.command(name='analyze')
@click.option('--vault-id', type=int, default=1, help='ID des Vaults (Standard: 1)')
@click.option('-f', '--file', type=click.Path(exists=True), help='Zu analysierende Datei')
@click.option('-c', '--content', help='Zu analysierender Inhalt')
@click.option('--json', 'output_json', is_flag=True, help='Ausgabe als JSON')
@click.pass_context
def analyze_command(ctx, vault_id, file, content, output_json):
    """Inhalte mit Cortex-AI analysieren"""
    
    result = _analyze_impl(
        vault_id=vault_id,
        file=file,
        content=content,
        output_json=output_json,
        verbose=ctx.obj.get('verbose', False) if ctx.obj else False
    )
    
    # Im programmatischen Modus gibt die Funktion das Ergebnis zurück
    if ctx.obj and ctx.obj.get('programmatic'):
        return result

@ai.command(name='validate')
@click.option('--json', 'output_json', is_flag=True, help='Ausgabe als JSON')
@click.pass_context
def validate_command(ctx, output_json):
    """Links mit Cortex-AI validieren"""
    
    result = _validate_impl(
        output_json=output_json,
        verbose=ctx.obj.get('verbose', False) if ctx.obj else False
    )
    
    # Im programmatischen Modus gibt die Funktion das Ergebnis zurück
    if ctx.obj and ctx.obj.get('programmatic'):
        return result

def _chat_impl(vault_id=1, interactive=False, message=None, output_json=False, verbose=False):
    """
    Implementierung des Chat-Befehls
    
    Args:
        vault_id: ID des Vaults
        interactive: Ob interaktiver Chat-Modus verwendet werden soll
        message: Einmalige Nachricht
        output_json: Ob Ausgabe als JSON erfolgen soll
        verbose: Ob ausführliche Ausgabe aktiviert ist
        
    Returns:
        dict: Ergebnis mit Status und Daten
    """
    try:
        from ..integrations.cortex_ai.client import get_client
        client = get_client()
        
        if not client.is_enabled():
            error_msg = "Cortex-AI Integration ist nicht aktiviert"
            
            if not output_json:
                console.print(f"[red]{error_msg}[/red]")
                console.print("[yellow]Aktivieren Sie die Integration in der Konfigurationsdatei.[/yellow]")
                
            return {
                'success': False,
                'error': error_msg
            }
            
        result = {
            'success': True,
            'vault_id': vault_id,
            'interactive': interactive
        }
        
        if interactive:
            if not output_json:
                console.print("Cortex-AI Chat (Drücke [bold red]Strg+C[/bold red] zum Beenden)")
                console.print("----------------------------------------")
            
            chat_history = []
            
            try:
                while True:
                    if not output_json:
                        message = input("\nDu: ")
                    
                    if not message.strip():
                        continue
                        
                    response = client.chat(message, vault_id)
                    
                    if "error" in response:
                        error_msg = f"Fehler: {response['error']}"
                        if not output_json:
                            console.print(f"[red]{error_msg}[/red]")
                        continue
                    
                    chat_entry = {
                        'user': message,
                        'ai': response.get('message', 'Keine Antwort erhalten'),
                        'links': response.get('links', [])
                    }
                    chat_history.append(chat_entry)
                    
                    if not output_json:
                        console.print("\n[bold green]Cortex-AI:[/bold green]", end=" ")
                        console.print(Markdown(response.get('message', 'Keine Antwort erhalten')))
                        
                        # Zeige Links an, falls vorhanden
                        links = response.get('links', [])
                        if links:
                            console.print("\n[bold blue]Verknüpfungen:[/bold blue]")
                            for link in links:
                                console.print(f"  - {link['link_text']} [dim]({link['target_type']})[/dim]")
            except KeyboardInterrupt:
                if not output_json:
                    console.print("\n[yellow]Chat beendet.[/yellow]")
                result['chat_history'] = chat_history
        else:
            # Einmalige Nachricht senden
            if not message:
                error_msg = "Keine Nachricht angegeben"
                if not output_json:
                    console.print(f"[red]{error_msg}[/red]")
                return {
                    'success': False,
                    'error': error_msg
                }
                
            response = client.chat(message, vault_id)
            
            if "error" in response:
                error_msg = f"Fehler: {response['error']}"
                if not output_json:
                    console.print(f"[red]{error_msg}[/red]")
                return {
                    'success': False,
                    'error': response['error']
                }
                
            result['message'] = message
            result['response'] = response.get('message', 'Keine Antwort erhalten')
            result['links'] = response.get('links', [])
            
            if not output_json:
                console.print(Markdown(response.get('message', 'Keine Antwort erhalten')))
                
                # Zeige Links an, falls vorhanden
                links = response.get('links', [])
                if links:
                    console.print("\n[bold blue]Verknüpfungen:[/bold blue]")
                    for link in links:
                        console.print(f"  - {link['link_text']} [dim]({link['target_type']})[/dim]")
        
        if output_json:
            console.print(json.dumps(result, indent=2))
            
        return result
        
    except Exception as e:
        error_msg = f"Fehler im Chat-Befehl: {str(e)}"
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

def _analyze_impl(vault_id=1, file=None, content=None, output_json=False, verbose=False):
    """
    Implementierung des Analyze-Befehls
    
    Args:
        vault_id: ID des Vaults
        file: Pfad zur zu analysierenden Datei
        content: Zu analysierender Inhalt
        output_json: Ob Ausgabe als JSON erfolgen soll
        verbose: Ob ausführliche Ausgabe aktiviert ist
        
    Returns:
        dict: Ergebnis mit Status und Daten
    """
    try:
        from ..integrations.cortex_ai.client import get_client
        client = get_client()
        
        if not client.is_enabled():
            error_msg = "Cortex-AI Integration ist nicht aktiviert"
            
            if not output_json:
                console.print(f"[red]{error_msg}[/red]")
                console.print("[yellow]Aktivieren Sie die Integration in der Konfigurationsdatei.[/yellow]")
                
            return {
                'success': False,
                'error': error_msg
            }
            
        # Inhalt beschaffen
        analyze_content = ""
        source_path = None
        
        if file:
            try:
                with open(file, 'r') as f:
                    analyze_content = f.read()
                source_path = file
            except Exception as e:
                error_msg = f"Fehler beim Lesen der Datei {file}: {str(e)}"
                if not output_json:
                    console.print(f"[red]{error_msg}[/red]")
                return {
                    'success': False,
                    'error': error_msg
                }
        elif content:
            analyze_content = content
        else:
            error_msg = "Weder Datei noch Inhalt angegeben"
            if not output_json:
                console.print(f"[red]{error_msg}[/red]")
            return {
                'success': False,
                'error': error_msg
            }
            
        if not output_json:
            console.print("[blue]🔍 Analysiere Inhalt mit Cortex-AI...[/blue]")
            
        response = client.analyze_content(analyze_content, source_path, vault_id)
        
        if "error" in response:
            error_msg = f"Fehler: {response['error']}"
            if not output_json:
                console.print(f"[red]{error_msg}[/red]")
            return {
                'success': False,
                'error': response['error']
            }
            
        result = {
            'success': True,
            'vault_id': vault_id,
            'source_path': source_path,
            'content_length': len(analyze_content),
            'analysis': response
        }
        
        # Zeige Links an
        links = response.get('links', [])
        if not output_json:
            if links:
                console.print(f"[green]{len(links)} potentielle Verknüpfungen gefunden:[/green]")
                for link in links:
                    target_id = link.get('target_chat_id') or link.get('target_external_id', '')
                    console.print(f"  - {link['link_text']} -> {link['target_type']} " + 
                                f"[dim]{target_id}[/dim]")
            else:
                console.print("[yellow]Keine relevanten Verknüpfungen gefunden.[/yellow]")
        
        if output_json:
            console.print(json.dumps(result, indent=2))
            
        return result
        
    except Exception as e:
        error_msg = f"Fehler im Analyze-Befehl: {str(e)}"
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

def _validate_impl(output_json=False, verbose=False):
    """
    Implementierung des Validate-Befehls
    
    Args:
        output_json: Ob Ausgabe als JSON erfolgen soll
        verbose: Ob ausführliche Ausgabe aktiviert ist
        
    Returns:
        dict: Ergebnis mit Status und Daten
    """
    try:
        from ..integrations.cortex_ai.client import get_client
        client = get_client()
        
        if not client.is_enabled():
            error_msg = "Cortex-AI Integration ist nicht aktiviert"
            
            if not output_json:
                console.print(f"[red]{error_msg}[/red]")
                console.print("[yellow]Aktivieren Sie die Integration in der Konfigurationsdatei.[/yellow]")
                
            return {
                'success': False,
                'error': error_msg
            }
            
        if not output_json:
            console.print("[blue]🔍 Validiere Links mit Cortex-AI...[/blue]")
            
        response = client.validate_links()
        
        if "error" in response:
            error_msg = f"Fehler: {response['error']}"
            if not output_json:
                console.print(f"[red]{error_msg}[/red]")
            return {
                'success': False,
                'error': response['error']
            }
            
        result = {
            'success': True,
            'validation': response
        }
        
        invalid_links = response.get('invalid_links', 0)
        
        if not output_json:
            if invalid_links > 0:
                console.print(f"[yellow]{invalid_links} ungültige Links gefunden![/yellow]")
                
                # Zeige Gründe an
                reason_counts = response.get('reason_counts', {})
                if reason_counts:
                    console.print("\n[bold blue]Häufigste Gründe:[/bold blue]")
                    for reason, count in reason_counts.items():
                        console.print(f"  - {reason}: {count}x")
                
                # Zeige Vorschläge an
                suggestions = response.get('suggestions', [])
                if suggestions:
                    console.print("\n[bold green]Verbesserungsvorschläge:[/bold green]")
                    for suggestion in suggestions:
                        console.print(f"  - {suggestion}")
            else:
                console.print("[green]✅ Alle Links sind gültig.[/green]")
        
        if output_json:
            console.print(json.dumps(result, indent=2))
            
        return result
        
    except Exception as e:
        error_msg = f"Fehler im Validate-Befehl: {str(e)}"
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

def chat(**kwargs):
    """Programmatischer Zugriff auf Chat-Befehl"""
    return _chat_impl(**kwargs)

def analyze(**kwargs):
    """Programmatischer Zugriff auf Analyze-Befehl"""
    return _analyze_impl(**kwargs)

def validate(**kwargs):
    """Programmatischer Zugriff auf Validate-Befehl"""
    return _validate_impl(**kwargs)
EOF

# Erstelle Integrationsverzeichnis und Client für Cortex-AI
mkdir -p cortex/integrations/cortex_ai
touch cortex/integrations/cortex_ai/__init__.py

cat > cortex/integrations/cortex_ai/client.py << 'EOF'
"""
Client-Modul für die Integration mit dem Cortex-AI System
"""
import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

from cortex.utils.yaml_utils import load_config

class CortexAIClient:
    """Client für die Kommunikation mit dem Cortex-AI System"""
    
    def __init__(self, config_path=None):
        """Initialisiert den Client mit Konfiguration"""
        self.config = load_config(config_path)
        self.ai_config = self.config.get('cortex_ai', {})
        self.api_url = self.ai_config.get('api_url', 'http://localhost:8000')
        
    def is_enabled(self) -> bool:
        """Prüft, ob die Cortex-AI Integration aktiviert ist"""
        return self.ai_config.get('enabled', False)
    
    def chat(self, message: str, vault_id: int = 1) -> Dict[str, Any]:
        """Sendet eine Chat-Nachricht an das Cortex-AI System"""
        if not self.is_enabled():
            return {"error": "Cortex-AI Integration ist nicht aktiviert"}
            
        try:
            response = requests.post(
                f"{self.api_url}/api/chat",
                json={"content": message, "vault_id": vault_id},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Fehler bei der Kommunikation mit Cortex-AI: {str(e)}"}
    
    def analyze_content(self, content: str, path: Optional[str] = None, vault_id: int = 1) -> Dict[str, Any]:
        """Analysiert Inhalte mit dem Cortex-AI System"""
        if not self.is_enabled():
            return {"error": "Cortex-AI Integration ist nicht aktiviert"}
            
        try:
            response = requests.post(
                f"{self.api_url}/api/analyze",
                json={"content": content, "path": path, "vault_id": vault_id},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Fehler bei der Analyse mit Cortex-AI: {str(e)}"}
    
    def validate_links(self) -> Dict[str, Any]:
        """Validiert Links mit dem Cortex-AI System"""
        if not self.is_enabled():
            return {"error": "Cortex-AI Integration ist nicht aktiviert"}
            
        try:
            response = requests.get(
                f"{self.api_url}/api/links/validate",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Fehler bei der Link-Validierung mit Cortex-AI: {str(e)}"}

# Singleton-Instanz
_client = None

def get_client(config_path=None) -> CortexAIClient:
    """Gibt eine Singleton-Instanz des Clients zurück"""
    global _client
    if _client is None:
        _client = CortexAIClient(config_path)
    return _client
EOF

# Verbessere cortex-cmd Datei
cat > bin/cortex-cmd << 'EOF'
#!/bin/bash
# Cortex Global Command - Universal Access to Cortex System
# Usage: cortex [command] [options]
# Updated for Refactored CLI System

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_CLI_PATH="$(dirname "$SCRIPT_DIR")"

# Color codes for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Error handling function
handle_error() {
    echo -e "${RED}❌ Fehler: $1${NC}"
    exit 1
}

# Function to check Python dependencies
check_dependencies() {
    python -c "import click, rich" &>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️ Fehlende Abhängigkeiten. Installation wird durchgeführt...${NC}"
        pip install -r "$CORTEX_CLI_PATH/requirements.txt" || handle_error "Abhängigkeiten konnten nicht installiert werden"
    fi
}

# Check if Python is available
if ! command -v python &>/dev/null; then
    handle_error "Python ist nicht installiert"
fi

# Check dependencies
check_dependencies

# Execute the Python CLI
cd "$CORTEX_CLI_PATH"
python -m cortex.cli.main "$@"
exit $?
EOF
chmod +x bin/cortex-cmd

# Erstelle Web-Interface-Starter
cat > bin/cortex-ai << 'EOF'
#!/bin/bash
# Cortex-AI Web Interface Starter
# Startet den Cortex-AI Server und öffnet die Webanwendung im Browser

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_CLI_PATH="$(dirname "$SCRIPT_DIR")"
CORTEX_PATH="$(dirname "$CORTEX_CLI_PATH")"
CORTEX_AI_PATH="${CORTEX_PATH}/cortex-ai"

# Color codes for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Error handling function
handle_error() {
    echo -e "${RED}❌ Fehler: $1${NC}"
    exit 1
}

# Check for uvicorn
if ! command -v uvicorn &>/dev/null; then
    echo -e "${YELLOW}⚠️ Uvicorn nicht gefunden. Installation wird durchgeführt...${NC}"
    pip install uvicorn || handle_error "Uvicorn konnte nicht installiert werden"
fi

# Parse command line arguments
PORT=8000
NO_BROWSER=0

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --port=*)
            PORT="${1#*=}"
            ;;
        --port)
            PORT="$2"
            shift
            ;;
        --no-browser)
            NO_BROWSER=1
            ;;
        *)
            echo -e "${YELLOW}⚠️ Unbekannte Option: $1${NC}"
            ;;
    esac
    shift
done

# Check if Cortex-AI directory exists
if [ ! -d "$CORTEX_AI_PATH" ]; then
    handle_error "Cortex-AI Verzeichnis nicht gefunden: $CORTEX_AI_PATH"
fi

# Start the server
echo -e "${BLUE}🚀 Starte Cortex-AI Server auf Port $PORT...${NC}"
cd "$CORTEX_AI_PATH"

# Start server in background
uvicorn app.main:app --reload --port=$PORT &
SERVER_PID=$!

# Wait for server to start
echo -e "${YELLOW}⏳ Warte auf Server-Start...${NC}"
sleep 3

# Check if server started successfully
if ! kill -0 $SERVER_PID 2>/dev/null; then
    handle_error "Server konnte nicht gestartet werden"
fi

# Open browser
if [ $NO_BROWSER -eq 0 ]; then
    echo -e "${GREEN}✅ Öffne Browser...${NC}"
    "$BROWSER" "http://localhost:$PORT" || echo -e "${YELLOW}⚠️ Browser konnte nicht geöffnet werden${NC}"
fi

echo -e "${GREEN}✅ Cortex-AI läuft auf http://localhost:$PORT${NC}"
echo -e "${YELLOW}Drücke Strg+C zum Beenden${NC}"

# Trap Ctrl+C
trap "echo -e '${BLUE}🛑 Beende Server...${NC}'; kill $SERVER_PID; exit 0" INT

# Keep script running until Ctrl+C
wait $SERVER_PID
EOF
chmod +x bin/cortex-ai

# Aktualisiere requirements.txt
cat > requirements.txt << 'EOF'
# Kern-Abhängigkeiten
click>=8.0.0
pyyaml>=6.0.0
rich>=12.0.0
requests>=2.28.0

# Optionale Abhängigkeiten für volles Feature-Set
aiohttp>=3.8.0
watchdog>=2.1.0
aiofiles>=0.8.0
asyncio-mqtt>=0.11.0
python-dateutil>=2.8.0
schedule>=1.2.0

# Test-Abhängigkeiten (nur für Entwicklung)
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
EOF

# Erstelle requirements-dev.txt für Entwicklungsabhängigkeiten
cat > requirements-dev.txt << 'EOF'
# Kern-Abhängigkeiten
-r requirements.txt

# Entwicklungs-Tools
black>=22.0.0
pylint>=2.14.0
mypy>=0.971
flake8>=5.0.0
isort>=5.10.0

# Dokumentation
sphinx>=5.0.0
sphinx-rtd-theme>=1.0.0
EOF

# Erstelle Installationsskript
cat > install.sh << 'EOF'
#!/bin/bash
# Cortex-CLI Installationsskript

# Farben für bessere Ausgabe
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Keine Farbe

# Fehlerbehebungsfunktion
handle_error() {
    echo -e "${RED}❌ Fehler: $1${NC}"
    exit 1
}

# Optionen
INSTALL_DEV=0
INSTALL_AI=0

# Befehlszeilenargumente verarbeiten
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dev)
            INSTALL_DEV=1
            ;;
        --ai)
            INSTALL_AI=1
            ;;
        --help)
            echo "Cortex-CLI Installationsskript"
            echo ""
            echo "Optionen:"
            echo "  --dev    Installiert auch Entwicklungsabhängigkeiten"
            echo "  --ai     Installiert auch Cortex-AI Abhängigkeiten"
            echo "  --help   Zeigt diese Hilfe an"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}⚠️ Unbekannte Option: $1${NC}"
            ;;
    esac
    shift
done

# Basis-Installation
echo -e "${BLUE}🔧 Installiere Kern-Abhängigkeiten...${NC}"
pip install -r requirements.txt || handle_error "Kern-Abhängigkeiten konnten nicht installiert werden"

# Entwicklungsabhängigkeiten
if [ $INSTALL_DEV -eq 1 ]; then
    echo -e "${BLUE}🔧 Installiere Entwicklungsabhängigkeiten...${NC}"
    pip install -r requirements-dev.txt || handle_error "Entwicklungsabhängigkeiten konnten nicht installiert werden"
fi

# Cortex-AI Abhängigkeiten
if [ $INSTALL_AI -eq 1 ]; then
    echo -e "${BLUE}🔧 Installiere Cortex-AI Abhängigkeiten...${NC}"
    pip install uvicorn fastapi sqlalchemy || handle_error "Cortex-AI Abhängigkeiten konnten nicht installiert werden"
fi

# Ausführungsrechte setzen
echo -e "${BLUE}🔧 Setze Ausführungsrechte...${NC}"
chmod +x bin/cortex-cmd
chmod +x bin/cortex-ai

# Symbolische Links erstellen
echo -e "${BLUE}🔧 Erstelle symbolische Links...${NC}"
mkdir -p ~/.local/bin

if [ -f ~/.local/bin/cortex ]; then
    echo -e "${YELLOW}⚠️ ~/.local/bin/cortex existiert bereits. Überschreiben? (j/n)${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        ln -sf "$(pwd)/bin/cortex-cmd" ~/.local/bin/cortex
    fi
else
    ln -sf "$(pwd)/bin/cortex-cmd" ~/.local/bin/cortex
fi

if [ $INSTALL_AI -eq 1 ]; then
    ln -sf "$(pwd)/bin/cortex-ai" ~/.local/bin/cortex-ai
fi

echo -e "${GREEN}✅ Installation abgeschlossen!${NC}"
echo -e "${BLUE}Führe 'cortex --help' aus, um zu beginnen.${NC}"

# Überprüfe, ob ~/.local/bin im PATH ist
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}⚠️ $HOME/.local/bin ist nicht im PATH.${NC}"
    echo -e "${YELLOW}   Füge die folgende Zeile zu deiner Shell-Konfiguration hinzu:${NC}"
    echo -e "${BLUE}   export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
fi
EOF
chmod +x install.sh

# Aktualisiere Dokumentation für bessere Verständlichkeit
cat > README.md << 'EOF'
# Cortex-CLI

Eine umfassende Befehlszeilen-Schnittstelle für Cortex-Workspaces.

## Installation

```bash
# Grundinstallation
./install.sh

# Mit Entwicklertools
./install.sh --dev

# Mit Cortex-AI Integration
./install.sh --ai
```

## Verwendung

```bash
# Hilfe anzeigen
cortex --help

# Link-Befehle
cortex linking --help
cortex linking validate
cortex linking rule-linker --run

# Analysebefehle
cortex analyze --help

# Testbefehle
cortex test --help

# Cortex-AI Befehle (wenn aktiviert)
cortex ai --help
cortex ai chat -i  # Interaktiver Chat
cortex ai analyze -f datei.md
cortex ai validate
```

## Cortex-AI Webanwendung

```bash
# Starten der Webanwendung
cortex-ai

# Mit angepasstem Port
cortex-ai --port=8080

# Ohne Browser zu öffnen
cortex-ai --no-browser
```

## Programmierbare API

Sie können die Cortex-Funktionen auch aus Ihrem eigenen Python-Code aufrufen:

```python
from cortex.cli.linking import validate_command
from cortex.cli.ai_commands import chat, analyze

# Link-Validierung ausführen
result = validate_command(cortex_path='/path/to/workspace', fix=True)
print(f"Ergebnis: {result['success']}")

# Mit Cortex-AI chatten
chat_result = chat(message="Was ist Cortex?", vault_id=1)
print(f"Antwort: {chat_result['response']}")
```

## Konfiguration

Die Konfiguration erfolgt über die Datei `config/cortex.yaml`. Um Cortex-AI zu aktivieren, fügen Sie folgendes hinzu:

```yaml
cortex_ai:
  enabled: true
  api_url: "http://localhost:8000"
```

## Entwicklung

```bash
# Installieren der Entwicklungsabhängigkeiten
./install.sh --dev

# Tests ausführen
pytest

# Code-Stil prüfen
black cortex/
pylint cortex/
```
EOF

echo "3. Aktualisiere Konfigurationsdatei mit Cortex-AI Einstellungen..."

# Aktualisiere Konfigurationsdatei
cat > config/cortex.yaml << 'EOF'
# Cortex Configuration File

# Allgemeine Einstellungen
general:
  log_level: "info"
  workspace_path: "."
  
# Linking-Einstellungen
linking:
  auto_link: true
  min_confidence: 0.75
  rules_path: "rules"
  
# Vault-Einstellungen
vaults:
  enabled: true
  paths:
    - "~/obsidian/vault1"
    - "~/obsidian/vault2"
    
# Cortex-AI Integration
cortex_ai:
  enabled: false  # Auf true setzen, um Cortex-AI zu aktivieren
  api_url: "http://localhost:8000"
  storage:
    type: "sqlite"
    path: "../cortex-ai/data/cortex.db"
  features:
    chat_storage: true
    auto_linking: true
    link_validation: true
    link_analysis: true
EOF

echo "4. Erstelle verbesserte Tests mit besserer Testbarkeit..."

# Verbessere test_utils für bessere Testbarkeit
cat > tests/enhanced_test_utils.py << 'EOF'
"""
Enhanced test utilities with proper workspace setup and CLI runner configuration
"""
import os
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager
from click.testing import CliRunner
from unittest.mock import patch

class CortexTestRunner(CliRunner):
    """Enhanced CLI runner for Cortex tests with proper workspace setup"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_workspace = None
    
    def setup_test_workspace(self):
        """Set up a temporary test workspace"""
        self.test_workspace = tempfile.mkdtemp(prefix="cortex_test_")
        
        # Create sample vault directories and files
        sample_vault_path = Path(self.test_workspace) / "sample_vault"
        sample_vault_path.mkdir(exist_ok=True)
        
        # Create config directory
        config_path = Path(self.test_workspace) / "config"
        config_path.mkdir(exist_ok=True)
        
        # Create test config file
        config_content = """
        general:
          log_level: "debug"
          workspace_path: "."
          
        linking:
          auto_link: true
          min_confidence: 0.5
          
        cortex_ai:
          enabled: true
          api_url: "http://localhost:8000"
        """
        
        with open(config_path / "cortex.yaml", "w") as f:
            f.write(config_content)
            
        return self.test_workspace
    
    def cleanup_test_workspace(self):
        """Clean up the temporary test workspace"""
        if self.test_workspace and os.path.exists(self.test_workspace):
            shutil.rmtree(self.test_workspace)
            self.test_workspace = None
    
    @contextmanager
    def isolated_cortex_workspace(self):
        """Context manager for an isolated Cortex workspace"""
        workspace_path = self.setup_test_workspace()
        
        try:
            with patch('cortex.cli.main.load_config') as mock_load_config:
                mock_load_config.return_value = {
                    'general': {'workspace_path': workspace_path},
                    'linking': {'auto_link': True, 'min_confidence': 0.5},
                    'cortex_ai': {'enabled': True, 'api_url': 'http://localhost:8000'}
                }
                
                yield workspace_path
        finally:
            self.cleanup_test_workspace()
    
    def invoke_cortex(self, command, *args, **kwargs):
        """Invoke a Cortex command with proper setup"""
        from cortex.cli.main import cli
        
        # Create a list of command parts if a string is provided
        if isinstance(command, str):
            command = command.split()
            
        return self.invoke(cli, command, *args, **kwargs)


def create_test_content(content="Sample content", filename="test.md"):
    """Create test content for tests"""
    return {
        "content": content,
        "filename": filename
    }

@contextmanager
def mock_cortex_ai_client():
    """Mock the Cortex AI client for testing"""
    with patch('cortex.integrations.cortex_ai.client.get_client') as mock_get_client:
        mock_client = mock_get_client.return_value
        mock_client.is_enabled.return_value = True
        mock_client.chat.return_value = {
            "message": "This is a test response",
            "links": [{"link_text": "Test Link", "target_type": "file"}]
        }
        mock_client.analyze_content.return_value = {
            "links": [{"link_text": "Test Link", "target_type": "file"}]
        }
        mock_client.validate_links.return_value = {
            "invalid_links": 0
        }
        
        yield mock_client
EOF

# Erstelle Beispieltest für Cortex-AI Integration
cat > tests/test_ai_integration.py << 'EOF'
"""
Tests für die Cortex-AI Integration
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from cortex.cli.ai_commands import chat, analyze, validate
from tests.enhanced_test_utils import CortexTestRunner, mock_cortex_ai_client

@pytest.fixture
def runner():
    """Fixture for a CortexTestRunner"""
    runner = CortexTestRunner()
    try:
        yield runner
    finally:
        runner.cleanup_test_workspace()

def test_chat_command(runner):
    """Test the chat command"""
    with mock_cortex_ai_client() as mock_client:
        # Test programmatic chat
        result = chat(message="Test message", vault_id=1)
        assert result['success'] is True
        assert "response" in result
        
        # Test CLI chat
        cli_result = runner.invoke_cortex(['ai', 'chat', '-m', 'Test message'])
        assert cli_result.exit_code == 0
        assert "This is a test response" in cli_result.output
        
        mock_client.chat.assert_called_with("Test message", 1)

def test_analyze_command(runner):
    """Test the analyze command"""
    with mock_cortex_ai_client() as mock_client:
        # Create test file
        workspace = runner.setup_test_workspace()
        test_file = Path(workspace) / "test.md"
        test_file.write_text("This is test content")
        
        # Test programmatic analyze
        result = analyze(file=str(test_file), vault_id=1)
        assert result['success'] is True
        assert "links" in result['analysis']
        
        # Test CLI analyze
        cli_result = runner.invoke_cortex(['ai', 'analyze', '-f', str(test_file)])
        assert cli_result.exit_code == 0
        assert "potentielle Verknüpfungen gefunden" in cli_result.output
        
        # Make sure client was called with correct parameters
        mock_client.analyze_content.assert_called()

def test_validate_command(runner):
    """Test the validate command"""
    with mock_cortex_ai_client() as mock_client:
        # Test programmatic validate
        result = validate()
        assert result['success'] is True
        
        # Test CLI validate
        cli_result = runner.invoke_cortex(['ai', 'validate'])
        assert cli_result.exit_code == 0
        assert "Alle Links sind gültig" in cli_result.output
        
        mock_client.validate_links.assert_called()

def test_error_handling():
    """Test error handling in AI commands"""
    with patch('cortex.integrations.cortex_ai.client.get_client') as mock_get_client:
        mock_client = mock_get_client.return_value
        mock_client.is_enabled.return_value = False
        
        # Test disabled AI
        result = chat(message="Test")
        assert result['success'] is False
        assert "nicht aktiviert" in result['error']
        
        # Test exception handling
        mock_client.is_enabled.return_value = True
        mock_client.chat.side_effect = Exception("Test error")
        
        result = chat(message="Test", verbose=True)
        assert result['success'] is False
        assert "error" in result
        assert "traceback" in result
EOF

echo "5. Aktualisiere README.md mit aktueller Dokumentation..."

echo "Refactoring abgeschlossen! Die verbesserte Version des cortex-cli Projekts befindet sich in $CORTEX_CLI_DIR."
echo "Ein Backup des Originalprojekts wurde in $BACKUP_DIR erstellt."
echo "Verwende ./install.sh um die Refactored-Version zu installieren."
echo "Verwende 'cortex --help' um Hilfe zu den verfügbaren Befehlen anzuzeigen."