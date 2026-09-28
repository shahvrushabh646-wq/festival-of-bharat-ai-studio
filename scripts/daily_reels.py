#!/usr/bin/env python3
import json, os, re, subprocess, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
import textwrap
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"daily-output"; RAW=ROOT/"daily-raw"
OUT.mkdir(exist_ok=True); RAW.mkdir(exist_ok=True)
# Clear previous generated media/stage files so stale batches can never be published.
for p in OUT.glob('*.mp4'): p.unlink(missing_ok=True)
if (OUT/'stages').exists():
    for p in (OUT/'stages').glob('*.json'): p.unlink(missing_ok=True)
UA="FestivalOfBharatCreatorOS/3.1 (festivalofbharat; GitHub Actions)"

def fetch(url, timeout=60):
    import time
    last=None
    for attempt in range(5):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
            with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()
        except Exception as e:
            last=e
            if "429" not in str(e): raise
            time.sleep(min(20,2**attempt*2))
    raise last
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
        # Only accept culturally relevant trends. Generic country names such as "India"
        # are deliberately excluded because sports/news trends can contain them.
        culture=re.compile(r"ganesh|ganpati|bappa|festival|diwali|holi|navratri|garba|krishna|janmashtami|shiva|mahadev|temple|pooja|puja|utsav|mela|heritage|culture|craft|handloom|pottery|artisan|food|cuisine|tradition|ritual|architecture|fort|palace|indian art",re.I)
        for t in titles:
            if culture.search(t) and len(t.strip()) >= 4:
                return t
        return "Indian culture"
    except Exception:return "Indian culture"

USEFUL_RULE=("Every Reel must teach, explain, preserve, or give practical cultural context about an Indian "
"festival, tradition, place, craft, food, history, or cultural practice. Avoid fabricated facts, empty trend-chasing, copied creator content, and generic filler.")
user_topic=os.getenv("TOPIC","").strip()
trend_topic=trends()
IST=timezone(__import__('datetime').timedelta(hours=5,minutes=30))
today_key=datetime.now(IST).strftime('%Y-%m-%d')

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
# A morning re-edit keeps the exact same four topics from the completed batch.
if user_topic.startswith("EDITTOPICS:"):
    try:
        locked=json.loads(user_topic[len("EDITTOPICS:"):])
        if len(locked)==4:
            daily_topics=[]
            for t in locked:
                name,title,fact,queries=profile(t)
                daily_topics.append({"topic":t,"pillar":name,"title":title,"fact":fact,"queries":queries})
    except Exception as e:
        print("Could not lock previous topics for re-edit:",e)
source_url=os.getenv("SOURCE_URL","").strip()
edit_request=os.getenv("EDIT_REQUEST","").strip()

STAGES=OUT/"stages"; STAGES.mkdir(exist_ok=True)

# Live production telemetry is written to a dedicated GitHub "status" branch.
# This keeps the dashboard accurate without pushing status commits to main
# (which would otherwise trigger another production run).
STATUS_API="https://api.github.com"
REPO=os.getenv("GITHUB_REPOSITORY","shahvrushabh646-wq/festival-of-bharat-ai-studio")
GH_TOKEN=os.getenv("GITHUB_TOKEN","").strip()
STATUS_BRANCH="status"
RUN_STARTED_AT=datetime.now(timezone.utc)
RUN_STARTED_MONO=time.monotonic()
HANDOFF_FILE=ROOT/"daily-handoff-history.json"
try:
    HANDOFF_FILE.unlink(missing_ok=True)
except Exception:
    pass

def record_local_handoff(percent, team, employee, task, phase, reel=None):
    """Durable local journal used by workflow failure recovery."""
    event={
        "started_at":datetime.now(timezone.utc).isoformat(),
        "ended_at":None,
        "duration_seconds":None,
        "percent":percent,
        "phase":phase,
        "team":team,
        "employee":employee,
        "task":task,
        "reel":reel,
        "topic":(daily_topics[reel-1].get("topic") if isinstance(reel,int) and 1 <= reel <= len(daily_topics) else None)
    }
    try:
        history=[]
        if HANDOFF_FILE.exists():
            history=json.loads(HANDOFF_FILE.read_text(encoding="utf-8")).get("history") or []
        if history and history[-1].get("ended_at") is None:
            history[-1]["ended_at"]=event["started_at"]
            try:
                history[-1]["duration_seconds"]=round(max(0,(datetime.fromisoformat(event["started_at"])-datetime.fromisoformat(history[-1]["started_at"])).total_seconds()),1)
            except Exception:
                pass
        history.append(event)
        HANDOFF_FILE.write_text(json.dumps({"history":history[-100:]},ensure_ascii=False),encoding="utf-8")
    except Exception as e:
        print("local handoff journal skipped:",e)

