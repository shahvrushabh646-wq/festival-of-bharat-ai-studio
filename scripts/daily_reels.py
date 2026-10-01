#!/usr/bin/env python3
import json, os, re, subprocess, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"daily-output"; RAW=ROOT/"daily-raw"
OUT.mkdir(exist_ok=True); RAW.mkdir(exist_ok=True)
IST=timezone(timedelta(hours=5,minutes=30))
TODAY=datetime.now(IST).strftime("%Y-%m-%d")
UA="FestivalOfBharatCreatorOS/4.0"
TOPIC=os.getenv("TOPIC","").strip()
SOURCE_URL=os.getenv("SOURCE_URL","").strip()
EDIT_REQUEST=os.getenv("EDIT_REQUEST","").strip()
try: TARGET_REEL=int(os.getenv("TARGET_REEL","0") or 0)
except: TARGET_REEL=0

def fetch(url,timeout=45):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()

def run(cmd):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if p.returncode: raise RuntimeError((p.stderr or "")[-3000:])
    return p.stdout

def trends():
    try:
        x=fetch("https://trends.google.com/trending/rss?geo=IN").decode("utf-8","ignore")
        titles=re.findall(r"<title>(?:<!\\[CDATA\\[)?(.*?)(?:\\]\\]>)?</title>",x,re.I)
        for t in titles:
            if re.search(r"ganesh|ganpati|diwali|holi|navratri|krishna|shiva|temple|festival|culture|heritage|craft|food",t,re.I):
                return re.sub("<.*?>","",t).strip()
    except Exception: pass
    return "Indian culture"

TOPICS=[
 ("Ganesh Chaturthi","Ganesh festival","Why Ganpati celebrations end with Visarjan",["Ganesh Chaturthi","Ganesh idol India","Ganesh visarjan"]),
 ("Indian Temple Architecture","Temple heritage","What makes an Indian temple more than a place of worship",["Indian temple architecture","Indian temple heritage","temple India"]),
 ("Indian Traditional Craft","Traditional craft","The story behind an Indian traditional craft",["Indian handicraft","Indian handloom","Indian artisan"]),
 ("Regional Indian Food","Food culture","The cultural story behind a regional Indian food",["Indian regional food","traditional Indian food","Indian cuisine culture"]),
 ("Indian Heritage","Heritage","A closer look at India's living heritage",["Indian heritage","Indian fort India","Indian palace India"]),
 ("Navratri / Garba","Festival tradition","Why Garba circles around a central space",["Navratri Garba","Garba Gujarat","Navratri India"]),
 ("Janmashtami","Krishna tradition","Why Krishna Janmashtami is celebrated",["Janmashtami India","Dahi Handi","Krishna temple India"]),
 ("Holi","Festival tradition","Why Holi is more than a colour festival",["Holi India","Holika Dahan","Holi celebration India"]),
 ("Diwali","Festival tradition","What the lights of Diwali represent",["Diwali India","Deepavali festival","Diwali diya"])
]

def choose():
    pool=[]
    if TOPIC: pool.append(TOPIC)
    pool.append(trends())
    pool += [x[0] for x in TOPICS]
    result=[];seen=set()
    for raw in pool:
        match=next((x for x in TOPICS if x[0].lower() in raw.lower() or raw.lower() in x[0].lower()),None)
        if match is None: match=("Bharat culture",raw,f"A closer look at {raw}",[raw+" India",raw+" culture India"])
        key=match[0].lower()
        if key not in seen:
            result.append(match);seen.add(key)
        if len(result)==4: break
    return result[:4]

daily=choose()

def commons_search(q):
    url="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({
      "action":"query","format":"json","origin":"*","generator":"search","gsrsearch":q,
      "gsrnamespace":"6","gsrlimit":"5","prop":"imageinfo","iiprop":"url|extmetadata|mime","iiurlwidth":"1080"})
    data=json.loads(fetch(url))
    out=[]
    for p in (data.get("query",{}).get("pages",{}) or {}).values():
        ii=(p.get("imageinfo") or [{}])[0]; meta=ii.get("extmetadata") or {}
        if not ii.get("url") or not str(ii.get("mime","")).startswith("image/"): continue
        lic=str(meta.get("LicenseShortName",{}).get("value") or meta.get("License",{}).get("value") or "")
        if not re.search(r"CC|Creative Commons|Public Domain|PD|GFDL|Attribution|ShareAlike",lic,re.I): continue
        out.append({"title":p.get("title",""),"url":ii["url"],"preview":ii.get("thumburl") or ii["url"],
                    "page":"https://commons.wikimedia.org/wiki/"+urllib.parse.quote(str(p.get("title","")).replace(" ","_")),
                    "creator":str(meta.get("Artist",{}).get("value") or ""), "license":lic})
    return out

