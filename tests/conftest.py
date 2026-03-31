"""
Pytest configuration for outbid-dirigent tests.

This file sets up the Python path so tests can import the source code
without needing to install the package.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Mock the version for tests (since package isn't installed)
import outbid_dirigent
outbid_dirigent.__version__ = "test"
