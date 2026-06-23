from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "username",
            "email",
            "nickname",
            "avatar_url",
            "hashtags",
            "show_hashtags",
            "pc_specs",
            "owned_games",
            "interested_games",
            "game_platforms",
            "interest_alerts",
            "discount_alerts",
        ]


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    nickname = serializers.CharField(max_length=40, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 사용 중인 아이디입니다.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "비밀번호가 일치하지 않습니다."})
        return attrs

    def create(self, validated_data):
        nickname = validated_data.pop("nickname", "")
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        user.profile.nickname = nickname or user.username
        user.profile.save(update_fields=["nickname"])
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("아이디 또는 비밀번호를 확인해주세요.")
        attrs["user"] = user
        return attrs
