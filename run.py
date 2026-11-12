#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Root-level One-Click Launcher for BookVerse AI
Allows running `python run.py` directly from workspace root.
"""
import os
import sys
from pathlib import Path

# Force UTF-8 encoding on standard streams to prevent Windows charmap encoding errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

inner_dir = Path(__file__).resolve().parent / "book_recommendation_system"
if inner_dir.exists():
    os.chdir(inner_dir)
    sys.path.insert(0, str(inner_dir))
    import run
    run.main()
else:
    print(f"Error: Could not locate directory {inner_dir}")
    sys.exit(1)
