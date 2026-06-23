from rest_framework import serializers
from .models import Game, UserGame, GameReview


class GameSerializer(serializers.ModelSerializer):
    is_owned = serializers.SerializerMethodField()
    is_interested = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            'id', 'title', 'description', 'genre', 'platform',
            'price', 'original_price', 'discount_percent', 'image_url',
            'min_cpu', 'min_gpu', 'min_ram', 'rec_cpu', 'rec_gpu', 'rec_ram',
            'created_at', 'is_owned', 'is_interested',
        ]

    def get_is_owned(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user_games.filter(user=request.user, status='owned').exists()
        return False

    def get_is_interested(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user_games.filter(user=request.user, status='interested').exists()
        return False


class UserGameSerializer(serializers.ModelSerializer):
    game = GameSerializer(read_only=True)
    game_id = serializers.PrimaryKeyRelatedField(
        queryset=Game.objects.all(), source='game', write_only=True
    )

    class Meta:
        model = UserGame
        fields = ['id', 'game', 'game_id', 'status', 'added_at']


class GameReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = GameReview
        fields = ['id', 'username', 'content', 'rating', 'created_at']
        read_only_fields = ['id', 'username', 'created_at']
