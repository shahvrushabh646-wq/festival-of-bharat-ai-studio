#!/usr/bin/env python3
import json, os, re, subprocess, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
import textwrap

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"daily-output"; RAW=ROOT/"daily-raw"
OUT.mkdir(exist_ok=True); RAW.mkdir(exist_ok=True)
# Clear previous generated media/stage files so stale batches can never be published.
for p in OUT.glob('*.mp4'): p.unlink(missing_ok=True)
if (OUT/'stages').exists():
    for p in (OUT/'stages').glob('*.json'): p.unlink(missing_ok=True)
UA="FestivalOfBharatCreatorOS/3.0"

def fetch(url, timeout=60):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()
def run(cmd, check=True):
    return subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=check)
def esc(s):
    return str(s or "").replace("\\","\\\\").replace(":","\\:").replace("'","\\'").replace("%","\\%").replace("[","\\[").replace("]","\\]")
def clean(s): return re.sub("<[^>]+>"," ",str(s or "")).strip()
def fit_text(s,width=30): return '\\n'.join(textwrap.wrap(str(s or ''),width=width,break_long_words=False,break_on_hyphens=False))
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
user_topic=os.getenv("TOPIC","").strip()
trend_topic=trends()
today_key=datetime.now(timezone.utc).strftime('%Y-%m-%d')

topic_profiles=[
(r"ganesh|ganpati|bappa","Ganpati / Ganesh festival","Why Ganpati celebrations end with Visarjan","Ganesh Chaturthi celebrates Lord Ganesha and the festival concludes with immersion according to local tradition.",["ganesh chaturthi","ganpati visarjan","ganesh festival india","ganpati procession"]),
(r"holi","Holi","Why Holi is more than a colour festival","Holi is associated with seasonal celebration, community, colour and regional traditions across India.",["holi india","holika dahan","holi celebration india","indian colours festival"]),
(r"diwali|deepavali","Diwali","What the lights of Diwali represent","Diwali is celebrated across India with regional customs centred on light, community and renewal.",["diwali india","deepavali festival","diwali diya","diwali celebration india"]),
(r"navratri|garba","Navratri / Garba","Why Garba circles around a central space","Garba is a community dance tradition strongly associated with Navratri, with regional variations.",["navratri garba","garba gujarat","navratri india","garba dance"]),
(r"janmashtami|krishna|dahi handi","Janmashtami","Why Krishna Janmashtami is celebrated","Janmashtami marks the birth of Krishna and is observed through diverse regional devotional traditions.",["janmashtami india","krishna temple india","dahi handi","krishna festival"]),
(r"shiva|mahadev|mahashivratri","Shaiv traditions","A closer look at Shiva devotion in India","Shiva worship has many regional forms, expressed through temples, rituals, music and pilgrimage.",["mahadev temple india","mahashivratri india","shiva temple","shiva pilgrimage"]),
(r"temple|mandir","Indian temples","What makes an Indian temple more than a place of worship","Indian temples can also preserve architecture, sculpture, ritual practice and local history.",["indian temple architecture","temples india","ancient temple india","indian temple culture"]),
(r"craft|handloom|weaving|pottery","Indian crafts","The story behind an Indian traditional craft","Traditional crafts preserve regional materials, techniques, livelihoods and cultural identity.",["indian handicraft","indian handloom","traditional craft india","indian artisan"]),
(r"food|cuisine|dish|street food","Indian food culture","The cultural story behind a regional Indian food","Regional food traditions reflect local ingredients, climate, communities and long-standing practices.",["indian regional food","traditional indian food","indian cuisine culture","indian street food"]),
(r"heritage|fort|palace|architecture","Indian heritage","A closer look at India's living heritage","Indian heritage sites connect architecture, local history, craftsmanship and community memory.",["indian heritage site","indian fort architecture","indian palace india","bharat heritage"])
]
def profile(t):
    for pat,name,title,fact,queries in topic_profiles:
        if re.search(pat,t,re.I): return name,title,fact,queries
    return "Bharat culture",f"A closer look at {t}",f"Explore the people, place, tradition or history behind {t}",[t+" India",t+" culture India",t+" tradition",t+" heritage"]

def normalized_key(t):
    return re.sub(r"[^a-z0-9]+"," ",t.lower()).strip()

