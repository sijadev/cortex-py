#!/usr/bin/env python3
"""
Health Check CLI - Generate health dashboards and reports for Cortex
"""

import click
import json
from pathlib import Path
from datetime import datetime


@click.command()
@click.option("--output", default="cortex-health.html", help="Output file path")
@click.option("--format", "output_format", default="html", type=click.Choice(['html', 'markdown']), help="Output format")
@click.option("--input-dir", default="test-results", help="Directory with analysis results")
def main(output, output_format, input_dir):
    """Generate health dashboard and reports for Cortex"""
    
    click.echo("📊 Cortex Health Check Generator")
    click.echo("=" * 35)
    
    try:
        input_path = Path(input_dir)
        
        # Find latest analysis results
        json_files = list(input_path.glob("broken_links_*.json"))
        
        if json_files:
            latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
            click.echo(f"📖 Reading data from: {latest_file}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            click.echo("⚠️  No analysis data found, creating basic report")
            data = _create_fallback_data()
        
        # Generate report based on format
        if output_format == 'html':
            content = _generate_html_dashboard(data)
        else:
            content = _generate_markdown_report(data)
        
        # Write output
        with open(output, 'w', encoding='utf-8') as f:
            f.write(content)
        
        click.echo(f"✅ Health {output_format.upper()} generated: {output}")
        
    except Exception as e:
        click.echo(f"❌ Health check generation failed: {e}", err=True)
        return 1
    
    return 0


def _generate_html_dashboard(data: dict) -> str:
    """Generate HTML dashboard"""
    
    summary = data.get('summary', {})
    broken_links = data.get('broken_links', [])
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    # Calculate health score
    total_files = summary.get('total_files_processed', 1)
    total_broken = summary.get('total_broken_links', 0)
    health_score = max(100 - (total_broken * 2), 0)
    
    # Group broken links by type
    wikilinks = len([link for link in broken_links if link.get('type') == 'wikilink'])
    markdown_links = len([link for link in broken_links if link.get('type') == 'markdown'])
    errors = len([link for link in broken_links if link.get('type') == 'error'])
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cortex Health Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 2.5em; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stat-card h3 {{ margin: 0 0 10px 0; color: #333; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .health-score {{ font-size: 3em; font-weight: bold; }}
        .health-good {{ color: #28a745; }}
        .health-warning {{ color: #ffc107; }}
        .health-danger {{ color: #dc3545; }}
        .chart-container {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .timestamp {{ text-align: center; color: #666; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔗 Cortex Health Dashboard</h1>
            <p>Repository link health monitoring and analysis</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Health Score</h3>
                <div class="stat-value health-score {'health-good' if health_score >= 80 else 'health-warning' if health_score >= 60 else 'health-danger'}">{health_score:.1f}%</div>
            </div>
            
            <div class="stat-card">
                <h3>Files Processed</h3>
                <div class="stat-value">{total_files:,}</div>
            </div>
            
            <div class="stat-card">
                <h3>Broken Links</h3>
                <div class="stat-value">{total_broken:,}</div>
            </div>
            
            <div class="stat-card">
                <h3>Files with Issues</h3>
                <div class="stat-value">{summary.get('files_with_issues', 0):,}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>📊 Issue Breakdown</h3>
            <p><strong>WikiLink Issues:</strong> {wikilinks}</p>
            <p><strong>Markdown Link Issues:</strong> {markdown_links}</p>
            <p><strong>Processing Errors:</strong> {errors}</p>
        </div>
        
        <div class="timestamp">
            <p>Generated: {datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S UTC') if 'T' in timestamp else timestamp}</p>
            <p>Powered by Cortex Test Framework v0.1.0</p>
        </div>
    </div>
</body>
</html>"""


def _generate_markdown_report(data: dict) -> str:
    """Generate Markdown report"""
    
    summary = data.get('summary', {})
    broken_links = data.get('broken_links', [])
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    # Calculate health score
    total_files = summary.get('total_files_processed', 1)
    total_broken = summary.get('total_broken_links', 0)
    health_score = max(100 - (total_broken * 2), 0)
    
    # Group broken links by type
    wikilinks = len([link for link in broken_links if link.get('type') == 'wikilink'])
    markdown_links = len([link for link in broken_links if link.get('type') == 'markdown'])
    errors = len([link for link in broken_links if link.get('type') == 'error'])
    
    status_emoji = "✅" if health_score >= 80 else "⚠️" if health_score >= 60 else "❌"
    
    return f"""# {status_emoji} Cortex Health Monitoring Report

Generated: {datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S UTC') if 'T' in timestamp else timestamp}

## 📊 Health Summary

| Metric | Value |
|--------|-------|
| **Health Score** | **{health_score:.1f}%** |
| Files Processed | {total_files:,} |
| Broken Links Found | {total_broken:,} |
| Files with Issues | {summary.get('files_with_issues', 0):,} |

## 🔍 Issue Breakdown

### WikiLink Issues: {wikilinks}
{_format_link_issues([link for link in broken_links if link.get('type') == 'wikilink'])}

### Markdown Link Issues: {markdown_links}  
{_format_link_issues([link for link in broken_links if link.get('type') == 'markdown'])}

### Processing Errors: {errors}
{_format_link_issues([link for link in broken_links if link.get('type') == 'error'])}

## 📈 Health Trend

- **Current Score**: {health_score:.1f}%
- **Status**: {_get_health_status(health_score)}
- **Recommendation**: {_get_health_recommendation(health_score)}

---
*Report generated by Cortex Test Framework v0.1.0*
"""


def _format_link_issues(issues: list) -> str:
    """Format link issues for markdown"""
    if not issues:
        return "✅ No issues found!"
    
    if len(issues) <= 5:
        formatted = []
        for issue in issues:
            file_path = issue.get('file', 'unknown')
            line_num = issue.get('line', '?')
            text = issue.get('text', 'unknown')
            formatted.append(f"- `{file_path}:{line_num}` - {text}")
        return "\n".join(formatted)
    else:
        return f"Found {len(issues)} issues. Check detailed analysis for complete list."


def _get_health_status(score: float) -> str:
    """Get health status description"""
    if score >= 80:
        return "🟢 Excellent - Repository is in great shape"
    elif score >= 60:
        return "🟡 Good - Minor issues need attention"
    else:
        return "🔴 Needs Attention - Multiple issues require fixes"


def _get_health_recommendation(score: float) -> str:
    """Get health recommendations"""
    if score >= 80:
        return "Continue regular maintenance and monitoring"
    elif score >= 60:
        return "Review and fix broken links to improve score"
    else:
        return "Prioritize fixing broken links and validation errors"


def _create_fallback_data() -> dict:
    """Create fallback data when no analysis results available"""
    return {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_files_processed': 0,
            'total_broken_links': 0,
            'files_with_issues': 0
        },
        'broken_links': []
    }


if __name__ == "__main__":
    exit(main())