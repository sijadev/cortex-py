#!/usr/bin/env python3
"""
Cortex Markdown Management System
Provides comprehensive markdown-focused features for the Cortex system
"""

import re
import os
import yaml
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime


class MDContentType(Enum):
    """Types of markdown content"""
    MEETING_NOTES = "meeting-notes"
    PROJECT_DOCS = "project-docs"
    TECHNICAL_SPECS = "technical-specs"
    RESEARCH_NOTES = "research-notes"
    GENERAL_NOTES = "general-notes"
    DOCUMENTATION = "documentation"


class MDLinkType(Enum):
    """Types of markdown links"""
    INTERNAL_WIKI = "internal-wiki"  # [[internal-link]]
    EXTERNAL_HTTP = "external-http"  # [text](http://...)
    RELATIVE_FILE = "relative-file"  # [text](./file.md)
    ABSOLUTE_FILE = "absolute-file"  # [text](/path/file.md)
    ANCHOR_LINK = "anchor-link"     # [text](#heading)


@dataclass
class MDFrontmatter:
    """Structured frontmatter for markdown files"""
    title: str
    tags: List[str]
    category: str
    created: str
    updated: str
    author: Optional[str] = None
    project: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    content_type: Optional[str] = None

    def to_yaml(self) -> str:
        """Convert to YAML frontmatter"""
        data = asdict(self)
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        return f"---\n{yaml.dump(data, default_flow_style=False)}---\n"


@dataclass
class MDStructure:
    """Represents the structure of a markdown document"""
    headings: List[Tuple[int, str]]  # (level, text)
    lists: List[str]
    code_blocks: List[Tuple[str, str]]  # (language, code)
    tables: List[str]
    links: List[Tuple[MDLinkType, str, str]]  # (type, text, url)
    images: List[Tuple[str, str]]  # (alt_text, url)
    hashtags: Set[str]
    wiki_links: Set[str]
    frontmatter: Optional[MDFrontmatter]
    mermaid_diagrams: List[str]
    math_blocks: List[str]


