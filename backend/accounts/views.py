from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PCSpec
from .serializers import PCSpecSerializer, ProfileUpdateSerializer, RegisterSerializer, UserSerializer

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


@api_view(["GET"])
@permission_classes([AllowAny])
def user_detail(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(UserSerializer(user, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_users(request):
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response([])
    users = User.objects.filter(
        Q(username__icontains=query) | Q(nickname__icontains=query)
    ).exclude(pk=request.user.pk)[:20]
    return Response(UserSerializer(users, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def user_detail_by_username(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(UserSerializer(user, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    current = request.data.get("current_password", "")
    new_pw = request.data.get("new_password", "")
    if not request.user.check_password(current):
        return Response({"current_password": "현재 비밀번호가 올바르지 않습니다."}, status=400)
    if len(new_pw) < 8:
        return Response({"new_password": "비밀번호는 8자 이상이어야 합니다."}, status=400)
    request.user.set_password(new_pw)
    request.user.save()
    return Response({"detail": "비밀번호가 변경되었습니다."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_follow(request, user_id):
    try:
        target = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if target == request.user:
        return Response({"error": "자기 자신은 팔로우할 수 없습니다."}, status=400)
    if target.followers.filter(pk=request.user.pk).exists():
        target.followers.remove(request.user)
        followed = False
    else:
        target.followers.add(request.user)
        followed = True
    return Response({
        "followed": followed,
        "followers_count": target.followers.count(),
        "following_count": target.following.count(),
    })
