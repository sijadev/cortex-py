#!/usr/bin/env python3
"""
Rule-Based Cross-Vault Linker for Cortex
Predictable, maintainable linking based on defined rules instead of AI guessing
"""

import os
import re
import yaml
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import fnmatch

@dataclass
class LinkRule:
    """Represents a single linking rule"""
    name: str
    description: str
    trigger: Dict
    target: Dict
    action: str
    strength: float
    enabled: bool = True

@dataclass
class LinkMatch:
    """Represents a successful rule match"""
    rule_name: str
    source_file: Path
    target_file: Path
    strength: float
    action: str
    reason: str

class RuleBasedLinker:
    """Rule-based cross-vault linking engine"""
    
    def __init__(self, cortex_path: str = None):
        self.cortex_path = Path(cortex_path) if cortex_path else Path.cwd()
        self.rules_file = self.cortex_path / "00-System" / "Cross-Vault-Linker" / "link_rules.yaml"
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('RuleBasedLinker')
        
        # Load configuration
        self.rules: List[LinkRule] = []
        self.config = {}
        self.load_rules()
        
        # Cache for performance
        self.file_cache = {}
        self.tag_cache = {}
    
    def load_rules(self):
        """Load linking rules from YAML configuration"""
        try:
            if not self.rules_file.exists():
                self.logger.error(f"Rules file not found: {self.rules_file}")
                return
            
            with open(self.rules_file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Load rules
            for rule_data in data.get('link_rules', []):
                rule = LinkRule(
                    name=rule_data['name'],
                    description=rule_data.get('description', ''),
                    trigger=rule_data['trigger'],
                    target=rule_data['target'],
                    action=rule_data['action'],
                    strength=rule_data['strength'],
                    enabled=rule_data.get('enabled', True)
                )
                self.rules.append(rule)
            
            # Load configuration
            self.config = data.get('rule_config', {})
            self.validation_config = data.get('validation', {})
            
            self.logger.info(f"Loaded {len([r for r in self.rules if r.enabled])} active rules")
            
        except Exception as e:
            self.logger.error(f"Error loading rules: {e}")
    
    def discover_files(self) -> List[Path]:
        """Discover all markdown files in the cortex system"""
        md_files = []
        
        # Get exclusion patterns
        exclude_patterns = self.validation_config.get('exclude_patterns', [])
        
        for md_file in self.cortex_path.rglob('*.md'):
            # Check exclusions
            excluded = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(str(md_file), pattern):
                    excluded = True
                    break
            
            if not excluded:
                md_files.append(md_file)
        
        return md_files
    
    def extract_file_metadata(self, file_path: Path) -> Dict:
        """Extract metadata from a markdown file"""
        if str(file_path) in self.file_cache:
            return self.file_cache[str(file_path)]
        
        metadata = {
            'path': str(file_path),
            'relative_path': str(file_path.relative_to(self.cortex_path)),
            'filename': file_path.name,
            'content': '',
            'tags': set(),
            'size_kb': 0
        }
        
        try:
            # Check file size limit
            max_size_kb = self.config.get('max_file_size_kb', 1024)
            file_size_kb = file_path.stat().st_size / 1024
            
            if file_size_kb > max_size_kb:
                self.logger.warning(f"Skipping large file: {file_path} ({file_size_kb:.1f}KB)")
                return metadata
            
            metadata['size_kb'] = file_size_kb
            
            # Read content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                metadata['content'] = content.lower()  # For case-insensitive matching
                
                # Extract tags
                tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
                metadata['tags'] = set(tag.lower() for tag in tags)
        
        except Exception as e:
            self.logger.warning(f"Error reading file {file_path}: {e}")
        
        # Cache result
        self.file_cache[str(file_path)] = metadata
        return metadata
    
    def check_trigger_match(self, rule: LinkRule, file_metadata: Dict) -> bool:
        """Check if a file matches the trigger conditions of a rule"""
        trigger = rule.trigger
        
        # Check tags
        if 'tags' in trigger:
            required_tags = set(tag.lower() for tag in trigger['tags'])
            if not required_tags.intersection(file_metadata['tags']):
                return False
        
        # Check path patterns
        if 'path_pattern' in trigger:
            pattern = trigger['path_pattern']
            if not fnmatch.fnmatch(file_metadata['relative_path'], pattern):
                return False
        
        # Check filename
        if 'filename' in trigger:
            if trigger['filename'] != file_metadata['filename']:
                return False
        
        if 'filename_contains' in trigger:
            filename_lower = file_metadata['filename'].lower()
            required_strings = [s.lower() for s in trigger['filename_contains']]
            if not any(req_str in filename_lower for req_str in required_strings):
                return False
        
        if 'filename_pattern' in trigger:
            if not fnmatch.fnmatch(file_metadata['filename'], trigger['filename_pattern']):
                return False
        
        # Check content
        if 'content_contains' in trigger:
            required_content = [s.lower() for s in trigger['content_contains']]
            if not any(req_content in file_metadata['content'] for req_content in required_content):
                return False
        
        # Check path
        if 'path' in trigger:
            if trigger['path'] != file_metadata['relative_path']:
                return False
        
        return True
    
    def find_target_matches(self, rule: LinkRule, trigger_file: Dict, all_files: List[Dict]) -> List[Dict]:
        """Find files that match the target conditions of a rule"""
        target = rule.target
        matches = []
        
        for file_metadata in all_files:
            # Don't link to self
            if file_metadata['path'] == trigger_file['path']:
                continue
            
            # Check exclude_same_project
            if target.get('exclude_same_project', False):
                trigger_project = self.extract_project_name(trigger_file['relative_path'])
                target_project = self.extract_project_name(file_metadata['relative_path'])
                if trigger_project and trigger_project == target_project:
                    continue
            
            # Check target conditions
            match = True
            
            # Check tags
            if 'tags' in target:
                required_tags = set(tag.lower() for tag in target['tags'])
                if not required_tags.intersection(file_metadata['tags']):
                    match = False
            
            # Check path patterns
            if 'path_pattern' in target and match:
                pattern = target['path_pattern']
                if not fnmatch.fnmatch(file_metadata['relative_path'], pattern):
                    match = False
            
            # Check filename patterns
            if 'filename_pattern' in target and match:
                if not fnmatch.fnmatch(file_metadata['filename'], target['filename_pattern']):
                    match = False
            
            if 'filename_contains' in target and match:
                filename_lower = file_metadata['filename'].lower()
                required_strings = [s.lower() for s in target['filename_contains']]
                if not any(req_str in filename_lower for req_str in required_strings):
                    match = False
            
            # Check content
            if 'content_contains' in target and match:
                required_content = [s.lower() for s in target['content_contains']]
                if not any(req_content in file_metadata['content'] for req_content in required_content):
                    match = False
            
            # Check specific path
            if 'path' in target and match:
                if target['path'] != file_metadata['relative_path']:
                    match = False
            
            # Check content similarity threshold
            if 'content_similarity_threshold' in target and match:
                threshold = target['content_similarity_threshold']
                similarity = self.calculate_content_similarity(trigger_file, file_metadata)
                if similarity < threshold:
                    match = False
            
            if match:
                matches.append(file_metadata)
        
        return matches
    
    def extract_project_name(self, path: str) -> Optional[str]:
        """Extract project name from a path"""
        parts = Path(path).parts
        for i, part in enumerate(parts):
            if part == '01-Projects' and i + 1 < len(parts):
                return parts[i + 1]
        return None
    
    def calculate_content_similarity(self, file1: Dict, file2: Dict) -> float:
        """Calculate similarity between two files"""
        algorithm = self.config.get('content_similarity_algorithm', 'jaccard')
        
        if algorithm == 'jaccard':
            return self.jaccard_similarity(file1, file2)
        else:
            # Default to tag similarity
            return self.tag_similarity(file1, file2)
    
    def jaccard_similarity(self, file1: Dict, file2: Dict) -> float:
        """Calculate Jaccard similarity between two files"""
        # Combine tags and content words
        words1 = set(file1['content'].split()) | file1['tags']
        words2 = set(file2['content'].split()) | file2['tags']
        
        if not words1 and not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def tag_similarity(self, file1: Dict, file2: Dict) -> float:
        """Calculate tag-based similarity"""
        tags1 = file1['tags']
        tags2 = file2['tags']
        
        if not tags1 and not tags2:
            return 0.0
        
        intersection = len(tags1 & tags2)
        union = len(tags1 | tags2)
        
        return intersection / union if union > 0 else 0.0
    
    def apply_rules(self) -> List[LinkMatch]:
        """Apply all rules and generate link matches"""
        self.logger.info("Applying rule-based linking...")
        
        # Discover all files
        files = self.discover_files()
        self.logger.info(f"Processing {len(files)} files")
        
        # Extract metadata for all files
        all_metadata = []
        for file_path in files:
            metadata = self.extract_file_metadata(file_path)
            all_metadata.append(metadata)
        
        # Apply rules
        matches = []
        min_threshold = self.config.get('min_strength_threshold', 0.7)
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            rule_matches = 0
            
            for file_metadata in all_metadata:
                # Check if file triggers this rule
                if self.check_trigger_match(rule, file_metadata):
                    # Find target matches
                    targets = self.find_target_matches(rule, file_metadata, all_metadata)
                    
                    for target in targets:
                        # Calculate final strength
                        strength = self.calculate_link_strength(rule, file_metadata, target)
                        
                        if strength >= min_threshold:
                            match = LinkMatch(
                                rule_name=rule.name,
                                source_file=Path(file_metadata['path']),
                                target_file=Path(target['path']),
                                strength=strength,
                                action=rule.action,
                                reason=f"Rule: {rule.name} | Strength: {strength:.2f}"
                            )
                            matches.append(match)
                            rule_matches += 1
            
            if rule_matches > 0:
                self.logger.info(f"Rule '{rule.name}': {rule_matches} matches")
        
        # Remove duplicates and apply limits
        matches = self.filter_and_limit_matches(matches)
        
        self.logger.info(f"Generated {len(matches)} total link matches")
        return matches
    
    def calculate_link_strength(self, rule: LinkRule, source: Dict, target: Dict) -> float:
        """Calculate the final strength of a potential link"""
        base_strength = rule.strength
        
        # Apply weights from config
        tag_weight = self.config.get('tag_weight', 0.6)
        content_weight = self.config.get('content_weight', 0.3)
        path_weight = self.config.get('path_weight', 0.1)
        
        # Calculate component scores
        tag_score = self.tag_similarity(source, target)
        content_score = min(self.jaccard_similarity(source, target), 1.0)
        
        # Path similarity (same directory structure)
        source_parts = set(Path(source['relative_path']).parts[:-1])
        target_parts = set(Path(target['relative_path']).parts[:-1])
        path_score = len(source_parts & target_parts) / max(len(source_parts | target_parts), 1)
        
        # Weighted combination
        calculated_strength = (
            tag_score * tag_weight +
            content_score * content_weight +
            path_score * path_weight
        )
        
        # Combine with base rule strength
        final_strength = (base_strength + calculated_strength) / 2
        
        return min(final_strength, 1.0)
    
    def filter_and_limit_matches(self, matches: List[LinkMatch]) -> List[LinkMatch]:
        """Filter duplicates and apply limits"""
        # Group by source file
        by_source = defaultdict(list)
        for match in matches:
            by_source[str(match.source_file)].append(match)
        
        filtered_matches = []
        max_links = self.config.get('max_links_per_file', 10)
        
        for source_file, file_matches in by_source.items():
            # Sort by strength, take top N
            file_matches.sort(key=lambda x: x.strength, reverse=True)
            filtered_matches.extend(file_matches[:max_links])
        
        return filtered_matches
    
    def create_links(self, matches: List[LinkMatch]) -> Dict:
        """Create actual links in the markdown files"""
        results = {
            'links_created': 0,
            'files_modified': 0,
            'errors': []
        }
        
        # Group matches by source file and action
        by_source_action = defaultdict(lambda: defaultdict(list))
        for match in matches:
            by_source_action[str(match.source_file)][match.action].append(match)
        
        for source_file_str, actions in by_source_action.items():
            try:
                source_file = Path(source_file_str)
                if self.create_file_links(source_file, actions):
                    results['files_modified'] += 1
                    results['links_created'] += sum(len(matches) for matches in actions.values())
                    
            except Exception as e:
                error_msg = f"Error creating links for {source_file_str}: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
        
        return results
    
    def create_file_links(self, source_file: Path, actions: Dict[str, List[LinkMatch]]) -> bool:
        """Create links in a specific file"""
        try:
            # Read current content
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            section_names = self.config.get('section_names', {})
            auto_create_sections = self.config.get('auto_create_sections', True)
            
            # Process each action type
            for action, matches in actions.items():
                section_name = section_names.get(action, "Related Links")
                
                # Create links text
                links_text = []
                for match in matches:
                    rel_path = match.target_file.relative_to(self.cortex_path)
                    link_text = f"- [[{rel_path}]] - {match.reason}"
                    links_text.append(link_text)
                
                if links_text:
                    # Add or update section
                    content = self.add_links_to_section(content, section_name, links_text, auto_create_sections)
            
            # Write back if changed
            if content != original_content:
                with open(source_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating file {source_file}: {e}")
            return False
        
        return False
    
    def add_links_to_section(self, content: str, section_name: str, links: List[str], auto_create: bool = True) -> str:
        """Add links to a specific section in markdown content"""
        lines = content.split('\n')
        section_pattern = f"## {section_name}"
        section_found = False
        insert_index = -1
        
        # Find existing section
        for i, line in enumerate(lines):
            if line.strip() == section_pattern:
                section_found = True
                insert_index = i + 1
                break
        
        if not section_found and auto_create:
            # Add section at the end
            lines.extend([
                "",
                section_pattern,
                ""
            ])
            insert_index = len(lines)
        
        if insert_index >= 0:
            # Insert links
            for link in links:
                lines.insert(insert_index, link)
                insert_index += 1
        
        return '\n'.join(lines)
    
    def run_linking_cycle(self) -> Dict:
        """Run a complete rule-based linking cycle"""
        start_time = datetime.now()
        self.logger.info("Starting rule-based linking cycle")
        
        try:
            # Apply rules to find matches
            matches = self.apply_rules()
            
            # Create actual links
            results = self.create_links(matches)
            
            # Generate report
            duration = (datetime.now() - start_time).total_seconds()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'type': 'rule_based_linking',
                'duration_seconds': duration,
                'rules_applied': len([r for r in self.rules if r.enabled]),
                'matches_found': len(matches),
                'links_created': results['links_created'],
                'files_modified': results['files_modified'],
                'errors': results['errors'],
                'success': len(results['errors']) == 0
            }
            
            self.logger.info(f"Rule-based linking completed in {duration:.1f}s: {results['links_created']} links, {results['files_modified']} files")
            return report
            
        except Exception as e:
            error_msg = f"Error in linking cycle: {e}"
            self.logger.error(error_msg)
            return {
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': error_msg
            }


def main():
    """Test the rule-based linker"""
    cortex_path = "/Users/simonjanke/Projects/cortex"
    linker = RuleBasedLinker(cortex_path)
    
    print("🔗 Rule-Based Cross-Vault Linker")
    print("Generating predictable, maintainable links...")
    
    report = linker.run_linking_cycle()
    
    if report.get('success', False):
        print(f"\n✅ Linking completed!")
        print(f"📊 Results:")
        print(f"  - Rules applied: {report['rules_applied']}")
        print(f"  - Matches found: {report['matches_found']}")
        print(f"  - Links created: {report['links_created']}")
        print(f"  - Files modified: {report['files_modified']}")
        print(f"  - Duration: {report['duration_seconds']:.1f}s")
        
        if report.get('errors'):
            print(f"\n⚠️  Errors:")
            for error in report['errors']:
                print(f"  - {error}")
    else:
        print(f"❌ Linking failed: {report.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()