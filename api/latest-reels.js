export default async function handler(req,res){
  try{
    const r=await fetch("https://api.github.com/repos/shahvrushabh646-wq/festival-of-bharat-ai-studio/releases?per_page=10",{
      headers:{"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"FestivalOfBharatCreatorOS"}
    });
    if(!r.ok) return res.status(r.status).json({error:"Unable to read daily Reel releases"});
    const releases=await r.json();
    const latest=releases.find(x=>!x.draft && !x.prerelease && String(x.tag_name).startsWith("daily-"));
    if(!latest) return res.status(200).json({ready:false});
    res.setHeader("Cache-Control","s-maxage=300, stale-while-revalidate=900");
    res.status(200).json({
      ready:true,
      tag:latest.tag_name,
      date:latest.published_at,
      title:latest.name,
      url:latest.html_url,
      assets:(latest.assets||[]).filter(a=>/\.mp4$/i.test(a.name)).map(a=>({name:a.name,size:a.size,download_url:a.browser_download_url}))
    });
  }catch(e){res.status(500).json({error:e.message||"release lookup failed"});}
}