export default async function handler(req,res){
 const topic=String(req.query?.topic||'Bharat culture').trim().slice(0,100);
 const clean=topic.replace(/\s+/g,' ');
 const packs=[
  {id:1,angle:'The Moment',goal:'Emotion-first story using the strongest human or arrival visual.',pace:'cinematic build',rule:'Open with the strongest emotional frame; finish on a memorable detail.'},
  {id:2,angle:'The Detail',goal:'Curiosity-first story built around a close detail people usually miss.',pace:'slow → reveal',rule:'Start tight, then reveal the wider cultural context.'},
  {id:3,angle:'The Energy',goal:'Momentum-first story using movement, crowds, rhythm and action.',pace:'fast cuts',rule:'Lead with motion and keep visual changes frequent.'},
  {id:4,angle:'The Meaning',goal:'Culture-first story using architecture, ritual, people and quiet moments.',pace:'measured',rule:'Prioritize respectful context and a strong closing thought.'}
 ];
 res.setHeader('Cache-Control','s-maxage=300, stale-while-revalidate=600');
 return res.status(200).json({date:new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',dateStyle:'full'}).format(new Date()),topic:clean,format:'1080×1920 • 9:16 • 30fps',count:4,packs});
}