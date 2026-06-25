import json
import os

from openai import OpenAI
from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Game
from .adapters import game_to_catalog

SYSTEM_PROMPT = """게임 검색 AI. 사용자 검색어와 게임 카탈로그(id,title,tags=장르목록,desc,dc=할인율)를 보고 관련 게임을 찾아라. tags 필드를 우선 활용해 장르 매칭 정확도를 높여라.
JSON만 출력:{"game_ids":[id,...최대10개],"summary":"한국어 결과 요약","intent":"파악한 검색의도"}"""


def _build_client():
    return OpenAI(
        api_key=os.environ.get("GMS_API_KEY", ""),
        base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1",
    )


def _compact_game(game):
    desc = (game.description or "").strip()
    genre_tags = [gg.genre.name for gg in game.game_genres.all()]
    return {
        "id": game.id,
        "title": game.title,
        "tags": genre_tags[:6],
        "desc": desc[:60] if desc else "",
        "dc": game.discount_percent,
    }


class AISearchView(APIView):
    def post(self, request):
        query = (request.data.get("query") or "").strip()
        if not query:
            return Response({"detail": "검색어를 입력해주세요."}, status=400)

        games = list(Game.objects.prefetch_related("game_genres__genre").all()[:200])
        if not games:
            return Response({"results": [], "summary": "등록된 게임이 없습니다.", "intent": ""})

        compact = [_compact_game(g) for g in games[:100]]
        user_message = (
            f'검색어: "{query}"\n'
            f"카탈로그: {json.dumps(compact, ensure_ascii=False, separators=(',', ':'))}"
        )

        client = _build_client()
        try:
            response = client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            choice = response.choices[0]
            raw = choice.message.content or ""
            print(f"[AI Search] finish_reason={choice.finish_reason}, raw={repr(raw[:300])}")

            if not raw:
                return Response({"detail": f"AI가 빈 응답을 반환했습니다. finish_reason={choice.finish_reason}"}, status=500)

            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            return Response({"detail": f"JSON 파싱 실패. AI 원본 응답: {raw[:300]}"}, status=500)
        except Exception as e:
            return Response({"detail": f"AI 검색 오류: {str(e)}"}, status=500)

        game_ids = result.get("game_ids") or []
        summary = result.get("summary") or ""
        intent = result.get("intent") or ""

        game_map = {g.id: g for g in games}
        matched = [
            game_to_catalog(game_map[gid], request, include_price_history=False)
            for gid in game_ids
            if gid in game_map
        ]

        return Response({"results": matched, "summary": summary, "intent": intent})
