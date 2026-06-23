from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    nickname = models.CharField(max_length=40, blank=True)
    avatar_url = models.TextField(blank=True)
    hashtags = models.JSONField(default=list, blank=True)
    show_hashtags = models.BooleanField(default=True)
    pc_specs = models.JSONField(default=dict, blank=True)
    owned_games = models.JSONField(default=list, blank=True)
    interested_games = models.JSONField(default=list, blank=True)
    game_platforms = models.JSONField(default=dict, blank=True)
    interest_alerts = models.JSONField(default=dict, blank=True)
    discount_alerts = models.BooleanField(default=True)

    def __str__(self):
        return self.nickname or self.user.username
