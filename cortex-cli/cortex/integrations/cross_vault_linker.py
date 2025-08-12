#!/usr/bin/env python3
"""
Cross-Vault Linker - Intelligent linking system for multi-vault Cortex
Converts tag correlations into actionable cross-vault links and suggestions
"""

import os
import json
import re
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, Counter

@dataclass
class LinkSuggestion:
    """Represents a suggested link between vaults"""
    source_vault: str
    source_file: str
    target_vault: str
    target_file: str
    correlation_score: float
    shared_tags: List[str]
    confidence: float
    reason: str
    link_type: str  # 'strong', 'medium', 'weak'
    created_date: str
    semantic_relevance: float = 0.0
    content_overlap: float = 0.0
    is_actionable: bool = False
    link_purpose: str = ""  # 'reference', 'related-work', 'dependency', 'example'

@dataclass
class VaultConnection:
    """Represents a connection between two vaults"""
    vault1: str
    vault2: str
    connection_strength: float
    shared_tags: List[str]
    common_files: int
    last_updated: str

@dataclass
class SmartTagSuggestion:
    """Represents a smart tag suggestion based on context"""
    suggested_tag: str
    confidence: float
    reason: str
    related_files: List[str]
    vaults_using_tag: List[str]

@dataclass
class LinkingReport:
    """Comprehensive linking report"""
    timestamp: str
    total_suggestions: int
    strong_links: int
    medium_links: int
    weak_links: int
    vault_connections: int
    actionable_links: int
    links_created: int
    execution_time: float
    top_suggestions: List[LinkSuggestion]
    vault_stats: Dict[str, Any]

