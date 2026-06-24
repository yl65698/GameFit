from django.contrib.auth import get_user_model
from rest_framework import serializers

from games.models import Game, UserGame
from .models import PCSpec, TasteMiniGameResult

User = get_user_model()


class PCSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = PCSpec
        fields = ["id", "cpu", "gpu", "ram", "storage", "has_vr", "vr_type", "has_console", "console_type"]


class UserBasicSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "nickname", "avatar_url"]

    def get_avatar_url(self, obj):
        if not obj.profile_image:
            return ""
        request = self.context.get("request")
        url = obj.profile_image.url
        return request.build_absolute_uri(url) if request else url


class TasteMiniGameResultSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = TasteMiniGameResult
        fields = [
            "id",
            "user_id",
            "result_key",
            "result_title",
            "result_summary",
            "competitive_score",
            "strategy_score",
            "exploration_score",
            "social_score",
            "story_score",
            "action_score",
            "challenge_score",
            "cozy_score",
            "tags",
            "recommended_games",
            "answers",
            "created_at",
        ]
        read_only_fields = ["id", "user_id", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    pc_spec = PCSpecSerializer(read_only=True)
    hashtags = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    pc_specs = serializers.SerializerMethodField()
    owned_games = serializers.SerializerMethodField()
    interested_games = serializers.SerializerMethodField()
    game_platforms = serializers.SerializerMethodField()
    interest_alerts = serializers.SerializerMethodField()
    discount_alerts = serializers.SerializerMethodField()
    followers_list = serializers.SerializerMethodField()
    following_list = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "nickname",
            "profile_image",
            "hashtags",
            "pc_spec",
            "followers_count",
            "following_count",
            "followers_list",
            "following_list",
            "is_following",
            "avatar_url",
            "pc_specs",
            "owned_games",
            "interested_games",
            "game_platforms",
            "interest_alerts",
            "discount_alerts",
        ]

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_followers_list(self, obj):
        return UserBasicSerializer(obj.followers.all(), many=True, context=self.context).data

    def get_following_list(self, obj):
        return UserBasicSerializer(obj.following.all(), many=True, context=self.context).data

    def get_is_following(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.followers.filter(pk=request.user.pk).exists()

    def get_hashtags(self, obj):
        if not obj.hashtags:
            return []
        return [tag.strip().lstrip("#") for tag in obj.hashtags.split(",") if tag.strip()]

    def get_avatar_url(self, obj):
        if not obj.profile_image:
            return ""
        request = self.context.get("request")
        url = obj.profile_image.url
        return request.build_absolute_uri(url) if request else url

    def get_pc_specs(self, obj):
        pc_spec, _ = PCSpec.objects.get_or_create(user=obj)
        memory_list = [m.strip() for m in (pc_spec.ram or "").split(",") if m.strip()]
        return {
            "cpu": pc_spec.cpu,
            "gpu": pc_spec.gpu,
            "memory": memory_list,
            "storage": pc_spec.storage,
            "vr": pc_spec.vr_type if pc_spec.has_vr else "없음",
            "console": pc_spec.console_type if pc_spec.has_console else "없음",
        }

    def get_owned_games(self, obj):
        return [
            {
                "id": ug.game.id,
                "title": ug.game.title,
                "platform": ug.platform or ug.game.platform or "other",
                "image_url": ug.game.image_url,
            }
            for ug in obj.user_games.filter(status="owned").select_related("game")
        ]

    def get_interested_games(self, obj):
        return [
            {
                "id": ug.game.id,
                "title": ug.game.title,
                "platform": ug.platform or ug.game.platform or "other",
                "image_url": ug.game.image_url,
            }
            for ug in obj.user_games.filter(status="interested").select_related("game")
        ]

    def get_game_platforms(self, obj):
        return {
            ug.game.title: ug.platform or ug.game.platform or "other"
            for ug in obj.user_games.select_related("game").all()
        }

    def get_interest_alerts(self, obj):
        return {
            user_game.game.title: True
            for user_game in obj.user_games.select_related("game").filter(status="interested")
        }

    def get_discount_alerts(self, obj):
        return True


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "password", "password2", "email", "nickname"]

    def validate(self, attrs):
        password2 = attrs.get("password2")
        if password2 and attrs["password"] != password2:
            raise serializers.ValidationError({"password2": "비밀번호가 일치하지 않습니다."})
        return attrs

    def validate_nickname(self, value):
        if value and User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")
        return value

    def create(self, validated_data):
        validated_data.pop("password2", None)
        nickname = validated_data.get("nickname") or validated_data["username"]
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
            nickname=nickname,
        )
        PCSpec.objects.create(user=user)
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    hashtags = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    pc_specs = serializers.DictField(write_only=True, required=False)
    owned_games = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    interested_games = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    game_platforms = serializers.DictField(write_only=True, required=False)
    interest_alerts = serializers.DictField(write_only=True, required=False)
    discount_alerts = serializers.BooleanField(write_only=True, required=False)
    avatar_url = serializers.CharField(write_only=True, required=False, allow_blank=True)
    show_hashtags = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "nickname",
            "hashtags",
            "profile_image",
            "avatar_url",
            "show_hashtags",
            "pc_specs",
            "owned_games",
            "interested_games",
            "game_platforms",
            "interest_alerts",
            "discount_alerts",
        ]

    def update(self, instance, validated_data):
        hashtags = validated_data.pop("hashtags", None)
        pc_specs = validated_data.pop("pc_specs", None)
        owned_games = validated_data.pop("owned_games", None)
        interested_games = validated_data.pop("interested_games", None)
        game_platforms = validated_data.pop("game_platforms", {})
        validated_data.pop("interest_alerts", None)
        validated_data.pop("discount_alerts", None)
        validated_data.pop("avatar_url", None)
        validated_data.pop("show_hashtags", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if hashtags is not None:
            instance.hashtags = ",".join(tag.strip().lstrip("#") for tag in hashtags if tag.strip())
        instance.save()

        if pc_specs is not None:
            sync_pc_specs(instance, pc_specs)
        if owned_games is not None:
            sync_user_games(instance, owned_games, "owned", game_platforms)
        if interested_games is not None:
            sync_user_games(instance, interested_games, "interested", game_platforms)

        return instance


def sync_pc_specs(user, pc_specs):
    pc_spec, _ = PCSpec.objects.get_or_create(user=user)
    pc_spec.cpu = pc_specs.get("cpu", pc_specs.get("CPU", pc_spec.cpu))
    pc_spec.gpu = pc_specs.get("gpu", pc_specs.get("GPU", pc_spec.gpu))
    memory_value = pc_specs.get("memory", pc_specs.get("ram", None))
    if memory_value is not None:
        if isinstance(memory_value, list):
            pc_spec.ram = ",".join(str(m).strip() for m in memory_value if str(m).strip())
        else:
            pc_spec.ram = str(memory_value).strip()
    pc_spec.storage = pc_specs.get("storage", pc_spec.storage)
    vr_value = pc_specs.get("vr", "")
    pc_spec.has_vr = bool(vr_value and str(vr_value).strip().lower() not in ["없음", "false", "no", "0", ""])
    pc_spec.vr_type = "" if not pc_spec.has_vr else str(vr_value).strip()
    console_value = pc_specs.get("console", "")
    pc_spec.has_console = bool(console_value and console_value != "없음")
    pc_spec.console_type = "" if console_value == "없음" else console_value
    pc_spec.save()


def sync_user_games(user, titles, status, platforms=None):
    platforms = platforms or {}
    UserGame.objects.filter(user=user, status=status).exclude(game__title__in=titles).delete()
    for title in titles:
        game = Game.objects.filter(title=title).first()
        if not game:
            continue
        platform = platforms.get(title, game.platform or "other")
        UserGame.objects.update_or_create(
            user=user,
            game=game,
            defaults={"status": status, "platform": platform},
        )
