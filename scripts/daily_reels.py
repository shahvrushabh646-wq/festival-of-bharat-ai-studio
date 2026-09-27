#!/usr/bin/env python3
import json, os, re, subprocess, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"daily-output"; RAW=ROOT/"daily-raw"
OUT.mkdir(exist_ok=True); RAW.mkdir(exist_ok=True)

UA="FestivalOfBharatCreatorOS/2.0"

def fetch(url, timeout=45):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()

def clean_html(s):
    return re.sub("<[^>]+>","",str(s or "")).strip()

def trends():
    try:
        root=ET.fromstring(fetch("https://trends.google.com/trending/rss?geo=IN"))
        titles=[(x.findtext("title") or "").strip() for x in root.findall(".//item")]
        culture=re.compile(r"ganesh|ganpati|bappa|festival|diwali|holi|navratri|garba|krishna|janmashtami|shiva|mahadev|temple|india|bharat|pooja|puja|utsav|mela|heritage|culture",re.I)
        for t in titles:
            if culture.search(t): return t
        return titles[0] if titles else "Indian culture"
    except Exception:
        return "Indian culture"

USEFUL_RULE=("Every Reel must teach, explain, preserve, or give practical cultural context about an Indian "
             "festival, tradition, place, craft, food, history, or cultural practice. Avoid fabricated facts, "
             "empty trend-chasing, copied creator content, and generic filler.")

topic=os.getenv("TOPIC","").strip() or trends()
source_url=os.getenv("SOURCE_URL","").strip()

# Four differentiated, retention-oriented creative directions.
styles=[
 ("moment",[0,1,2,3],2.7,"THE MOMENT","Open with the strongest emotional or human visual."),
 ("detail",[2,0,3,1],2.2,"THE DETAIL","Open on a surprising close-up or cultural detail."),
 ("energy",[1,3,0,2],1.55,"THE ENERGY","Fastest rhythm; movement and peak moment first."),
 ("meaning",[3,2,1,0],3.0,"THE MEANING","Slow the ending and leave viewers with context.")
]

topic_profiles=[
 (r"ganesh|ganpati|bappa", "Ganpati / Ganesh festival", "Why Ganpati celebrations end with Visarjan", "Ganesh Chaturthi celebrates Lord Ganesha and the festival concludes with immersion according to local tradition."),
 (r"holi", "Holi", "Why Holi is more than a colour festival", "Holi is associated with seasonal celebration, community, colour and regional traditions across India."),
 (r"diwali|deepavali", "Diwali", "What the lights of Diwali represent", "Diwali is celebrated across India with regional customs centred on light, community and renewal."),
 (r"navratri|garba", "Navratri / Garba", "Why Garba circles around a central space", "Garba is a community dance tradition strongly associated with Navratri, with regional variations."),
 (r"janmashtami|krishna|dahi handi", "Janmashtami", "Why Krishna Janmashtami is celebrated", "Janmashtami marks the birth of Krishna and is observed through diverse regional devotional traditions."),
 (r"shiva|mahadev|mahashivratri", "Shaiv traditions", "A closer look at Shiva devotion in India", "Shiva worship has many regional forms, expressed through temples, rituals, music and pilgrimage."),
]
def profile(t):
    for pat,name,title,fact in topic_profiles:
        if re.search(pat,t,re.I): return name,title,fact
    return "Bharat culture", f"A closer look at {t}", f"Explore the people, place, tradition or history behind {t}."

culture_name,educational_title,educational_fact=profile(topic)

assets=[]

def add_source_asset(title,url,license_name,author,page,file_path=None,kind="video"):
    assets.append({
        "title":title,"url":url,"license":license_name or "License not displayed",
        "author":author,"page":page,"kind":kind,"rights_review":True,**({"file":file_path} if file_path else {})
    })

# A supplied public MP4 is a supported source, but it is never treated as licensed automatically.
if source_url:
    dest=RAW/"source_0.mp4"
    try:
        data=fetch(source_url,120)
        dest.write_bytes(data)
        if dest.stat().st_size>10000:
            add_source_asset("Provided MP4",source_url,"User-provided source — verify rights","",source_url,str(dest),"video")
    except Exception as e:
        print("SOURCE_URL failed:",e)

