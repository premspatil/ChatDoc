from rest_framework import serializers

from documents.models import Document

from .models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "sources", "created_at"]
        read_only_fields = fields


class ChatSessionSerializer(serializers.ModelSerializer):
    document_id = serializers.PrimaryKeyRelatedField(
        source="document", queryset=Document.objects.all(), write_only=True
    )
    document = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ["id", "title", "document", "document_id", "created_at", "updated_at"]
        read_only_fields = ["id", "title", "created_at", "updated_at"]

    def get_document(self, obj):
        return {
            "id": obj.document_id,
            "original_filename": obj.document.original_filename,
            "status": obj.document.status,
        }

    def validate_document_id(self, document):
        request = self.context["request"]
        # Must be MY document, and it must be fully processed.
        if document.owner_id != request.user.id:
            raise serializers.ValidationError("Document not found.")
        if document.status != Document.Status.READY:
            raise serializers.ValidationError("This document is not ready for questions yet.")
        return document


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000, trim_whitespace=True)