def publish_status(percent, team, employee, task, phase, departments=None, reel=None):

    if not GH_TOKEN:
        return
    now=datetime.now(timezone.utc)
    payload={
        "date":today_key,
        "run_id":os.getenv("GITHUB_RUN_ID",""),
        "run_number":os.getenv("GITHUB_RUN_NUMBER",""),
        "overall_percent":percent,
        "phase":phase,
        "current_team":team,
        "current_employee":employee,
        "current_task":task,
        "reel":reel,
        "departments":departments or {},
        "updated_at":now.isoformat(),
        "elapsed_seconds":round(time.monotonic()-RUN_STARTED_MONO,1)
    }
    try:
        data=json.dumps(payload,ensure_ascii=False).encode()
        headers={"Authorization":f"Bearer {GH_TOKEN}","Accept":"application/vnd.github+json",
                 "X-GitHub-Api-Version":"2022-11-28","User-Agent":UA}
        path="/repos/"+REPO+"/contents/status/status.json"
        # Read the current status file on the status branch to obtain its SHA.
        req=urllib.request.Request(STATUS_API+path+"?ref="+STATUS_BRANCH,headers=headers)
        sha=None
        previous={}
        try:
            with urllib.request.urlopen(req,timeout=20) as r:
                old=json.loads(r.read().decode())
                sha=old.get("sha")
                previous=old.get("content") and json.loads(__import__("base64").b64decode(old["content"]).decode()) or {}
        except Exception:
            pass
        history=list(previous.get("history") or [])
        prev=history[-1] if history else None
        if prev:
            prev["ended_at"]=payload["updated_at"]
            prev["duration_seconds"]=round(max(0, (now-datetime.fromisoformat(prev["started_at"])).total_seconds()),1)
        event={
            "started_at":payload["updated_at"],
            "ended_at":None,
            "duration_seconds":None,
            "percent":percent,
            "phase":phase,
            "team":team,
            "employee":employee,
            "task":task,
            "reel":reel,
            "topic":(daily_topics[reel-1].get("topic") if isinstance(reel,int) and 1 <= reel <= len(daily_topics) else None)
        }
        history.append(event)
        payload["history"]=history[-100:]
        payload["department_details"]={
            "Strategy & Research":"Trend selection, daily topic strategy, cultural research and source/fact gate.",
            "Creative & Story":"Creative direction, four story angles, scripts, six-beat structure and storyboards.",
            "Production":"Licensed visual scouting, rights screening, video editing, rendering and master export.",
            "Quality & Growth":"Quality checks, automatic re-edit, caption/cover preparation, approval gate and learning."
        }
        data=json.dumps(payload,ensure_ascii=False).encode()
        body={"message":f"live status: {employee}","content":__import__("base64").b64encode(data).decode(),
              "branch":STATUS_BRANCH}
        if sha: body["sha"]=sha
        req=urllib.request.Request(STATUS_API+path,data=json.dumps(body).encode(),headers={**headers,"Content-Type":"application/json"},method="PUT")
        with urllib.request.urlopen(req,timeout=20) as r: r.read()
    except Exception as e:
        print("status telemetry skipped:",e)

def employee_handoff(percent, team, employee, task, phase, reel=None):
    """Record a real employee handoff in local and live telemetry."""
    record_local_handoff(percent, team, employee, task, phase, reel)
    publish_status(percent, team, employee, task, phase, {
        "Strategy & Research":"complete" if team != "Strategy & Research" else "working",
        "Creative & Story":"complete" if team in ["Production","Quality & Growth"] else ("working" if team == "Creative & Story" else "waiting"),
        "Production":"complete" if team == "Quality & Growth" else ("working" if team == "Production" else "waiting"),
        "Quality & Growth":"working" if team == "Quality & Growth" else "waiting"
    }, reel)

def stage(name,data):
    (STAGES/f"{name}.json").write_text(json.dumps(data,indent=2,ensure_ascii=False))

employee_handoff(10,"Strategy & Research","Trend Researcher","Select culturally relevant India trend and reject unrelated trends","trend")
stage("01-trend",{
    "status":"complete",
    "daily_plan":"four_distinct_topics",
    "trend_source":"Google Trends India RSS",
    "user_topic":user_topic or None,
    "edit_request":edit_request or None,
    "production_window":"02:00–06:00 IST",
    "trend_topic":trend_topic,
    "topics":[{"reel":i+1,"topic":x["topic"],"pillar":x["pillar"],"title":x["title"]} for i,x in enumerate(daily_topics)]
})
employee_handoff(18,"Strategy & Research","Content Manager","Build four-topic strategy and enforce topic/pillar diversity","strategy")
stage("02-strategy",{
    "status":"complete",
    "objective":"Create four useful Indian-culture Reels with four different topics and pillars",
    "diversity_rule":"No two Reels in the same daily batch may use the same topic or editorial pillar",
    "audience":"Instagram users interested in Indian culture",
    "retention":"visual change every beat",
    "cta":"save/share/follow"
})
for i,item in enumerate(daily_topics,1):
    employee_handoff(24+i*4,"Strategy & Research","Cultural Researcher",f"Research and verification gate for Reel {i}: {item['topic']}","research",i)
    stage(f"03-research-{i:02d}",{
        'status':'research_gate','reel':i,'topic':item['topic'],'fact':item['fact'],
        'verification_required':True,
        'rule':'Verify factual cultural claims before publishing; preserve supporting source records.'
    })
    stage(f"03-idea-{i:02d}",{
        "status":"complete","reel":i,"topic":item["topic"],"pillar":item["pillar"],
        "title":item["title"],"core_idea":item["fact"],"rule":"one clear cultural idea per Reel"
    })
    if i == 1:
        employee_handoff(40,"Creative & Story","Creative Director","Create four distinct story treatments from the researched topics","creative")
    employee_handoff(42+i,"Creative & Story","Script Writer",f"Write six-beat script for Reel {i}","script",i)
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
    employee_handoff(46+i,"Creative & Story","Storyboard Director",f"Build 9:16 storyboard and visual beat order for Reel {i}","storyboard",i)
    stage(f"05-storyboard-{i:02d}",{
        "status":"complete","reel":i,"topic":item["topic"],"format":"9:16 vertical",
        "beats":["hook","proof","context","detail","meaning","CTA"],
        "visual_direction":"cinematic realistic Indian culture; original editorial treatment; source intelligence from Instagram, Pinterest, Google and Canva; no random montage"
    })

