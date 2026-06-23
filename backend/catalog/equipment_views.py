from rest_framework.response import Response
from rest_framework.views import APIView

from hardware.models import Hardware
from .adapters import catalog_queryset, hardware_to_catalog


class EquipmentListView(APIView):
    def get(self, request):
        equipment = catalog_queryset(
            Hardware,
            request.query_params,
            request.query_params.get("sort", "created_at"),
            category_field="category",
        )[:100]
        return Response([hardware_to_catalog(item, request) for item in equipment])


class EquipmentDetailView(APIView):
    def get(self, request, equipment_id):
        try:
            equipment = Hardware.objects.get(pk=equipment_id)
        except Hardware.DoesNotExist:
            return Response({"detail": "장비를 찾을 수 없습니다."}, status=404)
        return Response(hardware_to_catalog(equipment, request))
