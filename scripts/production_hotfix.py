#!/usr/bin/env python3
"""Safe production preflight. It intentionally makes no source-code mutations."""
from pathlib import Path
import ast
root=Path(__file__).resolve().parents[1]
ast.parse((root/"scripts/daily_reels.py").read_text(encoding="utf-8"))
print("production hotfix/preflight OK")
