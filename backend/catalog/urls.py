from django.urls import path

from .ai_equipment_view import AIEquipmentSearchView
from .ai_search_view import AISearchView
from .analysis_views import RecommendationsView
from .calendar_views import CalendarView
from .community_views import (
    CommunityCommentDeleteView,
    CommunityCommentView,
    CommunityGroupJoinView,
    CommunityGroupLeaveView,
    CommunityGroupListView,
    CommunityPostDetailView,
    CommunityPostLikeView,
    CommunityPostListView,
)
from .equipment_ai_view import EquipmentGameSuitabilityView, EquipmentPCCompareView
from .equipment_views import EquipmentDetailView, EquipmentListView
from .buy_timing_view import GameBuyTimingView
from .compat_view import GameCompatView
from .game_views import FilteredGamesView, GameAutocompleteView, GameDetailView, GameListView, GameLivePricesView

urlpatterns = [
    path("games/", GameListView.as_view(), name="games"),
    path("games/autocomplete/", GameAutocompleteView.as_view(), name="games-autocomplete"),
    path("games/filter/", FilteredGamesView.as_view(), name="games-filter"),
    path("ai-search/", AISearchView.as_view(), name="ai-search"),
    path("games/<int:game_id>/", GameDetailView.as_view(), name="game-detail"),
    path("games/<int:game_id>/live-prices/", GameLivePricesView.as_view(), name="game-live-prices"),
    path("games/<int:game_id>/buy-timing/", GameBuyTimingView.as_view(), name="game-buy-timing"),
    path("games/<int:game_id>/compat/", GameCompatView.as_view(), name="game-compat"),
    # Community — posts
    path("games/<int:game_id>/community/", CommunityPostListView.as_view(), name="game-community"),
    path("games/<int:game_id>/community/posts/", CommunityPostListView.as_view(), name="game-community-posts"),
    path("games/<int:game_id>/community/posts/<int:post_id>/", CommunityPostDetailView.as_view(), name="game-community-post-detail"),
    path("games/<int:game_id>/community/posts/<int:post_id>/like/", CommunityPostLikeView.as_view(), name="game-community-post-like"),
    path("games/<int:game_id>/community/posts/<int:post_id>/comments/", CommunityCommentView.as_view(), name="game-community-comments"),
    path("games/<int:game_id>/community/comments/<int:comment_id>/", CommunityCommentDeleteView.as_view(), name="game-community-comment-delete"),
    # Community — groups
    path("games/<int:game_id>/community/groups/", CommunityGroupListView.as_view(), name="game-community-groups"),
    path("games/<int:game_id>/community/groups/<int:group_id>/join/", CommunityGroupJoinView.as_view(), name="game-community-group-join"),
    path("games/<int:game_id>/community/groups/<int:group_id>/leave/", CommunityGroupLeaveView.as_view(), name="game-community-group-leave"),
    # Equipment
    path("equipment/", EquipmentListView.as_view(), name="equipment"),
    path("equipment/<int:equipment_id>/", EquipmentDetailView.as_view(), name="equipment-detail"),
    path("equipment/<int:equipment_id>/game-suitability/", EquipmentGameSuitabilityView.as_view(), name="equipment-game-suitability"),
    path("equipment/<int:equipment_id>/pc-compare/", EquipmentPCCompareView.as_view(), name="equipment-pc-compare"),
    path("ai-equipment-search/", AIEquipmentSearchView.as_view(), name="ai-equipment-search"),
    path("recommendations/", RecommendationsView.as_view(), name="recommendations"),
    path("calendar/", CalendarView.as_view(), name="calendar"),
]
