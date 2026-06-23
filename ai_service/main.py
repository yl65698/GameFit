from __future__ import annotations

import json
import os
import re
from http.client import IncompleteRead
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="GameFit AI Search")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
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


class Equipment(BaseModel):
    id: int
    name: str
    type: str = ""
    price: int = 0
    fit: str = ""


class SearchRequest(BaseModel):
    query: str
    games: list[Game]


class EquipmentSearchRequest(BaseModel):
    query: str
    equipment: list[Equipment]


class SearchResponse(BaseModel):
    summary: str
    results: list[dict[str, Any]]
    source: str = "local"


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

EQUIPMENT_KEYWORD_MAP = {
    "qhd": ["GPU", "4070"],
    "그래픽": ["GPU", "4070"],
    "gpu": ["GPU"],
    "전략": ["CPU", "7800"],
    "시뮬": ["CPU", "7800"],
    "cpu": ["CPU"],
    "vr": ["VR", "Quest"],
    "용량": ["저장장치", "SSD"],
    "저장": ["저장장치", "SSD"],
    "마우스": ["주변장치", "마우스"],
    "헤드셋": ["주변장치", "헤드셋"],
    "음성": ["주변장치", "헤드셋"],
}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_ready": bool(get_api_key()),
        "model": get_model(),
    }


@app.post("/ai/search", response_model=SearchResponse)
def ai_search(payload: SearchRequest):
    catalog = [game.model_dump() for game in payload.games]
    llm = ask_gms_llm(
        task="game",
        query=payload.query,
        catalog=catalog,
        item_label="게임",
    )
    if llm:
        results = pick_results(catalog, llm.get("ids", []), llm.get("names", []))
        if results:
            return {
                "summary": llm.get("summary") or build_summary(payload.query, results),
                "results": results[:6],
                "source": "gms",
            }

    return local_game_search(payload)


@app.post("/ai/equipment-search", response_model=SearchResponse)
def ai_equipment_search(payload: EquipmentSearchRequest):
    catalog = [item.model_dump() for item in payload.equipment]
    llm = ask_gms_llm(
        task="equipment",
        query=payload.query,
        catalog=catalog,
        item_label="장비",
    )
    if llm:
        results = pick_results(catalog, llm.get("ids", []), llm.get("names", []))
        if results:
            return {
                "summary": llm.get("summary") or build_equipment_summary(payload.query, results),
                "results": results[:6],
                "source": "gms",
            }

    return local_equipment_search(payload)


def ask_gms_llm(task: str, query: str, catalog: list[dict[str, Any]], item_label: str) -> dict[str, Any] | None:
    api_key = get_api_key()
    if not api_key:
        return None

    model = get_model()
    prompt = build_llm_prompt(task, query, catalog, item_label)

    data = None
    if not is_full_chat_completions_url():
        data = call_responses_api(api_key, model, prompt)
    if data is None:
        data = call_chat_completions_api(api_key, model, prompt)

    if data is None:
        return None

    text = extract_gms_text(data)
    if not text:
        return None

    return parse_llm_json(text)


def call_responses_api(api_key: str, model: str, prompt: str) -> dict[str, Any] | None:
    url = build_api_url("responses")
    body = {
        "model": model,
        "input": prompt,
        "text": {
            "format": {
                "type": "json_object",
            },
        },
    }
    return post_llm_json(url, api_key, body)


def call_chat_completions_api(api_key: str, model: str, prompt: str) -> dict[str, Any] | None:
    url = build_api_url("chat/completions")
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "JSON만 반환하세요."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    return post_llm_json(url, api_key, body)


