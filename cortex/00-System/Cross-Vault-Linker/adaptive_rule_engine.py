#!/usr/bin/env python3
"""
Adaptive Rule Learning Engine for Cortex
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
import numpy as np
from rule_based_linker import RuleBasedLinker, LinkRule, LinkMatch

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
    
    def __init__(self, cortex_path: str = None):
        self.cortex_path = Path(cortex_path) if cortex_path else Path.cwd()
        self.base_linker = RuleBasedLinker(cortex_path)
        
        # AI learning paths
        self.learning_path = self.cortex_path / "00-System" / "Cross-Vault-Linker" / "learning"
        self.learning_path.mkdir(exist_ok=True)
        
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
                with open(self.adaptive_rules_file, 'r') as f:
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
                with open(self.metrics_file, 'r') as f:
                    metrics_data = json.load(f)
                    for rule_name, metrics in metrics_data.items():
                        self.rule_metrics[rule_name] = RuleMetrics(**metrics)
            
            # Load discovered patterns
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                    self.discovered_patterns = [PatternDiscovery(**p) for p in patterns_data]
            
            # Load user feedback
            if self.user_feedback_file.exists():
                with open(self.user_feedback_file, 'r') as f:
                    self.user_feedback_history = json.load(f)
            
            self.logger.info(f"Loaded {len(self.adaptive_rules)} adaptive rules, {len(self.discovered_patterns)} patterns")
            
        except Exception as e:
            self.logger.error(f"Error loading learning data: {e}")
            self.initialize_adaptive_rules()
    
    def initialize_adaptive_rules(self):
        """Initialize adaptive rules from base rule set"""
        for rule in self.base_linker.rules:
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
            self.rule_metrics[rule.name] = metrics
    
    def save_learning_data(self):
        """Save all AI learning data"""
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
            
            with open(self.adaptive_rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2, default=str)
            
            # Save metrics
            metrics_data = {name: asdict(metrics) for name, metrics in self.rule_metrics.items()}
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            
            # Save patterns
            patterns_data = [asdict(pattern) for pattern in self.discovered_patterns]
            with open(self.patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2, default=str)
            
            # Save user feedback
            with open(self.user_feedback_file, 'w') as f:
                json.dump(self.user_feedback_history, f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")
    
    def discover_new_patterns(self, recent_links: List[Dict]) -> List[PatternDiscovery]:
        """Analyze recent successful links to discover new patterns"""
        discoveries = []
        
        # Group links by common characteristics
        tag_correlations = self.analyze_tag_correlations(recent_links)
        content_patterns = self.analyze_content_patterns(recent_links)
        path_patterns = self.analyze_path_patterns(recent_links)
        
        # Convert significant correlations to pattern discoveries
        min_frequency = self.learning_config['min_pattern_frequency']
        
        # Tag-based patterns
        for (source_tags, target_tags), frequency in tag_correlations.items():
            if frequency >= min_frequency:
                pattern = PatternDiscovery(
                    pattern_type='tag_correlation',
                    source_pattern={'tags': list(source_tags)},
                    target_pattern={'tags': list(target_tags)},
                    frequency=frequency,
                    strength=min(frequency / 10.0, 1.0),
                    example_files=self.get_pattern_examples(recent_links, source_tags, target_tags),
                    confidence=min(frequency / min_frequency * 0.2, 1.0)
                )
                discoveries.append(pattern)
        
        # Content-based patterns
        for (source_content, target_content), frequency in content_patterns.items():
            if frequency >= min_frequency:
                pattern = PatternDiscovery(
                    pattern_type='content_pattern',
                    source_pattern={'content_contains': [source_content]},
                    target_pattern={'content_contains': [target_content]},
                    frequency=frequency,
                    strength=min(frequency / 8.0, 1.0),
                    example_files=[],
                    confidence=min(frequency / min_frequency * 0.15, 1.0)
                )
                discoveries.append(pattern)
        
        self.logger.info(f"Discovered {len(discoveries)} new patterns")
        return discoveries
    
    def analyze_tag_correlations(self, links: List[Dict]) -> Counter:
        """Analyze tag correlations in successful links"""
        correlations = Counter()
        
        for link in links:
            source_tags = frozenset(link.get('source_tags', []))
            target_tags = frozenset(link.get('target_tags', []))
            
            if len(source_tags) > 0 and len(target_tags) > 0:
                correlations[(source_tags, target_tags)] += 1
        
        return correlations
    
    def analyze_content_patterns(self, links: List[Dict]) -> Counter:
        """Analyze content patterns in successful links"""
        patterns = Counter()
        
        # Common technical terms to look for
        tech_terms = [
            'fastapi', 'react', 'python', 'javascript', 'api', 'database',
            'testing', 'deployment', 'docker', 'kubernetes', 'typescript'
        ]
        
        for link in links:
            source_content = link.get('source_content', '').lower()
            target_content = link.get('target_content', '').lower()
            
            for term in tech_terms:
                if term in source_content and term in target_content:
                    patterns[(term, term)] += 1
        
        return patterns
    
    def analyze_path_patterns(self, links: List[Dict]) -> Counter:
        """Analyze path patterns in successful links"""
        patterns = Counter()
        
        for link in links:
            source_path = link.get('source_path', '')
            target_path = link.get('target_path', '')
            
            # Extract directory patterns
            source_parts = Path(source_path).parts[:-1] if source_path else []
            target_parts = Path(target_path).parts[:-1] if target_path else []
            
            if source_parts and target_parts:
                patterns[(tuple(source_parts), tuple(target_parts))] += 1
        
        return patterns
    
    def get_pattern_examples(self, links: List[Dict], source_tags: frozenset, target_tags: frozenset) -> List[Tuple[str, str]]:
        """Get example file pairs for a tag pattern"""
        examples = []
        
        for link in links:
            link_source_tags = set(link.get('source_tags', []))
            link_target_tags = set(link.get('target_tags', []))
            
            if source_tags.issubset(link_source_tags) and target_tags.issubset(link_target_tags):
                examples.append((link.get('source_path', ''), link.get('target_path', '')))
                if len(examples) >= 3:  # Limit examples
                    break
        
        return examples
    
    def optimize_existing_rules(self):
        """Optimize existing rules based on performance metrics"""
        optimizations_made = 0
        
        for rule_name, adaptive_rule in self.adaptive_rules.items():
            metrics = adaptive_rule.metrics
            
            if metrics.matches_generated < 5:  # Not enough data
                continue
            
            # Calculate success rate
            success_rate = metrics.links_clicked / max(metrics.links_created, 1)
            removal_rate = metrics.links_removed / max(metrics.links_created, 1)
            
            # Update rule based on performance
            if success_rate > 0.7 and removal_rate < 0.2:
                # High-performing rule - increase strength
                current_multiplier = adaptive_rule.ai_modifications.get('strength_multiplier', 1.0)
                new_multiplier = min(current_multiplier * 1.1, 2.0)
                adaptive_rule.ai_modifications['strength_multiplier'] = new_multiplier
                optimizations_made += 1
                
            elif success_rate < 0.3 or removal_rate > 0.5:
                # Poor-performing rule - decrease strength or disable
                current_multiplier = adaptive_rule.ai_modifications.get('strength_multiplier', 1.0)
                new_multiplier = max(current_multiplier * 0.9, 0.3)
                adaptive_rule.ai_modifications['strength_multiplier'] = new_multiplier
                
                if new_multiplier < 0.5:
                    adaptive_rule.enabled = False
                    self.logger.info(f"Disabled poor-performing rule: {rule_name}")
                
                optimizations_made += 1
            
            # Update metrics
            metrics.success_rate = success_rate
        
        self.logger.info(f"Optimized {optimizations_made} rules")
        return optimizations_made
    
    def generate_new_rules(self, patterns: List[PatternDiscovery]) -> List[AdaptiveRule]:
        """Generate new rules from discovered patterns"""
        new_rules = []
        max_new_rules = self.learning_config['max_new_rules_per_cycle']
        confidence_threshold = self.learning_config['confidence_threshold']
        
        # Sort patterns by confidence and frequency
        patterns.sort(key=lambda p: (p.confidence * p.frequency), reverse=True)
        
        for pattern in patterns[:max_new_rules]:
            if pattern.confidence < confidence_threshold:
                continue
            
            # Generate rule name
            rule_name = f"AI_Generated_{pattern.pattern_type}_{len(new_rules)+1}"
            
            # Create base rule from pattern
            base_rule = LinkRule(
                name=rule_name,
                description=f"AI-discovered {pattern.pattern_type} pattern",
                trigger=pattern.source_pattern,
                target=pattern.target_pattern,
                action="ai_generated",
                strength=pattern.strength,
                enabled=True
            )
            
            # Create adaptive rule
            metrics = RuleMetrics(
                rule_name=rule_name,
                created=datetime.now().isoformat()
            )
            
            adaptive_rule = AdaptiveRule(
                base_rule=base_rule,
                ai_modifications={
                    'strength_multiplier': 1.0,
                    'pattern_source': 'ai_discovered',
                    'discovery_confidence': pattern.confidence
                },
                metrics=metrics,
                confidence=pattern.confidence
            )
            
            new_rules.append(adaptive_rule)
            self.adaptive_rules[rule_name] = adaptive_rule
            self.rule_metrics[rule_name] = metrics
        
        if new_rules:
            self.logger.info(f"Generated {len(new_rules)} new AI rules")
        
        return new_rules
    
    def record_user_feedback(self, link_path: str, action: str, feedback_score: float = None):
        """Record user feedback on generated links"""
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'link_path': link_path,
            'action': action,  # 'clicked', 'removed', 'ignored'
            'feedback_score': feedback_score
        }
        
        self.user_feedback_history.append(feedback)
        
        # Update rule metrics based on feedback
        # This would need link-to-rule mapping
        
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
            self.logger.info(f"Learning cycle completed in {duration:.1f}s")
            
        except Exception as e:
            self.logger.error(f"Error in learning cycle: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_recent_successful_links(self) -> List[Dict]:
        """Get recent successful links for pattern analysis"""
        # This would integrate with actual link usage tracking
        # For now, return empty list - would need implementation
        return []
    
    def apply_adaptive_rules(self) -> List[LinkMatch]:
        """Apply rules with AI modifications"""
        # Update base linker rules with AI modifications
        modified_rules = []
        
        for rule_name, adaptive_rule in self.adaptive_rules.items():
            if not adaptive_rule.enabled:
                continue
            
            # Apply AI modifications to base rule
            modified_rule = self.apply_ai_modifications(adaptive_rule)
            modified_rules.append(modified_rule)
        
        # Temporarily replace base linker rules
        original_rules = self.base_linker.rules
        self.base_linker.rules = modified_rules
        
        try:
            # Run linking with modified rules
            matches = self.base_linker.apply_rules()
            
            # Record metrics
            self.record_rule_performance(matches)
            
            return matches
        finally:
            # Restore original rules
            self.base_linker.rules = original_rules
    
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
    
    def record_rule_performance(self, matches: List[LinkMatch]):
        """Record performance metrics for rules"""
        for match in matches:
            rule_name = match.rule_name.replace('_AI', '')  # Remove AI suffix
            if rule_name in self.rule_metrics:
                self.rule_metrics[rule_name].matches_generated += 1
                self.rule_metrics[rule_name].last_used = datetime.now().isoformat()


def main():
    """Test the adaptive rule engine"""
    cortex_path = "/Users/simonjanke/Projects/cortex"
    engine = AdaptiveRuleEngine(cortex_path)
    
    print("🧠 Adaptive Rule Learning Engine")
    print("Running AI-enhanced rule optimization...")
    
    # Run learning cycle
    learning_results = engine.run_learning_cycle()
    
    print(f"\n📊 Learning Results:")
    print(f"  - Patterns discovered: {learning_results['patterns_discovered']}")
    print(f"  - Rules optimized: {learning_results['rules_optimized']}")
    print(f"  - New rules generated: {learning_results['new_rules_generated']}")
    
    # Apply adaptive rules
    matches = engine.apply_adaptive_rules()
    
    print(f"\n🔗 Adaptive Linking Results:")
    print(f"  - Matches found: {len(matches)}")
    print(f"  - Active adaptive rules: {len([r for r in engine.adaptive_rules.values() if r.enabled])}")


if __name__ == "__main__":
    main()