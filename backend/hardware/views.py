from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.core.paginator import EmptyPage, Paginator
from .models import Hardware, UserHardware
from .serializers import HardwareSerializer, UserHardwareSerializer


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
def hardware_list(request):
    hardware = Hardware.objects.all()
    category = request.query_params.get('category')
    q = request.query_params.get('q')
    sort = request.query_params.get('sort', 'created_at')

    if category:
        hardware = hardware.filter(category=category)
    if q:
        hardware = hardware.filter(name__icontains=q)
    if sort == 'discount':
        hardware = hardware.order_by('-discount_percent')
    elif sort == 'price':
        hardware = hardware.order_by('price')
    elif sort == 'benchmark':
        hardware = hardware.order_by('-benchmark_score')
    else:
        hardware = hardware.order_by('-created_at')

    return paginated_response(hardware, HardwareSerializer, request)


@api_view(['GET'])
@permission_classes([AllowAny])
def hardware_detail(request, hw_id):
    try:
        hw = Hardware.objects.get(pk=hw_id)
    except Hardware.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = HardwareSerializer(hw, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_user_hardware(request):
    hw_id = request.data.get('hardware_id')
    status_val = request.data.get('status', 'owned')
    try:
        hw = Hardware.objects.get(pk=hw_id)
    except Hardware.DoesNotExist:
        return Response({'error': '장비를 찾을 수 없습니다.'}, status=404)

    user_hw, created = UserHardware.objects.get_or_create(
        user=request.user, hardware=hw,
        defaults={'status': status_val}
    )
    if not created:
        user_hw.status = status_val
        user_hw.save()

    return Response(UserHardwareSerializer(user_hw).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_user_hardware(request, hw_id):
    try:
        user_hw = UserHardware.objects.get(user=request.user, hardware_id=hw_id)
        user_hw.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except UserHardware.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_hardware(request):
    user_hw = UserHardware.objects.filter(user=request.user).select_related('hardware')
    serializer = UserHardwareSerializer(user_hw, many=True)
    return Response(serializer.data)
