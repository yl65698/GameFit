from rest_framework.response import Response
from rest_framework.views import APIView

from .data import COMMUNITY_POSTS


class CommunityPostListView(APIView):
    def get(self, request, game_id):
        posts = [post for post in COMMUNITY_POSTS if post["game_id"] == game_id]
        return Response(posts)
