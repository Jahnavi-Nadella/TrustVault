
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path(
        "upload/",
        views.upload_document,
        name="upload_document"
    ),
    path(
    "details/<uuid:document_id>/",
    views.document_details,
    name="document_details"
),
    path(
        "view/<uuid:document_id>/",
        views.view_document,
        name="view_document"
    ),

    path(
        "download/<uuid:document_id>/",
        views.download_document,
        name="download_document"
    ),

    path(
        "delete/<uuid:document_id>/",
        views.delete_document,
        name="delete_document"
    ),

    path(
        "share/<uuid:document_id>/",
        views.share_document,
        name="share_document"
    ),
    path("edit/<uuid:document_id>/", views.edit_document, name="edit_document"),
    path("shared/", views.shared_documents, name="shared_documents"),
    path(
    "revoke/<uuid:document_id>/<str:username>/",
    views.revoke_share,
    name="revoke_share",
),
path("register/", views.register_view, name="register"),
]
