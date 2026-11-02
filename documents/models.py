
import uuid
from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)

    file = models.FileField(upload_to="documents/")

    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class DocumentPermission(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    can_view = models.BooleanField(default=True)
    can_download = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "user"],
                name="unique_document_user"
            )
        ]

    def __str__(self):
        return f"{self.document.title} - {self.user.username}"


class AuditLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    document_id = models.UUIDField()
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return self.action
