import { useRef, useState } from "react";
import { getErrorMessage } from "../api/client";
import { uploadDocument } from "../api/documents";
import Spinner from "./Spinner";

const MAX_MB = 20;

export default function UploadBox({ onUploaded }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("idle"); // idle | uploading | processing
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const busy = stage !== "idle";

  const handleFile = async (file) => {
    if (!file) return;
    setError("");
    setNotice("");
    if (!file.name.toLowerCase().endsWith(".pdf")) return setError("Please choose a PDF file.");
    if (file.size > MAX_MB * 1024 * 1024) return setError(`File is too large (max ${MAX_MB} MB).`);

    try {
      setStage("uploading");
      setProgress(0);
      const doc = await uploadDocument(file, (p) => {
        setProgress(p);
        if (p >= 100) setStage("processing"); // the server now reads and indexes the PDF
      });
      if (doc.duplicate) setNotice("You already uploaded this PDF, so the existing copy is being used.");
      onUploaded?.(doc);
    } catch (err) {
      setError(getErrorMessage(err, "Upload failed."));
    } finally {
      setStage("idle");
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div>
      <div
        className={`dropzone ${dragging ? "dragging" : ""} ${busy ? "busy" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!busy) handleFile(e.dataTransfer.files[0]);
        }}
        onClick={() => !busy && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && !busy && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          onChange={(e) => handleFile(e.target.files[0])}
        />
        {stage === "uploading" && (
          <>
            <Spinner label={`Uploading... ${progress}%`} />
            <div className="progress">
              <div className="progress-bar" style={{ width: `${progress}%` }} />
            </div>
          </>
        )}
        {stage === "processing" && (
          <Spinner label="Reading and indexing your PDF... (the first time can take a minute)" />
        )}
        {stage === "idle" && (
          <>
            <div className="dropzone-icon">📄</div>
            <strong>Drop a PDF here or click to browse</strong>
            <span className="muted">Text-based PDFs up to {MAX_MB} MB</span>
          </>
        )}
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-info">{notice}</div>}
    </div>
  );
}
