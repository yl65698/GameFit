from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Post
from .adapters import community_post_to_catalog


class CommunityPostListView(APIView):
    def get(self, request, game_id):
        posts = (
            Post.objects.filter(game_id=game_id)
            .select_related("user", "game")
            .prefetch_related("likes", "comments__user")
            .order_by("-created_at")
        )
        return Response([community_post_to_catalog(post) for post in posts])
