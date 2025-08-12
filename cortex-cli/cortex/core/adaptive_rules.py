#!/usr/bin/env python3
"""
Adaptive Rule Learning Engine for Cortex CLI
AI-enhanced rule-based linking with continuous learning and optimization
"""

import json
import logging
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
# Import from existing CLI modules (will be added when needed)
# from ..linker.cross_vault_linker import CrossVaultLinker

@dataclass
class RuleMetrics:
    """Performance metrics for a single rule"""
    rule_name: str
    matches_generated: int = 0
    links_created: int = 0
    links_clicked: int = 0
    links_removed: int = 0
    user_feedback_score: float = 0.0
    success_rate: float = 0.0
    last_used: Optional[str] = None
    created: str = None

@dataclass
class LinkRule:
    """Enhanced rule for adaptive linking"""
    name: str
    description: str
    trigger: Dict
    target: Dict
    action: Dict
    strength: float = 1.0
    enabled: bool = True

@dataclass
class AdaptiveRule:
    """Rule with AI-learned modifications"""
    base_rule: LinkRule
    ai_modifications: Dict
    metrics: RuleMetrics
    confidence: float = 1.0
    enabled: bool = True

@dataclass
class PatternDiscovery:
    """Discovered pattern that could become a rule"""
    pattern_type: str  # 'tag_correlation', 'content_pattern', 'path_pattern'
    source_pattern: Dict
    target_pattern: Dict
    frequency: int
    strength: float
    example_files: List[Tuple[str, str]]
    confidence: float

