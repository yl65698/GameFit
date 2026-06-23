from rest_framework.response import Response
from rest_framework.views import APIView

from .data import EQUIPMENT


class EquipmentListView(APIView):
    def get(self, request):
        return Response(EQUIPMENT)


class EquipmentDetailView(APIView):
    def get(self, request, equipment_id):
        equipment = next((item for item in EQUIPMENT if item["id"] == equipment_id), None)
        if not equipment:
            return Response({"detail": "장비를 찾을 수 없습니다."}, status=404)
        return Response(equipment)
