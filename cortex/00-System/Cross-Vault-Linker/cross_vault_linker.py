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
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "00-Templates"))
from link_templates import LinkTemplates, LINK_INSERTION_CONFIG

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

class CrossVaultLinker:
    """Main cross-vault linking engine"""
    
    def __init__(self, hub_vault_path: str = "/Users/simonjanke/Projects/cortex"):
        self.hub_path = Path(hub_vault_path)
        self.linker_path = self.hub_path / "00-System" / "Cross-Vault-Linker"
        self.data_path = self.linker_path / "data"
        self.cache_path = self.linker_path / "cache"
        self.logs_path = self.linker_path / "logs"
        
        # Ensure directories exist
        for path in [self.data_path, self.cache_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Load AI learning data
        self.load_ai_data()
        
        # Initialize storage
        self.link_suggestions: List[LinkSuggestion] = []
        self.vault_connections: List[VaultConnection] = []
        self.tag_suggestions: List[SmartTagSuggestion] = []
        
        self.logger.info("Cross-Vault Linker initialized")
    
    def setup_logging(self):
        """Configure logging"""
        log_file = self.logs_path / "cross_vault_linker.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('CrossVaultLinker')
    
    def _read_file_safe(self, file_path: Path) -> str:
        """Safely read file content, return empty string if error"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    
    def analyze_link_quality(self, source_path: Path, target_path: Path, shared_tags: List[str]) -> Dict:
        """Analyze the quality and actionability of a potential link"""
        source_content = self._read_file_safe(source_path)
        target_content = self._read_file_safe(target_path)
        
        # Calculate semantic relevance based on content analysis
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
        import re
        
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
            terms.update(match.lower() for match in matches)
        
        return terms
    
    def _calculate_content_overlap(self, source_content: str, target_content: str) -> float:
        """Calculate content overlap percentage"""
        if not source_content or not target_content:
            return 0.0
        
        source_words = set(source_content.lower().split())
        target_words = set(target_content.lower().split())
        
        common_words = source_words.intersection(target_words)
        total_words = len(source_words.union(target_words))
        
        return len(common_words) / total_words if total_words > 0 else 0.0
    
    def _determine_link_purpose(self, source_content: str, target_content: str, shared_tags: List[str]) -> str:
        """Determine the purpose/type of the link"""
        source_lower = source_content.lower()
        target_lower = target_content.lower()
        
        # Check for specific patterns
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
        # Criteria for actionable links
        criteria_met = 0
        
        # High semantic relevance
        if semantic_relevance > 0.3:
            criteria_met += 2
        elif semantic_relevance > 0.15:
            criteria_met += 1
        
        # Quality shared tags
        quality_tags = [tag for tag in shared_tags if len(tag) > 3 and tag not in ['web', 'dev', 'test']]
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
    
    def generate_actionable_links(self, suggestions: List[LinkSuggestion]) -> int:
        """Generate actual link entries in files for actionable suggestions"""
        links_created = 0
        
        for suggestion in suggestions:
            if suggestion.is_actionable and suggestion.confidence >= 0.4:
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
        
        # Generate link entry based on purpose
        link_entry = self._generate_link_entry(suggestion)
        
        # Check if link already exists
        if suggestion.target_file in content:
            return False  # Link already exists
        
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
            except Exception:
                return False
        
        return False
    
    def _generate_link_entry(self, suggestion: LinkSuggestion) -> str:
        """Generate the actual link entry text using templates"""
        target_display = Path(suggestion.target_file).stem
        
        return LinkTemplates.format_link_entry(
            target_vault=suggestion.target_vault,
            target_file=suggestion.target_file,
            display_name=target_display,
            confidence=suggestion.confidence,
            purpose=suggestion.link_purpose
        )
    
    def _find_insertion_point(self, content: str, link_purpose: str) -> Optional[int]:
        """Find the best place to insert a link in the file"""
        lines = content.split('\n')
        
        # Use configured section markers
        link_section_patterns = LINK_INSERTION_CONFIG["section_markers"]
        
        for i, line in enumerate(lines):
            for pattern in link_section_patterns:
                if pattern in line:
                    # Insert after the header
                    return i + 1
        
        # If no link section exists, create one before the end
        for i in reversed(range(len(lines))):
            line = lines[i].strip()
            if line and not line.startswith('#'):
                # Insert after content, before tags/metadata
                if i + 1 < len(lines):
                    lines.insert(i + 1, '')
                    lines.insert(i + 2, '## Related Links')
                    return i + 3
                else:
                    return len(lines)
        
        return len(lines)
    
    def cleanup_old_summaries(self, keep_count: int = 3):
        """Remove old Cross-Vault Link Summary files, keeping only the most recent ones"""
        summaries_dir = self.hub_path / "02-Neural-Links" / "Summaries"
        if not summaries_dir.exists():
            return
        
        # Find all summary files
        summary_files = list(summaries_dir.glob("Cross-Vault Link Summary - *.md"))
        
        if len(summary_files) <= keep_count:
            return
        
        # Sort by modification time (newest first)
        summary_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Remove old files
        for old_file in summary_files[keep_count:]:
            try:
                old_file.unlink()
                self.logger.info(f"Removed old summary: {old_file.name}")
            except Exception as e:
                self.logger.warning(f"Could not remove {old_file.name}: {e}")
    
    def load_ai_data(self):
        """Load AI learning data from the learning engine"""
        try:
            ai_data_path = self.hub_path / "00-System" / "AI-Learning-Engine" / "data"
            
            # Load tag correlations
            correlations_file = ai_data_path / "tag_correlations.json"
            self.tag_correlations = []
            if correlations_file.exists():
                with open(correlations_file, 'r') as f:
                    data = json.load(f)
                    self.tag_correlations = data
            
            # Load vault profiles
            profiles_file = ai_data_path / "vault_profiles.json"
            self.vault_profiles = {}
            if profiles_file.exists():
                with open(profiles_file, 'r') as f:
                    self.vault_profiles = json.load(f)
            
            # Load cross-vault patterns
            patterns_file = ai_data_path / "cross_vault_patterns.json"
            self.cross_vault_patterns = []
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    self.cross_vault_patterns = json.load(f)
            
            self.logger.info("AI learning data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading AI data: {e}")
            # Initialize empty data if loading fails
            self.tag_correlations = []
            self.vault_profiles = {}
            self.cross_vault_patterns = []
    
    def discover_vaults(self) -> List[Path]:
        """Discover all available vaults"""
        vaults = []
        
        # Add hub vault
        if self.hub_path.exists():
            vaults.append(self.hub_path)
        
        # Look for project vaults
        parent_dir = self.hub_path.parent
        for item in parent_dir.iterdir():
            if item.is_dir() and item.name.startswith('project-'):
                if (item / '.obsidian').exists() or len(list(item.glob('*.md'))) > 0:
                    vaults.append(item)
        
        return vaults
    
    def extract_file_tags(self, file_path: Path) -> Set[str]:
        """Extract tags from a markdown file"""
        tags = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find hashtags
                found_tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
                tags.update(found_tags)
        except Exception as e:
            self.logger.warning(f"Error reading file {file_path}: {e}")
        
        return tags
    
    def calculate_file_similarity(self, file1_tags: Set[str], file2_tags: Set[str]) -> float:
        """Calculate similarity between two files based on shared tags"""
        if not file1_tags or not file2_tags:
            return 0.0
        
        # Jaccard similarity
        intersection = len(file1_tags & file2_tags)
        union = len(file1_tags | file2_tags)
        
        return intersection / union if union > 0 else 0.0
    
    def find_cross_vault_links(self, min_similarity: float = 0.3) -> List[LinkSuggestion]:
        """Find potential links between files in different vaults"""
        self.logger.info("Finding cross-vault links...")
        
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
                    'Cross-Vault Link Summary' in md_file.name or
                    '#auto-generated' in self._read_file_safe(md_file)):
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
                            source_full_path = list(vaults)[i] / file1_path
                            target_full_path = list(vaults)[j] / file2_path
                            
                            quality_analysis = self.analyze_link_quality(
                                source_full_path, target_full_path, shared_tags
                            )
                            
                            # Determine link strength with quality factors
                            base_confidence = similarity
                            semantic_bonus = quality_analysis['semantic_relevance'] * 0.3
                            final_confidence = min(0.95, base_confidence + semantic_bonus)
                            
                            if final_confidence >= 0.7:
                                link_type = 'strong'
                                confidence = final_confidence
                            elif final_confidence >= 0.5:
                                link_type = 'medium'
                                confidence = final_confidence
                            else:
                                link_type = 'weak'
                                confidence = final_confidence
                            
                            # Only keep actionable links or strong/medium links
                            if quality_analysis['is_actionable'] or link_type in ['strong', 'medium']:
                                # Create enhanced link suggestion
                                suggestion = LinkSuggestion(
                                    source_vault=vault1,
                                    source_file=file1_path,
                                    target_vault=vault2,
                                    target_file=file2_path,
                                    correlation_score=similarity,
                                    shared_tags=shared_tags,
                                    confidence=confidence,
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
        
        self.logger.info(f"Found {len(link_suggestions)} cross-vault link suggestions")
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
                            shared_tags=list(shared_tags),
                            common_files=common_files,
                            last_updated=datetime.now().isoformat()
                        )
                        
                        vault_connections.append(connection)
        
        # Sort by connection strength
        vault_connections.sort(key=lambda x: x.connection_strength, reverse=True)
        
        self.logger.info(f"Generated {len(vault_connections)} vault connections")
        return vault_connections
    
    def suggest_smart_tags(self, file_content: str, current_vault: str) -> List[SmartTagSuggestion]:
        """Suggest smart tags based on file content and cross-vault analysis"""
        suggestions = []
        
        try:
            # Extract current tags from content
            current_tags = set(re.findall(r'#([a-zA-Z0-9_-]+)', file_content))
            
            # Find related tags from correlations
            for correlation in self.tag_correlations:
                tag1 = correlation['tag1']
                tag2 = correlation['tag2']
                correlation_score = correlation['correlation_score']
                
                # If file has tag1, suggest tag2
                if tag1 in current_tags and tag2 not in current_tags:
                    suggestions.append(SmartTagSuggestion(
                        suggested_tag=tag2,
                        confidence=correlation_score,
                        reason=f"Often used with #{tag1} (correlation: {correlation_score})",
                        related_files=[],
                        vaults_using_tag=[]
                    ))
                # If file has tag2, suggest tag1
                elif tag2 in current_tags and tag1 not in current_tags:
                    suggestions.append(SmartTagSuggestion(
                        suggested_tag=tag1,
                        confidence=correlation_score,
                        reason=f"Often used with #{tag2} (correlation: {correlation_score})",
                        related_files=[],
                        vaults_using_tag=[]
                    ))
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x.confidence, reverse=True)
            
            # Keep only top suggestions
            suggestions = suggestions[:5]
            
        except Exception as e:
            self.logger.error(f"Error generating smart tag suggestions: {e}")
        
        return suggestions
    
    def generate_connection_files(self):
        """Generate connection files for each vault"""
        self.logger.info("Generating cross-vault connection files...")
        
        # Generate link suggestions
        self.link_suggestions = self.find_cross_vault_links()
        
        # Generate vault connections
        self.vault_connections = self.generate_vault_connections()
        
        # Group suggestions by source vault
        suggestions_by_vault = defaultdict(list)
        for suggestion in self.link_suggestions:
            suggestions_by_vault[suggestion.source_vault].append(suggestion)
        
        # Generate connection file for each vault
        vaults = self.discover_vaults()
        
        for vault_path in vaults:
            vault_name = vault_path.name
            
            # Skip hub vault for now
            if vault_name == 'cortex':
                continue
            
            # Create meta directory if it doesn't exist
            meta_dir = vault_path / "00-Meta"
            meta_dir.mkdir(exist_ok=True)
            
            # Generate connection file content
            connection_content = self.generate_connection_file_content(
                vault_name, 
                suggestions_by_vault.get(vault_name, [])
            )
            
            # Write connection file
            connection_file = meta_dir / "Cross-Vault-Links.md"
            with open(connection_file, 'w', encoding='utf-8') as f:
                f.write(connection_content)
            
            self.logger.info(f"Generated connection file for vault: {vault_name}")
    
    def generate_connection_file_content(self, vault_name: str, suggestions: List[LinkSuggestion]) -> str:
        """Generate content for a vault's connection file"""
        
        # Group suggestions by strength
        strong_links = [s for s in suggestions if s.link_type == 'strong']
        medium_links = [s for s in suggestions if s.link_type == 'medium']
        weak_links = [s for s in suggestions if s.link_type == 'weak']
        
        content = f"""# 🔗 Cross-Vault Connections for {vault_name}

*AI-discovered connections to other Cortex vaults*

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Total Connections Found:** {len(suggestions)}

## 🎯 **High Confidence Connections (>70%)**

"""
        
        if strong_links:
            for link in strong_links[:10]:  # Top 10 strong links
                content += f"""### 📄 {link.source_file}
**→ Related in `{link.target_vault}`:** {link.target_file}  
**Similarity:** {link.correlation_score:.1%} | **Confidence:** {link.confidence:.1%}  
**Shared Tags:** {', '.join([f'#{tag}' for tag in link.shared_tags])}  
**Reason:** {link.reason}

"""
        else:
            content += "*No high confidence connections found yet.*\n\n"
        
        content += f"""## 🔍 **Medium Confidence Connections (50-70%)**

"""
        
        if medium_links:
            for link in medium_links[:10]:  # Top 10 medium links
                content += f"""### 📄 {link.source_file}
**→ Related in `{link.target_vault}`:** {link.target_file}  
**Similarity:** {link.correlation_score:.1%} | **Tags:** {', '.join([f'#{tag}' for tag in link.shared_tags])}

"""
        else:
            content += "*No medium confidence connections found yet.*\n\n"
        
        content += f"""## 💡 **Potential Connections (30-50%)**

"""
        
        if weak_links:
            for link in weak_links[:5]:  # Top 5 weak links
                content += f"- **{link.target_vault}**/{link.target_file} ({link.correlation_score:.1%} similarity)\n"
        else:
            content += "*No potential connections found yet.*\n"
        
        # Add vault-level connections
        vault_connections = [c for c in self.vault_connections 
                           if c.vault1 == vault_name or c.vault2 == vault_name]
        
        if vault_connections:
            content += f"""

## 🌐 **Vault-Level Connections**

"""
            for conn in vault_connections:
                other_vault = conn.vault2 if conn.vault1 == vault_name else conn.vault1
                content += f"""### 🔗 Connection to `{other_vault}`
**Strength:** {conn.connection_strength:.1%}  
**Shared Tags:** {', '.join([f'#{tag}' for tag in conn.shared_tags[:10]])}  
**Common Topics:** {conn.common_files} files with shared tags

"""
        
        content += f"""

## 🏷️ **Tag Network Analysis**

*Based on your vault's tag usage patterns*

"""
        
        # Add tag analysis from AI data
        if hasattr(self, 'tag_correlations') and self.tag_correlations:
            content += "### 🔗 **Strong Tag Correlations**\n\n"
            
            for corr in self.tag_correlations[:5]:
                content += f"- **#{corr['tag1']}** ↔ **#{corr['tag2']}** "
                content += f"({corr['correlation_score']:.1%} correlation)\n"
        
        content += f"""

---

## 🤖 **How This Works**

This file is automatically generated by the Cortex AI Learning Engine based on:

- **Tag Correlation Analysis**: Finding files with similar tag patterns
- **Cross-Vault Pattern Detection**: Identifying common themes across projects  
- **Semantic Similarity**: Analyzing content and tag relationships
- **Usage Pattern Learning**: Learning from your organizational habits

**Next Actions:**
- Review high confidence connections and create manual links where relevant
- Consider adding suggested tags to improve AI learning
- Use connections to cross-reference knowledge between projects

*File automatically updated every 6 hours by Cortex AI*
"""
        
        return content
    
    def run_full_linking_cycle(self, sync_to_obsidian: bool = True):
        """Run complete cross-vault linking cycle with optional Obsidian sync"""
        self.logger.info("Starting rule-based cross-vault linking cycle")
        
        # Use adaptive rule-based linker with AI learning
        from .adaptive_rule_engine import AdaptiveRuleEngine
        adaptive_engine = AdaptiveRuleEngine(str(self.hub_path))
        
        try:
            # Run AI learning cycle first
            learning_results = adaptive_engine.run_learning_cycle()
            self.logger.info(f"AI learning: {learning_results.get('patterns_discovered', 0)} patterns, "
                           f"{learning_results.get('rules_optimized', 0)} optimizations")
            
            # Apply adaptive rules
            matches = adaptive_engine.apply_adaptive_rules()
            
            # Create links
            if matches:
                create_results = adaptive_engine.base_linker.create_links(matches)
                links_created = create_results.get('links_created', 0)
            else:
                links_created = 0
            
            # Convert to expected format
            linking_report = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_link_suggestions': len(matches),
                    'strong_links': links_created,
                    'medium_links': 0,
                    'weak_links': 0,
                    'vault_connections': 0
                },
                'success': True,
                'type': 'adaptive_ai_rules',
                'learning_results': learning_results
            }
            
            return linking_report
            
        except Exception as e:
            self.logger.error(f"Error in rule-based linking: {e}")
            return None
    
    async def sync_to_obsidian(self):
        """Sync cross-vault links and insights to Obsidian via MCP bridge"""
        try:
            from obsidian_mcp_bridge import integrate_with_obsidian
            
            # Prepare AI insights data
            ai_insights = []
            if hasattr(self, 'ai_data') and self.ai_data:
                for insight in self.ai_data.get('insights', []):
                    ai_insights.append({
                        'topic': insight.get('insight_type', 'Cross-Vault Pattern'),
                        'summary': insight.get('description', ''),
                        'findings': [insight.get('pattern', '')],
                        'related_concepts': insight.get('related_tags', []),
                        'cross_vault_connections': [],
                        'tags': ['cross-vault', 'ai-generated', 'linking'],
                        'source_vaults': insight.get('related_vaults', []),
                        'correlation_count': insight.get('strength', 0),
                        'confidence': insight.get('confidence', 0.5),
                        'pattern_types': ['cross-vault-linking']
                    })
            
            # Prepare cross-vault link data
            cross_vault_links = []
            for suggestion in self.link_suggestions:
                cross_vault_links.append({
                    'source_file': suggestion.source_file,
                    'target_file': suggestion.target_file,
                    'target_vault': suggestion.target_vault,
                    'confidence': suggestion.confidence,
                    'shared_tags': suggestion.shared_tags,
                    'reason': suggestion.reason,
                    'link_type': suggestion.link_type
                })
            
            # Execute sync
            sync_result = await integrate_with_obsidian(
                ai_insights=ai_insights,
                cross_vault_links=cross_vault_links,
                target_vault="cortex"
            )
            
            if sync_result.success:
                self.logger.info(f"Successfully synced to Obsidian: {sync_result.notes_created} notes, {sync_result.links_added} links")
            else:
                self.logger.warning(f"Obsidian sync completed with errors: {sync_result.errors}")
                
        except ImportError:
            self.logger.warning("Obsidian MCP bridge not available, skipping sync")
        except Exception as e:
            self.logger.error(f"Error syncing to Obsidian: {e}")
    
    async def run_full_linking_cycle_async(self, sync_to_obsidian: bool = True):
        """Async version of run_full_linking_cycle"""
        self.logger.info("Starting full cross-vault linking cycle (async)")
        
        try:
            # 0. Clean up old summary files first
            self.cleanup_old_summaries(keep_count=3)
            
            # 1. Load fresh AI data
            self.load_ai_data()
            
            # 2. Generate all connection files
            self.generate_connection_files()
            
            # 3. Generate actionable links in files
            # Show actionable link analysis
            actionable_count = len([s for s in self.link_suggestions if s.is_actionable])
            qualified_count = len([s for s in self.link_suggestions if s.is_actionable and s.confidence >= 0.4])
            self.logger.info(f"Link analysis: {actionable_count} actionable, {qualified_count} meet confidence threshold")
            
            links_created = self.generate_actionable_links(self.link_suggestions)
            self.logger.info(f"Generated {links_created} actionable links in files")
            
            # 4. Save linking data
            self.save_linking_data()
            
            # 5. Generate summary report
            report = self.generate_linking_report()
            report['links_created'] = links_created
            
            # 6. Sync to Obsidian if enabled
            if sync_to_obsidian:
                await self.sync_to_obsidian()
            
            self.logger.info("Cross-vault linking cycle completed successfully (async)")
            return report
            
        except Exception as e:
            self.logger.error(f"Error in async linking cycle: {e}")
            return None
    
    def save_linking_data(self):
        """Save linking data to storage"""
        try:
            # Save link suggestions
            suggestions_data = [asdict(s) for s in self.link_suggestions]
            with open(self.data_path / "link_suggestions.json", 'w') as f:
                json.dump(suggestions_data, f, indent=2, default=str)
            
            # Save vault connections
            connections_data = [asdict(c) for c in self.vault_connections]
            with open(self.data_path / "vault_connections.json", 'w') as f:
                json.dump(connections_data, f, indent=2, default=str)
            
            self.logger.info("Linking data saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving linking data: {e}")
    
    def generate_linking_report(self) -> Dict:
        """Generate comprehensive linking report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_link_suggestions': len(self.link_suggestions),
                'strong_links': len([s for s in self.link_suggestions if s.link_type == 'strong']),
                'medium_links': len([s for s in self.link_suggestions if s.link_type == 'medium']),
                'weak_links': len([s for s in self.link_suggestions if s.link_type == 'weak']),
                'vault_connections': len(self.vault_connections)
            },
            'top_suggestions': [
                asdict(s) for s in self.link_suggestions[:10]
            ],
            'vault_connections': [
                asdict(c) for c in self.vault_connections
            ]
        }
        
        # Save report
        report_file = self.logs_path / f"linking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report


def main():
    """Main entry point for testing the cross-vault linker"""
    linker = CrossVaultLinker()
    
    print("🔗 Cortex Cross-Vault Linker")
    print("Generating cross-vault connections...")
    
    report = linker.run_full_linking_cycle()
    
    if report:
        print(f"\n✅ Linking completed!")
        print(f"📊 Summary:")
        print(f"  - Total link suggestions: {report['summary']['total_link_suggestions']}")
        print(f"  - Strong links (>70%): {report['summary']['strong_links']}")
        print(f"  - Medium links (50-70%): {report['summary']['medium_links']}")
        print(f"  - Weak links (30-50%): {report['summary']['weak_links']}")
        print(f"  - Vault connections: {report['summary']['vault_connections']}")
        
        if report.get('links_created', 0) > 0:
            print(f"  - 🔗 Actionable links created: {report['links_created']}")
        else:
            print(f"  - 🔍 No actionable links created (quality threshold not met)")
        
        if report['top_suggestions']:
            print(f"\n🔗 Top Link Suggestions:")
            for suggestion in report['top_suggestions'][:5]:
                print(f"  - {suggestion['source_vault']}/{suggestion['source_file']}")
                print(f"    → {suggestion['target_vault']}/{suggestion['target_file']}")
                print(f"    Similarity: {suggestion['correlation_score']:.1%}, Tags: {', '.join(suggestion['shared_tags'])}")
    else:
        print("❌ Linking failed")


if __name__ == "__main__":
    main()
