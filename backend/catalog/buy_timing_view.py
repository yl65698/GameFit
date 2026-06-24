import json
import os

from openai import OpenAI
from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Game
from .itad_service import get_live_prices
from .buy_timing import compute_buy_score

_SIGNAL_DEFAULTS = {
    "buy_now": (
        "지금 구매 추천",
        "현재 가격이 역대 최저가에 근접한 수준으로, 지금 바로 구매하기 좋은 타이밍이에요.",
    ),
    "good": (
        "좋은 가격",
        "현재 할인폭이 괜찮은 편이에요. 역대 최저가는 아니지만 충분히 구매를 고려할 만한 가격이에요.",
    ),
    "watch": (
        "조금 더 지켜보세요",
        "현재 가격이 나쁘지 않지만, 더 낮아질 가능성이 있어요. 관심게임 등록 후 알림을 받아보세요.",
    ),
    "wait": (
        "다음 세일까지 대기",
        "현재 할인율이 낮아요. Steam 대형 세일(여름·연말) 때 다시 확인하는 걸 추천해요.",
    ),
}


def _build_client():
    return OpenAI(
        api_key=os.environ.get("GMS_API_KEY", ""),
        base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1",
    )


def _generate_timing_text(title: str, analysis: dict) -> dict:
    signal = analysis["signal"]
    score = analysis["score"]
    discount = analysis["discount"]
    current_price = analysis.get("current_price") or 0
    history_low_all = analysis.get("history_low_all")
    factors = analysis.get("factors") or []

    positive = [f for f in factors if f["positive"]]
    negative = [f for f in factors if not f["positive"]]

    factor_lines = "\n".join(
        [f"(긍정) {f['label']}: {f['detail']}" for f in positive]
        + [f"(부정) {f['label']}: {f['detail']}" for f in negative]
    )

    low_text = f"역대 최저가 {history_low_all:,}원" if history_low_all else "역대 최저가 정보 없음"
    price_text = f"현재 최저가 {current_price:,}원" if current_price else "가격 정보 없음"

    user_msg = (
        f'게임: "{title}"\n'
        f"{price_text} / 할인율 {discount}% / {low_text}\n"
        f"종합 점수: {score}/100\n"
        f"분석 요소:\n{factor_lines}\n\n"
        "위 분석을 바탕으로 한국어 구매 추천 문구를 작성하세요.\n"
        'JSON만 출력: {"headline": "핵심 메시지 (12자 이내)", "message": "자세한 설명 (70자 이내)"}'
    )

    try:
        client = _build_client()
        resp = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "게임 구매 타이밍 분석 전문가. JSON만 출력. 숫자 언급 최소화, 자연스러운 문장 작성."},
                {"role": "user", "content": user_msg},
            ],
        )
        raw = resp.choices[0].message.content or ""
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(cleaned)
        headline = result.get("headline") or _SIGNAL_DEFAULTS[signal][0]
        message = result.get("message") or _SIGNAL_DEFAULTS[signal][1]
        return {"headline": headline, "message": message}
    except Exception:
        return {"headline": _SIGNAL_DEFAULTS[signal][0], "message": _SIGNAL_DEFAULTS[signal][1]}


class GameBuyTimingView(APIView):
    def get(self, request, game_id):
        try:
            game = Game.objects.only(
                "id", "title", "itad_id", "price", "original_price",
                "discount_percent", "release_date",
            ).get(pk=game_id)
        except Game.DoesNotExist:
            return Response({"detail": "게임을 찾을 수 없습니다."}, status=404)

        live_prices = {}
        if game.itad_id:
            result = get_live_prices(str(game.itad_id))
            if isinstance(result, dict):
                live_prices = result

        game_data = {
            "title": game.title,
            "price": int(game.price or 0),
            "discount_percent": game.discount_percent or 0,
            "release_date": str(game.release_date) if game.release_date else None,
        }

        analysis = compute_buy_score(game_data, live_prices)
        text = _generate_timing_text(game.title, analysis)

        return Response({**analysis, **text})
