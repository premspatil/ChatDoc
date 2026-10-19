"""Upload validation and the processing step that turns a PDF into searchable vectors."""
import hashlib
import logging

from django.conf import settings
from rest_framework.exceptions import ValidationError

from rag.pdf_processor import PDFProcessingError, get_page_count
from rag.pipeline import NoExtractableTextError, index_document

from .models import Document

logger = logging.getLogger(__name__)

SCANNED_MESSAGE = (
    "No selectable text was found in this PDF. It may be a scanned document made of images. "
    "Please upload a PDF with real text (or run OCR on it first)."
)


def validate_upload(uploaded_file) -> tuple[bytes, int]:
    """Check name, size, type and readability. Returns (file bytes, page count)."""
    name = (uploaded_file.name or "").lower()
    if not name.endswith(".pdf"):
        raise ValidationError({"file": "Only .pdf files are allowed."})
    if uploaded_file.size == 0:
        raise ValidationError({"file": "The file is empty."})
    if uploaded_file.size > settings.MAX_UPLOAD_BYTES:
        raise ValidationError({"file": f"File is too large. Maximum size is {settings.MAX_UPLOAD_MB} MB."})

    data = uploaded_file.read()
    uploaded_file.seek(0)
    if not data.startswith(b"%PDF-"):  # check real content, not just the extension
        raise ValidationError({"file": "This file is not a valid PDF."})

    try:
        pages = get_page_count(data)
    except PDFProcessingError as exc:
        raise ValidationError({"file": str(exc)}) from exc
    if pages == 0:
        raise ValidationError({"file": "This PDF has no pages."})
    if pages > settings.MAX_PDF_PAGES:
        raise ValidationError({"file": f"PDF has too many pages (limit is {settings.MAX_PDF_PAGES})."})
    return data, pages


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def process_document(document: Document) -> Document:
    """Index the PDF. Never raises: problems are saved on the document as status=failed."""
    document.status = Document.Status.PROCESSING
    document.error_message = ""
    document.save(update_fields=["status", "error_message", "updated_at"])
    try:
        chunk_count = index_document(document.pk, document.owner_id, document.file.path)
        document.chunk_count = chunk_count
        document.status = Document.Status.READY
    except NoExtractableTextError:
        document.status = Document.Status.FAILED
        document.error_message = SCANNED_MESSAGE
    except PDFProcessingError as exc:
        document.status = Document.Status.FAILED
        document.error_message = str(exc)
    except Exception:  # noqa: BLE001
        logger.exception("Processing failed for document %s", document.pk)
        document.status = Document.Status.FAILED
        document.error_message = "Something went wrong while processing this PDF. Please try again."
    document.save()
    return document
