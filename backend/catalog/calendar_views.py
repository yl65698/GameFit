from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import CalendarEvent


class CalendarView(APIView):
    def get(self, request):
        events = CalendarEvent.objects.all()
        return Response([
            {
                "date": str(e.date),
                "title": e.title,
                "description": e.description,
                "type": e.event_type,
                "url": e.url,
            }
            for e in events
        ])
