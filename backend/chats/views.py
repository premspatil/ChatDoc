import logging

from django.conf import settings
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from documents.models import Document
from rag import pipeline
from rag.llm_service import LLMError

from .models import ChatMessage, ChatSession
from .serializers import AskSerializer, ChatMessageSerializer, ChatSessionSerializer

logger = logging.getLogger(__name__)


def my_sessions(user):
    return ChatSession.objects.filter(owner=user).select_related("document")


class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        return my_sessions(self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ChatDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        return my_sessions(self.request.user)


class ChatMessagesView(APIView):
    def get(self, request, pk):
        session = generics.get_object_or_404(my_sessions(request.user), pk=pk)
        return Response(ChatMessageSerializer(session.messages.all(), many=True).data)

    def delete(self, request, pk):
        """Clear the conversation (messages only). The chat session itself stays."""
        session = generics.get_object_or_404(my_sessions(request.user), pk=pk)
        session.messages.all().delete()
        session.title = ChatSession.DEFAULT_TITLE
        session.save(update_fields=["title", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class AskView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ask"

    def post(self, request, pk):
        session = generics.get_object_or_404(my_sessions(request.user), pk=pk)
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]

        if session.document.status != Document.Status.READY:
            return Response(
                {"error": "This document is not ready for questions."}, status=status.HTTP_409_CONFLICT
            )

        history = [
            {"role": m.role, "content": m.content}
            for m in session.messages.order_by("-created_at", "-id")[: settings.HISTORY_MESSAGES]
        ][::-1]

        try:
            result = pipeline.answer_question(session.document_id, request.user.id, question, history)
        except LLMError as exc:
            return Response({"error": exc.message}, status=exc.status_code)
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected error while answering")
            return Response(
                {"error": "Something went wrong while answering. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        with transaction.atomic():
            user_message = ChatMessage.objects.create(
                session=session, role=ChatMessage.Role.USER, content=question
            )
            assistant_message = ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.ASSISTANT,
                content=result["answer"],
                sources=result["sources"],
            )
            if session.title == ChatSession.DEFAULT_TITLE:
                session.title = question[:60]
            session.save(update_fields=["title", "updated_at"])

        return Response(
            {
                "user_message": ChatMessageSerializer(user_message).data,
                "assistant_message": ChatMessageSerializer(assistant_message).data,
                "chat_title": session.title,
            },
            status=status.HTTP_201_CREATED,
        )
