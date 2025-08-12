"""
Analyse-Funktionalität für Cortex-AI
"""
import json
import sys
import click
from pathlib import Path
from rich.console import Console

console = Console()

@click.command(name='analyze')
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
        from ...integrations.cortex_ai.client import get_client
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

def analyze(**kwargs):
    """Programmatischer Zugriff auf Analyze-Befehl"""
    return _analyze_impl(**kwargs)