def post_llm_json(url: str, api_key: str, body: dict[str, Any]) -> dict[str, Any] | None:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            return parse_response_json(response.read().decode("utf-8"))
    except IncompleteRead as error:
        partial = error.partial.decode("utf-8", "ignore") if isinstance(error.partial, bytes) else str(error.partial)
        return parse_response_json(partial)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def parse_response_json(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if not cleaned:
        return None

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        if cleaned.startswith('"choices"') or cleaned.startswith('"id"') or cleaned.startswith('"output"'):
            try:
                data = json.loads("{" + cleaned)
            except json.JSONDecodeError:
                return None
        else:
            return None

    return data if isinstance(data, dict) else None


def parse_llm_json(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    if not isinstance(parsed, dict):
        return None
    return parsed


def build_api_url(path: str) -> str:
    base_url = (
        os.environ.get("GMS_API_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or "https://api.openai.com/v1"
    ).rstrip("/")
    if base_url.endswith("/responses") or base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/{path}"


def is_full_chat_completions_url() -> bool:
    base_url = (
        os.environ.get("GMS_API_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or "https://api.openai.com/v1"
    ).rstrip("/")
    return base_url.endswith("/chat/completions")


def build_llm_prompt(task: str, query: str, catalog: list[dict[str, Any]], item_label: str) -> str:
    compact_catalog = [
        {key: item.get(key) for key in ("id", "title", "name", "genre", "type", "price", "discount", "compatibility", "buy_signal", "summary", "fit") if key in item}
        for item in catalog[:30]
    ]
    return f"""
너는 GameFit의 {item_label} 검색 도우미야.
사용자의 자연어 요청을 보고 아래 후보 중 가장 적합한 항목을 골라줘.

규칙:
- 반드시 제공된 후보 안에서만 골라.
- 결과는 적합한 순서대로 최대 6개.
- JSON만 반환해.
- 스키마: {{"summary":"한국어 한 문장 추천 이유","ids":[숫자 id 배열],"names":["후보 이름 배열"]}}

검색 종류: {task}
사용자 요청: {query}
후보 목록:
{json.dumps(compact_catalog, ensure_ascii=False)}
""".strip()


def extract_gms_text(data: dict[str, Any]) -> str:
    if data.get("output_text"):
        return str(data["output_text"])

    output = data.get("output") or []
    for item in output:
        content = item.get("content") or []
        for part in content:
            if part.get("text"):
                return str(part["text"])

    choices = data.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        if message.get("content"):
            return str(message["content"])

    return ""


def pick_results(catalog: list[dict[str, Any]], ids: list[Any], names: list[Any]) -> list[dict[str, Any]]:
    by_id = {int(item["id"]): item for item in catalog if "id" in item}
    picked: list[dict[str, Any]] = []

    for raw_id in ids:
        try:
            item = by_id.get(int(raw_id))
        except (TypeError, ValueError):
            item = None
        if item and item not in picked:
            picked.append(item)

    normalized_names = [str(name).lower() for name in names]
    for name in normalized_names:
        for item in catalog:
            item_name = str(item.get("title") or item.get("name") or "").lower()
            if item_name and (item_name == name or name in item_name or item_name in name) and item not in picked:
                picked.append(item)

    return picked


def local_game_search(payload: SearchRequest) -> SearchResponse:
    query = payload.query.strip().lower()
    ranked = sorted(
        payload.games,
        key=lambda game: score_game(query, game),
        reverse=True,
    )
    results = [game.model_dump() for game in ranked if score_game(query, game) > 0]

    if not results:
        results = [game.model_dump() for game in ranked[:3]]

    return SearchResponse(
        summary=build_summary(payload.query, results),
        results=results[:6],
        source="local",
    )


def local_equipment_search(payload: EquipmentSearchRequest) -> SearchResponse:
    query = payload.query.strip().lower()
    ranked = sorted(
        payload.equipment,
        key=lambda item: score_equipment(query, item),
        reverse=True,
    )
    results = [item.model_dump() for item in ranked if score_equipment(query, item) > 0]

    if not results:
        results = [item.model_dump() for item in ranked[:3]]

    return SearchResponse(
        summary=build_equipment_summary(payload.query, results),
        results=results[:6],
        source="local",
    )


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


def score_equipment(query: str, item: Equipment) -> int:
    haystack = f"{item.name} {item.type} {item.fit}".lower()
    score = 0

    for token in query.split():
        if token and token in haystack:
            score += 4

    for keyword, hints in EQUIPMENT_KEYWORD_MAP.items():
        if keyword in query:
            for hint in hints:
                if hint.lower() in haystack:
                    score += 10

    return score


def build_summary(query: str, results: list[dict[str, Any]]) -> str:
    if not results:
        return f"'{query}' 조건에 맞는 게임을 찾지 못했습니다."

    top_titles = ", ".join(game["title"] for game in results[:3])
    return f"'{query}' 조건을 기준으로 {top_titles} 순서로 추천했어요."


def build_equipment_summary(query: str, results: list[dict[str, Any]]) -> str:
    if not results:
        return f"'{query}' 조건에 맞는 장비를 찾지 못했습니다."

    top_names = ", ".join(item["name"] for item in results[:3])
    return f"'{query}' 조건을 기준으로 {top_names} 순서로 추천했어요."


def get_api_key() -> str:
    load_env_files()
    return (
        os.environ.get("GMS_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or ""
    )


def get_model() -> str:
    load_env_files()
    return os.environ.get("GMS_MODEL") or os.environ.get("OPENAI_MODEL") or "gpt-5-nano"


def load_env_files() -> None:
    candidates = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    for path in candidates:
        if path.exists():
            load_env_file(path)


def load_env_file(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
