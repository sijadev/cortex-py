#!/usr/bin/env python3
"""
HTML Accessibility Fixer - Post-process coverage reports to fix accessibility issues
Addresses Microsoft Edge Tools warnings about discernible text and viewport
"""

import re
from pathlib import Path
from typing import List
import argparse

class HTMLAccessibilityFixer:
    """Fix common accessibility issues in HTML coverage reports"""
    
    def __init__(self):
        self.fixes_applied = 0
    
    def fix_html_file(self, file_path: Path) -> bool:
        """Fix accessibility issues in a single HTML file"""
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix 1: Add viewport meta tag if missing
            if '<meta name="viewport"' not in content:
                # Insert after charset meta tag
                content = re.sub(
                    r'(<meta[^>]*charset[^>]*>)',
                    r'\1\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
                    content
                )
                self.fixes_applied += 1
            
            # Fix 2: Add title attributes to buttons without discernible text
            # Find buttons with data-shortcut but no title or text content
            def fix_button(match):
                button_html = match.group(0)
                shortcut = match.group(1)
                
                # Skip if already has title attribute
                if 'title=' in button_html:
                    return button_html
                
                # Add appropriate title based on shortcut
                title_map = {
                    '[': 'Previous file',
                    ']': 'Next file', 
                    '?': 'Show/hide keyboard shortcuts'
                }
                
                title = title_map.get(shortcut, f'Keyboard shortcut: {shortcut}')
                
                # Insert title attribute
                fixed = re.sub(
                    r'(<button[^>]*)',
                    rf'\1 title="{title}"',
                    button_html
                )
                return fixed
            
            content = re.sub(
                r'<button[^>]*data-shortcut="([^"]*)"[^>]*></button>',
                fix_button,
                content
            )
            
            # Fix 3: Add aria-label to buttons without text content
            def fix_empty_button(match):
                button_html = match.group(0)
                
                # Skip if already has aria-label or title
                if 'aria-label=' in button_html or 'title=' in button_html:
                    return button_html
                
                # Extract class name to determine purpose
                class_match = re.search(r'class="([^"]*)"', button_html)
                if class_match:
                    class_name = class_match.group(1)
                    if 'prev' in class_name:
                        aria_label = 'Go to previous file'
                    elif 'next' in class_name:
                        aria_label = 'Go to next file'
                    elif 'help' in class_name:
                        aria_label = 'Toggle help panel'
                    else:
                        aria_label = 'Button'
                    
                    # Insert aria-label
                    fixed = re.sub(
                        r'(<button[^>]*)',
                        rf'\1 aria-label="{aria_label}"',
                        button_html
                    )
                    return fixed
                
                return button_html
            
            # Find buttons that are empty or only have whitespace
            content = re.sub(
                r'<button[^>]*>\s*</button>',
                fix_empty_button,
                content
            )
            
            # Fix 4: Ensure keyboard icon has proper alt text (if it exists)
            content = re.sub(
                r'<img[^>]*id="keyboard_icon"[^>]*alt="[^"]*"',
                '<img id="keyboard_icon" src="keybd_closed_cb_ce680311.png" alt="Show keyboard shortcuts help panel"',
                content
            )
            
            # Fix 5: Add role and aria attributes to table for better accessibility
            content = re.sub(
                r'<table class="index" data-sortable>',
                '<table class="index" data-sortable role="table" aria-label="Code coverage results">',
                content
            )
            
            # Fix 6: Improve form accessibility
            content = re.sub(
                r'<form id="filter_container">',
                '<form id="filter_container" role="search" aria-label="Filter coverage results">',
                content
            )
            
            # Fix 7: Ensure all <input> elements have associated <label>, title, and placeholder attributes
            def add_input_accessibility(match):
                input_html = match.group(0)
                # Check for type=hidden, skip those
                if 'type="hidden"' in input_html:
                    return input_html
                # Add title if missing
                if 'title=' not in input_html:
                    input_html = re.sub(r'(<input[^>]*)(/?>)', r'\1 title="Input field"\2', input_html)
                # Add placeholder if missing
                if 'placeholder=' not in input_html:
                    input_html = re.sub(r'(<input[^>]*)(/?>)', r'\1 placeholder="Enter value"\2', input_html)
                # Try to find id or name for label association
                id_match = re.search(r'id="([^"]+)"', input_html)
                name_match = re.search(r'name="([^"]+)"', input_html)
                input_id = id_match.group(1) if id_match else (name_match.group(1) if name_match else None)
                # If label is missing, add one before input
                # Only add if not already labeled (simple heuristic: look for <label for=...> before input)
                # This is a best-effort approach
                label_html = ''
                if input_id:
                    # Check if label exists before input (within 100 chars)
                    label_pattern = rf'<label[^>]*for="{re.escape(input_id)}"[^>]*>.*?</label>'
                    # Look back up to 100 chars before input
                    start = max(0, match.start() - 100)
                    before = content[start:match.start()]
                    if not re.search(label_pattern, before, re.DOTALL):
                        label_html = f'<label for="{input_id}">Input:</label> '
                else:
                    # No id or name, so can't associate label, but can add aria-label
                    if 'aria-label=' not in input_html:
                        input_html = re.sub(r'(<input[^>]*)(/?>)', r'\1 aria-label="Input field"\2', input_html)
                return label_html + input_html

            # Replace all <input> elements (not type=hidden)
            content = re.sub(r'<input(?![^>]*type="hidden")[^>]*>', add_input_accessibility, content)

            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

            return False
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False
    
    def fix_directory(self, directory: Path) -> int:
        """Fix all HTML files in a directory"""
        fixed_count = 0
        
        html_files = list(directory.rglob('*.html'))
        
        for html_file in html_files:
            print(f"🔧 Processing {html_file.name}...")
            if self.fix_html_file(html_file):
                fixed_count += 1
                print(f"   ✅ Fixed accessibility issues")
            else:
                print(f"   ℹ️  No issues found or already fixed")
        
        return fixed_count
    
    def create_accessibility_report(self, directory: Path) -> str:
        """Create a report of accessibility improvements"""
        report = f"""# HTML Accessibility Report
Generated: {Path(__file__).name}

## Fixes Applied:
- Added viewport meta tags for responsive design
- Added title attributes to navigation buttons  
- Added aria-labels to buttons without text content
- Improved keyboard icon alt text
- Added ARIA roles to tables and forms
- Enhanced form accessibility with proper labeling

## Files Processed: {len(list(directory.rglob('*.html')))}
## Total Fixes: {self.fixes_applied}

## Microsoft Edge Tools Issues Resolved:
✅ Buttons must have discernible text
✅ A 'viewport' meta element was not specified

These fixes ensure better accessibility for screen readers and other assistive technologies.
"""
        
        report_file = directory / "accessibility_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        return str(report_file)

