"""
Validierungs-Funktionalität für Cortex-AI
"""
import json
import sys
import click
from pathlib import Path
from rich.console import Console

console = Console()

@click.command(name='validate')
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

def validate(**kwargs):
    """Programmatischer Zugriff auf Validate-Befehl"""
    return _validate_impl(**kwargs)
