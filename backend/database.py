import aiosqlite
import hashlib
from datetime import datetime

DB_PATH = "news.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL,
                source TEXT,
                category TEXT DEFAULT '일반',
                published_at TEXT,
                collected_at TEXT NOT NULL,
                summary TEXT,
                sentiment TEXT DEFAULT 'neutral',
                keywords TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS briefings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                content TEXT NOT NULL,
                article_count INTEGER DEFAULT 0
            )
        """)
        await db.commit()

def make_url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()

async def save_articles(articles: list[dict]) -> int:
    saved = 0
    async with aiosqlite.connect(DB_PATH) as db:
        for article in articles:
            url_hash = make_url_hash(article["url"])
            try:
                await db.execute("""
                    INSERT INTO articles 
                    (url_hash, title, description, url, source, category, published_at, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    url_hash,
                    article.get("title", ""),
                    article.get("description", ""),
                    article.get("url", ""),
                    article.get("source", ""),
                    article.get("category", "일반"),
                    article.get("published_at", ""),
                    datetime.now().isoformat()
                ))
                saved += 1
            except aiosqlite.IntegrityError:
                pass  # 중복 URL 스킵
        await db.commit()
    return saved

async def get_articles(limit: int = 50, category: str = None, keyword: str = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        if category and category != "전체":
            query += " AND category = ?"
            params.append(category)
        if keyword:
            query += " AND (title LIKE ? OR description LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        query += " ORDER BY collected_at DESC LIMIT ?"
        params.append(limit)
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_unanalyzed_articles(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM articles WHERE summary IS NULL ORDER BY collected_at DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def update_article_analysis(article_id: int, summary: str, sentiment: str, keywords: str, category: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE articles SET summary=?, sentiment=?, keywords=?, category=?
            WHERE id=?
        """, (summary, sentiment, keywords, category, article_id))
        await db.commit()

async def save_briefing(content: str, article_count: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO briefings (created_at, content, article_count) VALUES (?, ?, ?)",
            (datetime.now().isoformat(), content, article_count)
        )
        await db.commit()

async def get_latest_briefing() -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM briefings ORDER BY created_at DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM articles") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM articles WHERE summary IS NOT NULL") as cur:
            analyzed = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT category, COUNT(*) as cnt FROM articles GROUP BY category ORDER BY cnt DESC"
        ) as cur:
            rows = await cur.fetchall()
            categories = [{"category": r[0], "count": r[1]} for r in rows]
        async with db.execute(
            "SELECT sentiment, COUNT(*) as cnt FROM articles WHERE sentiment IS NOT NULL GROUP BY sentiment"
        ) as cur:
            rows = await cur.fetchall()
            sentiments = {r[0]: r[1] for r in rows}
    return {
        "total": total,
        "analyzed": analyzed,
        "categories": categories,
        "sentiments": sentiments
    }