# If no usable supplied MP4, scout Wikimedia Commons video + photo assets.
if not any(a.get("file") for a in assets):
    queries=[topic, topic+" temple devotion", topic+" festival India", topic+" culture heritage India"]
    seen=set()
    for q in queries:
        params=urllib.parse.urlencode({
            "action":"query","format":"json","generator":"search",
            "gsrsearch":q,"gsrnamespace":"6","gsrlimit":"15",
            "prop":"imageinfo","iiprop":"url|extmetadata|mime"
        })
        try: data=json.loads(fetch("https://commons.wikimedia.org/w/api.php?"+params))
        except Exception: continue
        for p in (data.get("query",{}).get("pages",{}) or {}).values():
            ii=(p.get("imageinfo") or [{}])[0]
            url=ii.get("url",""); mime=ii.get("mime","")
            meta=ii.get("extmetadata") or {}
            lic=clean_html(meta.get("LicenseShortName",{}).get("value",""))
            title=p.get("title","")
            if not url or title in seen: continue
            if not re.search(r"CC BY|CC BY-SA|CC0|Public Domain|PD|GFDL|GPL|Attribution|ShareAlike",lic,re.I): continue
            kind="video" if mime.startswith("video/") else ("image" if mime.startswith("image/") else "")
            if kind not in ("video","image"): continue
            seen.add(title)
            page="https://commons.wikimedia.org/wiki/"+urllib.parse.quote(title.replace(" ","_"))
            add_source_asset(title,url,lic,clean_html(meta.get("Artist",{}).get("value","")),page,None,kind)
            if len(assets)>=8: break
        if len(assets)>=8: break

# Download and retain only assets that actually arrive.
for i,a in enumerate(assets[:8]):
    dest=RAW/f"source_{i}"+Path(urllib.parse.urlparse(a["url"]).path).suffix
    if dest.suffix.lower() not in (".mp4",".webm",".mov",".mkv",".jpg",".jpeg",".png",".webp",".gif"):
        dest=RAW/f"source_{i}.bin"
    try:
        data=fetch(a["url"],120); dest.write_bytes(data)
        if dest.stat().st_size>10000: a["file"]=str(dest)
    except Exception as e: print("asset download failed:",a["title"],e)
assets=[a for a in assets if a.get("file") and Path(a["file"]).stat().st_size>10000]

def asset_score(a):
    try:
        q=subprocess.run(["ffprobe","-v","error","-show_entries","stream=width,height,duration","-of","json",a["file"]],capture_output=True,text=True)
        j=json.loads(q.stdout); st=(j.get("streams") or [{}])[0]
        w=int(st.get("width",0) or 0); h=int(st.get("height",0) or 0)
        portrait=3 if h>=w else 0
        resolution=min((w*h)/2073600,2.0)
        return portrait + resolution + (1 if a.get("kind")=="video" else 0)
    except Exception:
        return 0
assets=sorted(assets,key=asset_score,reverse=True)
if len(assets)<3: raise SystemExit("Not enough usable licensed footage/photos were available today.")

# Reorder so every Reel can start differently and use the strongest available source first.
assets=assets[:8]
manifest={
 "date":datetime.now(timezone.utc).isoformat(),"topic":topic,"content_rule":USEFUL_RULE,
 "content_angle":educational_title,"educational_context":educational_fact,
 "virality_strategy":"Trend-led topic + immediate hook + four distinct openings + fast first seconds + useful cultural context; virality is not guaranteed.",
 "creator_pack":{"posting_order":["Moment","Detail","Energy","Meaning"],"approval_required":True,"audio_policy":"Add eligible/trending Instagram audio inside Instagram after rights review."},
 "rights_note":"Only footage/photos whose displayed license matches an allowed open/public license pattern are imported. Verify each individual file's license, attribution, share-alike and third-party rights before posting.",
 "rights_review_required":True,"assets":[],"reels":[]
}
for a in assets:
    manifest["assets"].append({k:a.get(k,"") for k in ("title","license","author","page","kind","rights_review")})

