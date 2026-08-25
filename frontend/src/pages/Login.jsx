import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";
import { api } from "../lib/api.js";
import { ShieldCheck, ArrowLeft, Lock, Mail, CheckCircle2 } from "lucide-react";

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
    <div className="min-h-screen flex bg-canvas font-body text-ink antialiased">
      {/* Left Hero Panel */}
      <div className="hidden lg:flex flex-1 bg-ink text-white flex-col justify-between p-14 relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />

        <div className="relative">
          <Link to="/" className="inline-flex items-center gap-2.5 mb-14 text-white/80 hover:text-white transition-colors group">
            <div className="w-9 h-9 rounded-xl bg-accent flex items-center justify-center shadow-md shadow-accent/30">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <span className="font-display font-bold text-lg tracking-tight">GeM Sentinel</span>
            <span className="text-xs text-white/40 group-hover:text-white/60 ml-2">← Back to Overview</span>
          </Link>

          <h1 className="font-display text-5xl font-bold leading-[1.12] max-w-lg tracking-tight">
            Verify bid compliance with evidence, not guesswork.
          </h1>

          <p className="mt-6 text-white/70 max-w-md leading-relaxed text-base font-light">
            Every requirement extracted from the tender, every claim checked against
            source records, every recommendation traceable to the document it came from.
            The officer decides — the platform proves its work.
          </p>
        </div>

        <div className="relative flex flex-wrap gap-8 text-xs text-white/60 pt-8 border-t border-white/10">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-pass shrink-0" />
            <span><strong className="text-white">Rule-based</strong> logic engine</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-pass shrink-0" />
            <span><strong className="text-white">Evidence-linked</strong> verdicts</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-pass shrink-0" />
            <span><strong className="text-white">Human-in-the-loop</strong> gating</span>
          </div>
        </div>
      </div>

      {/* Right Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-canvas">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <div className="lg:hidden flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
                <ShieldCheck className="w-4 h-4 text-white" />
              </div>
              <span className="font-display font-bold text-base text-ink">GeM Sentinel</span>
            </div>

            <h2 className="font-display text-2xl font-bold text-ink tracking-tight">Sign In</h2>
            <p className="text-xs text-slate mt-1">
              Live Demo: GeM/2026/T-101 — Chennai Petroleum Corp Ltd
            </p>
          </div>

          {/* Role Tabs */}
          <div className="flex rounded-xl bg-line/80 p-1 mb-6 border border-line">
            {["officer", "bidder"].map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRole(r)}
                className={`flex-1 text-xs font-semibold py-2.5 rounded-lg transition-all cursor-pointer ${
                  role === r ? "bg-white text-ink shadow-xs" : "text-slate hover:text-ink"
                }`}
              >
                {r === "officer" ? "Procurement Officer" : "Bidder Account"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate uppercase tracking-wider mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={role === "officer" ? "po.sharma@gem.gov.in" : "bidder@company.com"}
                  className="w-full pl-9 pr-3.5 py-2.5 rounded-xl border border-line bg-white text-xs font-medium text-ink focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent shadow-xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate uppercase tracking-wider mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3.5 py-2.5 rounded-xl border border-line bg-white text-xs font-medium text-ink focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent shadow-xs"
                />
              </div>
            </div>

            {error && <div className="text-xs text-fail bg-failBg p-2.5 rounded-lg border border-fail/20">{error}</div>}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-accent hover:bg-accent2 text-white text-xs font-semibold py-3 rounded-xl shadow-sm shadow-accent/20 transition-all hover:scale-[1.01] disabled:opacity-60 cursor-pointer"
            >
              {loading ? "Authenticating…" : `Sign In as ${role === "officer" ? "Officer" : "Bidder"}`}
            </button>
          </form>

          <p className="text-[11px] text-slate mt-6 text-center">
            Demo workspace — credentials pre-filled for rapid evaluation.
          </p>
        </div>
      </div>
    </div>
  );
}
