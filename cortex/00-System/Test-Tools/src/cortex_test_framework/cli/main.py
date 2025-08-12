#!/usr/bin/env python3
"""
Main CLI entry point for Cortex Test Framework
"""

import click
from .ai_link_advisor import main as ai_advisor_main
from .health_check import main as health_check_main


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Cortex Test Framework - Testing and validation tools for Cortex AI Knowledge Management System"""
    pass


# Add subcommands
main.add_command(ai_advisor_main, name='ai-advisor')
main.add_command(health_check_main, name='health-check')


if __name__ == "__main__":
    main()