import datetime


def compute_buy_score(game_data: dict, live_prices: dict) -> dict:
    """
    ITAD 실시간 가격 + 게임 정보로 구매 타이밍 점수(0-100) 계산.

    game_data: {title, price, discount_percent, release_date}
    live_prices: {deals, history_low_all, history_low_1y, history_low_3m}
    """
    deals = live_prices.get("deals") or []
    current_price = int(deals[0]["price"]) if deals else int(game_data.get("price") or 0)
    discount = int(game_data.get("discount_percent") or 0)
    history_low_all = live_prices.get("history_low_all")
    history_low_1y = live_prices.get("history_low_1y")
    history_low_3m = live_prices.get("history_low_3m")
    release_date_str = game_data.get("release_date")

    score = 0
    factors = []

    # ── Factor 1: 역대 최저가 대비 (max 35점) ──
    # 비율과 절대금액 차이를 함께 고려: 저가 게임은 수천 원 차이가 비율상 크게 보여도 실질 부담이 작음
    if history_low_all and current_price > 0:
        ratio = current_price / history_low_all
        abs_diff = current_price - history_low_all  # 원화 절대 차이
        if ratio <= 1.0:
            score += 35
            factors.append({
                "label": "역대 최저가 달성",
                "detail": f"역대 최저가({history_low_all:,}원)와 동일하거나 낮은 가격",
                "positive": True,
            })
        elif ratio <= 1.05 or abs_diff <= 2_000:
            score += 28
            label = "역대 최저가 근접"
            detail = (
                f"역대 최저가({history_low_all:,}원)보다 {abs_diff:,}원 차이 (소액)"
                if abs_diff <= 2_000
                else f"역대 최저가({history_low_all:,}원)보다 {(ratio - 1) * 100:.0f}% 높음"
            )
            factors.append({"label": label, "detail": detail, "positive": True})
        elif ratio <= 1.2 or abs_diff <= 5_000:
            score += 16
            label = "역대 최저가와 근소한 차이"
            detail = (
                f"역대 최저가({history_low_all:,}원)보다 {abs_diff:,}원 차이"
                if abs_diff <= 5_000
                else f"역대 최저가({history_low_all:,}원)보다 {(ratio - 1) * 100:.0f}% 높음"
            )
            factors.append({"label": label, "detail": detail, "positive": True})
        elif ratio <= 1.5 or abs_diff <= 10_000:
            score += 6
            label = "역대 최저가보다 소폭 높음"
            detail = (
                f"역대 최저가({history_low_all:,}원)보다 {abs_diff:,}원 높음"
                if abs_diff <= 10_000
                else f"역대 최저가({history_low_all:,}원)보다 {(ratio - 1) * 100:.0f}% 높음"
            )
            factors.append({"label": label, "detail": detail, "positive": False})
        else:
            factors.append({
                "label": "역대 최저가와 큰 차이",
                "detail": f"역대 최저가({history_low_all:,}원)보다 {abs_diff:,}원 ({(ratio - 1) * 100:.0f}%) 높음",
                "positive": False,
            })

    # ── Factor 2: 할인율 (max 25점) ──
    if discount >= 75:
        score += 25
        factors.append({"label": "대폭 할인 중", "detail": f"현재 {discount}% 할인 적용 중", "positive": True})
    elif discount >= 50:
        score += 18
        factors.append({"label": "높은 할인율", "detail": f"현재 {discount}% 할인 적용 중", "positive": True})
    elif discount >= 33:
        score += 12
        factors.append({"label": "적당한 할인율", "detail": f"현재 {discount}% 할인 적용 중", "positive": True})
    elif discount >= 10:
        score += 5
        factors.append({"label": "소폭 할인 중", "detail": f"현재 {discount}% 할인 적용 중", "positive": False})
    else:
        factors.append({"label": "할인 없음", "detail": "현재 정가로 판매 중", "positive": False})

    # ── Factor 3: 1년 최저가 대비 (max 20점) ──
    if history_low_1y and current_price > 0:
        ratio = current_price / history_low_1y
        abs_diff = current_price - history_low_1y
        if ratio <= 1.0:
            score += 20
            factors.append({
                "label": "최근 1년 내 최저가",
                "detail": f"최근 1년 최저가({history_low_1y:,}원)와 동일하거나 낮음",
                "positive": True,
            })
        elif ratio <= 1.1 or abs_diff <= 3_000:
            score += 13
            detail = (
                f"최근 1년 최저가({history_low_1y:,}원)보다 {abs_diff:,}원 차이 (소액)"
                if abs_diff <= 3_000
                else f"최근 1년 최저가({history_low_1y:,}원)의 {ratio:.0%}"
            )
            factors.append({"label": "1년 최저가에 근접", "detail": detail, "positive": True})
        elif ratio <= 1.3 or abs_diff <= 7_000:
            score += 5
            detail = (
                f"최근 1년 최저가({history_low_1y:,}원)보다 {abs_diff:,}원 높음"
                if abs_diff <= 7_000
                else f"최근 1년 최저가({history_low_1y:,}원)보다 {(ratio - 1) * 100:.0f}% 높음"
            )
            factors.append({"label": "1년 최저가보다 소폭 높음", "detail": detail, "positive": False})
        else:
            factors.append({
                "label": "1년 최저가와 큰 차이",
                "detail": f"최근 1년 최저가({history_low_1y:,}원)보다 {abs_diff:,}원 ({(ratio - 1) * 100:.0f}%) 높음",
                "positive": False,
            })

    # ── Factor 4: 3개월 최저가 대비 (max 10점) ──
    if history_low_3m and current_price > 0:
        ratio = current_price / history_low_3m
        abs_diff = current_price - history_low_3m
        if ratio <= 1.0:
            score += 10
            factors.append({
                "label": "최근 3개월 내 최저가",
                "detail": f"최근 3개월({history_low_3m:,}원) 기준 최저 수준",
                "positive": True,
            })
        elif ratio <= 1.1 or abs_diff <= 3_000:
            score += 6
            detail = (
                f"최근 3개월 최저가({history_low_3m:,}원)보다 {abs_diff:,}원 차이 (소액)"
                if abs_diff <= 3_000
                else f"최근 3개월 최저가({history_low_3m:,}원)에 근접"
            )
            factors.append({"label": "최근 가격 대비 양호", "detail": detail, "positive": True})

    # ── Factor 5: 출시 경과 기간 (max 10점) ──
    if release_date_str:
        try:
            release_date = datetime.date.fromisoformat(str(release_date_str))
            age_days = (datetime.date.today() - release_date).days
            if age_days >= 730:
                score += 10
                factors.append({
                    "label": "출시 후 장기간 경과",
                    "detail": f"출시 {age_days // 365}년 경과 — 충분한 할인 이력 보유",
                    "positive": True,
                })
            elif age_days >= 365:
                score += 6
                factors.append({
                    "label": "출시 1년 이상",
                    "detail": f"출시 {age_days // 30}개월 경과",
                    "positive": True,
                })
            elif age_days >= 180:
                score += 3
                factors.append({
                    "label": "출시 6개월 이상",
                    "detail": f"출시 {age_days // 30}개월 경과 — 추가 할인 가능성 있음",
                    "positive": False,
                })
            else:
                factors.append({
                    "label": "신규 출시작",
                    "detail": f"출시 {age_days}일 경과 — 할인 이력 적음",
                    "positive": False,
                })
        except (ValueError, TypeError):
            pass

    score = min(100, score)

    if score >= 75:
        signal = "buy_now"
    elif score >= 50:
        signal = "good"
    elif score >= 30:
        signal = "watch"
    else:
        signal = "wait"

    return {
        "score": score,
        "signal": signal,
        "factors": factors,
        "current_price": current_price,
        "discount": discount,
        "history_low_all": history_low_all,
        "history_low_1y": history_low_1y,
        "history_low_3m": history_low_3m,
    }
