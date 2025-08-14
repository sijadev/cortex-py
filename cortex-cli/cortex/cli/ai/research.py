"""
CLI-Befehl zum Recherchieren von Wissenslücken mit der AIEngine.
"""
import click
import asyncio
from cortex.core.ai_engine import CortexAIEngine

@click.command(name="research")
@click.argument('gap_id')
@click.pass_context
def research_command(ctx, gap_id: str):
    """
    Führt eine KI-gestützte Recherche für eine bestimmte Wissenslücke durch.
    """
    workspace_path = ctx.obj.get('cortex_path', '.')
    engine = CortexAIEngine(workspace_path=str(workspace_path))

    click.echo(f"Starte Recherche für Wissenslücke: {gap_id}...")

    # Führe die asynchrone research_gap Methode aus
    gap_result = asyncio.run(engine.research_gap(gap_id))

    if gap_result:
        click.secho(f"Recherche für '{gap_result.title}' erfolgreich abgeschlossen.", fg='green')

        # Ergebnisse anzeigen
        research_results = engine.research_results.get(gap_id)
        if research_results:
            click.echo("\n--- Recherche-Ergebnisse ---")
            for i, result in enumerate(research_results):
                click.secho(f"\nErgebnis {i+1}: {result.title}", fg='cyan')
                click.echo(f"Quelle: {result.source_url}")
                click.echo(f"Anfrage: {result.query}")
                click.echo("\nInhalt:")
                click.echo(result.content)
            click.echo("\n--------------------------")
        else:
            click.secho("Keine spezifischen Ergebnisse gefunden, aber die Recherche wurde durchgeführt.", fg='yellow')
    else:
        click.secho(f"Recherche für Wissenslücke {gap_id} fehlgeschlagen oder Lücke nicht gefunden.", fg='red')