@dataclass
class MDValidationResult:
    """Results from markdown validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    structure_score: float  # 0-1 score for document structure quality


class MarkdownManager:
    """Comprehensive markdown management system for Cortex"""

    def __init__(self, workspace_root: str = "/Users/simonjanke/Projects/cortex-py"):
        self.workspace_root = Path(workspace_root)
        self.templates_dir = self.workspace_root / "templates" / "markdown"
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure required directories exist"""
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    # ===== MD-TEMPLATE-SYSTEM =====

    def create_md_template(self, template_type: MDContentType,
                          title: str, tags: List[str] = None,
                          additional_sections: List[str] = None) -> str:
        """Create standardized markdown template"""
        tags = tags or []
        additional_sections = additional_sections or []

        # Create frontmatter
        frontmatter = MDFrontmatter(
            title=title,
            tags=tags,
            category=template_type.value,
            created=datetime.now().isoformat(),
            updated=datetime.now().isoformat(),
            content_type=template_type.value
        )

        # Base template structure based on type
        templates = {
            MDContentType.MEETING_NOTES: self._create_meeting_template(),
            MDContentType.PROJECT_DOCS: self._create_project_template(),
            MDContentType.TECHNICAL_SPECS: self._create_technical_template(),
            MDContentType.RESEARCH_NOTES: self._create_research_template(),
            MDContentType.GENERAL_NOTES: self._create_general_template(),
            MDContentType.DOCUMENTATION: self._create_documentation_template()
        }

        content = templates.get(template_type, templates[MDContentType.GENERAL_NOTES])

        # Add additional sections
        if additional_sections:
            content += "\n\n## Additional Sections\n\n"
            for section in additional_sections:
                content += f"### {section}\n\n<!-- Add content here -->\n\n"

        return frontmatter.to_yaml() + "\n" + content

    def _create_meeting_template(self) -> str:
        return """# Meeting Notes

## 📅 Meeting Details
- **Date**: 
- **Time**: 
- **Attendees**: 
- **Meeting Type**: 

## 📋 Agenda
1. 
2. 
3. 

## 📝 Discussion Points
### Topic 1


### Topic 2


## ✅ Decisions Made
- 
- 

## 🎯 Action Items
| Task | Assignee | Due Date | Status |
|------|----------|----------|---------|
|      |          |          |         |

## 📎 Follow-up Items
- 

## 🔗 Related Links
- [[Related-Document]]
- [External Link](https://example.com)

#meeting #notes"""

    def _create_project_template(self) -> str:
        return """# Project Documentation

## 🎯 Project Overview
<!-- Brief description of the project -->

## 📊 Project Status
- **Status**: 
- **Progress**: 
- **Last Updated**: 

## 🎯 Objectives
1. 
2. 
3. 

## 📋 Requirements
### Functional Requirements
- 

### Non-Functional Requirements
- 

## 🏗️ Architecture
```mermaid
graph TD
    A[Component A] --> B[Component B]
    B --> C[Component C]
```

## 🛠️ Implementation Plan
### Phase 1
- [ ] Task 1
- [ ] Task 2

### Phase 2
- [ ] Task 3
- [ ] Task 4

## 📚 Resources
- [[Related-Documentation]]
- [External Resource](https://example.com)

## 🧪 Testing
### Test Cases
| Test Case | Expected Result | Status |
|-----------|----------------|--------|
|           |                |        |

#project #documentation"""

    def _create_technical_template(self) -> str:
        return """# Technical Specification

## 📋 Overview
<!-- Brief technical overview -->

## 🎯 Requirements
### Technical Requirements
- 

### Performance Requirements
- 

## 🏗️ System Design
### Architecture
```mermaid
graph LR
    A[Input] --> B[Process]
    B --> C[Output]
```

### Components
#### Component 1
- **Purpose**: 
- **Responsibilities**: 
- **Interfaces**: 

## 📊 Data Models
```python
class ExampleModel:
    def __init__(self):
        pass
```

## 🔌 API Specification
### Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | /api/v1/ | Description |

## 🧪 Testing Strategy
### Unit Tests
- 

### Integration Tests
- 

## 📈 Performance Considerations
- 

## 🔒 Security Considerations
- 

#technical #specification #architecture"""

    def _create_research_template(self) -> str:
        return """# Research Notes

## 🔬 Research Question
<!-- Main research question or hypothesis -->

## 📚 Background
### Context
<!-- Background information and context -->

### Related Work
- [[Related-Research]]
- [Academic Paper](https://example.com)

## 🎯 Methodology
### Approach
- 

### Tools & Resources
- 

## 📊 Findings
### Key Insights
1. 
2. 
3. 

### Data Analysis
| Metric | Value | Notes |
|--------|-------|-------|
|        |       |       |

## 💡 Conclusions
### Summary
<!-- Summary of findings -->

### Implications
- 

### Future Work
- [ ] Follow-up research area 1
- [ ] Follow-up research area 2

## 🔗 References
1. 
2. 

#research #analysis #findings"""

    def _create_general_template(self) -> str:
        return """# General Notes

## 📝 Overview
<!-- Brief overview of the topic -->

## 🎯 Key Points
- 
- 
- 

## 📋 Details
### Section 1
<!-- Add content here -->

### Section 2
<!-- Add content here -->

## 💡 Insights
- 

## 🔗 Related
- [[Related-Note]]
- [External Link](https://example.com)

## 📎 Additional Notes
<!-- Any additional notes or thoughts -->

#notes #general"""

    def _create_documentation_template(self) -> str:
        return """# Documentation

## 📋 Overview
<!-- Brief overview of what this documents -->

## 🚀 Getting Started
### Prerequisites
- 
- 

### Installation
```bash
# Add installation commands here
```

## 📖 Usage
### Basic Usage
```python
# Example code here
```

### Advanced Usage
```python
# Advanced examples here
```

## 📊 Configuration
### Configuration Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
|        |      |         |             |

### Example Configuration
```yaml
# Example config
option: value
```

## 🔧 Troubleshooting
### Common Issues
#### Issue 1
**Problem**: 
**Solution**: 

## 📚 API Reference
### Methods
#### method_name()
**Description**: 
**Parameters**: 
**Returns**: 

## 🔗 See Also
- [[Related-Documentation]]
- [External Documentation](https://example.com)

#documentation #guide #reference"""

    # ===== MD-SYNTAX-ENHANCEMENT =====

    def enhance_markdown_syntax(self, content: str) -> str:
        """Enhance markdown with extended features"""
        enhanced = content

        # Add Mermaid diagram support
        enhanced = self._enhance_mermaid_diagrams(enhanced)

        # Add Math support
        enhanced = self._enhance_math_expressions(enhanced)

        # Enhance table formatting
        enhanced = self._enhance_tables(enhanced)

        # Add callout boxes
        enhanced = self._enhance_callouts(enhanced)

        return enhanced

    def _enhance_mermaid_diagrams(self, content: str) -> str:
        """Enhance Mermaid diagram rendering"""
        # Find and validate Mermaid blocks
        mermaid_pattern = r'```mermaid\n(.*?)\n```'

        def enhance_mermaid(match):
            diagram = match.group(1)
            # Add theme and styling - fix f-string syntax
            theme_config = "%%{init: {'theme':'base', 'themeVariables': { 'primaryColor': '#ff0000'}}}%%"
            enhanced_diagram = f"```mermaid\n{theme_config}\n{diagram}\n```"
            return enhanced_diagram

        return re.sub(mermaid_pattern, enhance_mermaid, content, flags=re.DOTALL)

    def _enhance_math_expressions(self, content: str) -> str:
        """Enhance mathematical expressions"""
        # Support for inline math: $equation$
        inline_math_pattern = r'\$([^$]+)\$'

        # Support for block math: $$equation$$
        block_math_pattern = r'\$\$([^$]+)\$\$'

        # Add LaTeX rendering hints - fix block math first to avoid conflicts
        content = re.sub(block_math_pattern, r'$$\1$$<!-- LaTeX block -->', content, flags=re.DOTALL)
        content = re.sub(inline_math_pattern, r'$\1$<!-- LaTeX inline -->', content)

        return content

    def _enhance_tables(self, content: str) -> str:
        """Enhance table formatting and features"""
        lines = content.split('\n')
        enhanced_lines = []
        in_table = False

        for line in lines:
            # Detect table lines
            if '|' in line and not in_table:
                # Starting a table - add table wrapper
                enhanced_lines.append('<!-- Enhanced Table Start -->')
                in_table = True
            elif '|' not in line and in_table:
                # Ending a table
                enhanced_lines.append('<!-- Enhanced Table End -->')
                in_table = False

            # Enhance table formatting
            if in_table and '|' in line:
                # Add better spacing and alignment
                parts = line.split('|')
                enhanced_parts = [part.strip() for part in parts]
                line = ' | '.join(enhanced_parts)

            enhanced_lines.append(line)

        return '\n'.join(enhanced_lines)

    def _enhance_callouts(self, content: str) -> str:
        """Add callout box support"""
        # Support for different callout types
        callout_patterns = {
            r'> \[!NOTE\]': '> **📝 Note:**',
            r'> \[!TIP\]': '> **💡 Tip:**',
            r'> \[!WARNING\]': '> **⚠️ Warning:**',
            r'> \[!DANGER\]': '> **🚨 Danger:**',
            r'> \[!INFO\]': '> **ℹ️ Info:**'
        }

        for pattern, replacement in callout_patterns.items():
            content = re.sub(pattern, replacement, content)

        return content

    # ===== MD-CONTENT-ANALYSIS =====

    def analyze_markdown_structure(self, content: str) -> MDStructure:
        """Analyze markdown structure and content"""
        frontmatter = self._extract_frontmatter(content)
        content_body = self._remove_frontmatter(content)

        structure = MDStructure(
            headings=self._extract_headings(content_body),
            lists=self._extract_lists(content_body),
            code_blocks=self._extract_code_blocks(content_body),
            tables=self._extract_tables(content_body),
            links=self._extract_links(content_body),
            images=self._extract_images(content_body),
            hashtags=self._extract_hashtags(content_body),
            wiki_links=self._extract_wiki_links(content_body),
            frontmatter=frontmatter,
            mermaid_diagrams=self._extract_mermaid_diagrams(content_body),
            math_blocks=self._extract_math_blocks(content_body)
        )

        return structure

    def _extract_frontmatter(self, content: str) -> Optional[MDFrontmatter]:
        """Extract YAML frontmatter"""
        # More flexible frontmatter pattern to handle various spacing
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            try:
                yaml_content = match.group(1).strip()
                yaml_data = yaml.safe_load(yaml_content)
                if yaml_data and isinstance(yaml_data, dict):
                    # Provide defaults for required fields if missing
                    title = yaml_data.get('title', '')
                    tags = yaml_data.get('tags', [])
                    category = yaml_data.get('category', 'general')

                    # Convert date objects to strings if needed
                    created = yaml_data.get('created', '')
                    if hasattr(created, 'isoformat'):  # datetime.date or datetime.datetime
                        created = created.isoformat()
                    elif created is None:
                        created = ''

                    updated = yaml_data.get('updated', '')
                    if hasattr(updated, 'isoformat'):  # datetime.date or datetime.datetime
                        updated = updated.isoformat()
                    elif updated is None:
                        updated = ''

                    return MDFrontmatter(
                        title=title,
                        tags=tags,
                        category=category,
                        created=str(created),
                        updated=str(updated),
                        author=yaml_data.get('author'),
                        project=yaml_data.get('project'),
                        status=yaml_data.get('status'),
                        priority=yaml_data.get('priority'),
                        content_type=yaml_data.get('content_type')
                    )
            except (yaml.YAMLError, TypeError, KeyError) as e:
                # If YAML parsing fails, return None
                return None
        return None

    def _remove_frontmatter(self, content: str) -> str:
        """Remove frontmatter from content"""
        frontmatter_pattern = r'^---\n.*?\n---\n'
        return re.sub(frontmatter_pattern, '', content, flags=re.DOTALL)

    def _extract_headings(self, content: str) -> List[Tuple[int, str]]:
        """Extract all headings with their levels"""
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        headings = []

        for line in content.split('\n'):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append((level, text))

        return headings

    def _extract_lists(self, content: str) -> List[str]:
        """Extract list items"""
        list_pattern = r'^[\s]*[-*+]\s+(.+)$'
        lists = []

        for line in content.split('\n'):
            match = re.match(list_pattern, line)
            if match:
                lists.append(match.group(1).strip())

        return lists

    def _extract_code_blocks(self, content: str) -> List[Tuple[str, str]]:
        """Extract code blocks with language"""
        code_pattern = r'```(\w*)\n(.*?)\n```'
        code_blocks = []

        for match in re.finditer(code_pattern, content, re.DOTALL):
            language = match.group(1) or 'text'
            code = match.group(2)
            code_blocks.append((language, code))

        return code_blocks

    def _extract_tables(self, content: str) -> List[str]:
        """Extract markdown tables"""
        lines = content.split('\n')
        tables = []
        current_table = []

        for line in lines:
            if '|' in line:
                current_table.append(line)
            else:
                if current_table:
                    tables.append('\n'.join(current_table))
                    current_table = []

        if current_table:
            tables.append('\n'.join(current_table))

        return tables

    def _extract_links(self, content: str) -> List[Tuple[MDLinkType, str, str]]:
        """Extract all types of links"""
        links = []

        # Wiki-style links [[text]]
        wiki_pattern = r'\[\[([^\]]+)\]\]'
        for match in re.finditer(wiki_pattern, content):
            links.append((MDLinkType.INTERNAL_WIKI, match.group(1), match.group(1)))

        # Standard markdown links [text](url)
        md_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(md_pattern, content):
            text = match.group(1)
            url = match.group(2)

            if url.startswith('http'):
                link_type = MDLinkType.EXTERNAL_HTTP
            elif url.startswith('#'):
                link_type = MDLinkType.ANCHOR_LINK
            elif url.startswith('./') or url.startswith('../'):
                link_type = MDLinkType.RELATIVE_FILE
            elif url.startswith('/'):
                link_type = MDLinkType.ABSOLUTE_FILE
            else:
                link_type = MDLinkType.RELATIVE_FILE

            links.append((link_type, text, url))

        return links

    def _extract_images(self, content: str) -> List[Tuple[str, str]]:
        """Extract image references"""
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        images = []

        for match in re.finditer(image_pattern, content):
            alt_text = match.group(1)
            url = match.group(2)
            images.append((alt_text, url))

        return images

    def _extract_hashtags(self, content: str) -> Set[str]:
        """Extract hashtags from content"""
        hashtag_pattern = r'#(\w+)'
        hashtags = set()

        for match in re.finditer(hashtag_pattern, content):
            hashtags.add(match.group(1))

        return hashtags

    def _extract_wiki_links(self, content: str) -> Set[str]:
        """Extract wiki-style links"""
        wiki_pattern = r'\[\[([^\]]+)\]\]'
        wiki_links = set()

        for match in re.finditer(wiki_pattern, content):
            wiki_links.add(match.group(1))

        return wiki_links

    def _extract_mermaid_diagrams(self, content: str) -> List[str]:
        """Extract Mermaid diagrams"""
        mermaid_pattern = r'```mermaid\n(.*?)\n```'
        diagrams = []

        for match in re.finditer(mermaid_pattern, content, re.DOTALL):
            diagrams.append(match.group(1))

        return diagrams

    def _extract_math_blocks(self, content: str) -> List[str]:
        """Extract mathematical expressions"""
        math_blocks = []

        # Block math $$...$$
        block_pattern = r'\$\$(.*?)\$\$'
        for match in re.finditer(block_pattern, content, re.DOTALL):
            math_blocks.append(match.group(1))

        # Inline math $...$
        inline_pattern = r'\$([^$]+)\$'
        for match in re.finditer(inline_pattern, content):
            math_blocks.append(match.group(1))

        return math_blocks

    # ===== MD-CROSS-REFERENCES =====

    def generate_cross_references(self, markdown_files: List[Path]) -> Dict[str, List[str]]:
        """Generate automatic cross-references between markdown files"""
        cross_refs = {}
        file_contents = {}

        # Load all markdown files
        for file_path in markdown_files:
            if file_path.suffix == '.md':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_contents[file_path.name] = f.read()
                except Exception:
                    continue

        # Find cross-references
        for filename, content in file_contents.items():
            refs = []

            # Find existing wiki links
            structure = self.analyze_markdown_structure(content)
            refs.extend(structure.wiki_links)

            # Find potential references based on content similarity
            for other_filename, other_content in file_contents.items():
                if filename != other_filename:
                    if self._should_cross_reference(content, other_content):
                        base_name = other_filename.replace('.md', '')
                        refs.append(base_name)

            cross_refs[filename] = list(set(refs))

        return cross_refs

    def _should_cross_reference(self, content1: str, content2: str) -> bool:
        """Determine if two documents should cross-reference each other"""
        # Extract keywords from both documents
        keywords1 = self._extract_keywords(content1)
        keywords2 = self._extract_keywords(content2)

        # Check for common keywords (simple implementation)
        common_keywords = keywords1.intersection(keywords2)

        # Cross-reference if they share significant keywords
        return len(common_keywords) >= 3

    def _extract_keywords(self, content: str) -> Set[str]:
        """Extract keywords from content"""
        # Remove frontmatter and markdown syntax
        clean_content = self._remove_frontmatter(content)
        clean_content = re.sub(r'[#*`\[\]()]', ' ', clean_content)

        # Extract meaningful words (simple implementation)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', clean_content.lower())

        # Filter common words
        stopwords = {'that', 'this', 'with', 'from', 'they', 'been', 'have',
                    'their', 'said', 'each', 'which', 'more', 'will', 'would',
                    'there', 'could', 'other', 'after', 'also', 'should'}

        keywords = set(words) - stopwords
        return keywords

    def insert_cross_references(self, content: str, cross_refs: List[str]) -> str:
        """Insert cross-references into markdown content"""
        if not cross_refs:
            return content

        # Add cross-references section at the end
        ref_section = "\n\n## 🔗 Related Documents\n\n"
        for ref in cross_refs:
            ref_section += f"- [[{ref}]]\n"

        return content + ref_section

    # ===== MD-VALIDATION =====

    def validate_markdown(self, content: str) -> MDValidationResult:
        """Comprehensive markdown validation"""
        errors = []
        warnings = []
        suggestions = []

        # Structure analysis
        structure = self.analyze_markdown_structure(content)

        # Validate frontmatter
        if not structure.frontmatter:
            warnings.append("Missing YAML frontmatter - consider adding metadata")
        elif not structure.frontmatter.title:
            errors.append("Frontmatter missing required 'title' field")

        # Validate heading structure
        heading_levels = [h[0] for h in structure.headings]
        if heading_levels:
            # Check for proper heading hierarchy
            for i in range(1, len(heading_levels)):
                if heading_levels[i] > heading_levels[i-1] + 1:
                    warnings.append(f"Heading level jump detected - avoid skipping levels")

            # Check for H1
            if 1 not in heading_levels:
                suggestions.append("Consider adding a main heading (H1)")
        else:
            warnings.append("No headings found - document structure unclear")

        # Validate links
        for link_type, text, url in structure.links:
            if link_type == MDLinkType.EXTERNAL_HTTP:
                if not url.startswith(('http://', 'https://')):
                    errors.append(f"Invalid external link: {url}")
            elif link_type == MDLinkType.INTERNAL_WIKI:
                # Could validate that referenced files exist
                pass

        # Validate images
        for alt_text, url in structure.images:
            if not alt_text:
                warnings.append(f"Image missing alt text: {url}")

        # Validate code blocks
        for language, code in structure.code_blocks:
            if not code.strip():
                warnings.append("Empty code block found")

        # Calculate structure score
        structure_score = self._calculate_structure_score(structure)

        # Overall validation
        is_valid = len(errors) == 0

        return MDValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            structure_score=structure_score
        )

    def _calculate_structure_score(self, structure: MDStructure) -> float:
        """Calculate document structure quality score"""
        score = 0.0
        max_score = 10.0

        # Frontmatter presence
        if structure.frontmatter:
            score += 2.0
            if structure.frontmatter.title:
                score += 1.0
            if structure.frontmatter.tags:
                score += 1.0

        # Heading structure
        if structure.headings:
            score += 2.0
            # Bonus for good hierarchy
            levels = [h[0] for h in structure.headings]
            if 1 in levels:
                score += 1.0

        # Content richness
        if structure.lists:
            score += 0.5
        if structure.code_blocks:
            score += 0.5
        if structure.tables:
            score += 0.5
        if structure.links:
            score += 1.0
        if structure.images:
            score += 0.5
        if structure.hashtags:
            score += 0.5
        if structure.wiki_links:
            score += 0.5

        return min(score / max_score, 1.0)


