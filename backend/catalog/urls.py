from django.urls import path

from .analysis_views import RecommendationsView
from .calendar_views import CalendarView
from .community_views import CommunityPostListView
from .equipment_views import EquipmentDetailView, EquipmentListView
from .game_views import GameDetailView, GameListView

urlpatterns = [
    path("games/", GameListView.as_view(), name="games"),
    path("games/<int:game_id>/", GameDetailView.as_view(), name="game-detail"),
    path("games/<int:game_id>/community/", CommunityPostListView.as_view(), name="game-community"),
    path("equipment/", EquipmentListView.as_view(), name="equipment"),
    path("equipment/<int:equipment_id>/", EquipmentDetailView.as_view(), name="equipment-detail"),
    path("recommendations/", RecommendationsView.as_view(), name="recommendations"),
    path("calendar/", CalendarView.as_view(), name="calendar"),
]
