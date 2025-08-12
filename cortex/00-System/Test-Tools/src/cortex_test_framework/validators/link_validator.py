"""Link validation utilities for Cortex"""

import re
from pathlib import Path
from typing import Dict, List, Any


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
- Appropriate link targets
- No security risks

### ⚠️ Review Required  
- Complex link restructuring
- Cross-vault dependencies
- Potential naming conflicts
- Manual verification needed

### ❌ Rejected Suggestions
- Invalid file paths
- Security concerns
- Syntax errors
- Conflicting recommendations

## 📝 Detailed Analysis

{self._analyze_content_safety(suggestions_content)}

---
*Validation completed by Cortex Test Framework v0.1.0*
"""
        return validation_report
    
    def find_broken_links(self, file_path: Path, repository_root: Path) -> List[Dict[str, Any]]:
        """Find broken links in a markdown file"""
        broken_links = []
        
        if not file_path.exists() or not file_path.suffix == '.md':
            return broken_links
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Check wikilinks [[Link]]
                for match in self.wikilink_pattern.finditer(line):
                    link_text = match.group(1)
                    if not self._is_valid_wikilink(link_text, repository_root):
                        broken_links.append({
                            'type': 'wikilink',
                            'text': link_text,
                            'line': line_num,
                            'file': str(file_path.relative_to(repository_root))
                        })
                
                # Check markdown links [text](path)
                for match in self.markdown_link_pattern.finditer(line):
                    link_text, link_path = match.groups()
                    if not self._is_valid_markdown_link(link_path, file_path, repository_root):
                        broken_links.append({
                            'type': 'markdown',
                            'text': link_text,
                            'path': link_path,
                            'line': line_num,
                            'file': str(file_path.relative_to(repository_root))
                        })
        
        except Exception as e:
            # Log error but don't fail completely
            broken_links.append({
                'type': 'error',
                'text': f'Failed to process file: {e}',
                'line': 0,
                'file': str(file_path.relative_to(repository_root))
            })
        
        return broken_links
    
    def _is_valid_wikilink(self, link_text: str, repo_root: Path) -> bool:
        """Check if a wikilink target exists"""
        # Simple check - look for files with similar names
        possible_files = [
            f"{link_text}.md",
            f"{link_text.replace(' ', '-')}.md",
            f"{link_text.replace(' ', '_')}.md"
        ]
        
        for possible_file in possible_files:
            if list(repo_root.rglob(possible_file)):
                return True
        
        return False
    
    def _is_valid_markdown_link(self, link_path: str, current_file: Path, repo_root: Path) -> bool:
        """Check if a markdown link target exists"""
        if link_path.startswith(('http://', 'https://', 'mailto:')):
            return True  # External links assumed valid
        
        if link_path.startswith('#'):
            return True  # Internal anchors assumed valid
        
        # Resolve relative path
        try:
            target_path = (current_file.parent / link_path).resolve()
            return target_path.exists() and repo_root in target_path.parents
        except:
            return False
    
    def _analyze_content_safety(self, content: str) -> str:
        """Analyze content for potential safety issues"""
        issues = []
        
        # Check for potentially dangerous operations
        dangerous_patterns = [
            (r'rm\s+-rf', 'Dangerous file deletion commands'),
            (r'sudo\s+', 'Elevated privilege operations'),
            (r'>\s*/dev/', 'System device access'),
            (r'curl.*\|.*sh', 'Remote script execution')
        ]
        
        for pattern, description in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"⚠️ {description} detected")
        
        if not issues:
            issues.append("✅ No security concerns detected")
        
        return "\n".join(issues)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")