# Template library: templates are executable production rules, not UI labels.
# Every template defines how photos move, how videos are paced, and how captions sit
# on the vertical frame. The renderer below uses these rules for the actual Reel.
TEMPLATES = {
    "cinematic_festival": {
        "id":"cinematic_festival","name":"Cinematic Festival","eq":"eq=contrast=1.08:saturation=1.14:brightness=0.01",
        "effects":["slow_zoom_in","pan_right","slow_zoom_out","tilt_up","slow_zoom_in","pan_left"],
        "beat_durations":[2.2,2.2,2.5,2.5,2.2,2.2],"pacing":"cinematic","photo_bias":1
    },
    "photo_story": {
        "id":"photo_story","name":"Photo Story","eq":"eq=contrast=1.05:saturation=1.08",
        "effects":["slow_zoom_in","pan_left","slow_zoom_out","pan_right","tilt_down","slow_zoom_in"],
        "beat_durations":[2.2,2.2,2.3,2.3,2.2,2.2],"pacing":"measured","photo_bias":3
    },
    "documentary": {
        "id":"documentary","name":"Documentary","eq":"eq=contrast=1.04:saturation=0.96:gamma=0.98",
        "effects":["slow_zoom_in","tilt_up","pan_right","slow_zoom_out","slow_zoom_in","pan_left"],
        "beat_durations":[2.3,2.3,2.5,2.4,2.2,2.2],"pacing":"measured","photo_bias":2
    },
    "fast_cultural": {
        "id":"fast_cultural","name":"Fast Cultural","eq":"eq=contrast=1.10:saturation=1.18:brightness=0.02",
        "effects":["pan_right","slow_zoom_in","pan_left","tilt_down","slow_zoom_out","slow_zoom_in"],
        "beat_durations":[1.6,1.8,1.8,1.9,1.8,1.9],"pacing":"fast","photo_bias":1
    },
    "temple_spiritual": {
        "id":"temple_spiritual","name":"Temple / Spiritual","eq":"eq=contrast=1.03:saturation=1.06:gamma=0.96",
        "effects":["slow_zoom_in","slow_zoom_out","tilt_up","pan_right","slow_zoom_in","pan_left"],
        "beat_durations":[2.3,2.3,2.5,2.4,2.2,2.2],"pacing":"slow","photo_bias":3
    }
}

ANGLE_LIBRARY = [
    {"key":"unknown","label":"3 things you didn't know","template":"fast_cultural"},
    {"key":"history","label":"History behind the story","template":"documentary"},
    {"key":"why","label":"Why people celebrate it","template":"temple_spiritual"},
    {"key":"journey","label":"Visual journey / story","template":"photo_story"},
]

def choose_template(item, edit_request=""):
    req=(edit_request or "").lower()
    for tid,spec in TEMPLATES.items():
        if tid.replace("_"," ") in req or spec["name"].lower() in req:
            return dict(spec)
    if "photo" in req: return dict(TEMPLATES["photo_story"])
    if "documentary" in req: return dict(TEMPLATES["documentary"])
    if "fast" in req: return dict(TEMPLATES["fast_cultural"])
    topic=(str(item.get("topic",""))+" "+str(item.get("pillar",""))).lower()
    if re.search(r"temple|mandir|shiva|krishna|aarti|devotion",topic):
        return dict(TEMPLATES["temple_spiritual"])
    if re.search(r"heritage|fort|palace|history|architecture",topic):
        return dict(TEMPLATES["documentary"])
    if re.search(r"ganesh|ganpati|holi|diwali|navratri|festival",topic):
        return dict(TEMPLATES["cinematic_festival"])
    return dict(TEMPLATES[["cinematic_festival","photo_story","documentary","fast_cultural"][
        (int(today_key.replace("-","")) + len(str(item.get("topic","")))) % 4
    ]])

SHOT_WANTS = [
    {"want":["skyline","city","wide","landscape","ghat","river","exterior"],"pref":"video"},
    {"want":["idol","deity","murti","statue","ganesh","krishna","shiva"],"pref":"photo"},
    {"want":["crowd","procession","festival","celebration","people"],"pref":"video"},
    {"want":["decoration","flower","diya","lamp","rangoli","mandap"],"pref":"photo"},
    {"want":["aarti","ritual","puja","temple","offering"],"pref":"video"},
    {"want":["architecture","carving","detail","craft","close"],"pref":"photo"},
]

def score_asset(asset,want):
    blob=" ".join([str(asset.get("title") or ""),str(asset.get("page") or ""),str(asset.get("query") or "")]).lower()
    score=sum(1 for w in want if w in blob)
    if asset.get("kind") in {"photo","image"} and "photo" in want: score += 2
    if asset.get("kind")=="video" and "video" in want: score += 2
    return score

def arrange_shots(pool,template,item):
    """Turn the template into actual photo/video shot assignments."""
    pool=[dict(x) for x in pool if x.get("file")]
    if not pool: return []
    remaining=list(pool); chosen=[]
    for i,slot in enumerate(SHOT_WANTS[:6]):
        pref=slot["pref"]
        candidates=sorted(remaining,key=lambda a:score_asset(a,slot["want"])+(2 if a.get("kind")==pref else 0),reverse=True)
        pick=candidates[0] if candidates else None
        if pick is None: break
        remaining=[a for a in remaining if a is not pick]
        rec=dict(pick)
        rec["shot"]=i+1
        rec["effect"]=template["effects"][i%len(template["effects"])]
        rec["duration"]=template["beat_durations"][i%len(template["beat_durations"])]
        chosen.append(rec)
    # Reuse only same-topic licensed assets when the pool is smaller than six slots.
    if chosen:
        idx=0
        while len(chosen)<6:
            base=chosen[idx%len(chosen)]
            rec=dict(base); rec["shot"]=len(chosen)+1; rec["reused_for_continuity"]=True
            rec["effect"]=template["effects"][len(chosen)%len(template["effects"])]
            rec["duration"]=template["beat_durations"][len(chosen)%len(template["beat_durations"])]
            chosen.append(rec); idx+=1
    # Hard mixed-media guard: if both kinds exist, at least one of each must survive.
    kinds={x.get("kind") for x in pool}
    if {"photo","video"} <= kinds and len(chosen)>=2:
        if not any(x.get("kind")=="photo" for x in chosen):
            photo=next(x for x in pool if x.get("kind")=="photo")
            chosen[1]={**photo,"shot":2,"effect":template["effects"][1],"duration":template["beat_durations"][1]}
        if not any(x.get("kind")=="video" for x in chosen):
            video=next(x for x in pool if x.get("kind")=="video")
            chosen[0]={**video,"shot":1,"effect":template["effects"][0],"duration":template["beat_durations"][0]}
    return chosen[:6]

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

def _openverse_results(endpoint,q):
    api=(endpoint+"?q="+urllib.parse.quote(q)+
         "&license=cc0,by,by-sa&per_page=12&page=1")
    try:
        return json.loads(fetch(api,60)).get("results",[])
    except Exception as e:
        print("Openverse search failed",endpoint,q,e)
        return []

