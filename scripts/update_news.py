#!/usr/bin/env python3
"""Free daily news mode: fetch RSS headlines and translate headlines using MyMemory.
No OpenAI key or paid AI service is required. Full publisher articles are not copied.
"""
import json, re, sys, time, urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"
FEEDS = [
    ("BBC News", "https://feeds.bbci.co.uk/news/world/rss.xml", "WORLD"),
    ("BBC Science", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "SCIENCE"),
    ("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml", "TECHNOLOGY"),
]
UA = "NewslingoLearningSite/1.0 (free RSS learning mode)"
STOP = set("the a an and or but if to of in on at for from by with as is are was were be been being it its this that these those how why what when where who which after before over under into about against more most new says said could would should will may might their his her they them we you your our has have had not no".split())

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read()

def field(item, tag):
    node = item.find(tag)
    return (node.text or "").strip() if node is not None else ""

def translate(text):
    """Use a public no-key translation endpoint; return None when unavailable."""
    if not text:
        return None
    params = urllib.parse.urlencode({"q": text[:450], "langpair": "en|zh-CN"})
    req = urllib.request.Request(
        "https://api.mymemory.translated.net/get?" + params,
        headers={"User-Agent": UA}
    )
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
    advanced = {"corroborate","geopolitical","legislation","infrastructure","amid","amidst","scrutiny","resilience","volatile","sovereignty","mitigate","consecutive","surge","pledge","amid","amidst"}
    count = sum(1 for w in words if w.lower() in advanced)
    if count >= 2 or len(words) >= 15: return "C1"
    if count or len(words) >= 12: return "B2"
    if len(words) >= 8: return "B1"
    if len(words) >= 5: return "A2"
    return "A1"

def make_card(title, url, publisher, category, published):
    zh = translate(title)
    time.sleep(1.2)
    level = level_for(title)
    words = [w for w in re.findall(r"[A-Za-z']{4,}", title) if w.lower() not in STOP]
    vocab = []
    for word in words[:4]:
        vocab.append({
            "word": word,
            "pos": "headline vocabulary",
            "ipa": "",
            "zh": "点击英文单词查看词义；建议结合标题语境理解。",
            "ex": title,
            "exZh": zh or "本次免费翻译服务暂不可用。",
            "tip": "这是新闻标题中的重点词。点击正文中带下划线的单词，可查看本地学习提示。"
        })
    sentence = {
        "en": title,
        "zh": zh or "免费翻译服务暂不可用，请点击原文链接核对标题含义。",
        "note": "新闻标题常省略冠词、助动词或 be 动词。阅读时先找核心名词和动词，再判断事件、人物与时间。标题翻译由免费公共翻译服务提供，建议结合原文核对。"
    }
    date = published or datetime.now(timezone.utc).date().isoformat()
    return {
        "id": "rss-" + str(abs(hash(url))),
        "title": title,
        "titleZh": zh or "标题翻译暂不可用",
        "level": level,
        "category": category,
        "source": publisher,
        "date": date,
        "minutes": 3,
        "summary": "Free daily RSS headline. Open the publisher's page for the full report; Newslingo does not republish the full article.",
        "summaryZh": "免费每日新闻标题学习卡。请打开原始媒体链接阅读完整报道；本站不转载完整文章。",
        "art": "◈",
        "color": "linear-gradient(135deg,#173c6a,#5a83bd)",
        "videoUrl": "https://www.youtube.com/results?search_query=" + urllib.parse.quote(title + " news video"),
        "articleUrl": url,
        "demo": False,
        "sourceNote": "RSS headline · free translation · open original publisher",
        "sentences": [sentence],
        "vocab": vocab,
        "grammar": [
            {"title": "新闻标题语序", "body": "英文新闻标题常使用简洁表达，可能省略冠词、be 动词或助动词。阅读时先识别核心主语和谓语，再理解修饰语。"},
            {"title": "分级说明", "body": "A1–C1 等级根据标题长度和部分词汇线索自动估算，仅供学习参考，并非官方 CEFR 评定。"}
        ]
    }

def main():
    articles, seen = [], set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    for publisher, feed, category in FEEDS:
        try:
            root = ET.fromstring(fetch(feed))
            for item in root.findall(".//item"):
                title = field(item, "title")
                url = field(item, "link")
                if not title or not url or url in seen:
                    continue
                seen.add(url)
                pub = field(item, "pubDate")
                date = ""
                if pub:
                    try:
                        dt = parsedate_to_datetime(pub)
                        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                        if dt < cutoff:
                            continue
                        date = dt.date().isoformat()
                    except Exception:
                        pass
                articles.append(make_card(title, url, publisher, category, date))
                if len(articles) >= 5:
                    break
            if len(articles) >= 5:
                break
        except Exception as exc:
            print("RSS feed failed:", feed, repr(exc), file=sys.stderr)
    if not articles:
        print("No fresh RSS articles found; preserving current JSON.", file=sys.stderr)
        return 0
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "free-rss",
        "articles": articles,
        "notice": "Free RSS mode: headlines and source links are updated daily. Headline translation uses a public no-key translation endpoint and may be unavailable or inaccurate. Full articles and videos are opened at their original sources."
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", len(articles), "free RSS learning cards to", OUT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
