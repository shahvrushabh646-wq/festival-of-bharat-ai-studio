export default async function handler(req,res){
  if(req.method!=='POST') return res.status(405).json({error:'POST only'});
  const token=(process.env.GITHUB_TOKEN||process.env.GITHUB_PAT||process.env.GH_TOKEN||'').trim();
  if(!token) return res.status(503).json({ok:false,bridge:'not_configured',error:'GitHub Actions token is missing in Vercel. Configure GITHUB_TOKEN (or GITHUB_PAT) with Actions: Read and write for this repository.'});
  let body={}; try{body=typeof req.body==='string'?JSON.parse(req.body):req.body||{}}catch{}
  const topic=String(body.topic||'').trim();
  const source_url=String(body.source_url||'').trim();
  const edit_request=String(body.edit_request||'').trim();
  const target_reel=Number(body.target_reel)||((edit_request.match(/reel\s*(\d+)/i)||[])[1] ? Number((edit_request.match(/reel\s*(\d+)/i)||[])[1]) : 0);
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
  const payload={ref:'main',inputs:{topic:dispatchTopic,source_url,edit_request,target_reel:target_reel>=1&&target_reel<=4?String(target_reel):''}};
  try{
    const check=await fetch('https://api.github.com/repos/'+owner+'/'+repo+'/actions/workflows/'+workflow,{headers:{'Authorization':`Bearer ${token}`,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'FestivalOfBharatCreatorOS'}});
    if(!check.ok){const data=await check.json().catch(()=>({}));return res.status(check.status).json({ok:false,bridge:'github_rejected',githubStatus:check.status,error:data?.message||'GitHub workflow is not accessible with the configured token.'});}
  }catch(e){return res.status(502).json({ok:false,bridge:'network_error',error:e.message||'GitHub request failed.'});}
  const r=await fetch(`https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`,{method:'POST',headers:{'Authorization':`Bearer ${token}`,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(!r.ok){
    let detail='GitHub rejected the workflow dispatch.';
    try{ const data=await r.json(); if(data?.message) detail=data.message; }catch{}
    const hint=r.status===401||r.status===403?' Check Vercel GITHUB_TOKEN: it must be a GitHub fine-grained token for this repository with Actions = Read and write (and Contents = Read and write if the workflow creates releases/updates repository content).':'';
    return res.status(r.status).json({error:`${detail}${hint}`,githubStatus:r.status});
  }
  let run=null; const dispatchStarted=Date.now();
  for(let attempt=0;attempt<5 && !run;attempt++){
    if(attempt) await new Promise(r=>setTimeout(r,900));
    try{
      const rr=await fetch('https://api.github.com/repos/'+owner+'/'+repo+'/actions/runs?event=workflow_dispatch&per_page=20',{headers:{'Authorization':`Bearer ${token}`,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'FestivalOfBharatCreatorOS'},cache:'no-store'});
      if(rr.ok){const data=await rr.json();const candidates=(data.workflow_runs||[]).filter(x=>x.path&&x.path.endsWith(workflow)&&x.head_branch==='main'&&new Date(x.created_at||0).getTime()>=dispatchStarted-15000);run=candidates.sort((a,b)=>new Date(b.created_at)-new Date(a.created_at))[0]||null;}
    }catch(e){}
  }
  res.status(200).json({ok:true,dispatched:true,message:run?'Production started — GitHub Run #'+run.run_number+' is '+run.status+'.':'Production dispatch accepted by GitHub. Open Production Runs to watch the new run.',run:run?{id:run.id,number:run.run_number,status:run.status,conclusion:run.conclusion,sha:run.head_sha,created_at:run.created_at}:null,target_reel:target_reel||null,actionsUrl:'https://github.com/'+owner+'/'+repo+'/actions/workflows/'+workflow});
}