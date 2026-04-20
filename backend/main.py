from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio

from backend.database import init_db, get_articles, get_stats, get_latest_briefing
from backend.collector import collect_all_news
from backend.database import save_articles
from backend.analyzer import analyze_pending_articles, generate_daily_briefing
from backend.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    await init_db()
    print("[main] DB 초기화 완료")
    # 최초 수집 (비동기로 백그라운드에서)
    asyncio.create_task(initial_collect())
    start_scheduler()
    yield
    # 종료 시
    stop_scheduler()

async def initial_collect():
    print("[main] 최초 뉴스 수집 시작")
    articles = await collect_all_news()
    saved = await save_articles(articles)
    print(f"[main] 최초 수집 완료: {saved}건 저장")
    await analyze_pending_articles()

app = FastAPI(title="Daily News Briefing", lifespan=lifespan)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

# ── API 엔드포인트 ──

@app.get("/api/articles")
async def api_get_articles(
    limit: int = Query(50, ge=1, le=200),
    category: str = Query(None),
    keyword: str = Query(None)
):
    articles = await get_articles(limit=limit, category=category, keyword=keyword)
    return {"articles": articles, "count": len(articles)}

@app.get("/api/stats")
async def api_get_stats():
    return await get_stats()

@app.get("/api/briefing")
async def api_get_briefing():
    briefing = await get_latest_briefing()
    return briefing or {"content": None, "created_at": None}

@app.post("/api/briefing/generate")
async def api_generate_briefing():
    content = await generate_daily_briefing()
    return {"content": content}

@app.post("/api/collect")
async def api_trigger_collect():
    articles = await collect_all_news()
    saved = await save_articles(articles)
    analyzed = await analyze_pending_articles()
    return {"collected": len(articles), "saved": saved, "analyzed": analyzed}

@app.post("/api/analyze")
async def api_trigger_analyze():
    count = await analyze_pending_articles()
    return {"analyzed": count}