def choose_four_topics():
    # One daily topic pool, then four genuinely different editorial pillars.
    # A user-supplied topic is used as Reel 1; the other three are selected from different pillars.
    candidates=[]
    if user_topic:
        candidates.append(user_topic)
    if trend_topic and normalized_key(trend_topic) not in [normalized_key(x) for x in candidates]:
        candidates.append(trend_topic)
    evergreen=[
        "Indian temple architecture",
        "Indian traditional craft",
        "Regional Indian food culture",
        "Indian heritage",
        "Indian festival tradition",
        "Indian ritual and custom",
        "Indian folk art",
        "Indian architecture"
    ]
    offset=int(today_key.replace('-','')) % len(evergreen)
    rotated=evergreen[offset:]+evergreen[:offset]
    candidates += [x for x in rotated if normalized_key(x) not in [normalized_key(y) for y in candidates]]
    chosen=[]
    used_names=set()
    for c in candidates:
        name, title, fact, queries=profile(c)
        key=name.lower()
        if key not in used_names:
            chosen.append({"topic":c,"pillar":name,"title":title,"fact":fact,"queries":queries})
            used_names.add(key)
        if len(chosen)>=4: break
    # Guarantee four different pillars even if the trend is repetitive.
    if len(chosen)<4:
        fallback=["Indian temple architecture","Indian traditional craft","Regional Indian food culture","Indian heritage"]
        for c in fallback:
            name,title,fact,queries=profile(c)
            if name.lower() not in used_names:
                chosen.append({"topic":c,"pillar":name,"title":title,"fact":fact,"queries":queries})
                used_names.add(name.lower())
            if len(chosen)>=4: break
    return chosen[:4]

daily_topics=choose_four_topics()
source_url=os.getenv("SOURCE_URL","").strip()

STAGES=OUT/"stages"; STAGES.mkdir(exist_ok=True)
def stage(name,data):
    (STAGES/f"{name}.json").write_text(json.dumps(data,indent=2,ensure_ascii=False))

stage("01-trend",{
    "status":"complete",
    "daily_plan":"four_distinct_topics",
    "trend_source":"Google Trends India RSS",
    "user_topic":user_topic or None,
    "trend_topic":trend_topic,
    "topics":[{"reel":i+1,"topic":x["topic"],"pillar":x["pillar"],"title":x["title"]} for i,x in enumerate(daily_topics)]
})
stage("02-strategy",{
    "status":"complete",
    "objective":"Create four useful Indian-culture Reels with four different topics and pillars",
    "diversity_rule":"No two Reels in the same daily batch may use the same topic or editorial pillar",
    "audience":"Instagram users interested in Indian culture",
    "retention":"visual change every beat",
    "cta":"save/share/follow"
})
for i,item in enumerate(daily_topics,1):
    stage(f"03-research-{i:02d}",{
        'status':'research_gate','reel':i,'topic':item['topic'],'fact':item['fact'],
        'verification_required':True,
        'rule':'Verify factual cultural claims before publishing; preserve supporting source records.'
    })
    stage(f"03-idea-{i:02d}",{
        "status":"complete","reel":i,"topic":item["topic"],"pillar":item["pillar"],
        "title":item["title"],"core_idea":item["fact"],"rule":"one clear cultural idea per Reel"
    })
    stage(f"04-script-{i:02d}",{
        "status":"complete","reel":i,"topic":item["topic"],"beats":[
            {"time":"0-2s","role":"HOOK","text":f"STOP SCROLLING: {item['title']}"},
            {"time":"2-4s","role":"VISUAL PROOF","text":f"LOOK CLOSER • {item['pillar']}"},
            {"time":"4-7s","role":"CONTEXT","text":item["fact"]},
            {"time":"7-10s","role":"DETAIL","text":"This is the detail most quick videos skip."},
            {"time":"10-12s","role":"MEANING","text":"Now you know what you're actually seeing."},
            {"time":"12-14s","role":"CTA","text":"SAVE THIS • FOLLOW FESTIVAL OF BHARAT"}
        ]
    })
    stage(f"05-storyboard-{i:02d}",{
        "status":"complete","reel":i,"topic":item["topic"],"format":"9:16 vertical",
        "beats":["hook","proof","context","detail","meaning","CTA"],
        "visual_direction":"cinematic realistic Indian culture; original editorial treatment; no random montage"
    })
