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

WATERMARK_RISK=re.compile(r"watermark|logo|channel|creator|youtube|instagram|tiktok|facebook|reel|shorts|©|www\\.",re.I)

def reject_source(title, author, page):
    text=" ".join([str(title or ""),str(author or ""),str(page or "")])
    return bool(WATERMARK_RISK.search(text))

def add_source_asset(title,url,license_name,author,page,file_path=None,kind="video"):
    if reject_source(title,author,page):
        print("REJECTED creator/watermark-risk source:", title)
        return False
    assets.append({
        "title":title,"url":url,"license":license_name or "License not displayed",
        "author":author,"page":page,"kind":kind,"rights_review":True,**({"file":file_path} if file_path else {})
    })
    return True
