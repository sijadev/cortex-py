#!/usr/bin/env python3
"""
Setup configuration for Cortex CLI Package
Professional CLI tool for knowledge management and AI-powered analysis
"""

from setuptools import setup, find_packages

def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "Cortex CLI - AI-powered knowledge management tool"

def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "click>=8.0.0",
            "pyyaml>=6.0.0",
            "aiohttp>=3.8.0",
            "watchdog>=2.1.0",
            "rich>=12.0.0",
            "aiofiles>=0.8.0"
        ]

setup(
    name="cortex-cli",
    version="0.1.0",
    author="Simon Janke",
    author_email="simon@sijadev.com",
    description="AI-powered knowledge management and cross-vault linking CLI tool",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/sijadev/cortex-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Researchers", 
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business :: Groupware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "cortex=cortex.cli.main:cli",
        ],
    },
    scripts=[
        "bin/cortex-cmd",
        "bin/cortex-service",
    ],
    include_package_data=True,
    package_data={
        "cortex": [
            "templates/**/*",
            "*.yaml",
            "*.yml"
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/sijadev/cortex-cli/issues",
        "Source": "https://github.com/sijadev/cortex-cli",
        "Documentation": "https://github.com/sijadev/cortex-cli/wiki",
    },
)
