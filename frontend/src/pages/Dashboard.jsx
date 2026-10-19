import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createChat } from "../api/chats";
import { getErrorMessage } from "../api/client";
import ConfirmDialog from "../components/ConfirmDialog";
import DocumentCard from "../components/DocumentCard";
import Spinner from "../components/Spinner";
import UploadBox from "../components/UploadBox";
import { useAuth } from "../context/AuthContext";
import useDocuments from "../hooks/useDocuments";

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { documents, loading, error, reload, remove } = useDocuments();
  const [toDelete, setToDelete] = useState(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");

  const startChat = async (doc) => {
    setBusy(true);
    setActionError("");
    try {
      const chat = await createChat(doc.id);
      navigate(`/chat/${chat.id}`);
    } catch (err) {
      setActionError(getErrorMessage(err, "Could not start a chat."));
      setBusy(false);
    }
  };

  const confirmDelete = async () => {
    setBusy(true);
    try {
      await remove(toDelete.id);
      setToDelete(null);
    } catch (err) {
      setActionError(getErrorMessage(err, "Could not delete the document."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container page">
      <div className="page-head">
        <div>
          <h1>Your documents</h1>
          <p className="muted">Hi {user.username}, upload a PDF and start asking questions.</p>
        </div>
      </div>

      <UploadBox onUploaded={reload} />
      {actionError && <div className="alert alert-error">{actionError}</div>}

      <h2 className="section-title left">Uploaded PDFs</h2>
      {loading && <Spinner label="Loading documents..." />}
      {error && <div className="alert alert-error">{error}</div>}
      {!loading && !error && documents.length === 0 && (
        <div className="empty">
          <div className="empty-icon">🗂️</div>
          <h3>No documents yet</h3>
          <p className="muted">Upload your first PDF above to get started.</p>
        </div>
      )}
      <div className="grid grid-3">
        {documents.map((doc) => (
          <DocumentCard key={doc.id} doc={doc} busy={busy} onChat={startChat} onDelete={setToDelete} />
        ))}
      </div>

      <ConfirmDialog
        open={Boolean(toDelete)}
        title="Delete this document?"
        message={`"${toDelete?.original_filename}" and all chats about it will be permanently deleted.`}
        busy={busy}
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
