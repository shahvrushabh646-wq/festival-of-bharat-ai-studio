#!/usr/bin/env python3
"""Production preflight and FFmpeg smoke test.

This script deliberately does not rewrite daily_reels.py. It validates the
actual renderer prerequisites and executes a tiny synthetic vertical concat
using the same FFmpeg filter shape as production.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "daily_reels.py"


def require(cmd):
    if shutil.which(cmd) is None:
        raise SystemExit(f"Production preflight failed: missing {cmd}")


def smoke_test():
    require("ffmpeg")
    require("ffprobe")

    with tempfile.TemporaryDirectory(prefix="fob_ffmpeg_smoke_") as td:
        d = Path(td)
        a = d / "a.mp4"
        b = d / "b.mp4"
        out = d / "concat.mp4"

        base = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i",
        ]
        subprocess.run(
            base + ["color=c=black:s=1080x1920:r=30:d=1.2",
                    "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-threads", "2", str(a)],
            check=True,
        )
        subprocess.run(
            base + ["color=c=white:s=1080x1920:r=30:d=1.2",
                    "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-threads", "2", str(b)],
            check=True,
        )

        fc = (
            "[0:v]settb=AVTB,setpts=PTS-STARTPTS,"
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
            "setsar=1,fps=30,settb=AVTB,setpts=PTS-STARTPTS,"
            "format=yuv420p[v0];"
            "[1:v]settb=AVTB,setpts=PTS-STARTPTS,"
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
            "setsar=1,fps=30,settb=AVTB,setpts=PTS-STARTPTS,"
            "format=yuv420p[v1];"
            "[v0][v1]concat=n=2:v=1:a=0:unsafe=1[v]"
        )

        p = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-filter_threads", "1", "-filter_complex_threads", "1",
                "-i", str(a), "-i", str(b),
                "-filter_complex", fc, "-map", "[v]", "-an",
                "-r", "30", "-s", "1080x1920",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-threads", "2",
                "-fps_mode", "cfr", "-movflags", "+faststart", str(out),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if p.returncode != 0 or not out.exists() or out.stat().st_size < 10000:
            raise SystemExit(
                "FFmpeg concat smoke test failed:\n" + (p.stderr or "")[-3000:]
            )

        probe = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,codec_name",
                "-of", "csv=p=0", str(out),
            ],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

        if probe != "1080,1920,h264":
            raise SystemExit(f"FFmpeg smoke test returned invalid output: {probe}")

        print("FFmpeg smoke test PASSED:", probe)


if not SCRIPT.exists():
    raise SystemExit("Production script missing: scripts/daily_reels.py")

text = SCRIPT.read_text(encoding="utf-8")
for marker in ("def render_reel", "def scout_openverse_topic", "concat=n="):
    if marker not in text:
        raise SystemExit(f"Production preflight failed: missing {marker}")

smoke_test()
print("Production preflight OK: renderer and FFmpeg concat are executable")
