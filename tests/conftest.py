"""
Global pytest configuration for cortex-py project.
Ensures proper Python path setup for all tests.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add src directory to path for governance modules
src_dir = project_root / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

# Add cortex_neo directory to path
cortex_neo_dir = project_root / "cortex_neo"
if cortex_neo_dir.exists():
    sys.path.insert(0, str(cortex_neo_dir))
