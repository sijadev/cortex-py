#!/usr/bin/env python3
"""
Cortex AI Engine - Extracted from gap_detection_engine.py
Professional knowledge gap detection for CLI package
"""

import os
import json
import yaml
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, Counter
import re
import hashlib
import asyncio
import aiohttp

@dataclass
class KnowledgeGap:
    """Represents a detected knowledge gap"""
    gap_id: str
    gap_type: str  # 'missing_benchmarks', 'incomplete_research', 'outdated_data', 'missing_examples'
    title: str
    description: str
    context: str  # Where the gap was found
    priority: str  # 'critical', 'high', 'medium', 'low'
    confidence: float  # How confident we are this is actually a gap
    research_queries: List[str]  # Specific queries to fill this gap
    detected_date: str
    last_research_attempt: Optional[str] = None
    filled_date: Optional[str] = None
    filled_by: Optional[str] = None  # 'web_research', 'manual', 'ai_generation'
    
@dataclass
class ResearchResult:
    """Result from web research"""
    query: str
    source_url: str
    title: str
    content: str
    relevance_score: float
    authority_score: float
    currency_score: float
    extracted_data: Dict[str, Any]
    timestamp: str

@dataclass
class GapFillStrategy:
    """Strategy for filling a specific type of gap"""
    gap_type: str
    priority_weight: float
    research_methods: List[str]  # 'web_search', 'academic_papers', 'documentation', 'examples'
    query_templates: List[str]
    quality_thresholds: Dict[str, float]
    max_results_per_query: int

