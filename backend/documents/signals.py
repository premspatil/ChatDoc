"""When a Document row is deleted (directly or by cascade), also delete its PDF file
and its vectors in ChromaDB, so nothing is left behind."""
import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver

from rag import vector_store

from .models import Document

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=Document)
def cleanup_document(sender, instance, **kwargs):
    try:
        vector_store.delete_document(instance.pk)
    except Exception:  # noqa: BLE001 - never block a delete because of the vector store
        logger.exception("Could not delete vectors for document %s", instance.pk)
    try:
        if instance.file:
            instance.file.delete(save=False)
    except Exception:  # noqa: BLE001
        logger.exception("Could not delete file for document %s", instance.pk)