# ===== MARKDOWN TAG SYSTEM =====

class MarkdownTagSystem:
    """Advanced tagging system for markdown content"""

    def __init__(self):
        self.tag_categories = {
            'content': ['docs', 'notes', 'specs', 'meeting', 'research'],
            'status': ['draft', 'review', 'final', 'archived'],
            'priority': ['high', 'medium', 'low'],
            'project': [],  # Dynamic based on projects
            'technical': ['api', 'database', 'frontend', 'backend', 'devops'],
            'performance': ['optimization', 'monitoring', 'benchmarks', 'metrics']
        }

    def generate_content_based_tags(self, structure: MDStructure) -> List[str]:
        """Generate tags based on markdown content analysis"""
        tags = []

        # Tags from frontmatter
        if structure.frontmatter and structure.frontmatter.tags:
            tags.extend(structure.frontmatter.tags)

        # Tags from hashtags
        tags.extend([f"#{tag}" for tag in structure.hashtags])

        # Content-based tags
        if structure.code_blocks:
            languages = [lang for lang, _ in structure.code_blocks if lang]
            tags.extend([f"lang-{lang}" for lang in languages])

        if structure.mermaid_diagrams:
            tags.append('diagrams')

        if structure.math_blocks:
            tags.append('mathematics')

        if structure.tables:
            tags.append('data-tables')

        # Link-based tags
        link_types = [link[0] for link in structure.links]
        if MDLinkType.EXTERNAL_HTTP in link_types:
            tags.append('external-refs')
        if MDLinkType.INTERNAL_WIKI in link_types:
            tags.append('internal-refs')

        # Structure-based tags
        heading_count = len(structure.headings)
        if heading_count > 10:
            tags.append('detailed-doc')
        elif heading_count > 5:
            tags.append('structured-doc')

        return list(set(tags))

    def categorize_tags(self, tags: List[str]) -> Dict[str, List[str]]:
        """Categorize tags by type"""
        categorized = {category: [] for category in self.tag_categories.keys()}
        categorized['other'] = []

        for tag in tags:
            categorized_flag = False
            for category, category_tags in self.tag_categories.items():
                if any(cat_tag in tag.lower() for cat_tag in category_tags):
                    categorized[category].append(tag)
                    categorized_flag = True
                    break

            if not categorized_flag:
                categorized['other'].append(tag)

        return {k: v for k, v in categorized.items() if v}  # Remove empty categories

    def suggest_missing_tags(self, current_tags: List[str], structure: MDStructure) -> List[str]:
        """Suggest missing tags based on content analysis"""
        suggestions = []
        current_lower = [tag.lower() for tag in current_tags]

        # Suggest content type tags
        if not any(tag in current_lower for tag in self.tag_categories['content']):
            if 'meeting' in str(structure.frontmatter).lower():
                suggestions.append('meeting')
            elif structure.code_blocks:
                suggestions.append('technical')
            else:
                suggestions.append('documentation')

        # Suggest status tags
        if not any(tag in current_lower for tag in self.tag_categories['status']):
            suggestions.append('draft')

        # Suggest technical tags based on code blocks
        if structure.code_blocks:
            languages = [lang.lower() for lang, _ in structure.code_blocks]
            if 'python' in languages and 'python' not in current_lower:
                suggestions.append('python')
            if 'javascript' in languages and 'javascript' not in current_lower:
                suggestions.append('javascript')

        return suggestions


if __name__ == "__main__":
    # Example usage
    md_manager = MarkdownManager()
    tag_system = MarkdownTagSystem()

    # Create a meeting notes template
    template = md_manager.create_md_template(
        MDContentType.MEETING_NOTES,
        "Weekly Team Sync",
        tags=["meeting", "team", "weekly"]
    )

    print("Generated Template:")
    print(template)

    # Analyze structure
    structure = md_manager.analyze_markdown_structure(template)
    print(f"\nStructure Analysis:")
    print(f"Headings: {len(structure.headings)}")
    print(f"Tags: {structure.hashtags}")

    # Validate
    validation = md_manager.validate_markdown(template)
    print(f"\nValidation:")
    print(f"Valid: {validation.is_valid}")
    print(f"Structure Score: {validation.structure_score:.2f}")
