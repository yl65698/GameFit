import json
import os

from openai import OpenAI
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import PCSpec
from games.models import UserGame
from hardware.models import Hardware

_GMS_BASE = "https://gms.ssafy.io/gmsapi/api.openai.com/v1"
_SYSTEM = "PC 장비 성능 분석 전문가. 요청된 JSON 형식으로만 응답."

_SPEC_CATEGORIES = {"cpu", "gpu", "ram"}
_CAT_SPEC_FIELDS = {
    "cpu": ("min_cpu", "rec_cpu"),
    "gpu": ("min_gpu", "rec_gpu"),
    "ram": ("min_ram", "rec_ram"),
}
_CAT_LABEL = {
    "cpu": "CPU", "gpu": "GPU", "ram": "메모리", "storage": "저장장치",
    "monitor": "모니터", "mouse": "마우스", "keyboard": "키보드",
    "headset": "헤드셋", "vr": "VR 기기", "power": "파워 서플라이",
}
_NON_SPEC_BENEFIT = {
    "monitor": "고해상도·고주사율로 게임 몰입감 및 화질 향상",
    "mouse": "경량·고DPI 센서로 정밀한 조준과 반응속도 향상",
    "keyboard": "기계식 스위치로 빠른 입력 반응과 내구성 확보",
    "headset": "정밀한 사운드로 적 위치 파악 및 몰입감 향상",
    "storage": "NVMe SSD로 게임 로딩 시간 대폭 단축",
    "power": "안정적인 전원 공급으로 시스템 안정성 확보",
    "vr": "VR 지원 게임 플레이 가능",
}


def _build_client():
    return OpenAI(
        api_key=os.environ.get("GMS_API_KEY", ""),
        base_url=_GMS_BASE,
    )


def _call_gms(prompt):
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
        return json.loads(cleaned)
    except Exception:
        return None


class EquipmentGameSuitabilityView(APIView):
    def get(self, request, equipment_id):
        try:
            equipment = Hardware.objects.get(pk=equipment_id)
        except Hardware.DoesNotExist:
            return Response({"detail": "장비를 찾을 수 없습니다."}, status=404)

        if not request.user.is_authenticated:
            return Response({"owned": [], "interested": [], "requires_login": True})

        cat = equipment.category
        user_games_qs = (
            UserGame.objects
            .filter(user=request.user)
            .select_related("game")
            .order_by("status")
        )
        owned_ug = [ug for ug in user_games_qs if ug.status == "owned"][:5]
        interested_ug = [ug for ug in user_games_qs if ug.status == "interested"][:5]

        # Non-spec categories: generic improvement message per game
        if cat not in _SPEC_CATEGORIES:
            benefit = _NON_SPEC_BENEFIT.get(cat, "전반적인 게임 환경 개선")
            return Response({
                "owned": [
                    {"title": ug.game.title, "status": "info", "verdict": "환경 개선", "detail": benefit}
                    for ug in owned_ug if ug.game
                ],
                "interested": [
                    {"title": ug.game.title, "status": "info", "verdict": "환경 개선", "detail": benefit}
                    for ug in interested_ug if ug.game
                ],
            })

        # Spec categories: GMS batch analysis
        min_field, rec_field = _CAT_SPEC_FIELDS[cat]
        all_ug = owned_ug + interested_ug
        games_info = []
        for ug in all_ug:
            if not ug.game:
                continue
            g = ug.game
            min_val = getattr(g, min_field, "") or ""
            rec_val = getattr(g, rec_field, "") or ""
            games_info.append({
                "title": g.title,
                "min_req": min_val or "정보 없음",
                "rec_req": rec_val or "정보 없음",
                "status": ug.status,
            })

        if not games_info:
            return Response({"owned": [], "interested": []})

        games_str = "\n".join(
            f'{i+1}. "{g["title"]}" — {cat.upper()} 최소: {g["min_req"]}, 권장: {g["rec_req"]}'
            for i, g in enumerate(games_info)
        )

        cat_label = _CAT_LABEL.get(cat, cat.upper())
        prompt = f"""장비: {equipment.name}
카테고리: {cat_label}
스펙: {equipment.specs or equipment.description or "공식 제품"}

위 장비와 아래 게임들의 {cat_label} 요구사양을 비교해 호환성을 분석하세요:

{games_str}

판단 기준:
- pass: 권장사양 이상 충족
- warn: 최소사양 충족, 권장사양 미달 (설정 조절 필요)
- fail: 최소사양 미달
- unknown: 요구사양 정보 부족

JSON만 출력:
{{
  "games": [
    {{"title": "게임명", "status": "pass|warn|fail|unknown", "verdict": "15자 이내", "detail": "25자 이내 구체 이유"}}
  ]
}}"""

        data = _call_gms(prompt)

        if not data:
            result = {"owned": [], "interested": []}
            for g_info in games_info:
                key = "owned" if g_info["status"] == "owned" else "interested"
                result[key].append({
                    "title": g_info["title"],
                    "status": "unknown",
                    "verdict": "분석 불가",
                    "detail": "잠시 후 다시 시도해주세요",
                })
            return Response(result)

        result_map = {g["title"]: g for g in data.get("games", [])}
        result = {"owned": [], "interested": []}
        for g_info in games_info:
            matched = result_map.get(g_info["title"], {
                "title": g_info["title"],
                "status": "unknown",
                "verdict": "분석 불가",
                "detail": "",
            })
            key = "owned" if g_info["status"] == "owned" else "interested"
            result[key].append(matched)

        return Response(result)


