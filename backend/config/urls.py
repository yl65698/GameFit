from django.contrib import admin
from django.conf import settings
from django.views.generic import TemplateView
from django.views.static import serve
from django.urls import include, path
from django.urls import re_path


def serve_frontend_asset(request, path):
    response = serve(request, path, document_root=settings.FRONTEND_DIST_DIR / "assets")
    if path.endswith(".js"):
        response["Content-Type"] = "application/javascript"
    return response


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/games/", include("games.urls")),
    path("api/hardware/", include("hardware.urls")),
    path("api/catalog/", include("catalog.urls")),
    re_path(r"^assets/(?P<path>.*)$", serve_frontend_asset),
    re_path(r"^(?!api/|admin/|assets/).*", TemplateView.as_view(template_name="index.html")),
]
