from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .adapters import recommendation_payload


class RecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(recommendation_payload(request.user, request))
