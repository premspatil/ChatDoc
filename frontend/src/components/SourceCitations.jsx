import { useState } from "react";
import { uniquePages } from "../utils/format";

export default function SourceCitations({ sources }) {
  const [open, setOpen] = useState(false);
  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources">
      <button className="sources-toggle" onClick={() => setOpen((o) => !o)}>
        📎 Sources: page {uniquePages(sources)} {open ? "▲" : "▼"}
      </button>
      {open && (
        <ul className="sources-list">
          {sources.map((s) => (
            <li key={s.chunk_id}>
              <span className="source-page">Page {s.page}</span>
              <span className="source-snippet">“{s.snippet}”</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