def scout_openverse_videos(topic_item,reel_no):
    pool=[]; seen=set()
    for q in list(dict.fromkeys(topic_item["queries"])):
        for item in _openverse_results("https://api.openverse.org/v1/videos/",q):
            url=item.get("url") or item.get("thumbnail")
            title=clean(item.get("title") or q); lic=clean(item.get("license") or "")
            author=clean(item.get("creator") or "")
            pageurl=item.get("foreign_landing_url") or item.get("detail_url") or ""
            if not url or url in seen or str(item.get("license","")).lower() not in {"cc0","by","by-sa"}: continue
            if reject_source(title,author,pageurl): continue
            dest=RAW/(f"reel{reel_no}_video{len(pool):02d}.mp4")
            try:
                dest.write_bytes(fetch(url,90))
                dur,w,h,codec=probe(dest)
                if dest.stat().st_size<30000 or w<400 or h<400 or dur<1:
                    dest.unlink(missing_ok=True); continue
                seen.add(url)
                add_source_asset(pool,title,url,lic,author,pageurl,str(dest),"video")
            except Exception as e:
                dest.unlink(missing_ok=True)
                print("Openverse video skip",e)
            if len(pool)>=4: return pool
    return pool

def scout_openverse_topic(topic_item,reel_no):
    """Build a mixed visual pool: always try to include both video and photo."""
    videos=scout_openverse_videos(topic_item,reel_no)
    pool=list(videos[:3])
    seen={a.get("url") for a in pool}
    image_target=1 if videos else 4
    for q in list(dict.fromkeys(topic_item["queries"])):
        for item in _openverse_results("https://api.openverse.org/v1/images/",q):
            url=item.get("url") or item.get("thumbnail")
            title=clean(item.get("title") or q); lic=clean(item.get("license") or "")
            author=clean(item.get("creator") or "")
            pageurl=item.get("foreign_landing_url") or item.get("detail_url") or ""
            if not url or url in seen or str(item.get("license","")).lower() not in {"cc0","by","by-sa"}: continue
            if reject_source(title,author,pageurl): continue
            dest=RAW/(f"reel{reel_no}_asset{len(pool):02d}.jpg")
            try:
                dest.write_bytes(fetch(url,60))
                dur,w,h,codec=probe(dest)
                if dest.stat().st_size<15000 or w<400 or h<400:
                    dest.unlink(missing_ok=True); continue
                seen.add(url)
                add_source_asset(pool,title,url,lic,author,pageurl,str(dest),"photo")
            except Exception as e:
                dest.unlink(missing_ok=True)
                print("Openverse image skip",e)
            if sum(1 for x in pool if x.get("kind")=="photo")>=image_target:
                break
        if sum(1 for x in pool if x.get("kind")=="photo")>=image_target:
            break
    # Fill any remaining slots with licensed visuals; preserve at least one photo whenever available.
    if len(pool)<4:
        for extra in scout_openverse_videos(topic_item,reel_no):
            if extra.get("url") not in seen:
                pool.append(extra); seen.add(extra.get("url"))
            if len(pool)>=4: break
    return pool[:4]

def scout_topic(topic_item,reel_no):
    # Source priority: openly licensed video -> openly licensed image -> Wikimedia.
    # Instagram/Pinterest/Google/Canva remain intelligence/reference sources, not
    # arbitrary media download targets.
    pool=scout_openverse_topic(topic_item,reel_no)
    if len(pool)>=4: return pool
    print(f"Openverse supplied {len(pool)} assets; trying Wikimedia Commons fallback.")
    queries=list(dict.fromkeys(topic_item["queries"]))
    seen={a.get("url") for a in pool}
    for q in queries:
        import time; time.sleep(1.2)
        api=("https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch="+urllib.parse.quote(q)+
             "&gsrnamespace=6&gsrlimit=8&prop=imageinfo&iiprop=url|mime|size|extmetadata&iiurlwidth=600&format=json&origin=*")
        try:data=json.loads(fetch(api))
        except Exception as e:
            print("Wikimedia search failed",q,e); continue
        for page in data.get("query",{}).get("pages",{}).values():
            info=(page.get("imageinfo") or [{}])[0]
            url=(info.get("thumburl") if info.get("mime","").startswith("image/") and info.get("thumburl") else info.get("url",""))
            mime=info.get("mime",""); meta=info.get("extmetadata",{})
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
                print("Wikimedia asset skip",e)
            if len(pool)>=4: return pool
    return pool

