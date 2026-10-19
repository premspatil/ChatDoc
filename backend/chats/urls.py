from django.urls import path

from .views import AskView, ChatDetailView, ChatListCreateView, ChatMessagesView

urlpatterns = [
    path("", ChatListCreateView.as_view(), name="chat-list"),
    path("<int:pk>/", ChatDetailView.as_view(), name="chat-detail"),
    path("<int:pk>/messages/", ChatMessagesView.as_view(), name="chat-messages"),
    path("<int:pk>/ask/", AskView.as_view(), name="chat-ask"),
]