assets_by_reel={}
instagram_refs=[
 {"type":"explore","url":"https://www.instagram.com/explore/","use":"trend discovery"},
 {"type":"hashtag","url":"https://www.instagram.com/explore/tags/indianculture/","use":"culture patterns"},
 {"type":"hashtag","url":"https://www.instagram.com/explore/tags/indianfestivals/","use":"festival patterns"},
 {"type":"hashtag","url":"https://www.instagram.com/explore/tags/ganeshchaturthi/","use":"Ganpati patterns"}
]
pinterest_refs=[
 {"type":"search","url":"https://www.pinterest.com/search/pins/?q=indian%20culture%20reels","use":"visual composition and cultural inspiration"},
 {"type":"search","url":"https://www.pinterest.com/search/pins/?q=indian%20festival%20aesthetic","use":"festival visual language"},
 {"type":"search","url":"https://www.pinterest.com/search/pins/?q=indian%20heritage%20design","use":"heritage design and typography"}
]
canva_refs=[
 {"type":"source","url":"https://www.canva.com/","use":"eligible Reel layouts, typography and graphics"},
 {"type":"license","url":"https://www.canva.com/en_in/policies/content-license-agreement/","use":"license verification before Canva content use"}
]

stage("05a-instagram-intelligence",{
    "status":"reference_only","platform":"Instagram","sources":instagram_refs,
    "analyze":["hook","opening visual","pacing","text","cover","topic angle","editing pattern","audio direction"],
    "rule":"Instagram references guide original production; arbitrary creator Reels are not downloaded or reused without permission/license."
})
stage("05b-visual-intelligence",{
 "status":"reference_only",
 "sources":{
  "Instagram":["hooks","opening visual","pacing","text","cover","editing pattern","audio direction"],
  "Pinterest":["composition","visual mood","colour","typography","cultural design references"],
  "Canva":["eligible Reel layouts","typography","graphics","transitions","licensed Free/Pro content where applicable"]
 },
 "rule":"References guide original Festival of Bharat production; arbitrary creator media is not downloaded or reposted.",
 "canva_license_gate":"Verify content source and applicable Canva license before use; Popular Music is outside the Canva Content License Agreement."
})


WATERMARK_RISK=re.compile(r"watermark|youtube|instagram|tiktok|facebook|vimeo|dailymotion|@\w+|©|www\.|https?://",re.I)
def reject_source(title,author,page):
    return bool(WATERMARK_RISK.search(" ".join([str(title or ""),str(author or "")])))

def add_source_asset(pool,title,url,license_name,author,page,file_path=None,kind="video"):
    if reject_source(title,author,page):
        print("REJECTED creator/platform risk:",title); return False
    pool.append({"title":title,"url":url,"license":license_name or "License not displayed","author":author,
                 "page":page,"kind":kind,"rights_review":True,**({"file":file_path} if file_path else {})})
    return True

def scout_topic(topic_item, reel_no):
    pool=[]
    queries=topic_item["queries"]
    seen=set()
    for q in list(dict.fromkeys(queries)):
        import time; time.sleep(0.8)
        api=("https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch="+urllib.parse.quote(q)+
             "&gsrnamespace=6&gsrlimit=12&prop=imageinfo&iiprop=url|mime|size|extmetadata&iiurlwidth=1600&format=json")
        try:data=json.loads(fetch(api))
        except Exception as e:
            print("Wikimedia search failed",q,e); continue
        for page in data.get("query",{}).get("pages",{}).values():
            info=(page.get("imageinfo") or [{}])[0]
            url=(info.get("thumburl") if info.get("mime","").startswith("image/") and info.get("thumburl") else info.get("url",""))
            mime=info.get("mime","")
            meta=info.get("extmetadata",{})
            title=page.get("title","")
            lic=clean((meta.get("LicenseShortName") or {}).get("value",""))
            author=clean((meta.get("Artist") or {}).get("value",""))
            pageurl="https://commons.wikimedia.org/?curid="+str(page.get("pageid"))
            if not url or url in seen or not (mime.startswith("video/") or mime.startswith("image/")): continue
            if not re.search(r"CC BY|CC BY-SA|CC0|Public Domain|PD|GFDL|Attribution|ShareAlike",re.sub("<[^>]+>","",lic),re.I): continue
            if reject_source(title,author,pageurl): continue
            seen.add(url)
            ext=".webm" if "webm" in mime else ".mp4" if "mp4" in mime else ".jpg"
            dest=RAW/(f"reel{reel_no}_asset{len(pool):02d}{ext}")
            try:
                dest.write_bytes(fetch(url,90))
                dur,w,h,codec=probe(dest)
                if dest.stat().st_size<15000 or w<400 or h<400 or (dur and dur<1):
                    dest.unlink(missing_ok=True); continue
                add_source_asset(pool,title,url,lic,author,pageurl,str(dest),"video" if mime.startswith("video/") else "photo")
            except Exception as e:
                print("asset skip",e)
            if len(pool)>=8: return pool
    return pool

