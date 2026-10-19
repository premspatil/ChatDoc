import { formatBytes, formatDate } from "../utils/format";

const STATUS_LABEL = {
  pending: "Pending",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

export default function DocumentCard({ doc, onChat, onDelete, busy }) {
  return (
    <div className="card doc-card">
      <div className="doc-card-head">
        <span className="doc-icon">📕</span>
        <div className="doc-title" title={doc.original_filename}>
          {doc.original_filename}
        </div>
        <span className={`badge badge-${doc.status}`}>{STATUS_LABEL[doc.status] || doc.status}</span>
      </div>
      <div className="doc-meta">
        <span>{doc.page_count} pages</span>
        <span>{formatBytes(doc.file_size)}</span>
        <span>{formatDate(doc.created_at)}</span>
      </div>
      {doc.status === "failed" && doc.error_message && (
        <div className="alert alert-error">{doc.error_message}</div>
      )}
      <div className="doc-actions">
        <button
          className="btn btn-primary btn-sm"
          disabled={doc.status !== "ready" || busy}
          onClick={() => onChat(doc)}
        >
          Ask questions
        </button>
        <button className="btn btn-ghost btn-sm" disabled={busy} onClick={() => onDelete(doc)}>
          Delete
        </button>
      </div>
    </div>
  );
}
