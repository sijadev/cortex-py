"""
Output-Formatter für Cortex CLI
"""
import json
from rich.console import Console
from rich.table import Table

console = Console()

def format_json_output(data, print_output=True):
    """
    Formatiert Daten als JSON-Ausgabe
    
    Args:
        data: Zu formatierende Daten
        print_output: Ob die Ausgabe gedruckt werden soll
        
    Returns:
        str: JSON-String
    """
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if print_output:
        console.print(json_str)
    return json_str

def create_result_table(title, data, success_key='success'):
    """
    Erstellt eine Rich-Tabelle für Ergebnisanzeige
    
    Args:
        title: Titel der Tabelle
        data: Dictionary mit Daten
        success_key: Key für Success-Status
        
    Returns:
        Table: Rich Table-Objekt
    """
    table = Table(title=title)
    table.add_column("Eigenschaft", style="cyan", no_wrap=True)
    table.add_column("Wert", style="green" if data.get(success_key) else "red")
    
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            value = str(len(value)) + " Einträge" if isinstance(value, list) else "Objekt"
        table.add_row(str(key), str(value))
    
    return table

def print_success_message(message, details=None):
    """
    Druckt eine Erfolgsmeldung
    
    Args:
        message: Hauptnachricht
        details: Optionale Details als Dictionary
    """
    console.print(f"[green]✅ {message}[/green]")
    if details:
        for key, value in details.items():
            console.print(f"  {key}: [bold]{value}[/bold]")

def print_warning_message(message, details=None):
    """
    Druckt eine Warnmeldung
    
    Args:
        message: Hauptnachricht  
        details: Optionale Details als Dictionary
    """
    console.print(f"[yellow]⚠️ {message}[/yellow]")
    if details:
        for key, value in details.items():
            console.print(f"  {key}: [dim]{value}[/dim]")

def print_info_message(message, details=None):
    """
    Druckt eine Informationsmeldung
    
    Args:
        message: Hauptnachricht
        details: Optionale Details als Dictionary  
    """
    console.print(f"[blue]ℹ️ {message}[/blue]")
    if details:
        for key, value in details.items():
            console.print(f"  {key}: {value}")

def format_command_output(result, output_json=False, operation_name="Operation"):
    """
    Standardisierte Ausgabeformatierung für CLI-Commands
    
    Args:
        result: Result-Dictionary
        output_json: Ob JSON-Ausgabe gewünscht ist
        operation_name: Name der Operation
    """
    if output_json:
        format_json_output(result)
    else:
        if result.get('success'):
            print_success_message(f"{operation_name} erfolgreich abgeschlossen", 
                                 {k: v for k, v in result.items() if k != 'success'})
        else:
            console.print(f"[red]❌ {operation_name} fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}[/red]")
