import mimetypes

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from .models import AuditLog
from .models import Document, DocumentPermission, AuditLog
from .forms import DocumentForm


User = get_user_model()


# --------------------------------------------------
# AUDIT LOG
# --------------------------------------------------

def create_audit_log(user, document, action, details=""):
    AuditLog.objects.create(
        user=user,
        document_id=str(document.id),
        action=action,
        details=details
    )


# --------------------------------------------------
# CHECK DOCUMENT PERMISSION
# --------------------------------------------------

def has_document_access(user, document, permission="can_view"):
    # The owner has access to their own document.
    if document.owner == user:
        return True

    access = DocumentPermission.objects.filter(
        document=document,
        user=user
    ).first()

    return bool(access and getattr(access, permission, False))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@login_required
def dashboard(request):
    search_query = request.GET.get("q", "").strip()

    documents = Document.objects.filter(
        Q(owner=request.user)
        | Q(
            documentpermission__user=request.user,
            documentpermission__can_view=True,
        )
    ).distinct()

    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query)
            | Q(category__icontains=search_query)
        )

    documents = documents.order_by("-uploaded_at")

    downloadable_document_ids = [
        document.id
        for document in documents
        if has_document_access(request.user, document, "can_download")
    ]

    return render(
        request,
        "dashboard.html",
        {
            "documents": documents,
            "search_query": search_query,
            "downloadable_document_ids": downloadable_document_ids,
        },
    )
