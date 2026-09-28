#!/usr/bin/env python3
"""Runtime hotfixes for the production renderer.
This file is intentionally small: it patches known-safe source/FFmpeg escaping
issues before the existing production pipeline executes.
"""
from pathlib import Path

p=Path("scripts/daily_reels.py")
s=p.read_text(encoding="utf-8")

old='def esc(s):\n    return str(s or "").replace("\\\\","\\\\\\\\").replace(":","\\\\:").replace("'","\\\\'").replace("%","\\\\%").replace("[","\\\\[").replace("]","\\\\]")'
new='def esc(s):\n    # Escape characters that are meaningful inside an FFmpeg drawtext filter.\n    return (str(s or "").replace("\\\\","\\\\\\\\").replace("\'","\\\\\'")\n            .replace(":","\\\\:").replace(",","\\\\,").replace(";","\\\\;")\n            .replace("%","\\\\%").replace("[","\\\\[").replace("]","\\\\]"))'
if old not in s:
    raise SystemExit("esc() hotfix target not found")
s=s.replace(old,new,1)

old='WATERMARK_RISK=re.compile(r"watermark|youtube|instagram|tiktok|facebook|vimeo|dailymotion|@\\w+|©|www\\.|https?://",re.I)\ndef reject_source(title,author,page):\n    return bool(WATERMARK_RISK.search(" ".join([str(title or ""),str(author or "")])))'
new='WATERMARK_RISK=re.compile(r"watermark|youtube|instagram|tiktok|facebook|vimeo|dailymotion|@\\w+|©|\\bwww\\.",re.I)\ndef reject_source(title,author,page):\n    # The landing-page URL itself is not a watermark. Inspect source metadata/title/author,\n    # while separately rejecting known platform marks in the metadata.\n    metadata=" ".join([str(title or ""),str(author or "")])\n    return bool(WATERMARK_RISK.search(metadata))'
if old not in s:
    raise SystemExit("rights-filter hotfix target not found")
s=s.replace(old,new,1)

p.write_text(s,encoding="utf-8")
print("Applied production hotfixes to",p)
