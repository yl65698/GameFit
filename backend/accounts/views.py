from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PCSpec, TasteMiniGameResult
from .serializers import (
    PCSpecSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    TasteMiniGameResultSerializer,
    UserSerializer,
)

User = get_user_model()


def auth_payload(user, request):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user, context={"request": request}).data,
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(auth_payload(user, request), status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"detail": "아이디 또는 비밀번호를 확인해주세요."}, status=400)
    if not user.check_password(password):
        return Response({"detail": "아이디 또는 비밀번호를 확인해주세요."}, status=400)
    return Response(auth_payload(user, request))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user, context={"request": request}).data)


@api_view(["GET", "PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    if request.method == "GET":
        return Response(UserSerializer(request.user, context={"request": request}).data)

    serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(UserSerializer(request.user, context={"request": request}).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_pc_spec(request):
    pc_spec, _ = PCSpec.objects.get_or_create(user=request.user)
    serializer = PCSpecSerializer(pc_spec, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def taste_minigame_results(request):
    if request.method == "GET":
        results = TasteMiniGameResult.objects.filter(user=request.user)
        serializer = TasteMiniGameResultSerializer(results, many=True)
        return Response(serializer.data)

    serializer = TasteMiniGameResultSerializer(data=request.data)
    if serializer.is_valid():
        result = serializer.save(user=request.user)
        return Response(TasteMiniGameResultSerializer(result).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def user_detail(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(UserSerializer(user, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_follow(request, user_id):
    try:
        target = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if target == request.user:
        return Response({"error": "자기 자신은 팔로우할 수 없습니다."}, status=400)
    if request.user in target.followers.all():
        target.followers.remove(request.user)
        return Response({"followed": False})
    target.followers.add(request.user)
    return Response({"followed": True})