def visual_risk(path):
    try:
        tmp=RAW/(Path(path).stem+"_ocr.jpg")
        run(["ffmpeg","-y","-ss","0.8","-i",str(path),"-frames:v","1","-q:v","3",str(tmp)],False)
        if not tmp.exists(): return False
        try: out=run(["tesseract",str(tmp),"stdout","--psm","11"],False).stdout
        finally: tmp.unlink(missing_ok=True)
        return bool(re.search(r"youtube|instagram|tiktok|facebook|vimeo|dailymotion|@\w+",out,re.I))
    except Exception: return False

for reel_no,item in enumerate(daily_topics,1):
    pool=scout_topic(item,reel_no)
    pool=[a for a in pool if not visual_risk(a["file"])]
    if len(pool)<6:
        raise RuntimeError(f"Reel {reel_no} ({item['topic']}) has only {len(pool)} clean visual assets; production stops instead of mixing unrelated content.")
    assets_by_reel[reel_no]=pool[:8]
    stage(f"06-footage-{reel_no:02d}",{"status":"complete","reel":reel_no,"topic":item["topic"],"asset_count":len(assets_by_reel[reel_no]),"assets":assets_by_reel[reel_no]})
    stage(f"07-rights-{reel_no:02d}",{"status":"complete","reel":reel_no,"topic":item["topic"],"gate":"reject risky creator/platform/watermarked sources",
           "assets":[{"title":a["title"],"license":a["license"],"author":a["author"],"page":a["page"],"rights_review":True} for a in assets_by_reel[reel_no]]})

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def make_clip(src,out,dur):
    sd,sw,sh,codec=probe(src); start=0 if sd<dur+0.3 else min(.7,sd-dur)
    if Path(src).suffix.lower() in [".jpg",".jpeg",".png",".webp"]:
        vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-1080)/2:(ih-1920)/2,zoompan=z='min(zoom+0.0018,1.12)':d=1:s=1080x1920:fps=30,eq=contrast=1.06:saturation=1.12:brightness=.01"
        run(["ffmpeg","-y","-loop","1","-i",str(src),"-t",str(dur),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(out)])
    else:
        vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-1080)/2:(ih-1920)/2,eq=contrast=1.06:saturation=1.12:brightness=.01,unsharp=5:5:.35:5:5:0,fps=30"
        run(["ffmpeg","-y","-ss",str(start),"-i",str(src),"-t",str(dur),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(out)])

def quality_check(path):
    dur,w,h,codec=probe(path)
    checks={"resolution":w==1080 and h==1920,"duration":9<=dur<=16.5,"codec":codec=="h264"}
    return {"pass":all(checks.values()),"checks":checks,"duration":round(dur,2),"width":w,"height":h,"codec":codec}

def render_reel(idx,style,item,assets):
    name,label,order,durations,tempo=style
    texts=[f"STOP SCROLLING: {item['title']}",f"LOOK CLOSER • {item['pillar']}",item["fact"],
           "This is the detail most quick videos skip.","Now you know what you're actually seeing.",
           "SAVE THIS • FOLLOW FESTIVAL OF BHARAT"]
    roles=["HOOK","VISUAL PROOF","CONTEXT","DETAIL","MEANING","CTA"]; clips=[]
    for j,(ai,d) in enumerate(zip(order,durations)):
        raw=OUT/f"_raw{idx}_{j}.mp4"; styled=OUT/f"_cut{idx}_{j}.mp4"
        make_clip(assets[ai%len(assets)]["file"],raw,d)
        main=esc(fit_text(texts[j],30 if j in [2,3,4] else 25)); role=esc(roles[j])
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
    for j,c in enumerate(clips): inputs += ["-i",str(c)]; fg.append(f"[{j}:v]")
    run(["ffmpeg","-y",*inputs,"-filter_complex","".join(fg)+"concat=n=6:v=1:a=0[v]","-map","[v]","-an","-r","30","-s","1080x1920","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",str(final)])
    q=quality_check(final)
    if not q["pass"]:
        print("QUALITY FAIL -> AUTO RE-EDIT",idx,q)
        alt=styles[idx%len(styles)]
        if alt[1]==label: raise RuntimeError("Automatic re-edit exhausted")
        return render_reel(idx,alt,item,assets)
    dur,w,h,codec=probe(final)
    result={"file":final.name,"reel":idx,"topic":item["topic"],"pillar":item["pillar"],"title":item["title"],
            "style":label,"tempo":tempo,"duration":round(dur,2),"quality":q}
    for p in clips+[OUT/f"_raw{idx}_{j}.mp4" for j in range(6)]: p.unlink(missing_ok=True)
    return result

