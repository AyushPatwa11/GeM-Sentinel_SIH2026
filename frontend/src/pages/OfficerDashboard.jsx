import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";

export default function OfficerDashboard() {
  const [bids, setBids] = useState(null);
  const [filterRisk, setFilterRisk] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState("");
  const [lastSync, setLastSync] = useState(new Date());
  const navigate = useNavigate();

  async function load() {
    try {
      const data = await api.officerBids();
      setBids(data);
      setLastSync(new Date());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
    const refreshTimer = window.setInterval(load, 3000);
    return () => window.clearInterval(refreshTimer);
  }, []);

  async function evaluateAll() {
    for (const b of bids || []) {
      await api.officerEvaluate(b.bid_id);
    }
    load();
  }

  const summary = bids
    ? {
        total: bids.length,
        high: bids.filter((b) => b.risk_level === "HIGH").length,
        medium: bids.filter((b) => b.risk_level === "MEDIUM").length,
        low: bids.filter((b) => b.risk_level === "LOW").length,
        pending: bids.filter((b) => b.decision === "PENDING").length,
        verified: bids.filter((b) => b.decision === "VERIFIED").length,
        non_compliant: bids.filter((b) => b.decision === "NON_COMPLIANT").length,
      }
    : null;

  const filteredBids = (bids || []).filter((b) => {
    if (filterRisk !== "ALL" && b.risk_level !== filterRisk) return false;
    if (
      searchQuery &&
      !b.bidder_org_name.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !b.bid_id.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <Shell>
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <div className="inline-flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-2.5 py-0.5 rounded-full">
              Procurement Officer Workspace
            </span>
            <span className="text-xs text-slate">MoPNG / CPCL Sentinel</span>
          </div>
          <h1 className="font-display text-2xl font-bold text-ink">Bid Verification & Evaluation Queue</h1>
          <p className="text-sm text-slate mt-0.5">
            Real-time compliance monitoring, risk assessment, and decision gating for GeM procurement.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-xs text-slate flex items-center gap-1.5 bg-card border border-line px-3 py-2 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-pass animate-pulse" />
            <span>Synced: {lastSync.toLocaleTimeString()}</span>
          </div>
          <button
            onClick={evaluateAll}
            className="bg-accent hover:bg-accent2 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm transition-colors"
          >
            ⚡ Re-run Verification on All
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-card border border-line rounded-card p-4 shadow-xs">
            <div className="text-xs text-slate font-medium">Total Bids In Queue</div>
            <div className="text-2xl font-bold text-ink mt-1 font-mono">{summary.total}</div>
            <div className="text-[11px] text-slate mt-1">{summary.pending} awaiting officer decision</div>
          </div>

          <div className="bg-card border border-line rounded-card p-4 shadow-xs">
            <div className="text-xs font-medium text-fail">High Risk Signals</div>
            <div className="text-2xl font-bold text-fail mt-1 font-mono">{summary.high}</div>
            <div className="text-[11px] text-slate mt-1">Requires forensic review</div>
          </div>

          <div className="bg-card border border-line rounded-card p-4 shadow-xs">
            <div className="text-xs font-medium text-review">Pending Officer Decision</div>
            <div className="text-2xl font-bold text-review mt-1 font-mono">{summary.pending}</div>
            <div className="text-[11px] text-slate mt-1">Human-in-the-loop gating</div>
          </div>

          <div className="bg-card border border-line rounded-card p-4 shadow-xs">
            <div className="text-xs font-medium text-pass">Decided / Verified</div>
            <div className="text-2xl font-bold text-pass mt-1 font-mono">{summary.verified}</div>
            <div className="text-[11px] text-slate mt-1">{summary.non_compliant} marked non-compliant</div>
          </div>
        </div>
      )}

      {/* Main Table Card */}
      <div className="bg-card border border-line rounded-card overflow-hidden shadow-sm">
        {/* Table Filters Bar */}
        <div className="px-5 py-3.5 border-b border-line bg-canvas/40 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-ink uppercase tracking-wider">Filter Risk:</span>
            {["ALL", "HIGH", "MEDIUM", "LOW"].map((r) => (
              <button
                key={r}
                onClick={() => setFilterRisk(r)}
                className={`text-xs px-2.5 py-1 rounded-md font-semibold transition-all ${
                  filterRisk === r
                    ? "bg-accent text-white shadow-xs"
                    : "bg-white border border-line text-slate hover:text-ink"
                }`}
              >
                {r}
              </button>
            ))}
          </div>

          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search bidder or bid ID…"
              className="bg-white border border-line rounded-lg px-3 py-1.5 text-xs text-ink focus:outline-none focus:border-accent w-56"
            />
          </div>
        </div>

        {!bids && !error && <div className="px-5 py-12 text-center text-sm text-slate">Loading real-time bid queue…</div>}
        {error && <div className="px-5 py-6 text-sm text-fail">{error}</div>}

        {bids && (
          <table className="w-full text-xs text-left">
            <thead className="bg-canvas border-b border-line text-slate uppercase font-semibold">
              <tr>
                <th className="px-5 py-3">Bidder Entity</th>
                <th className="px-5 py-3">GSTIN / Identifiers</th>
                <th className="px-5 py-3">Tender</th>
                <th className="px-5 py-3">Submission</th>
                <th className="px-5 py-3">Compliance</th>
                <th className="px-5 py-3">Risk Level</th>
                <th className="px-5 py-3">Officer Decision</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {filteredBids.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-5 py-8 text-center text-slate">
                    No bids match the active filters.
                  </td>
                </tr>
              ) : (
                filteredBids.map((b) => (
                  <tr
                    key={b.bid_id}
                    className="hover:bg-canvas/60 cursor-pointer transition-colors"
                    onClick={() => navigate(`/officer/bids/${b.bid_id}`)}
                  >
                    <td className="px-5 py-3.5">
                      <div className="font-bold text-ink">{b.bidder_org_name}</div>
                      <div className="text-[11px] font-mono text-slate mt-0.5">ID: {b.bid_id}</div>
                    </td>
                    <td className="px-5 py-3.5 font-mono text-[11px] text-slate">
                      {b.gstin || "—"}
                    </td>
                    <td className="px-5 py-3.5 text-slate max-w-[200px] truncate">
                      {b.tender?.title || "—"}
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={b.status} />
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={b.compliance_status} />
                    </td>
                    <td className="px-5 py-3.5">
                      {b.risk_level ? (
                        <div className="flex items-center gap-1.5">
                          <StatusBadge status={b.risk_level} />
                          <span className="font-mono text-[11px] text-slate font-medium">({b.risk_score})</span>
                        </div>
                      ) : (
                        <span className="text-slate">Not evaluated</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={b.decision} />
                    </td>
                    <td className="px-5 py-3.5 text-right font-semibold text-accent hover:underline">
                      Review Bid →
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </Shell>
  );
}
