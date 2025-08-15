#!/usr/bin/env python3
"""
Cortex Markdown Integration System
Integrates markdown-focused features with the existing governance system
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

# Add src to path for imports
sys.path.append("/Users/simonjanke/Projects/cortex-py/src")

from markdown.md_manager import (
    MarkdownManager, MarkdownTagSystem, MDContentType,
    MDValidationResult, MDStructure
)
from governance.data_governance import DataGovernanceEngine, ValidationResult


@dataclass
class IntegratedValidationResult:
    """Combined validation result from both governance and markdown systems"""
    governance_result: ValidationResult
    markdown_result: MDValidationResult
    combined_passed: bool
    combined_suggestions: List[str]
    enhanced_tags: List[str]


class CortexMarkdownIntegration:
    """Integration layer between markdown system and governance engine"""

    def __init__(self, workspace_root: str = "/Users/simonjanke/Projects/cortex-py"):
        self.workspace_root = Path(workspace_root)
        self.md_manager = MarkdownManager(workspace_root)
        self.tag_system = MarkdownTagSystem()
        self.governance = DataGovernanceEngine()

        # Enhanced validation rules for markdown content
        self.governance.update_validation_rules({
            "markdown_structure_min_score": 0.6,
            "require_frontmatter": True,
            "require_headings": True,
            "max_heading_depth": 6,
            "min_sections": 2
        })

    def create_governed_markdown(self, content_type: MDContentType,
                                title: str, description: str,
                                project_type: str = None,
                                tags: List[str] = None) -> str:
        """Create markdown content with integrated governance validation"""

        # Create base template
        template = self.md_manager.create_md_template(
            content_type, title, tags or []
        )

        # Enhance with syntax features
        enhanced_template = self.md_manager.enhance_markdown_syntax(template)

        # Validate with integrated system
        validation_result = self.validate_integrated_content(
            title, enhanced_template, description,
            content_type.value, project_type
        )

        if not validation_result.combined_passed:
            # Add validation feedback to template
            enhanced_template += self._add_validation_feedback(validation_result)

        # Add cross-references if possible
        cross_refs = self._suggest_cross_references(enhanced_template, content_type)
        if cross_refs:
            enhanced_template = self.md_manager.insert_cross_references(
                enhanced_template, cross_refs
            )

        return enhanced_template

    def validate_integrated_content(self, name: str, content: str,
                                   description: str, note_type: str,
                                   project_type: str = None) -> IntegratedValidationResult:
        """Comprehensive validation using both systems"""

        # Governance validation
        governance_result = self.governance.validate_note_creation_with_context(
            name=name,
            content=content,
            description=description,
            note_type=note_type,
            project_type=project_type or "documentation"
        )

        # Markdown-specific validation
        markdown_result = self.md_manager.validate_markdown(content)

        # Analyze structure for enhanced tagging
        structure = self.md_manager.analyze_markdown_structure(content)
        enhanced_tags = self.tag_system.generate_content_based_tags(structure)

        # Add markdown-specific suggestions
        combined_suggestions = list(governance_result.suggestions)

        # Add markdown structure suggestions
        if markdown_result.structure_score < 0.6:
            combined_suggestions.append("Consider improving document structure (add more headings, lists, or code examples)")

        if not structure.frontmatter:
            combined_suggestions.append("Add YAML frontmatter for better metadata management")

        if len(structure.headings) < 2:
            combined_suggestions.append("Add more section headings to improve document organization")

        # Suggest markdown-specific tags
        missing_md_tags = self.tag_system.suggest_missing_tags(
            governance_result.suggestions, structure
        )
        if missing_md_tags:
            combined_suggestions.append(f"Consider adding markdown-specific tags: {', '.join(missing_md_tags)}")

        # Combined pass/fail logic
        combined_passed = (
            governance_result.passed and
            markdown_result.is_valid and
            markdown_result.structure_score >= 0.5
        )

        return IntegratedValidationResult(
            governance_result=governance_result,
            markdown_result=markdown_result,
            combined_passed=combined_passed,
            combined_suggestions=combined_suggestions,
            enhanced_tags=enhanced_tags
        )

    def _add_validation_feedback(self, result: IntegratedValidationResult) -> str:
        """Add validation feedback section to markdown"""
        feedback = "\n\n---\n\n## 🔍 Validation Feedback\n\n"

        if result.governance_result.errors:
            feedback += "### ❌ Governance Errors\n"
            for error in result.governance_result.errors:
                feedback += f"- {error}\n"
            feedback += "\n"

        if result.markdown_result.errors:
            feedback += "### ❌ Markdown Errors\n"
            for error in result.markdown_result.errors:
                feedback += f"- {error}\n"
            feedback += "\n"

        if result.governance_result.warnings or result.markdown_result.warnings:
            feedback += "### ⚠️ Warnings\n"
            for warning in result.governance_result.warnings:
                feedback += f"- **Governance:** {warning}\n"
            for warning in result.markdown_result.warnings:
                feedback += f"- **Markdown:** {warning}\n"
            feedback += "\n"

        if result.combined_suggestions:
            feedback += "### 💡 Suggestions\n"
            for suggestion in result.combined_suggestions:
                feedback += f"- {suggestion}\n"
            feedback += "\n"

        feedback += f"**Structure Score:** {result.markdown_result.structure_score:.2f}/1.0\n"
        feedback += f"**Enhanced Tags:** {', '.join(result.enhanced_tags)}\n"

        return feedback

    def _suggest_cross_references(self, content: str, content_type: MDContentType) -> List[str]:
        """Suggest cross-references based on content type and existing content"""
        cross_refs = []

        # Content type specific suggestions
        if content_type == MDContentType.MEETING_NOTES:
            cross_refs.extend(["Project-Overview", "Action-Items-Tracker"])
        elif content_type == MDContentType.TECHNICAL_SPECS:
            cross_refs.extend(["Architecture-Overview", "API-Documentation"])
        elif content_type == MDContentType.PROJECT_DOCS:
            cross_refs.extend(["Technical-Specifications", "Meeting-Notes"])
        elif content_type == MDContentType.RESEARCH_NOTES:
            cross_refs.extend(["Literature-Review", "Methodology-Guide"])

        # Content-based suggestions (simplified)
        content_lower = content.lower()
        if "api" in content_lower:
            cross_refs.append("API-Guidelines")
        if "database" in content_lower:
            cross_refs.append("Database-Schema")
        if "testing" in content_lower:
            cross_refs.append("Testing-Strategy")
        if "deployment" in content_lower:
            cross_refs.append("Deployment-Guide")

        return list(set(cross_refs))  # Remove duplicates

    def analyze_workspace_markdown(self) -> Dict[str, any]:
        """Analyze all markdown files in the workspace"""
        analysis = {
            "total_files": 0,
            "by_content_type": {},
            "validation_summary": {
                "passed": 0,
                "failed": 0,
                "warnings": 0
            },
            "tag_analysis": {
                "most_common": {},
                "uncategorized": 0
            },
            "structure_scores": [],
            "cross_references": {}
        }

        # Find all markdown files
        md_files = list(self.workspace_root.rglob("*.md"))
        analysis["total_files"] = len(md_files)

        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')

                # Analyze structure
                structure = self.md_manager.analyze_markdown_structure(content)
                analysis["structure_scores"].append(
                    self.md_manager.validate_markdown(content).structure_score
                )

                # Content type analysis
                if structure.frontmatter and structure.frontmatter.category:
                    category = structure.frontmatter.category
                    analysis["by_content_type"][category] = analysis["by_content_type"].get(category, 0) + 1

                # Tag analysis
                if structure.frontmatter and structure.frontmatter.tags:
                    for tag in structure.frontmatter.tags:
                        analysis["tag_analysis"]["most_common"][tag] = (
                            analysis["tag_analysis"]["most_common"].get(tag, 0) + 1
                        )

                # Validation
                validation = self.md_manager.validate_markdown(content)
                if validation.is_valid:
                    analysis["validation_summary"]["passed"] += 1
                else:
                    analysis["validation_summary"]["failed"] += 1

                if validation.warnings:
                    analysis["validation_summary"]["warnings"] += 1

            except Exception as e:
                # Skip files that can't be read
                continue

        # Calculate average structure score
        if analysis["structure_scores"]:
            analysis["average_structure_score"] = sum(analysis["structure_scores"]) / len(analysis["structure_scores"])
        else:
            analysis["average_structure_score"] = 0.0

        return analysis

    def generate_workspace_report(self) -> str:
        """Generate a comprehensive markdown workspace report"""
        analysis = self.analyze_workspace_markdown()

        report = f"""# Cortex Markdown Workspace Report