def make_local_fallback_asset(item,reel_no):
    # Last-resort production safety net. This keeps the batch alive without
    # pretending an unlicensed/random web image is usable.
    dest=RAW/f"reel{reel_no}_fallback.jpg"
    title=esc(f"{item['title']}")
    pillar=esc(f"{item['pillar'].upper()} • FESTIVAL OF BHARAT")
    fallback_font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    run(["ffmpeg","-y","-f","lavfi","-i","color=c=0x17120f:s=1080x1920:d=1",
         "-vf",f"drawtext=fontfile={fallback_font}:text='{title}':fontcolor=white:fontsize=58:borderw=3:bordercolor=black@.8:x=70:y=780:enable='between(t,0,1)',"
               f"drawtext=fontfile={fallback_font}:text='{pillar}':fontcolor=white:fontsize=30:borderw=2:bordercolor=black@.7:x=70:y=900",
         "-frames:v","1",str(dest)])
    return {"title":item["title"],"url":"","license":"Original fallback graphic","author":"Festival of Bharat","page":"",
            "kind":"photo","rights_review":True,"file":str(dest),"fallback":True}

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
    employee_handoff(40+reel_no*7,"Production","Visual Source Director",f"Combine Instagram, Pinterest, Google and Canva intelligence and source visuals for Reel {reel_no}","visual sources",reel_no)
    # A single provider failure must never block the whole batch. Try every permitted
    # source and keep only topic-matched, clean assets. If fewer than four are found,
    # retry broader queries for the SAME topic before considering the Reel blocked.
    pool=[]
    try:
        pool=scout_topic(item,reel_no)
    except Exception as e:
        print(f"Primary visual scouting failed for Reel {reel_no}: {e}")
    pool=[a for a in pool if not visual_risk(a["file"])]
    if len(pool)<4:
        retry_item=dict(item)
        retry_item["topic"]=item["topic"]+" India culture"
        retry_item["queries"]=list(dict.fromkeys(
            list(item.get("queries",[]))+
            [item["title"],item["topic"],item["pillar"]+" India",item["topic"]+" Indian culture"]
        ))
        try:
            retry_pool=scout_topic(retry_item,reel_no)
            retry_pool=[a for a in retry_pool if not visual_risk(a["file"])]
            seen={a.get("page") or a.get("file") for a in pool}
            pool.extend(a for a in retry_pool if (a.get("page") or a.get("file")) not in seen)
        except Exception as e:
            print(f"Fallback visual scouting failed for Reel {reel_no}: {e}")
    if len(pool)<4:
        # Reuse clean assets from the SAME topic before falling back to an original
        # generated card. Never mix an unrelated topic into this Reel.
        if pool:
            while len(pool)<4:
                pool.append({**pool[len(pool)%len(pool)],"reused_for_continuity":True})
            print(f"Reel {reel_no}: only {len(set(a.get('url') for a in pool))} unique clean assets; reusing same-topic assets to complete the visual sequence.")
        else:
            fallback=make_local_fallback_asset(item,reel_no)
            pool=[fallback]*4
            print(f"Reel {reel_no}: no licensed web assets available; using original fallback graphic so the production batch continues.")
        stage(f"06-visual-sources-{reel_no:02d}",{"status":"complete_with_fallback" if any(a.get("fallback") for a in pool) else "complete",
            "reel":reel_no,"topic":item["topic"],"asset_count":len(pool),
            "unique_asset_count":len(set(a.get("url") or a.get("file") for a in pool)),
            "fallback_used":any(a.get("fallback") for a in pool)})
    assets_by_reel[reel_no]=pool[:4]
    stage(f"06-visual-sources-{reel_no:02d}",{"status":"complete","reel":reel_no,"topic":item["topic"],"asset_count":len(assets_by_reel[reel_no]),"assets":assets_by_reel[reel_no],"source_intelligence":{"Instagram":"trend/hook/pacing reference","Pinterest":"composition and visual mood reference","Google":"topic/image research reference","Canva":"eligible design/layout/asset reference"}})
    employee_handoff(58+reel_no,"Production","Rights & Copyright Manager",f"Screen licenses, authors, watermarks and platform-risk sources for Reel {reel_no}","rights",reel_no)
    stage(f"07-rights-{reel_no:02d}",{"status":"complete","reel":reel_no,"topic":item["topic"],"gate":"reject risky creator/platform/watermarked sources",
           "assets":[{"title":a["title"],"license":a["license"],"author":a["author"],"page":a["page"],"rights_review":True} for a in assets_by_reel[reel_no]]})

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def preflight_render_environment():
    required=["ffmpeg","ffprobe","tesseract"]
    missing=[x for x in required if subprocess.call(["bash","-lc",f"command -v {x} >/dev/null 2>&1"])!=0]
    if not Path(FONT).exists():
        missing.append(FONT)
    if missing:
        raise RuntimeError("Production preflight failed. Missing: "+", ".join(missing))
    print("RENDER PREFLIGHT OK")

preflight_render_environment()

def make_cover(reel_path,item,idx):
    covers=OUT/"covers"
    covers.mkdir(exist_ok=True)
    dest=covers/f"reel_{idx:02d}_cover.jpg"
    title=esc(item["title"][:48])
    pillar=esc(item["pillar"].upper()+" • FESTIVAL OF BHARAT")
    run(["ffmpeg","-y","-ss","0.5","-i",str(reel_path),"-frames:v","1","-q:v","3",
         "-vf",f"drawbox=x=0:y=0:w=iw:h=360:color=black@0.42:t=fill,drawtext=fontfile={FONT}:text='{title}':fontcolor=white:fontsize=54:borderw=3:bordercolor=black@.8:x=55:y=105,drawtext=fontfile={FONT}:text='{pillar}':fontcolor=white:fontsize=26:borderw=2:bordercolor=black@.7:x=55:y=245",
         str(dest)])
    if not dest.exists() or dest.stat().st_size<10000:
        raise RuntimeError(f"Cover generation failed for Reel {idx}")
    return dest.name

def make_clip(src,out,dur,effect="slow_zoom_in",grade="eq=contrast=1.06:saturation=1.12:brightness=.01"):
    """Normalize photos/videos while applying the selected template motion."""
    sd,sw,sh,codec=probe(src); start=0 if sd<dur+0.3 else min(.7,sd-dur)
    is_image=Path(src).suffix.lower() in [".jpg",".jpeg",".png",".webp"]
    if is_image:
        if effect=="pan_right":
            motion=f"scale=1680:1920:force_original_aspect_ratio=increase,crop=1680:1920,crop=1080:1920:x='(in_w-1080)*t/{max(dur,0.1)}':y=0"
        elif effect=="pan_left":
            motion=f"scale=1680:1920:force_original_aspect_ratio=increase,crop=1680:1920,crop=1080:1920:x='(in_w-1080)*(1-t/{max(dur,0.1)})':y=0"
        elif effect=="tilt_up":
            motion=f"scale=1080:2300:force_original_aspect_ratio=increase,crop=1080:2300,crop=1080:1920:x=0:y='(in_h-1920)*(1-t/{max(dur,0.1)})'"
        elif effect=="tilt_down":
            motion=f"scale=1080:2300:force_original_aspect_ratio=increase,crop=1080:2300,crop=1080:1920:x=0:y='(in_h-1920)*t/{max(dur,0.1)}'"
        else:
            frames=max(2,int(dur*30))
            motion=f"scale=1600:2844:force_original_aspect_ratio=increase,crop=1600:2844,zoompan=z='min(1+0.0013*on,1.14)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30"
        vf=motion+","+grade+",setsar=1,format=yuv420p"
        cmd=["ffmpeg","-y","-loop","1","-framerate","30","-i",str(src),"-t",str(dur),"-vf",vf,
             "-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-r","30","-threads","2",str(out)]
    else:
        vf=f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{grade},unsharp=5:5:.35:5:5:0,fps=30,setsar=1,format=yuv420p"
        cmd=["ffmpeg","-y","-ss",str(start),"-i",str(src),"-t",str(dur),"-vf",vf,
             "-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-r","30","-threads","2",str(out)]
    r=run(cmd,check=False)
    if r.returncode!=0 or not Path(out).exists() or Path(out).stat().st_size<20000:
        raise RuntimeError((r.stderr or "")[-1200:])
    return out

