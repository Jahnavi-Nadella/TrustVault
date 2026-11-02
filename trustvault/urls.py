from django.contrib import admin
from django.urls import include, path
from documents import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("documents.urls")),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("logout/", views.logout_view, name="custom_logout"),
    path("audit-logs/", views.audit_logs, name="audit_logs"),
]
