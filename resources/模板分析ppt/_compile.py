#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Helper script to compile this project."""
import os
import sys
from pathlib import Path

# Set UTF-8 encoding
os.environ['PYTHONUTF8'] = '1'

# Get the project directory (where this script is)
project_dir = Path(__file__).parent.resolve()
infra_dir = project_dir.parent.parent

# Add compile_ncd.py location to path
sys.path.insert(0, str(infra_dir))

# Add scripts to path
scripts_path = infra_dir / "nc_compilations" / "provisions" / "scripts"
if scripts_path.exists():
    sys.path.insert(0, str(scripts_path))

# Import and run
from compile_ncd import compile_project
compile_project(str(project_dir))

