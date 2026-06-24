import os
import time
import requests

ITAD_API_KEY = os.environ.get("IS_THERE_ANY_DEAL_API_KEY", "")
ITAD_BASE = "https://api.isthereanydeal.com"
_cache: dict = {}
_CACHE_TTL = 1800  # 30분
_shop_url_cache: dict = {}  # itad_shop_id → homepage url


def _get_shop_url(shop_name: str) -> str:
    if not _shop_url_cache:
        try:
            from games.models import GameShop
            for s in GameShop.objects.values("name", "url"):
                _shop_url_cache[s["name"]] = s["url"]
        except Exception:
            pass
    return _shop_url_cache.get(shop_name, "")


def _cache_key(itad_id: str) -> str:
    return f"prices:{itad_id}"


def get_live_prices(itad_id: str) -> list[dict]:
    """
    ITAD /games/prices/v3 로 현재 전체 샵 가격 조회 (KRW).
    30분 캐싱.
    """
    if not ITAD_API_KEY or not itad_id:
        return []

    ck = _cache_key(itad_id)
    now = time.time()
    if ck in _cache and now - _cache[ck]["ts"] < _CACHE_TTL:
        return _cache[ck]["data"]

    try:
        resp = requests.post(
            f"{ITAD_BASE}/games/prices/v3",
            params={"country": "KR", "key": ITAD_API_KEY},
            json=[str(itad_id)],
            timeout=8,
        )
        resp.raise_for_status()
        items = resp.json()
    except Exception:
        return []

    if not items:
        return []

    raw_deals = items[0].get("deals", [])
    history_low = items[0].get("historyLow", {})

    deals = []
    for d in raw_deals:
        price = d["price"]["amount"]
        regular = d["regular"]["amount"]
        cut = d.get("cut", 0)
        expiry = d.get("expiry")
        flag = d.get("flag")           # "H" = 역대 최저가
        store_low = (d.get("storeLow") or {}).get("amount", 0)
        drm = [x["name"] for x in (d.get("drm") or [])]
        platforms = [x["name"] for x in (d.get("platforms") or [])]

        shop_name = d["shop"]["name"]
        deals.append({
            "shop": shop_name,
            "price": int(price),
            "regular": int(regular),
            "cut": cut,
            "url": d.get("url", ""),
            "shop_url": _get_shop_url(shop_name),
            "expiry": expiry,
            "is_history_low": flag == "H",
            "store_low": int(store_low),
            "drm": drm,
            "platforms": platforms,
        })

    # 가격 오름차순 정렬
    deals.sort(key=lambda x: x["price"])

    all_low = (history_low.get("all") or {}).get("amount")
    result = {
        "deals": deals,
        "history_low_all": int(all_low) if all_low else None,
        "history_low_1y": int((history_low.get("y1") or {}).get("amount", 0) or 0) or None,
        "history_low_3m": int((history_low.get("m3") or {}).get("amount", 0) or 0) or None,
    }

    _cache[ck] = {"data": result, "ts": now}
    return result
