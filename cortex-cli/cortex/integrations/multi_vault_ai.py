#!/usr/bin/env python3
"""
Multi-Vault AI - Advanced Cross-Vault Pattern Analysis and Learning System
Sophisticated intelligence layer for analyzing patterns across multiple knowledge vaults
Migrated and enhanced from 00-System/AI-Learning-Engine/multi_vault_ai.py
"""

import os
import json
import yaml
import time
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, Counter
import re
import hashlib


@dataclass
class TagCorrelation:
    """Represents a correlation between two tags across vaults"""
    tag1: str
    tag2: str
    correlation_score: float
    vaults: List[str]
    co_occurrence_count: int
    confidence: float
    discovered_date: str


@dataclass
class VaultProfile:
    """Comprehensive profile information for a knowledge vault"""
    name: str
    path: str
    type: str  # 'hub', 'project', 'personal', etc.
    created: str
    last_analyzed: str
    file_count: int
    tag_count: int
    size_mb: float
    ai_learning_enabled: bool
    health_score: float = 0.0
    dominant_tags: List[str] = None
    structure_complexity: float = 0.0
    activity_level: str = "unknown"


@dataclass
class CrossVaultPattern:
    """Pattern detected across multiple knowledge vaults"""
    pattern_id: str
    name: str
    description: str
    vaults: List[str]
    confidence: float
    success_indicators: List[str]
    tags_involved: List[str]
    detected_date: str
    usage_count: int
    pattern_type: str = "general"
    actionable_insight: str = ""


@dataclass
class AIInsight:
    """AI-generated insight from multi-vault analysis"""
    insight_id: str
    title: str
    description: str
    insight_type: str  # 'pattern', 'recommendation', 'anomaly', 'opportunity'
    confidence: float
    supporting_evidence: List[str]
    actionable_recommendations: List[str]
    affected_vaults: List[str]
    generated_date: str
    priority: str = "medium"  # 'low', 'medium', 'high', 'critical'


