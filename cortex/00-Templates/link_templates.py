"""
Link Templates for Cross-Vault Linker

Template system for generating consistent link entries across files.
"""

from dataclasses import dataclass
from enum import Enum


class LinkPurpose(Enum):
    """Enum for different link purposes"""
    REFERENCE = "reference"
    RELATED_WORK = "related-work"
    EXAMPLE = "example"
    DOCUMENTATION = "documentation"
    IMPLEMENTATION = "implementation"


@dataclass
class LinkTemplate:
    """Template for generating link entries"""
    purpose: LinkPurpose
    icon: str
    label: str
    format_string: str

    def format_link(self, **kwargs) -> str:
        """Format the link using the template"""
        return self.format_string.format(**kwargs)


class LinkTemplates:
    """Collection of link templates"""

    TEMPLATES = {
        LinkPurpose.REFERENCE: LinkTemplate(
            purpose=LinkPurpose.REFERENCE,
            icon="🔍",
            label="Reference",
            format_string="- {icon} **{label}**: [[{target_vault}/{target_file}|{display_name}]] "
                         "(Confidence: {confidence}%)"
        ),

        LinkPurpose.RELATED_WORK: LinkTemplate(
            purpose=LinkPurpose.RELATED_WORK,
            icon="↔️",
            label="Related",
            format_string="- {icon} **{label}**: [[{target_vault}/{target_file}|{display_name}]] "
                         "(Confidence: {confidence}%)"
        ),

        LinkPurpose.EXAMPLE: LinkTemplate(
            purpose=LinkPurpose.EXAMPLE,
            icon="💡",
            label="Example",
            format_string="- {icon} **{label}**: [[{target_vault}/{target_file}|{display_name}]] "
                         "(Confidence: {confidence}%)"
        ),

        LinkPurpose.DOCUMENTATION: LinkTemplate(
            purpose=LinkPurpose.DOCUMENTATION,
            icon="📚",
            label="Docs",
            format_string="- {icon} **{label}**: [[{target_vault}/{target_file}|{display_name}]] "
                         "(Confidence: {confidence}%)"
        ),

        LinkPurpose.IMPLEMENTATION: LinkTemplate(
            purpose=LinkPurpose.IMPLEMENTATION,
            icon="⚙️",
            label="Implementation",
            format_string="- {icon} **{label}**: [[{target_vault}/{target_file}|{display_name}]] "
                         "(Confidence: {confidence}%)"
        )
    }

    @classmethod
    def get_template(cls, purpose: str) -> LinkTemplate:
        """Get template by purpose string"""
        try:
            link_purpose = LinkPurpose(purpose)
            return cls.TEMPLATES[link_purpose]
        except (ValueError, KeyError):
            # Fallback to reference template
            return cls.TEMPLATES[LinkPurpose.REFERENCE]

    @classmethod
    def format_link_entry(cls, target_vault: str, target_file: str,
                         display_name: str, confidence: float,
                         purpose: str = "reference") -> str:
        """Generate formatted link entry using template"""
        template = cls.get_template(purpose)

        return template.format_link(
            icon=template.icon,
            label=template.label,
            target_vault=target_vault,
            target_file=target_file,
            display_name=display_name,
            confidence=int(confidence * 100)
        )


# Template configuration for different link contexts
LINK_INSERTION_CONFIG = {
    "section_markers": [
        "---",
        "## Related Links",
        "## Cross-Vault Links",
        "## References"
    ],
    "fallback_position": "end",  # Where to insert if no markers found
    "separator": "\n"
}