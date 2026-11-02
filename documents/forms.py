
from django import forms
from .models import Document
import os
import magic
import zipfile


class DocumentForm(forms.ModelForm):

    class Meta:
        model = Document
        fields = ["title", "category", "file"]

    def clean_file(self):

        uploaded_file = self.cleaned_data.get("file")

        if not uploaded_file:
            raise forms.ValidationError("Please select a file.")

        # Check file extension
        allowed_extensions = [".pdf", ".docx", ".txt"]

        extension = os.path.splitext(uploaded_file.name)[1].lower()

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "Only PDF, DOCX and TXT files are allowed."
            )

        # Check file size (5 MB)
        max_size = 5 * 1024 * 1024

        if uploaded_file.size > max_size:
            raise forms.ValidationError(
                "File size must not exceed 5 MB."
            )

        # Reject empty files
        if uploaded_file.size == 0:
            raise forms.ValidationError(
                "Empty files are not allowed."
            )

        # Read file content
        uploaded_file.seek(0)
        file_content = uploaded_file.read()
        uploaded_file.seek(0)

        # Validate actual file type
        if extension == ".pdf":

            if not file_content.startswith(b"%PDF-"):
                raise forms.ValidationError(
                    "Invalid PDF file content."
                )

            detected_type = magic.from_buffer(
                file_content[:2048],
                mime=True
            )

            if detected_type != "application/pdf":
                raise forms.ValidationError(
                    "The uploaded file is not a valid PDF."
                )

        elif extension == ".docx":

            uploaded_file.seek(0)

            try:
                with zipfile.ZipFile(uploaded_file) as docx_file:

                    if (
                        "[Content_Types].xml" not in docx_file.namelist()
                        or "word/document.xml" not in docx_file.namelist()
                    ):
                        raise forms.ValidationError(
                            "Invalid DOCX document."
                        )

                    if docx_file.testzip() is not None:
                        raise forms.ValidationError(
                            "DOCX file is corrupted."
                        )

            except zipfile.BadZipFile:
                raise forms.ValidationError(
                    "Invalid DOCX file content."
                )

            finally:
                uploaded_file.seek(0)

        elif extension == ".txt":

            try:
                file_content.decode("utf-8")
            except UnicodeDecodeError:
                raise forms.ValidationError(
                    "TXT file must contain valid UTF-8 text."
                )

        return uploaded_file


class DocumentUpdateForm(forms.ModelForm):

    class Meta:
        model = Document
        fields = ["title", "category"]
