#!/usr/bin/env python3
"""
Rule-Based Cross-Vault Linker for Cortex.

Predictable, maintainable linking based on defined rules instead of AI guessing
"""
from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from .storage_provider import StorageProvider, MarkdownFSProvider
except ImportError:  # pragma: no cover - fallback for direct execution
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from storage_provider import StorageProvider, MarkdownFSProvider


@dataclass
class LinkRule:
    """Represents a single linking rule."""

    name: str
    description: str
    trigger: Dict
    target: Dict
    action: str
    strength: float
    enabled: bool = True


@dataclass
class LinkMatch:
    """Represents a successful rule match."""

    rule_name: str
    source_file: Path
    target_file: Path
    strength: float
    action: str
    reason: str


class RuleBasedLinker:
    """Rule-based cross-vault linking engine."""

    def __init__(
        self,
        cortex_path: Path,
        storage_provider: StorageProvider = None
    ):
        self.cortex_path = Path(cortex_path)
        self.rules_file = (
            self.cortex_path
            / "00-System"
            / "Cross-Vault-Linker"
            / "link_rules.yaml"
        )

        # Storage provider for IO operations
        self.storage = storage_provider or MarkdownFSProvider(self.cortex_path)

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("RuleBasedLinker")

        # Load configuration
        self.rules: List[LinkRule] = []
        self.config = {}
        self.load_rules()

        # Cache for performance
        self.file_cache = {}
        self.tag_cache = {}

    def load_rules(self):
        """Load linking rules from configuration."""
        try:
            if self.rules_file.exists():
                self.storage.read_text(self.rules_file)
                # Simple YAML-like parsing for demo - use yaml.safe_load
                self.logger.info("Loaded rules from %s", self.rules_file)
            else:
                self.logger.warning("No rules file found, creating default")
                self.create_default_rules()
        except Exception as e:
            self.logger.error("Error loading rules: %s", e)
            self.create_default_rules()

    def create_default_rules(self):
        """Create default linking rules."""
        default_rules = [
            LinkRule(
                name="project_to_decisions",
                description="Link project files to related decisions",
                trigger={"path_pattern": "01-Projects/**/*.md"},
                target={"path_pattern": "03-Decisions/ADR-*.md"},
                action="link_related",
                strength=0.8
            ),
            LinkRule(
                name="decision_to_code",
                description="Link decisions to code fragments",
                trigger={"path_pattern": "03-Decisions/*.md"},
                target={"path_pattern": "04-Code-Fragments/**/*.md"},
                action="link_implementation",
                strength=0.7
            ),
            LinkRule(
                name="neural_link_to_insights",
                description="Link AI sessions to generated insights",
                trigger={"path_pattern": "02-Neural-Links/*.md"},
                target={"path_pattern": "05-Insights/*.md"},
                action="link_insights",
                strength=0.9
            )
        ]

        self.rules = default_rules
        self.save_rules()

    def save_rules(self):
        """Save rules to configuration file."""
        try:
            self.rules_file.parent.mkdir(parents=True, exist_ok=True)
            # Simple YAML dump for demo - use yaml.safe_dump in production
            rule_yaml = "# Rule-based linker configuration\n"
            self.storage.write_text(self.rules_file, rule_yaml)
        except Exception as e:
            self.logger.error("Error saving rules: %s", e)

    def find_files_matching_pattern(self, pattern: str) -> List[Path]:
        """Find files matching a glob pattern."""
        try:
            return self.storage.list_files(pattern)
        except Exception as e:
            self.logger.error(
                "Error finding files with pattern %s: %s", pattern, e
            )
            return []

    def extract_tags_from_file(self, file_path: Path) -> List[str]:
        """Extract tags from markdown file."""
        if str(file_path) in self.tag_cache:
            return self.tag_cache[str(file_path)]

        tags = []
        try:
            content = self.storage.read_text(file_path)
            hashtags = re.findall(r'#([a-zA-Z0-9-_/]+)', content)
            tags.extend(hashtags)
            self.tag_cache[str(file_path)] = tags
        except Exception as e:
            self.logger.error(
                "Error extracting tags from %s: %s", file_path, e
            )

        return tags

    def files_share_tags(
        self, file1: Path, file2: Path, min_shared: int = 1
    ) -> bool:
        """Check if two files share at least min_shared tags."""
        tags1 = set(self.extract_tags_from_file(file1))
        tags2 = set(self.extract_tags_from_file(file2))
        shared = tags1.intersection(tags2)
        return len(shared) >= min_shared

    def apply_rule(self, rule: LinkRule) -> List[LinkMatch]:
        """Apply a single rule and find matches."""
        matches = []

        if not rule.enabled:
            return matches

        try:
            trigger_pattern = rule.trigger.get('path_pattern', '')
            trigger_files = self.find_files_matching_pattern(trigger_pattern)

            target_pattern = rule.target.get('path_pattern', '')
            target_files = self.find_files_matching_pattern(target_pattern)

            for source_file in trigger_files:
                for target_file in target_files:
                    if source_file == target_file:
                        continue

                    if self.should_link_files(source_file, target_file, rule):
                        match = LinkMatch(
                            rule_name=rule.name,
                            source_file=source_file,
                            target_file=target_file,
                            strength=rule.strength,
                            action=rule.action,
                            reason=f"Rule '{rule.name}': {rule.description}"
                        )
                        matches.append(match)

        except Exception as e:
            self.logger.error("Error applying rule %s: %s", rule.name, e)

        return matches

    def should_link_files(
        self, source: Path, target: Path, rule: LinkRule
    ) -> bool:
        """Determine if two files should be linked based on rule criteria."""
        try:
            if not source.exists() or not target.exists():
                return False

            if self.files_share_tags(source, target):
                return True

            if self.files_have_similar_names(source, target):
                return True

            if self.files_have_content_relationship(source, target):
                return True

        except Exception as e:
            self.logger.error(
                "Error checking if files should be linked: %s", e
            )

        return False

    def files_have_similar_names(self, file1: Path, file2: Path) -> bool:
        """Check if files have similar names (basic implementation)."""
        name1 = file1.stem.lower()
        name2 = file2.stem.lower()

        # Remove common prefixes/suffixes
        prefixes = ['adr-', 'project-', 'insight-', 'session-']
        suffixes = ['-workspace', '-analysis', '-report']

        for prefix in prefixes:
            name1 = name1.removeprefix(prefix)
            name2 = name2.removeprefix(prefix)

        for suffix in suffixes:
            name1 = name1.removesuffix(suffix)
            name2 = name2.removesuffix(suffix)

        return name1 in name2 or name2 in name1

    def files_have_content_relationship(
        self, source: Path, target: Path
    ) -> bool:
        """Check if files have content relationships."""
        try:
            source_content = self.storage.read_text(source).lower()
            target_content = self.storage.read_text(target).lower()

            source_name = source.stem.lower()
            target_name = target.stem.lower()

            if source_name in target_content or target_name in source_content:
                return True

            source_words = set(re.findall(r'\w+', source_content))
            target_words = set(re.findall(r'\w+', target_content))

            # Filter out common words
            common_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at',
                'to', 'for', 'of', 'with', 'by'
            }
            source_words -= common_words
            target_words -= common_words

            shared_words = source_words.intersection(target_words)
            return len(shared_words) >= 3

        except Exception as e:
            self.logger.error("Error checking content relationship: %s", e)
            return False

    def apply_rules(self) -> List[LinkMatch]:
        """Apply all enabled rules and collect matches."""
        all_matches = []

        for rule in self.rules:
            if rule.enabled:
                matches = self.apply_rule(rule)
                all_matches.extend(matches)
                self.logger.info(
                    "Rule '%s' found %d matches", rule.name, len(matches)
                )

        return all_matches

    def create_links(self, matches: List[LinkMatch]) -> Dict:
        """Create actual links from matches."""
        results = {
            'links_created': 0,
            'files_modified': 0,
            'errors': []
        }

        matches_by_source = defaultdict(list)
        for match in matches:
            matches_by_source[match.source_file].append(match)

        for source_file, file_matches in matches_by_source.items():
            try:
                if self.update_file_with_links(source_file, file_matches):
                    results['files_modified'] += 1
                    results['links_created'] += len(file_matches)
            except Exception as e:
                error_msg = f"Error updating {source_file}: {e}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)

        return results

    def update_file_with_links(
        self, source_file: Path, matches: List[LinkMatch]
    ) -> bool:
        """Update a file with new links."""
        try:
            original_content = self.storage.read_text(source_file)
            content = original_content

            actions = defaultdict(list)
            for match in matches:
                actions[match.action].append(match)

            section_names = {
                'link_related': 'Related Files',
                'link_implementation': 'Implementation',
                'link_insights': 'Generated Insights',
                'link_decisions': 'Related Decisions'
            }

            auto_create_sections = self.config.get(
                'auto_create_sections', True
            )

            for action, action_matches in actions.items():
                section_name = section_names.get(action, "Related Links")

                links_text = []
                for match in action_matches:
                    rel_path = match.target_file.relative_to(self.cortex_path)
                    link_text = f"- [[{rel_path}]] - {match.reason}"
                    links_text.append(link_text)

                if links_text:
                    content = self.add_links_to_section(
                        content, section_name, links_text, auto_create_sections
                    )

            if content != original_content:
                self.storage.write_text(source_file, content)
                return True

        except Exception as e:
            self.logger.error("Error updating file %s: %s", source_file, e)
            return False

        return False

    def add_links_to_section(
        self,
        content: str,
        section_name: str,
        links: List[str],
        auto_create: bool = True
    ) -> str:
        """Add links to a specific section in markdown content."""
        lines = content.split('\n')
        section_pattern = f"## {section_name}"
        section_found = False
        insert_index = -1

        for i, line in enumerate(lines):
            if line.strip() == section_pattern:
                section_found = True
                insert_index = i + 1
                break

        if not section_found and auto_create:
            lines.extend(["", section_pattern, ""])
            insert_index = len(lines)

        if insert_index >= 0:
            for link in links:
                lines.insert(insert_index, link)
                insert_index += 1

        return '\n'.join(lines)

    def run_linking_cycle(self) -> Dict:
        """Run a complete rule-based linking cycle."""
        start_time = datetime.now()
        self.logger.info("Starting rule-based linking cycle")

        try:
            matches = self.apply_rules()
            results = self.create_links(matches)

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

            self.logger.info(
                "Rule-based linking completed in %.1fs: %d links, %d files",
                duration,
                results['links_created'],
                results['files_modified']
            )
            return report

        except Exception as e:
            error_msg = f"Error in linking cycle: {e}"
            self.logger.error(error_msg)
            return {
                'timestamp': datetime.now().isoformat(),
                'type': 'rule_based_linking',
                'success': False,
                'error': error_msg
            }


def main():
    """CLI entry point for rule-based linker."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rule-Based Cross-Vault Linker"
    )
    parser.add_argument(
        "--cortex-path",
        default="/Users/simonjanke/Projects/cortex",
        help="Path to Cortex vault"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    args = parser.parse_args()

    linker = RuleBasedLinker(Path(args.cortex_path))

    if args.dry_run:
        matches = linker.apply_rules()
        print("\n=== Dry Run Results ===")
        print(f"Total matches found: {len(matches)}")
        for match in matches[:5]:
            print(
                f"- {match.source_file.name} -> "
                f"{match.target_file.name} (strength: {match.strength:.2f})"
            )
    else:
        report = linker.run_linking_cycle()
        print("\n=== Rule-Based Linking Results ===")
        print(f"Success: {report.get('success', False)}")
        print(f"Links created: {report.get('links_created', 0)}")
        print(f"Files modified: {report.get('files_modified', 0)}")


if __name__ == "__main__":  # pragma: no cover
    main()
