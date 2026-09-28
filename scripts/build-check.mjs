import fs from 'node:fs';

// Vercel build validation must be self-contained in the Node build runtime.
// Python/FFmpeg production checks belong to GitHub Actions, not Vercel.
const required = [
  'index.html',
  'vercel.json',
  'package.json',
  '.github/workflows/daily-reels.yml',
  'api/run-reels.js',
  'api/status.js',
  'api/batch.js',
  'api/approval.js',
  'scripts/daily_reels.py',
  'scripts/production_hotfix.py'
];

for (const file of required) {
  if (!fs.existsSync(file)) throw new Error('Missing required file: ' + file);
}

const html = fs.readFileSync('index.html', 'utf8');
for (const id of ['makeBtn','planBtn','topic','startMsg','reviewReels','reviewCount','sendEdit']) {
  if (!html.includes('id="' + id + '"') && !html.includes("id='" + id + "'")) {
    throw new Error('Missing required DOM id: ' + id);
  }
}

for (const file of ['api/run-reels.js','api/status.js','api/batch.js','api/approval.js']) {
  const source = fs.readFileSync(file, 'utf8');
  if (!source.includes('export default')) throw new Error('Invalid API module: ' + file);
}

const production = fs.readFileSync('scripts/daily_reels.py', 'utf8');
for (const marker of ['def render_reel', 'def arrange_shots', 'set_render_step', 'TEMPLATES = {']) {
  if (!production.includes(marker)) throw new Error('Production marker missing: ' + marker);
}

console.log('APP BUILD CHECK PASSED');
