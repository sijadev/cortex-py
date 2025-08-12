"""Core analysis utilities for Cortex repository"""

from pathlib import Path
from typing import Dict, List, Any
import json
from datetime import datetime
from ..validators.link_validator import LinkValidator


class CortexAnalyzer:
    """Main analyzer for Cortex repository structure and links"""
    
    def __init__(self, repository_path: Path):
        self.repo_path = Path(repository_path)
        self.link_validator = LinkValidator()
        
    def analyze_links(self) -> Dict[str, Any]:
        """Perform comprehensive link analysis on the repository"""
        
        analysis_start = datetime.now()
        
        # Find all markdown files
        md_files = list(self.repo_path.rglob("*.md"))
        
        # Exclude common non-content directories
        excluded_patterns = ['.git', 'node_modules', '__pycache__', '.pytest_cache']
        md_files = [f for f in md_files if not any(pattern in str(f) for pattern in excluded_patterns)]
        
        broken_links = []
        processed_files = []
        
        for md_file in md_files:
            try:
                file_broken_links = self.link_validator.find_broken_links(md_file, self.repo_path)
                broken_links.extend(file_broken_links)
                processed_files.append({
                    'file': str(md_file.relative_to(self.repo_path)),
                    'size': md_file.stat().st_size,
                    'broken_links_count': len(file_broken_links)
                })
            except Exception as e:
                # Log processing error but continue
                processed_files.append({
                    'file': str(md_file.relative_to(self.repo_path)),
                    'error': str(e)
                })
        
        analysis_end = datetime.now()
        
        return {
            'timestamp': analysis_start.isoformat(),
            'analysis_duration': str(analysis_end - analysis_start),
            'repository_path': str(self.repo_path),
            'summary': {
                'total_files_processed': len(processed_files),
                'total_broken_links': len(broken_links),
                'files_with_issues': len([f for f in processed_files if f.get('broken_links_count', 0) > 0])
            },
            'broken_links': broken_links,
            'processed_files': processed_files,
            'system_info': self._get_system_info()
        }
    
    def analyze_vault_structure(self) -> Dict[str, Any]:
        """Analyze the vault structure and organization"""
        
        structure = {
            'directories': [],
            'special_dirs': {},
            'file_distribution': {}
        }
        
        # Identify special Cortex directories
        special_patterns = {
            'system': '00-System',
            'archive': '99-Archive', 
            'ai_engine': 'AI-Learning-Engine',
            'cross_vault': 'Cross-Vault-Linker',
            'management': 'Management-Service'
        }
        
        for name, pattern in special_patterns.items():
            matches = list(self.repo_path.rglob(pattern))
            if matches:
                structure['special_dirs'][name] = [str(p.relative_to(self.repo_path)) for p in matches]
        
        # Analyze file distribution by type
        file_types = {}
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
        
        structure['file_distribution'] = file_types
        
        return structure
    
    def get_health_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall repository health score"""
        
        summary = analysis_results.get('summary', {})
        total_files = summary.get('total_files_processed', 1)
        broken_links = summary.get('total_broken_links', 0)
        files_with_issues = summary.get('files_with_issues', 0)
        
        # Simple scoring algorithm
        if total_files == 0:
            return 100.0
        
        # Penalize broken links and files with issues
        link_penalty = min(broken_links * 2, 50)  # Max 50 point penalty
        file_penalty = min((files_with_issues / total_files) * 30, 30)  # Max 30 point penalty
        
        score = max(100 - link_penalty - file_penalty, 0)
        return round(score, 2)
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for the analysis report"""
        import platform
        import sys
        
        return {
            'python_version': sys.version,
            'platform': platform.platform(),
            'framework_version': '0.1.0'
        }