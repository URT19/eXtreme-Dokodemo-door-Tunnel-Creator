#!/usr/bin/env python3
"""Launcher when the package sits next to this file (dev / before install)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from exrelay.__main__ import main

if __name__ == "__main__":
    main()
