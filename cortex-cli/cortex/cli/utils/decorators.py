"""
Gemeinsame Click-Decorators für Cortex CLI
"""
import click
from functools import wraps

def common_options(func):
    """
    Decorator für häufig verwendete CLI-Optionen
    """
    @click.option('--cortex-path', type=click.Path(), 
                  default='.', help='Pfad zum Cortex-Vault')
    @click.option('--json', 'output_json', is_flag=True, help='Ausgabe als JSON')
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def verbose_option(func):
    """
    Decorator für Verbose-Option
    """
    @click.option('--verbose', '-v', is_flag=True, help='Ausführliche Ausgabe aktivieren')
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def with_error_handling(operation_name):
    """
    Decorator für automatisches Error-Handling
    
    Args:
        operation_name: Name der Operation für Fehlermeldungen
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                from .error_handlers import handle_standard_error
                output_json = kwargs.get('output_json', False)
                verbose = kwargs.get('verbose', False)
                return handle_standard_error(e, operation_name, output_json, verbose)
        return wrapper
    return decorator

def programmatic_result(func):
    """
    Decorator für programmatische API-Unterstützung
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        ctx = None
        # Suche nach ctx in args (Click-Context)
        for arg in args:
            if hasattr(arg, 'obj') and arg.obj is not None:
                ctx = arg
                break
                
        result = func(*args, **kwargs)
        
        # Im programmatischen Modus gibt die Funktion das Ergebnis zurück
        if ctx and ctx.obj and ctx.obj.get('programmatic'):
            return result
            
        return result
    return wrapper
