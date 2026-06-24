from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("signup/", views.register, name="signup"),
    path("login/", views.login, name="token_obtain_pair"),
    path("logout/", views.logout, name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", views.me, name="me"),
    path("me/profile/", views.update_profile, name="update_profile"),
    path("me/pc-spec/", views.update_pc_spec, name="update_pc_spec"),
    path("profile/", views.update_profile, name="profile"),
    path("taste-results/", views.taste_minigame_results, name="taste_minigame_results"),
    path("users/<int:user_id>/", views.user_detail, name="user_detail"),
    path("users/<int:user_id>/follow/", views.toggle_follow, name="toggle_follow"),
]
