#!/usr/bin/env python3
"""
Test für Keyword-Extraktion Fix
"""

import pytest
import sys

sys.path.append("/Users/simonjanke/Projects/cortex-py/src")

from src.governance.data_governance import DataGovernanceEngine


def test_keyword_extraction():
    """Test der korrigierten Keyword-Extraktion"""
    engine = DataGovernanceEngine()

    content = "Dies ist ein Test für Python development mit machine learning und api integration"
    keywords = engine._extract_keywords_from_content(content)

    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert "python" in keywords
    assert "development" in keywords
