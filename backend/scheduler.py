from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.collector import collect_all_news
from backend.database import save_articles
from backend.analyzer import analyze_pending_articles

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

async def collect_and_analyze():
    print("[scheduler] 뉴스 수집 시작")
    articles = await collect_all_news()
    saved = await save_articles(articles)
    print(f"[scheduler] 신규 저장: {saved}건")
    analyzed = await analyze_pending_articles()
    print(f"[scheduler] 분석 완료: {analyzed}건")

def start_scheduler():
    # 30분마다 수집
    scheduler.add_job(collect_and_analyze, "interval", minutes=30, id="collect_news")
    scheduler.start()
    print("[scheduler] 스케줄러 시작 (30분 간격)")

def stop_scheduler():
    scheduler.shutdown()
