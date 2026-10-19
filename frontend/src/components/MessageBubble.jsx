import { formatTime } from "../utils/format";
import SourceCitations from "./SourceCitations";

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={`message ${isUser ? "message-user" : "message-ai"}`}>
      <div className="avatar">{isUser ? "You" : "AI"}</div>
      <div className="bubble">
        <div className="bubble-text">{message.content}</div>
        {!isUser && <SourceCitations sources={message.sources} />}
        {message.created_at && <div className="bubble-time">{formatTime(message.created_at)}</div>}
      </div>
    </div>
  );
}
