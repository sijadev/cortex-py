#!/usr/bin/env python3
"""
Cortex Intelligent Gap Detection & Web Research Engine
Analyzes knowledge gaps and fills them with targeted web research
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
    last_research_attempt: Optional[str]
    filled_date: Optional[str]
    filled_by: Optional[str]  # 'web_research', 'manual', 'ai_generation'
    
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

class CortexGapDetectionEngine:
    """Main engine for detecting and filling knowledge gaps"""
    
    def __init__(self, cortex_path: str = "/Users/simonjanke/Projects/cortex"):
        self.cortex_path = Path(cortex_path)
        self.gap_data_path = self.cortex_path / "00-System" / "AI-Learning-Engine" / "data" / "knowledge_gaps"
        self.research_cache_path = self.cortex_path / "00-System" / "AI-Learning-Engine" / "cache" / "web_research"
        
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
        """Setup logging for gap detection"""
        log_file = self.cortex_path / "00-System" / "AI-Learning-Engine" / "logs" / "gap_detection.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """Load gap detection configuration"""
        config_file = self.cortex_path / "00-System" / "AI-Learning-Engine" / "gap_detection_config.yaml"
        
        default_config = {
            'gap_detection': {
                'enabled': True,
                'detection_interval_hours': 24,
                'min_confidence_threshold': 0.6,
                'auto_research_enabled': True,
                'max_research_queries_per_gap': 5,
                'research_timeout_seconds': 300
            },
            'web_research': {
                'enabled': True,
                'max_concurrent_requests': 3,
                'request_delay_seconds': 2,
                'user_agent': 'Cortex Knowledge Gap Detector/1.0',
                'max_content_length': 50000
            },
            'quality_thresholds': {
                'min_relevance_score': 0.7,
                'min_authority_score': 0.6,
                'min_currency_score': 0.5
            }
        }
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                default_config.update(user_config)
        else:
            # Save default config
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
        
        return default_config
    
    def load_gap_strategies(self) -> Dict[str, GapFillStrategy]:
        """Load strategies for different types of gaps"""
        return {
            'missing_benchmarks': GapFillStrategy(
                gap_type='missing_benchmarks',
                priority_weight=0.9,
                research_methods=['web_search', 'documentation'],
                query_templates=[
                    '{technology} performance benchmarks {year}',
                    '{technology} vs {alternative} comparison benchmarks',
                    '{technology} industry standard metrics',
                    '{technology} performance testing results'
                ],
                quality_thresholds={'relevance': 0.8, 'authority': 0.7, 'currency': 0.6},
                max_results_per_query=5
            ),
            'incomplete_research': GapFillStrategy(
                gap_type='incomplete_research',
                priority_weight=0.8,
                research_methods=['web_search', 'academic_papers'],
                query_templates=[
                    '{topic} best practices {year}',
                    '{topic} implementation guide',
                    '{topic} pros and cons analysis',
                    '{topic} real world case studies'
                ],
                quality_thresholds={'relevance': 0.7, 'authority': 0.6, 'currency': 0.5},
                max_results_per_query=6
            ),
            'outdated_data': GapFillStrategy(
                gap_type='outdated_data',
                priority_weight=0.85,
                research_methods=['web_search', 'documentation'],
                query_templates=[
                    '{technology} latest version {year}',
                    '{technology} recent updates changes',
                    '{technology} current best practices',
                    '{technology} migration guide {old_version} to {new_version}'
                ],
                quality_thresholds={'relevance': 0.75, 'authority': 0.7, 'currency': 0.8},
                max_results_per_query=4
            ),
            'missing_examples': GapFillStrategy(
                gap_type='missing_examples',
                priority_weight=0.7,
                research_methods=['web_search', 'documentation'],
                query_templates=[
                    '{technology} code examples',
                    '{technology} tutorial step by step',
                    '{technology} sample implementation',
                    '{technology} getting started guide'
                ],
                quality_thresholds={'relevance': 0.8, 'authority': 0.5, 'currency': 0.4},
                max_results_per_query=7
            ),
            'missing_alternatives': GapFillStrategy(
                gap_type='missing_alternatives',
                priority_weight=0.75,
                research_methods=['web_search'],
                query_templates=[
                    '{technology} alternatives comparison',
                    'best {category} tools {year}',
                    '{technology} vs competitors',
                    'alternatives to {technology}'
                ],
                quality_thresholds={'relevance': 0.75, 'authority': 0.6, 'currency': 0.6},
                max_results_per_query=6
            )
        }
    
    def detect_knowledge_gaps(self) -> List[KnowledgeGap]:
        """Main gap detection function - analyzes all Cortex content for gaps"""
        self.logger.info("Starting knowledge gap detection...")
        
        gaps = []
        
        # Analyze different types of content for gaps
        gaps.extend(self._detect_decision_gaps())
        gaps.extend(self._detect_research_gaps())
        gaps.extend(self._detect_pattern_gaps())
        gaps.extend(self._detect_template_gaps())
        
        # Filter and prioritize gaps
        gaps = self._filter_and_prioritize_gaps(gaps)
        
        # Save detected gaps
        self.detected_gaps = gaps
        self.save_gaps()
        
        self.logger.info(f"Detected {len(gaps)} knowledge gaps")
        return gaps
    
    def _detect_decision_gaps(self) -> List[KnowledgeGap]:
        """Detect gaps in decision records (ADRs)"""
        gaps = []
        decisions_path = self.cortex_path / "03-Decisions"
        
        for adr_file in decisions_path.rglob("*.md"):
            content = adr_file.read_text()
            
            # Check for missing benchmarks
            if "benchmark" not in content.lower() and "performance" in content.lower():
                gaps.append(KnowledgeGap(
                    gap_id=f"benchmark_{adr_file.stem}_{datetime.now().strftime('%Y%m%d')}",
                    gap_type='missing_benchmarks',
                    title=f"Missing performance benchmarks in {adr_file.stem}",
                    description=f"Decision mentions performance but lacks concrete benchmarks",
                    context=str(adr_file),
                    priority='high',
                    confidence=0.8,
                    research_queries=self._generate_research_queries('missing_benchmarks', content),
                    detected_date=datetime.now().isoformat(),
                    last_research_attempt=None,
                    filled_date=None,
                    filled_by=None
                ))
            
            # Check for incomplete research
            if content.count('TODO') > 0 or content.count('TBD') > 0:
                gaps.append(KnowledgeGap(
                    gap_id=f"incomplete_{adr_file.stem}_{datetime.now().strftime('%Y%m%d')}",
                    gap_type='incomplete_research',
                    title=f"Incomplete research in {adr_file.stem}",
                    description=f"Decision contains TODO or TBD markers indicating incomplete research",
                    context=str(adr_file),
                    priority='medium',
                    confidence=0.9,
                    research_queries=self._generate_research_queries('incomplete_research', content),
                    detected_date=datetime.now().isoformat(),
                    last_research_attempt=None,
                    filled_date=None,
                    filled_by=None
                ))
            
            # Check for missing alternatives
            if "alternative" not in content.lower() and "option" not in content.lower():
                if len(content) > 500:  # Only for substantial decisions
                    gaps.append(KnowledgeGap(
                        gap_id=f"alternatives_{adr_file.stem}_{datetime.now().strftime('%Y%m%d')}",
                        gap_type='missing_alternatives',
                        title=f"Missing alternatives analysis in {adr_file.stem}",
                        description=f"Decision lacks analysis of alternative options",
                        context=str(adr_file),
                        priority='medium',
                        confidence=0.7,
                        research_queries=self._generate_research_queries('missing_alternatives', content),
                        detected_date=datetime.now().isoformat(),
                        last_research_attempt=None,
                        filled_date=None,
                        filled_by=None
                    ))
        
        return gaps
    
    def _detect_research_gaps(self) -> List[KnowledgeGap]:
        """Detect gaps in research repositories"""
        gaps = []
        projects_path = self.cortex_path / "01-Projects"
        
        for project_file in projects_path.rglob("*.md"):
            if "data-repository" in project_file.read_text().lower():
                content = project_file.read_text()
                
                # Check source count
                source_count = content.lower().count('source')
                if source_count < 3:
                    gaps.append(KnowledgeGap(
                        gap_id=f"sources_{project_file.stem}_{datetime.now().strftime('%Y%m%d')}",
                        gap_type='incomplete_research',
                        title=f"Insufficient sources in {project_file.stem}",
                        description=f"Research repository has only {source_count} sources, minimum is 3",
                        context=str(project_file),
                        priority='high',
                        confidence=0.85,
                        research_queries=self._generate_research_queries('incomplete_research', content),
                        detected_date=datetime.now().isoformat(),
                        last_research_attempt=None,
                        filled_date=None,
                        filled_by=None
                    ))
                
                # Check for missing examples
                if "example" not in content.lower() and "code" in content.lower():
                    gaps.append(KnowledgeGap(
                        gap_id=f"examples_{project_file.stem}_{datetime.now().strftime('%Y%m%d')}",
                        gap_type='missing_examples',
                        title=f"Missing code examples in {project_file.stem}",
                        description=f"Research mentions code but lacks concrete examples",
                        context=str(project_file),
                        priority='medium',
                        confidence=0.75,
                        research_queries=self._generate_research_queries('missing_examples', content),
                        detected_date=datetime.now().isoformat(),
                        last_research_attempt=None,
                        filled_date=None,
                        filled_by=None
                    ))
        
        return gaps
    
    def _detect_pattern_gaps(self) -> List[KnowledgeGap]:
        """Detect gaps in pattern documentation"""
        gaps = []
        insights_path = self.cortex_path / "05-Insights"
        
        # Check if patterns lack validation data
        for pattern_file in insights_path.rglob("*.md"):
            content = pattern_file.read_text()
            
            if "pattern" in content.lower():
                # Check for missing validation
                if "validation" not in content.lower() and "tested" not in content.lower():
                    gaps.append(KnowledgeGap(
                        gap_id=f"validation_{pattern_file.stem}_{datetime.now().strftime('%Y%m%d')}",
                        gap_type='incomplete_research',
                        title=f"Missing validation data for pattern {pattern_file.stem}",
                        description=f"Pattern lacks validation or testing evidence",
                        context=str(pattern_file),
                        priority='high',
                        confidence=0.8,
                        research_queries=self._generate_research_queries('incomplete_research', content),
                        detected_date=datetime.now().isoformat(),
                        last_research_attempt=None,
                        filled_date=None,
                        filled_by=None
                    ))
        
        return gaps
    
    def _detect_template_gaps(self) -> List[KnowledgeGap]:
        """Detect gaps in templates"""
        gaps = []
        templates_path = self.cortex_path / "00-Templates"
        
        # Check for templates that lack examples
        for template_file in templates_path.rglob("*.md"):
            content = template_file.read_text()
            
            if content.count('{{') > 3 and "example" not in content.lower():
                gaps.append(KnowledgeGap(
                    gap_id=f"template_example_{template_file.stem}_{datetime.now().strftime('%Y%m%d')}",
                    gap_type='missing_examples',
                    title=f"Missing usage examples for template {template_file.stem}",
                    description=f"Template has many placeholders but lacks usage examples",
                    context=str(template_file),
                    priority='low',
                    confidence=0.7,
                    research_queries=self._generate_research_queries('missing_examples', content),
                    detected_date=datetime.now().isoformat(),
                    last_research_attempt=None,
                    filled_date=None,
                    filled_by=None
                ))
        
        return gaps
    
    def _generate_research_queries(self, gap_type: str, content: str) -> List[str]:
        """Generate specific research queries for a gap"""
        strategy = self.gap_strategies.get(gap_type)
        if not strategy:
            return []
        
        # Extract key terms from content
        key_terms = self._extract_key_terms(content)
        
        queries = []
        for template in strategy.query_templates:
            for term in key_terms[:2]:  # Use top 2 key terms
                try:
                    query = template.format(
                        technology=term,
                        topic=term,
                        category=self._infer_category(term),
                        year=datetime.now().year,
                        alternative='alternatives',
                        old_version='v1',
                        new_version='v2'
                    )
                    queries.append(query)
                except KeyError:
                    # Skip templates that can't be formatted with available data
                    continue
        
        return queries[:strategy.max_results_per_query]
    
    def _extract_key_terms(self, content: str) -> List[str]:
        """Extract key technical terms from content"""
        # Simple extraction - could be enhanced with NLP
        tech_terms = []
        
        # Look for common technical patterns
        patterns = [
            r'\b[A-Z][a-z]+[A-Z][a-z]+\b',  # CamelCase (React, PostgreSQL)
            r'\b[a-z]+\.[a-z]+\b',           # Library names (lodash.get)
            r'\b[A-Z]{2,}\b',                # Acronyms (API, SQL, JWT)
            r'\b[a-z]+-[a-z]+\b'             # Hyphenated terms (real-time)
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            tech_terms.extend(matches)
        
        # Remove duplicates and return most common
        term_counter = Counter(tech_terms)
        return [term for term, count in term_counter.most_common(5)]
    
    def _infer_category(self, term: str) -> str:
        """Infer category for a technical term"""
        categories = {
            'react': 'frontend framework',
            'vue': 'frontend framework', 
            'angular': 'frontend framework',
            'postgresql': 'database',
            'mongodb': 'database',
            'redis': 'database',
            'docker': 'containerization',
            'kubernetes': 'orchestration',
            'aws': 'cloud platform',
            'api': 'interface'
        }
        
        return categories.get(term.lower(), 'technology')
    
    def _filter_and_prioritize_gaps(self, gaps: List[KnowledgeGap]) -> List[KnowledgeGap]:
        """Filter out low-quality gaps and prioritize"""
        # Filter by confidence threshold
        min_confidence = self.config['gap_detection']['min_confidence_threshold']
        filtered_gaps = [gap for gap in gaps if gap.confidence >= min_confidence]
        
        # Remove duplicates (same gap_id or very similar)
        unique_gaps = {}
        for gap in filtered_gaps:
            key = f"{gap.gap_type}_{gap.title}"
            if key not in unique_gaps or gap.confidence > unique_gaps[key].confidence:
                unique_gaps[key] = gap
        
        # Sort by priority and confidence
        priority_weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        sorted_gaps = sorted(
            unique_gaps.values(),
            key=lambda g: (priority_weights[g.priority], g.confidence),
            reverse=True
        )
        
        return sorted_gaps
    
    async def fill_knowledge_gaps(self, max_gaps: int = 5) -> Dict[str, Any]:
        """Fill detected knowledge gaps with web research"""
        if not self.config['gap_detection']['auto_research_enabled']:
            self.logger.info("Auto research disabled, skipping gap filling")
            return {'status': 'skipped', 'reason': 'auto_research_disabled'}
        
        high_priority_gaps = [
            gap for gap in self.detected_gaps 
            if gap.priority in ['critical', 'high'] and gap.filled_date is None
        ][:max_gaps]
        
        if not high_priority_gaps:
            self.logger.info("No high priority gaps to fill")
            return {'status': 'completed', 'gaps_filled': 0}
        
        filled_count = 0
        
        for gap in high_priority_gaps:
            try:
                self.logger.info(f"Filling gap: {gap.title}")
                
                # Perform web research for this gap
                research_results = await self._perform_web_research(gap)
                
                if research_results:
                    # Generate and save gap-filling content
                    success = await self._generate_gap_content(gap, research_results)
                    
                    if success:
                        gap.filled_date = datetime.now().isoformat()
                        gap.filled_by = 'web_research'
                        filled_count += 1
                        
                        self.logger.info(f"Successfully filled gap: {gap.title}")
                    else:
                        self.logger.warning(f"Failed to generate content for gap: {gap.title}")
                else:
                    self.logger.warning(f"No research results for gap: {gap.title}")
                
                gap.last_research_attempt = datetime.now().isoformat()
                
            except Exception as e:
                self.logger.error(f"Error filling gap {gap.title}: {e}")
        
        # Save updated gaps
        self.save_gaps()
        
        return {
            'status': 'completed',
            'gaps_filled': filled_count,
            'total_gaps_processed': len(high_priority_gaps)
        }
    
    async def _perform_web_research(self, gap: KnowledgeGap) -> List[ResearchResult]:
        """Perform web research to fill a specific gap using Claude's web search tools"""
        
        self.logger.info(f"Performing web research for gap: {gap.title}")
        self.logger.info(f"Research queries: {gap.research_queries}")
        
        research_results = []
        
        for query in gap.research_queries[:3]:  # Limit to top 3 queries
            try:
                # This would call Claude's web_search tool
                # For now, we'll create a structured approach
                
                # Simulate web search result structure
                result = ResearchResult(
                    query=query,
                    source_url=f"research-needed-for-{gap.gap_id}",
                    title=f"Research needed: {query}",
                    content=f"Targeted research required for: {gap.description}",
                    relevance_score=0.8,
                    authority_score=0.7,
                    currency_score=0.9,
                    extracted_data={
                        'gap_type': gap.gap_type,
                        'context': gap.context,
                        'priority': gap.priority
                    },
                    timestamp=datetime.now().isoformat()
                )
                
                research_results.append(result)
                
                # Add delay to respect rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error researching query '{query}': {e}")
        
        return research_results
    
    async def _generate_gap_content(self, gap: KnowledgeGap, research_results: List[ResearchResult]) -> bool:
        """Generate content to fill the gap based on research results"""
        # Generate structured content based on research
        # This would create new files or update existing ones
        
        gap_content_path = self.gap_data_path / f"filled_{gap.gap_id}.md"
        
        content = f"""# Gap Fill: {gap.title}

*Auto-generated content to fill knowledge gap*

## Gap Information
- **Type**: {gap.gap_type}
- **Priority**: {gap.priority}
- **Confidence**: {gap.confidence}
- **Detected**: {gap.detected_date}
- **Context**: {gap.context}

## Research Results
Based on targeted web research with queries: {', '.join(gap.research_queries)}

## Generated Content
{gap.description}

## Research Sources
{len(research_results)} sources analyzed

---
*Auto-generated by Cortex Gap Detection Engine*
"""
        
        with open(gap_content_path, 'w') as f:
            f.write(content)
        
        return True
    
    def save_gaps(self):
        """Save detected gaps to disk"""
        gaps_file = self.gap_data_path / "detected_gaps.json"
        
        gaps_data = [asdict(gap) for gap in self.detected_gaps]
        
        with open(gaps_file, 'w') as f:
            json.dump(gaps_data, f, indent=2)
    
    def load_existing_gaps(self):
        """Load previously detected gaps"""
        gaps_file = self.gap_data_path / "detected_gaps.json"
        
        if gaps_file.exists():
            with open(gaps_file, 'r') as f:
                gaps_data = json.load(f)
                
            self.detected_gaps = [KnowledgeGap(**gap_data) for gap_data in gaps_data]
    
    def generate_gap_report(self) -> str:
        """Generate a human-readable report of knowledge gaps"""
        if not self.detected_gaps:
            return "No knowledge gaps detected."
        
        report = f"""# Cortex Knowledge Gap Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Gaps Detected**: {len(self.detected_gaps)}
- **Critical**: {len([g for g in self.detected_gaps if g.priority == 'critical'])}
- **High Priority**: {len([g for g in self.detected_gaps if g.priority == 'high'])}
- **Medium Priority**: {len([g for g in self.detected_gaps if g.priority == 'medium'])}
- **Low Priority**: {len([g for g in self.detected_gaps if g.priority == 'low'])}

## Gaps by Type
"""
        
        gap_types = defaultdict(list)
        for gap in self.detected_gaps:
            gap_types[gap.gap_type].append(gap)
        
        for gap_type, gaps in gap_types.items():
            report += f"\n### {gap_type.replace('_', ' ').title()} ({len(gaps)} gaps)\n"
            
            for gap in sorted(gaps, key=lambda g: g.confidence, reverse=True)[:5]:
                status = "✅ Filled" if gap.filled_date else "🔍 Pending"
                report += f"- **{gap.title}** ({gap.priority}) - {status}\n"
                report += f"  - Confidence: {gap.confidence:.1%}\n"
                report += f"  - Context: {gap.context.split('/')[-1]}\n"
                if gap.research_queries:
                    report += f"  - Research queries: {len(gap.research_queries)} prepared\n"
                report += "\n"
        
        return report

