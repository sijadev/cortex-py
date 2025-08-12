#!/bin/bash
# Erstelle das fehlende testing-Modul

cd /workspaces/cortex-py/cortex-cli

cat > cortex/cli/testing.py << 'EOF'
"""
Test-Befehle für Cortex CLI
Ausführen von Tests und Testberichten
"""
import json
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def testing():
    """Test-Befehle zur Überprüfung von Cortex-Komponenten"""
    pass

@testing.command(name='run')
@click.option('--cortex-path', type=click.Path(), 
              help='Pfad zum Cortex Workspace', default='.')
@click.option('--module', '-m', help='Spezifisches Modul testen')
@click.option('--verbose', '-v', is_flag=True, help='Ausführliche Ausgabe')
@click.option('--json', 'output_json', is_flag=True, help='Ausgabe als JSON')
@click.pass_context
def run_tests(ctx, cortex_path, module, verbose, output_json):
    """Tests für Cortex-Komponenten ausführen"""
    
    result = _run_tests_impl(
        cortex_path=cortex_path,
        module=module,
        verbose=verbose or ctx.obj.get('verbose', False) if ctx.obj else False,
        output_json=output_json
    )
    
    # Im programmatischen Modus gibt die Funktion das Ergebnis zurück
    if ctx.obj and ctx.obj.get('programmatic'):
        return result

@testing.command(name='analyze')
@click.option('--cortex-path', type=click.Path(), 
              help='Pfad zum Cortex Workspace', default='.')
@click.option('--report', type=click.Path(), help='Testbericht speichern')
@click.option('--json', 'output_json', is_flag=True, help='Ausgabe als JSON')
@click.pass_context
def analyze_tests(ctx, cortex_path, report, output_json):
    """Testabdeckung und -qualität analysieren"""
    
    result = _analyze_tests_impl(
        cortex_path=cortex_path,
        report=report,
        verbose=ctx.obj.get('verbose', False) if ctx.obj else False,
        output_json=output_json
    )
    
    # Im programmatischen Modus gibt die Funktion das Ergebnis zurück
    if ctx.obj and ctx.obj.get('programmatic'):
        return result

def _run_tests_impl(cortex_path='.', module=None, verbose=False, output_json=False):
    """
    Implementierung der Testausführung
    
    Returns:
        dict: Ergebnis mit Status und Daten
    """
    try:
        import pytest
        
        cortex_root = Path(cortex_path).resolve()
        if not output_json:
            console.print("[blue]🧪 Führe Tests aus...[/blue]")
            
        # Baue Pytest-Argumente
        pytest_args = ['-xvs'] if verbose else ['-x']
        
        if module:
            pytest_args.append(module)
        else:
            # Standardmäßig alle Tests ausführen
            pytest_args.append(str(cortex_root / 'tests'))
            
        # Führe Pytest aus
        pytest_result = pytest.main(pytest_args)
        
        success = pytest_result == 0
        
        result = {
            'success': success,
            'cortex_path': str(cortex_root),
            'exit_code': pytest_result,
            'module': module
        }
        
        if output_json:
            console.print(json.dumps(result, indent=2))
        else:
            if success:
                console.print("[green]✅ Alle Tests erfolgreich![/green]")
            else:
                console.print(f"[red]❌ Tests fehlgeschlagen (Exit-Code: {pytest_result})[/red]")
                
        return result
            
    except Exception as e:
        error_msg = f"Fehler bei der Testausführung: {str(e)}"
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

def _analyze_tests_impl(cortex_path='.', report=None, verbose=False, output_json=False):
    """
    Implementierung der Testanalyse
    
    Returns:
        dict: Analyseergebnis mit Status und Statistiken
    """
    try:
        import pytest
        from pytest_cov.plugin import CoverageError
        
        cortex_root = Path(cortex_path).resolve()
        if not output_json:
            console.print("[blue]🔍 Analysiere Testabdeckung...[/blue]")
        
        # Baue Pytest-Argumente für Coverage
        pytest_args = ['--cov=cortex', '--cov-report=term']
        
        if report:
            report_path = Path(report)
            if report_path.suffix.lower() == '.xml':
                pytest_args.append('--cov-report=xml:' + str(report_path))
            elif report_path.suffix.lower() == '.html':
                pytest_args.append('--cov-report=html:' + str(report_path.parent / 'htmlcov'))
            else:
                pytest_args.append('--cov-report=term-missing')
                
        # Führe Coverage-Analyse aus
        pytest_args.append(str(cortex_root / 'tests'))
        pytest_result = pytest.main(pytest_args)
        
        # Ergebnis sammeln
        result = {
            'success': pytest_result == 0,
            'cortex_path': str(cortex_root),
            'exit_code': pytest_result
        }
        
        if report:
            result['report_path'] = str(report)
            
        if output_json:
            console.print(json.dumps(result, indent=2))
        else:
            if result['success']:
                console.print("[green]✅ Testanalyse erfolgreich abgeschlossen![/green]")
                if report:
                    console.print(f"[blue]📊 Bericht gespeichert in: {report}[/blue]")
            else:
                console.print(f"[red]❌ Testanalyse fehlgeschlagen (Exit-Code: {pytest_result})[/red]")
                
        return result
                
    except CoverageError as e:
        error_msg = f"Coverage-Fehler: {str(e)}"
        result = {
            'success': False,
            'error': error_msg,
            'error_type': 'CoverageError'
        }
        
        if not output_json:
            console.print(f"[red]{error_msg}[/red]")
            console.print("[yellow]⚠️ Bitte stellen Sie sicher, dass pytest-cov installiert ist.[/yellow]")
            
        if output_json:
            console.print(json.dumps(result, indent=2))
            
        return result
            
    except Exception as e:
        error_msg = f"Fehler bei der Testanalyse: {str(e)}"
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

def run_tests(**kwargs):
    """Programmatischer Zugriff auf Testausführung"""
    return _run_tests_impl(**kwargs)

def analyze_tests(**kwargs):
    """Programmatischer Zugriff auf Testanalyse"""
    return _analyze_tests_impl(**kwargs)
EOF

echo "Fehlende Testmodule erstellt. Versuche jetzt, den Befehl auszuführen..."
chmod +x bin/cortex-cmd
bin/cortex-cmd --help