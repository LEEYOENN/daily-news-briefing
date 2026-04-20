# Daily News Briefing

> AI 기반 뉴스 자동 수집·분석·보고 시스템 — 서울신문 실무평가 과제

편집국 기자들이 매일 수동으로 수행하던 뉴스 모니터링을 자동화하는 시스템입니다.  
NewsAPI와 RSS 피드에서 국내외 주요 이슈를 실시간 수집하고, LLM이 요약·감성분석·카테고리 분류를 수행한 뒤 웹 대시보드로 자동 보고합니다.

---

## 시스템 흐름

```
[NewsAPI / RSS 피드]
        ↓ 30분 간격 자동 수집 (APScheduler)
[FastAPI 백엔드]
        ↓ LLM API 호출 (백엔드에서만)
[OpenAI GPT-5.4-mini] → 요약 / 감성분석 / 카테고리 분류
        ↓
[SQLite DB] → 중복 제거(URL hash) 후 저장
        ↓
[웹 대시보드] → 실시간 뉴스 카드 / AI 브리핑 보고서
```

## 기술 스택

| 영역 | 기술 |
|---|---|
| 백엔드 | Python 3.11+, FastAPI, APScheduler |
| LLM | OpenAI GPT-5.4-mini |
| 뉴스 소스 | NewsAPI.org, RSS (BBC, CNN, 연합뉴스TV) |
| DB | SQLite (aiosqlite) |
| 프론트엔드 | HTML + Vanilla JS (빌드 도구 없음) |

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 키를 입력합니다:

```
NEWS_API_KEY=발급받은_NewsAPI_키
OPENAI_API_KEY=발급받은_OpenAI_키
OPENAI_MODEL=gpt-5.4-mini
```

**NewsAPI 키 발급:** https://newsapi.org/register (무료, 이메일 인증 즉시 발급)

### 3. 서버 실행

```bash
uvicorn backend.main:app --reload
```

브라우저에서 http://localhost:8000 접속

## 주요 기능

- **자동 수집** — 30분 간격으로 NewsAPI + RSS 피드에서 뉴스 수집, URL 해시 기반 중복 제거
- **AI 분석** — 기사별 3줄 요약, 감성(긍정/부정/중립), 카테고리 자동 분류
- **대시보드** — 카테고리 필터, 키워드 검색, 감성 분포 바, 1분 자동 갱신
- **AI 브리핑** — 버튼 클릭 한 번으로 편집국 보고서 형식의 일일 브리핑 생성
- **수동 제어** — 즉시 수집 / 즉시 분석 버튼

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/articles` | 기사 목록 (category, keyword, limit 쿼리 파라미터) |
| GET | `/api/stats` | 통계 (전체 건수, 분석 건수, 카테고리·감성 분포) |
| GET | `/api/briefing` | 최신 브리핑 조회 |
| POST | `/api/briefing/generate` | AI 브리핑 생성 |
| POST | `/api/collect` | 즉시 수집 트리거 |
| POST | `/api/analyze` | 즉시 분석 트리거 |

## AI 도구 사용

- **Claude (claude.ai)** — 시스템 설계, 코드 전체 작성에 활용
- 개발 플로우: 요구사항 분석 → 아키텍처 설계 → 백엔드 코드 생성 → 프론트엔드 코드 생성 → README 작성

## 구현 조건 충족 여부

- [x] 웹 기반 클라이언트
- [x] LLM API 호출은 백엔드(FastAPI)에서만 수행 — 프론트엔드 직접 호출 없음
- [x] 로컬 환경 실행 가능
- [x] 선택 모델: GPT-5.4-mini (과제 조건 내 모델)
- [x] 공개 API(NewsAPI) + 검색도구(RSS) 활용
- [x] 실시간 수집·분석·자동 보고 시스템 구현