class CortexAIEngine:
    """Main engine for detecting and filling knowledge gaps - CLI version"""
    
    def __init__(self, workspace_path: str = None):
        if workspace_path:
            self.workspace_path = Path(workspace_path)
        else:
            self.workspace_path = Path.cwd()
        
        self.gap_data_path = self.workspace_path / ".cortex" / "data" / "knowledge_gaps"
        self.research_cache_path = self.workspace_path / ".cortex" / "cache" / "web_research"
        
        # Ensure directories exist
        for path in [self.gap_data_path, self.research_cache_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration and strategies
        self.config = self.load_config()
        self.gap_strategies = self.load_gap_strategies()
        
        # Initialize data stores
        self.detected_gaps: List[KnowledgeGap] = []
        self.research_results: Dict[str, List[ResearchResult]] = {}
        
        # Load existing data
        self.load_existing_gaps()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.workspace_path / ".cortex" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "ai_engine.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """Load AI engine configuration"""
        config_file = self.workspace_path / ".cortex" / "ai_config.yaml"
        
        default_config = {
            "analysis_patterns": {
                "missing_benchmarks": {
                    "keywords": ["performance", "benchmark", "comparison", "metrics"],
                    "indicators": ["no data", "missing metrics", "unclear performance"]
                },
                "incomplete_research": {
                    "keywords": ["research needed", "investigate", "explore", "analyze"],
                    "indicators": ["TODO", "FIXME", "research required"]
                },
                "outdated_data": {
                    "keywords": ["outdated", "old", "deprecated", "legacy"],
                    "indicators": ["2020", "2021", "old version"]
                }
            },
            "research_settings": {
                "max_queries_per_gap": 3,
                "max_results_per_query": 5,
                "cache_duration_hours": 24,
                "quality_threshold": 0.7
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    # Merge with defaults
                    default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Could not load config file: {e}")
        
        return default_config
    
    def load_gap_strategies(self) -> List[GapFillStrategy]:
        """Load gap fill strategies"""
        return [
            GapFillStrategy(
                gap_type="missing_benchmarks",
                priority_weight=0.9,
                research_methods=["web_search", "documentation"],
                query_templates=[
                    "{context} performance benchmarks",
                    "{context} performance comparison",
                    "{context} benchmark results"
                ],
                quality_thresholds={"relevance": 0.8, "authority": 0.7},
                max_results_per_query=5
            ),
            GapFillStrategy(
                gap_type="incomplete_research",
                priority_weight=0.8,
                research_methods=["web_search", "academic_papers"],
                query_templates=[
                    "{context} research study",
                    "{context} analysis",
                    "{context} findings"
                ],
                quality_thresholds={"relevance": 0.7, "authority": 0.8},
                max_results_per_query=3
            )
        ]
    
    def load_existing_gaps(self):
        """Load previously detected gaps"""
        gaps_file = self.gap_data_path / "detected_gaps.json"
        if gaps_file.exists():
            try:
                with open(gaps_file, 'r', encoding='utf-8') as f:
                    gaps_data = json.load(f)
                    self.detected_gaps = [
                        KnowledgeGap(**gap) for gap in gaps_data
                    ]
                self.logger.info(f"Loaded {len(self.detected_gaps)} existing gaps")
            except Exception as e:
                self.logger.warning(f"Could not load existing gaps: {e}")
    
    def analyze_workspace(self) -> List[KnowledgeGap]:
        """Main analysis method - detects knowledge gaps in workspace"""
        self.logger.info("Starting workspace knowledge gap analysis")
        
        # Analyze different types of files
        new_gaps = []
        
        # Analyze markdown files
        md_gaps = self.analyze_markdown_files()
        new_gaps.extend(md_gaps)
        
        # Analyze code files
        code_gaps = self.analyze_code_files()
        new_gaps.extend(code_gaps)
        
        # Analyze documentation
        doc_gaps = self.analyze_documentation()
        new_gaps.extend(doc_gaps)
        
        # Update detected gaps
        self.detected_gaps.extend(new_gaps)
        
        # Save results
        self.save_detected_gaps()
        
        self.logger.info(f"Analysis complete. Found {len(new_gaps)} new gaps")
        return new_gaps
    
    def analyze_markdown_files(self) -> List[KnowledgeGap]:
        """Analyze markdown files for knowledge gaps"""
        gaps = []
        
        for md_file in self.workspace_path.rglob("*.md"):
            if ".cortex" in str(md_file):
                continue  # Skip our own files
                
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for TODO, FIXME, research needed, etc.
                gap_patterns = [
                    (r'TODO.*research', 'incomplete_research'),
                    (r'FIXME.*performance', 'missing_benchmarks'),
                    (r'need.*benchmark', 'missing_benchmarks'),
                    (r'missing.*data', 'incomplete_research')
                ]
                
                for pattern, gap_type in gap_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        gap = self.create_gap_from_match(
                            md_file, match, gap_type, content
                        )
                        gaps.append(gap)
                        
            except Exception as e:
                self.logger.warning(f"Error analyzing {md_file}: {e}")
        
        return gaps
    
    def analyze_code_files(self) -> List[KnowledgeGap]:
        """Analyze code files for knowledge gaps"""
        gaps = []
        
        code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c']
        
        for ext in code_extensions:
            for code_file in self.workspace_path.rglob(f"*{ext}"):
                if ".cortex" in str(code_file) or ".venv" in str(code_file):
                    continue
                    
                try:
                    with open(code_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for performance TODOs, missing error handling, etc.
                    gap_patterns = [
                        (r'# TODO.*performance', 'missing_benchmarks'),
                        (r'// TODO.*optimize', 'missing_benchmarks'),
                        (r'raise NotImplementedError', 'incomplete_research')
                    ]
                    
                    for pattern, gap_type in gap_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            gap = self.create_gap_from_match(
                                code_file, match, gap_type, content
                            )
                            gaps.append(gap)
                            
                except Exception as e:
                    self.logger.warning(f"Error analyzing {code_file}: {e}")
        
        return gaps
    
    def analyze_documentation(self) -> List[KnowledgeGap]:
        """Analyze documentation for knowledge gaps"""
        gaps = []
        
        # Look for documentation directories
        doc_dirs = ["docs", "documentation", "wiki"]
        
        for doc_dir in doc_dirs:
            doc_path = self.workspace_path / doc_dir
            if doc_path.exists():
                for doc_file in doc_path.rglob("*.md"):
                    try:
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Look for empty sections, placeholders
                        if "TBD" in content or "To be determined" in content:
                            gap = self.create_documentation_gap(doc_file, content)
                            gaps.append(gap)
                            
                    except Exception as e:
                        self.logger.warning(f"Error analyzing {doc_file}: {e}")
        
        return gaps
    
    def create_gap_from_match(self, file_path: Path, match, gap_type: str, content: str) -> KnowledgeGap:
        """Create a KnowledgeGap from a regex match"""
        context_start = max(0, match.start() - 100)
        context_end = min(len(content), match.end() + 100)
        context = content[context_start:context_end]
        
        gap_id = hashlib.md5(f"{file_path}{match.start()}{gap_type}".encode()).hexdigest()[:8]
        
        return KnowledgeGap(
            gap_id=gap_id,
            gap_type=gap_type,
            title=f"{gap_type.replace('_', ' ').title()} in {file_path.name}",
            description=match.group(0),
            context=context,
            priority=self.calculate_priority(gap_type, context),
            confidence=0.8,  # Default confidence
            research_queries=self.generate_research_queries(gap_type, context),
            detected_date=datetime.now().isoformat()
        )
    
    def create_documentation_gap(self, file_path: Path, content: str) -> KnowledgeGap:
        """Create a gap for documentation issues"""
        gap_id = hashlib.md5(f"{file_path}documentation".encode()).hexdigest()[:8]
        
        return KnowledgeGap(
            gap_id=gap_id,
            gap_type="incomplete_research",
            title=f"Incomplete documentation in {file_path.name}",
            description="Documentation contains placeholders or incomplete sections",
            context=content[:200],
            priority="medium",
            confidence=0.9,
            research_queries=[f"how to document {file_path.stem}"],
            detected_date=datetime.now().isoformat()
        )
    
    def calculate_priority(self, gap_type: str, context: str) -> str:
        """Calculate priority based on gap type and context"""
        priority_keywords = {
            "critical": ["critical", "urgent", "important", "must"],
            "high": ["should", "need", "required"],
            "low": ["nice", "optional", "maybe"]
        }
        
        context_lower = context.lower()
        for priority, keywords in priority_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                return priority
        
        return "medium"  # Default
    
    def generate_research_queries(self, gap_type: str, context: str) -> List[str]:
        """Generate research queries for a gap"""
        # Extract key terms from context
        terms = re.findall(r'\b[A-Za-z]+\b', context)
        key_terms = [term for term in terms if len(term) > 3][:3]
        
        base_query = " ".join(key_terms)
        
        queries = [
            f"{base_query} best practices",
            f"{base_query} examples",
            f"{base_query} documentation"
        ]
        
        return queries[:2]  # Limit queries
    
    def save_detected_gaps(self):
        """Save detected gaps to file"""
        gaps_file = self.gap_data_path / "detected_gaps.json"
        
        gaps_data = [asdict(gap) for gap in self.detected_gaps]
        
        with open(gaps_file, 'w', encoding='utf-8') as f:
            json.dump(gaps_data, f, indent=2)
        
        self.logger.info(f"Saved {len(self.detected_gaps)} gaps to {gaps_file}")
    
    def get_gap_summary(self) -> Dict[str, Any]:
        """Get summary of detected gaps"""
        if not self.detected_gaps:
            return {"total": 0, "by_type": {}, "by_priority": {}}
        
        gap_types = Counter(gap.gap_type for gap in self.detected_gaps)
        priorities = Counter(gap.priority for gap in self.detected_gaps)
        
        return {
            "total": len(self.detected_gaps),
            "by_type": dict(gap_types),
            "by_priority": dict(priorities),
            "last_analysis": datetime.now().isoformat()
        }

def main():
    """CLI entry point for gap detection"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cortex AI Engine - Knowledge Gap Detection")
    parser.add_argument("--workspace", help="Workspace path")
    parser.add_argument("--quick", action="store_true", help="Quick analysis")
    
    args = parser.parse_args()
    
    engine = CortexAIEngine(args.workspace)
    
    if args.quick:
        print("Running quick analysis...")
        gaps = engine.analyze_workspace()[:5]  # Limit for quick mode
    else:
        print("Running full analysis...")
        gaps = engine.analyze_workspace()
    
    summary = engine.get_gap_summary()
    print(f"Analysis complete! Found {summary['total']} total gaps")
    print(f"By type: {summary['by_type']}")
    print(f"By priority: {summary['by_priority']}")

if __name__ == "__main__":
    main()
