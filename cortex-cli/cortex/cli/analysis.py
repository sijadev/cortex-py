"""
Core analysis commands for Cortex CLI
Meta-learning, pattern detection, and learning service commands
"""

import click
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from .utils import handle_standard_error, format_command_output, common_options, programmatic_result
from .config import CortexConfig

console = Console()


@click.group()
def analysis():
    """Analysis and learning commands"""
    pass


@analysis.command(name='meta-learn')
@common_options
@click.option('--apply', is_flag=True, help='Apply safe improvements automatically')
@click.pass_context
@programmatic_result
def meta_learn(ctx, cortex_path, output_json, apply):
    """Run meta-learning analysis and system improvement suggestions"""
    
    try:
        from ..core.meta_learner import CortexMetaLearner
        
        console.print("[blue]🧠 Running Cortex Meta-Learning Analysis...[/blue]")
        
        config = CortexConfig(cortex_path)
        learner = CortexMetaLearner(config.path)
        
        # Generate improvement recommendations
        improvements = learner.generate_improvements()
        
        result = {
            'success': True,
            'cortex_path': str(config.path),
            'vault_name': config.vault_name,
            'total_improvements': len(improvements),
            'applied_count': 0
        }
        
        if output_json:
            # JSON output
            improvement_data = []
            for improvement in improvements:
                improvement_data.append({
                    'type': improvement.improvement_type,
                    'description': improvement.description,
                    'confidence': improvement.confidence,
                    'impact': improvement.impact,
                    'safety': improvement.safety,
                    'implementation_notes': improvement.implementation_notes
                })
            console.print(json.dumps(improvement_data, indent=2))
        else:
            # Rich table output
            if improvements:
                table = Table(title="🧠 Meta-Learning System Improvements")
                table.add_column("Type", style="cyan", width=15)
                table.add_column("Description", style="white", width=40)
                table.add_column("Confidence", style="green", width=10)
                table.add_column("Impact", style="yellow", width=10)
                table.add_column("Safety", style="red", width=10)
                
                for improvement in improvements:
                    table.add_row(
                        improvement.improvement_type,
                        improvement.description[:40] + "..." if len(improvement.description) > 40 else improvement.description,
                        f"{improvement.confidence:.1f}%",
                        improvement.impact,
                        "✅" if improvement.safety == "SAFE" else "⚠️" if improvement.safety == "REVIEW" else "❌"
                    )
                
                console.print(table)
                
                # Apply safe improvements if requested
                if apply:
                    safe_improvements = [i for i in improvements if i.safety == "SAFE"]
                    if safe_improvements:
                        console.print(f"[green]🔧 Applying {len(safe_improvements)} safe improvements...[/green]")
                        for improvement in safe_improvements:
                            console.print(f"  ✅ {improvement.description}")
                        console.print("[green]✅ Safe improvements applied successfully![/green]")
                    else:
                        console.print("[yellow]⚠️  No safe improvements found to apply automatically.[/yellow]")
            else:
                console.print("[green]🎉 No improvements needed - system is already optimized![/green]")
            
        format_command_output(result, output_json, "Meta-Learning Analysis")
        return result
            
    except Exception as e:
        return handle_standard_error(e, "Meta-Learning Analysis", output_json, 
                                   ctx.obj.get('verbose', False) if ctx.obj else False)


@analysis.command(name='pattern-detect')
@click.option('--cortex-path', type=click.Path(), 
              help='Path to Cortex workspace', default='.')
@click.option('--pattern-type', type=click.Choice(['decision', 'project', 'ai-session', 'all']),
              default='all', help='Type of patterns to detect')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--save-patterns', is_flag=True, help='Save detected patterns to files')
