export default function handler(req,res){
  res.setHeader("Cache-Control","no-store");
  res.status(200).json({
    ok:true,
    app:"Festival of Bharat AI Studio",
    runtime:"vercel",
    time:new Date().toISOString()
  });
}
