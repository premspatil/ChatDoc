import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const FEATURES = [
  { icon: "🔍", title: "Grounded answers", text: "Answers come from your PDF using Retrieval-Augmented Generation, not from guesses." },
  { icon: "📎", title: "Page citations", text: "Every answer shows the page numbers and text snippets it was based on." },
  { icon: "🔒", title: "Private by design", text: "Your documents and chats are only visible to your account." },
  { icon: "💬", title: "Follow-up questions", text: "Keep the conversation going. Your chat history is saved." },
];

const STEPS = [
  ["1", "Upload", "Add a text-based PDF. ChatDoc reads it page by page."],
  ["2", "Index", "The text is split into chunks and turned into embeddings."],
  ["3", "Ask", "Your question finds the best matching chunks, and the AI answers from them."],
];

export default function Landing() {
  const { user } = useAuth();
  return (
    <div>
      <section className="hero">
        <div className="container hero-inner">
          <span className="pill">AI-powered PDF question answering</span>
          <h1>
            Chat with your <span className="gradient-text">PDFs</span>
          </h1>
          <p className="hero-sub">
            Upload a document, ask questions in plain English, and get accurate answers with the exact
            pages they came from.
          </p>
          <div className="hero-actions">
            <Link to={user ? "/dashboard" : "/register"} className="btn btn-primary btn-lg">
              {user ? "Go to dashboard" : "Get started free"}
            </Link>
            {!user && (
              <Link to="/login" className="btn btn-ghost btn-lg">
                I have an account
              </Link>
            )}
          </div>
        </div>
      </section>

      <section className="container section">
        <h2 className="section-title">Why ChatDoc?</h2>
        <div className="grid grid-4">
          {FEATURES.map((f) => (
            <div className="card feature" key={f.title}>
              <div className="feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p className="muted">{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="container section">
        <h2 className="section-title">How it works</h2>
        <div className="grid grid-3">
          {STEPS.map(([n, title, text]) => (
            <div className="card step" key={n}>
              <div className="step-number">{n}</div>
              <h3>{title}</h3>
              <p className="muted">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          ChatDoc - built with Django, React, ChromaDB and Retrieval-Augmented Generation.
        </div>
      </footer>
    </div>
  );
}
