#!/usr/bin/env python3
"""
Unit tests for MD Manager functionality
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.md_system.md_manager import MarkdownManager, MDFrontmatter, MDContentType, MDLinkType


class TestMDManager:
    """Test cases for MarkdownManager class"""

    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.md_manager = MarkdownManager()

    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_frontmatter_basic(self):
        """Test basic frontmatter extraction"""
        content = """---
title: Test Document
tags: [test, markdown]
category: general
created: 2025-01-01
updated: 2025-01-02
author: Test Author
---

# Test Content

This is test content.
"""
        frontmatter = self.md_manager._extract_frontmatter(content)

        assert frontmatter is not None
        assert frontmatter.title == "Test Document"
        assert frontmatter.tags == ["test", "markdown"]
        assert frontmatter.category == "general"
        assert frontmatter.created == "2025-01-01"
        assert frontmatter.updated == "2025-01-02"
        assert frontmatter.author == "Test Author"

    def test_extract_frontmatter_minimal(self):
        """Test frontmatter extraction with minimal fields"""
        content = """---
title: Minimal Document
---

# Content
"""
        frontmatter = self.md_manager._extract_frontmatter(content)

        assert frontmatter is not None
        assert frontmatter.title == "Minimal Document"
        assert frontmatter.tags == []
        assert frontmatter.category == "general"
        assert frontmatter.created == ""
        assert frontmatter.updated == ""
        assert frontmatter.author is None

    def test_extract_frontmatter_no_frontmatter(self):
        """Test content with no frontmatter"""
        content = """# Regular Document

This is a regular markdown document without frontmatter.
"""
        frontmatter = self.md_manager._extract_frontmatter(content)
        assert frontmatter is None

    def test_extract_frontmatter_invalid_yaml(self):
        """Test frontmatter with invalid YAML"""
        content = """---
title: Test Document
tags: [invalid yaml structure
category: general
---

# Content
"""
        frontmatter = self.md_manager._extract_frontmatter(content)
        assert frontmatter is None

    def test_extract_frontmatter_empty_frontmatter(self):
        """Test empty frontmatter section"""
        content = """---
---

# Content
"""
        frontmatter = self.md_manager._extract_frontmatter(content)
        assert frontmatter is None

    def test_remove_frontmatter(self):
        """Test frontmatter removal"""
        content = """---
title: Test Document
tags: [test, markdown]
---

# Test Content

This is the actual content.
"""
        expected_content = """# Test Content

This is the actual content.
"""
        result = self.md_manager._remove_frontmatter(content)
        assert result.strip() == expected_content.strip()

    def test_remove_frontmatter_no_frontmatter(self):
        """Test frontmatter removal on content without frontmatter"""
        content = """# Test Content

This is the actual content.
"""
        result = self.md_manager._remove_frontmatter(content)
        assert result == content

    def test_extract_headings(self):
        """Test heading extraction"""
        content = """# Main Heading

Some content.

## Secondary Heading

More content.

### Tertiary Heading

Even more content.

#### Fourth Level

And more.
"""
        headings = self.md_manager._extract_headings(content)
        expected = [
            (1, "Main Heading"),
            (2, "Secondary Heading"),
            (3, "Tertiary Heading"),
            (4, "Fourth Level")
        ]
        assert headings == expected

    def test_frontmatter_to_yaml(self):
        """Test MDFrontmatter YAML serialization"""
        frontmatter = MDFrontmatter(
            title="Test Document",
            tags=["test", "markdown"],
            category="general",
            created="2025-01-01",
            updated="2025-01-02",
            author="Test Author"
        )
        yaml_output = frontmatter.to_yaml()
        assert "title: Test Document" in yaml_output
        assert "tags:" in yaml_output
        assert "test" in yaml_output
        assert "markdown" in yaml_output
        assert "category: general" in yaml_output

    def test_frontmatter_with_special_characters(self):
        """Test frontmatter extraction with special characters"""
        content = """---
title: "Test: Document with Special Characters!"
tags: ["test-tag", "special_chars"]
category: "test-category"
created: "2025-01-01"
updated: "2025-01-02"
---

# Content
"""
        frontmatter = self.md_manager._extract_frontmatter(content)

        assert frontmatter is not None
        assert frontmatter.title == "Test: Document with Special Characters!"
        assert "test-tag" in frontmatter.tags
        assert "special_chars" in frontmatter.tags
        assert frontmatter.category == "test-category"

    def test_frontmatter_with_multiline_values(self):
        """Test frontmatter with multiline values"""
        content = """---
title: Test Document
tags: 
  - test
  - markdown
  - multiline
category: general
created: "2025-01-01"
updated: "2025-01-02"
---

# Content
"""
        frontmatter = self.md_manager._extract_frontmatter(content)

        assert frontmatter is not None
        assert frontmatter.title == "Test Document"
        assert set(frontmatter.tags) == {"test", "markdown", "multiline"}
        assert frontmatter.category == "general"
