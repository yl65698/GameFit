from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Q
from django.core.paginator import EmptyPage, Paginator
from .models import Game, UserGame, GameReview
from .serializers import GameSerializer, UserGameSerializer, GameReviewSerializer


PAGE_SIZE = 20


def paginated_response(queryset, serializer_class, request):
    page = max(int(request.query_params.get('page', 1) or 1), 1)
    paginator = Paginator(queryset, PAGE_SIZE)

    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages or 1)

    serializer = serializer_class(page_obj.object_list, many=True, context={'request': request})
    return Response({
        'count': paginator.count,
        'page': page_obj.number,
        'page_size': PAGE_SIZE,
        'total_pages': paginator.num_pages,
        'results': serializer.data,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def game_list(request):
    games = Game.objects.all()
    q = request.query_params.get('q')
    genre = request.query_params.get('genre')
    platform = request.query_params.get('platform')
    sort = request.query_params.get('sort', 'created_at')

    if q:
        games = games.filter(title__icontains=q)
    if genre:
        games = games.filter(genre=genre)
    if platform:
        games = games.filter(platform=platform)
    if sort == 'discount':
        games = games.order_by('-discount_percent')
    elif sort == 'price':
        games = games.order_by('price')
    else:
        games = games.order_by('-created_at')

    return paginated_response(games, GameSerializer, request)


@api_view(['GET'])
@permission_classes([AllowAny])
def game_detail(request, game_id):
    try:
        game = Game.objects.get(pk=game_id)
    except Game.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = GameSerializer(game, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_user_game(request):
    game_id = request.data.get('game_id')
    status_val = request.data.get('status', 'owned')
    try:
        game = Game.objects.get(pk=game_id)
    except Game.DoesNotExist:
        return Response({'error': '게임을 찾을 수 없습니다.'}, status=404)

    user_game, created = UserGame.objects.get_or_create(
        user=request.user, game=game,
        defaults={'status': status_val}
    )
    if not created:
        user_game.status = status_val
        user_game.save()

    return Response(UserGameSerializer(user_game).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_user_game(request, game_id):
    try:
        user_game = UserGame.objects.get(user=request.user, game_id=game_id)
        user_game.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except UserGame.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_games(request):
    user_games = UserGame.objects.filter(user=request.user).select_related('game')
    serializer = UserGameSerializer(user_games, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def game_reviews(request, game_id):
    try:
        game = Game.objects.get(pk=game_id)
    except Game.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        reviews = GameReview.objects.filter(game=game).order_by('-created_at')
        return Response(GameReviewSerializer(reviews, many=True).data)

    serializer = GameReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(game=game, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
