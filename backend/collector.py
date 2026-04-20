import httpx
import feedparser
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# RSS 피드 목록
RSS_FEEDS = [
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC", "category": "국제"},
    {"url": "https://rss.cnn.com/rss/edition.rss", "source": "CNN", "category": "국제"},
    {"url": "https://www.yonhapnewstv.co.kr/category/news/rss", "source": "연합뉴스TV", "category": "국내"},
]

# NewsAPI 검색 키워드/카테고리
NEWSAPI_QUERIES = [
    {"q": "Korea economy", "category": "경제"},
    {"q": "artificial intelligence technology", "category": "기술"},
    {"q": "Korea politics", "category": "정치"},
    {"q": "global market finance", "category": "경제"},
    {"q": "science environment", "category": "사회"},
]

async def fetch_newsapi(query: str, category: str) -> list[dict]:
    articles = []
    if not NEWS_API_KEY:
        print("[collector] NEWS_API_KEY 없음, NewsAPI 스킵")
        return articles
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(NEWS_API_URL, params={
                "q": query,
                "apiKey": NEWS_API_KEY,
                "language": "en",
                "pageSize": 10,
                "sortBy": "publishedAt"
            })
            data = resp.json()
            for item in data.get("articles", []):
                if not item.get("url") or not item.get("title"):
                    continue
                if item["title"] == "[Removed]":
                    continue
                articles.append({
                    "title": item["title"],
                    "description": item.get("description") or "",
                    "url": item["url"],
                    "source": item.get("source", {}).get("name", "NewsAPI"),
                    "category": category,
                    "published_at": item.get("publishedAt", "")
                })
    except Exception as e:
        print(f"[collector] NewsAPI 오류 ({query}): {e}")
    return articles

async def fetch_rss(feed_url: str, source: str, category: str) -> list[dict]:
    articles = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(feed_url, follow_redirects=True)
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:10]:
                url = entry.get("link", "")
                title = entry.get("title", "")
                if not url or not title:
                    continue
                published = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                    except Exception:
                        pass
                articles.append({
                    "title": title,
                    "description": entry.get("summary", "")[:500],
                    "url": url,
                    "source": source,
                    "category": category,
                    "published_at": published
                })
    except Exception as e:
        print(f"[collector] RSS 오류 ({source}): {e}")
    return articles

async def collect_all_news() -> list[dict]:
    all_articles = []

    # NewsAPI 수집
    for config in NEWSAPI_QUERIES:
        articles = await fetch_newsapi(config["q"], config["category"])
        all_articles.extend(articles)
        print(f"[collector] NewsAPI '{config['q']}': {len(articles)}건")

    # RSS 수집
    for feed in RSS_FEEDS:
        articles = await fetch_rss(feed["url"], feed["source"], feed["category"])
        all_articles.extend(articles)
        print(f"[collector] RSS '{feed['source']}': {len(articles)}건")

    print(f"[collector] 총 수집: {len(all_articles)}건")
    return all_articles
