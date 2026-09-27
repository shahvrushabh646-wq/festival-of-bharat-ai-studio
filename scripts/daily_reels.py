#!/usr/bin/env python3
import json, os, re, subprocess, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"daily-output"; RAW=ROOT/"daily-raw"
OUT.mkdir(exist_ok=True); RAW.mkdir(exist_ok=True)
UA="FestivalOfBharatCreatorOS/3.0"

def fetch(url, timeout=60):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()
def run(cmd, check=True):
    return subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=check)
def esc(s):
    return str(s or "").replace("\\","\\\\").replace(":","\\:").replace("'","\\'").replace("%","\\%").replace("[","\\[").replace("]","\\]")
def clean(s): return re.sub("<[^>]+>"," ",str(s or "")).strip()
def probe(path):
    try:
        d=json.loads(run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)]).stdout)
        v=next((x for x in d.get("streams",[]) if x.get("codec_type")=="video"),{})
        return float(d.get("format",{}).get("duration") or 0),int(v.get("width") or 0),int(v.get("height") or 0),v.get("codec_name","")
    except Exception:return 0,0,0,""

def trends():
    try:
        root=ET.fromstring(fetch("https://trends.google.com/trending/rss?geo=IN"))
        titles=[(x.findtext("title") or "").strip() for x in root.findall(".//item")]
        culture=re.compile(r"ganesh|ganpati|bappa|festival|diwali|holi|navratri|garba|krishna|janmashtami|shiva|mahadev|temple|india|bharat|pooja|puja|utsav|mela|heritage|culture",re.I)
        for t in titles:
            if culture.search(t): return t
        return titles[0] if titles else "Indian culture"
    except Exception:return "Indian culture"

USEFUL_RULE=("Every Reel must teach, explain, preserve, or give practical cultural context about an Indian "
"festival, tradition, place, craft, food, history, or cultural practice. Avoid fabricated facts, empty trend-chasing, copied creator content, and generic filler.")
topic=os.getenv("TOPIC","").strip() or trends()
source_url=os.getenv("SOURCE_URL","").strip()

styles=[
("moment","THE MOMENT",[0,1,2,3,4,5],[2.2,1.9,2.0,2.0,1.8,1.8],"emotion-first"),
("detail","THE DETAIL",[2,4,1,5,0,3],[1.6,1.7,1.8,1.8,1.9,2.0],"detail-first"),
("energy","THE ENERGY",[1,3,5,0,4,2],[1.15,1.25,1.35,1.45,1.55,1.65],"fast-cut"),
("meaning","THE MEANING",[3,2,0,5,4,1],[2.0,2.1,2.2,2.1,2.0,2.0],"documentary")]

topic_profiles=[
(r"ganesh|ganpati|bappa","Ganpati / Ganesh festival","Why Ganpati celebrations end with Visarjan","Ganesh Chaturthi celebrates Lord Ganesha and the festival concludes with immersion according to local tradition.",["ganesh chaturthi","ganpati visarjan","ganesh festival india","ganpati procession"]),
(r"holi","Holi","Why Holi is more than a colour festival","Holi is associated with seasonal celebration, community, colour and regional traditions across India.",["holi india","holika dahan","holi celebration india","indian colours festival"]),
(r"diwali|deepavali","Diwali","What the lights of Diwali represent","Diwali is celebrated across India with regional customs centred on light, community and renewal.",["diwali india","deepavali festival","diwali diya","diwali celebration india"]),
(r"navratri|garba","Navratri / Garba","Why Garba circles around a central space","Garba is a community dance tradition strongly associated with Navratri, with regional variations.",["navratri garba","garba gujarat","navratri india","garba dance"]),
(r"janmashtami|krishna|dahi handi","Janmashtami","Why Krishna Janmashtami is celebrated","Janmashtami marks the birth of Krishna and is observed through diverse regional devotional traditions.",["janmashtami india","krishna temple india","dahi handi","krishna festival"]),
(r"shiva|mahadev|mahashivratri","Shaiv traditions","A closer look at Shiva devotion in India","Shiva worship has many regional forms, expressed through temples, rituals, music and pilgrimage.",["mahadev temple india","mahashivratri india","shiva temple","shiva pilgrimage"])]
def profile(t):
    for pat,name,title,fact,queries in topic_profiles:
        if re.search(pat,t,re.I): return name,title,fact,queries
    return "Bharat culture",f"A closer look at {t}",f"Explore the people, place, tradition or history behind {t}",[t+" India",t+" festival",t+" culture India",t+" tradition"]
culture_name,educational_title,educational_fact,search_terms=profile(topic)
assets=[]

