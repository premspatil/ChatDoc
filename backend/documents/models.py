import uuid

from django.conf import settings
from django.db import models


def upload_path(instance, filename):
    """Store files as documents/<user_id>/<random>.pdf.

    The user's original filename is NEVER used in the path, which blocks path-traversal
    tricks like '../../etc/passwd.pdf'. The original name is kept in `original_filename`.
    """
    return f"documents/{instance.owner_id}/{uuid.uuid4().hex}.pdf"


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents"
    )
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=upload_path, max_length=255)
    file_hash = models.CharField(max_length=64)  # SHA-256, used to skip duplicate uploads
    file_size = models.PositiveBigIntegerField(default=0)
    page_count = models.PositiveIntegerField(default=0)
    chunk_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["owner", "-created_at"])]
        constraints = [
            models.UniqueConstraint(fields=["owner", "file_hash"], name="unique_pdf_per_owner")
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"
