from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    nickname = models.CharField(max_length=50, unique=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    hashtags = models.CharField(max_length=200, blank=True, default='')
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)

    def __str__(self):
        return self.nickname or self.username


class PCSpec(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pc_spec')
    cpu = models.CharField(max_length=100, blank=True, default='')
    gpu = models.CharField(max_length=100, blank=True, default='')
    ram = models.CharField(max_length=500, blank=True, default='')
    storage = models.CharField(max_length=100, blank=True, default='')
    has_vr = models.BooleanField(default=False)
    vr_type = models.CharField(max_length=100, blank=True, default='')
    has_console = models.BooleanField(default=False)
    console_type = models.CharField(max_length=50, blank=True, default='')

    def __str__(self):
        return f"{self.user.nickname}'s PC"


class TasteMiniGameResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taste_minigame_results')
    result_key = models.CharField(max_length=30)
    result_title = models.CharField(max_length=100)
    result_summary = models.TextField(blank=True, default='')
    competitive_score = models.PositiveSmallIntegerField(default=0)
    strategy_score = models.PositiveSmallIntegerField(default=0)
    exploration_score = models.PositiveSmallIntegerField(default=0)
    social_score = models.PositiveSmallIntegerField(default=0)
    story_score = models.PositiveSmallIntegerField(default=0)
    action_score = models.PositiveSmallIntegerField(default=0)
    challenge_score = models.PositiveSmallIntegerField(default=0)
    cozy_score = models.PositiveSmallIntegerField(default=0)
    tags = models.JSONField(default=list, blank=True)
    recommended_games = models.JSONField(default=list, blank=True)
    answers = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.nickname} - {self.result_title}"