def esc_textfile(p):
    return str(p).replace("\\","/").replace(":","\\:")

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def ffmpeg_clip(src,out,dur,index,hook="",label="",context=""):
    ext=Path(src).suffix.lower()
    hook_file=RAW/f"hook_{index}.txt"
    hook_file.write_text(hook,encoding="utf-8")
    label_file=RAW/f"label_{index}.txt"
    label_file.write_text("FESTIVAL OF BHARAT  •  "+label,encoding="utf-8")
    context_file=RAW/f"context_{index}.txt"
    context_file.write_text(context,encoding="utf-8")
    hf=esc_textfile(hook_file); lf=esc_textfile(label_file); cf=esc_textfile(context_file)
    base="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,eq=contrast=1.06:saturation=1.08:brightness=0.01,unsharp=5:5:0.35:5:5:0"
    if ext in (".jpg",".jpeg",".png",".webp"):
        base="scale=1188:2112:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0018,1.09)':d=81:s=1080x1920:fps=30,eq=contrast=1.06:saturation=1.08:brightness=0.01,unsharp=5:5:0.35:5:5:0"
        inp=["-loop","1","-i",src]
    else:
        inp=["-i",src]
    draw=(
        f"drawtext=fontfile={FONT_REG}:textfile='{lf}':fontcolor=white:fontsize=26:"
        f"x=64:y=92:box=1:boxcolor=black@0.34:boxborderw=14:"
        f"shadowcolor=black@0.65:shadowx=2:shadowy=2,"
        f"drawtext=fontfile={FONT}:textfile='{hf}':fontcolor=white:fontsize=54:"
        f"x=64:y=h-390:box=1:boxcolor=black@0.48:boxborderw=24:"
        f"line_spacing=8:shadowcolor=black@0.8:shadowx=3:shadowy=3,"
        f"drawtext=fontfile={FONT_REG}:textfile='{cf}':fontcolor=white:fontsize=30:"
        f"x=64:y=h-210:box=1:boxcolor=black@0.34:boxborderw=16:"
        f"shadowcolor=black@0.65:shadowx=2:shadowy=2"
    )
    vf=base+","+draw
    cmd=["ffmpeg","-y","-loglevel","error",*inp,"-t",str(dur),"-vf",vf,
         "-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",
         "-movflags","+faststart",str(out)]
    subprocess.run(cmd,check=True)