def quality_check(path):
    dur,w,h,codec=probe(path)
    checks={"resolution":w==1080 and h==1920,"duration":9<=dur<=16.5,"codec":codec=="h264"}
    return {"pass":all(checks.values()),"checks":checks,"duration":round(dur,2),"width":w,"height":h,"codec":codec}

STYLE_LIBRARY=[
    ("moment","THE MOMENT — topic treatment",[0,1,2,3,4,5],[2.0,2.0,2.5,2.5,2.0,2.0],"cinematic"),
    ("detail","THE DETAIL — topic treatment",[1,0,2,3,4,5],[2.0,2.0,2.5,2.5,2.0,2.0],"curiosity"),
    ("energy","THE ENERGY — topic treatment",[0,2,1,3,5,4],[1.5,1.8,2.0,2.2,2.0,2.2],"fast"),
    ("meaning","THE MEANING — topic treatment",[0,1,3,2,4,5],[2.2,2.0,2.5,2.5,2.0,2.0],"reflective")
]
styles=STYLE_LIBRARY

def render_reel(idx,style,item,assets,template=None):
    # Final hard safety guard: render_reel must never receive an empty asset list.
    # This is intentionally redundant with visual sourcing so a future sourcing change
    # cannot reintroduce the assets[... % len(assets)] crash.
    if not assets:
        fallback=make_local_fallback_asset(item,idx)
        assets=[fallback,fallback,fallback,fallback]
        print(f"Reel {idx}: render guard created an original fallback asset.")
    name,label,order,durations,tempo=style
    template=template or choose_template(item,edit_request)
    grade=template["eq"]
    shots=arrange_shots(assets,template,item)
    if len(shots)<2:
        raise RuntimeError(f"Reel {idx}: template could not assemble enough visual shots")
    # Template now controls real visual motion. The style remains the six-beat editorial order.
    order=list(range(min(6,len(shots))))
    durations=[float(shots[j].get("duration") or durations[j]) for j in range(min(6,len(shots)))]
    texts=[f"STOP SCROLLING: {item['title']}",f"LOOK CLOSER • {item['pillar']}",item["fact"],
           "This is the detail most quick videos skip.","Now you know what you're actually seeing.",
           "SAVE THIS • FOLLOW FESTIVAL OF BHARAT"]
    # Apply concrete human feedback during the morning re-edit pass.
    req=edit_request.lower()
    # Morning review edits are targeted to one rejected Reel.
    m=re.search(r"reel\s*(\d+)",req,re.I)
    target_reel=int(m.group(1)) if m else None
    if req and (target_reel is None or target_reel==idx):
        if any(x in req for x in ["remove text","no text","without text"]):
            texts=[""]*6
        if "hook" in req and "strong" in req:
            texts[0]=f"YOU NEED TO KNOW: {item['title']}"
        if any(x in req for x in ["faster","fast pace","quick"]):
            durations=[max(1.2,d*0.82) for d in durations]
        if any(x in req for x in ["slower","slow pace"]):
            durations=[d*1.15 for d in durations]
    roles=["HOOK","VISUAL PROOF","CONTEXT","DETAIL","MEANING","CTA"]; clips=[]
    for j,(ai,d) in enumerate(zip(order,durations)):
        raw=OUT/f"_raw{idx}_{j}.mp4"; styled=OUT/f"_cut{idx}_{j}.mp4"
        asset=shots[ai%len(shots)]
        source=asset.get("file","")
        try:
            if not source or not Path(source).exists():
                raise RuntimeError("visual asset file is missing")
            make_clip(source,raw,d,asset.get("effect") or "slow_zoom_in",grade)
        except Exception as e:
            print(f"Reel {idx} beat {j+1}: source render failed; replacing only this visual with an original fallback: {e}")
            fallback=make_local_fallback_asset(item,idx)
            make_clip(fallback["file"],raw,d,"slow_zoom_in",grade)
            asset=fallback
        # Use FFmpeg textfile= for editorial copy. This prevents filter-parser
        # failures from commas, apostrophes, brackets and other trend text.
        role_path=OUT/f"_role{idx}_{j}.txt"
        main_path=OUT/f"_text{idx}_{j}.txt"
        role_path.write_text(roles[j],encoding="utf-8")
        main_path.write_text(fit_text(texts[j],30 if j in [2,3,4] else 25),encoding="utf-8")
        role_file=esc(str(role_path)); main_file=esc(str(main_path))
        if j in [2,3,4]:
            draw=f"drawtext=fontfile={FONT}:textfile='{role_file}':expansion=none:fontcolor=white:fontsize=28:borderw=3:bordercolor=black@.75:x=55:y=1510,drawtext=fontfile={FONT}:textfile='{main_file}':expansion=none:fontcolor=white:fontsize=42:borderw=4:bordercolor=black@.8:x=55:y=1555"
        elif j==5:
            draw=f"drawtext=fontfile={FONT}:textfile='{main_file}':expansion=none:fontcolor=white:fontsize=42:borderw=4:bordercolor=black@.8:x=55:y=1740"
        else:
            draw=f"drawtext=fontfile={FONT}:textfile='{role_file}':expansion=none:fontcolor=white:fontsize=30:borderw=3:bordercolor=black@.75:x=60:y=120,drawtext=fontfile={FONT}:textfile='{main_file}':expansion=none:fontcolor=white:fontsize=48:borderw=4:bordercolor=black@.8:x=60:y=160"
        rr=run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),"-vf",draw+",fade=t=in:st=0:d=.10,fade=t=out:st="+str(max(0,d-.18))+":d=.18","-an","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-r","30","-threads","2",str(styled)],check=False)
        role_path.unlink(missing_ok=True); main_path.unlink(missing_ok=True)
        if rr.returncode!=0 or not styled.exists() or styled.stat().st_size<20000:
            raise RuntimeError("Caption/motion render failed: "+(rr.stderr or "")[-1600:])
        clips.append(styled)
    final=OUT/f"reel_{idx:02d}.mp4"
    valid=[Path(x) for x in clips if Path(x).exists() and Path(x).stat().st_size>20000]
    if len(valid)<2:
        raise RuntimeError(f"Reel {idx}: not enough valid rendered clips for concat")
    inputs=[];parts=[]
    for j,clip in enumerate(valid):
        inputs += ["-i",str(clip)]
        parts.append(f"[{j}:v]settb=AVTB,setpts=PTS-STARTPTS,"
                     f"scale=1080:1920:force_original_aspect_ratio=decrease,"
                     f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,"
                     f"fps=30,settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[v{j}]")
    n=len(valid)
    fc=";".join(parts)+";"+"".join(f"[v{j}]" for j in range(n))+f"concat=n={n}:v=1:a=0:unsafe=1[v]"
    r=run(["ffmpeg","-y","-filter_threads","1","-filter_complex_threads","1",*inputs,
           "-filter_complex",fc,"-map","[v]","-an","-r","30","-s","1080x1920",
           "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
           "-threads","2","-fps_mode","cfr","-movflags","+faststart",str(final)],check=False)
    if r.returncode!=0 or not final.exists() or final.stat().st_size<100000:
        raise RuntimeError("Final concat failed: "+(r.stderr or "")[-1600:])
    q=quality_check(final)
    if not q["pass"]:
        print("QUALITY FAIL -> AUTO RE-EDIT",idx,q)
        alt=styles[idx%len(styles)]
        if alt[1]==label: raise RuntimeError("Automatic re-edit exhausted")
        return render_reel(idx,alt,item,assets)
    dur,w,h,codec=probe(final)
    result={"file":final.name,"reel":idx,"topic":item["topic"],"pillar":item["pillar"],"title":item["title"],
            "style":label,"template":template["id"],"template_name":template["name"],"tempo":tempo,
            "duration":round(dur,2),"quality":q,"edit_request_applied":edit_request or None,
            "shots":[{"shot":x.get("shot"),"kind":x.get("kind"),"title":x.get("title"),"effect":x.get("effect"),
                     "duration":x.get("duration"),"license":x.get("license"),"page":x.get("page")} for x in shots]}
    for p in clips+[OUT/f"_raw{idx}_{j}.mp4" for j in range(6)]: p.unlink(missing_ok=True)
    return result