def download_assets(queries,reel):
    assets=[]
    for qi,q in enumerate(queries):
        try:
            for j,a in enumerate(commons_search(q)[:2]):
                path=RAW/f"reel_{reel:02d}_{qi}_{j}.jpg"
                try:
                    path.write_bytes(fetch(a["url"],60))
                    if path.stat().st_size>5000:
                        a["file"]=str(path);assets.append(a)
                except Exception: pass
        except Exception: pass
        if len(assets)>=6: break
    if not assets: raise RuntimeError(f"Reel {reel}: no licensed Wikimedia image could be downloaded")
    return assets

def render_reel(reel,item,assets):
    clips=[]
    captions=[
      "STOP SCROLLING: "+item[2],
      "LOOK CLOSER • "+item[1],
      item[0]+" has a story worth knowing.",
      "This is the detail most quick videos skip.",
      "Save this cultural detail for later.",
      "FOLLOW FESTIVAL OF BHARAT"
    ]
    for i in range(6):
        src=assets[i%len(assets)]["file"]; clip=OUT/f"_r{reel}_{i}.mp4"
        text=clips_text=Path(OUT/f"_r{reel}_{i}.txt"); text.write_text(captions[i],encoding="utf-8")
        duration=2.3
        vf=f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0008,1.06)':d=69:s=1080x1920:fps=30,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile='{text}':fontcolor=white:fontsize=48:borderw=4:bordercolor=black@0.85:x=(w-text_w)/2:y=h-420"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-i",src,"-t",str(duration),"-vf",vf,"-an","-r","30","-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(clip)])
        text.unlink(missing_ok=True);clips.append(clip)
    final=OUT/f"reel_{reel:02d}.mp4"
    inputs=[];parts=[]
    for i,c in enumerate(clips):
        inputs += ["-i",str(c)]
        parts.append(f"[{i}:v]setpts=PTS-STARTPTS,scale=1080:1920,setsar=1,fps=30,format=yuv420p[v{i}]")
    fc=";".join(parts)+";"+"".join(f"[v{i}]" for i in range(len(clips)))+f"concat=n={len(clips)}:v=1:a=0[v]"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y",*inputs,"-filter_complex",fc,"-map","[v]","-r","30","-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(final)])
    for c in clips: Path(c).unlink(missing_ok=True)
    probe=json.loads(run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(final)]))
    v=next(x for x in probe["streams"] if x["codec_type"]=="video")
    if int(v.get("width",0))!=1080 or int(v.get("height",0))!=1920 or v.get("codec_name")!="h264": raise RuntimeError(f"Reel {reel}: QC failed")
    return {"reel":reel,"file":final.name,"topic":item[0],"pillar":item[1],"title":item[2],
            "duration":float(probe["format"].get("duration",0)),"quality":{"pass":True,"width":1080,"height":1920,"codec":"h264","fps":30},
            "assets":[{k:a.get(k) for k in ["title","page","creator","license"]} for a in assets]}

for p in OUT.glob("reel_*.mp4"): p.unlink(missing_ok=True)
for p in OUT.glob("_*.mp4"): p.unlink(missing_ok=True)
reels=[]
for i,item in enumerate(daily,1):
    if TARGET_REEL and i!=TARGET_REEL:
        old=OUT/f"reel_{i:02d}.mp4"
        if not old.exists(): raise RuntimeError("Targeted re-edit requires previous release files in daily-output")
        continue
    assets=download_assets(item[3],i)
    reels.append(render_reel(i,item,assets))

if len(reels)!=4 and not TARGET_REEL: raise RuntimeError("Expected exactly four rendered Reels")
manifest={"generated_at":datetime.now(timezone.utc).isoformat(),"daily_key":TODAY,"run_number":os.getenv("GITHUB_RUN_NUMBER",""),
"trend":trends(),"topics":[{"reel":i+1,"topic":x[0],"pillar":x[1],"title":x[2]} for i,x in enumerate(daily)],
"reels":reels,"rights_policy":"Wikimedia Commons assets are retained with source page, creator and license records; verify current license before posting.",
"format":"1080x1920 9:16 H.264 30fps","music_policy":"Master is rendered without commercial music; add eligible Instagram/Edits audio after approval."}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
(OUT/"creator-pack.json").write_text(json.dumps({"captions":[r["title"]+" — save and share this cultural detail." for r in reels],"approval":"Human approval required before publishing."},indent=2),encoding="utf-8")
(OUT/"README.txt").write_text("Four professional 1080x1920 H.264 Reels. Human approval required. Verify each source licence before posting.",encoding="utf-8")
print("BUILT",len(reels),"REELS")
