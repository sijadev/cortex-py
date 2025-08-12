"""
Cortex AI Integration Module
"""
import click
from .chat import chat_command
from .analyze import analyze_command  
from .validate import validate_command

@click.group(name="ai")
def ai():
    """Cortex-AI Befehle für Chat und Analyse"""
    pass

# Commands zum ai-Group hinzufügen
ai.add_command(chat_command, name='chat')
ai.add_command(analyze_command, name='analyze')
ai.add_command(validate_command, name='validate')

# Programmatische API exportieren
from .chat import chat
from .analyze import analyze
from .validate import validate

__all__ = ['ai', 'chat', 'analyze', 'validate']
