#!/usr/bin/env python3
"""
Tests for the Cortex Markdown Management System
Comprehensive testing of all markdown-focused features
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.append("/Users/simonjanke/Projects/cortex-py/src")

from md_system.md_manager import (
    MarkdownManager,
    MarkdownTagSystem,
    MDContentType,
    MDLinkType,
    MDFrontmatter,
    MDStructure,
    MDValidationResult
)


class TestMarkdownTemplateSystem:
    """Tests for MD-Template-System"""

    @pytest.fixture
    def md_manager(self):
        return MarkdownManager()

    def test_create_meeting_notes_template(self, md_manager):
        """Test creating meeting notes template"""
        template = md_manager.create_md_template(
            MDContentType.MEETING_NOTES,
            "Weekly Team Meeting",
            tags=["meeting", "team"]
        )

        assert "---" in template  # Has frontmatter
        assert "title: Weekly Team Meeting" in template
        assert "category: meeting-notes" in template
        assert "# Meeting Notes" in template
        assert "## 📅 Meeting Details" in template
        assert "## 📋 Agenda" in template
        assert "## ✅ Decisions Made" in template
        assert "## 🎯 Action Items" in template
        assert "#meeting #notes" in template

    def test_create_project_docs_template(self, md_manager):
        """Test creating project documentation template"""
        template = md_manager.create_md_template(
            MDContentType.PROJECT_DOCS,
            "New Project Documentation",
            tags=["project", "documentation"]
        )

        assert "# Project Documentation" in template
        assert "## 🎯 Project Overview" in template
        assert "## 🏗️ Architecture" in template
        assert "```mermaid" in template
        assert "## 🛠️ Implementation Plan" in template
        assert "#project #documentation" in template

    def test_create_technical_spec_template(self, md_manager):
        """Test creating technical specification template"""
        template = md_manager.create_md_template(
            MDContentType.TECHNICAL_SPECS,
            "API Specification",
            tags=["technical", "api", "spec"]
        )

        assert "# Technical Specification" in template
        assert "## 🏗️ System Design" in template
        assert "## 📊 Data Models" in template
        assert "## 🔌 API Specification" in template
        assert "```python" in template
        assert "#technical #specification #architecture" in template

    def test_create_research_notes_template(self, md_manager):
        """Test creating research notes template"""
        template = md_manager.create_md_template(
            MDContentType.RESEARCH_NOTES,
            "Machine Learning Research",
            tags=["research", "ml", "analysis"]
        )

        assert "# Research Notes" in template
        assert "## 🔬 Research Question" in template
        assert "## 📚 Background" in template
        assert "## 🎯 Methodology" in template
        assert "## 📊 Findings" in template
        assert "## 💡 Conclusions" in template
        assert "#research #analysis #findings" in template

    def test_template_with_additional_sections(self, md_manager):
        """Test template creation with additional custom sections"""
        template = md_manager.create_md_template(
            MDContentType.GENERAL_NOTES,
            "Custom Notes",
            tags=["custom"],
            additional_sections=["Custom Section 1", "Custom Section 2"]
        )

        assert "## Additional Sections" in template
        assert "### Custom Section 1" in template
        assert "### Custom Section 2" in template


class TestMarkdownSyntaxEnhancement:
    """Tests for MD-Syntax-Enhancement features"""

    @pytest.fixture
    def md_manager(self):
        return MarkdownManager()

    def test_enhance_mermaid_diagrams(self, md_manager):
        """Test Mermaid diagram enhancement"""
        content = """
# Test Document

```mermaid
graph TD
    A --> B
```
        """

        enhanced = md_manager.enhance_markdown_syntax(content)

        assert "%%{init:" in enhanced
        assert "theme" in enhanced
        assert "themeVariables" in enhanced

    def test_enhance_math_expressions(self, md_manager):
        """Test mathematical expression enhancement"""
        content = """
# Math Test

Inline math: $E = mc^2$

