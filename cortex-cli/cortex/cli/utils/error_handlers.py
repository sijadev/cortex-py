"""
Standardisierte Error-Handler für Cortex CLI
"""
import json
import traceback
from rich.console import Console

console = Console()

def handle_standard_error(e, operation_name="Operation", output_json=False, verbose=False):
    """
    Standardisierter Error-Handler für CLI-Commands
    
    Args:
        e: Exception-Objekt
        operation_name: Name der Operation für die Fehlermeldung
        output_json: Ob Ausgabe als JSON erfolgen soll
        verbose: Ob ausführliche Ausgabe (mit Traceback) aktiviert ist
        
    Returns:
        dict: Standardisiertes Error-Result-Dictionary
    """
    error_msg = f"Fehler in {operation_name}: {str(e)}"
    result = {
        'success': False,
        'error': error_msg,
        'error_type': type(e).__name__
    }
    
    if not output_json:
        console.print(f"[red]{error_msg}[/red]")
        
    if verbose:
        trace = traceback.format_exc()
        result['traceback'] = trace
        if not output_json:
            console.print(trace)
            
    if output_json:
        console.print(json.dumps(result, indent=2))
        
    return result

def handle_integration_error(integration_name, output_json=False):
    """
    Spezieller Error-Handler für deaktivierte Integrationen
    
    Args:
        integration_name: Name der Integration
        output_json: Ob Ausgabe als JSON erfolgen soll
        
    Returns:
        dict: Error-Result für deaktivierte Integration
    """
    error_msg = f"{integration_name} Integration ist nicht aktiviert"
    
    if not output_json:
        console.print(f"[red]{error_msg}[/red]")
        console.print("[yellow]Aktivieren Sie die Integration in der Konfigurationsdatei.[/yellow]")
        
    return {
        'success': False,
        'error': error_msg
    }

def validate_required_param(param_name, param_value, output_json=False):
    """
    Validiert erforderliche Parameter
    
    Args:
        param_name: Name des Parameters
        param_value: Wert des Parameters  
        output_json: Ob Ausgabe als JSON erfolgen soll
        
    Returns:
        dict oder None: Error-Result falls Parameter fehlt, sonst None
    """
    if not param_value:
        error_msg = f"{param_name} ist erforderlich"
        if not output_json:
            console.print(f"[red]{error_msg}[/red]")
        return {
            'success': False,
            'error': error_msg
        }
    return None
