from django.core.paginator import Paginator
from rest_framework.response import Response
from rest_framework.views import APIView

from hardware.models import Hardware
from .adapters import hardware_to_catalog

PAGE_SIZE = 20


class EquipmentListView(APIView):
    def get(self, request):
        category = request.query_params.get("category", "").strip()
        q = request.query_params.get("q", "").strip()
        sort = request.query_params.get("sort", "benchmark")
        page = max(1, int(request.query_params.get("page", 1) or 1))

        equipment = Hardware.objects.prefetch_related("price_history", "user_hardware")

        if category:
            equipment = equipment.filter(category=category)
        if q:
            equipment = equipment.filter(name__icontains=q)

        if sort == "discount":
            equipment = equipment.order_by("-discount_percent", "-benchmark_score")
        elif sort == "price_asc":
            equipment = equipment.order_by("price")
        elif sort == "price_desc":
            equipment = equipment.order_by("-price")
        else:  # benchmark (default)
            equipment = equipment.order_by("-benchmark_score", "-created_at")

        paginator = Paginator(equipment, PAGE_SIZE)
        page_obj = paginator.get_page(page)

        return Response({
            "results": [hardware_to_catalog(item, request) for item in page_obj],
            "total": paginator.count,
            "total_pages": paginator.num_pages,
            "page": page_obj.number,
        })


class EquipmentDetailView(APIView):
    def get(self, request, equipment_id):
        try:
            equipment = Hardware.objects.prefetch_related(
                "price_history", "user_hardware"
            ).get(pk=equipment_id)
        except Hardware.DoesNotExist:
            return Response({"detail": "장비를 찾을 수 없습니다."}, status=404)
        return Response(hardware_to_catalog(equipment, request))
