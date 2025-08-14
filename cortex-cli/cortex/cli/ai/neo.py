import click
from ...core.ai_engine import CortexAIEngine

@click.command(name="suggest-links")
@click.argument('node_name')
@click.pass_context
def suggest_links(ctx, node_name):
    """Schlägt neue Links für einen bestimmten Knoten vor, basierend auf der Graphenstruktur."""
    engine = CortexAIEngine(workspace_path=str(ctx.obj.get('cortex_path', '.')))
    suggestions = engine.suggest_links(node_name=node_name)
    click.echo(suggestions)

# Die Gruppe 'neo' wird beibehalten, um eine konsistente Befehlsstruktur zu gewährleisten,
# auch wenn sie derzeit nur einen Befehl enthält.
@click.group()
def neo():
    """Befehle zur Interaktion mit dem Neo4j-Graphen mittels interner AI."""
    pass

neo.add_command(suggest_links)
