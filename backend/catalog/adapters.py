from collections import Counter

from django.db.models import Count, Min, Max

from games.models import Game
from hardware.models import Hardware
from catalog.currency import normalize_price


def _build_price_history(price_history_qs, max_points=20):
    """
    모든 배포사 포함 → 원화 정규화 → 날짜별 최저가 → 균등 샘플링(첫/끝 필수, 최대 max_points).
    """
    all_items = list(price_history_qs)

    date_min = {}
    for item in all_items:
        raw_price = float(item.price or 0)
        if raw_price <= 0:
            continue
        krw_price, krw_orig = normalize_price(item.price, item.original_price, item.shop_name)
        if krw_price <= 0:
            continue
        d = item.recorded_at.date()
        if d not in date_min or krw_price < date_min[d]["price"]:
            date_min[d] = {
                "shop_name": item.shop_name,
                "price": krw_price,
                "original_price": krw_orig,
                "discount": item.discount_percent,
                "recorded_at": item.recorded_at.isoformat(),
            }

    entries = [date_min[d] for d in sorted(date_min)]
    n = len(entries)
    if n == 0:
        return []
    if n <= max_points:
        return entries

    # 첫·끝 필수 포함, 나머지는 균등 분배
    indices = sorted({round(i * (n - 1) / (max_points - 1)) for i in range(max_points)})
    return [entries[i] for i in indices]


def game_to_catalog(game, request=None):
    user = getattr(request, "user", None)
    is_authenticated = bool(user and user.is_authenticated)
    is_owned = game.user_games.filter(user=user, status="owned").exists() if is_authenticated else False
    is_interested = game.user_games.filter(user=user, status="interested").exists() if is_authenticated else False

    price_history = _build_price_history(game.price_history.order_by("recorded_at"), max_points=100)

    # GameGenre 기반 다중 장르 (prefetch_related 활용)
    genres = [
        {"key": gg.genre.key, "name": gg.genre.name}
        for gg in game.game_genres.select_related("genre").all()
    ]

    krw_price, krw_orig = normalize_price(game.price, game.original_price)

    return {
        "id": game.id,
        "title": game.title,
        "genre": game.get_genre_display() or game.genre,
        "genre_key": game.genre,
        "genres": genres,
        "platform": game.get_platform_display() or game.platform,
        "price": krw_price,
        "original_price": krw_orig,
        "discount": game.discount_percent,
        "discount_percent": game.discount_percent,
        "compatibility": compatibility_label(game),
        "buy_signal": buy_signal(game.discount_percent),
        "summary": game.description or f"{game.title}의 가격과 사양 정보를 확인해보세요.",
        "description": game.description,
        "reviews": "아직 등록된 리뷰가 없습니다.",
        "image_url": game.image_url,
        "min_cpu": game.min_cpu,
        "min_gpu": game.min_gpu,
        "min_ram": game.min_ram,
        "rec_cpu": game.rec_cpu,
        "rec_gpu": game.rec_gpu,
        "rec_ram": game.rec_ram,
        "price_history": price_history,
        "release_date": game.release_date.isoformat() if game.release_date else None,
        "publisher": game.publisher,
        "developer": game.developer,
        "age_rating": game.age_rating,
        "is_owned": is_owned,
        "is_interested": is_interested,
    }


def hardware_to_catalog(item, request=None):
    user = getattr(request, "user", None)
    is_authenticated = bool(user and user.is_authenticated)
    is_owned = item.user_hardware.filter(user=user, status="owned").exists() if is_authenticated else False
    is_interested = item.user_hardware.filter(user=user, status="interested").exists() if is_authenticated else False

    price_history_qs = list(item.price_history.order_by("-recorded_at")[:12])

    return {
        "id": item.id,
        "name": item.name,
        "type": item.get_category_display() or item.category,
        "category": item.category,
        "manufacturer": item.manufacturer,
        "price": int(item.price or 0),
        "original_price": int(item.original_price or 0),
        "discount": item.discount_percent,
        "discount_percent": item.discount_percent,
        "description": item.description,
        "fit": item.specs or hardware_fit_label(item),
        "specs": item.specs,
        "benchmark_score": item.benchmark_score,
        "image_url": item.image_url,
        "is_owned": is_owned,
        "is_interested": is_interested,
        "price_history": [
            {
                "shop_name": h.shop_name,
                "price": int(h.price or 0),
                "original_price": int(h.original_price or 0),
                "discount": h.discount_percent,
                "recorded_at": h.recorded_at.isoformat() if h.recorded_at else None,
            }
            for h in reversed(price_history_qs)
        ],
    }


