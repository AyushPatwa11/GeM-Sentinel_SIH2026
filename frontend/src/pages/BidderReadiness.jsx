import React, { useEffect, useState } from "react";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";

const DEMO_BIDS = [
  { id: "bid-northline", label: "Northline Engineering (clean bid demo)" },
  { id: "bid-coastal", label: "Coastal Agro Supplies (missing threshold demo)" },
  { id: "bid-meridian", label: "Meridian Textiles (identity mismatch demo)" },
];

export default function BidderReadiness() {
  const [bidId, setBidId] = useState("bid-northline");
  const [readiness, setReadiness] = useState(null);
  const [loading, setLoading] = useState(false);

  async function load(id) {
    setLoading(true);
    try {
      const data = await api.bidderReadiness(id);
      setReadiness(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(bidId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bidId]);

  const ICON = {
    SATISFIED: "✓",
    MISSING: "✕",
    WEAK_EVIDENCE: "⚠",
    REVIEW: "⚠",
  };

  const canSubmit = readiness && !readiness.items.some((i) => i.status === "MISSING");

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold text-ink mb-1">Pre-submission compliance check</h1>
      <p className="text-sm text-slate mb-6">Run this before submitting to catch avoidable rejections. You cannot change tender requirements here.</p>

      <select
        value={bidId}
        onChange={(e) => setBidId(e.target.value)}
        className="mb-5 text-sm border border-line rounded-lg px-3 py-2 bg-white"
      >
        {DEMO_BIDS.map((b) => (
          <option key={b.id} value={b.id}>{b.label}</option>
        ))}
      </select>

      <div className="bg-card border border-line rounded-card px-5 py-5 max-w-lg">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-ink">Compliance readiness</span>
          <span className="font-display text-2xl font-semibold text-ink">
            {loading ? "…" : `${readiness?.readiness_percent ?? 0}%`}
          </span>
        </div>
        <p className="text-xs text-slate mb-4">GeM/2026/T-101 — Industrial Textile Materials</p>

        <div className="space-y-2">
          {readiness?.items.map((item) => (
            <div key={item.clause_id} className="flex items-start gap-2.5 border border-line rounded-lg px-3 py-2.5">
              <span
                className={`text-sm mt-0.5 ${
                  item.status === "SATISFIED" ? "text-pass" : item.status === "MISSING" ? "text-fail" : "text-review"
                }`}
              >
                {ICON[item.status]}
              </span>
              <span className="text-xs text-ink leading-relaxed">{item.requirement_summary}</span>
            </div>
          ))}
        </div>

        <div className="flex gap-2 mt-5 pt-4 border-t border-line">
          <button className="flex-1 text-xs font-medium border border-line text-ink rounded-lg py-2.5 hover:bg-canvas transition-colors">
            Upload documents
          </button>
          <button
            disabled={!canSubmit}
            className="flex-1 text-xs font-medium bg-accent text-white rounded-lg py-2.5 hover:bg-accent2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title={!canSubmit ? "Resolve mandatory items first" : ""}
          >
            Submit bid
          </button>
        </div>
      </div>
    </Shell>
  );
}