Generated: {os.popen('date').read().strip()}

## 📊 Overview

- **Total Markdown Files**: {analysis['total_files']}
- **Average Structure Score**: {analysis.get('average_structure_score', 0):.2f}/1.0
- **Validation Pass Rate**: {analysis['validation_summary']['passed']}/{analysis['total_files']} ({(analysis['validation_summary']['passed']/max(analysis['total_files'], 1)*100):.1f}%)

## 📋 Content Type Distribution

"""

        for content_type, count in analysis["by_content_type"].items():
            percentage = (count / analysis['total_files']) * 100
            report += f"- **{content_type.title()}**: {count} files ({percentage:.1f}%)\n"

        report += f"""
## ✅ Validation Summary

- **Passed**: {analysis['validation_summary']['passed']} files
- **Failed**: {analysis['validation_summary']['failed']} files  
- **With Warnings**: {analysis['validation_summary']['warnings']} files

## 🏷️ Tag Analysis

### Most Common Tags
"""

        # Sort tags by frequency
        sorted_tags = sorted(
            analysis["tag_analysis"]["most_common"].items(),
            key=lambda x: x[1], reverse=True
        )[:10]  # Top 10

        for tag, count in sorted_tags:
            report += f"- **{tag}**: {count} uses\n"

        report += f"""

