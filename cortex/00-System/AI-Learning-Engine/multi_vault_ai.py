#!/usr/bin/env python3
"""
Cortex Multi-Vault AI Learning Engine
Advanced tag correlation and cross-vault pattern detection system
"""

import os
import json
import yaml
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
import re
import hashlib

@dataclass
class TagCorrelation:
    """Represents a correlation between two tags"""
    tag1: str
    tag2: str
    correlation_score: float
    co_occurrence_count: int
    vault_count: int
    confidence: float
    last_updated: str
    
@dataclass
class VaultProfile:
    """Profile information for a vault"""
    name: str
    path: str
    type: str  # 'hub', 'project', 'archive'
    created: str
    last_analyzed: str
    file_count: int
    tag_count: int
    size_mb: float
    ai_learning_enabled: bool
    
@dataclass
class CrossVaultPattern:
    """Pattern detected across multiple vaults"""
    pattern_id: str
    name: str
    description: str
    vaults: List[str]
    confidence: float
    success_indicators: List[str]
    tags_involved: List[str]
    detected_date: str
    usage_count: int

class MultiVaultAILearningEngine:
    """Main AI learning engine for multi-vault Cortex system"""
    
    def __init__(self, hub_vault_path: str = "/Users/simonjanke/Projects/cortex"):
        self.hub_path = Path(hub_vault_path)
        self.engine_path = self.hub_path / "00-System" / "AI-Learning-Engine"
        self.data_path = self.engine_path / "data"
        self.cache_path = self.engine_path / "cache"
        self.logs_path = self.engine_path / "logs"
        
        # Ensure directories exist
        for path in [self.data_path, self.cache_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize data stores
        self.vault_profiles: Dict[str, VaultProfile] = {}
        self.tag_correlations: List[TagCorrelation] = []
        self.cross_vault_patterns: List[CrossVaultPattern] = []
        
        # Load existing data
        self.load_learning_data()
        
        self.logger.info("Multi-Vault AI Learning Engine initialized")
    
    def setup_logging(self):
        """Configure logging for the AI engine"""
        log_file = self.logs_path / "ai_learning.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('MultiVaultAIEngine')
    
    def load_config(self) -> Dict:
        """Load AI learning configuration"""
        config_file = self.engine_path / "ai_config.yaml"
        
        default_config = {
            'tag_correlation_threshold': 0.7,
            'pattern_detection_confidence': 0.85,
            'min_co_occurrence': 3,
            'vault_scan_interval_hours': 6,
            'max_vault_size_mb': 2048,
            'learning_cache_ttl_hours': 24,
            'cross_vault_analysis_enabled': True,
            'real_time_learning': True
        }
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        else:
            # Create default config
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
        
        return default_config
    
    def run_full_analysis(self):
        """Run complete analysis cycle on all vaults"""
        self.logger.info("Starting full multi-vault analysis")
        
        try:
            # 1. Discover and analyze all vaults
            vaults = self.discover_vaults()
            self.logger.info(f"Discovered {len(vaults)} vaults")
            
            for vault_path in vaults:
                self.analyze_vault(vault_path)
            
            # 2. Calculate tag correlations
            self.calculate_tag_correlations()
            
            # 3. Detect cross-vault patterns
            self.detect_cross_vault_patterns()
            
            # 4. Generate insights
            insights = self.generate_insights()
            
            # 5. Save all learning data
            self.save_learning_data()
            
            # 6. Generate summary report
            report = self.generate_analysis_report()
            
            self.logger.info("Full analysis completed successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"Error in full analysis: {e}")
            return None
    
    def discover_vaults(self) -> List[Path]:
        """Discover all vault directories, filtering out test/performance data"""
        vaults = []
        
        # Add hub vault
        if self.hub_path.exists():
            vaults.append(self.hub_path)
        
        # Look for project vaults in parent directory
        parent_dir = self.hub_path.parent
        for item in parent_dir.iterdir():
            if item.is_dir() and item.name.startswith('project-'):
                # Filter out test/performance vaults
                if self._is_test_vault(item.name):
                    self.logger.debug(f"Skipping test vault: {item.name}")
                    continue
                    
                # Check if it's a valid Obsidian vault
                if (item / '.obsidian').exists() or len(list(item.glob('*.md'))) > 0:
                    vaults.append(item)
        
        return vaults
    
    def analyze_vault(self, vault_path: Path) -> VaultProfile:
        """Analyze a single vault and create/update its profile"""
        try:
            vault_name = vault_path.name
            
            # Count files and calculate size
            md_files = list(vault_path.glob('**/*.md'))
            file_count = len(md_files)
            
            total_size = sum(f.stat().st_size for f in md_files if f.exists())
            size_mb = total_size / (1024 * 1024)
            
            # Extract and count tags, filtering out test/performance data
            all_tags = set()
            for md_file in md_files:
                try:
                    # Skip test/performance files
                    if self._is_test_file(md_file):
                        continue
                        
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Find hashtags
                        tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
                        # Filter out test tags
                        real_tags = [tag for tag in tags if not self._is_test_tag(tag)]
                        all_tags.update(real_tags)
                except Exception as e:
                    self.logger.warning(f"Error reading file {md_file}: {e}")
            
            # Determine vault type
            vault_type = 'hub' if vault_name == 'cortex' else 'project'
            
            # Create profile
            profile = VaultProfile(
                name=vault_name,
                path=str(vault_path),
                type=vault_type,
                created=datetime.now().isoformat() if vault_name not in self.vault_profiles else self.vault_profiles[vault_name].created,
                last_analyzed=datetime.now().isoformat(),
                file_count=file_count,
                tag_count=len(all_tags),
                size_mb=round(size_mb, 2),
                ai_learning_enabled=True
            )
            
            self.vault_profiles[vault_name] = profile
            self.logger.info(f"Analyzed vault '{vault_name}': {file_count} files, {len(all_tags)} unique tags")
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error analyzing vault {vault_path}: {e}")
            return None
    
    def calculate_tag_correlations(self):
        """Calculate correlations between tags across all vaults"""
        self.logger.info("Calculating tag correlations across vaults")
        
        try:
            # Collect tag co-occurrences across all vaults
            tag_cooccurrences = defaultdict(int)
            tag_vault_counts = defaultdict(set)
            tag_file_counts = defaultdict(int)
            
            vaults = self.discover_vaults()
            
            for vault_path in vaults:
                vault_name = vault_path.name
                md_files = list(vault_path.glob('**/*.md'))
                
                for md_file in md_files:
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            file_tags = set(re.findall(r'#([a-zA-Z0-9_-]+)', content))
                            
                            # Count individual tags
                            for tag in file_tags:
                                tag_file_counts[tag] += 1
                                tag_vault_counts[tag].add(vault_name)
                            
                            # Count tag co-occurrences in same file
                            for tag1 in file_tags:
                                for tag2 in file_tags:
                                    if tag1 < tag2:  # Avoid duplicates and self-correlation
                                        tag_cooccurrences[(tag1, tag2)] += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error processing file {md_file}: {e}")
            
            # Calculate correlation scores
            new_correlations = []
            min_co_occurrence = self.config['min_co_occurrence']
            
            for (tag1, tag2), co_count in tag_cooccurrences.items():
                if co_count >= min_co_occurrence:
                    # Calculate correlation score using Jaccard similarity
                    tag1_count = tag_file_counts[tag1]
                    tag2_count = tag_file_counts[tag2]
                    
                    # Jaccard similarity: intersection / union
                    union_count = tag1_count + tag2_count - co_count
                    correlation_score = co_count / union_count if union_count > 0 else 0
                    
                    # Calculate confidence based on vault diversity and frequency
                    vault_count = len(tag_vault_counts[tag1] & tag_vault_counts[tag2])
                    confidence = min(1.0, (co_count / 10) * (vault_count / max(len(vaults), 1)))
                    
                    correlation = TagCorrelation(
                        tag1=tag1,
                        tag2=tag2,
                        correlation_score=round(correlation_score, 3),
                        co_occurrence_count=co_count,
                        vault_count=vault_count,
                        confidence=round(confidence, 3),
                        last_updated=datetime.now().isoformat()
                    )
                    
                    new_correlations.append(correlation)
            
            # Filter by threshold and update
            threshold = self.config['tag_correlation_threshold']
            self.tag_correlations = [
                corr for corr in new_correlations 
                if corr.correlation_score >= threshold
            ]
            
            # Sort by correlation score
            self.tag_correlations.sort(key=lambda x: x.correlation_score, reverse=True)
            
            self.logger.info(f"Calculated {len(self.tag_correlations)} tag correlations above threshold {threshold}")
            
        except Exception as e:
            self.logger.error(f"Error calculating tag correlations: {e}")
    
    def detect_cross_vault_patterns(self):
        """Detect patterns that appear across multiple vaults"""
        self.logger.info("Detecting cross-vault patterns")
        
        try:
            vaults = self.discover_vaults()
            if len(vaults) < 2:
                self.logger.info("Need at least 2 vaults for cross-vault pattern detection")
                return
            
            detected_patterns = []
            
            # Pattern 1: Common directory structures
            common_structures = self.detect_directory_patterns(vaults)
            detected_patterns.extend(common_structures)
            
            # Pattern 2: Similar tag usage patterns
            tag_patterns = self.detect_tag_usage_patterns(vaults)
            detected_patterns.extend(tag_patterns)
            
            # Pattern 3: File naming conventions
            naming_patterns = self.detect_naming_patterns(vaults)
            detected_patterns.extend(naming_patterns)
            
            self.cross_vault_patterns = detected_patterns
            self.logger.info(f"Detected {len(detected_patterns)} cross-vault patterns")
            
        except Exception as e:
            self.logger.error(f"Error detecting cross-vault patterns: {e}")
    
    def detect_directory_patterns(self, vaults: List[Path]) -> List[CrossVaultPattern]:
        """Detect common directory structure patterns"""
        patterns = []
        
        # Collect directory structures from each vault
        vault_directories = {}
        for vault_path in vaults:
            directories = set()
            for item in vault_path.rglob('*'):
                if item.is_dir() and not item.name.startswith('.'):
                    rel_path = str(item.relative_to(vault_path))
                    directories.add(rel_path)
            vault_directories[vault_path.name] = directories
        
        # Find common directory patterns
        if len(vault_directories) >= 2:
            all_dirs = set()
            for dirs in vault_directories.values():
                all_dirs.update(dirs)
            
            for directory in all_dirs:
                vaults_with_dir = [
                    vault_name for vault_name, dirs in vault_directories.items()
                    if directory in dirs
                ]
                
                if len(vaults_with_dir) >= 2:
                    pattern_id = hashlib.md5(f"dir_{directory}".encode()).hexdigest()[:8]
                    pattern = CrossVaultPattern(
                        pattern_id=pattern_id,
                        name=f"Directory Structure: {directory}",
                        description=f"Common directory '{directory}' found in {len(vaults_with_dir)} vaults",
                        vaults=vaults_with_dir,
                        confidence=len(vaults_with_dir) / len(vault_directories),
                        success_indicators=["organized_structure", "consistent_workflow"],
                        tags_involved=[],
                        detected_date=datetime.now().isoformat(),
                        usage_count=len(vaults_with_dir)
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def detect_tag_usage_patterns(self, vaults: List[Path]) -> List[CrossVaultPattern]:
        """Detect common tag usage patterns"""
        patterns = []
        
        # Collect tag usage from each vault
        vault_tags = {}
        for vault_path in vaults:
            tags = defaultdict(int)
            for md_file in vault_path.glob('**/*.md'):
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
                        for tag in file_tags:
                            tags[tag] += 1
                except Exception:
                    pass
            vault_tags[vault_path.name] = dict(tags)
        
        # Find tags that appear in multiple vaults
        all_tags = set()
        for tags in vault_tags.values():
            all_tags.update(tags.keys())
        
        for tag in all_tags:
            vaults_with_tag = [
                vault_name for vault_name, tags in vault_tags.items()
                if tag in tags and tags[tag] >= 3  # Tag used at least 3 times
            ]
            
            if len(vaults_with_tag) >= 2:
                total_usage = sum(vault_tags[vault_name].get(tag, 0) for vault_name in vaults_with_tag)
                
                pattern_id = hashlib.md5(f"tag_{tag}".encode()).hexdigest()[:8]
                pattern = CrossVaultPattern(
                    pattern_id=pattern_id,
                    name=f"Tag Usage: #{tag}",
                    description=f"Tag #{tag} consistently used across {len(vaults_with_tag)} vaults ({total_usage} total uses)",
                    vaults=vaults_with_tag,
                    confidence=len(vaults_with_tag) / len(vault_tags),
                    success_indicators=["consistent_tagging", "knowledge_organization"],
                    tags_involved=[tag],
                    detected_date=datetime.now().isoformat(),
                    usage_count=total_usage
                )
                patterns.append(pattern)
        
        return patterns
    
    def detect_naming_patterns(self, vaults: List[Path]) -> List[CrossVaultPattern]:
        """Detect common file naming patterns"""
        patterns = []
        
        # Collect file naming patterns
        vault_naming_patterns = {}
        
        for vault_path in vaults:
            naming_patterns = defaultdict(int)
            for md_file in vault_path.glob('**/*.md'):
                # Extract naming pattern (prefix, structure)
                filename = md_file.stem
                
                # Check for common patterns
                if re.match(r'^\d{4}-\d{2}-\d{2}', filename):
                    naming_patterns['date_prefix'] += 1
                elif re.match(r'^ADR-\d{3}', filename):
                    naming_patterns['adr_format'] += 1
                elif re.match(r'^[A-Z]{2,}-\d{3}', filename):
                    naming_patterns['code_prefix'] += 1
                elif '-' in filename:
                    naming_patterns['dash_separated'] += 1
                elif '_' in filename:
                    naming_patterns['underscore_separated'] += 1
            
            vault_naming_patterns[vault_path.name] = dict(naming_patterns)
        
        # Find common naming patterns
        all_patterns = set()
        for patterns_dict in vault_naming_patterns.values():
            all_patterns.update(patterns_dict.keys())
        
        for pattern_name in all_patterns:
            vaults_with_pattern = [
                vault_name for vault_name, patterns_dict in vault_naming_patterns.items()
                if pattern_name in patterns_dict and patterns_dict[pattern_name] >= 2
            ]
            
            if len(vaults_with_pattern) >= 2:
                total_usage = sum(
                    vault_naming_patterns[vault_name].get(pattern_name, 0) 
                    for vault_name in vaults_with_pattern
                )
                
                pattern_id = hashlib.md5(f"naming_{pattern_name}".encode()).hexdigest()[:8]
                pattern = CrossVaultPattern(
                    pattern_id=pattern_id,
                    name=f"Naming Pattern: {pattern_name}",
                    description=f"Consistent {pattern_name} naming used in {len(vaults_with_pattern)} vaults",
                    vaults=vaults_with_pattern,
                    confidence=len(vaults_with_pattern) / len(vault_naming_patterns),
                    success_indicators=["consistent_naming", "organization"],
                    tags_involved=[],
                    detected_date=datetime.now().isoformat(),
                    usage_count=total_usage
                )
                patterns.append(pattern)
        
        return patterns
    
    def generate_insights(self) -> List[Dict]:
        """Generate actionable insights from learning data"""
        insights = []
        
        try:
            # Insight 1: Tag correlation insights
            if self.tag_correlations:
                top_correlations = self.tag_correlations[:5]
                insights.append({
                    'type': 'tag_correlation',
                    'title': 'Strong Tag Relationships Detected',
                    'description': f'Found {len(self.tag_correlations)} strong tag correlations',
                    'details': [
                        f"#{corr.tag1} ↔ #{corr.tag2} (score: {corr.correlation_score})"
                        for corr in top_correlations
                    ],
                    'actionable': 'Consider creating tag hierarchy or linking related concepts'
                })
            
            # Insight 2: Cross-vault pattern insights
            if self.cross_vault_patterns:
                patterns_by_type = defaultdict(list)
                for pattern in self.cross_vault_patterns:
                    if 'Directory' in pattern.name:
                        patterns_by_type['structure'].append(pattern)
                    elif 'Tag' in pattern.name:
                        patterns_by_type['tagging'].append(pattern)
                    elif 'Naming' in pattern.name:
                        patterns_by_type['naming'].append(pattern)
                
                for pattern_type, patterns in patterns_by_type.items():
                    insights.append({
                        'type': 'cross_vault_pattern',
                        'title': f'Consistent {pattern_type.title()} Patterns',
                        'description': f'Found {len(patterns)} consistent {pattern_type} patterns across vaults',
                        'details': [pattern.name for pattern in patterns[:3]],
                        'actionable': f'Document {pattern_type} standards for future projects'
                    })
            
            # Insight 3: Vault health insights
            if self.vault_profiles:
                total_files = sum(profile.file_count for profile in self.vault_profiles.values())
                total_tags = sum(profile.tag_count for profile in self.vault_profiles.values())
                avg_files_per_vault = total_files / len(self.vault_profiles)
                
                insights.append({
                    'type': 'vault_health',
                    'title': 'Vault Ecosystem Overview',
                    'description': f'{len(self.vault_profiles)} vaults with {total_files} total files',
                    'details': [
                        f"Average {avg_files_per_vault:.1f} files per vault",
                        f"Total {total_tags} unique tags across all vaults",
                        f"Active learning in {sum(1 for p in self.vault_profiles.values() if p.ai_learning_enabled)} vaults"
                    ],
                    'actionable': 'Monitor vault growth and maintain consistent organization'
                })
            
            self.logger.info(f"Generated {len(insights)} insights")
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return []
    
    def generate_analysis_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        insights = self.generate_insights()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'vaults_analyzed': len(self.vault_profiles),
                'tag_correlations_found': len(self.tag_correlations),
                'cross_vault_patterns': len(self.cross_vault_patterns),
                'insights_generated': len(insights)
            },
            'vault_profiles': {name: asdict(profile) for name, profile in self.vault_profiles.items()},
            'top_tag_correlations': [
                asdict(corr) for corr in self.tag_correlations[:10]
            ],
            'detected_patterns': [
                asdict(pattern) for pattern in self.cross_vault_patterns
            ],
            'insights': insights,
            'recommendations': self.generate_recommendations()
        }
        
        # Save report
        report_file = self.logs_path / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Recommendations based on correlations
        if len(self.tag_correlations) > 10:
            recommendations.append("Consider creating a tag taxonomy to organize the many tag relationships")
        elif len(self.tag_correlations) < 3:
            recommendations.append("Increase consistent tagging to enable better AI learning")
        
        # Recommendations based on patterns
        strong_patterns = [p for p in self.cross_vault_patterns if p.confidence > 0.8]
        if strong_patterns:
            recommendations.append("Document strong patterns as organizational standards for new projects")
        
        # Recommendations based on vault health
        large_vaults = [p for p in self.vault_profiles.values() if p.file_count > 100]
        if large_vaults:
            recommendations.append("Consider splitting large vaults or archiving old content")
        
        return recommendations
    
    def load_learning_data(self):
        """Load existing learning data from storage"""
        try:
            # Load vault profiles
            vault_profiles_file = self.data_path / "vault_profiles.json"
            if vault_profiles_file.exists():
                with open(vault_profiles_file, 'r') as f:
                    data = json.load(f)
                    self.vault_profiles = {
                        name: VaultProfile(**profile) 
                        for name, profile in data.items()
                    }
            
            # Load tag correlations
            correlations_file = self.data_path / "tag_correlations.json"
            if correlations_file.exists():
                with open(correlations_file, 'r') as f:
                    data = json.load(f)
                    self.tag_correlations = [
                        TagCorrelation(**corr) for corr in data
                    ]
            
            # Load cross-vault patterns
            patterns_file = self.data_path / "cross_vault_patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    self.cross_vault_patterns = [
                        CrossVaultPattern(**pattern) for pattern in data
                    ]
            
            self.logger.info("Learning data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading learning data: {e}")
    
    def save_learning_data(self):
        """Save learning data to storage"""
        try:
            # Save vault profiles
            vault_profiles_data = {
                name: asdict(profile) 
                for name, profile in self.vault_profiles.items()
            }
            with open(self.data_path / "vault_profiles.json", 'w') as f:
                json.dump(vault_profiles_data, f, indent=2, default=str)
            
            # Save tag correlations
            correlations_data = [asdict(corr) for corr in self.tag_correlations]
            with open(self.data_path / "tag_correlations.json", 'w') as f:
                json.dump(correlations_data, f, indent=2, default=str)
            
            # Save cross-vault patterns
            patterns_data = [asdict(pattern) for pattern in self.cross_vault_patterns]
            with open(self.data_path / "cross_vault_patterns.json", 'w') as f:
                json.dump(patterns_data, f, indent=2, default=str)
            
            self.logger.info("Learning data saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")
    
    def _is_test_vault(self, vault_name: str) -> bool:
        """Check if a vault name indicates test/performance data"""
        test_patterns = [
            'project-0',    # Performance test projects (project-001, project-002, etc.)
            'test-',        # Test vaults
            'temp-',        # Temporary vaults  
            'performance-', # Performance test vaults
            'benchmark-',   # Benchmark vaults
            'demo-'         # Demo vaults
        ]
        
        vault_lower = vault_name.lower()
        return any(vault_lower.startswith(pattern) for pattern in test_patterns)
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is from test/performance data"""
        file_name = file_path.name.lower()
        file_str = str(file_path).lower()
        
        test_patterns = [
            'category-',       # Performance test categories
            'file-',          # Performance test files
            'test-',          # Test files
            'performance-',   # Performance files
            'benchmark-',     # Benchmark files
            'cross-vault link summary'  # Auto-generated summaries
        ]
        
        return any(pattern in file_name or pattern in file_str for pattern in test_patterns)
    
    def _is_test_tag(self, tag: str) -> bool:
        """Check if a tag is from test/performance data"""
        test_tag_patterns = [
            'tag-0',          # Performance test tags (tag-001, tag-002, etc.)
            'test-',          # Test tags
            'performance-',   # Performance tags  
            'benchmark-',     # Benchmark tags
            'temp-',          # Temporary tags
            'fake-',          # Fake tags
            'generated-'      # Generated tags
        ]
        
        tag_lower = tag.lower()
        return any(tag_lower.startswith(pattern) for pattern in test_tag_patterns)


def main():
    """Main entry point for testing the AI learning engine"""
    engine = MultiVaultAILearningEngine()
    
    print("🧠 Cortex Multi-Vault AI Learning Engine")
    print("Starting analysis...")
    
    report = engine.run_full_analysis()
    
    if report:
        print(f"\n✅ Analysis completed!")
        print(f"📊 Summary:")
        print(f"  - Vaults analyzed: {report['summary']['vaults_analyzed']}")
        print(f"  - Tag correlations: {report['summary']['tag_correlations_found']}")
        print(f"  - Cross-vault patterns: {report['summary']['cross_vault_patterns']}")
        print(f"  - Insights generated: {report['summary']['insights_generated']}")
        
        if report['insights']:
            print(f"\n💡 Key Insights:")
            for insight in report['insights'][:3]:
                print(f"  - {insight['title']}: {insight['description']}")
    else:
        print("❌ Analysis failed")


if __name__ == "__main__":
    main()