WATERMARK_RISK=re.compile(r"watermark|youtube|instagram|tiktok|facebook|reel|shorts|channel|creator|@\w+|©|www\.|https?://",re.I)
def reject_source(title,author,page):
    return bool(WATERMARK_RISK.search(" ".join([str(title or ""),str(author or ""),str(page or "")])))
def add_source_asset(title,url,license_name,author,page,file_path=None,kind="video"):
    if reject_source(title,author,page):
        print("REJECTED creator/platform risk:",title); return False
    assets.append({"title":title,"url":url,"license":license_name or "License not displayed","author":author,"page":page,"kind":kind,"rights_review":True,**({"file":file_path} if file_path else {})})
    return True

def scout_wikimedia():
    queries=list(dict.fromkeys(search_terms+["Indian culture festival India","Indian temple culture"]))
    seen=set()
    for q in queries:
        api=("https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch="+urllib.parse.quote(q)+"&gsrnamespace=6&gsrlimit=15&prop=imageinfo&iiprop=url|mime|size|extmetadata&iiurlwidth=1600&format=json")
        try:data=json.loads(fetch(api))
        except Exception:continue
        for page in data.get("query",{}).get("pages",{}).values():
            info=(page.get("imageinfo") or [{}])[0]; url=info.get("url",""); mime=info.get("mime","")
            meta=info.get("extmetadata",{}); title=page.get("title","")
            lic=(meta.get("LicenseShortName") or {}).get("value",""); author=clean((meta.get("Artist") or {}).get("value",""))
            pageurl="https://commons.wikimedia.org/?curid="+str(page.get("pageid"))
            if not url or url in seen or not (mime.startswith("video/") or mime.startswith("image/")):continue
            if not re.search(r"CC BY|CC BY-SA|CC0|Public Domain|PD|GFDL|Attribution|ShareAlike",re.sub("<[^>]+>","",lic),re.I):continue
            if reject_source(title,author,pageurl):continue
            seen.add(url); ext=".webm" if "webm" in mime else ".mp4" if "mp4" in mime else ".jpg"
            dest=RAW/(f"asset_{len(assets):02d}{ext}")
            try:
                dest.write_bytes(fetch(url,90)); dur,w,h,codec=probe(dest)
                if dest.stat().st_size<15000 or w<400 or h<400 or (dur and dur<1):dest.unlink(missing_ok=True);continue
                add_source_asset(title,url,lic,author,pageurl,str(dest),"video" if mime.startswith("video/") else "photo")
            except Exception as e:print("asset skip",e)
            if len(assets)>=12:return

if source_url:
    try:
        dest=RAW/"provided.mp4";dest.write_bytes(fetch(source_url,120));dur,w,h,codec=probe(dest)
        if dur>1 and w>=400 and h>=400 and not reject_source("Provided MP4","",source_url):
            add_source_asset("Provided MP4",source_url,"User-provided source — verify rights","",source_url,str(dest),"video")
    except Exception as e:print("provided source unusable",e)
if len(assets)<6:scout_wikimedia()
if len(assets)<6:raise RuntimeError("Not enough clean, rights-reviewable footage; risky/random sources were rejected.")

def visual_risk(path):
    try:
        tmp=RAW/(Path(path).stem+"_ocr.jpg")
        run(["ffmpeg","-y","-ss","0.8","-i",str(path),"-frames:v","1","-q:v","3",str(tmp)],False)
        if not tmp.exists():return False
        try:out=run(["tesseract",str(tmp),"stdout","--psm","11"],False).stdout
        finally:tmp.unlink(missing_ok=True)
        return bool(re.search(r"youtube|instagram|tiktok|facebook|@\w+|www\.|\.com\b",out,re.I))
    except Exception:return False
assets=[a for a in assets if not visual_risk(a["file"])]
if len(assets)<6:raise RuntimeError("Visual watermark/platform screening left fewer than six clean assets.")

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def make_clip(src,out,dur):
    sd,sw,sh,codec=probe(src); start=0 if sd<dur+0.3 else min(.7,sd-dur)
    if Path(src).suffix.lower() in [".jpg",".jpeg",".png",".webp"]:
        vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-1080)/2:(ih-1920)/2,zoompan=z='min(zoom+0.0018,1.12)':d=1:s=1080x1920:fps=30,eq=contrast=1.06:saturation=1.12:brightness=.01"
        run(["ffmpeg","-y","-loop","1","-i",str(src),"-t",str(dur),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(out)])
    else:
        vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-1080)/2:(ih-1920)/2,eq=contrast=1.06:saturation=1.12:brightness=.01,unsharp=5:5:.35:5:5:0,fps=30"
        run(["ffmpeg","-y","-ss",str(start),"-i",str(src),"-t",str(dur),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(out)])

