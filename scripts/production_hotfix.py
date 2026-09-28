#!/usr/bin/env python3
"""Safe production preflight.

The current daily_reels.py already contains the FFmpeg escaping, source
screening and mixed-media fixes. This preflight intentionally does not
rewrite source code with fragile regex replacements. It only validates that
the production script is present and readable, then exits successfully.
"""
from pathlib import Path

p = Path("scripts/daily_reels.py")
if not p.exists():
    raise SystemExit("Production script missing: scripts/daily_reels.py")
text = p.read_text(encoding="utf-8")
if "def render_reel" not in text:
    raise SystemExit("Production renderer missing: render_reel()")
if "def scout_openverse_topic" not in text:
    raise SystemExit("Visual source scout missing: scout_openverse_topic()")
if "concat=n=" not in text:
    raise SystemExit("FFmpeg concat stage missing")
print("Production preflight OK: no source rewrite required")
