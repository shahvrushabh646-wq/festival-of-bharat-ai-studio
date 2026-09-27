export default async function handler(req,res){
  if(req.method!=='POST') return res.status(405).json({error:'POST only'});
  const token=process.env.GITHUB_TOKEN;
  if(!token) return res.status(500).json({error:'GITHUB_TOKEN is not configured in Vercel. Add a GitHub fine-grained token with Actions: Read and write permission.'});
  let body={}; try{body=typeof req.body==='string'?JSON.parse(req.body):req.body||{}}catch{}
  const topic=String(body.topic||'').trim();
  const owner='shahvrushabh646-wq', repo='festival-of-bharat-ai-studio', workflow='daily-reels.yml';
  const r=await fetch(`https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`,{
    method:'POST',headers:{'Authorization':`Bearer ${token}`,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'},
    body:JSON.stringify({ref:'main',inputs:{topic}})
  });
  if(!r.ok) return res.status(r.status).json({error:'GitHub could not start the workflow. Check that the token has Actions: Read and write permission.'});
  res.status(200).json({ok:true,actionsUrl:`https://github.com/${owner}/${repo}/actions/workflows/${workflow}`});
}