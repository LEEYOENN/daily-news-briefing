import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
from backend.database import get_unanalyzed_articles, update_article_analysis, save_briefing, get_articles

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CATEGORIES = ["정치", "경제", "기술", "사회", "국제", "문화", "스포츠", "일반"]
SENTIMENTS = ["positive", "negative", "neutral"]

async def analyze_article(article: dict) -> dict:
    title = article.get("title", "")
    description = article.get("description", "")
    content = f"제목: {title}\n내용: {description}"

    prompt = f"""다음 뉴스 기사를 분석해주세요. 반드시 JSON만 반환하세요.

{content}

응답 형식:
{{
  "summary": "3줄 이내 한국어 요약",
  "sentiment": "positive 또는 negative 또는 neutral 중 하나",
  "keywords": "핵심 키워드 3개를 쉼표로 구분",
  "category": "{' 또는 '.join(CATEGORIES)} 중 가장 적합한 카테고리 하나"
}}"""

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return {
            "summary": result.get("summary", ""),
            "sentiment": result.get("sentiment", "neutral"),
            "keywords": result.get("keywords", ""),
            "category": result.get("category", article.get("category", "일반"))
        }
    except Exception as e:
        print(f"[analyzer] 분석 오류 ({article['id']}): {e}")
        return {
            "summary": "",
            "sentiment": "neutral",
            "keywords": "",
            "category": article.get("category", "일반")
        }

async def analyze_pending_articles():
    articles = await get_unanalyzed_articles(limit=20)
    if not articles:
        print("[analyzer] 분석할 기사 없음")
        return 0

    count = 0
    for article in articles:
        result = await analyze_article(article)
        if result["summary"]:
            await update_article_analysis(
                article["id"],
                result["summary"],
                result["sentiment"],
                result["keywords"],
                result["category"]
            )
            count += 1
    print(f"[analyzer] {count}건 분석 완료")
    return count

async def generate_daily_briefing() -> str:
    articles = await get_articles(limit=20)
    analyzed = [a for a in articles if a.get("summary")]

    if not analyzed:
        return "분석된 기사가 없어 브리핑을 생성할 수 없습니다."

    articles_text = "\n\n".join([
        f"[{a['category']}] {a['title']}\n요약: {a['summary']}\n감성: {a['sentiment']}\n키워드: {a['keywords']}"
        for a in analyzed[:15]
    ])

    prompt = f"""당신은 신문사 편집국의 AI 뉴스 브리핑 어시스턴트입니다.
다음 뉴스 기사들을 바탕으로 오늘의 핵심 이슈를 편집장에게 보고하는 형식으로 브리핑을 작성해주세요.

{articles_text}

작성 조건:
- 카테고리별로 핵심 이슈 2~3개씩 정리
- 전체 트렌드 요약 포함
- 한국어로 작성
- 실제 편집국 보고서처럼 간결하고 명확하게
- 마크다운 형식 사용 가능"""

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.5
        )
        briefing = response.choices[0].message.content
        await save_briefing(briefing, len(analyzed))
        return briefing
    except Exception as e:
        print(f"[analyzer] 브리핑 생성 오류: {e}")
        return f"브리핑 생성 중 오류가 발생했습니다: {str(e)}"
