export default async function handler(req,res){
  try{
    const r=await fetch("https://api.github.com/repos/shahvrushabh646-wq/festival-of-bharat-ai-studio/releases?per_page=10",{
      headers:{"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"FestivalOfBharatCreatorOS"}
    });
    if(!r.ok) return res.status(r.status).json({ready:false,error:"Unable to read releases"});
    const releases=await r.json();
    const latest=(releases||[]).find(x=>!x.draft&&!x.prerelease&&String(x.tag_name).startsWith("daily-"));
    if(!latest) return res.status(200).json({ready:false,reels:[]});
    const assets=Object.fromEntries((latest.assets||[]).map(a=>[a.name,a.browser_download_url]));
    const readJson=async(name)=>{
      const u=assets[name]; if(!u) return null;
      const x=await fetch(u,{headers:{"User-Agent":"FestivalOfBharatCreatorOS"}});
      return x.ok?x.json():null;
    };
    const manifest=await readJson("manifest.json");
    if(!manifest) return res.status(200).json({ready:false,reels:[]});
    // Do not display an older successful release while the same run is still
    // executing or has failed. A stale batch is worse than showing no batch.
    try{
      const sr=await fetch("https://raw.githubusercontent.com/shahvrushabh646-wq/festival-of-bharat-ai-studio/status/status/status.json?x="+Date.now(),{cache:"no-store"});
      if(sr.ok){
        const live=await sr.json();
        const liveRun=String(live.run_number||"");
        const batchRun=String(manifest.run_number||"");
        if(batchRun && liveRun===batchRun && ["failed","running"].includes(String(live.phase||""))){
          return res.status(200).json({ready:false,stale:true,reels:[],error:"Current production run is not ready yet."});
        }
      }
    }catch(e){}
    const pack=await readJson("creator-pack.json");
    const rights={};
    for(let i=1;i<=4;i++){
      const rec=await readJson(`07-rights-${String(i).padStart(2,"0")}.json`);
      if(rec?.reel) rights[rec.reel]=rec.assets||[];
    }
    const topics=manifest.daily_topics||[];
    const reels=(manifest.reels||[]).map((r,i)=>{
      const t=topics[i]||{};
      return {
        ...r,
        topic:r.topic||t.topic||"",
        pillar:r.pillar||t.pillar||"",
        title:r.title||t.title||`Reel ${i+1}`,
        hook:r.hook||t.hook,
        caption:r.caption||t.caption,
        cover_text:r.cover_text||t.cover_text,
        fact:t.fact||t.fact,
        music_direction:r.music_direction||t.music_direction,
        sensitivity:r.sensitivity||t.sensitivity,
        videoUrl:r.file?assets[r.file]:undefined,
        coverUrl:r.cover_file?assets[`covers/${r.cover_file}`]||assets[r.cover_file]:undefined,
        decision:"pending",
        assets:rights[r.reel]||[]
      };
    });
    res.setHeader("Cache-Control","no-store");
    return res.status(200).json({ready:reels.length===4&&!manifest.plan_only,planOnly:Boolean(manifest.plan_only),date:manifest.daily_key,generatedAt:manifest.generated_at,reels,pack,manifest,releaseUrl:latest.html_url});
  }catch(e){return res.status(500).json({ready:false,error:e.message||"batch lookup failed"})}
}