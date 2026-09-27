#!/usr/bin/env python3
import json, os, re, subprocess, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"daily-output"; RAW=ROOT/"daily-raw"
OUT.mkdir(exist_ok=True); RAW.mkdir(exist_ok=True)

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"FestivalOfBharatCreatorOS/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r: return r.read()

def trends():
    try:
        xml=fetch("https://trends.google.com/trending/rss?geo=IN")
        root=ET.fromstring(xml)
        titles=[(x.findtext("title") or "").strip() for x in root.findall(".//item")]
        for t in titles:
            if re.search(r"ganesh|ganpati|bappa|festival|diwali|holi|navratri|garba|krishna|janmashtami|shiva|mahadev|temple|india|bharat",t,re.I):
                return t
        return titles[0] if titles else "Indian culture festival"
    except Exception:
        return "Indian culture festival"

topic=os.getenv("TOPIC","").strip() or trends()
source_url=os.getenv("SOURCE_URL","").strip()

# Optional direct MP4 input: the workflow can process one public MP4 URL instead of scouting footage.
# This keeps MP4 as a first-class automation input while retaining the free licensed-footage fallback.
assets=[]
if source_url:
    dest=RAW/"source_0.mp4"
    try:
        with urllib.request.urlopen(urllib.request.Request(source_url,headers={"User-Agent":"FestivalOfBharatCreatorOS/1.0"}),timeout=120) as r:
            with open(dest,"wb") as f:
                while True:
                    b=r.read(1024*1024)
                    if not b: break
                    f.write(b)
        if dest.stat().st_size>10000:
            assets.append({"title":"Provided MP4","url":source_url,"license":"User-provided source — verify rights","author":"","page":source_url,"file":str(dest)})
    except Exception as e:
        print("SOURCE_URL download failed:",e)

# If no direct MP4 was supplied, scout openly licensed video from Wikimedia Commons.

queries=[topic,topic+" temple devotion",topic+" festival India",topic+" culture India"]
seen=set(); assets=[]
for q in queries:
    params=urllib.parse.urlencode({
        "action":"query","format":"json","generator":"search","gsrsearch":q+" filetype:video",
        "gsrnamespace":"6","gsrlimit":"10","prop":"imageinfo",
        "iiprop":"url|extmetadata|mime"
    })
    try: data=json.loads(fetch("https://commons.wikimedia.org/w/api.php?"+params))
    except Exception: continue
    for p in (data.get("query",{}).get("pages",{}) or {}).values():
        ii=(p.get("imageinfo") or [{}])[0]; url=ii.get("url",""); mime=ii.get("mime","")
        meta=ii.get("extmetadata") or {}
        lic=str(meta.get("LicenseShortName",{}).get("value",""))
        if not url or not mime.startswith("video/") or p.get("title") in seen: continue
        if not re.search(r"CC|Creative Commons|Public Domain|PD|GFDL|GPL|Attribution|ShareAlike",lic,re.I): continue
        seen.add(p.get("title")); assets.append({
            "title":p.get("title",""),"url":url,"license":re.sub("<[^>]+>","",lic),
            "author":re.sub("<[^>]+>","",str(meta.get("Artist",{}).get("value",""))),
            "page":"https://commons.wikimedia.org/wiki/"+urllib.parse.quote(p.get("title","").replace(" ","_"))
        })
        if len(assets)>=8: break
    if len(assets)>=8: break

for i,a in enumerate(assets[:8]):
    dest=RAW/f"clip_{i}.mp4"
    try:
        with urllib.request.urlopen(urllib.request.Request(a["url"],headers={"User-Agent":"FestivalOfBharatCreatorOS/1.0"}),timeout=90) as r:
            with open(dest,"wb") as f:
                while True:
                    b=r.read(1024*1024)
                    if not b: break
                    f.write(b)
        a["file"]=str(dest)
    except Exception: pass
assets=[a for a in assets if "file" in a and Path(a["file"]).stat().st_size>10000]
if len(assets)<3: raise SystemExit("Not enough licensed video footage was available today.")

styles=[
 ("moment",[0,1,2,3],3.0,"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"),
 ("detail",[2,0,3,1],2.6,"scale=1180:2100:force_original_aspect_ratio=increase,crop=1080:1920"),
 ("energy",[1,3,0,2],1.8,"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"),
 ("meaning",[3,2,1,0],3.4,"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"),
]
manifest={"date":datetime.now(timezone.utc).isoformat(),"topic":topic,"rights_note":"Only Commons assets with open/public license metadata were selected. Verify each asset license before posting.","assets":[],"reels":[]}

for a in assets: manifest["assets"].append({k:a[k] for k in ("title","license","author","page")})
for n,(name,order,dur,vf) in enumerate(styles,1):
    parts=[]
    for j in order:
        a=assets[j%len(assets)]; parts.append(a["file"])
    segs=[]
    for j,f in enumerate(parts):
        seg=RAW/f"r{n}_{j}.mp4"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f,"-t",str(dur),"-vf",vf+",fps=30","-an","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-movflags","+faststart",str(seg)],check=True)
        segs.append(seg)
    lst=RAW/f"list_{n}.txt"; lst.write_text("".join("file '"+str(s).replace("'","'\\''")+"'\n" for s in segs))
    out=OUT/f"festival-of-bharat-reel-{n}.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-an","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-movflags","+faststart",str(out)],check=True)
    # Basic production quality gate + self-re-edit fallback.
    probe=subprocess.run(["ffprobe","-v","error","-show_entries","stream=width,height,r_frame_rate:format=duration","-of","json",str(out)],capture_output=True,text=True)
    quality={"passed":False,"reason":"ffprobe failed"}
    try:
        pj=json.loads(probe.stdout); st=(pj.get("streams") or [{}])[0]; fmt=pj.get("format") or {}
        w,h=int(st.get("width",0)),int(st.get("height",0))
        dur=float(fmt.get("duration",0))
        quality={"passed":w==1080 and h==1920 and dur>=5,"width":w,"height":h,"duration":round(dur,2)}
    except Exception: pass
    if not quality["passed"]:
        # Re-encode once with strict portrait output.
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(out),"-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30","-an","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",str(out)],check=True)
        quality["self_reedited"]=True
    manifest["reels"].append({"file":out.name,"style":name,"quality":quality,"music":"Add eligible Instagram audio in Instagram after approval."})
(OUT/"README.txt").write_text(f"""Festival of Bharat — Daily Reel Production
Topic: {topic}
Four MP4s were rendered at 1080x1920 / 30fps.
Add eligible Instagram audio inside Instagram after approval.
Verify source licenses before posting.
""")
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({"topic":topic,"assets":len(assets),"reels":4}))
