"""
Chat-Funktionalität für Cortex-AI
"""
import json
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

console = Console()

@click.command(name='chat')
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

def chat(**kwargs):
    """Programmatischer Zugriff auf Chat-Befehl"""
    return _chat_impl(**kwargs)