def recommendation_payload(user, request=None):
    user_games = user.user_games.select_related("game").all()
    genres = [user_game.game.genre for user_game in user_games if user_game.game.genre]
    genre_counts = Counter(genres)
    taste_tags = [label_genre(genre) for genre, _ in genre_counts.most_common(4)]
    if not taste_tags:
        raw_tags = getattr(user, "hashtags", "")
        taste_tags = [tag.strip().lstrip("#") for tag in raw_tags.split(",") if tag.strip()]
    if not taste_tags:
        taste_tags = ["할인", "추천", "PC"]

    vector_map = [
        {"genre": label_genre(genre), "score": min(100, 55 + count * 15)}
        for genre, count in genre_counts.most_common(5)
    ]
    if not vector_map:
        vector_map = [
            {"genre": "RPG", "score": 72},
            {"genre": "FPS", "score": 66},
            {"genre": "Indie", "score": 61},
        ]

    preferred_genres = list(genre_counts.keys())
    games = Game.objects.all()
    if preferred_genres:
        games = games.filter(genre__in=preferred_genres)
    games = games.order_by("-discount_percent", "price")[:8]

    return {
        "taste_tags": taste_tags,
        "report": "보유 및 관심 게임과 현재 할인율을 기준으로 추천을 계산했습니다.",
        "vector_map": vector_map,
        "games": [game_to_catalog(game, request) for game in games],
    }


def calendar_payload(user=None):
    discounted_games = Game.objects.filter(discount_percent__gt=0).order_by("-discount_percent")[:8]
    events = [
        {
            "date": "2026-06-25",
            "title": f"{game.title} {game.discount_percent}% 할인",
            "game": game.title,
            "type": "sale",
        }
        for game in discounted_games
    ]
    if user and user.is_authenticated:
        interested = user.user_games.filter(status="interested").select_related("game")[:5]
        events.extend(
            {
                "date": "2026-06-28",
                "title": f"{item.game.title} 관심 게임 가격 확인",
                "game": item.game.title,
                "type": "alert",
            }
            for item in interested
        )
    return events


def catalog_queryset(model, query, sort, category_field=None):
    queryset = model.objects.all()
    keyword = query.get("q") or query.get("search")
    if keyword:
        lookup = "title__icontains" if model is Game else "name__icontains"
        queryset = queryset.filter(**{lookup: keyword})

    category = query.get("genre") or query.get("category") or query.get("type")
    if category and category_field:
        queryset = queryset.filter(**{category_field: category})

    if sort == "discount":
        return queryset.order_by("-discount_percent")
    if sort == "price":
        return queryset.order_by("price")
    if sort == "benchmark" and model is Hardware:
        return queryset.order_by("-benchmark_score")
    return queryset.order_by("-created_at")


def community_post_to_catalog(post):
    return {
        "id": post.id,
        "game_id": post.game_id,
        "title": post.title,
        "body": post.content,
        "content": post.content,
        "author": post.user.nickname or post.user.username,
        "createdAt": post.created_at.strftime("%Y-%m-%d"),
        "recommendations": post.likes.count(),
        "comments": [
            {
                "id": comment.id,
                "author": comment.user.nickname or comment.user.username,
                "body": comment.content,
            }
            for comment in post.comments.select_related("user").all()
        ],
    }


def compatibility_label(game):
    if game.rec_gpu or game.rec_cpu:
        return "권장 사양 확인 필요"
    if game.min_gpu or game.min_cpu:
        return "최소 사양 확인 필요"
    return "사양 정보 확인 중"


def buy_signal(discount_percent):
    if discount_percent >= 50:
        return "지금 구매 추천"
    if discount_percent >= 25:
        return "관심 등록 추천"
    return "가격 추적 추천"


def hardware_fit_label(item):
    if item.category in ["cpu", "gpu"]:
        return f"벤치마크 {item.benchmark_score}점 기준 게임 성능 업그레이드 후보"
    if item.discount_percent:
        return f"{item.discount_percent}% 할인 중인 {item.get_category_display()} 장비"
    return f"{item.get_category_display()} 장비 비교 후보"


def label_genre(genre):
    try:
        return dict(Game.GENRE_CHOICES).get(genre, genre)
    except Exception:
        return genre
