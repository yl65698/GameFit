from rest_framework.response import Response
from rest_framework.views import APIView

from .data import GAMES


class RecommendationsView(APIView):
    def get(self, request):
        profile = request.user.profile
        return Response(
            {
                "taste_tags": profile.hashtags,
                "report": "전략, 협동, 반복 성장 장르 선호가 강합니다.",
                "vector_map": [
                    {"genre": "전략", "score": 92},
                    {"genre": "협동", "score": 81},
                    {"genre": "인디", "score": 74},
                    {"genre": "공포", "score": 58},
                ],
                "games": GAMES,
            }
        )
