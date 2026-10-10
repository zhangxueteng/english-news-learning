#!/usr/bin/env python3
"""Fetch licensed/public RSS headlines and generate original English-learning study notes.
Requires OPENAI_API_KEY GitHub secret. Only short headlines/metadata are sent for transformation;
the script does not scrape or republish full publisher articles or captions.
"""
import json, os, re, sys, time, urllib.request, urllib.error, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"
FEEDS = [
    ("BBC News", "https://feeds.bbci.co.uk/news/world/rss.xml", "WORLD"),
    ("BBC Science", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "SCIENCE"),
    ("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml", "TECHNOLOGY"),
]
UA = "NewslingoLearningSite/1.0 (RSS reader)"
def fetch(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA})
    with urllib.request.urlopen(req, timeout=25) as r: return r.read()
def text(tag, item):
    node=item.find(tag)
    return (node.text or "").strip() if node is not None else ""
def call_openai(headline, description, source, url, category):
    key=os.environ.get("OPENAI_API_KEY")
    if not key: return None
    prompt = """Create ONE English-learning news card based only on the metadata below. Do not invent facts. If the description is too thin to support a factual story, create a short language-learning explainer clearly labelled as background, not a news report. Output JSON object only with fields: title, titleZh, level (A1/A2/B1/B2/C1), category, summary (original 1-2 sentence summary, no copied article text), summaryZh, minutes (integer), sentences (3-5 objects with en, zh, note), vocab (3-5 objects with word,pos,ipa,zh,ex,exZh,tip), grammar (2-3 objects with title,body). Sentence text must be original paraphrase, not copied from source. Keep claims faithful to supplied metadata; no fabricated quotations or numbers. Use natural simplified Chinese translations. The source URL is for reader attribution only."""
    payload={"model":os.environ.get("OPENAI_MODEL","gpt-4.1-mini"),"messages":[{"role":"system","content":prompt},{"role":"user","content":json.dumps({"headline":headline,"description":description[:900],"publisher":source,"url":url,"category":category},ensure_ascii=False)}],"temperature":0.3,"response_format":{"type":"json_object"}}
    req=urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","User-Agent":UA}, method="POST")
    with urllib.request.urlopen(req,timeout=60) as r: result=json.loads(r.read())
    content=result["choices"][0]["message"]["content"]
    return json.loads(content)
def main():
    key=os.environ.get("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY is not configured; keep existing content and exit without overwriting.")
        return 0
    articles=[]
    seen=set()
    for publisher, feed, category in FEEDS:
        try:
            root=ET.fromstring(fetch(feed))
            for item in root.findall(".//item"):
                title=text("title",item); url=text("link",item); desc=re.sub("<[^>]+>"," ",text("description",item))
                if not title or not url or url in seen: continue
                seen.add(url)
                try:
                    data=call_openai(title,desc,publisher,url,category)
                    if not data: continue
                    data.update({"id":"news-"+str(abs(hash(url))),"source":publisher,"date":datetime.now(timezone.utc).date().isoformat(),"articleUrl":url,"videoUrl":"","videoEmbed":"","demo":False,"sourceNote":"Original publisher link"})
                    data["art"]="◈"; data["color"]="linear-gradient(135deg,#173c6a,#5a83bd)"
                    articles.append(data)
                    if len(articles)>=10: break
                    time.sleep(0.8)
                except Exception as e: print("AI processing failed:",title,repr(e),file=sys.stderr)
            if len(articles)>=10: break
        except Exception as e: print("RSS feed failed:",feed,repr(e),file=sys.stderr)
    if not articles:
        print("No articles generated; preserving current JSON.",file=sys.stderr)
        return 0
    payload={"updated_at":datetime.now(timezone.utc).isoformat(),"articles":articles,"notice":"Generated from RSS metadata. Check source links; summaries and learning notes are AI-generated."}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Wrote",len(articles),"learning articles to",OUT)
    return 0
if __name__=="__main__": raise SystemExit(main())
