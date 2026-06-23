from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="GameFit AI Search")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Game(BaseModel):
    id: int
    title: str
    genre: str = ""
    price: int = 0
    discount: int = 0
    compatibility: str = ""
    buy_signal: str = ""
    summary: str = ""


class SearchRequest(BaseModel):
    query: str
    games: list[Game]


class SearchResponse(BaseModel):
    summary: str
    results: list[dict[str, Any]]


KEYWORD_MAP = {
    "친구": ["협동", "멀티", "It Takes Two"],
    "협동": ["협동", "It Takes Two"],
    "할인": ["discount"],
    "싸": ["discount"],
    "전략": ["전략", "Civilization"],
    "문명": ["Civilization"],
    "공포": ["공포", "Dead by Daylight"],
    "액션": ["액션", "Hades"],
    "가벼운": ["쾌적"],
    "내 pc": ["쾌적", "권장"],
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ai/search", response_model=SearchResponse)
def ai_search(payload: SearchRequest):
    query = payload.query.strip().lower()
    ranked = sorted(
        payload.games,
        key=lambda game: score_game(query, game),
        reverse=True,
    )
    results = [game.model_dump() for game in ranked if score_game(query, game) > 0]

    if not results:
        results = [game.model_dump() for game in ranked[:3]]

    return {
        "summary": build_summary(payload.query, results),
        "results": results[:6],
    }


def score_game(query: str, game: Game) -> int:
    haystack = f"{game.title} {game.genre} {game.compatibility} {game.buy_signal} {game.summary}".lower()
    score = 0

    for token in query.split():
        if token and token in haystack:
            score += 3

    for keyword, hints in KEYWORD_MAP.items():
        if keyword in query:
            for hint in hints:
                if hint == "discount":
                    score += game.discount
                elif hint.lower() in haystack:
                    score += 8

    if "할인" in query or "싸" in query:
        score += game.discount // 5
    if "지금" in query and "구매" in game.buy_signal:
        score += 6

    return score


def build_summary(query: str, results: list[dict[str, Any]]) -> str:
    if not results:
        return f"'{query}' 조건에 맞는 게임을 찾지 못했습니다."

    top_titles = ", ".join(game["title"] for game in results[:3])
    return f"'{query}' 조건을 기준으로 {top_titles} 순서로 추천했어요."