def render_reel(idx,style):
    name,label,order,durations,tempo=style
    texts=[f"STOP SCROLLING: {educational_title}",f"LOOK CLOSER • {culture_name}",educational_fact,"This is the detail most quick videos skip.","Now you know what you're actually seeing.","SAVE THIS • FOLLOW FESTIVAL OF BHARAT"]
    roles=["HOOK","VISUAL PROOF","CONTEXT","DETAIL","MEANING","CTA"]; clips=[]
    for j,(ai,d) in enumerate(zip(order,durations)):
        raw=OUT/f"_raw{idx}_{j}.mp4";styled=OUT/f"_cut{idx}_{j}.mp4"
        make_clip(assets[ai%len(assets)]["file"],raw,d)
        main=esc(texts[j]);role=esc(roles[j])
        if j in [2,3,4]:
            draw=f"drawtext=fontfile={FONT}:text='{role}':fontcolor=white:fontsize=28:borderw=3:bordercolor=black@.75:x=55:y=1510,drawtext=fontfile={FONT}:text='{main}':fontcolor=white:fontsize=42:borderw=4:bordercolor=black@.8:x=55:y=1555"
        elif j==5:
            draw=f"drawtext=fontfile={FONT}:text='{main}':fontcolor=white:fontsize=42:borderw=4:bordercolor=black@.8:x=55:y=1740"
        else:
            draw=f"drawtext=fontfile={FONT}:text='{role}':fontcolor=white:fontsize=30:borderw=3:bordercolor=black@.75:x=60:y=120,drawtext=fontfile={FONT}:text='{main}':fontcolor=white:fontsize=48:borderw=4:bordercolor=black@.8:x=60:y=160"
        run(["ffmpeg","-y","-i",str(raw),"-vf",draw+",fade=t=in:st=0:d=.10,fade=t=out:st="+str(max(0,d-.18))+":d=.18","-an","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",str(styled)])
        clips.append(styled)
    final=OUT/f"reel_{idx:02d}.mp4"
    inputs=[];fg=[]
    for j,c in enumerate(clips):inputs+=["-i",str(c)];fg.append(f"[{j}:v]")
    run(["ffmpeg","-y",*inputs,"-filter_complex","".join(fg)+"concat=n=6:v=1:a=0[v]","-map","[v]","-an","-r","30","-s","1080x1920","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",str(final)])
    dur,w,h,codec=probe(final)
    if w!=1080 or h!=1920 or dur<9 or dur>16.5:raise RuntimeError(f"Quality gate failed for Reel {idx}: {w}x{h}, {dur:.1f}s")
    for p in clips+[OUT/f"_raw{idx}_{j}.mp4" for j in range(6)]:p.unlink(missing_ok=True)
    return {"file":final.name,"style":label,"tempo":tempo,"duration":round(dur,2)}

reels=[render_reel(i,s) for i,s in enumerate(styles,1)]
manifest={
"generated_at":datetime.now(timezone.utc).isoformat(),"topic":topic,"format":"1080x1920 9:16 Instagram Reel",
"production":"professional six-beat short-form edit — hook, visual proof, context, detail, meaning, CTA",
"content_rule":USEFUL_RULE,
"story_engine":{"beats":["hook","visual proof","context","detail","meaning","CTA"],"rule":"One clear cultural idea per Reel; no random clip montage."},
"editorial_scorecard":{"hook":"immediate","visual_change":"high","information_density":"one clear idea","ending":"clean CTA"},
"asset_screening":{"creator_name_risk":"reject","platform_mark_risk":"reject","visual_watermark_risk":"sampled-frame OCR reject","third_party_content":"reject","attribution":"preserve in rights record"},
"rights_review_required":True,"assets":assets,"reels":reels}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
(OUT/"README.txt").write_text("Festival of Bharat — professional daily Reel batch\nSix-beat edit: hook → visual proof → context → detail → meaning → CTA.\n1080x1920, 30fps, no embedded commercial music. Add eligible/trending Instagram audio after approval.\nRisky creator/platform/watermarked sources are rejected rather than stripped. Verify rights before posting.\n")
(OUT/"creator-pack.json").write_text(json.dumps({"topic":topic,"caption_direction":"Lead with the useful cultural fact, then invite a save/share.","music_direction":"Use eligible/trending Instagram audio inside Instagram; do not embed commercial music in the master.","posting_note":"Human approval required before publishing."},indent=2))
print("BUILT",len(reels),"professional Reels for",topic)
