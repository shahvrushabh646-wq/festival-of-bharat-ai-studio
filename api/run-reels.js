export default async function handler(req,res){
  if(req.method!=='POST') return res.status(405).json({error:'POST only'});
  const token=process.env.GITHUB_TOKEN;
  if(!token) return res.status(500).json({error:'GITHUB_TOKEN is not configured in Vercel. Add a GitHub fine-grained token with Actions: Read and write permission.'});
  let body={}; try{body=typeof req.body==='string'?JSON.parse(req.body):req.body||{}}catch{}
  const topic=String(body.topic||'').trim();
  const source_url=String(body.source_url||'').trim();
  const edit_request=String(body.edit_request||'').trim();
  const plan_only=String(body.plan_only||'').toLowerCase()==='true';
  const owner='shahvrushabh646-wq', repo='festival-of-bharat-ai-studio', workflow='daily-reels.yml';
  if(plan_only) return res.status(200).json({ok:true,planOnly:true,message:'Plan only selected. No GitHub Actions production run was started.',planUrl:`https://github.com/${owner}/${repo}/actions/workflows/${workflow}`});
  let dispatchTopic=topic;
  if(edit_request){
    try{
      const rel=await fetch(`https://api.github.com/repos/${owner}/${repo}/releases?per_page=10`,{headers:{'Authorization':`Bearer ${token}`,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'FestivalOfBharatCreatorOS'}});
      const releases=await rel.json();
      const latest=(releases||[]).find(x=>!x.draft&&!x.prerelease&&String(x.tag_name).startsWith('daily-'));
      const manifestAsset=(latest?.assets||[]).find(x=>x.name==='manifest.json');
      if(manifestAsset){
        const mr=await fetch(manifestAsset.url,{headers:{'Authorization':`Bearer ${token}`,'Accept':'application/octet-stream','X-GitHub-Api-Version':'2022-11-28','User-Agent':'FestivalOfBharatCreatorOS'}});
        if(mr.ok){
          const manifest=await mr.json();
          const topics=(manifest.topics||[]).map(x=>x.topic).filter(Boolean).slice(0,4);
          if(topics.length===4) dispatchTopic='EDITTOPICS:'+JSON.stringify(topics);
        }
      }
    }catch(e){}
  }
  const payload={ref:'main',inputs:{topic:dispatchTopic,source_url,edit_request}};
  const r=await fetch(`https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`,{
    method:'POST',headers:{'Authorization':`Bearer ${token}`,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'},
    body:JSON.stringify(payload)
  });
  if(!r.ok){
    let detail='GitHub rejected the workflow dispatch.';
    try{ const data=await r.json(); if(data?.message) detail=data.message; }catch{}
    const hint=r.status===401||r.status===403
      ?' Check Vercel GITHUB_TOKEN: it must be a GitHub fine-grained token for this repository with Actions = Read and write (and Contents = Read and write if the workflow creates releases/updates repository content).'
      :'';
    return res.status(r.status).json({error:`${detail}${hint}`,githubStatus:r.status});
  }
  res.status(200).json({ok:true,actionsUrl:`https://github.com/${owner}/${repo}/actions/workflows/${workflow}`});
}