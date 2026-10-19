import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getErrorMessage } from "../api/client";
import Spinner from "../components/Spinner";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) return setError("Passwords do not match.");
    setBusy(true);
    try {
      await register({ username: form.username, email: form.email, password: form.password });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, "Registration failed."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-wrap">
      <form className="card auth-card" onSubmit={onSubmit}>
        <h2>Create your account</h2>
        <p className="muted">It takes less than a minute.</p>
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Username
          <input name="username" value={form.username} onChange={onChange} autoComplete="username" required autoFocus />
        </label>
        <label>
          Email <span className="muted">(optional)</span>
          <input type="email" name="email" value={form.email} onChange={onChange} autoComplete="email" />
        </label>
        <label>
          Password
          <input type="password" name="password" value={form.password} onChange={onChange} autoComplete="new-password" required minLength={8} />
        </label>
        <label>
          Confirm password
          <input type="password" name="confirm" value={form.confirm} onChange={onChange} autoComplete="new-password" required />
        </label>
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? <Spinner small label="Creating account..." /> : "Sign up"}
        </button>
        <p className="auth-switch">
          Already registered? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
