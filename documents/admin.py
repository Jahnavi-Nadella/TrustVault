from django.contrib import admin
from .models import Document, DocumentPermission, AuditLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "owner", "uploaded_at")
    search_fields = ("title", "category", "owner__username")
    list_filter = ("category", "uploaded_at")


@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "user",
        "can_view",
        "can_download",
        "can_edit",
    )
    list_filter = ("can_view", "can_download", "can_edit")
    search_fields = ("document__title", "user__username")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "document_id", "details")
    list_filter = ("action", "timestamp")
    search_fields = ("user__username", "document_id", "details")
    readonly_fields = ("user", "document_id", "action", "timestamp", "details")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False