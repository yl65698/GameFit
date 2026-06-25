from collections import Counter

from django.core.paginator import Paginator
from django.db.models import Count, F
from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Game, GameGenre, UserGame
from .adapters import catalog_queryset, game_to_catalog
from .itad_service import get_live_prices

PAGE_SIZE = 20


class GameListView(APIView):
    def get(self, request):
        games = catalog_queryset(
            Game,
            request.query_params,
            request.query_params.get("sort", "created_at"),
            category_field="genre",
        )[:100]
        return Response([game_to_catalog(game, request, include_price_history=False) for game in games])


class GameAutocompleteView(APIView):
    """자동완성용 경량 API — id/title/genre/discount만 반환"""
    def get(self, request):
        games = Game.objects.only("id", "title", "genre", "discount_percent").order_by("-discount_percent")[:300]
        return Response([
            {"id": g.id, "title": g.title, "genre": g.genre, "discount": g.discount_percent}
            for g in games
        ])


class FilteredGamesView(APIView):
    def get(self, request):
        filter_type = request.query_params.get("type", "top-discount")
        page = max(1, int(request.query_params.get("page", 1)))
        games = Game.objects.prefetch_related("game_genres__genre", "user_games")

        if filter_type == "top-discount":
            games = games.filter(discount_percent__gt=0).order_by("-discount_percent")

        elif filter_type == "interest-genre":
            user = request.user
            if user.is_authenticated:
                # 사용자 보유/관심 게임의 GameGenre 기반 선호 장르 추출
                genre_keys = list(
                    GameGenre.objects.filter(game__user_games__user=user)
                    .values_list("genre__key", flat=True)
                )
                preferred_keys = [key for key, _ in Counter(genre_keys).most_common(5)]
                if preferred_keys:
                    matched_ids = (
                        GameGenre.objects.filter(genre__key__in=preferred_keys)
                        .values_list("game_id", flat=True)
                    )
                    games = games.filter(id__in=matched_ids).order_by("-discount_percent")
                else:
                    games = games.order_by("-discount_percent")
            else:
                games = games.order_by("-discount_percent")

        elif filter_type == "new-release":
            games = games.order_by(F("release_date").desc(nulls_last=True), "-created_at")

        elif filter_type == "popular":
            games = games.annotate(popularity=Count("user_games")).order_by("-popularity", "-discount_percent")

        else:
            games = games.order_by("-discount_percent")

        paginator = Paginator(games, PAGE_SIZE)
        page_obj = paginator.get_page(page)

        return Response({
            "results": [game_to_catalog(g, request, include_price_history=False) for g in page_obj],
            "total": paginator.count,
            "total_pages": paginator.num_pages,
            "page": page_obj.number,
        })


class GameDetailView(APIView):
    def get(self, request, game_id):
        try:
            game = Game.objects.prefetch_related("game_genres__genre", "user_games", "price_history").get(pk=game_id)
        except Game.DoesNotExist:
            return Response({"detail": "게임을 찾을 수 없습니다."}, status=404)
        return Response(game_to_catalog(game, request))


class GameLivePricesView(APIView):
    def get(self, request, game_id):
        try:
            game = Game.objects.only("id", "itad_id").get(pk=game_id)
        except Game.DoesNotExist:
            return Response({"detail": "게임을 찾을 수 없습니다."}, status=404)
        if not game.itad_id:
            return Response({"deals": [], "history_low_all": None, "history_low_1y": None, "history_low_3m": None})
        return Response(get_live_prices(str(game.itad_id)))