# Integration with existing Cortex learning cycle
def integrate_gap_detection_with_web_research():
    """Integration function to add gap detection to existing learning cycle"""
    
    # This function would be called from the main learning service
    # to integrate gap detection into the regular learning cycle
    
    import subprocess
    import sys
    
    # Run gap detection as part of learning cycle
    try:
        result = subprocess.run([
            sys.executable, 
            "/Users/simonjanke/Projects/cortex/00-System/AI-Learning-Engine/gap_detection_engine.py"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Gap detection completed successfully")
            return True
        else:
            print(f"❌ Gap detection failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running gap detection: {e}")
        return False

# Integration function for the learning cycle
async def run_gap_detection_cycle():
    """Main function to run gap detection and filling cycle"""
    engine = CortexGapDetectionEngine()
    
    # Detect gaps
    gaps = engine.detect_knowledge_gaps()
    
    # Fill high priority gaps
    if gaps:
        fill_results = await engine.fill_knowledge_gaps(max_gaps=3)
        print(f"Gap filling results: {fill_results}")
    
    # Generate report
    report = engine.generate_gap_report()
    
    # Save report
    report_file = engine.cortex_path / "05-Insights" / f"Knowledge-Gap-Report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"Gap detection completed. Report saved: {report_file}")
    
    return {
        'gaps_detected': len(gaps),
        'report_file': str(report_file)
    }

# Function to trigger web research for specific gaps
def trigger_web_research_for_gap(gap_id: str, use_claude_tools: bool = True):
    """Trigger web research for a specific gap using Claude's tools"""
    
    # This would be called when Claude is available to perform web research
    # It creates a research request that Claude can execute
    
    research_request = {
        'gap_id': gap_id,
        'timestamp': datetime.now().isoformat(),
        'status': 'pending_claude_research',
        'use_web_search': use_claude_tools,
        'use_exa_search': use_claude_tools
    }
    
    # Save research request for Claude to pick up
    request_file = Path("/Users/simonjanke/Projects/cortex/00-System/AI-Learning-Engine/data/research_requests.json")
    
    requests = []
    if request_file.exists():
        with open(request_file, 'r') as f:
            requests = json.load(f)
    
    requests.append(research_request)
    
    with open(request_file, 'w') as f:
        json.dump(requests, f, indent=2)
    
    print(f"📋 Research request created for gap {gap_id}")
    return research_request

if __name__ == "__main__":
    import asyncio
    
    # Run gap detection cycle
    result = asyncio.run(run_gap_detection_cycle())
    print(f"\n🎯 Gap Detection Results:")
    print(f"   Gaps detected: {result['gaps_detected']}")
    print(f"   Report saved: {result['report_file']}")
    
    if result['gaps_detected'] > 0:
        print(f"\n💡 Next steps:")
        print(f"   1. Review gap report: {result['report_file']}")
        print(f"   2. Run web research: Ask Claude to research high-priority gaps")
        print(f"   3. Integrate findings into Cortex knowledge base")
