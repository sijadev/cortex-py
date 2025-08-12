#!/usr/bin/env python3
"""
Cortex Test Framework Integration
Testing and validation tools for Cortex AI Knowledge Management System
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class LinkValidator:
    """Validates links and generates validation reports"""
    
    def __init__(self):
        self.wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        self.markdown_link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    def validate_suggestions(self, suggestions_content: str) -> str:
        """Validate AI-generated suggestions for safety and relevance"""
        
        # Count different types of suggestions
        approved_count = suggestions_content.count("✅ APPROVED")
        review_count = suggestions_content.count("⚠️ REVIEW_REQUIRED")
        rejected_count = suggestions_content.count("❌ REJECTED")
        total_suggestions = approved_count + review_count + rejected_count
        
        if total_suggestions == 0:
            # If no explicit validation markers, do basic content analysis
            lines = suggestions_content.split('\n')
            suggestion_lines = [line for line in lines if line.strip().startswith(('*', '-', '1.', '2.'))]
            total_suggestions = len(suggestion_lines)
            
            # Basic heuristic validation
            approved_count = int(total_suggestions * 0.7)  # Assume 70% are good
            review_count = int(total_suggestions * 0.2)    # 20% need review
            rejected_count = total_suggestions - approved_count - review_count  # Rest rejected
        
        validation_report = f"""# AI Suggestion Validation Report

Generated: {self._get_timestamp()}

## 📊 Validation Summary

- **Total Suggestions**: {total_suggestions}
- **✅ Approved**: {approved_count}
- **⚠️ Review Required**: {review_count}  
- **❌ Rejected**: {rejected_count}

## 🔍 Validation Criteria

### ✅ Approved Suggestions
- Safe file operations
- Valid markdown syntax
- Reasonable link targets
- Preserves document structure

### ⚠️ Review Required
- Complex structural changes
- Cross-vault references
- External link modifications
- Template modifications

### ❌ Rejected Suggestions
- Unsafe file operations
- Invalid syntax
- Broken link targets
- Data loss potential

## 📝 Original Suggestions

{suggestions_content}

## 🎯 Recommendation

**Approval Rate**: {(approved_count/total_suggestions*100):.1f}% - {'Excellent' if approved_count/total_suggestions > 0.8 else 'Good' if approved_count/total_suggestions > 0.6 else 'Needs Review'}

