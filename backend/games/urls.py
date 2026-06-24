from django.urls import path
from . import views

urlpatterns = [
    path('featured/', views.featured_games, name='featured_games'),
    path('', views.game_list, name='game_list'),
    path('<int:game_id>/', views.game_detail, name='game_detail'),
    path('my/', views.my_games, name='my_games'),
    path('add/', views.add_user_game, name='add_user_game'),
    path('<int:game_id>/remove/', views.remove_user_game, name='remove_user_game'),
    path('<int:game_id>/reviews/', views.game_reviews, name='game_reviews'),
    path('<int:game_id>/reviews/create/', views.game_review_create, name='game_review_create'),
    path('<int:game_id>/reviews/my/', views.game_my_review, name='game_my_review'),
    path('<int:game_id>/reviews/update/', views.game_review_update, name='game_review_update'),
]
