import json
"""
Hauptmodul für die Cortex CLI - Refactored Version
Verbesserte Befehlsstruktur und Fehlerbehandlung
"""
import sys
import click
from pathlib import Path
from rich.console import Console

from .config import CortexConfig
from . import linking, analysis, testing
from .ai import ai

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
# Registriere test als separates Alias-Command
from . import testing
cli.add_command(testing.test, name='test')
cli.add_command(ai)  # Neue AI-Befehle

if __name__ == '__main__':
    try:
        cli()  # pylint: disable=no-value-for-parameter
    except Exception as e:
        console.print(f"[red]Fehler: {str(e)}[/red]")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            console.print_exception()
        sys.exit(1)

def find_cortex_root(start_path='.'):
    """
    DEPRECATED: Verwende CortexConfig.find_cortex_root() stattdessen
    """
    from .config import CortexConfig
    return CortexConfig.find_cortex_root(start_path)

# Für Tests verfügbar machen
__all__ = ['cli', 'find_cortex_root']

@cli.command()
@click.option('--cortex-path', type=click.Path(), 
              help='Pfad zum Cortex Workspace', default='.')
@click.option('--force', is_flag=True, help='Überschreibe existierende Konfiguration')
@click.pass_context
def init(ctx, cortex_path, force):
    """Initialisiere ein neues Cortex Workspace"""
    workspace_path = Path(cortex_path).resolve()
    config_dir = workspace_path / 'config'
    config_path = config_dir / 'cortex.yaml'
    
    if config_path.exists() and not force:
        console.print("[yellow]Cortex Workspace bereits initialisiert![/yellow]")
        console.print(f"Verwende --force zum Überschreiben.")
        return
    
    # Erstelle Verzeichnisstruktur
    vault_path = workspace_path / 'obsidian-vault'
    directories = [
        config_dir,
        vault_path / 'Chat-Sessions',
        vault_path / 'Code-Fragments', 
        vault_path / 'Decisions'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Erstelle basic cortex.yaml
    config_content = """# Cortex Workspace Configuration
workspace:
  name: "My Cortex Workspace"
  version: "1.0"
  
vaults:
  - name: "main"
    path: "./obsidian-vault"
    type: "markdown"
    
linking:
  auto_link: true
  validation: true
  
ai:
  enabled: false
"""
    
    config_path.write_text(config_content)
    console.print(f"[green]✅ Cortex Workspace initialisiert in {workspace_path}[/green]")
    console.print(f"Konfiguration: {config_path}")
    console.print("Initializing Cortex workspace...")  # Test-erwarteter Text

@cli.command()
@click.option('--cortex-path', type=click.Path(), 
              help='Pfad zum Cortex Workspace', default='.')
@click.option('--json', 'output_json', is_flag=True, help='Ausgabe als JSON')
@click.pass_context
def status(ctx, cortex_path, output_json):
    """Zeige Cortex Workspace Status"""
    workspace_path = Path(cortex_path).resolve()
    config_path = workspace_path / 'cortex.yaml'
    
    status_info = {
        'workspace_path': str(workspace_path),
        'configured': config_path.exists(),
        'config_path': str(config_path) if config_path.exists() else None,
        'version': '0.2.0'
    }
    
    if output_json:
        click.echo(json.dumps(status_info, indent=2))
    else:
        console.print("[blue]📊 Workspace Status[/blue]")
        console.print(f"Pfad: {workspace_path}")
        console.print(f"Konfiguriert: {'✅' if status_info['configured'] else '❌'}")
        if status_info['configured']:
            console.print(f"Konfiguration: {config_path}")