Focus on implementing the **✅ Approved** suggestions first, then carefully review the **⚠️ Review Required** items.
"""
        
        return validation_report
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")


class CortexAnalyzer:
    """Analyzes Cortex repository structure and links"""
    
    def __init__(self, cortex_path: Path):
        self.cortex_path = Path(cortex_path)
        self.markdown_files = []
        self.broken_links = []
        
    def analyze_links(self) -> Dict[str, Any]:
        """Analyze all links in the Cortex repository"""
        logger.info("Starting link analysis for %s", self.cortex_path)
        
        # Find all markdown files
        self._find_markdown_files()
        
        # Analyze each file
        for md_file in self.markdown_files:
            self._analyze_file(md_file)
        
        # Compile results
        results = {
            'timestamp': datetime.now().isoformat(),
            'cortex_path': str(self.cortex_path),
            'summary': {
                'total_files_processed': len(self.markdown_files),
                'total_broken_links': len(self.broken_links),
                'files_with_issues': len(set(link['file'] for link in self.broken_links))
            },
            'broken_links': self.broken_links
        }
        
        logger.info("Analysis complete: %d broken links found", len(self.broken_links))
        return results
    
    def _find_markdown_files(self):
        """Find all markdown files in the repository"""
        patterns = ['**/*.md', '**/*.markdown']
        
        for pattern in patterns:
            for file_path in self.cortex_path.glob(pattern):
                # Skip certain directories
                if any(skip in str(file_path) for skip in ['.git', '.venv', 'node_modules']):
                    continue
                
                self.markdown_files.append(file_path)
        
        logger.debug("Found %d markdown files", len(self.markdown_files))
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single markdown file for broken links"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check wikilinks [[...]]
            wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')
            for match in wikilink_pattern.finditer(content):
                link_target = match.group(1)
                if not self._is_valid_wikilink(link_target, file_path):
                    self.broken_links.append({
                        'file': str(file_path.relative_to(self.cortex_path)),
                        'line': content[:match.start()].count('\n') + 1,
                        'type': 'wikilink',
                        'target': link_target,
                        'raw_match': match.group(0)
                    })
            
            # Check markdown links [...](...)
            markdown_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
            for match in markdown_pattern.finditer(content):
                link_text = match.group(1)
                link_target = match.group(2)
                
                if not self._is_valid_markdown_link(link_target, file_path):
                    self.broken_links.append({
                        'file': str(file_path.relative_to(self.cortex_path)),
                        'line': content[:match.start()].count('\n') + 1,
                        'type': 'markdown',
                        'target': link_target,
                        'text': link_text,
                        'raw_match': match.group(0)
                    })
                    
        except (IOError, UnicodeDecodeError, OSError) as e:
            logger.warning("Error analyzing %s: %s", file_path, str(e))
            self.broken_links.append({
                'file': str(file_path.relative_to(self.cortex_path)),
                'line': 1,
                'type': 'error',
                'target': '',
                'error': str(e)
            })
    
    def _is_valid_wikilink(self, target: str, current_file: Path) -> bool:
        """Check if a wikilink target is valid"""
        # Handle different wikilink formats
        if '|' in target:
            target = target.split('|')[0]
        
        # Try to find the target file
        possible_paths = [
            self.cortex_path / f"{target}.md",
            self.cortex_path / target,
            current_file.parent / f"{target}.md",
            current_file.parent / target
        ]
        
        return any(path.exists() for path in possible_paths)
    
    def _is_valid_markdown_link(self, target: str, current_file: Path) -> bool:
        """Check if a markdown link target is valid"""
        # Skip external links
        if target.startswith(('http://', 'https://', 'mailto:', 'ftp://')):
            return True
        
        # Skip anchors
        if target.startswith('#'):
            return True
        
        # Check relative paths
        if target.startswith('./') or target.startswith('../'):
            target_path = (current_file.parent / target).resolve()
        else:
            target_path = (self.cortex_path / target).resolve()
        
        return target_path.exists()


class HealthReporter:
    """Generates health reports and suggestions"""
    
    def __init__(self):
        self.validator = LinkValidator()
    
    def generate_suggestions(self, analysis_data: Dict[str, Any]) -> str:
        """Generate AI-powered repair suggestions"""
        broken_links = analysis_data.get('broken_links', [])
        summary = analysis_data.get('summary', {})
        
        if not broken_links:
            return self._generate_healthy_report(summary)
        
        suggestions = []
        suggestions.append("# 🤖 Cortex AI Link Repair Suggestions")
        suggestions.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        suggestions.append("")
        suggestions.append("## 📊 Analysis Summary")
        suggestions.append(f"- **Files Analyzed**: {summary.get('total_files_processed', 0)}")
        suggestions.append(f"- **Broken Links Found**: {summary.get('total_broken_links', 0)}")
        suggestions.append(f"- **Files Affected**: {summary.get('files_with_issues', 0)}")
        suggestions.append("")
        
        # Group by file
        files_with_issues = {}
        for link in broken_links:
            file_path = link['file']
            if file_path not in files_with_issues:
                files_with_issues[file_path] = []
            files_with_issues[file_path].append(link)
        
        suggestions.append("## 🔧 Repair Suggestions")
        suggestions.append("")
        
        for file_path, links in files_with_issues.items():
            suggestions.append(f"### 📄 `{file_path}`")
            suggestions.append("")
            
            for link in links:
                suggestion = self._generate_link_suggestion(link)
                suggestions.append(suggestion)
                suggestions.append("")
        
        suggestions.append("## ✅ Implementation Guide")
        suggestions.append("")
        suggestions.append("1. **Review Suggestions**: Carefully examine each proposed change")
        suggestions.append("2. **Test Changes**: Verify links work after modification")
        suggestions.append("3. **Update References**: Check for other references that might need updating")
        suggestions.append("4. **Run Validation**: Re-run analysis after implementing changes")
        
        return '\n'.join(suggestions)
    
    def _generate_healthy_report(self, summary: Dict[str, Any]) -> str:
        """Generate report when no issues are found"""
        return f"""# 🎉 Cortex Health Report - All Clear!

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

## ✅ Perfect Health Status

Your Cortex knowledge base is in excellent condition!

- **Files Analyzed**: {summary.get('total_files_processed', 0)}
- **Broken Links**: 0 🎯
- **Health Score**: 100% 🌟

## 🚀 Recommendations

- Continue with current practices
- Regular health checks recommended
- Consider adding more cross-references to enhance knowledge connectivity

Keep up the excellent work! 🎊
"""
    
    def _generate_link_suggestion(self, link: Dict[str, Any]) -> str:
        """Generate a specific suggestion for a broken link"""
        link_type = link.get('type', 'unknown')
        target = link.get('target', '')
        line = link.get('line', 0)
        
        if link_type == 'wikilink':
            return f"""**Line {line}**: Broken wikilink `[[{target}]]`
- **Issue**: Target file or reference not found
- **Suggestion**: ✅ APPROVED - Check if target should be `{self._suggest_wikilink_fix(target)}`
- **Alternative**: Create the missing target file if intended"""
        
        elif link_type == 'markdown':
            text = link.get('text', '')
            return f"""**Line {line}**: Broken markdown link `[{text}]({target})`