class EquipmentPCCompareView(APIView):
    def get(self, request, equipment_id):
        try:
            equipment = Hardware.objects.get(pk=equipment_id)
        except Hardware.DoesNotExist:
            return Response({"detail": "장비를 찾을 수 없습니다."}, status=404)

        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)

        pc_spec, _ = PCSpec.objects.get_or_create(user=request.user)

        cat = equipment.category
        cat_label = _CAT_LABEL.get(cat, cat)

        current_map = {
            "cpu": pc_spec.cpu,
            "gpu": pc_spec.gpu,
            "ram": pc_spec.ram,
            "storage": pc_spec.storage,
        }
        current_spec = current_map.get(cat, "") or ""
        specs_info = equipment.specs or equipment.description or ""

        prompt = f"""PC 장비 교체 비교 분석

[현재 내 PC — 지금 실제로 보유 중인 장비]
CPU: {pc_spec.cpu or "정보 없음"}
GPU: {pc_spec.gpu or "정보 없음"}
메모리: {pc_spec.ram or "정보 없음"}
저장장치: {pc_spec.storage or "정보 없음"}

[교체 후보 장비 — 구매를 고려하는 신규 장비]
이름: {equipment.name}
카테고리: {cat_label}
{f"세부 스펙: {specs_info}" if specs_info else ""}

비교 대상:
- 현재 보유 {cat_label}: {current_spec or "정보 없음"}
- 교체 후보 {cat_label}: {equipment.name}

분석 지침:
1. "교체 후보 장비"가 "현재 보유 장비"보다 성능이 낮으면 반드시 upgrade_value를 "downgrade"로 설정하세요.
2. 예시: 현재 RTX 4070 보유 → RTX 3050 검토 = downgrade
3. points는 교체 후 실제로 달라지는 점을 현실적으로 서술하세요. 다운그레이드라면 성능 하락 내용을 포함하세요.

upgrade_value 기준:
- "high": 교체 후보가 현재 대비 30% 이상 성능 향상
- "medium": 교체 후보가 현재 대비 10~30% 성능 향상
- "low": 교체 후보와 현재가 비슷한 성능 (±10% 이내)
- "downgrade": 교체 후보가 현재보다 성능 하락
- "na": 비교 정보 부족

JSON만 출력:
{{
  "current_spec": "현재 보유 {cat_label} 이름",
  "diff_summary": "현재 대비 교체 후보의 성능 차이 (30자 이내)",
  "upgrade_value": "high|medium|low|downgrade|na",
  "verdict": "교체 추천 여부 한 줄 (20자 이내)",
  "points": ["교체 후 변화 포인트1 (25자 이내)", "포인트2 (25자 이내)", "포인트3 (25자 이내)"]
}}"""

        data = _call_gms(prompt)

        if not data:
            return Response({
                "current_spec": current_spec or "정보 없음",
                "diff_summary": "분석 중 오류가 발생했습니다.",
                "upgrade_value": "na",
                "verdict": "잠시 후 다시 시도해주세요",
                "points": [],
            })

        return Response(data)