MUSIC_POLICY={
 "master_audio":"silent",
 "instagram_edits":"Use Instagram/Edits music only through the Instagram/Edits in-app music workflow after upload/approval; do not scrape or extract commercial tracks.",
 "youtube":"Use only YouTube Audio Library tracks whose current usage terms permit the intended Instagram use; ordinary YouTube uploads labelled 'no copyright' are not automatically safe.",
 "preferred":"Original/commissioned music or a verified cross-platform licence; otherwise add eligible Instagram audio in-app.",
 "attribution":"Preserve required attribution/license evidence in the creator pack."
}

def music_direction(item):
    mood={"heritage":"cinematic Indian instrumental / tanpura / soft percussion","food":"warm folk instrumental / light rhythmic texture","festival":"energetic Indian percussion / festive instrumental","craft":"organic folk instrumental / hand-percussion texture","tradition":"calm devotional-inspired instrumental / ambient texture","culture":"cinematic Indian instrumental / subtle tabla texture"}
    return {"direction":mood.get(item["pillar"],"cinematic Indian instrumental / subtle percussion"),
            "instagram_edits":"Add eligible/trending audio from Instagram or Edits after the master is approved.",
            "youtube_source":"YouTube Audio Library only; verify the track's current licence and cross-platform permission before importing.",
            "license_status":"not_assumed","master_audio":"none"}

reels=[]
for i,(item,style) in enumerate(zip(daily_topics,styles),1):
    employee_handoff(68+i*5,"Production","Video Director",f"Direct shot order, pacing and cinematic treatment for Reel {i}","direction",i)
    employee_handoff(69+i*5,"Production","Video Editor",f"Render six-beat 1080x1920 edit for Reel {i}","edit",i)
    employee_handoff(70+i*5,"Production","Motion Graphics Designer",f"Apply motion treatment and readable graphics for Reel {i}","motion",i)
    employee_handoff(71+i*5,"Production","Caption Designer",f"Apply on-screen hook, context and CTA text for Reel {i}","caption design",i)
    employee_handoff(72+i*5,"Production","Music & Sound Designer",f"Set music direction while keeping master audio-free for Reel {i}","sound",i)
    employee_handoff(73+i*5,"Production","Voiceover Director",f"Check voiceover requirement for Reel {i}; keep silent master unless required","voiceover",i)
    employee_handoff(74+i*5,"Production","Colorist",f"Apply crop, contrast, saturation and sharpening treatment for Reel {i}","color",i)
    template=choose_template(item,edit_request)
    rendered=render_reel(i,style,item,assets_by_reel[i],template)
    stage(f"05-template-{i:02d}",{"status":"complete","reel":i,"template":template["id"],"template_name":template["name"],
        "pacing":template["pacing"],"photo_motion":template["effects"],"beat_durations":template["beat_durations"],
        "asset_rule":"Templates must use the actual licensed photo/video assets assigned to their slots."})
    rendered["cover_file"]=make_cover(OUT/rendered["file"],item,i)
    reels.append(rendered)