Block math:
$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$
        """

        enhanced = md_manager.enhance_markdown_syntax(content)

        assert "<!-- LaTeX inline -->" in enhanced
        assert "<!-- LaTeX block -->" in enhanced

    def test_enhance_tables(self, md_manager):
        """Test table enhancement"""
        content = """
# Table Test

|Column1|Column2|Column3|
|---|---|---|
|Value1|Value2|Value3|
        """

        enhanced = md_manager.enhance_markdown_syntax(content)

        assert "<!-- Enhanced Table Start -->" in enhanced
        assert "<!-- Enhanced Table End -->" in enhanced
        assert " | " in enhanced  # Better spacing

    def test_enhance_callouts(self, md_manager):
        """Test callout box enhancement"""
        content = """
> [!NOTE]
> This is a note

> [!WARNING]
> This is a warning

> [!TIP]
> This is a tip
        """

        enhanced = md_manager.enhance_markdown_syntax(content)

        assert "**📝 Note:**" in enhanced
        assert "**⚠️ Warning:**" in enhanced
        assert "**💡 Tip:**" in enhanced


class TestMarkdownContentAnalysis:
    """Tests for MD-Content-Analysis"""

    @pytest.fixture
    def md_manager(self):
        return MarkdownManager()

    @pytest.fixture
    def sample_markdown(self):
        return """---
title: Test Document
tags: [test, analysis]
category: documentation
created: 2025-01-01T00:00:00
updated: 2025-01-01T00:00:00
---

# Main Heading

## Section 1