## 📈 Recommendations

### Structure Improvements
"""

        avg_score = analysis.get('average_structure_score', 0)
        if avg_score < 0.6:
            report += "- **Low Average Structure Score**: Consider improving document organization with more headings, lists, and structured content\n"
        if avg_score < 0.4:
            report += "- **Critical Structure Issues**: Many documents lack basic structure elements\n"

        if analysis['validation_summary']['failed'] > 0:
            report += f"- **Validation Failures**: {analysis['validation_summary']['failed']} files need attention\n"

        if analysis['validation_summary']['warnings'] > analysis['total_files'] * 0.3:
            report += "- **High Warning Rate**: Consider addressing common warnings across documents\n"

        report += f"""
### Content Type Recommendations

"""

        if not analysis["by_content_type"]:
            report += "- **No Content Types Detected**: Add YAML frontmatter with category field to improve organization\n"

        if analysis["by_content_type"].get("general-notes", 0) > analysis['total_files'] * 0.5:
            report += "- **Too Many General Notes**: Consider categorizing documents more specifically\n"

        report += """
## 🔧 Next Steps

1. **Address Validation Failures**: Review and fix documents that failed validation
2. **Improve Structure Scores**: Add more headings, lists, and structured elements
3. **Standardize Frontmatter**: Ensure all documents have proper YAML metadata
4. **Cross-Reference Opportunities**: Link related documents using [[wiki-style]] links
5. **Tag Standardization**: Review and standardize tag usage across documents

---

*Report generated by Cortex Markdown Integration System*
        """

        return report

    def batch_enhance_markdown_files(self, directory: str = None) -> Dict[str, str]:
        """Batch enhance all markdown files in a directory"""
        target_dir = Path(directory) if directory else self.workspace_root
        results = {}

        for md_file in target_dir.rglob("*.md"):
            try:
                original_content = md_file.read_text(encoding='utf-8')

                # Enhance the content
                enhanced_content = self.md_manager.enhance_markdown_syntax(original_content)

                # Validate
                validation = self.md_manager.validate_markdown(enhanced_content)

                if validation.structure_score > 0.5:
                    results[str(md_file)] = "Enhanced successfully"
                    # Optionally write back (commented out for safety)
                    # md_file.write_text(enhanced_content, encoding='utf-8')
                else:
                    results[str(md_file)] = f"Enhancement needed (score: {validation.structure_score:.2f})"

            except Exception as e:
                results[str(md_file)] = f"Error: {str(e)}"

        return results


# CLI interface for the markdown system
def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Cortex Markdown Integration System")
    parser.add_argument("--create", choices=["meeting", "project", "technical", "research", "docs"],
                       help="Create new markdown document")
    parser.add_argument("--title", help="Title for new document")
    parser.add_argument("--description", help="Description for new document")
    parser.add_argument("--analyze", action="store_true", help="Analyze workspace markdown")
    parser.add_argument("--report", action="store_true", help="Generate workspace report")
    parser.add_argument("--validate", help="Validate specific markdown file")

    args = parser.parse_args()

    integration = CortexMarkdownIntegration()

    if args.create and args.title:
        content_type_map = {
            "meeting": MDContentType.MEETING_NOTES,
            "project": MDContentType.PROJECT_DOCS,
            "technical": MDContentType.TECHNICAL_SPECS,
            "research": MDContentType.RESEARCH_NOTES,
            "docs": MDContentType.DOCUMENTATION
        }

        content = integration.create_governed_markdown(
            content_type_map[args.create],
            args.title,
            args.description or "Generated document"
        )

        # Save to file
        filename = f"{args.title.lower().replace(' ', '-')}.md"
        Path(filename).write_text(content)
        print(f"Created: {filename}")

    elif args.analyze:
        analysis = integration.analyze_workspace_markdown()
        print(f"Total files: {analysis['total_files']}")
        print(f"Average structure score: {analysis.get('average_structure_score', 0):.2f}")
        print(f"Validation pass rate: {analysis['validation_summary']['passed']}/{analysis['total_files']}")

    elif args.report:
        report = integration.generate_workspace_report()
        report_file = "markdown-workspace-report.md"
        Path(report_file).write_text(report)
        print(f"Report generated: {report_file}")

    elif args.validate:
        file_path = Path(args.validate)
        if file_path.exists():
            content = file_path.read_text()
            validation = integration.md_manager.validate_markdown(content)
            print(f"Valid: {validation.is_valid}")
            print(f"Structure score: {validation.structure_score:.2f}")
            if validation.errors:
                print("Errors:", validation.errors)
            if validation.warnings:
                print("Warnings:", validation.warnings)
        else:
            print(f"File not found: {args.validate}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