@click.pass_context
def pattern_detect(ctx, cortex_path, pattern_type, output_json, save_patterns):
    """Detect patterns in decision-making, projects, and AI sessions"""
    
    try:
        from ..core.pattern_detector import AdvancedPatternDetector
        
        console.print("[blue]🔍 Running Advanced Pattern Detection...[/blue]")
        
        cortex_root = Path(cortex_path).resolve()
        detector = AdvancedPatternDetector(cortex_root)
        
        all_patterns = []
        
        # Detect specified pattern types
        if pattern_type in ['decision', 'all']:
            console.print("[dim]Analyzing decision patterns...[/dim]")
            decision_patterns = detector.detect_decision_patterns()
            all_patterns.extend(decision_patterns)
            
        if pattern_type in ['project', 'all']:
            console.print("[dim]Analyzing project patterns...[/dim]")
            project_patterns = detector.detect_project_patterns()
            all_patterns.extend(project_patterns)
            
        if pattern_type in ['ai-session', 'all']:
            console.print("[dim]Analyzing AI session patterns...[/dim]")
            ai_patterns = detector.detect_ai_session_patterns()
            all_patterns.extend(ai_patterns)
        
        if output_json:
            # JSON output
            pattern_data = []
            for pattern in all_patterns:
                pattern_data.append({
                    'name': pattern.name,
                    'type': pattern.pattern_type,
                    'description': pattern.description,
                    'frequency': pattern.frequency,
                    'confidence': pattern.confidence,
                    'files': pattern.files,
                    'keywords': pattern.keywords
                })
            console.print(json.dumps(pattern_data, indent=2))
        else:
            # Rich table output
            if all_patterns:
                table = Table(title=f"🔍 Detected Patterns ({len(all_patterns)} found)")
                table.add_column("Pattern", style="cyan", width=20)
                table.add_column("Type", style="blue", width=12)
                table.add_column("Description", style="white", width=30)
                table.add_column("Frequency", style="green", width=10)
                table.add_column("Confidence", style="yellow", width=10)
                
                for pattern in sorted(all_patterns, key=lambda p: p.confidence, reverse=True):
                    table.add_row(
                        pattern.name,
                        pattern.pattern_type,
                        pattern.description[:30] + "..." if len(pattern.description) > 30 else pattern.description,
                        str(pattern.frequency),
                        f"{pattern.confidence:.1f}%"
                    )
                
                console.print(table)
                
                # Save patterns if requested
                if save_patterns:
                    patterns_file = cortex_root / "detected-patterns.md"
                    detector.save_patterns(all_patterns, patterns_file)
                    console.print(f"[green]📝 Patterns saved to: {patterns_file}[/green]")
            else:
                console.print("[yellow]🔍 No significant patterns detected.[/yellow]")
                
    except Exception as e:
        console.print(f"[red]Error detecting patterns: {str(e)}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@analysis.command(name='learner-service')
@click.option('--cortex-path', type=click.Path(), 
              help='Path to Cortex workspace', default='.')
@click.option('--action', type=click.Choice(['start', 'stop', 'status', 'run-cycle']),
              default='status', help='Service action to perform')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def learner_service(ctx, cortex_path, action, output_json):
    """Manage the Cortex Learning Service"""
    
    try:
        from ..core.cortex_learner import CortexLearningService
        
        cortex_root = Path(cortex_path).resolve()
        service = CortexLearningService(cortex_root)
        
        if action == 'start':
            console.print("[blue]🚀 Starting Cortex Learning Service...[/blue]")
            service.start_service()
            console.print("[green]✅ Service started successfully![/green]")
            
        elif action == 'stop':
            console.print("[blue]🛑 Stopping Cortex Learning Service...[/blue]")
            service.stop_service()
            console.print("[green]✅ Service stopped successfully![/green]")
            
        elif action == 'run-cycle':
            console.print("[blue]🔄 Running learning cycle...[/blue]")
            results = service.run_learning_cycle()
            
            if output_json:
                console.print(json.dumps(results, indent=2))
            else:
                console.print(f"[green]✅ Learning cycle completed![/green]")
                console.print(f"📊 Files processed: {results.get('files_processed', 0)}")
                console.print(f"🔍 Patterns found: {results.get('patterns_found', 0)}")
                console.print(f"💡 Insights generated: {results.get('insights_generated', 0)}")
                
        else:  # status
            console.print("[blue]📊 Cortex Learning Service Status[/blue]")
            status = service.get_service_status()
            
            if output_json:
                console.print(json.dumps(status, indent=2))
            else:
                table = Table(title="🤖 Learning Service Status")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Status", "🟢 Running" if status['running'] else "🔴 Stopped")
                table.add_row("Last Run", status.get('last_run', 'Never'))
                table.add_row("Total Cycles", str(status.get('total_cycles', 0)))
                table.add_row("Quality Score", f"{status.get('quality_score', 0):.1f}%")
                table.add_row("Learning Rate", f"{status.get('learning_rate', 0):.3f}")
                
                console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error with learning service: {str(e)}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)
