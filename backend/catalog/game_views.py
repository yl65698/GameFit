from rest_framework.response import Response
from rest_framework.views import APIView

from .data import GAMES


class GameListView(APIView):
    def get(self, request):
        return Response(GAMES)


class GameDetailView(APIView):
    def get(self, request, game_id):
        game = next((item for item in GAMES if item["id"] == game_id), None)
        if not game:
            return Response({"detail": "게임을 찾을 수 없습니다."}, status=404)
        return Response(game)
