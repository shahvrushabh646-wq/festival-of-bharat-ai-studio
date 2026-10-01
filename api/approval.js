export default async function handler(req,res){
  const owner='shahvrushabh646-wq', repo='festival-of-bharat-ai-studio', path='status/approvals.json', branch='status';
  const raw=\`https://raw.githubusercontent.com/\${owner}/\${repo}/\${branch}/\${path}?x=\${Date.now()}\`;
  const token=(process.env.GITHUB_TOKEN||process.env.GITHUB_PAT||process.env.GH_TOKEN||'').trim();
  if(req.method==='GET'){
    try{const r=await fetch(raw,{cache:'no-store',headers:{'User-Agent':'FestivalOfBharatCreatorOS'}}); if(!r.ok)return res.status(200).json({approvals:{}}); return res.status(200).json(await r.json());}
    catch(e){return res.status(200).json({approvals:{},error:e.message||'approval lookup failed'});}
  }
  if(req.method!=='POST') return res.status(405).json({error:'GET or POST only'});
  if(!token) return res.status(503).json({ok:false,error:'GitHub token is missing. Configure GITHUB_TOKEN in Vercel.'});
  let body={}; try{body=typeof req.body==='string'?JSON.parse(req.body):req.body||{}}catch{}
  const date=String(body.date||'').trim(), reel=Number(body.reel), decision=String(body.decision||'').trim().toLowerCase();
  if(!/^\\d{4}-\\d{2}-\\d{2}$/.test(date)||!Number.isInteger(reel)||reel<1||reel>4||!['approved','rejected'].includes(decision)) return res.status(400).json({ok:false,error:'date, reel (1-4), and decision (approved/rejected) are required.'});
  const api=\`https://api.github.com/repos/\${owner}/\${repo}/contents/\${path}?ref=\${branch}\`;
  const headers={'Authorization':\`Bearer \${token}\`,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'FestivalOfBharatCreatorOS'};
  let current={approvals:{}}, sha;
  try{const r=await fetch(api,{headers}); if(r.ok){const d=await r.json(); sha=d.sha; current=JSON.parse(Buffer.from(d.content.replace(/\\n/g,''),'base64').toString('utf8'));}}
  catch(e){}
  current.approvals=current.approvals||{};
  current.approvals[date]=current.approvals[date]||{};
  current.approvals[date][String(reel)]={decision,at:new Date().toISOString()};
  const content=Buffer.from(JSON.stringify(current,null,2)+'\\n').toString('base64');
  const payload={message:\`\${decision==='approved'?'Approve':'Reject'} Reel \${reel} for \${date}\`,content,branch}; if(sha)payload.sha=sha;
  const r=await fetch(api,{method:'PUT',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const d=await r.json().catch(()=>({}));
  if(!r.ok)return res.status(r.status).json({ok:false,error:d?.message||'GitHub could not save approval.'});
  res.setHeader('Cache-Control','no-store'); return res.status(200).json({ok:true,date,reel,decision,record:current.approvals[date][String(reel)]});
}