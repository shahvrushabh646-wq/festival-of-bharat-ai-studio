# Festival of Bharat AI Studio — Merged Production Edition

This edition combines the newer React/TypeScript production studio with the previous Festival of Bharat Creator OS backend.

## Two production paths

### 1. Browser production / preview
- React production dashboard
- Four reel angles
- Six-scene storyboard
- Wikimedia image collection
- Rights metadata
- Canvas 1080x1920 rendering
- WebM recording with MP4 conversion attempt
- QC and approval/re-edit flow
- Local persistence

### 2. Cloud / 24×7 production
The previous working production system is preserved under:
- \`scripts/daily_reels.py\`
- \`api/run-reels.js\`
- \`api/batch.js\`
- \`api/scout.js\`
- \`api/status.js\`
- \`api/approval.js\`
- \`.github/workflows/daily-reels.yml\`
- \`.github/workflows/24x7-watchdog.yml\`

The dashboard's **Run 4 Reels** button dispatches the GitHub Actions production pipeline through \`/api/run-reels\`.

## Cloud requirements
Configure a Vercel \`GITHUB_TOKEN\`/\`GITHUB_PAT\`/\`GH_TOKEN\` with the repository permissions required by the existing workflow. The GitHub Actions workflow needs the media tools used by \`daily_reels.py\`, including FFmpeg/ffprobe.

## Important
No fake MP4 path should be treated as a completed render. The browser renderer only marks a render complete after a real Blob is produced. The cloud pipeline validates rendered media with ffprobe before publishing.

## Validation
- \`npm run build:check\`
- \`npm run validate:py\`
- \`npm run build\`
