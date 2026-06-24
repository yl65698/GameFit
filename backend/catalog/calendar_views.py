from rest_framework.response import Response
from rest_framework.views import APIView

from .adapters import calendar_payload


class CalendarView(APIView):
    def get(self, request):
        return Response(calendar_payload(request.user))
