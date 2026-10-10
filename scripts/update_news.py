#!/usr/bin/env python3
"""Build Newslingo from official news-channel videos so every published card has original English audio.
No paid API key is required. Video playback stays hosted by the publisher's official YouTube channel.
"""
import json, re, sys, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"
UA = "NewslingoLearningSite/1.0 (official news video RSS learning mode)"
# Official publisher channels. YouTube hosts the original video/audio; we do not download or rehost it.
VIDEO_FEEDS = [
    ("BBC News", "UC16niRr50-MSBwiO3YDb3RA", "WORLD"),
    ("CNN", "UCupvZG-5ko_eiXm5pPj9ZtA", "WORLD"),
]
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}
STOP = set("the a an and or but if to of in on at for from by with as is are was were be been being it its this that these those how why what when where who which after before over under into about against more most new says said could would should will may might their his her they them we you your our has have had not no".split())

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read()

def translate(text):
    if not text:
        return None
    params = urllib.parse.urlencode({"q": text[:450], "langpair": "en|zh-CN"})
    req = urllib.request.Request("https://api.mymemory.translated.net/get?" + params, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
        translated = data.get("responseData", {}).get("translatedText", "").strip()
        if data.get("responseStatus") == 200 and translated and translated.lower() != text.lower():
            return translated
    except Exception as exc:
        print("Free translation unavailable:", type(exc).__name__, file=sys.stderr)
    return None

def level_for(title):
    words = re.findall(r"[A-Za-z']+", title)
    advanced = {"corroborate","geopolitical","legislation","infrastructure","amid","amidst","scrutiny","resilience","volatile","sovereignty","mitigate","consecutive","surge","pledge"}
    count = sum(1 for w in words if w.lower() in advanced)
    if count >= 2 or len(words) >= 15: return "C1"
    if count or len(words) >= 12: return "B2"
    if len(words) >= 8: return "B1"
    if len(words) >= 5: return "A2"
    return "A1"

def category_for(title, default):
    t = title.lower()
    for words, cat in [
        (("technology","artificial intelligence","cyber","smartphone","robot","space"), "TECHNOLOGY"),
        (("climate","weather","wildfire","earthquake","flood","environment"), "SCIENCE"),
        (("business","market","stock","economy","trade","oil price"), "BUSINESS"),
        (("sport","football","soccer","tennis","olympic"), "SPORTS"),
        (("health","hospital","medical","disease"), "HEALTH"),
    ]:
        if any(w in t for w in words): return cat
    return default

def make_video_card(title, video_id, publisher, default_category, published, description=""):
    title_zh = translate(title) or "标题翻译暂不可用，请先听原声并查看视频说明。"
    time.sleep(0.8)
    words = [w for w in re.findall(r"[A-Za-z']{4,}", title) if w.lower() not in STOP]
    vocab = [{
        "word": word, "pos": "headline vocabulary", "ipa": "",
        "zh": "请结合原声视频标题与语境理解该词。",
        "ex": title, "exZh": title_zh,
        "tip": "听原声时留意这个词的重音、发音和上下文。"
    } for word in words[:4]]
    reading = [
        f'The original news video is titled: "{title}". Listen to the report and note the main people, places and events.',
        "As you listen, separate confirmed information from opinions and predictions. Pay attention to names, dates, numbers and direct quotations.",
        "After listening, summarise the report in your own words and compare your understanding with the publisher's video description or linked coverage."
    ]
    reading_zh = [
        f'这段新闻原声视频的标题是：“{title_zh}”。请听报道，并记录主要人物、地点和事件。',
        "听新闻时，应区分已确认的信息、观点和预测。注意人名、日期、数字以及直接引语。",
        "听完后，尝试用自己的话概括报道，再对照媒体的视频说明或相关报道检查理解。"
    ]
    notes = [
        "is titled 表示“标题为……”；listen to 后面接听的对象。",
        "separate A from B = 区分 A 与 B；pay attention to = 留意。",
        "in your own words = 用自己的话；compare A with B = 把 A 与 B 对照。"
    ]
    sentences = [{"en": reading[i], "zh": reading_zh[i], "note": notes[i]} for i in range(3)]
    date = published or datetime.now(timezone.utc).date().isoformat()
    watch_url = "https://www.youtube.com/watch?v=" + video_id
    return {
        "id": "video-" + video_id,
        "title": title,
        "titleZh": title_zh,
        "level": level_for(title),
        "category": category_for(title, default_category),
        "source": publisher + " · Official Video",
        "date": date,
        "minutes": 5,
        "summary": description or "Watch the original report from the publisher's official news video channel.",
        "summaryZh": "直接播放媒体官方频道发布的新闻视频，保留记者原声、现场声音及原始语速。",
        "art": "▶",
        "color": "linear-gradient(135deg,#173c6a,#5a83bd)",
        "videoUrl": watch_url,
        "videoEmbed": "https://www.youtube-nocookie.com/embed/" + video_id,
        "articleUrl": watch_url,
        "demo": False,
        "sourceNote": "Official publisher video · original English audio",
        "readingText": "\n\n".join(reading),
        "readingTextZh": "\n\n".join(reading_zh),
        "sentences": sentences,
        "vocab": vocab,
        "grammar": [
            {"title": "听力训练建议", "body": "第一遍不暂停，抓主旨；第二遍记录人物、地点、数字和关键动词；第三遍结合词汇解析复听。视频本身为媒体原声，学习正文为辅助训练材料。"},
            {"title": "难度说明", "body": "A1–C1 等级根据标题长度和部分词汇线索估算，仅供学习参考，并非官方 CEFR 评定。"}
        ]
    }

def main():
    articles, seen = [], set()
    cutoff = datetime.now(timezone.utc).timestamp() - 14 * 86400
    per_feed_limit = 4
    for publisher, channel_id, category in VIDEO_FEEDS:
        feed = "https://www.youtube.com/feeds/videos.xml?channel_id=" + channel_id
        try:
            root = ET.fromstring(fetch(feed))
            entries = root.findall("atom:entry", NS)
            print("Fetched", len(entries), "official videos from", publisher)
            added_from_feed = 0
            for entry in entries:
                title_node = entry.find("atom:title", NS)
                id_node = entry.find("yt:videoId", NS)
                published_node = entry.find("atom:published", NS)
                if title_node is None or id_node is None:
                    continue
                title, video_id = (title_node.text or "").strip(), (id_node.text or "").strip()
                if not title or not video_id or video_id in seen:
                    continue
                published = ""
                if published_node is not None and published_node.text:
                    try:
                        dt = datetime.fromisoformat(published_node.text.replace("Z", "+00:00"))
                        if dt.timestamp() < cutoff:
                            continue
                        published = dt.date().isoformat()
                    except Exception:
                        pass
                description_node = entry.find("media:group/media:description", NS)
                description = (description_node.text or "").strip() if description_node is not None else ""
                # Avoid music, promos and non-news material where the title makes that clear.
                if re.search(r"\b(music video|official trailer|livestream replay|full episode)\b", title, re.I):
                    continue
                seen.add(video_id)
                articles.append(make_video_card(title, video_id, publisher, category, published, description))
                added_from_feed += 1
                if added_from_feed >= per_feed_limit or len(articles) >= 8:
                    break
            if len(articles) >= 8:
                break
        except Exception as exc:
            print("Official video feed failed:", publisher, repr(exc), file=sys.stderr)
    if not articles:
        print("No official videos found. Preserving existing data rather than publishing text-only cards.", file=sys.stderr)
        return 0
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "official-video-rss",
        "articles": articles,
        "notice": "All published news cards link to or embed videos from official publisher YouTube channels so playback uses original English audio. If an official channel feed is temporarily unavailable, the updater preserves the last known dataset instead of replacing it with text-only cards."
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", len(articles), "original-audio news cards to", OUT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