This is some content with [[Internal-Link]] and [External Link](https://example.com).

- List item 1
- List item 2

### Subsection

```python
def hello():
    return "world"
```

```mermaid
graph TD
    A --> B
```

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |

Math: $x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$

![Alt text](image.png)

#hashtag #analysis
        """

    def test_analyze_markdown_structure(self, md_manager, sample_markdown):
        """Test comprehensive markdown structure analysis"""
        structure = md_manager.analyze_markdown_structure(sample_markdown)

        # Test frontmatter extraction
        assert structure.frontmatter is not None
        assert structure.frontmatter.title == "Test Document"
        assert "test" in structure.frontmatter.tags

        # Test heading extraction
        assert len(structure.headings) == 3
        assert (1, "Main Heading") in structure.headings
        assert (2, "Section 1") in structure.headings
        assert (3, "Subsection") in structure.headings

        # Test list extraction
        assert "List item 1" in structure.lists
        assert "List item 2" in structure.lists

        # Test code block extraction
        assert len(structure.code_blocks) == 2
        python_code = next((code for lang, code in structure.code_blocks if lang == "python"), None)
        assert "def hello():" in python_code

        # Test link extraction - fix the variable name issue
        wiki_links = [link_data for link_data in structure.links if link_data[0] == MDLinkType.INTERNAL_WIKI]
        external_links = [link_data for link_data in structure.links if link_data[0] == MDLinkType.EXTERNAL_HTTP]
        assert len(wiki_links) == 1
        assert len(external_links) == 1

        # Test hashtag extraction
        assert "hashtag" in structure.hashtags
        assert "analysis" in structure.hashtags

        # Test image extraction
        assert len(structure.images) == 1
        assert ("Alt text", "image.png") in structure.images

        # Test mermaid diagram extraction
        assert len(structure.mermaid_diagrams) == 1
        assert "A --> B" in structure.mermaid_diagrams[0]

        # Test math extraction
        assert len(structure.math_blocks) >= 1

    def test_extract_frontmatter(self, md_manager):
        """Test YAML frontmatter extraction"""
        content = """---
title: Test
tags: [tag1, tag2]
custom: value
---

# Content"""

        frontmatter = md_manager._extract_frontmatter(content)

        assert frontmatter is not None
        assert frontmatter.title == "Test"
        assert frontmatter.tags == ["tag1", "tag2"]

    def test_extract_headings(self, md_manager):
        """Test heading extraction"""
        content = """# H1
## H2
### H3
#### H4
##### H5
###### H6"""

        headings = md_manager._extract_headings(content)

        assert len(headings) == 6
        assert headings[0] == (1, "H1")
        assert headings[1] == (2, "H2")
        assert headings[5] == (6, "H6")

    def test_extract_links(self, md_manager):
        """Test link extraction and classification"""
        content = """
[[Wiki Link]]
[External](https://example.com)
[Relative](./file.md)
[Absolute](/path/file.md)
[Anchor](#section)
        """

        links = md_manager._extract_links(content)

        link_types = [link_type for link_type, _, _ in links]
        assert MDLinkType.INTERNAL_WIKI in link_types
        assert MDLinkType.EXTERNAL_HTTP in link_types
        assert MDLinkType.RELATIVE_FILE in link_types
        assert MDLinkType.ABSOLUTE_FILE in link_types
        assert MDLinkType.ANCHOR_LINK in link_types

    def test_extract_code_blocks(self, md_manager):
        """Test code block extraction"""
        content = """
```python
print("hello")
```

```javascript
console.log("world");
```

```
plain text
```
        """

        code_blocks = md_manager._extract_code_blocks(content)

        assert len(code_blocks) == 3
        languages = [lang for lang, _ in code_blocks]
        assert "python" in languages
        assert "javascript" in languages
        assert "text" in languages  # Default for no language specified


class TestMarkdownCrossReferences:
    """Tests for MD-Cross-References"""

    @pytest.fixture
    def md_manager(self):
        return MarkdownManager()

    @pytest.fixture
    def temp_md_files(self):
        """Create temporary markdown files for testing"""
        temp_dir = Path(tempfile.mkdtemp())

        files = {
            "project-overview.md": """# Project Overview
This project uses machine learning algorithms for data analysis.
Keywords: python, tensorflow, data science, analysis
            """,
            "ml-implementation.md": """# ML Implementation
Implementation details for machine learning models.
Using tensorflow and python for data analysis.
Keywords: machine learning, python, tensorflow, models
            """,
            "unrelated-doc.md": """# Unrelated Document
This document talks about cooking recipes.
Keywords: cooking, recipes, food
            """
        }

        file_paths = []
        for filename, content in files.items():
            file_path = temp_dir / filename
            file_path.write_text(content)
            file_paths.append(file_path)

        yield file_paths

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

    def test_generate_cross_references(self, md_manager, temp_md_files):
        """Test automatic cross-reference generation"""
        cross_refs = md_manager.generate_cross_references(temp_md_files)

        # Should find cross-references between related documents
        assert "project-overview.md" in cross_refs
        assert "ml-implementation.md" in cross_refs

        # Related documents should reference each other
        project_refs = cross_refs.get("project-overview.md", [])
        ml_refs = cross_refs.get("ml-implementation.md", [])

        # They should reference each other due to common keywords
        assert len(project_refs) > 0 or len(ml_refs) > 0

    def test_insert_cross_references(self, md_manager):
        """Test insertion of cross-references into content"""
        content = "# Test Document\n\nSome content here."
        cross_refs = ["Related-Doc-1", "Related-Doc-2"]

        enhanced_content = md_manager.insert_cross_references(content, cross_refs)

        assert "## 🔗 Related Documents" in enhanced_content
        assert "- [[Related-Doc-1]]" in enhanced_content
        assert "- [[Related-Doc-2]]" in enhanced_content

    def test_keyword_extraction(self, md_manager):
        """Test keyword extraction for cross-referencing"""
        content = """---
title: Test
---
# Machine Learning Project
This document describes machine learning algorithms and data analysis techniques.
Using python and tensorflow for implementation.
        """

        keywords = md_manager._extract_keywords(content)

        assert "machine" in keywords
        assert "learning" in keywords
        assert "python" in keywords
        assert "tensorflow" in keywords
        # Should filter out common words
        assert "this" not in keywords
        assert "that" not in keywords


class TestMarkdownValidation:
    """Tests for MD-Validation"""

    @pytest.fixture
    def md_manager(self):
        return MarkdownManager()

    def test_validate_good_markdown(self, md_manager):
        """Test validation of well-structured markdown"""
        good_content = """---
title: Good Document
tags: [test, validation]
---

# Main Title

## Section 1

This is good content with proper structure.

- Well formatted list
- Good organization

### Subsection

![Alt text](image.png)

[Good link](https://example.com)

## Section 2

More good content.
        """

        result = md_manager.validate_markdown(good_content)

        assert result.is_valid == True
        assert len(result.errors) == 0
        assert result.structure_score > 0.7  # Should have good structure score

    def test_validate_problematic_markdown(self, md_manager):
        """Test validation of problematic markdown"""
        bad_content = """
# Title

##### Bad heading jump (skips levels)

![](image.png)

[Bad link](not-a-url)

```

```

Some content.
        """

        result = md_manager.validate_markdown(bad_content)

        assert len(result.warnings) > 0  # Should have warnings
        assert any("Missing YAML frontmatter" in w for w in result.warnings)
        assert any("heading level jump" in w.lower() for w in result.warnings)
        assert any("missing alt text" in w.lower() for w in result.warnings)
        # Check for empty code block warning (make more flexible)
        has_empty_code_warning = any("empty" in w.lower() and "code" in w.lower() for w in result.warnings)
        # If no empty code warning, that's acceptable as the implementation may vary
        assert has_empty_code_warning

    def test_validate_missing_frontmatter(self, md_manager):
        """Test validation with missing frontmatter"""
        content = "# Just a title\n\nSome content."

        result = md_manager.validate_markdown(content)

        assert any("frontmatter" in w.lower() for w in result.warnings)

    def test_structure_score_calculation(self, md_manager):
        """Test structure score calculation"""
        # Minimal content
        minimal_content = "# Title\n\nContent."
        minimal_result = md_manager.validate_markdown(minimal_content)

        # Rich content
        rich_content = """---
title: Rich Document
tags: [test]
---

# Main Title

## Section 1

- List item
- Another item

```python
code here
```

| Table | Header |
|-------|--------|
| Data  | Value  |

[Link](https://example.com)

![Image](image.png)

#hashtag [[wiki-link]]
        """
        rich_result = md_manager.validate_markdown(rich_content)

        # Rich content should have higher structure score
        assert rich_result.structure_score > minimal_result.structure_score


class TestMarkdownTagSystem:
    """Tests for the Markdown Tag System"""

    @pytest.fixture
    def tag_system(self):
        return MarkdownTagSystem()

    @pytest.fixture
    def sample_structure(self):
        """Sample markdown structure for testing"""
        frontmatter = MDFrontmatter(
            title="Test Document",
            tags=["existing-tag", "documentation"],
            category="docs",
            created="2025-01-01T00:00:00",
            updated="2025-01-01T00:00:00"
        )

        return MDStructure(
            headings=[(1, "Main"), (2, "Section")],
            lists=["Item 1", "Item 2"],
            code_blocks=[("python", "print('hello')"), ("javascript", "console.log('hi')")],
            tables=["| A | B |\n|---|---|\n| 1 | 2 |"],
            links=[(MDLinkType.EXTERNAL_HTTP, "Example", "https://example.com")],
            images=[("Alt", "image.png")],
            hashtags={"performance", "optimization"},
            wiki_links={"Related-Doc"},
            frontmatter=frontmatter,
            mermaid_diagrams=["graph TD\n A --> B"],
            math_blocks=["x = y + z"]
        )

    def test_generate_content_based_tags(self, tag_system, sample_structure):
        """Test automatic tag generation based on content"""
        tags = tag_system.generate_content_based_tags(sample_structure)

        # Should include frontmatter tags
        assert "existing-tag" in tags
        assert "documentation" in tags

        # Should include hashtags with # prefix
        assert "#performance" in tags
        assert "#optimization" in tags

        # Should include language tags from code blocks
        assert "lang-python" in tags
        assert "lang-javascript" in tags

        # Should include feature-based tags
        assert "diagrams" in tags  # From mermaid
        assert "mathematics" in tags  # From math blocks
        assert "data-tables" in tags  # From tables
        assert "external-refs" in tags  # From external links
        # Check if internal-refs is generated (it should be from wiki_links)
        if sample_structure.wiki_links:
            assert "internal-refs" in tags  # From wiki links

    def test_categorize_tags(self, tag_system):
        """Test tag categorization"""
        tags = [
            "docs", "meeting", "high", "python", "optimization",
            "draft", "custom-tag", "api", "monitoring"
        ]

        categorized = tag_system.categorize_tags(tags)

        assert "docs" in categorized["content"]
        assert "meeting" in categorized["content"]
        assert "high" in categorized["priority"]
        assert "draft" in categorized["status"]
        assert "api" in categorized["technical"]
        assert "optimization" in categorized["performance"]
        assert "monitoring" in categorized["performance"]
        assert "custom-tag" in categorized["other"]

    def test_suggest_missing_tags(self, tag_system, sample_structure):
        """Test missing tag suggestions"""
        current_tags = ["existing-tag"]  # Minimal tags

        suggestions = tag_system.suggest_missing_tags(current_tags, sample_structure)

        # Should suggest content type
        assert any(tag in suggestions for tag in ["technical", "documentation"])

        # Should suggest status
        assert "draft" in suggestions

        # Should suggest language tags based on code blocks
        assert "python" in suggestions

    def test_suggest_tags_for_meeting_content(self, tag_system):
        """Test tag suggestions for meeting content"""
        meeting_frontmatter = MDFrontmatter(
            title="Meeting Notes",
            tags=[],
            category="meeting-notes",
            created="2025-01-01T00:00:00",
            updated="2025-01-01T00:00:00"
        )

        meeting_structure = MDStructure(
            headings=[(1, "Meeting Notes")],
            lists=[],
            code_blocks=[],
            tables=[],
            links=[],
            images=[],
            hashtags=set(),
            wiki_links=set(),
            frontmatter=meeting_frontmatter,
            mermaid_diagrams=[],
            math_blocks=[]
        )

        suggestions = tag_system.suggest_missing_tags([], meeting_structure)

        assert "meeting" in suggestions


class TestMarkdownIntegration:
    """Integration tests for the complete markdown system"""

    @pytest.fixture
    def md_manager(self):
        return MarkdownManager()

    @pytest.fixture
    def tag_system(self):
        return MarkdownTagSystem()

    def test_complete_workflow(self, md_manager, tag_system):
        """Test complete markdown workflow"""
        # 1. Create template
        template = md_manager.create_md_template(
            MDContentType.TECHNICAL_SPECS,
            "API Documentation",
            tags=["api", "documentation", "technical"]
        )

        # 2. Enhance syntax
        enhanced = md_manager.enhance_markdown_syntax(template)

        # 3. Analyze structure
        structure = md_manager.analyze_markdown_structure(enhanced)

        # 4. Generate additional tags
        content_tags = tag_system.generate_content_based_tags(structure)

        # 5. Validate
        validation = md_manager.validate_markdown(enhanced)

        # Assertions
        assert "# Technical Specification" in template
        assert structure.frontmatter is not None
        assert structure.frontmatter.title == "API Documentation"
        assert len(content_tags) > 0
        assert validation.is_valid
        assert validation.structure_score > 0.5

    def test_cross_reference_workflow(self, md_manager):
        """Test cross-reference generation workflow"""
        # Create sample documents
        doc1 = md_manager.create_md_template(
            MDContentType.PROJECT_DOCS,
            "Machine Learning Project",
            tags=["ml", "python", "tensorflow"]
        )

        doc2 = md_manager.create_md_template(
            MDContentType.TECHNICAL_SPECS,
            "ML API Specification",
            tags=["api", "ml", "python"]
        )

        # Test that they would cross-reference
        keywords1 = md_manager._extract_keywords(doc1)
        keywords2 = md_manager._extract_keywords(doc2)

        # Should have common keywords for cross-referencing
        common = keywords1.intersection(keywords2)
        assert len(common) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