class AdaptiveRuleEngine:
    """AI-enhanced rule engine that learns and evolves"""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        
        # AI learning paths
        self.learning_path = self.workspace_path / ".cortex" / "learning"
        self.learning_path.mkdir(parents=True, exist_ok=True)
        
        self.adaptive_rules_file = self.learning_path / "adaptive_rules.json"
        self.metrics_file = self.learning_path / "rule_metrics.json"
        self.patterns_file = self.learning_path / "discovered_patterns.json"
        self.user_feedback_file = self.learning_path / "user_feedback.json"
        
        # Setup logging
        self.logger = logging.getLogger('AdaptiveRuleEngine')
        
        # Load learning data
        self.adaptive_rules: Dict[str, AdaptiveRule] = {}
        self.rule_metrics: Dict[str, RuleMetrics] = {}
        self.discovered_patterns: List[PatternDiscovery] = []
        self.user_feedback_history: List[Dict] = []
        
        self.load_learning_data()
        
        # AI learning configuration
        self.learning_config = {
            'min_pattern_frequency': 3,
            'confidence_threshold': 0.7,
            'rule_optimization_interval_days': 7,
            'pattern_discovery_threshold': 0.6,
            'feedback_weight': 0.4,
            'usage_weight': 0.6,
            'auto_rule_generation': True,
            'max_new_rules_per_cycle': 5
        }
    
    def load_learning_data(self):
        """Load all AI learning data"""
        try:
            # Load adaptive rules
            if self.adaptive_rules_file.exists():
                with open(self.adaptive_rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for rule_name, rule_data in data.items():
                        base_rule = LinkRule(**rule_data['base_rule'])
                        metrics = RuleMetrics(**rule_data['metrics'])
                        self.adaptive_rules[rule_name] = AdaptiveRule(
                            base_rule=base_rule,
                            ai_modifications=rule_data['ai_modifications'],
                            metrics=metrics,
                            confidence=rule_data.get('confidence', 1.0),
                            enabled=rule_data.get('enabled', True)
                        )
            else:
                # Initialize from base rules
                self.initialize_adaptive_rules()
            
            # Load metrics
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    metrics_data = json.load(f)
                    for rule_name, metrics in metrics_data.items():
                        self.rule_metrics[rule_name] = RuleMetrics(**metrics)
            
            # Load discovered patterns
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                    self.discovered_patterns = [PatternDiscovery(**p) for p in patterns_data]
            
            # Load user feedback
            if self.user_feedback_file.exists():
                with open(self.user_feedback_file, 'r', encoding='utf-8') as f:
                    self.user_feedback_history = json.load(f)
            
            self.logger.info("Loaded %d adaptive rules, %d patterns", 
                           len(self.adaptive_rules), len(self.discovered_patterns))
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            self.logger.error("Error loading learning data: %s", e)
            self.initialize_adaptive_rules()
    
    def initialize_adaptive_rules(self):
        """Initialize adaptive rules from base rule set"""
        # Create some default rules
        default_rules = [
            LinkRule(
                name="tag_correlation",
                description="Link files with similar tags",
                trigger={"type": "tags", "min_match": 2},
                target={"type": "any"},
                action={"type": "suggest_link"},
                strength=0.8
            ),
            LinkRule(
                name="project_files",
                description="Link files within same project",
                trigger={"type": "path", "pattern": "*/Projects/*"},
                target={"type": "path", "pattern": "same_project"},
                action={"type": "auto_link"},
                strength=0.6
            )
        ]
        
        for rule in default_rules:
            metrics = RuleMetrics(
                rule_name=rule.name,
                created=datetime.now().isoformat()
            )
            
            adaptive_rule = AdaptiveRule(
                base_rule=rule,
                ai_modifications={
                    'strength_multiplier': 1.0,
                    'additional_triggers': [],
                    'additional_targets': [],
                    'learned_exclusions': []
                },
                metrics=metrics
            )
            
            self.adaptive_rules[rule.name] = adaptive_rule
    
    def save_learning_data(self):
        """Save all learning data"""
        try:
            # Save adaptive rules
            rules_data = {}
            for rule_name, adaptive_rule in self.adaptive_rules.items():
                rules_data[rule_name] = {
                    'base_rule': asdict(adaptive_rule.base_rule),
                    'ai_modifications': adaptive_rule.ai_modifications,
                    'metrics': asdict(adaptive_rule.metrics),
                    'confidence': adaptive_rule.confidence,
                    'enabled': adaptive_rule.enabled
                }
            
            with open(self.adaptive_rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2)
            
            # Save metrics
            metrics_data = {name: asdict(metrics) for name, metrics in self.rule_metrics.items()}
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2)
            
            # Save patterns
            patterns_data = [asdict(pattern) for pattern in self.discovered_patterns]
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2)
            
            # Save feedback
            with open(self.user_feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_feedback_history, f, indent=2)
                
        except (OSError, TypeError) as e:
            self.logger.error("Error saving learning data: %s", e)
    
    def discover_new_patterns(self, recent_links: List[Dict]) -> List[PatternDiscovery]:
        """Analyze recent successful links to discover patterns"""
        patterns = []
        
        # Group links by various criteria
        tag_correlations = defaultdict(list)
        # Note: path_patterns and content_patterns would be used for other pattern types
        # path_patterns = defaultdict(list)
        # content_patterns = defaultdict(list)
        
        for link in recent_links:
            source_file = link.get('source_file')
            target_file = link.get('target_file')
            
            if source_file and target_file:
                # Analyze tag correlations
                source_tags = link.get('source_tags', [])
                target_tags = link.get('target_tags', [])
                common_tags = set(source_tags) & set(target_tags)
                
                if len(common_tags) >= 2:
                    tag_key = tuple(sorted(common_tags))
                    tag_correlations[tag_key].append((source_file, target_file))
        
        # Create patterns from correlations
        for tag_combo, file_pairs in tag_correlations.items():
            if len(file_pairs) >= self.learning_config['min_pattern_frequency']:
                pattern = PatternDiscovery(
                    pattern_type='tag_correlation',
                    source_pattern={'tags': list(tag_combo)},
                    target_pattern={'tags': list(tag_combo)},
                    frequency=len(file_pairs),
                    strength=min(1.0, len(file_pairs) / 10),  # Normalize
                    example_files=file_pairs[:3],
                    confidence=min(0.9, len(file_pairs) / 5)
                )
                patterns.append(pattern)
        
        return patterns
    
    def optimize_existing_rules(self) -> int:
        """Optimize existing rules based on performance metrics"""
        optimizations = 0
        
        for adaptive_rule in self.adaptive_rules.values():
            metrics = adaptive_rule.metrics
            
            # Calculate success rate
            if metrics.matches_generated > 0:
                success_rate = metrics.links_created / metrics.matches_generated
                metrics.success_rate = success_rate
            
            # Adjust strength based on performance
            if metrics.success_rate < 0.3:
                # Poor performance - reduce strength
                adaptive_rule.ai_modifications['strength_multiplier'] *= 0.9
                optimizations += 1
            elif metrics.success_rate > 0.7:
                # Good performance - increase strength slightly
                adaptive_rule.ai_modifications['strength_multiplier'] = min(1.2, 
                    adaptive_rule.ai_modifications['strength_multiplier'] * 1.05)
                optimizations += 1
        
        return optimizations
    
    def generate_new_rules(self, patterns: List[PatternDiscovery]) -> List[LinkRule]:
        """Generate new rules from discovered patterns"""
        new_rules = []
        
        for pattern in patterns[:self.learning_config['max_new_rules_per_cycle']]:
            if pattern.pattern_type == 'tag_correlation':
                rule = LinkRule(
                    name=f"learned_tag_{len(new_rules)}",
                    description=f"AI-discovered tag correlation: {pattern.source_pattern['tags']}",
                    trigger=pattern.source_pattern,
                    target=pattern.target_pattern,
                    action={'type': 'suggest_link'},
                    strength=pattern.strength,
                    enabled=True
                )
                new_rules.append(rule)
                
                # Add to adaptive rules
                metrics = RuleMetrics(
                    rule_name=rule.name,
                    created=datetime.now().isoformat()
                )
                
                adaptive_rule = AdaptiveRule(
                    base_rule=rule,
                    ai_modifications={'strength_multiplier': 1.0},
                    metrics=metrics,
                    confidence=pattern.confidence
                )
                
                self.adaptive_rules[rule.name] = adaptive_rule
        
        return new_rules
    
    def record_user_feedback(self, link_id: str, feedback_type: str, rating: float = None):
        """Record user feedback on link suggestions"""
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'link_id': link_id,
            'feedback_type': feedback_type,  # 'accept', 'reject', 'rate'
            'rating': rating
        }
        
        self.user_feedback_history.append(feedback)
    
    def run_learning_cycle(self) -> Dict:
        """Run complete AI learning and optimization cycle"""
        start_time = datetime.now()
        self.logger.info("Starting adaptive rule learning cycle")
        
        results = {
            'timestamp': start_time.isoformat(),
            'patterns_discovered': 0,
            'rules_optimized': 0,
            'new_rules_generated': 0,
            'success': False
        }
        
        try:
            # 1. Discover new patterns from recent successful links
            recent_links = self.get_recent_successful_links()
            new_patterns = self.discover_new_patterns(recent_links)
            self.discovered_patterns.extend(new_patterns)
            results['patterns_discovered'] = len(new_patterns)
            
            # 2. Optimize existing rules
            optimizations = self.optimize_existing_rules()
            results['rules_optimized'] = optimizations
            
            # 3. Generate new rules from high-confidence patterns
            if self.learning_config['auto_rule_generation']:
                high_confidence_patterns = [p for p in new_patterns if p.confidence > 0.8]
                new_rules = self.generate_new_rules(high_confidence_patterns)
                results['new_rules_generated'] = len(new_rules)
            
            # 4. Save learning data
            self.save_learning_data()
            
            results['success'] = True
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info("Learning cycle completed in %.1fs", duration)
            
        except (ValueError, TypeError, OSError) as e:
            self.logger.error("Error in learning cycle: %s", e)
            results['error'] = str(e)
        
        return results
    
    def get_recent_successful_links(self) -> List[Dict]:
        """Get recent successful links for pattern analysis"""
        # This would integrate with actual link usage tracking
        # For now, return simulated data for testing
        return [
            {
                'source_file': 'project1/docs/readme.md',
                'target_file': 'project1/src/main.py',
                'source_tags': ['project1', 'documentation'],
                'target_tags': ['project1', 'code'],
                'created': datetime.now().isoformat()
            }
        ]
    
    def apply_adaptive_rules(self) -> List[Dict]:
        """Apply rules with AI modifications"""
        matches = []
        
        for rule_name, adaptive_rule in self.adaptive_rules.items():
            if not adaptive_rule.enabled:
                continue
            
            # Apply AI modifications to base rule
            modified_rule = self.apply_ai_modifications(adaptive_rule)
            
            # Simulate rule application (would integrate with actual linker)
            rule_matches = self.simulate_rule_application(modified_rule)
            matches.extend(rule_matches)
            
            # Record metrics
            if rule_name in self.rule_metrics:
                self.rule_metrics[rule_name].matches_generated += len(rule_matches)
                self.rule_metrics[rule_name].last_used = datetime.now().isoformat()
        
        return matches
    
    def apply_ai_modifications(self, adaptive_rule: AdaptiveRule) -> LinkRule:
        """Apply AI modifications to a base rule"""
        base = adaptive_rule.base_rule
        mods = adaptive_rule.ai_modifications
        
        # Apply strength multiplier
        modified_strength = base.strength * mods.get('strength_multiplier', 1.0)
        modified_strength = max(0.1, min(modified_strength, 1.0))  # Clamp
        
        # Apply additional triggers
        modified_trigger = base.trigger.copy()
        additional_triggers = mods.get('additional_triggers', [])
        if additional_triggers and 'tags' in modified_trigger:
            if 'tags' not in modified_trigger:
                modified_trigger['tags'] = []
            modified_trigger['tags'].extend(additional_triggers)
        
        # Create modified rule
        modified_rule = LinkRule(
            name=f"{base.name}_AI",
            description=f"{base.description} (AI-enhanced)",
            trigger=modified_trigger,
            target=base.target,
            action=base.action,
            strength=modified_strength,
            enabled=base.enabled
        )
        
        return modified_rule
    
    def simulate_rule_application(self, rule: LinkRule) -> List[Dict]:
        """Simulate rule application for testing"""
        # This would be replaced with actual rule application logic
        return [
            {
                'rule_name': rule.name,
                'source': 'example_source.md',
                'target': 'example_target.md',
                'strength': rule.strength,
                'confidence': 0.8
            }
        ]
    
    def get_learning_stats(self) -> Dict:
        """Get learning statistics"""
        return {
            'adaptive_rules': len(self.adaptive_rules),
            'active_rules': len([r for r in self.adaptive_rules.values() if r.enabled]),
            'discovered_patterns': len(self.discovered_patterns),
            'feedback_entries': len(self.user_feedback_history),
            'high_performance_rules': len([
                r for r in self.adaptive_rules.values() 
                if r.metrics.success_rate > 0.7
            ])
        }