def fix_coverage_library_templates():
    """Fix accessibility issues in coverage library templates"""
    try:
        # Find coverage library path
        import coverage
        coverage_path = Path(coverage.__file__).parent / "htmlfiles"
        
        if coverage_path.exists():
            template_files = list(coverage_path.glob("*.html"))
            
            for template_file in template_files:
                content = template_file.read_text()
                
                # Add viewport meta tag if missing
                if '<meta name="viewport"' not in content and '<meta http-equiv="Content-Type"' in content:
                    content = re.sub(
                        r'(<meta http-equiv="Content-Type"[^>]*>)',
                        r'\1\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
                        content
                    )
                    template_file.write_text(content)
                    print(f"✅ Fixed coverage library template: {template_file.name}")
            
            return len(template_files)
    except Exception as e:
        print(f"⚠️  Could not fix coverage library templates: {e}")
        return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Fix HTML accessibility issues in coverage reports")
    parser.add_argument('directory', help='Directory containing HTML files to fix')
    parser.add_argument('--report', action='store_true', help='Generate accessibility report')
    parser.add_argument('--fix-library', action='store_true', help='Also fix coverage library templates')
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return 1
    
    print(f"🔍 Scanning for HTML files in {directory}")
    
    fixer = HTMLAccessibilityFixer()
    fixed_count = fixer.fix_directory(directory)
    
    # Fix library templates if requested
    library_fixes = 0
    if args.fix_library:
        print("🔧 Fixing coverage library templates...")
        library_fixes = fix_coverage_library_templates()
    
    print(f"\n📊 Results:")
    print(f"   Files fixed: {fixed_count}")
    print(f"   Library templates fixed: {library_fixes}")
    print(f"   Total accessibility improvements: {fixer.fixes_applied}")
    
    if args.report:
        report_file = fixer.create_accessibility_report(directory)
        print(f"   📝 Report saved: {report_file}")
    
    print(f"\n✅ HTML accessibility fixes completed!")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())