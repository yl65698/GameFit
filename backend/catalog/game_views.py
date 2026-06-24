from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Game
from .adapters import catalog_queryset, game_to_catalog


class GameListView(APIView):
    def get(self, request):
        games = catalog_queryset(
            Game,
            request.query_params,
            request.query_params.get("sort", "created_at"),
            category_field="genre",
        )[:100]
        return Response([game_to_catalog(game, request) for game in games])


class GameDetailView(APIView):
    def get(self, request, game_id):
        try:
            game = Game.objects.get(pk=game_id)
        except Game.DoesNotExist:
            return Response({"detail": "게임을 찾을 수 없습니다."}, status=404)
        return Response(game_to_catalog(game, request))
