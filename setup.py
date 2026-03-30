"""
setup.py - Dynamic version configuration for getdate-next

Supports setting version via $VERSION environment variable.
Falls back to reading pyproject.toml if not set.
"""
import os
import re
from pathlib import Path


def get_version():
    """Get version from $VERSION env var or pyproject.toml"""
    # Try environment variable first
    version = os.environ.get('VERSION')
    if version:
        return version

    # Fall back to reading from pyproject.toml
    pyproject_path = Path(__file__).parent / 'pyproject.toml'
    with open(pyproject_path) as f:
        content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        if match:
            return match.group(1)

    return '0.1.0'  # Final fallback


from setuptools import setup

setup(version=get_version())
