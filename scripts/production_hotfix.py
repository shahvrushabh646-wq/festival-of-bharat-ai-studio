#!/usr/bin/env python3
"""Idempotent production safety hotfixes.
The script must never fail merely because a hotfix was already applied.
"""
from pathlib import Path
import re

p=Path("scripts/daily_reels.py")
s=p.read_text(encoding="utf-8")

# Escape characters meaningful to FFmpeg drawtext. Replace the whole esc()
# implementation rather than depending on an exact previous version.
esc_re=re.compile(r"def esc\(s\):\n(?:    .*\n)+?def clean\(s\):",re.M)
esc_block='''def esc(s):
    # Escape characters that are meaningful inside an FFmpeg drawtext filter.
    return (str(s or "").replace("\\\\","\\\\\\\\").replace("'","\\\\'")
            .replace(":","\\\\:").replace(",","\\\\,").replace(";","\\\\;")
            .replace("%","\\\\%").replace("[","\\\\[").replace("]","\\\\]"))
def clean(s):'''
s,n=esc_re.subn(esc_block,s,count=1)
if n==0:
    raise SystemExit("Could not locate esc()/clean() block safely")

# Never treat a normal https landing-page URL as a watermark.
risk_re=re.compile(r'WATERMARK_RISK=re\.compile\(r".*?"\,re\.I\)\ndef reject_source\(title,author,page\):\n(?:    .*\n){1,3}',re.S)
risk_block='''WATERMARK_RISK=re.compile(r"watermark|youtube|instagram|tiktok|facebook|vimeo|dailymotion|@\\w+|©|\\bwww\\.",re.I)
def reject_source(title,author,page):
    metadata=" ".join([str(title or ""),str(author or "")])
    return bool(WATERMARK_RISK.search(metadata))
'''
s,n=risk_re.subn(risk_block,s,count=1)
if n==0:
    raise SystemExit("Could not locate watermark filter safely")

p.write_text(s,encoding="utf-8")
print("Production hotfixes applied successfully")
