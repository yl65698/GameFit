import json
import os

from openai import OpenAI
from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Game

_SYSTEM = "PC 부품 호환성 분석 전문가. 게임 요구사양과 사용자 PC를 비교해 JSON으로만 응답."

_STATUS_MAP = {"pass": "pass", "warn": "warn", "fail": "fail", "unknown": "none"}
_ICON_MAP   = {"pass": "v",   "warn": "!",    "fail": "✕",   "unknown": "—"}


def _build_client():
    return OpenAI(
        api_key=os.environ.get("GMS_API_KEY", ""),
        base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1",
    )


def _to_check(label: str, current: str, item: dict) -> dict:
    s = item.get("status", "unknown")
    return {
        "label": label,
        "current": current or "정보 없음",
        "message": item.get("message", ""),
        "status": _STATUS_MAP.get(s, "none"),
        "icon": _ICON_MAP.get(s, "—"),
    }


def _analyze(game, user_cpu: str, user_gpu: str, user_ram: str) -> dict:
    def req_line(label, min_val, rec_val):
        parts = []
        if min_val:
            parts.append(f"최소 {min_val}")
        if rec_val:
            parts.append(f"권장 {rec_val}")
        return f"{label}: {', '.join(parts)}" if parts else ""

    req_lines = [
        req_line("CPU", game.min_cpu, game.rec_cpu),
        req_line("GPU", game.min_gpu, game.rec_gpu),
        req_line("RAM", game.min_ram, game.rec_ram),
    ]
    requirements = "\n".join(r for r in req_lines if r) or "정보 없음"

    user_lines = []
    if user_cpu: user_lines.append(f"CPU: {user_cpu}")
    if user_gpu: user_lines.append(f"GPU: {user_gpu}")
    if user_ram: user_lines.append(f"RAM: {user_ram}")
    user_spec = "\n".join(user_lines) or "정보 없음"

    prompt = f"""게임 "{game.title}" 호환성 분석

[게임 요구사양]
{requirements}

[사용자 PC 사양]
{user_spec}

판단 기준:
- CPU/GPU는 출시 세대와 성능 등급으로 비교. 요구사양 정보 없으면 unknown.
- RAM은 GB 숫자를 추출해 비교. "16 GB", "16GB", "16 기가" 모두 16GB로 처리.
- pass: 권장 사양 이상 / warn: 최소 사양은 충족 / fail: 최소 사양 미달 / unknown: 판단 불가

JSON만 출력:
{{
  "cpu": {{"status": "pass|warn|fail|unknown", "message": "15자 이내"}},
  "gpu": {{"status": "pass|warn|fail|unknown", "message": "15자 이내"}},
  "ram": {{"status": "pass|warn|fail|unknown", "message": "15자 이내"}},
  "summary": "한 줄 요약 (30자 이내)"
}}"""

    try:
        client = _build_client()
        resp = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        raw = resp.choices[0].message.content or ""
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
    except Exception:
        data = {
            "cpu": {"status": "unknown", "message": "분석 실패"},
            "gpu": {"status": "unknown", "message": "분석 실패"},
            "ram": {"status": "unknown", "message": "분석 실패"},
            "summary": "호환성 분석 중 오류가 발생했습니다.",
        }

    return {
        "spec_checks": [
            _to_check("CPU",  user_cpu, data.get("cpu", {"status": "unknown"})),
            _to_check("GPU",  user_gpu, data.get("gpu", {"status": "unknown"})),
            _to_check("메모리", user_ram, data.get("ram", {"status": "unknown"})),
        ],
        "summary": data.get("summary", ""),
    }


class GameCompatView(APIView):
    def get(self, request, game_id):
        try:
            game = Game.objects.only(
                "id", "title",
                "min_cpu", "min_gpu", "min_ram",
                "rec_cpu", "rec_gpu", "rec_ram",
            ).get(pk=game_id)
        except Game.DoesNotExist:
            return Response({"detail": "게임을 찾을 수 없습니다."}, status=404)

        user_cpu = request.query_params.get("cpu", "").strip()
        user_gpu = request.query_params.get("gpu", "").strip()
        user_ram = request.query_params.get("ram", "").strip()

        if not any([user_cpu, user_gpu, user_ram]):
            return Response({
                "spec_checks": [],
                "summary": "내 장비 정보를 먼저 등록해주세요.",
            })

        return Response(_analyze(game, user_cpu, user_gpu, user_ram))
