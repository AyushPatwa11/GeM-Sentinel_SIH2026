import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";

export default function OfficerDashboard() {
  const [bids, setBids] = useState(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function load() {
    try {
      const data = await api.officerBids();
      setBids(data);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
    const refreshTimer = window.setInterval(load, 4000);
    return () => window.clearInterval(refreshTimer);
  }, []);

  async function evaluateAll() {
    setBids(null);
    for (const b of bids || []) {
      await api.officerEvaluate(b.bid_id);
    }
    load();
  }

  const summary = bids
    ? {
        total: bids.length,
        high: bids.filter((b) => b.risk_level === "HIGH").length,
        pending: bids.filter((b) => b.decision === "PENDING").length,
      }
    : null;

  return (
    <Shell>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">GeM/2026/T-101</h1>
          <p className="text-sm text-slate mt-1">Supply of Industrial Textile Materials — Chennai Petroleum Corporation Limited</p>
        </div>
        <button
          onClick={evaluateAll}
          className="bg-accent hover:bg-accent2 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
        >
          Run verification on all bids
        </button>
      </div>

      {summary && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <SummaryCard label="Total bids received" value={summary.total} />
          <SummaryCard label="High-risk bids" value={summary.high} accent="fail" />
          <SummaryCard label="Awaiting officer decision" value={summary.pending} accent="review" />
        </div>
      )}

      <div className="bg-card border border-line rounded-card overflow-hidden">
        <div className="px-5 py-3.5 border-b border-line flex items-center justify-between">
          <span className="text-sm font-medium text-ink">Bids — sorted by risk</span>
        </div>

        {!bids && !error && <div className="px-5 py-10 text-center text-sm text-slate">Loading bids…</div>}
        {error && <div className="px-5 py-6 text-sm text-fail">{error} — is the backend running on :8000?</div>}

        {bids && (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate uppercase tracking-wide border-b border-line">
                <th className="px-5 py-3 font-medium">Bidder</th>
                <th className="px-5 py-3 font-medium">Tender</th>
                <th className="px-5 py-3 font-medium">Compliance</th>
                <th className="px-5 py-3 font-medium">Risk</th>
                <th className="px-5 py-3 font-medium">Decision</th>
                <th className="px-5 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {bids.map((b) => (
                <tr
                  key={b.bid_id}
                  className="border-b border-line last:border-0 hover:bg-canvas cursor-pointer transition-colors"
                  onClick={() => navigate(`/officer/bids/${b.bid_id}`)}
                >
                  <td className="px-5 py-3.5 font-medium text-ink">{b.bidder_org_name}</td>
                  <td className="px-5 py-3.5 text-xs text-slate">{b.tender?.title || "—"}</td>
                  <td className="px-5 py-3.5"><StatusBadge status={b.compliance_status} /></td>
                  <td className="px-5 py-3.5">{b.risk_level ? <StatusBadge status={b.risk_level} /> : <span className="text-slate text-xs">Not run</span>}</td>
                  <td className="px-5 py-3.5"><StatusBadge status={b.decision} /></td>
                  <td className="px-5 py-3.5 text-right text-accent text-xs font-medium">Review →</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Shell>
  );
}

function SummaryCard({ label, value, accent }) {
  const color = accent === "fail" ? "text-fail" : accent === "review" ? "text-review" : "text-ink";
  return (
    <div className="bg-card border border-line rounded-card px-5 py-4">
      <div className="text-xs text-slate mb-1">{label}</div>
      <div className={`font-display text-2xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}
