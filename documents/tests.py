
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .forms import DocumentForm
from .models import Document, DocumentPermission, AuditLog


User = get_user_model()


class DocumentAccessTests(TestCase):

    def setUp(self):

        self.owner = User.objects.create_user(
            username="owner",
            password="testpass123",
        )

        self.viewer = User.objects.create_user(
            username="viewer",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="other",
            password="testpass123",
        )

        self.editor = User.objects.create_user(
            username="editor",
            password="testpass123",
        )

        self.document = Document.objects.create(
            title="Test document",
            category="General",
            owner=self.owner,
            file=SimpleUploadedFile(
                "test.txt",
                b"Test file content",
                content_type="text/plain",
            ),
        )

    def test_owner_can_view_document_details(self):

        self.client.login(username="owner", password="testpass123")

        response = self.client.get(
            reverse("document_details", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 200)

    def test_unshared_user_cannot_view_document_details(self):

        self.client.login(username="other", password="testpass123")

        response = self.client.get(
            reverse("document_details", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_viewer_with_permission_can_view_document_details(self):

        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_view=True,
            can_download=True,
            can_edit=False,
        )

        self.client.login(username="viewer", password="testpass123")

        response = self.client.get(
            reverse("document_details", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 200)

    def test_viewer_without_download_permission_cannot_download(self):

        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_view=True,
            can_download=False,
            can_edit=False,
        )

        self.client.login(username="viewer", password="testpass123")

        response = self.client.get(
            reverse("download_document", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_viewer_with_download_permission_can_download(self):

        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_view=True,
            can_download=True,
            can_edit=False,
        )

        self.client.login(username="viewer", password="testpass123")

        response = self.client.get(
            reverse("download_document", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 200)

    def test_revoked_viewer_cannot_download_file(self):

        permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_view=True,
            can_download=True,
            can_edit=False,
        )

        permission.delete()

        self.client.login(username="viewer", password="testpass123")

        response = self.client.get(
            reverse("download_document", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_viewer_with_view_permission_can_view_file(self):

        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_view=True,
            can_download=False,
            can_edit=False,
        )

        self.client.login(username="viewer", password="testpass123")

        response = self.client.get(
            reverse("view_document", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 200)

    def test_unshared_user_cannot_view_file(self):

        self.client.login(username="other", password="testpass123")

        response = self.client.get(
            reverse("view_document", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_viewer_without_edit_permission_cannot_edit_document(self):

        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_view=True,
            can_download=False,
            can_edit=False,
        )

        self.client.login(username="viewer", password="testpass123")

        response = self.client.get(
            reverse("edit_document", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 403)

    # NEW TEST 10: Editor can access edit page

    def test_editor_with_permission_can_edit_document(self):

        DocumentPermission.objects.create(
            document=self.document,
            user=self.editor,
            can_view=True,
            can_download=False,
            can_edit=True,
        )

        self.client.login(username="editor", password="testpass123")

        response = self.client.get(
            reverse("edit_document", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 200)

    # NEW TEST 11: Unauthorized user cannot delete

    def test_unshared_user_cannot_delete_document(self):

        self.client.login(username="other", password="testpass123")

        response = self.client.post(
            reverse("delete_document", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Document.objects.filter(id=self.document.id).exists()
        )

    # NEW TEST 12: Unauthorized user cannot share

    def test_unshared_user_cannot_share_document(self):

        self.client.login(username="other", password="testpass123")

        response = self.client.post(
            reverse("share_document", args=[self.document.id]),
            {
                "username": "viewer",
                "can_view": "on",
            }
        )

        self.assertEqual(response.status_code, 403)

        self.assertFalse(
            DocumentPermission.objects.filter(
                document=self.document,
                user=self.viewer
            ).exists()
        )

    # NEW TEST 13: Unauthorized access is recorded

    def test_unauthorized_access_is_recorded_in_audit_log(self):

        self.client.login(username="other", password="testpass123")

        response = self.client.get(
            reverse("document_details", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            AuditLog.objects.filter(
                user=self.other_user,
                document_id=str(self.document.id),
                action="DENIED"
            ).exists()
        )
        
    

    def test_valid_txt_file_is_accepted(self):

        uploaded_file = SimpleUploadedFile(
            "sample.txt",
            b"Hello TrustVault",
            content_type="text/plain",
        )

        form = DocumentForm(
            data={
                "title": "Sample TXT",
                "category": "General",
            },
            files={"file": uploaded_file},
        )

        self.assertTrue(form.is_valid(), form.errors)



    def test_invalid_pdf_content_is_rejected(self):

        uploaded_file = SimpleUploadedFile(
            "fake.pdf",
            b"This is not a PDF file",
            content_type="application/pdf",
        )

        form = DocumentForm(
            data={
                "title": "Fake PDF",
                "category": "General",
            },
            files={"file": uploaded_file},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    

    def test_empty_file_is_rejected(self):

        uploaded_file = SimpleUploadedFile(
            "empty.txt",
            b"",
            content_type="text/plain",
        )

        form = DocumentForm(
            data={
                "title": "Empty File",
                "category": "General",
            },
            files={"file": uploaded_file},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    

    def test_file_above_5mb_is_rejected(self):

        uploaded_file = SimpleUploadedFile(
            "large.txt",
            b"A" * (5 * 1024 * 1024 + 1),
            content_type="text/plain",
        )

        form = DocumentForm(
            data={
                "title": "Large File",
                "category": "General",
            },
            files={"file": uploaded_file},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    

    def test_invalid_file_extension_is_rejected(self):

        uploaded_file = SimpleUploadedFile(
            "malware.exe",
            b"sample executable content",
            content_type="application/octet-stream",
        )

        form = DocumentForm(
            data={
                "title": "Invalid File",
                "category": "General",
            },
            files={"file": uploaded_file},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)


    def test_valid_pdf_file_is_accepted(self):

        pdf_content = (
            b"%PDF-1.4\n"
            b"1 0 obj\n"
            b"<< /Type /Catalog >>\n"
            b"endobj\n"
            b"%%EOF"
        )

        uploaded_file = SimpleUploadedFile(
            "sample.pdf",
            pdf_content,
            content_type="application/pdf",
        )

        form = DocumentForm(
            data={
                "title": "Sample PDF",
                "category": "General",
            },
            files={"file": uploaded_file},
        )

        self.assertTrue(form.is_valid(), form.errors)

