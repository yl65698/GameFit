import json
import os

from openai import OpenAI
from rest_framework.response import Response
from rest_framework.views import APIView

from hardware.models import Hardware
from .adapters import hardware_to_catalog

SYSTEM_PROMPT = """게임용 PC 장비 추천 AI. 사용자의 요구사항과 장비 목록(id,name,cat=카테고리,bench=벤치마크,price,spec)을 보고 최적 장비를 찾아라.
요구사항: 게임 환경, 해상도, 예산, 업그레이드 목적 등을 반영해 bench 높은 순으로 추천해라.
JSON만 출력:{"hw_ids":[id,...최대8개],"summary":"한국어 추천 이유 요약","intent":"파악한 요구사항"}"""


def _build_client():
    return OpenAI(
        api_key=os.environ.get("GMS_API_KEY", ""),
        base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1",
    )


def _compact_hw(item):
    spec = (item.specs or "").strip()
    return {
        "id": item.id,
        "name": item.name,
        "cat": item.get_category_display(),
        "bench": item.benchmark_score,
        "price": int(item.price or 0),
        "spec": spec[:60] if spec else "",
    }


class AIEquipmentSearchView(APIView):
    def post(self, request):
        query = (request.data.get("query") or "").strip()
        if not query:
            return Response({"detail": "검색어를 입력해주세요."}, status=400)

        category_filter = (request.data.get("category") or "").strip()

        hardware_qs = Hardware.objects.prefetch_related("price_history", "user_hardware")
        if category_filter:
            hardware_qs = hardware_qs.filter(category=category_filter)
        hardware_qs = hardware_qs.order_by("-benchmark_score")[:120]
        items = list(hardware_qs)

        if not items:
            return Response({"results": [], "summary": "등록된 장비가 없습니다.", "intent": ""})

        compact = [_compact_hw(hw) for hw in items[:100]]
        user_message = (
            f'요구사항: "{query}"\n'
            f"장비목록: {json.dumps(compact, ensure_ascii=False, separators=(',', ':'))}"
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
            print(f"[AI Equipment] finish_reason={choice.finish_reason}, raw={repr(raw[:300])}")

            if not raw:
                return Response({"detail": f"AI가 빈 응답을 반환했습니다. finish_reason={choice.finish_reason}"}, status=500)

            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            return Response({"detail": f"JSON 파싱 실패. AI 원본: {raw[:200]}"}, status=500)
        except Exception as e:
            return Response({"detail": f"AI 검색 오류: {str(e)}"}, status=500)

        hw_ids = result.get("hw_ids") or []
        summary = result.get("summary") or ""
        intent = result.get("intent") or ""

        hw_map = {hw.id: hw for hw in items}
        matched = [
            hardware_to_catalog(hw_map[hid], request)
            for hid in hw_ids
            if hid in hw_map
        ]

        return Response({"results": matched, "summary": summary, "intent": intent})
