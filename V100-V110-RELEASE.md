# Festival of Bharat AI Studio — V100→V110 merge

## Compared versions
- \`-llamacoder (13).zip\`
- \`-llamacoder (14).zip\`
- \`Festival-of-Bharat-AI-Studio-MERGED-FINAL.zip\`

## Merge decision
The merged release keeps the real browser renderer, real asset download attempts, rights/QC checks, cloud production bridge, automation and approval workflow from MERGED-FINAL. It incorporates the stronger language/rights/stage data model from version 14 and restores the broader template library (10 templates) from version 14.

## Deliberately not copied
The older 13/14 \`production-service.ts\` simulation-only rendering path was not used as the production engine. Its delay-based processing and placeholder MP4 path would regress the real rendering pipeline.

## Validation
- TypeScript source updated without changing the public production workflow.
- Python cloud scripts remain unchanged from the previously validated merged release.
- Browser rendering remains the single local render implementation.
