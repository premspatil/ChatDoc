import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import * as chatsApi from "../api/chats";
import { getErrorMessage } from "../api/client";
import ChatSidebar from "../components/ChatSidebar";
import ConfirmDialog from "../components/ConfirmDialog";
import MessageBubble from "../components/MessageBubble";
import Spinner from "../components/Spinner";
import useDocuments from "../hooks/useDocuments";

export default function ChatPage() {
  const { chatId } = useParams();
  const activeId = chatId ? Number(chatId) : null;
  const navigate = useNavigate();
  const { documents } = useDocuments();

  const [chats, setChats] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [confirm, setConfirm] = useState(null); // {type: "delete"|"clear", chat}
  const [confirmBusy, setConfirmBusy] = useState(false);
  const bottomRef = useRef(null);

  const activeChat = chats.find((c) => c.id === activeId);

  const loadChats = useCallback(async () => {
    try {
      setChats(await chatsApi.listChats());
    } catch (err) {
      setError(getErrorMessage(err, "Could not load your chats."));
    }
  }, []);

  useEffect(() => {
    loadChats();
  }, [loadChats]);

  // Load messages whenever the selected chat changes.
  useEffect(() => {
    setError("");
    if (!activeId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    setLoadingMessages(true);
    chatsApi
      .getMessages(activeId)
      .then((data) => !cancelled && setMessages(data))
      .catch((err) => {
        if (cancelled) return;
        setError(getErrorMessage(err, "Could not load this chat."));
        if (err.response?.status === 404) navigate("/chat", { replace: true });
      })
      .finally(() => !cancelled && setLoadingMessages(false));
    return () => {
      cancelled = true;
    };
  }, [activeId, navigate]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const selectChat = (id) => {
    setSidebarOpen(false);
    navigate(`/chat/${id}`);
  };

  const createNewChat = async (documentId) => {
    setCreating(true);
    setError("");
    try {
      const chat = await chatsApi.createChat(documentId);
      setChats((prev) => [chat, ...prev]);
      setSidebarOpen(false);
      navigate(`/chat/${chat.id}`);
    } catch (err) {
      setError(getErrorMessage(err, "Could not create the chat."));
    } finally {
      setCreating(false);
    }
  };

  const send = async () => {
    const question = input.trim();
    if (!question || sending || !activeId) return;
    setError("");
    setInput("");
    setSending(true);
    const tempId = `temp-${Date.now()}`;
    setMessages((prev) => [...prev, { id: tempId, role: "user", content: question, sources: [] }]);
    try {
      const data = await chatsApi.askQuestion(activeId, question);
      setMessages((prev) => [...prev.filter((m) => m.id !== tempId), data.user_message, data.assistant_message]);
      setChats((prev) =>
        prev
          .map((c) => (c.id === activeId ? { ...c, title: data.chat_title } : c))
          .sort((a, b) => (a.id === activeId ? -1 : b.id === activeId ? 1 : 0))
      );
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
      setInput(question); // give the question back so the user can retry
      setError(getErrorMessage(err, "Could not get an answer."));
    } finally {
      setSending(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const runConfirm = async () => {
    setConfirmBusy(true);
    try {
      if (confirm.type === "delete") {
        await chatsApi.deleteChat(confirm.chat.id);
        setChats((prev) => prev.filter((c) => c.id !== confirm.chat.id));
        if (confirm.chat.id === activeId) navigate("/chat");
      } else {
        await chatsApi.clearMessages(confirm.chat.id);
        setMessages([]);
        setChats((prev) => prev.map((c) => (c.id === confirm.chat.id ? { ...c, title: "New chat" } : c)));
      }
      setConfirm(null);
    } catch (err) {
      setError(getErrorMessage(err));
      setConfirm(null);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <div className="chat-layout">
      <ChatSidebar
        chats={chats}
        documents={documents}
        activeId={activeId}
        creating={creating}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onSelect={selectChat}
        onCreate={createNewChat}
        onDelete={(chat) => setConfirm({ type: "delete", chat })}
      />

      <section className="chat-main">
        <div className="chat-header">
          <button className="btn btn-ghost btn-sm menu-btn" onClick={() => setSidebarOpen(true)}>
            ☰ Chats
          </button>
          <div className="chat-header-title">
            {activeChat ? (
              <>
                <strong>{activeChat.title}</strong>
                <span className="muted small"> · {activeChat.document.original_filename}</span>
              </>
            ) : (
              <strong>ChatDoc</strong>
            )}
          </div>
          {activeChat && messages.length > 0 && (
            <button className="btn btn-ghost btn-sm" onClick={() => setConfirm({ type: "clear", chat: activeChat })}>
              Clear
            </button>
          )}
        </div>

        <div className="chat-body">
          {!activeId && (
            <div className="empty">
              <div className="empty-icon">💬</div>
              <h3>Select or start a chat</h3>
              <p className="muted">Pick a PDF in the sidebar and press “New chat”, or open an earlier conversation.</p>
            </div>
          )}
          {activeId && loadingMessages && <Spinner label="Loading messages..." />}
          {activeId && !loadingMessages && messages.length === 0 && (
            <div className="empty">
              <div className="empty-icon">❓</div>
              <h3>Ask your first question</h3>
              <p className="muted">For example: “Summarize this document” or “What does page 3 say about…?”</p>
            </div>
          )}
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {sending && (
            <div className="message message-ai">
              <div className="avatar">AI</div>
              <div className="bubble">
                <Spinner small label="Searching the document and thinking..." />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {error && <div className="alert alert-error chat-error">{error}</div>}

        {activeId && (
          <div className="chat-input">
            <textarea
              rows={1}
              value={input}
              maxLength={1000}
              placeholder="Ask a question about this PDF... (Enter to send, Shift+Enter for a new line)"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={sending}
            />
            <button className="btn btn-primary" onClick={send} disabled={sending || !input.trim()}>
              Send
            </button>
          </div>
        )}
      </section>

      <ConfirmDialog
        open={Boolean(confirm)}
        title={confirm?.type === "delete" ? "Delete this chat?" : "Clear this conversation?"}
        message={
          confirm?.type === "delete"
            ? "The chat and all its messages will be permanently deleted."
            : "All messages in this chat will be removed. The chat itself stays."
        }
        confirmLabel={confirm?.type === "delete" ? "Delete" : "Clear"}
        busy={confirmBusy}
        onConfirm={runConfirm}
        onCancel={() => setConfirm(null)}
      />
    </div>
  );
}
