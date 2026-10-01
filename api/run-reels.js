export default async function handler(req,res){
 if(req.method!=="POST") return res.status(405).json({error:"POST only"});
 const token=(process.env.GITHUB_TOKEN||process.env.GITHUB_PAT||process.env.GH_TOKEN||"").trim();
 if(!token) return res.status(503).json({ok:false,error:"GitHub Actions token is missing in Vercel."});
 let body={};try{body=typeof req.body==="string"?JSON.parse(req.body):req.body||{}}catch{}
 const owner="shahvrushabh646-wq",repo="festival-of-bharat-ai-studio",workflow="daily-reels.yml";
 const inputs={topic:String(body.topic||""),source_url:String(body.source_url||""),edit_request:String(body.edit_request||""),target_reel:String(body.target_reel||"")};
 const url=`https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`;
 const headers={"Authorization":`Bearer ${token}`,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"FestivalOfBharatCreatorOS"};
 const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json",...headers},body:JSON.stringify({ref:"main",inputs})});
 if(!r.ok)return res.status(r.status).json({ok:false,error:await r.text()});
 return res.status(200).json({ok:true,dispatched:true,message:"Production dispatched to GitHub Actions.",actionsUrl:`https://github.com/${owner}/${repo}/actions/workflows/${workflow}`});
}