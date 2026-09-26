export default async function handler(req,res){
  try{
    const r=await fetch('https://trends.google.com/trending/rss?geo=IN',{headers:{'user-agent':'Festival-of-Bharat-CreatorOS/1.0'}});
    if(!r.ok) throw new Error('Google Trends '+r.status);
    const xml=await r.text();
    const items=[...xml.matchAll(/<item>([\\s\\S]*?)<\\/item>/g)].slice(0,12).map(m=>{
      const b=m[1], title=(b.match(/<title><!\\[CDATA\\[(.*?)\\]\\]><\\/title>/)||b.match(/<title>(.*?)<\\/title>/)||[])[1]||'';
      const traffic=(b.match(/<ht:approx_traffic>(.*?)<\\/ht:approx_traffic>/)||[])[1]||'';
      return {title:title.replace(/&amp;/g,'&'),traffic};
    }).filter(x=>x.title);
    res.setHeader('Cache-Control','s-maxage=900, stale-while-revalidate=1800');
    return res.status(200).json({region:'IN',items});
  }catch(e){return res.status(502).json({region:'IN',items:[],error:String(e.message||e)})}
}