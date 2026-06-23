from rest_framework.response import Response
from rest_framework.views import APIView


class CalendarView(APIView):
    def get(self, request):
        return Response(
            [
                {"date": "2026-06-25", "title": "Steam 여름 할인 시작", "type": "sale"},
                {"date": "2026-06-28", "title": "It Takes Two 할인 종료", "type": "alert"},
                {"date": "2026-07-02", "title": "관심 게임 출시 예정", "type": "release"},
            ]
        )
