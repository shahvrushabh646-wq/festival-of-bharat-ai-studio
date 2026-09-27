# Festival of Bharat AI Studio V24 — Performance Memory

V24 adds a local Performance Memory layer to the V23 Daily Autopilot.

## What it does
- Record views, likes, shares, comments, average watch time and Reel duration.
- Label each result with topic, hook style and creative type.
- Store up to the latest 100 result records in the browser's localStorage.
- Analyze averages and top-viewed history.
- Build tomorrow's four creative treatments using the user's own history as a planning signal.
- Does not claim or predict viral performance.
- Human approval remains required.

## Privacy / free mode
Performance data stays in the browser localStorage for this module. No paid analytics API is required.

## V25 — Performance-Directed AI
V25 connects V24 local performance memory to the creative director. Historical results influence practical planning signals for topic, hook family, creative type, target duration, opening treatment and footage allocation. It does not claim to predict virality and does not auto-publish.

## Automation
The Daily 4 Reels workflow runs at 06:00 IST and can also be started manually from GitHub Actions. It supports an optional topic and an optional public MP4 source URL. The pipeline downloads/processes source footage, creates four 1080x1920/30fps MP4 variants, runs a quality gate with one self-re-encode fallback, and uploads the final files plus a production manifest as a 7-day Actions artifact. Instagram audio is added in Instagram after human approval.


Studio Day 1 launch trigger: 2026-09-27 — automated 4-Reel production started.

Production retry trigger: 2026-09-27 — fresh 4-Reel batch requested using latest rights/rate-limit fixes.
