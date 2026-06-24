from django.urls import path

from .ai_equipment_view import AIEquipmentSearchView
from .ai_search_view import AISearchView
from .analysis_views import RecommendationsView
from .calendar_views import CalendarView
from .community_views import CommunityPostListView
from .equipment_views import EquipmentDetailView, EquipmentListView
from .game_views import FilteredGamesView, GameAutocompleteView, GameDetailView, GameListView, GameLivePricesView

urlpatterns = [
    path("games/", GameListView.as_view(), name="games"),
    path("games/autocomplete/", GameAutocompleteView.as_view(), name="games-autocomplete"),
    path("games/filter/", FilteredGamesView.as_view(), name="games-filter"),
    path("ai-search/", AISearchView.as_view(), name="ai-search"),
    path("games/<int:game_id>/", GameDetailView.as_view(), name="game-detail"),
    path("games/<int:game_id>/live-prices/", GameLivePricesView.as_view(), name="game-live-prices"),
    path("games/<int:game_id>/community/", CommunityPostListView.as_view(), name="game-community"),
    path("equipment/", EquipmentListView.as_view(), name="equipment"),
    path("equipment/<int:equipment_id>/", EquipmentDetailView.as_view(), name="equipment-detail"),
    path("ai-equipment-search/", AIEquipmentSearchView.as_view(), name="ai-equipment-search"),
    path("recommendations/", RecommendationsView.as_view(), name="recommendations"),
    path("calendar/", CalendarView.as_view(), name="calendar"),
]
