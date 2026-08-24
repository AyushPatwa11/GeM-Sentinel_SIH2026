import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";
import { api } from "../lib/api.js";

export default function Login() {
  const [role, setRole] = useState("officer");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("demo");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api.login(email || `${role}@gem.gov.in`, password, role);
      login(data);
      navigate(role === "officer" ? "/officer" : "/bidder");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex flex-1 bg-ink text-white flex-col justify-between p-14 relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.07]" style={{
          backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
          backgroundSize: "28px 28px",
        }} />
        <div className="relative">
          <div className="flex items-center gap-2.5 mb-16">
            <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" className="w-5 h-5">
                <path d="M12 2 4 6v6c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V6l-8-4Z" />
                <path d="m9 12 2 2 4-4" />
              </svg>
            </div>
            <span className="font-display font-semibold text-lg">GeM Sentinel</span>
          </div>
          <h1 className="font-display text-5xl font-semibold leading-[1.1] max-w-lg">
            Verify bid compliance with evidence, not guesswork.
          </h1>
          <p className="mt-6 text-white/60 max-w-md leading-relaxed">
            Every requirement extracted from the tender, every claim checked against
            source records, every recommendation traceable to the document it came from.
            The officer decides — the platform proves its work.
          </p>
        </div>
        <div className="relative flex gap-8 text-sm text-white/50">
          <div><span className="text-white font-medium">Rule-based</span> compliance engine</div>
          <div><span className="text-white font-medium">Evidence-linked</span> every verdict</div>
          <div><span className="text-white font-medium">Human</span>-in-the-loop</div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-canvas">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h2 className="font-display text-2xl font-semibold text-ink">Sign in</h2>
            <p className="text-sm text-slate mt-1">GeM/2026/T-101 — Chennai Petroleum Corporation Limited</p>
          </div>

          <div className="flex rounded-lg bg-line p-1 mb-6">
            {["officer", "bidder"].map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRole(r)}
                className={`flex-1 text-sm font-medium py-2 rounded-md transition-colors ${
                  role === r ? "bg-white text-ink shadow-sm" : "text-slate"
                }`}
              >
                {r === "officer" ? "Procurement Officer" : "Bidder"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={role === "officer" ? "po.sharma@gem.gov.in" : "bidder@company.com"}
                className="w-full px-3 py-2.5 rounded-lg border border-line bg-white text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg border border-line bg-white text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
              />
            </div>
            {error && <div className="text-sm text-fail">{error}</div>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-accent hover:bg-accent2 text-white text-sm font-medium py-2.5 rounded-lg transition-colors disabled:opacity-60"
            >
              {loading ? "Signing in…" : `Sign in as ${role === "officer" ? "Officer" : "Bidder"}`}
            </button>
          </form>

          <p className="text-xs text-slate mt-6 text-center">
            Demo credentials — any email/password works. This is a hackathon build.
          </p>
        </div>
      </div>
    </div>
  );
}
