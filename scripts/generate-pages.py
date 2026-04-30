#!/usr/bin/env python3
"""
Backward-compatible entry point for older instructions.

The site now uses lossless WebP assets, so this wrapper delegates to
scripts/generate-webp.py.
"""

from pathlib import Path
import runpy
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
runpy.run_path(str(SCRIPT_DIR / "generate-webp.py"), run_name="__main__")
