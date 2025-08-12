#!/usr/bin/env python3
"""
AI Link Advisor CLI - Main entry point for AI-powered link analysis and suggestions
"""

import click
import json
import sys
from pathlib import Path
from datetime import datetime
from ..validators.link_validator import LinkValidator
from ..reports.health_reporter import HealthReporter
from ..utils.cortex_analyzer import CortexAnalyzer


@click.group()
@click.version_option(version="0.1.0")
def main():
    """AI-powered link analysis and repair suggestions for Cortex"""
    pass


@main.command()
@click.option("--cortex-path", default=".", help="Path to Cortex repository")
@click.option("--output-dir", default="00-System/Test-Tools/test-results", help="Output directory for results")
def analyze(cortex_path, output_dir):
    """Analyze Cortex repository for broken links and patterns"""
    click.echo("🤖 Cortex AI Link Advisor")
    click.echo("=" * 30)
    
    try:
        cortex_path = Path(cortex_path).resolve()
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        click.echo(f"🔍 Analyzing repository at: {cortex_path}")
        
        # Initialize analyzer
        analyzer = CortexAnalyzer(cortex_path)
        
        # Run analysis
        analysis_results = analyzer.analyze_links()
        
        # Generate timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"broken_links_{timestamp}.json"
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        click.echo(f"✅ Analysis complete: {len(analysis_results.get('broken_links', []))} issues found")
        click.echo(f"📄 Results saved to: {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--output", default="ai-suggestions-report.md", help="Output report file")
@click.option("--input-dir", default="00-System/Test-Tools/test-results", help="Directory with analysis results")
def suggest(output, input_dir):
    """Generate AI-powered repair suggestions"""
    click.echo("🤖 Cortex AI Link Advisor")
    click.echo("=" * 30)
    
    try:
        input_dir = Path(input_dir)
        
        # Find latest analysis results
        json_files = list(input_dir.glob("broken_links_*.json"))
        
        if not json_files:
            # Fallback: create basic report without AI analysis
            click.echo("⚠️  No analysis results found, creating basic report")
            fallback_report = _create_fallback_report()
            
            with open(output, 'w') as f:
                f.write(fallback_report)
            
            click.echo(f"📝 Fallback report created: {output}")
            return
        
        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
        
        click.echo(f"📖 Reading analysis from: {latest_file}")
        
        with open(latest_file, 'r') as f:
            analysis_data = json.load(f)
        
        # Generate suggestions
        reporter = HealthReporter()
        suggestions = reporter.generate_suggestions(analysis_data)
        
        with open(output, 'w') as f:
            f.write(suggestions)
        
        click.echo(f"✅ AI suggestions generated: {output}")
        
    except Exception as e:
        click.echo(f"❌ Suggestion generation failed: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--input", required=True, help="Input suggestions file")
@click.option("--output", default="ai-validation-report.md", help="Output validation report")
def validate(input, output):
    """Validate AI suggestions for safety and relevance"""
    click.echo("🔍 Validating AI suggestions...")
    
    try:
        if not Path(input).exists():
            click.echo(f"❌ Input file not found: {input}", err=True)
            sys.exit(1)
        
        # Read suggestions
        with open(input, 'r') as f:
            content = f.read()
        
        # Simple validation (can be enhanced with actual AI validation)
        validator = LinkValidator()
        validation_results = validator.validate_suggestions(content)
        
        with open(output, 'w') as f:
            f.write(validation_results)
        
        click.echo(f"✅ AI suggestion validation completed: {output}")
        
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)


def _create_fallback_report():
    """Create a basic fallback report when analysis data is missing"""
    return """# Cortex Link Health Report (Fallback Mode)

## ⚠️ Fallback Mode Active

The AI Link Advisor is running in fallback mode because analysis data is missing.
This typically happens when the link analysis step fails or produces no results.

## 🔍 Manual Review Required

Please manually check:

1. **Markdown Files**: Review all `.md` files for broken internal links
2. **Cross-References**: Verify links between vault sections
3. **File Existence**: Ensure referenced files exist in the repository

## 📋 Basic Validation Steps

- [ ] Check for broken `[[wikilinks]]`
- [ ] Verify file references in markdown
- [ ] Review cross-vault linking patterns
- [ ] Validate YAML configuration files

## 🛠️ Troubleshooting

To get full AI-powered analysis:
1. Ensure all required dependencies are installed
2. Check that the Cortex repository structure is intact
3. Verify file permissions and access rights

---
*Report generated in fallback mode - consider running full analysis when issues are resolved*
"""


@main.command()
@click.option("--target-dir", default="00-System/Test-Tools/test-results", help="Directory to clean")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def cleanup(target_dir, confirm):
    """Clean up test results directory"""
    target_path = Path(target_dir)
    
    if not target_path.exists():
        click.echo(f"✅ Directory {target_path} doesn't exist, nothing to clean")
        return
    
    files_to_remove = list(target_path.glob("*.json"))
    
    if not files_to_remove:
        click.echo(f"✅ No test result files found in {target_path}")
        return
    
    if not confirm:
        click.echo(f"🗑️  Found {len(files_to_remove)} test result files in {target_path}")
        if not click.confirm("Delete these files?"):
            click.echo("❌ Cleanup cancelled")
            return
    
    for file_path in files_to_remove:
        file_path.unlink()
        click.echo(f"🗑️  Removed {file_path.name}")
    
    click.echo(f"✅ Cleaned up {len(files_to_remove)} files from {target_path}")


if __name__ == "__main__":
    main()