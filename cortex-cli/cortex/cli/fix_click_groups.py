"""
Click Group Name Fix
Behebt Click Group .name Attribut Probleme
"""
import click

class NamedGroup(click.Group):
    """Click Group mit explizit gesetztem name Attribut"""
    
    def __init__(self, name=None, commands=None, **attrs):
        super().__init__(commands=commands, **attrs)
        if name:
            self.name = name

def create_named_group(name, **kwargs):
    """Erstelle eine Click Group mit garantiertem name Attribut"""
    group = NamedGroup(name=name, **kwargs)
    return group
