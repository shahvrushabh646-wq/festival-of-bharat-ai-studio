import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
const required=['index.html','vercel.json','package.json','.github/workflows/daily-reels.yml','api/run-reels.js','api/status.js','api/batch.js','api/approval.js','scripts/daily_reels.py','scripts/production_hotfix.py'];
for(const f of required) if(!fs.existsSync(f)) throw new Error(`Missing required file: ${f}`);
const html=fs.readFileSync('index.html','utf8');
for(const id of ['makeBtn','planBtn','topic','startMsg','reviewReels','reviewCount','sendEdit']) if(!new RegExp(`id=["']${id}["']`).test(html)) throw new Error(`Missing required DOM id: ${id}`);
for(const f of ['api/run-reels.js','api/status.js','api/batch.js','api/approval.js']){
  const s=fs.readFileSync(f,'utf8'); if(!s.includes('export default')) throw new Error(`Invalid API module: ${f}`);
}
execFileSync('python3',['-m','py_compile','scripts/daily_reels.py','scripts/production_hotfix.py'],{stdio:'inherit'});
console.log('APP BUILD CHECK PASSED');