for n,(name,order,dur,label,direction) in enumerate(styles,1):
    segs=[]
    hook_list=[
        f"{educational_title}.",
        f"Look closer: {culture_name} has more to the story.",
        f"Before you scroll: one useful fact about {culture_name}.",
        f"What this tradition means — in one quick Reel."
    ]
    for j,pos in enumerate(order):
        a=assets[pos%len(assets)]
        seg=RAW/f"r{n}_{j}.mp4"
        seg_hook=hook_list[n-1] if j==0 else ""
        ffmpeg_clip(a["file"],seg,dur,j+n*10,seg_hook,label,educational_fact if j==0 else "")
        segs.append(seg)

    transition=0.24
    inputs=[]
    for seg in segs: inputs += ["-i",str(seg)]
    filters=[]
    for i in range(len(segs)):
        filters.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}]")
    current="[v0]"
    elapsed=dur-transition
    for i in range(1,len(segs)):
        outv=f"[x{i}]"
        filters.append(f"{current}[v{i}]xfade=transition=fade:duration={transition}:offset={elapsed:.2f}{outv}")
        current=outv
        elapsed += dur-transition
    total=dur*4-transition*3
    end_text=RAW/f"end_{n}.txt"
    end_text.write_text("SAVE • SHARE • FOLLOW  |  FESTIVAL OF BHARAT",encoding="utf-8")
    ef=esc_textfile(end_text)
    filters.append(f"{current}fade=t=in:st=0:d=0.18,format=yuv420p[pre]")
    filters.append(f"color=c=black:s=1080x1920:r=30:d=1.2,drawtext=fontfile={FONT}:textfile='{ef}':fontcolor=white:fontsize=42:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.15:boxborderw=22[end]")
    filters.append(f"[pre][end]xfade=transition=fade:duration=0.28:offset={total-0.28:.2f},format=yuv420p[vout]")
    out=OUT/f"festival-of-bharat-reel-{n}.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error",*inputs,"-filter_complex",";".join(filters),
                     "-map","[vout]","-an","-c:v","libx264","-preset","veryfast","-crf","19",
                     "-pix_fmt","yuv420p","-movflags","+faststart",str(out)],check=True)

    probe=subprocess.run(["ffprobe","-v","error","-show_entries","stream=width,height,r_frame_rate:format=duration,size","-of","json",str(out)],capture_output=True,text=True)
    quality={"passed":False}
    try:
        pj=json.loads(probe.stdout); st=(pj.get("streams") or [{}])[0]; fmt=pj.get("format") or {}
        w,h=int(st.get("width",0)),int(st.get("height",0)); d=float(fmt.get("duration",0))
        fps=st.get("r_frame_rate","")
        quality={"passed":w==1080 and h==1920 and d>=5 and fps=="30/1","width":w,"height":h,"duration":round(d,2),"fps":fps}
    except Exception: pass
    if not quality["passed"]:
        tmp=OUT/f"fix-{n}.mp4"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(out),
                        "-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                        "-an","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
                        "-movflags","+faststart",str(tmp)],check=True)
        tmp.replace(out); quality["self_reedited"]=True

    caption = f"{educational_title} — a quick cultural context from Bharat. Save this Reel for later and share it with someone who loves Indian culture."
    hashtags = ["#FestivalOfBharat","#Bharat","#IndianCulture", "#IndianTraditions"]
    if re.search(r"ganesh|ganpati|bappa", topic, re.I): hashtags += ["#Ganpati","#GaneshChaturthi","#Mumbai"]
    elif re.search(r"holi", topic, re.I): hashtags += ["#Holi","#HoliFestival"]
    elif re.search(r"diwali|deepavali", topic, re.I): hashtags += ["#Diwali","#Deepavali"]
    elif re.search(r"navratri|garba", topic, re.I): hashtags += ["#Navratri","#Garba"]
    elif re.search(r"janmashtami|krishna", topic, re.I): hashtags += ["#Janmashtami","#Krishna"]
    elif re.search(r"shiva|mahadev", topic, re.I): hashtags += ["#Mahadev","#Mahashivratri"]
    cover = [educational_title, "LOOK CLOSER", "ONE USEFUL FACT", "THE MEANING"][n-1]
    manifest["reels"].append({
        "file":out.name,"style":name,"creative_label":label,"direction":direction,
        "hook":hook_list[n-1],"useful_context":educational_fact,"quality":quality,
        "cover_text":cover,"caption":caption,"hashtags":hashtags,"cta":"Save this Reel and share it with someone who loves Bharat.",
        "content_pillar":culture_name,
        "editing":"Portrait-aware source scoring + cinematic crop/zoom + subtle grade + branded strip + hook/context overlays + smooth crossfades + branded CTA end card + 1080x1920/30fps.",
        "music":"Search Instagram for an eligible/trending audio that fits the mood; add it inside Instagram after approval."
    })

(OUT/"README.txt").write_text(f"""Festival of Bharat — Daily 4-Reel Autopilot
Topic: {topic}
Angle: {educational_title}
Context: {educational_fact}

4 MP4s: 1080x1920 / 9:16 / 30fps.
Strategy: trend-led + useful cultural information + four different openings.
Virality is optimized for, not guaranteed.
Rights: verify every displayed license and attribution/share-alike requirement before posting.
Music: add eligible/trending Instagram audio in Instagram after human approval.
""")
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(OUT/"creator-pack.json").write_text(json.dumps({
 "topic":topic,"content_angle":educational_title,"context":educational_fact,
 "reels":[{"file":r["file"],"hook":r["hook"],"cover_text":r["cover_text"],"caption":r["caption"],"hashtags":r["hashtags"],"cta":r["cta"],"content_pillar":r["content_pillar"],"music":r["music"]} for r in manifest["reels"]]
},ensure_ascii=False,indent=2))
print(json.dumps({"topic":topic,"assets":len(assets),"reels":4,"angle":educational_title}))
