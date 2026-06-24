from django.db import models
from accounts.models import User


class GameShop(models.Model):
    """ITAD 기반 게임 판매 샵 정보"""
    itad_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    url = models.URLField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Genre(models.Model):
    key = models.CharField(max_length=50, unique=True)   # 'rpg', 'fps', ...
    name = models.CharField(max_length=100, unique=True) # 'RPG', 'FPS', ...

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Game(models.Model):
    PLATFORM_CHOICES = [
        ('steam', 'Steam'),
        ('epic', 'Epic Games'),
        ('ubisoft', 'Ubisoft'),
        ('other', 'Other'),
    ]
    GENRE_CHOICES = [
        ('rpg', 'RPG'),
        ('fps', 'FPS'),
        ('strategy', 'Strategy'),
        ('simulation', 'Simulation'),
        ('adventure', 'Adventure'),
        ('sports', 'Sports'),
        ('horror', 'Horror'),
        ('indie', 'Indie'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    itad_id = models.CharField(max_length=100, blank=True, default='', db_index=True)
    description = models.TextField(blank=True, default='')
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES, default='other')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='other')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.IntegerField(default=0)
    image_url = models.URLField(blank=True, default='')
    release_date = models.DateField(null=True, blank=True)
    publisher = models.CharField(max_length=200, blank=True, default='')
    developer = models.CharField(max_length=200, blank=True, default='')
    age_rating = models.CharField(max_length=50, blank=True, default='')
    min_cpu = models.CharField(max_length=100, blank=True, default='')
    min_gpu = models.CharField(max_length=100, blank=True, default='')
    min_ram = models.CharField(max_length=50, blank=True, default='4GB')
    rec_cpu = models.CharField(max_length=100, blank=True, default='')
    rec_gpu = models.CharField(max_length=100, blank=True, default='')
    rec_ram = models.CharField(max_length=50, blank=True, default='8GB')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class GameGenre(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='game_genres')
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name='game_genres')

    class Meta:
        unique_together = ('game', 'genre')

    def __str__(self):
        return f"{self.game.title} - {self.genre.name}"


class UserGame(models.Model):
    STATUS_CHOICES = [
        ('owned', '보유'),
        ('interested', '관심'),
    ]
    PLATFORM_CHOICES = [
        ('steam', 'Steam'),
        ('epic', 'Epic Games'),
        ('ubisoft', 'Ubisoft'),
        ('gog', 'GOG'),
        ('origin', 'EA/Origin'),
        ('battlenet', 'Battle.net'),
        ('other', '기타'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_games')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='user_games')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='owned')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, blank=True, default='')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'game')

    def __str__(self):
        return f"{self.user.nickname} - {self.game.title} ({self.status})"


class GameReview(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    content = models.TextField()
    rating = models.IntegerField(default=5)
    recommend = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('game', 'user')

    def __str__(self):
        return f"{self.user.nickname} → {self.game.title}"



class GamePriceHistory(models.Model):
    """ITAD API 기반 가격 변동 스냅샷 (가격변동 그래프용)"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='price_history')
    shop_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.IntegerField(default=0)
    currency = models.CharField(max_length=10, default='USD')
    recorded_at = models.DateTimeField()

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.game.title} - {self.shop_name} ({self.recorded_at:%Y-%m-%d})"


class GameGroup(models.Model):
    """게임 그룹 (ERD: team) — 커뮤니티 게임 그룹"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GameGroupMember(models.Model):
    """그룹 멤버십 (ERD: teamuser)"""
    group = models.ForeignKey(GameGroup, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_groups')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user.nickname} in {self.group.name}"


class Post(models.Model):
    """커뮤니티 게시글 (ERD: post)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Comment(models.Model):
    """게시글 댓글 (ERD: comment)"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.nickname}: {self.content[:30]}"
