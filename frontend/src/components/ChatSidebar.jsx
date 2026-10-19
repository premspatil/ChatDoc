import { useState } from "react";

export default function ChatSidebar({
  chats,
  documents,
  activeId,
  creating,
  onSelect,
  onCreate,
  onDelete,
  open,
  onClose,
}) {
  const readyDocs = documents.filter((d) => d.status === "ready");
  const [docId, setDocId] = useState("");

  return (
    <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
      <div className="sidebar-head">
        <h3>Chats</h3>
        <button className="btn btn-ghost btn-sm sidebar-close" onClick={onClose}>
          ✕
        </button>
      </div>

      <div className="new-chat">
        {readyDocs.length === 0 ? (
          <p className="muted small">Upload a PDF on the dashboard to start a chat.</p>
        ) : (
          <>
            <select value={docId} onChange={(e) => setDocId(e.target.value)} aria-label="Choose a PDF">
              <option value="">Choose a PDF...</option>
              {readyDocs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename}
                </option>
              ))}
            </select>
            <button
              className="btn btn-primary btn-block"
              disabled={!docId || creating}
              onClick={() => onCreate(Number(docId))}
            >
              + New chat
            </button>
          </>
        )}
      </div>

      <ul className="chat-list">
        {chats.length === 0 && <li className="muted small pad">No chats yet.</li>}
        {chats.map((c) => (
          <li key={c.id} className={c.id === activeId ? "active" : ""}>
            <button className="chat-item" onClick={() => onSelect(c.id)}>
              <span className="chat-item-title">{c.title}</span>
              <span className="chat-item-doc">{c.document.original_filename}</span>
            </button>
            <button className="icon-btn" title="Delete chat" onClick={() => onDelete(c)}>
              🗑
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
