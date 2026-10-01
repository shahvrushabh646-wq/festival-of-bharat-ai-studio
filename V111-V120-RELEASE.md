# Festival of Bharat AI Studio — V111 Merge

This build uses MERGED V2 as the main production baseline and incorporates the useful structural improvements identified in \`-llamacoder (16).zip\` without replacing the working rendering/asset pipeline.

## Integrated from (16)
- stronger asset rights metadata (license URL, attribution, usageAllowed, downloadedAt, asset hash fields)
- research sources and factual notes on generated scripts
- richer QC check fields for codec/FPS/audio/corrupt frames/blank scenes/rights/caption/safe duration
- reel version history model
- optional music-track model

## Deliberately NOT copied
The (16) production-service implementation contains delay-based simulated stages and Math.random-based behavior, so it was not used as the production engine. MERGED V2's real asset/rendering pipeline remains authoritative.

## Validation
- Existing V2 structure preserved
- No fake MP4 path introduced
- Existing browser renderer preserved
- Existing Wikimedia asset download path preserved
- New metadata fields are optional for backward compatibility