class CrossVaultLinker:
    """
    Cortex Cross-Vault Linking Engine
    
    Intelligently discovers and creates connections between files across different
    Obsidian vaults based on tag correlations, semantic analysis, and AI patterns.
    """
    
    def __init__(self, hub_vault_path: Optional[str] = None):
        """Initialize the cross-vault linker"""
        self.hub_path = Path(hub_vault_path or "/Users/simonjanke/Projects/cortex")
        self.linker_path = self.hub_path / "00-System" / "Cross-Vault-Linker"
        self.data_path = self.linker_path / "data"
        self.cache_path = self.linker_path / "cache"
        self.logs_path = self.linker_path / "logs"
        
        # Ensure directories exist
        for path in [self.data_path, self.cache_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize storage
        self.link_suggestions: List[LinkSuggestion] = []
        self.vault_connections: List[VaultConnection] = []
        self.tag_suggestions: List[SmartTagSuggestion] = []
        
        # Load AI learning data
        self.load_ai_data()
        
        self.logger.info("Cross-Vault Linker initialized")
    
    def setup_logging(self):
        """Configure logging"""
        log_file = self.logs_path / "cross_vault_linker.log"
        
        # Create logger if not exists
        self.logger = logging.getLogger('CrossVaultLinker')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            
            # File handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(levelname)s: %(message)s')
            )
            self.logger.addHandler(console_handler)
    
    def _read_file_safe(self, file_path: Path) -> str:
        """Safely read file content, return empty string if error"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.debug(f"Could not read file {file_path}: {e}")
            return ""
    
    def discover_vaults(self) -> List[Path]:
        """Discover all available vaults"""
        vaults = []
        
        # Add hub vault
        if self.hub_path.exists():
            vaults.append(self.hub_path)
        
        # Look for project vaults
        parent_dir = self.hub_path.parent
        if parent_dir.exists():
            for item in parent_dir.iterdir():
                if item.is_dir() and item.name.startswith('project-'):
                    if (item / '.obsidian').exists() or len(list(item.glob('*.md'))) > 0:
                        vaults.append(item)
        
        self.logger.info(f"Discovered {len(vaults)} vaults")
        return vaults
    
    def extract_file_tags(self, file_path: Path) -> Set[str]:
        """Extract tags from a markdown file"""
        tags = set()
        try:
            content = self._read_file_safe(file_path)
            if content:
                # Find hashtags
                found_tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
                tags.update(found_tags)
        except Exception as e:
            self.logger.warning(f"Error extracting tags from {file_path}: {e}")
        
        return tags
    
    def calculate_file_similarity(self, file1_tags: Set[str], file2_tags: Set[str]) -> float:
        """Calculate similarity between two files based on shared tags"""
        if not file1_tags or not file2_tags:
            return 0.0
        
        # Jaccard similarity coefficient
        intersection = len(file1_tags & file2_tags)
        union = len(file1_tags | file2_tags)
        
        return intersection / union if union > 0 else 0.0
    
    def analyze_link_quality(self, source_path: Path, target_path: Path, shared_tags: List[str]) -> Dict[str, Any]:
        """Analyze the quality and actionability of a potential link"""
        source_content = self._read_file_safe(source_path)
        target_content = self._read_file_safe(target_path)
        
        # Calculate semantic relevance
        semantic_relevance = self._calculate_semantic_relevance(source_content, target_content)
        
        # Calculate content overlap
        content_overlap = self._calculate_content_overlap(source_content, target_content)
        
        # Determine link purpose
        link_purpose = self._determine_link_purpose(source_content, target_content, shared_tags)
        
        # Check if link is actionable
        is_actionable = self._is_link_actionable(source_content, target_content, semantic_relevance, shared_tags)
        
        return {
            'semantic_relevance': semantic_relevance,
            'content_overlap': content_overlap,
            'link_purpose': link_purpose,
            'is_actionable': is_actionable
        }
    
    def _calculate_semantic_relevance(self, source_content: str, target_content: str) -> float:
        """Calculate semantic relevance between two documents"""
        if not source_content or not target_content:
            return 0.0
        
        # Extract key terms and concepts
        source_terms = self._extract_key_terms(source_content)
        target_terms = self._extract_key_terms(target_content)
        
        if not source_terms or not target_terms:
            return 0.0
        
        # Calculate overlap of key terms
        common_terms = source_terms.intersection(target_terms)
        total_terms = len(source_terms.union(target_terms))
        
        return len(common_terms) / total_terms if total_terms > 0 else 0.0
    
    def _extract_key_terms(self, content: str) -> Set[str]:
        """Extract key technical terms and concepts from content"""
        # Extract terms that are likely technical concepts
        patterns = [
            r'#\w+',  # Tags
            r'\b[A-Z][a-zA-Z]*(?:[A-Z][a-zA-Z]*)*\b',  # CamelCase terms
            r'\b\w+(?:[-_]\w+)+\b',  # Hyphenated/underscored terms
            r'\b(?:API|REST|HTTP|JSON|XML|SQL|NoSQL|Docker|React|Vue|Angular|Python|JavaScript|TypeScript)\b',  # Tech terms
        ]
        
        terms = set()
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            terms.update(match.lower() for match in matches if len(match) > 2)
        
        return terms
    
    def _calculate_content_overlap(self, source_content: str, target_content: str) -> float:
        """Calculate content overlap percentage"""
        if not source_content or not target_content:
            return 0.0
        
        # Use meaningful words (filter out common words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        
        source_words = set(word.lower() for word in source_content.split() if len(word) > 3 and word.lower() not in stop_words)
        target_words = set(word.lower() for word in target_content.split() if len(word) > 3 and word.lower() not in stop_words)
        
        if not source_words or not target_words:
            return 0.0
        
        common_words = source_words.intersection(target_words)
        total_words = len(source_words.union(target_words))
        
        return len(common_words) / total_words if total_words > 0 else 0.0
    
    def _determine_link_purpose(self, source_content: str, target_content: str, shared_tags: List[str]) -> str:
        """Determine the purpose/type of the link"""
        source_lower = source_content.lower()
        target_lower = target_content.lower()
        
        # Check for specific patterns in tags
        if any(tag in ['example', 'demo', 'tutorial'] for tag in shared_tags):
            return 'example'
        elif any(tag in ['dependency', 'requirement', 'prerequisite'] for tag in shared_tags):
            return 'dependency'
        elif 'related work' in source_lower or 'similar to' in source_lower:
            return 'related-work'
        elif any(keyword in source_lower for keyword in ['reference', 'see also', 'documentation']):
            return 'reference'
        else:
            return 'related-work'  # Default
    
    def _is_link_actionable(self, source_content: str, target_content: str, semantic_relevance: float, shared_tags: List[str]) -> bool:
        """Determine if a link is actionable (worth creating)"""
        criteria_met = 0
        
        # High semantic relevance
        if semantic_relevance > 0.3:
            criteria_met += 2
        elif semantic_relevance > 0.15:
            criteria_met += 1
        
        # Quality shared tags (avoid generic tags)
        quality_tags = [tag for tag in shared_tags if len(tag) > 3 and tag not in ['web', 'dev', 'test', 'todo']]
        if len(quality_tags) >= 3:
            criteria_met += 2
        elif len(quality_tags) >= 2:
            criteria_met += 1
        
        # Content indicators
        if any(keyword in source_content.lower() for keyword in ['see also', 'related to', 'similar', 'reference']):
            criteria_met += 1
        
        # File type compatibility
        if self._are_files_compatible(source_content, target_content):
            criteria_met += 1
        
        return criteria_met >= 3
    
    def _are_files_compatible(self, source_content: str, target_content: str) -> bool:
        """Check if files are compatible for linking"""
        # Both are projects
        if 'project' in source_content.lower() and 'project' in target_content.lower():
            return True
        # Both are documentation
        if any(keyword in source_content.lower() for keyword in ['# ', '## ', 'documentation']) and \
           any(keyword in target_content.lower() for keyword in ['# ', '## ', 'documentation']):
            return True
        # One is code, other is related doc
        if 'code' in source_content.lower() and 'documentation' in target_content.lower():
            return True
        return False
    
    def find_cross_vault_links(self, min_similarity: float = 0.3) -> List[LinkSuggestion]:
        """Find potential links between files in different vaults"""
        self.logger.info("Finding cross-vault links...")
        start_time = datetime.now()
        
        vaults = self.discover_vaults()
        link_suggestions = []
        
        # Collect all files with their tags from all vaults
        vault_files = {}
        for vault_path in vaults:
            vault_name = vault_path.name
            vault_files[vault_name] = {}
            
            for md_file in vault_path.glob('**/*.md'):
                # Skip system files and auto-generated content
                if ('00-System' in str(md_file) or 
                    '.obsidian' in str(md_file) or
                    'Cross-Vault Link Summary' in md_file.name):
                    continue
                
                # Skip if content contains auto-generated marker
                content = self._read_file_safe(md_file)
                if '#auto-generated' in content:
                    continue
                
                rel_path = str(md_file.relative_to(vault_path))
                tags = self.extract_file_tags(md_file)
                
                if tags:  # Only consider files with tags
                    vault_files[vault_name][rel_path] = tags
        
        # Compare files across different vaults
        vault_names = list(vault_files.keys())
        
        for i, vault1 in enumerate(vault_names):
            for j, vault2 in enumerate(vault_names):
                if i >= j:  # Avoid duplicates and self-comparison
                    continue
                
                # Compare all files between vault1 and vault2
                for file1_path, file1_tags in vault_files[vault1].items():
                    for file2_path, file2_tags in vault_files[vault2].items():
                        similarity = self.calculate_file_similarity(file1_tags, file2_tags)
                        
                        if similarity >= min_similarity:
                            shared_tags = list(file1_tags & file2_tags)
                            
                            # Perform deep link quality analysis
                            source_full_path = vaults[i] / file1_path
                            target_full_path = vaults[j] / file2_path
                            
                            quality_analysis = self.analyze_link_quality(
                                source_full_path, target_full_path, shared_tags
                            )
                            
                            # Determine link strength with quality factors
                            base_confidence = similarity
                            semantic_bonus = quality_analysis['semantic_relevance'] * 0.3
                            final_confidence = min(0.95, base_confidence + semantic_bonus)
                            
                            # Categorize link strength
                            if final_confidence >= 0.7:
                                link_type = 'strong'
                            elif final_confidence >= 0.5:
                                link_type = 'medium'
                            else:
                                link_type = 'weak'
                            
                            # Only keep actionable links or strong/medium links
                            if quality_analysis['is_actionable'] or link_type in ['strong', 'medium']:
                                suggestion = LinkSuggestion(
                                    source_vault=vault1,
                                    source_file=file1_path,
                                    target_vault=vault2,
                                    target_file=file2_path,
                                    correlation_score=similarity,
                                    shared_tags=shared_tags,
                                    confidence=final_confidence,
                                    reason=f"Shared tags: {', '.join([f'#{tag}' for tag in shared_tags])}",
                                    link_type=link_type,
                                    created_date=datetime.now().isoformat(),
                                    semantic_relevance=quality_analysis['semantic_relevance'],
                                    content_overlap=quality_analysis['content_overlap'],
                                    is_actionable=quality_analysis['is_actionable'],
                                    link_purpose=quality_analysis['link_purpose']
                                )
                                
                                link_suggestions.append(suggestion)
        
        # Sort by correlation score
        link_suggestions.sort(key=lambda x: x.correlation_score, reverse=True)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Found {len(link_suggestions)} cross-vault link suggestions in {execution_time:.2f}s")
        return link_suggestions
    
    def generate_vault_connections(self) -> List[VaultConnection]:
        """Generate high-level connections between vaults"""
        self.logger.info("Generating vault connections...")
        
        vaults = self.discover_vaults()
        vault_connections = []
        
        # Collect tag usage per vault
        vault_tags = {}
        vault_file_counts = {}
        
        for vault_path in vaults:
            vault_name = vault_path.name
            all_tags = defaultdict(int)
            file_count = 0
            
            for md_file in vault_path.glob('**/*.md'):
                if '00-System' in str(md_file) or '.obsidian' in str(md_file):
                    continue
                
                file_count += 1
                tags = self.extract_file_tags(md_file)
                for tag in tags:
                    all_tags[tag] += 1
            
            vault_tags[vault_name] = dict(all_tags)
            vault_file_counts[vault_name] = file_count
        
        # Calculate connections between vaults
        vault_names = list(vault_tags.keys())
        
        for i, vault1 in enumerate(vault_names):
            for j, vault2 in enumerate(vault_names):
                if i >= j:
                    continue
                
                tags1 = set(vault_tags[vault1].keys())
                tags2 = set(vault_tags[vault2].keys())
                
                shared_tags = tags1 & tags2
                if shared_tags:
                    # Calculate connection strength
                    total_tags = tags1 | tags2
                    connection_strength = len(shared_tags) / len(total_tags) if total_tags else 0
                    
                    # Count common files (files that share tags)
                    common_files = sum(
                        min(vault_tags[vault1].get(tag, 0), vault_tags[vault2].get(tag, 0))
                        for tag in shared_tags
                    )
                    
                    if connection_strength > 0.1:  # Only significant connections
                        connection = VaultConnection(
                            vault1=vault1,
                            vault2=vault2,
                            connection_strength=round(connection_strength, 3),
                            shared_tags=list(shared_tags)[:20],  # Limit for display
                            common_files=common_files,
                            last_updated=datetime.now().isoformat()
                        )
                        
                        vault_connections.append(connection)
        
        # Sort by connection strength
        vault_connections.sort(key=lambda x: x.connection_strength, reverse=True)
        
        self.logger.info(f"Generated {len(vault_connections)} vault connections")
        return vault_connections
    
    def generate_actionable_links(self, suggestions: List[LinkSuggestion]) -> int:
        """Generate actual link entries in files for actionable suggestions"""
        links_created = 0
        
        # Filter to actionable suggestions with sufficient confidence
        actionable_suggestions = [
            s for s in suggestions 
            if s.is_actionable and s.confidence >= 0.4
        ]
        
        self.logger.info(f"Processing {len(actionable_suggestions)} actionable link suggestions")
        
        for suggestion in actionable_suggestions:
            try:
                created = self._create_link_entry(suggestion)
                if created:
                    links_created += 1
                    self.logger.info(f"Created link: {suggestion.source_file} -> {suggestion.target_file}")
            except Exception as e:
                self.logger.warning(f"Failed to create link entry: {e}")
        
        return links_created
    
    def _create_link_entry(self, suggestion: LinkSuggestion) -> bool:
        """Create an actual link entry in the source file"""
        # Find the source file
        source_path = None
        for vault_path in self.discover_vaults():
            if vault_path.name == suggestion.source_vault:
                potential_path = vault_path / suggestion.source_file
                if potential_path.exists():
                    source_path = potential_path
                    break
        
        if not source_path:
            return False
        
        # Read the file content
        content = self._read_file_safe(source_path)
        if not content:
            return False
        
        # Check if link already exists (avoid duplicates)
        target_name = Path(suggestion.target_file).stem
        if target_name in content or suggestion.target_file in content:
            return False  # Link already exists
        
        # Generate link entry
        link_entry = self._generate_link_entry(suggestion)
        
        # Find insertion point
        insertion_point = self._find_insertion_point(content, suggestion.link_purpose)
        
        if insertion_point is not None:
            # Insert the link
            lines = content.split('\n')
            lines.insert(insertion_point, link_entry)
            
            # Write back to file
            try:
                with open(source_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                return True
            except Exception as e:
                self.logger.error(f"Failed to write link to {source_path}: {e}")
                return False
        
        return False
    
    def _generate_link_entry(self, suggestion: LinkSuggestion) -> str:
        """Generate the actual link entry text"""
        target_display = Path(suggestion.target_file).stem
        
        # Format based on purpose
        if suggestion.link_purpose == 'reference':
            return f"- **Reference**: [[{target_display}]] ({suggestion.target_vault}) - {suggestion.confidence:.1%} relevance"
        elif suggestion.link_purpose == 'example':
            return f"- **Example**: [[{target_display}]] ({suggestion.target_vault}) - See related example"
        elif suggestion.link_purpose == 'dependency':
            return f"- **Dependency**: [[{target_display}]] ({suggestion.target_vault}) - Required component"
        else:
            return f"- **Related**: [[{target_display}]] ({suggestion.target_vault}) - {', '.join(f'#{tag}' for tag in suggestion.shared_tags[:3])}"
    
    def _find_insertion_point(self, content: str, link_purpose: str) -> Optional[int]:
        """Find the best place to insert a link in the file"""
        lines = content.split('\n')
        
        # Look for existing link sections
        link_section_patterns = ['## Related', '## Links', '## See Also', '## References']
        
        for i, line in enumerate(lines):
            for pattern in link_section_patterns:
                if pattern.lower() in line.lower():
                    # Insert after the header
                    return i + 1
        
        # If no link section exists, create one near the end
        for i in reversed(range(len(lines))):
            line = lines[i].strip()
            if line and not line.startswith('#') and not line.startswith('---'):
                # Insert section header first
                if i + 1 < len(lines):
                    lines.insert(i + 1, '')
                    lines.insert(i + 2, '## Related Links')
                    return i + 3
                else:
                    lines.append('')
                    lines.append('## Related Links')
                    return len(lines)
        
        return len(lines)
    
    def load_ai_data(self):
        """Load AI learning data from the learning engine"""
        try:
            ai_data_path = self.hub_path / "00-System" / "AI-Learning-Engine" / "data"
            
            # Initialize empty data
            self.tag_correlations = []
            self.vault_profiles = {}
            self.cross_vault_patterns = []
            
            # Load tag correlations
            correlations_file = ai_data_path / "tag_correlations.json"
            if correlations_file.exists():
                with open(correlations_file, 'r', encoding='utf-8') as f:
                    self.tag_correlations = json.load(f)
            
            # Load vault profiles
            profiles_file = ai_data_path / "vault_profiles.json"
            if profiles_file.exists():
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    self.vault_profiles = json.load(f)
            
            # Load cross-vault patterns
            patterns_file = ai_data_path / "cross_vault_patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.cross_vault_patterns = json.load(f)
            
            self.logger.info("AI learning data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading AI data: {e}")
            # Ensure empty data structures exist
            self.tag_correlations = []
            self.vault_profiles = {}
            self.cross_vault_patterns = []
    
    def save_linking_data(self):
        """Save linking data to storage"""
        try:
            # Save link suggestions
            suggestions_data = [asdict(s) for s in self.link_suggestions]
            suggestions_file = self.data_path / "link_suggestions.json"
            with open(suggestions_file, 'w', encoding='utf-8') as f:
                json.dump(suggestions_data, f, indent=2, ensure_ascii=False)
            
            # Save vault connections
            connections_data = [asdict(c) for c in self.vault_connections]
            connections_file = self.data_path / "vault_connections.json"
            with open(connections_file, 'w', encoding='utf-8') as f:
                json.dump(connections_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Linking data saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving linking data: {e}")
    
    def generate_linking_report(self) -> LinkingReport:
        """Generate comprehensive linking report"""
        
        actionable_count = len([s for s in self.link_suggestions if s.is_actionable])
        
        # Get vault statistics
        vaults = self.discover_vaults()
        vault_stats = {}
        for vault in vaults:
            md_files = list(vault.glob('**/*.md'))
            vault_stats[vault.name] = {
                'total_files': len(md_files),
                'tagged_files': len([f for f in md_files if self.extract_file_tags(f)])
            }
        
        report = LinkingReport(
            timestamp=datetime.now().isoformat(),
            total_suggestions=len(self.link_suggestions),
            strong_links=len([s for s in self.link_suggestions if s.link_type == 'strong']),
            medium_links=len([s for s in self.link_suggestions if s.link_type == 'medium']),
            weak_links=len([s for s in self.link_suggestions if s.link_type == 'weak']),
            vault_connections=len(self.vault_connections),
            actionable_links=actionable_count,
            links_created=0,  # Will be updated by caller
            execution_time=0.0,  # Will be updated by caller
            top_suggestions=self.link_suggestions[:10],
            vault_stats=vault_stats
        )
        
        return report
    
    def run_linking_analysis(self, min_similarity: float = 0.3, create_links: bool = False) -> LinkingReport:
        """Run complete linking analysis cycle"""
        start_time = datetime.now()
        self.logger.info("Starting cross-vault linking analysis")
        
        try:
            # 1. Load fresh AI data
            self.load_ai_data()
            
            # 2. Find cross-vault links
            self.link_suggestions = self.find_cross_vault_links(min_similarity)
            
            # 3. Generate vault connections
            self.vault_connections = self.generate_vault_connections()
            
            # 4. Generate actionable links if requested
            links_created = 0
            if create_links:
                links_created = self.generate_actionable_links(self.link_suggestions)
            
            # 5. Save linking data
            self.save_linking_data()
            
            # 6. Generate report
            report = self.generate_linking_report()
            report.links_created = links_created
            report.execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Linking analysis completed in {report.execution_time:.2f}s")
            return report
            
        except Exception as e:
            self.logger.error(f"Error in linking analysis: {e}")
            # Return empty report on error
            return LinkingReport(
                timestamp=datetime.now().isoformat(),
                total_suggestions=0,
                strong_links=0,
                medium_links=0,
                weak_links=0,
                vault_connections=0,
                actionable_links=0,
                links_created=0,
                execution_time=(datetime.now() - start_time).total_seconds(),
                top_suggestions=[],
                vault_stats={}
            )
    
    def get_vault_statistics(self) -> Dict[str, Any]:
        """Get comprehensive vault statistics"""
        
        vaults = self.discover_vaults()
        stats = {
            'total_vaults': len(vaults),
            'vault_details': {},
            'tag_distribution': defaultdict(int),
            'total_files': 0,
            'total_tagged_files': 0
        }
        
        for vault in vaults:
            vault_name = vault.name
            md_files = list(vault.glob('**/*.md'))
            
            # Filter out system files
            content_files = [
                f for f in md_files 
                if '00-System' not in str(f) and '.obsidian' not in str(f)
            ]
            
            # Count tagged files and collect tags
            tagged_files = 0
            vault_tags = defaultdict(int)
            
            for file in content_files:
                tags = self.extract_file_tags(file)
                if tags:
                    tagged_files += 1
                    for tag in tags:
                        vault_tags[tag] += 1
                        stats['tag_distribution'][tag] += 1
            
            stats['vault_details'][vault_name] = {
                'path': str(vault),
                'total_files': len(content_files),
                'tagged_files': tagged_files,
                'unique_tags': len(vault_tags),
                'top_tags': dict(sorted(vault_tags.items(), key=lambda x: x[1], reverse=True)[:10])
            }
            
            stats['total_files'] += len(content_files)
            stats['total_tagged_files'] += tagged_files
        
        # Convert defaultdict to regular dict
        stats['tag_distribution'] = dict(stats['tag_distribution'])
        
        return stats

# Convenience functions for external usage
def run_cross_vault_analysis(hub_path: Optional[str] = None, min_similarity: float = 0.3, create_links: bool = False) -> Dict[str, Any]:
    """Run cross-vault linking analysis and return results"""
    
    linker = CrossVaultLinker(hub_path)
    report = linker.run_linking_analysis(min_similarity, create_links)
    
    return {
        'success': True,
        'report': asdict(report),
        'summary': {
            'total_suggestions': report.total_suggestions,
            'actionable_links': report.actionable_links,
            'vault_connections': report.vault_connections,
            'execution_time': report.execution_time
        }
    }

def get_linking_statistics(hub_path: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive linking statistics"""
    
    linker = CrossVaultLinker(hub_path)
    return linker.get_vault_statistics()

if __name__ == "__main__":
    # Test the cross-vault linker
    result = run_cross_vault_analysis()
    
    if result['success']:
        summary = result['summary']
        print("🔗 Cross-Vault Linking Analysis Complete")
        print(f"📊 Found {summary['total_suggestions']} link suggestions")
        print(f"🎯 {summary['actionable_links']} actionable links identified")
        print(f"🌐 {summary['vault_connections']} vault connections discovered")
        print(f"⏱️ Completed in {summary['execution_time']:.2f}s")
    else:
        print("❌ Cross-vault linking analysis failed")