reels=[]
for i,(item,style) in enumerate(zip(daily_topics,styles),1):
    reels.append(render_reel(i,style,item,assets_by_reel[i]))

for i,(item,reel) in enumerate(zip(daily_topics,reels),1):
    stage(f"08-edit-{i:02d}",{"status":"complete","reel":i,"topic":item["topic"],"format":"1080x1920","fps":30,"audio":"none","result":reel})
    stage(f"09-quality-{i:02d}",{"status":"complete","reel":i,"topic":item["topic"],"quality":reel["quality"]})
    stage(f"10-re-edit-{i:02d}",{"status":"complete","reel":i,"rule":"failed quality checks automatically trigger an alternate creative edit"})
    stage(f"11-caption-cover-{i:02d}",{"status":"complete","reel":i,"topic":item["topic"],
        "caption":f"{item['title']} — a useful detail from {item['pillar']}. Save this Reel for later and share it with someone who loves Indian culture.",
        "hashtags":["#FestivalOfBharat","#IndianCulture","#Bharat","#IndianTraditions","#IndianFestivals"],
        "cover_text":item["title"][:54],
        "music":"Add eligible/trending Instagram audio after approval; master MP4 stays music-free."})

stage("12-four-reels",{"status":"complete","count":4,"distinct_topics":[x["topic"] for x in daily_topics],
      "distinct_pillars":[x["pillar"] for x in daily_topics],"files":[r["file"] for r in reels],
      "rule":"Four different topics; four independent production tracks."})
stage("13-approval",{"status":"pending_human","rule":"No automatic publishing; human approval required."})
analytics_file=os.getenv("ANALYTICS_JSON","").strip()
analytics={}
if analytics_file and Path(analytics_file).exists():
    try: analytics=json.loads(Path(analytics_file).read_text())
    except Exception: analytics={}
stage("14-analytics",{"status":"ready","source":"provided Instagram analytics" if analytics else "awaiting Instagram analytics","data":analytics})
stage("15-learning",{"status":"complete" if analytics else "baseline_ready",
      "learned_from":"provided analytics" if analytics else "editorial baseline",
      "next_batch_adjustments":{"retain":"strong hooks + visual change + one useful idea",
      "test":"opening visual, pacing, cover text, CTA","do_not_copy":"creator content or copyrighted clips"}})

manifest={
"generated_at":datetime.now(timezone.utc).isoformat(),
"daily_key":today_key,
"reference_intelligence":{"instagram":instagram_refs,"pinterest":pinterest_refs,"canva":canva_refs},
"topics":[{"reel":i+1,"topic":x["topic"],"pillar":x["pillar"],"title":x["title"]} for i,x in enumerate(daily_topics)],
"format":"1080x1920 9:16 Instagram Reel",
"production":"four independent professional short-form edits — each Reel has a different topic and pillar",
"content_rule":USEFUL_RULE,
"diversity_rule":"No two Reels in the same daily batch may use the same topic or editorial pillar.",
"story_engine":{"beats":["hook","visual proof","context","detail","meaning","CTA"],"rule":"One clear cultural idea per Reel; no random clip montage."},
"editorial_scorecard":{"hook":"immediate","visual_change":"high","information_density":"one clear idea per Reel","ending":"clean CTA"},
"asset_screening":{"creator_name_risk":"reject","platform_mark_risk":"reject","visual_watermark_risk":"sampled-frame OCR reject","third_party_content":"reject","attribution":"preserve in rights record"},
"rights_review_required":True,
"user_supplied_source":{"provided":bool(source_url),"rights_assumption":"user must confirm ownership/permission before use" if source_url else None},
"reels":reels}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
(OUT/"README.txt").write_text("Festival of Bharat — professional daily Reel batch\nSix-beat edit: hook → visual proof → context → detail → meaning → CTA.\n1080x1920, 30fps, no embedded commercial music. Add eligible/trending Instagram audio after approval.\nRisky creator/platform/watermarked sources are rejected rather than stripped. Verify rights before posting.\n")
(OUT/"creator-pack.json").write_text(json.dumps({"topics":[x["topic"] for x in daily_topics],"caption_direction":"Lead with the useful cultural fact, then invite a save/share.","music_direction":"Use eligible/trending Instagram audio inside Instagram; do not embed commercial music in the master.","posting_note":"Human approval required before publishing."},indent=2))
print("BUILT",len(reels),"professional Reels across",len(daily_topics),"different topics")