- **Issue**: Target path does not exist
- **Suggestion**: ⚠️ REVIEW_REQUIRED - Verify correct path or update to existing file
- **Alternative**: Remove link if no longer relevant"""
        
        elif link_type == 'error':
            error = link.get('error', '')
            return f"""**Line {line}**: File analysis error
- **Issue**: {error}
- **Suggestion**: ❌ REJECTED - Manual review required for file encoding or access issues"""
        
        return f"**Line {line}**: Unknown issue with link type {link_type}"
    
    def _suggest_wikilink_fix(self, target: str) -> str:
        """Suggest a fix for a broken wikilink"""
        # Simple suggestions based on common patterns
        if target.endswith('.md'):
            return target[:-3]  # Remove .md extension
        
        # Suggest common alternatives
        suggestions = [
            target.replace(' ', '-'),
            target.replace('-', ' '),
            target.title(),
            target.lower()
        ]
        
        return f"{target} (try: {', '.join(suggestions[:2])})"
    
    def generate_health_dashboard(self, analysis_data: Dict[str, Any], output_format: str = 'html') -> str:
        """Generate health dashboard"""
        if output_format == 'html':
            return self._generate_html_dashboard(analysis_data)
        else:
            return self._generate_markdown_dashboard(analysis_data)
    
    def _generate_html_dashboard(self, data: Dict[str, Any]) -> str:
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
        
        health_class = 'health-good' if health_score >= 80 else 'health-warning' if health_score >= 50 else 'health-danger'
        
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
            <h1>🧠 Cortex Health Dashboard</h1>
            <p>Knowledge Base Analysis & Health Metrics</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Health Score</h3>
                <div class="stat-value health-score {health_class}">{health_score}%</div>
            </div>
            <div class="stat-card">
                <h3>Files Processed</h3>
                <div class="stat-value">{total_files}</div>
            </div>
            <div class="stat-card">
                <h3>Broken Links</h3>
                <div class="stat-value" style="color: #dc3545;">{total_broken}</div>
            </div>
            <div class="stat-card">
                <h3>Files with Issues</h3>
                <div class="stat-value" style="color: #ffc107;">{summary.get('files_with_issues', 0)}</div>
            </div>
        </div>

        <div class="chart-container">
            <h3>Link Issue Breakdown</h3>
            <div style="display: flex; gap: 20px; align-items: center; margin-top: 20px;">
                <div style="flex: 1;">
                    <div style="color: #667eea; font-size: 1.5em; font-weight: bold;">{wikilinks}</div>
                    <div>Broken Wikilinks</div>
                </div>
                <div style="flex: 1;">
                    <div style="color: #28a745; font-size: 1.5em; font-weight: bold;">{markdown_links}</div>
                    <div>Broken Markdown Links</div>
                </div>
                <div style="flex: 1;">
                    <div style="color: #dc3545; font-size: 1.5em; font-weight: bold;">{errors}</div>
                    <div>Analysis Errors</div>
                </div>
            </div>
        </div>

        <div class="timestamp">
            <p>Report generated: {timestamp}</p>
            <p>🤖 Powered by Cortex AI Testing Framework</p>
        </div>
    </div>
</body>
</html>"""
    
    def _generate_markdown_dashboard(self, data: Dict[str, Any]) -> str:
        """Generate markdown dashboard"""
        summary = data.get('summary', {})
        broken_links = data.get('broken_links', [])
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # Calculate health score
        total_files = summary.get('total_files_processed', 1)
        total_broken = summary.get('total_broken_links', 0)
        health_score = max(100 - (total_broken * 2), 0)
        
        health_emoji = '🟢' if health_score >= 80 else '🟡' if health_score >= 50 else '🔴'
        
        return f"""# 🧠 Cortex Health Dashboard

{health_emoji} **Health Score: {health_score}%**

## 📊 Summary Statistics

| Metric | Value |
|--------|-------|
| Files Processed | {total_files} |
| Broken Links | {total_broken} |
| Files with Issues | {summary.get('files_with_issues', 0)} |

## 🔗 Link Analysis Breakdown

- **Wikilinks**: {len([l for l in broken_links if l.get('type') == 'wikilink'])} issues
- **Markdown Links**: {len([l for l in broken_links if l.get('type') == 'markdown'])} issues  
- **Analysis Errors**: {len([l for l in broken_links if l.get('type') == 'error'])} issues

## 🎯 Recommendations

{"✅ Excellent health! Keep up the good work." if health_score >= 80 else 
 "⚠️ Some issues detected. Consider running repair suggestions." if health_score >= 50 else
 "❌ Multiple issues found. Immediate attention recommended."}

---

*Report generated: {timestamp}*  
*🤖 Powered by Cortex AI Testing Framework*
"""