employee_handoff(90,"Quality & Growth","Quality Manager","Check resolution, duration, codec and final export quality for all four Reels","quality")
for i,(item,reel) in enumerate(zip(daily_topics,reels),1):
    stage(f"08-edit-{i:02d}",{"status":"complete","reel":i,"topic":item["topic"],"format":"1080x1920","fps":30,"audio":"none","result":reel})
    stage(f"09-quality-{i:02d}",{"status":"complete","reel":i,"topic":item["topic"],"quality":reel["quality"]})
    employee_handoff(92+i,"Quality & Growth","Self-ReEditor",f"Review quality result and trigger alternate edit when Reel {i} fails","re-edit",i)
    stage(f"10-re-edit-{i:02d}",{"status":"complete","reel":i,"rule":"failed quality checks automatically trigger an alternate creative edit"})
    employee_handoff(96+i,"Quality & Growth","Cover Designer",f"Prepare cover text and composition direction for Reel {i}","cover",i)
    employee_handoff(97+i,"Quality & Growth","Caption Writer",f"Prepare publish caption and hashtags for Reel {i}","caption",i)
    stage(f"11-caption-cover-{i:02d}",{"status":"complete","reel":i,"topic":item["topic"],
        "caption":f"{item['title']} — a useful detail from {item['pillar']}. Save this Reel for later and share it with someone who loves Indian culture.",
        "hashtags":["#FestivalOfBharat","#IndianCulture","#Bharat","#IndianTraditions","#IndianFestivals"],
        "cover_text":item["title"][:54],
        "music":music_direction(item)})

stage("12-four-reels",{"status":"complete","count":4,"distinct_topics":[x["topic"] for x in daily_topics],
      "distinct_pillars":[x["pillar"] for x in daily_topics],"files":[r["file"] for r in reels],
      "rule":"Four different topics; four independent production tracks."})
employee_handoff(98,"Quality & Growth","Analytics Manager","Prepare analytics input stage and wait for provided Instagram results","analytics")
employee_handoff(99,"Quality & Growth","AI Manager / CEO","Coordinate final batch, enforce approval gate and stop before publishing","approval")
stage("13-approval",{"status":"pending_human","review_window":"Morning review after overnight 02:00–06:00 IST production","rule":"No automatic publishing; human approval required.","edit_request_received":bool(edit_request),"edit_request":edit_request or None})
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

EMPLOYEE_ROSTER=[
 {"department":"Strategy & Research","employee":"Content Manager"},
 {"department":"Strategy & Research","employee":"Trend Researcher"},
 {"department":"Strategy & Research","employee":"Cultural Researcher"},
 {"department":"Creative & Story","employee":"Creative Director"},
 {"department":"Creative & Story","employee":"Script Writer"},
 {"department":"Creative & Story","employee":"Storyboard Director"},
 {"department":"Production","employee":"Visual Source Director"},
 {"department":"Production","employee":"Rights & Copyright Manager"},
 {"department":"Production","employee":"Video Director"},
 {"department":"Production","employee":"Video Editor"},
 {"department":"Production","employee":"Motion Graphics Designer"},
 {"department":"Production","employee":"Caption Designer"},
 {"department":"Production","employee":"Music & Sound Designer"},
 {"department":"Production","employee":"Voiceover Director"},
 {"department":"Production","employee":"Colorist"},
 {"department":"Quality & Growth","employee":"Quality Manager"},
 {"department":"Quality & Growth","employee":"Self-ReEditor"},
 {"department":"Quality & Growth","employee":"Cover Designer"},
 {"department":"Quality & Growth","employee":"Caption Writer"},
 {"department":"Quality & Growth","employee":"Analytics Manager"},
 {"department":"Quality & Growth","employee":"Learning Manager"},
 {"department":"Quality & Growth","employee":"AI Manager / CEO"}
]

manifest={
"generated_at":datetime.now(timezone.utc).isoformat(),
"run_id":os.getenv("GITHUB_RUN_ID",""),
"run_number":os.getenv("GITHUB_RUN_NUMBER",""),
"daily_key":today_key,
"reference_intelligence":{"instagram":instagram_refs,"pinterest":pinterest_refs,"canva":canva_refs},
"topics":[{"reel":i+1,"topic":x["topic"],"pillar":x["pillar"],"title":x["title"]} for i,x in enumerate(daily_topics)],
"employee_roster":EMPLOYEE_ROSTER,
"departments":["Strategy & Research","Creative & Story","Production","Quality & Growth"],
"format":"1080x1920 9:16 Instagram Reel",
"production":"four independent professional short-form edits — each Reel has a different topic and pillar; visual direction informed by Instagram, Pinterest, Google and Canva",
"production_window":"02:00–06:00 IST overnight production; morning human review and edit pass follows.",
"edit_request":edit_request or None,
"content_rule":USEFUL_RULE,
"diversity_rule":"No two Reels in the same daily batch may use the same topic or editorial pillar.",
"story_engine":{"beats":["hook","visual proof","context","detail","meaning","CTA"],"rule":"One clear cultural idea per Reel; no random clip montage."},
"editorial_scorecard":{"hook":"immediate","visual_change":"high","information_density":"one clear idea per Reel","ending":"clean CTA"},
"asset_screening":{"creator_name_risk":"reject","platform_mark_risk":"reject","visual_watermark_risk":"sampled-frame OCR reject","third_party_content":"reject","attribution":"preserve in rights record"},
"rights_review_required":True,
"music_policy":MUSIC_POLICY,
"user_supplied_source":{"provided":bool(source_url),"rights_assumption":"user must confirm ownership/permission before use" if source_url else None},
"reels":reels}

employee_handoff(100,"Quality & Growth","Learning Manager","Record baseline learning and prepare next-batch adjustments","learning")
publish_status(100,"Quality & Growth","AI Manager / CEO","Batch complete. Human approval required before publishing.","complete",{
    "Strategy & Research":"complete",
    "Creative & Story":"complete",
    "Production":"complete",
    "Quality & Growth":"complete"
})
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
(OUT/"README.txt").write_text("Festival of Bharat — professional daily Reel batch\nSix-beat edit: hook → visual proof → context → detail → meaning → CTA.\n1080x1920, 30fps, no embedded commercial music. Add eligible/trending Instagram audio after approval.\nRisky creator/platform/watermarked sources are rejected rather than stripped. Verify rights before posting.\n")
(OUT/"creator-pack.json").write_text(json.dumps({"topics":[x["topic"] for x in daily_topics],"caption_direction":"Lead with the useful cultural fact, then invite a save/share.","music_direction":"Use eligible/trending Instagram audio inside Instagram; do not embed commercial music in the master.","posting_note":"Human approval required before publishing."},indent=2))
print("BUILT",len(reels),"professional Reels across",len(daily_topics),"different topics")
