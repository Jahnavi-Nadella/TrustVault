from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse
from django.urls import include, path
from documents import views


def google_site_verification(request):
    file_path = Path(settings.BASE_DIR) / "google8b98f7b72e6ce1f8.html"
    return FileResponse(open(file_path, "rb"), content_type="text/html")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("documents.urls")),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("logout/", views.logout_view, name="custom_logout"),
    path("audit-logs/", views.audit_logs, name="audit_logs"),

    path(
        "google8b98f7b72e6ce1f8.html",
        google_site_verification,
    ),
]