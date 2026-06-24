import time
import requests

_cache: dict = {}
_CACHE_TTL = 3600  # 1시간

FALLBACK_RATES = {
    "USD": 1380,
    "EUR": 1520,
    "GBP": 1760,
    "JPY": 9.2,
}

# GamesPlanet UK → GBP, DE/FR → EUR, Nuuvem → BRL(→USD 근사)
SHOP_CURRENCY = {
    "GamesPlanet UK": "GBP",
    "GamesPlanet DE": "EUR",
    "GamesPlanet FR": "EUR",
}


def get_rate(currency: str = "USD") -> float:
    now = time.time()
    if currency in _cache and now - _cache[currency]["ts"] < _CACHE_TTL:
        return _cache[currency]["rate"]
    try:
        resp = requests.get(
            f"https://api.frankfurter.app/latest?from={currency}&to=KRW",
            timeout=3,
        )
        resp.raise_for_status()
        rate = float(resp.json()["rates"]["KRW"])
        _cache[currency] = {"rate": rate, "ts": now}
        return rate
    except Exception:
        return FALLBACK_RATES.get(currency, FALLBACK_RATES["USD"])


def to_krw(amount: float, currency: str = "USD") -> int:
    if amount <= 0:
        return 0
    krw = amount * get_rate(currency)
    return round(krw / 100) * 100


def is_foreign_price(price, original_price) -> tuple[bool, str]:
    """
    가격이 원화인지 외화인지 판별.
    original_price가 0 초과 1000 미만이면 외화.
    original_price가 없고 price가 0 초과 1000 미만이면 외화.
    반환: (is_foreign, currency)
    """
    p = float(price or 0)
    op = float(original_price or 0)
    if p <= 0:
        return False, "KRW"
    if (op > 0 and op < 1000) or (op == 0 and 0 < p < 1000):
        return True, "USD"
    return False, "KRW"


def normalize_price(price, original_price, shop_name: str = "") -> tuple[int, int]:
    """
    (price, original_price)를 원화로 정규화.
    100원 미만 단위는 반올림.
    """
    p = float(price or 0)
    op = float(original_price or 0)

    if p <= 0:
        return 0, round(op / 100) * 100 if op >= 1000 else 0

    currency = SHOP_CURRENCY.get(shop_name, "USD")
    is_foreign, _ = is_foreign_price(p, op)

    if is_foreign:
        krw_price = to_krw(p, currency)
        krw_orig = to_krw(op, currency) if op > 0 else 0
        return krw_price, krw_orig

    return round(p / 100) * 100 if p < 1000 else int(p), int(op)