# --------------------------------------------------
# LOGIN
# --------------------------------------------------

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password.")

    return render(request, "login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


# --------------------------------------------------
# UPLOAD DOCUMENT
# --------------------------------------------------

@login_required
def upload_document(request):
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user
            document.save()

            create_audit_log(
                request.user,
                document,
                "UPLOAD",
                "Document uploaded"
            )

            messages.success(request, "Document uploaded successfully.")
            return redirect("dashboard")
    else:
        form = DocumentForm()

    return render(request, "upload.html", {
        "form": form
    })


# --------------------------------------------------
# DOCUMENT DETAILS
# --------------------------------------------------

@login_required
def document_details(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    if not has_document_access(request.user, document, "can_view"):
        create_audit_log(
            request.user,
            document,
            "DENIED",
            "Unauthorized document details access"
        )

        return HttpResponseForbidden("You do not have permission.")

    create_audit_log(
        request.user,
        document,
        "VIEW_DETAILS",
        "Document details accessed"
    )

    return render(request, "document_details.html", {
        "document": document
    })


# --------------------------------------------------
# VIEW DOCUMENT
# --------------------------------------------------

@login_required
def view_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    if not has_document_access(request.user, document, "can_view"):
        create_audit_log(
            request.user,
            document,
            "DENIED",
            "Unauthorized document view attempt"
        )

        return HttpResponseForbidden("You do not have permission.")

    if not document.file:
        return HttpResponseForbidden("Document file not found.")

    create_audit_log(
        request.user,
        document,
        "VIEW",
        "Document viewed"
    )

    content_type, encoding = mimetypes.guess_type(document.file.name)

    response = FileResponse(
        document.file.open("rb"),
        content_type=content_type or "application/octet-stream"
    )

    response["Content-Disposition"] = (
        f'inline; filename="{document.file.name.split("/")[-1]}"'
    )

    return response


# --------------------------------------------------
# DOWNLOAD DOCUMENT
# --------------------------------------------------

@login_required
def download_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    if not has_document_access(request.user, document, "can_download"):
        create_audit_log(
            request.user,
            document,
            "DENIED",
            "Unauthorized download attempt"
        )

        return HttpResponseForbidden("Download permission denied.")

    if not document.file:
        return HttpResponseForbidden("Document file not found.")

    create_audit_log(
        request.user,
        document,
        "DOWNLOAD",
        "Document downloaded"
    )

    return FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=document.file.name.split("/")[-1]
    )


# --------------------------------------------------
# EDIT DOCUMENT
# --------------------------------------------------

@login_required
def edit_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    if not has_document_access(request.user, document, "can_edit"):
        create_audit_log(
            request.user,
            document,
            "DENIED",
            "Unauthorized edit attempt"
        )

        return HttpResponseForbidden("Edit permission denied.")

    if request.method == "POST":
        form = DocumentForm(
            request.POST,
            request.FILES,
            instance=document
        )

        if form.is_valid():
            form.save()

            create_audit_log(
                request.user,
                document,
                "EDIT",
                "Document updated"
            )

            messages.success(request, "Document updated successfully.")
            return redirect("document_details", document_id=document.id)
    else:
        form = DocumentForm(instance=document)

    return render(request, "edit_document.html", {
        "form": form,
        "document": document
    })


# --------------------------------------------------
# DELETE DOCUMENT
# --------------------------------------------------

@login_required
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    if document.owner != request.user:
        create_audit_log(
            request.user,
            document,
            "DENIED",
            "Unauthorized delete attempt"
        )

        return HttpResponseForbidden(
            "Only the owner can delete this document."
        )

    if request.method == "POST":
        create_audit_log(
            request.user,
            document,
            "DELETE",
            "Document deleted"
        )

        document.delete()

        messages.success(request, "Document deleted successfully.")
        return redirect("dashboard")

    return render(request, "confirm_delete.html", {
        "document": document
    })


# --------------------------------------------------
# SHARE DOCUMENT
# --------------------------------------------------

@login_required
def share_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    if document.owner != request.user:
        create_audit_log(
            request.user,
            document,
            "DENIED",
            "Unauthorized share attempt"
        )

        return HttpResponseForbidden(
            "Only the owner can share this document."
        )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()

        shared_user = User.objects.filter(
            username=username
        ).first()

        if shared_user is None:
            messages.error(request, "User not found.")

        elif shared_user == request.user:
            messages.error(request, "You cannot share with yourself.")

        else:
            can_view = request.POST.get("can_view") == "on"
            can_download = request.POST.get("can_download") == "on"
            can_edit = request.POST.get("can_edit") == "on"

            # Downloading or editing also requires viewing.
            if can_download or can_edit:
                can_view = True

            DocumentPermission.objects.update_or_create(
                document=document,
                user=shared_user,
                defaults={
                    "can_view": can_view,
                    "can_download": can_download,
                    "can_edit": can_edit
                }
            )

            create_audit_log(
                request.user,
                document,
                "SHARE",
                f"Document shared with {username}"
            )

            messages.success(request, "Document shared successfully.")

    return render(request, "share_document.html", {
    "document": document,
    "permissions": DocumentPermission.objects.filter(
        document=document
    ).select_related("user"),
})

# --------------------------------------------------
# SHARED DOCUMENTS
# --------------------------------------------------

@login_required
def shared_documents(request):
    permissions = DocumentPermission.objects.filter(
        user=request.user,
        can_view=True
    ).select_related("document", "document__owner")

    return render(request, "shared_documents.html", {
        "permissions": permissions
    })


# --------------------------------------------------
# REVOKE DOCUMENT ACCESS
# --------------------------------------------------

@login_required
def revoke_share(request, document_id, username):
    document = get_object_or_404(Document, id=document_id)

    if document.owner != request.user:
        create_audit_log(
            request.user,
            document,
            "DENIED",
            "Unauthorized revoke attempt"
        )

        return HttpResponseForbidden(
            "Only the owner can revoke access."
        )

    shared_user = get_object_or_404(
        User,
        username=username
    )

    permission = DocumentPermission.objects.filter(
        document=document,
        user=shared_user
    ).first()

    if permission:
        permission.delete()

        create_audit_log(
            request.user,
            document,
            "REVOKE",
            f"Access revoked for {username}"
        )

        messages.success(request, "Access revoked successfully.")
    else:
        messages.error(request, "No permission found for this user.")

    return redirect("document_details", document_id=document.id)


# --------------------------------------------------
# AUDIT LOGS
# --------------------------------------------------

@login_required
def audit_logs(request):
    # Only staff users can view audit logs.
    if not request.user.is_staff:
        return HttpResponseForbidden(
            "Only administrators can access audit logs."
        )

    selected_action = request.GET.get("action", "")

    logs = AuditLog.objects.all().select_related(
        "user"
    ).order_by("-timestamp")

    if selected_action:
        logs = logs.filter(action=selected_action)

    return render(request, "audit_logs.html", {
        "logs": logs,
        "selected_action": selected_action,
    })