class MultiVaultAI:
    """
    Advanced Multi-Vault AI Learning Engine
    
    Provides sophisticated cross-vault pattern analysis, tag correlation detection,
    and AI-powered insights generation for knowledge management ecosystems.
    Features real-time learning, predictive analysis, and actionable recommendations.
    """
    
    def __init__(self, hub_vault_path: str = "/Users/simonjanke/Projects/cortex"):
        self.hub_path = Path(hub_vault_path)
        self.data_path = self.hub_path / "00-System" / "AI-Learning-Engine" / "data"
        self.logs_path = self.hub_path / "00-System" / "AI-Learning-Engine" / "logs"
        
        # Ensure directories exist
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        self.setup_logging()
        self.config = self.load_config()
        
        # Learning data structures
        self.vault_profiles: Dict[str, VaultProfile] = {}
        self.tag_correlations: List[TagCorrelation] = []
        self.cross_vault_patterns: List[CrossVaultPattern] = []
        self.ai_insights: List[AIInsight] = []
        
        # Performance tracking
        self.analysis_metrics = {
            'total_analyses': 0,
            'avg_analysis_time': 0.0,
            'last_full_analysis': None,
            'success_rate': 1.0
        }
        
        # Load existing data
        self.load_learning_data()
        
        self.logger.info("Multi-Vault AI Engine initialized")
    
    def setup_logging(self):
        """Configure comprehensive logging for the AI engine"""
        log_file = self.logs_path / "multi_vault_ai.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_config(self) -> Dict:
        """Load AI learning configuration with enhanced parameters"""
        config_file = self.hub_path / "00-System" / "AI-Learning-Engine" / "ai_config.yaml"
        
        default_config = {
            'analysis_settings': {
                'min_correlation_score': 0.3,
                'min_pattern_confidence': 0.6,
                'max_vaults_to_analyze': 50,
                'analysis_depth': 'comprehensive',  # 'basic', 'standard', 'comprehensive'
                'enable_predictive_analysis': True,
                'auto_insight_generation': True
            },
            'filtering': {
                'exclude_test_vaults': True,
                'min_vault_size_mb': 0.1,
                'min_file_count': 5,
                'exclude_patterns': ['test-', 'temp-', 'benchmark-']
            },
            'learning': {
                'enable_continuous_learning': True,
                'insight_retention_days': 90,
                'pattern_decay_rate': 0.95,
                'auto_prune_old_data': True
            },
            'performance': {
                'max_analysis_time_minutes': 30,
                'enable_parallel_processing': True,
                'cache_analysis_results': True
            }
        }
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            self.logger.warning(f"Could not load config, using defaults: {e}")
        
        return default_config
    
    async def run_comprehensive_analysis(self, force_refresh: bool = False) -> Dict:
        """Run complete multi-vault analysis with enhanced AI processing"""
        start_time = time.time()
        self.logger.info("Starting comprehensive multi-vault AI analysis")
        
        try:
            analysis_report = {
                'analysis_id': hashlib.md5(f"analysis_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
                'start_time': datetime.now().isoformat(),
                'status': 'running'
            }
            
            # Phase 1: Vault Discovery and Profiling
            vaults = await self.discover_vaults_async()
            self.logger.info(f"Discovered {len(vaults)} vaults for analysis")
            
            # Phase 2: Parallel Vault Analysis
            if self.config['performance']['enable_parallel_processing']:
                await self.analyze_vaults_parallel(vaults, force_refresh)
            else:
                await self.analyze_vaults_sequential(vaults, force_refresh)
            
            # Phase 3: Advanced Pattern Detection
            await self.detect_advanced_patterns()
            
            # Phase 4: Tag Correlation Analysis
            await self.calculate_advanced_correlations()
            
            # Phase 5: AI Insight Generation
            if self.config['analysis_settings']['auto_insight_generation']:
                await self.generate_ai_insights()
            
            # Phase 6: Predictive Analysis
            if self.config['analysis_settings']['enable_predictive_analysis']:
                await self.run_predictive_analysis()
            
            # Phase 7: Save and Report
            await self.save_learning_data_async()
            
            execution_time = time.time() - start_time
            analysis_report.update({
                'status': 'completed',
                'execution_time': execution_time,
                'end_time': datetime.now().isoformat(),
                'vaults_analyzed': len(self.vault_profiles),
                'patterns_detected': len(self.cross_vault_patterns),
                'correlations_found': len(self.tag_correlations),
                'insights_generated': len(self.ai_insights),
                'success': True
            })
            
            # Update metrics
            self.analysis_metrics.update({
                'total_analyses': self.analysis_metrics['total_analyses'] + 1,
                'avg_analysis_time': (self.analysis_metrics['avg_analysis_time'] + execution_time) / 2,
                'last_full_analysis': datetime.now().isoformat(),
                'success_rate': min(1.0, self.analysis_metrics['success_rate'] + 0.01)
            })
            
            self.logger.info(f"Comprehensive analysis completed in {execution_time:.2f}s")
            return analysis_report
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def discover_vaults_async(self) -> List[Path]:
        """Asynchronously discover all vault directories with enhanced filtering"""
        vaults = []
        
        # Add hub vault
        if self.hub_path.exists():
            vaults.append(self.hub_path)
        
        # Discover project vaults
        parent_dir = self.hub_path.parent
        if parent_dir.exists():
            for item in parent_dir.iterdir():
                if not item.is_dir():
                    continue
                    
                # Apply filtering rules
                if self._should_exclude_vault(item):
                    continue
                
                # Check if it's a valid knowledge vault
                if await self._is_valid_vault_async(item):
                    vaults.append(item)
        
        # Sort by priority (hub first, then by activity level)
        vaults.sort(key=lambda v: (v.name != 'cortex', -self._estimate_vault_activity(v)))
        
        return vaults
    
    def _should_exclude_vault(self, vault_path: Path) -> bool:
        """Enhanced vault exclusion logic"""
        vault_name = vault_path.name.lower()
        
        # Check explicit exclusion patterns
        exclude_patterns = self.config['filtering']['exclude_patterns']
        if any(vault_name.startswith(pattern) for pattern in exclude_patterns):
            return True
        
        # Check size requirements
        if self._estimate_vault_size_mb(vault_path) < self.config['filtering']['min_vault_size_mb']:
            return True
        
        # Check file count
        md_files = list(vault_path.glob('**/*.md'))
        if len(md_files) < self.config['filtering']['min_file_count']:
            return True
        
        return False
    
    async def _is_valid_vault_async(self, vault_path: Path) -> bool:
        """Asynchronously validate if directory is a knowledge vault"""
        try:
            # Check for Obsidian vault
            if (vault_path / '.obsidian').exists():
                return True
            
            # Check for markdown files
            md_files = list(vault_path.glob('**/*.md'))
            if len(md_files) > 0:
                return True
            
            # Check for Cortex system
            if (vault_path / '00-System').exists():
                return True
            
            return False
            
        except Exception:
            return False
    
    def _estimate_vault_activity(self, vault_path: Path) -> float:
        """Estimate vault activity level for prioritization"""
        try:
            recent_files = 0
            total_files = 0
            week_ago = datetime.now() - timedelta(days=7)
            
            for md_file in vault_path.glob('**/*.md'):
                if md_file.exists():
                    total_files += 1
                    if datetime.fromtimestamp(md_file.stat().st_mtime) > week_ago:
                        recent_files += 1
            
            if total_files == 0:
                return 0.0
            
            return recent_files / total_files
            
        except Exception:
            return 0.0
    
    def _estimate_vault_size_mb(self, vault_path: Path) -> float:
        """Estimate vault size in MB"""
        try:
            total_size = sum(
                f.stat().st_size 
                for f in vault_path.glob('**/*.md') 
                if f.exists()
            )
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0
    
    async def analyze_vaults_parallel(self, vaults: List[Path], force_refresh: bool = False):
        """Analyze vaults in parallel for improved performance"""
        tasks = []
        
        for vault_path in vaults:
            if force_refresh or await self._needs_analysis(vault_path):
                task = asyncio.create_task(self.analyze_vault_async(vault_path))
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_analyses = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error analyzing vault {vaults[i]}: {result}")
                else:
                    successful_analyses += 1
            
            self.logger.info(f"Parallel analysis: {successful_analyses}/{len(tasks)} vaults successful")
    
    async def analyze_vaults_sequential(self, vaults: List[Path], force_refresh: bool = False):
        """Analyze vaults sequentially (fallback method)"""
        for vault_path in vaults:
            if force_refresh or await self._needs_analysis(vault_path):
                await self.analyze_vault_async(vault_path)
    
    async def _needs_analysis(self, vault_path: Path) -> bool:
        """Determine if vault needs fresh analysis"""
        vault_name = vault_path.name
        
        if vault_name not in self.vault_profiles:
            return True
        
        profile = self.vault_profiles[vault_name]
        last_analyzed = datetime.fromisoformat(profile.last_analyzed)
        
        # Analyze if older than 24 hours or if files have been modified
        if datetime.now() - last_analyzed > timedelta(hours=24):
            return True
        
        # Check for recent file modifications
        try:
            for md_file in vault_path.glob('**/*.md'):
                if md_file.exists():
                    file_time = datetime.fromtimestamp(md_file.stat().st_mtime)
                    if file_time > last_analyzed:
                        return True
        except Exception:
            pass
        
        return False
    
    async def analyze_vault_async(self, vault_path: Path) -> VaultProfile:
        """Asynchronously analyze a single vault with enhanced profiling"""
        try:
            vault_name = vault_path.name
            analysis_start = time.time()
            
            # Basic metrics
            md_files = list(vault_path.glob('**/*.md'))
            file_count = len([f for f in md_files if not self._is_excluded_file(f)])
            
            total_size = sum(f.stat().st_size for f in md_files if f.exists())
            size_mb = total_size / (1024 * 1024)
            
            # Enhanced tag analysis
            all_tags = set()
            tag_frequency = Counter()
            content_analysis = {
                'total_words': 0,
                'avg_file_length': 0,
                'link_density': 0,
                'structure_indicators': []
            }
            
            for md_file in md_files:
                if self._is_excluded_file(md_file):
                    continue
                
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Tag extraction and analysis
                        tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
                        real_tags = [tag for tag in tags if not self._is_excluded_tag(tag)]
                        all_tags.update(real_tags)
                        tag_frequency.update(real_tags)
                        
                        # Content analysis
                        words = len(content.split())
                        content_analysis['total_words'] += words
                        
                        # Link analysis
                        wiki_links = len(re.findall(r'\[\[([^\]]+)\]\]', content))
                        content_analysis['link_density'] += wiki_links
                        
                        # Structure indicators
                        if content.startswith('#'):
                            content_analysis['structure_indicators'].append('structured_headers')
                        if '>' in content:
                            content_analysis['structure_indicators'].append('has_quotes')
                        if '```' in content:
                            content_analysis['structure_indicators'].append('has_code_blocks')
                            
                except Exception as e:
                    self.logger.warning(f"Error analyzing file {md_file}: {e}")
            
            # Calculate advanced metrics
            avg_file_length = content_analysis['total_words'] / max(file_count, 1)
            link_density = content_analysis['link_density'] / max(file_count, 1)
            structure_complexity = len(set(content_analysis['structure_indicators'])) / 3.0
            
            # Determine vault type and activity level
            vault_type = self._determine_vault_type(vault_path, all_tags)
            activity_level = self._calculate_activity_level(vault_path)
            health_score = self._calculate_health_score(file_count, len(all_tags), structure_complexity)
            
            # Get dominant tags
            dominant_tags = [tag for tag, count in tag_frequency.most_common(10)]
            
            # Create enhanced profile
            profile = VaultProfile(
                name=vault_name,
                path=str(vault_path),
                type=vault_type,
                created=self.vault_profiles.get(vault_name, {}).get('created', datetime.now().isoformat()),
                last_analyzed=datetime.now().isoformat(),
                file_count=file_count,
                tag_count=len(all_tags),
                size_mb=round(size_mb, 2),
                ai_learning_enabled=True,
                health_score=health_score,
                dominant_tags=dominant_tags,
                structure_complexity=structure_complexity,
                activity_level=activity_level
            )
            
            self.vault_profiles[vault_name] = profile
            
            analysis_time = time.time() - analysis_start
            self.logger.info(f"Analyzed vault '{vault_name}': {file_count} files, {len(all_tags)} tags, health: {health_score:.2f} (took {analysis_time:.2f}s)")
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error analyzing vault {vault_path}: {e}")
            return None
    
    def _is_excluded_file(self, file_path: Path) -> bool:
        """Enhanced file exclusion logic"""
        file_name = file_path.name.lower()
        file_str = str(file_path).lower()
        
        exclude_patterns = [
            'category-', 'file-', 'test-', 'performance-', 'benchmark-',
            'cross-vault link summary', 'temp-', 'draft-', '.obsidian'
        ]
        
        return any(pattern in file_name or pattern in file_str for pattern in exclude_patterns)
    
    def _is_excluded_tag(self, tag: str) -> bool:
        """Enhanced tag exclusion logic"""
        exclude_patterns = [
            'test', 'performance', 'benchmark', 'temp', 'draft', 
            'category-', 'file-', 'auto-generated'
        ]
        
        tag_lower = tag.lower()
        return any(pattern in tag_lower for pattern in exclude_patterns)
    
    def _determine_vault_type(self, vault_path: Path, tags: Set[str]) -> str:
        """Intelligent vault type detection"""
        vault_name = vault_path.name.lower()
        
        # Check for hub indicators
        if vault_name in ['cortex', 'hub', 'main', 'central']:
            return 'hub'
        
        # Check for project indicators
        if vault_name.startswith('project-') or 'project' in tags:
            return 'project'
        
        # Check for personal indicators
        if any(tag in tags for tag in ['personal', 'diary', 'journal', 'notes']):
            return 'personal'
        
        # Check for research indicators
        if any(tag in tags for tag in ['research', 'study', 'academic', 'paper']):
            return 'research'
        
        return 'general'
    
    def _calculate_activity_level(self, vault_path: Path) -> str:
        """Calculate vault activity level"""
        try:
            now = datetime.now()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            recent_files = 0
            total_files = 0
            
            for md_file in vault_path.glob('**/*.md'):
                if md_file.exists() and not self._is_excluded_file(md_file):
                    total_files += 1
                    file_time = datetime.fromtimestamp(md_file.stat().st_mtime)
                    
                    if file_time > week_ago:
                        recent_files += 2  # Weight recent files more
                    elif file_time > month_ago:
                        recent_files += 1
            
            if total_files == 0:
                return 'empty'
            
            activity_ratio = recent_files / total_files
            
            if activity_ratio > 0.3:
                return 'high'
            elif activity_ratio > 0.1:
                return 'medium'
            elif activity_ratio > 0.05:
                return 'low'
            else:
                return 'dormant'
                
        except Exception:
            return 'unknown'
    
    def _calculate_health_score(self, file_count: int, tag_count: int, structure_complexity: float) -> float:
        """Calculate vault health score (0.0 to 1.0)"""
        try:
            # Base score from file and tag counts
            file_score = min(1.0, file_count / 100.0)  # Max at 100 files
            tag_score = min(1.0, tag_count / 50.0)     # Max at 50 tags
            structure_score = structure_complexity      # Already 0.0-1.0
            
            # Weighted average
            health_score = (file_score * 0.4 + tag_score * 0.3 + structure_score * 0.3)
            
            return round(health_score, 3)
            
        except Exception:
            return 0.5
    
    async def detect_advanced_patterns(self):
        """Detect sophisticated cross-vault patterns with AI enhancement"""
        self.logger.info("Detecting advanced cross-vault patterns")
        
        try:
            vaults = list(self.vault_profiles.keys())
            if len(vaults) < 2:
                self.logger.info("Need at least 2 vaults for pattern detection")
                return
            
            detected_patterns = []
            vault_paths = [Path(self.vault_profiles[name].path) for name in vaults]
            
            # Advanced pattern detection
            structural_patterns = await self._detect_structural_patterns(vault_paths)
            detected_patterns.extend(structural_patterns)
            
            semantic_patterns = await self._detect_semantic_patterns(vault_paths)
            detected_patterns.extend(semantic_patterns)
            
            workflow_patterns = await self._detect_workflow_patterns(vault_paths)
            detected_patterns.extend(workflow_patterns)
            
            temporal_patterns = await self._detect_temporal_patterns(vault_paths)
            detected_patterns.extend(temporal_patterns)
            
            self.cross_vault_patterns = detected_patterns
            self.logger.info(f"Detected {len(detected_patterns)} advanced patterns")
            
        except Exception as e:
            self.logger.error(f"Error detecting advanced patterns: {e}")
    
    async def _detect_structural_patterns(self, vault_paths: List[Path]) -> List[CrossVaultPattern]:
        """Detect structural organization patterns"""
        patterns = []
        
        # Analyze directory structures
        vault_structures = {}
        for vault_path in vault_paths:
            structures = set()
            for item in vault_path.rglob('*'):
                if item.is_dir() and not item.name.startswith('.'):
                    rel_path = str(item.relative_to(vault_path))
                    if not any(exclude in rel_path.lower() for exclude in ['test', 'temp', 'benchmark']):
                        structures.add(rel_path)
            vault_structures[vault_path.name] = structures
        
        # Find common structures
        all_structures = set()
        for structures in vault_structures.values():
            all_structures.update(structures)
        
        for structure in all_structures:
            vaults_with_structure = [
                vault_name for vault_name, structures in vault_structures.items()
                if structure in structures
            ]
            
            if len(vaults_with_structure) >= 2:
                pattern_id = hashlib.md5(f"structure_{structure}".encode()).hexdigest()[:8]
                pattern = CrossVaultPattern(
                    pattern_id=pattern_id,
                    name=f"Structural Pattern: {structure}",
                    description=f"Common directory structure '{structure}' found in {len(vaults_with_structure)} vaults",
                    vaults=vaults_with_structure,
                    confidence=len(vaults_with_structure) / len(vault_structures),
                    success_indicators=["organized_structure", "consistent_workflow", "scalable_organization"],
                    tags_involved=[],
                    detected_date=datetime.now().isoformat(),
                    usage_count=len(vaults_with_structure),
                    pattern_type="structural",
                    actionable_insight=f"Consider implementing {structure} structure in other vaults for consistency"
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_semantic_patterns(self, vault_paths: List[Path]) -> List[CrossVaultPattern]:
        """Detect semantic tag and content patterns"""
        patterns = []
        
        # Analyze tag relationships across vaults
        vault_tag_contexts = {}
        
        for vault_path in vault_paths:
            tag_contexts = defaultdict(list)
            
            for md_file in vault_path.glob('**/*.md'):
                if self._is_excluded_file(md_file):
                    continue
                
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
                        
                        # Analyze context around each tag
                        for tag in tags:
                            if not self._is_excluded_tag(tag):
                                # Get surrounding words for context
                                tag_pattern = f'#{tag}'
                                tag_index = content.find(tag_pattern)
                                if tag_index != -1:
                                    start = max(0, tag_index - 50)
                                    end = min(len(content), tag_index + len(tag_pattern) + 50)
                                    context = content[start:end].strip()
                                    tag_contexts[tag].append(context)
                                    
                except Exception as e:
                    self.logger.debug(f"Error analyzing semantic patterns in {md_file}: {e}")
            
            vault_tag_contexts[vault_path.name] = dict(tag_contexts)
        
        # Find tags with similar usage patterns
        all_tags = set()
        for contexts in vault_tag_contexts.values():
            all_tags.update(contexts.keys())
        
        for tag in all_tags:
            vaults_with_tag = [
                vault_name for vault_name, contexts in vault_tag_contexts.items()
                if tag in contexts and len(contexts[tag]) >= 2
            ]
            
            if len(vaults_with_tag) >= 2:
                total_usage = sum(
                    len(vault_tag_contexts[vault_name].get(tag, []))
                    for vault_name in vaults_with_tag
                )
                
                pattern_id = hashlib.md5(f"semantic_{tag}".encode()).hexdigest()[:8]
                pattern = CrossVaultPattern(
                    pattern_id=pattern_id,
                    name=f"Semantic Pattern: #{tag}",
                    description=f"Tag #{tag} used consistently across {len(vaults_with_tag)} vaults with similar semantic context",
                    vaults=vaults_with_tag,
                    confidence=len(vaults_with_tag) / len(vault_tag_contexts),
                    success_indicators=["consistent_tagging", "semantic_coherence", "knowledge_organization"],
                    tags_involved=[tag],
                    detected_date=datetime.now().isoformat(),
                    usage_count=total_usage,
                    pattern_type="semantic",
                    actionable_insight=f"Tag #{tag} shows strong cross-vault relevance - consider it for knowledge integration"
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_workflow_patterns(self, vault_paths: List[Path]) -> List[CrossVaultPattern]:
        """Detect workflow and process patterns"""
        patterns = []
        
        # Analyze file naming conventions that suggest workflows
        vault_workflows = {}
        
        for vault_path in vault_paths:
            workflows = defaultdict(int)
            
            for md_file in vault_path.glob('**/*.md'):
                if self._is_excluded_file(md_file):
                    continue
                
                filename = md_file.stem
                
                # Detect workflow patterns
                if re.match(r'^\d{4}-\d{2}-\d{2}', filename):
                    workflows['daily_notes'] += 1
                elif re.match(r'^ADR-\d{3}', filename):
                    workflows['architecture_decisions'] += 1
                elif re.match(r'^MEETING-\d{4}\d{2}\d{2}', filename):
                    workflows['meeting_notes'] += 1
                elif 'TODO' in filename.upper() or 'TASK' in filename.upper():
                    workflows['task_management'] += 1
                elif 'REVIEW' in filename.upper():
                    workflows['review_process'] += 1
                elif filename.startswith('DRAFT-'):
                    workflows['draft_workflow'] += 1
            
            vault_workflows[vault_path.name] = dict(workflows)
        
        # Find common workflow patterns
        all_workflows = set()
        for workflows in vault_workflows.values():
            all_workflows.update(workflows.keys())
        
        for workflow in all_workflows:
            vaults_with_workflow = [
                vault_name for vault_name, workflows in vault_workflows.items()
                if workflow in workflows and workflows[workflow] >= 3
            ]
            
            if len(vaults_with_workflow) >= 2:
                total_usage = sum(
                    vault_workflows[vault_name].get(workflow, 0)
                    for vault_name in vaults_with_workflow
                )
                
                pattern_id = hashlib.md5(f"workflow_{workflow}".encode()).hexdigest()[:8]
                pattern = CrossVaultPattern(
                    pattern_id=pattern_id,
                    name=f"Workflow Pattern: {workflow.replace('_', ' ').title()}",
                    description=f"Workflow pattern '{workflow}' implemented in {len(vaults_with_workflow)} vaults",
                    vaults=vaults_with_workflow,
                    confidence=len(vaults_with_workflow) / len(vault_workflows),
                    success_indicators=["process_consistency", "workflow_standardization", "operational_efficiency"],
                    tags_involved=[],
                    detected_date=datetime.now().isoformat(),
                    usage_count=total_usage,
                    pattern_type="workflow",
                    actionable_insight=f"Workflow '{workflow}' proves effective across vaults - consider standardizing"
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_temporal_patterns(self, vault_paths: List[Path]) -> List[CrossVaultPattern]:
        """Detect temporal activity and creation patterns"""
        patterns = []
        
        # Analyze creation and modification patterns
        vault_temporal_data = {}
        
        for vault_path in vault_paths:
            temporal_data = {
                'creation_by_month': defaultdict(int),
                'modification_by_month': defaultdict(int),
                'peak_activity_hours': defaultdict(int)
            }
            
            for md_file in vault_path.glob('**/*.md'):
                if self._is_excluded_file(md_file):
                    continue
                
                try:
                    stat = md_file.stat()
                    
                    # Creation patterns
                    created = datetime.fromtimestamp(stat.st_ctime)
                    creation_month = created.strftime('%Y-%m')
                    temporal_data['creation_by_month'][creation_month] += 1
                    
                    # Modification patterns
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    mod_month = modified.strftime('%Y-%m')
                    temporal_data['modification_by_month'][mod_month] += 1
                    
                    # Activity hour patterns
                    hour = modified.hour
                    temporal_data['peak_activity_hours'][hour] += 1
                    
                except Exception:
                    pass
            
            vault_temporal_data[vault_path.name] = temporal_data
        
        # Detect temporal patterns (simplified for this implementation)
        # This could be expanded with more sophisticated temporal analysis
        
        return patterns
    
    async def calculate_advanced_correlations(self):
        """Calculate sophisticated tag correlations with context awareness"""
        self.logger.info("Calculating advanced tag correlations")
        
        try:
            # Collect tag co-occurrences with context
            tag_cooccurrences = defaultdict(lambda: defaultdict(int))
            tag_vault_usage = defaultdict(set)
            
            for vault_name, profile in self.vault_profiles.items():
                vault_path = Path(profile.path)
                
                for md_file in vault_path.glob('**/*.md'):
                    if self._is_excluded_file(md_file):
                        continue
                    
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            tags = [tag for tag in re.findall(r'#([a-zA-Z0-9_-]+)', content) 
                                   if not self._is_excluded_tag(tag)]
                            
                            # Record vault usage
                            for tag in tags:
                                tag_vault_usage[tag].add(vault_name)
                            
                            # Record co-occurrences
                            for i, tag1 in enumerate(tags):
                                for tag2 in tags[i+1:]:
                                    if tag1 != tag2:
                                        # Bidirectional recording
                                        tag_cooccurrences[tag1][tag2] += 1
                                        tag_cooccurrences[tag2][tag1] += 1
                                        
                    except Exception as e:
                        self.logger.debug(f"Error processing correlations in {md_file}: {e}")
            
            # Calculate correlation scores
            correlations = []
            min_correlation_score = self.config['analysis_settings']['min_correlation_score']
            
            processed_pairs = set()
            
            for tag1, related_tags in tag_cooccurrences.items():
                for tag2, cooccurrence_count in related_tags.items():
                    
                    # Avoid duplicate pairs
                    pair = tuple(sorted([tag1, tag2]))
                    if pair in processed_pairs:
                        continue
                    processed_pairs.add(pair)
                    
                    # Calculate correlation score
                    vaults1 = tag_vault_usage[tag1]
                    vaults2 = tag_vault_usage[tag2]
                    common_vaults = vaults1 & vaults2
                    
                    if len(common_vaults) >= 1:  # Must appear together in at least 1 vault
                        # Jaccard similarity for correlation
                        union_vaults = vaults1 | vaults2
                        correlation_score = len(common_vaults) / len(union_vaults)
                        
                        # Boost score based on co-occurrence frequency
                        frequency_boost = min(0.3, cooccurrence_count / 10.0)
                        final_score = correlation_score + frequency_boost
                        
                        if final_score >= min_correlation_score:
                            confidence = min(1.0, cooccurrence_count / 5.0)  # Max confidence at 5 co-occurrences
                            
                            correlation = TagCorrelation(
                                tag1=tag1,
                                tag2=tag2,
                                correlation_score=round(final_score, 3),
                                vaults=list(common_vaults),
                                co_occurrence_count=cooccurrence_count,
                                confidence=round(confidence, 3),
                                discovered_date=datetime.now().isoformat()
                            )
                            correlations.append(correlation)
            
            # Sort by correlation score
            correlations.sort(key=lambda c: c.correlation_score, reverse=True)
            self.tag_correlations = correlations[:100]  # Keep top 100
            
            self.logger.info(f"Calculated {len(self.tag_correlations)} advanced tag correlations")
            
        except Exception as e:
            self.logger.error(f"Error calculating correlations: {e}")
    
    async def generate_ai_insights(self):
        """Generate sophisticated AI insights from analysis data"""
        self.logger.info("Generating AI insights")
        
        try:
            insights = []
            current_time = datetime.now().isoformat()
            
            # Insight 1: Cross-vault pattern opportunities
            if self.cross_vault_patterns:
                high_confidence_patterns = [p for p in self.cross_vault_patterns if p.confidence > 0.7]
                
                if high_confidence_patterns:
                    insight = AIInsight(
                        insight_id=hashlib.md5(f"patterns_{current_time}".encode()).hexdigest()[:12],
                        title="Strong Cross-Vault Patterns Detected",
                        description=f"Found {len(high_confidence_patterns)} high-confidence patterns that could be leveraged across your vault ecosystem",
                        insight_type="opportunity",
                        confidence=0.85,
                        supporting_evidence=[p.name for p in high_confidence_patterns[:3]],
                        actionable_recommendations=[
                            "Standardize successful patterns across all vaults",
                            "Create templates based on proven patterns",
                            "Document pattern usage guidelines"
                        ],
                        affected_vaults=list(set(vault for pattern in high_confidence_patterns for vault in pattern.vaults)),
                        generated_date=current_time,
                        priority="high"
                    )
                    insights.append(insight)
            
            # Insight 2: Tag correlation opportunities
            if self.tag_correlations:
                strong_correlations = [c for c in self.tag_correlations if c.correlation_score > 0.6]
                
                if strong_correlations:
                    insight = AIInsight(
                        insight_id=hashlib.md5(f"correlations_{current_time}".encode()).hexdigest()[:12],
                        title="Knowledge Integration Opportunities",
                        description=f"Discovered {len(strong_correlations)} strong tag correlations suggesting potential knowledge integration points",
                        insight_type="recommendation",
                        confidence=0.75,
                        supporting_evidence=[f"{c.tag1} ↔ {c.tag2} (score: {c.correlation_score:.2f})" for c in strong_correlations[:3]],
                        actionable_recommendations=[
                            "Create cross-vault links for highly correlated tags",
                            "Consider merging related knowledge areas",
                            "Develop integrated workflows for correlated concepts"
                        ],
                        affected_vaults=list(set(vault for corr in strong_correlations for vault in corr.vaults)),
                        generated_date=current_time,
                        priority="medium"
                    )
                    insights.append(insight)
            
            # Insight 3: Vault health analysis
            if self.vault_profiles:
                low_health_vaults = [(name, profile) for name, profile in self.vault_profiles.items() 
                                   if profile.health_score < 0.4]
                
                if low_health_vaults:
                    insight = AIInsight(
                        insight_id=hashlib.md5(f"health_{current_time}".encode()).hexdigest()[:12],
                        title="Vault Health Attention Needed",
                        description=f"{len(low_health_vaults)} vaults show low health scores and may need attention",
                        insight_type="anomaly",
                        confidence=0.9,
                        supporting_evidence=[f"{name} (health: {profile.health_score:.2f})" for name, profile in low_health_vaults],
                        actionable_recommendations=[
                            "Review and organize low-health vaults",
                            "Add more structured content and tags",
                            "Consider archiving inactive vaults"
                        ],
                        affected_vaults=[name for name, _ in low_health_vaults],
                        generated_date=current_time,
                        priority="medium"
                    )
                    insights.append(insight)
            
            # Insight 4: Growth opportunity analysis
            active_vaults = [(name, profile) for name, profile in self.vault_profiles.items() 
                           if profile.activity_level in ['high', 'medium']]
            
            if len(active_vaults) >= 2:
                insight = AIInsight(
                    insight_id=hashlib.md5(f"growth_{current_time}".encode()).hexdigest()[:12],
                    title="Knowledge Ecosystem Growth Potential",
                    description=f"Your {len(active_vaults)} active vaults show good growth potential for knowledge integration",
                    insight_type="opportunity",
                    confidence=0.7,
                    supporting_evidence=[f"{name} ({profile.activity_level} activity)" for name, profile in active_vaults],
                    actionable_recommendations=[
                        "Establish regular cross-vault content reviews",
                        "Create integrated knowledge workflows",
                        "Implement automated cross-referencing"
                    ],
                    affected_vaults=[name for name, _ in active_vaults],
                    generated_date=current_time,
                    priority="low"
                )
                insights.append(insight)
            
            self.ai_insights = insights
            self.logger.info(f"Generated {len(insights)} AI insights")
            
        except Exception as e:
            self.logger.error(f"Error generating AI insights: {e}")
    
    async def run_predictive_analysis(self):
        """Run predictive analysis for future trends and recommendations"""
        self.logger.info("Running predictive analysis")
        
        try:
            # Simple predictive analysis - could be expanded with ML models
            predictions = {}
            
            # Predict vault growth trends
            for vault_name, profile in self.vault_profiles.items():
                if profile.activity_level in ['high', 'medium']:
                    growth_score = min(1.0, profile.health_score * 1.2)
                    predictions[f"{vault_name}_growth"] = {
                        'prediction': 'positive_growth',
                        'confidence': growth_score,
                        'timeframe': '3_months'
                    }
            
            # Predict integration opportunities
            if len(self.tag_correlations) > 10:
                predictions['integration_opportunity'] = {
                    'prediction': 'high_integration_potential',
                    'confidence': 0.75,
                    'timeframe': '1_month'
                }
            
            # Store predictions for future analysis
            # This is simplified - in a full implementation, this would be more sophisticated
            
            self.logger.info(f"Generated {len(predictions)} predictive insights")
            
        except Exception as e:
            self.logger.error(f"Error in predictive analysis: {e}")
    
    def load_learning_data(self):
        """Load existing learning data from storage"""
        try:
            # Load vault profiles
            profiles_file = self.data_path / "vault_profiles.json"
            if profiles_file.exists():
                with open(profiles_file, 'r') as f:
                    data = json.load(f)
                    self.vault_profiles = {
                        name: VaultProfile(**profile) 
                        for name, profile in data.items()
                    }
            
            # Load correlations
            correlations_file = self.data_path / "tag_correlations.json"
            if correlations_file.exists():
                with open(correlations_file, 'r') as f:
                    data = json.load(f)
                    self.tag_correlations = [
                        TagCorrelation(**corr) for corr in data
                    ]
            
            # Load patterns
            patterns_file = self.data_path / "cross_vault_patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    self.cross_vault_patterns = [
                        CrossVaultPattern(**pattern) for pattern in data
                    ]
            
            # Load insights
            insights_file = self.data_path / "ai_insights.json"
            if insights_file.exists():
                with open(insights_file, 'r') as f:
                    data = json.load(f)
                    self.ai_insights = [
                        AIInsight(**insight) for insight in data
                    ]
            
            self.logger.info("Learning data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading learning data: {e}")
    
    async def save_learning_data_async(self):
        """Asynchronously save all learning data to storage"""
        try:
            # Save vault profiles
            profiles_file = self.data_path / "vault_profiles.json"
            with open(profiles_file, 'w') as f:
                json.dump({name: asdict(profile) for name, profile in self.vault_profiles.items()}, 
                         f, indent=2)
            
            # Save correlations
            correlations_file = self.data_path / "tag_correlations.json"
            with open(correlations_file, 'w') as f:
                json.dump([asdict(corr) for corr in self.tag_correlations], f, indent=2)
            
            # Save patterns
            patterns_file = self.data_path / "cross_vault_patterns.json"
            with open(patterns_file, 'w') as f:
                json.dump([asdict(pattern) for pattern in self.cross_vault_patterns], f, indent=2)
            
            # Save insights
            insights_file = self.data_path / "ai_insights.json"
            with open(insights_file, 'w') as f:
                json.dump([asdict(insight) for insight in self.ai_insights], f, indent=2)
            
            # Save analysis metrics
            metrics_file = self.data_path / "analysis_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(self.analysis_metrics, f, indent=2)
            
            self.logger.info("Learning data saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")
    
    def get_comprehensive_stats(self) -> Dict:
        """Get comprehensive Multi-Vault AI statistics"""
        return {
            'engine_info': {
                'version': '2.0.0',
                'analysis_depth': self.config['analysis_settings']['analysis_depth'],
                'total_analyses': self.analysis_metrics['total_analyses'],
                'last_analysis': self.analysis_metrics['last_full_analysis'],
                'avg_analysis_time': round(self.analysis_metrics['avg_analysis_time'], 2),
                'success_rate': self.analysis_metrics['success_rate']
            },
            'vault_ecosystem': {
                'total_vaults': len(self.vault_profiles),
                'vault_types': Counter(profile.type for profile in self.vault_profiles.values()),
                'activity_levels': Counter(profile.activity_level for profile in self.vault_profiles.values()),
                'avg_health_score': round(sum(p.health_score for p in self.vault_profiles.values()) / max(1, len(self.vault_profiles)), 3),
                'total_files': sum(profile.file_count for profile in self.vault_profiles.values()),
                'total_tags': sum(profile.tag_count for profile in self.vault_profiles.values()),
                'total_size_mb': round(sum(profile.size_mb for profile in self.vault_profiles.values()), 2)
            },
            'learning_metrics': {
                'tag_correlations_found': len(self.tag_correlations),
                'cross_vault_patterns': len(self.cross_vault_patterns),
                'pattern_types': Counter(pattern.pattern_type for pattern in self.cross_vault_patterns),
                'avg_pattern_confidence': round(sum(p.confidence for p in self.cross_vault_patterns) / max(1, len(self.cross_vault_patterns)), 3),
                'ai_insights_generated': len(self.ai_insights),
                'insight_priorities': Counter(insight.priority for insight in self.ai_insights)
            },
            'top_insights': [
                {
                    'title': insight.title,
                    'type': insight.insight_type,
                    'priority': insight.priority,
                    'confidence': insight.confidence
                }
                for insight in sorted(self.ai_insights, key=lambda x: x.confidence, reverse=True)[:5]
            ]
        }


# Main CLI integration functions
async def run_multi_vault_analysis(force_refresh: bool = False) -> Dict:
    """Run comprehensive multi-vault AI analysis"""
    engine = MultiVaultAI()
    return await engine.run_comprehensive_analysis(force_refresh)


async def get_vault_profiles() -> Dict[str, Dict]:
    """Get all vault profiles"""
    engine = MultiVaultAI()
    return {name: asdict(profile) for name, profile in engine.vault_profiles.items()}


async def get_ai_insights(insight_type: Optional[str] = None) -> List[Dict]:
    """Get AI-generated insights, optionally filtered by type"""
    engine = MultiVaultAI()
    insights = engine.ai_insights
    
    if insight_type:
        insights = [insight for insight in insights if insight.insight_type == insight_type]
    
    return [asdict(insight) for insight in insights]


async def get_cross_vault_patterns(pattern_type: Optional[str] = None) -> List[Dict]:
    """Get cross-vault patterns, optionally filtered by type"""
    engine = MultiVaultAI()
    patterns = engine.cross_vault_patterns
    
    if pattern_type:
        patterns = [pattern for pattern in patterns if pattern.pattern_type == pattern_type]
    
    return [asdict(pattern) for pattern in patterns]


def get_multi_vault_stats() -> Dict:
    """Get comprehensive Multi-Vault AI statistics"""
    engine = MultiVaultAI()
    return engine.get_comprehensive_stats()


async def analyze_vault_ecosystem() -> Dict:
    """Analyze the complete vault ecosystem"""
    engine = MultiVaultAI()
    
    # Run analysis if needed
    last_analysis = engine.analysis_metrics.get('last_full_analysis')
    if not last_analysis:
        await engine.run_comprehensive_analysis()
    
    return {
        'ecosystem_health': engine.get_comprehensive_stats(),
        'top_patterns': await get_cross_vault_patterns(),
        'key_insights': await get_ai_insights(),
        'vault_profiles': await get_vault_profiles()
    }
