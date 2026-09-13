import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";
import {
  ShieldAlert,
  ShieldCheck,
  Clock,
  FileStack,
  RefreshCw,
  Search,
  ChevronRight,
  Filter,
  Sparkles,
} from "lucide-react";

export default function OfficerDashboard() {
  const [bids, setBids] = useState(null);
  const [tenders, setTenders] = useState(null);
  const [filterRisk, setFilterRisk] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState("");
  const [lastSync, setLastSync] = useState(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState("bids"); // 'bids' or 'tenders'
  const navigate = useNavigate();

  async function load() {
    try {
      const bidsData = await api.officerBids();
      setBids(bidsData);
      
      // Fetch tenders list
      try {
        const tendersData = await api.officerTenders();
        setTenders(tendersData);
      } catch (e) {
        // Tenders endpoint might not exist, that's okay
        setTenders([]);
      }
      
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
    setIsRefreshing(true);
    try {
      for (const b of bids || []) {
        await api.officerEvaluate(b.bid_id);
      }
      await load();
    } finally {
      setIsRefreshing(false);
    }
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
    if (filterRisk !== "ALL" && (b.risk_level || "UNKNOWN") !== filterRisk) return false;
    if (
      searchQuery &&
      !(b.bidder_org_name || "").toLowerCase().includes(searchQuery.toLowerCase()) &&
      !(b.bid_id || "").toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <>
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-2.5 py-0.5 rounded-full border border-accent/20">
              Procurement Officer Workspace
            </span>
            <span className="text-xs text-slate">MoPNG / CPCL Sentinel</span>
          </div>
          <h1 className="font-display text-3xl font-bold text-ink tracking-tight">
            Bid Verification & Evaluation Queue
          </h1>
          <p className="text-sm text-slate mt-1">
            Real-time compliance monitoring, risk assessment, and decision gating for GeM procurement.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/officer/tenders/create")}
            className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-xs transition-all hover:scale-[1.02] flex items-center gap-2 cursor-pointer"
          >
            <span>+ Create Tender</span>
          </button>

          <div className="text-xs text-slate font-mono flex items-center gap-2 bg-card border border-line px-3.5 py-2 rounded-xl shadow-xs">
            <span className="w-2 h-2 rounded-full bg-pass animate-pulse" />
            <span>Synced: {lastSync.toLocaleTimeString()}</span>
          </div>

          <button
            onClick={evaluateAll}
            disabled={isRefreshing}
            className="bg-accent hover:bg-accent2 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-xs transition-all hover:scale-[1.02] flex items-center gap-2 disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>{isRefreshing ? "Evaluating…" : "Re-evaluate All"}</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards — Bold visual treatment */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <div className="bg-card border border-line rounded-card p-5 shadow-xs flex items-center justify-between">
            <div>
              <div className="text-[11px] font-mono uppercase tracking-wider text-slate font-semibold">Total Queue</div>
              <div className="text-3xl font-bold text-ink font-mono mt-1">{summary.total}</div>
            </div>
            <div className="w-11 h-11 rounded-xl bg-ink/5 text-ink flex items-center justify-center">
              <FileStack className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-card border border-line rounded-card p-5 shadow-xs flex items-center justify-between">
            <div>
              <div className="text-[11px] font-mono uppercase tracking-wider text-fail font-semibold">High Risk</div>
              <div className="text-3xl font-bold text-fail font-mono mt-1">{summary.high}</div>
            </div>
            <div className="w-11 h-11 rounded-xl bg-failBg text-fail flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-card border border-line rounded-card p-5 shadow-xs flex items-center justify-between">
            <div>
              <div className="text-[11px] font-mono uppercase tracking-wider text-review font-semibold">Pending Action</div>
              <div className="text-3xl font-bold text-review font-mono mt-1">{summary.pending}</div>
            </div>
            <div className="w-11 h-11 rounded-xl bg-reviewBg text-review flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-card border border-line rounded-card p-5 shadow-xs flex items-center justify-between">
            <div>
              <div className="text-[11px] font-mono uppercase tracking-wider text-pass font-semibold">Verified</div>
              <div className="text-3xl font-bold text-pass font-mono mt-1">{summary.verified}</div>
            </div>
            <div className="w-11 h-11 rounded-xl bg-passBg text-pass flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </div>
        </div>
      )}

      {/* Tabs for Bids / Tenders */}
      <div className="flex gap-3 mb-6 border-b border-line">
        <button
          onClick={() => setActiveTab("bids")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "bids"
              ? "border-accent text-accent"
              : "border-transparent text-slate hover:text-ink"
          }`}
        >
          📋 Received Bids ({bids?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab("tenders")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "tenders"
              ? "border-accent text-accent"
              : "border-transparent text-slate hover:text-ink"
          }`}
        >
          📢 Created Tenders ({tenders?.length || 0})
        </button>
      </div>

      {/* Main Table Card */}
      {activeTab === "bids" ? (
      <div className="bg-card border border-line rounded-card overflow-hidden shadow-xs">
        {/* Table Filters Bar */}
        <div className="px-6 py-4 border-b border-line bg-canvas/40 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <Filter className="w-4 h-4 text-slate" />
            <span className="text-xs font-semibold text-slate uppercase tracking-wider">Risk Filter:</span>
            {["ALL", "HIGH", "MEDIUM", "LOW"].map((r) => (
              <button
                key={r}
                onClick={() => setFilterRisk(r)}
                className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                  filterRisk === r
                    ? "bg-ink text-white shadow-xs"
                    : "bg-white border border-line text-slate hover:text-ink hover:border-slate/40"
                }`}
              >
                {r}
              </button>
            ))}
          </div>

          <div className="relative">
            <Search className="w-4 h-4 text-slate absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search entity or Bid ID…"
              className="bg-white border border-line rounded-xl pl-9 pr-3.5 py-1.5 text-xs text-ink focus:outline-none focus:border-accent w-64 shadow-xs"
            />
          </div>
        </div>

        {!bids && !error && (
          <div className="px-6 py-16 text-center text-sm text-slate">
            <div className="inline-block animate-spin mb-2">⚡</div>
            <div>Loading live verification queue…</div>
          </div>
        )}
        {error && <div className="px-6 py-6 text-sm text-fail bg-failBg/30">{error}</div>}

        {bids && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-canvas border-b border-line text-slate uppercase font-semibold text-[11px] tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Bidder Entity</th>
                  <th className="px-6 py-3.5">Identifiers</th>
                  <th className="px-6 py-3.5">Tender Target</th>
                  <th className="px-6 py-3.5">Submission</th>
                  <th className="px-6 py-3.5">Compliance</th>
                  <th className="px-6 py-3.5">Risk Gauge</th>
                  <th className="px-6 py-3.5">Officer Verdict</th>
                  <th className="px-6 py-3.5 text-right">Review</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {filteredBids.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-slate">
                      No bids match the active filters.
                    </td>
                  </tr>
                ) : (
                  filteredBids.map((b) => {
                    // Risk left-border indicator
                    const riskBorderCls =
                      b.risk_level === "HIGH"
                        ? "border-l-4 border-l-fail"
                        : b.risk_level === "MEDIUM"
                        ? "border-l-4 border-l-review"
                        : "border-l-4 border-l-pass";

                    return (
                      <tr
                        key={b.bid_id}
                        className={`hover:bg-canvas/70 cursor-pointer transition-colors ${riskBorderCls}`}
                        onClick={() => navigate(`/officer/bids/${b.bid_id}`)}
                      >
                        <td className="px-6 py-4">
                          <div className="font-bold text-ink text-sm leading-tight">{b.bidder_org_name}</div>
                          <div className="text-[11px] font-mono text-slate mt-0.5">ID: {b.bid_id}</div>
                        </td>
                        <td className="px-6 py-4 font-mono text-[11px] text-slate">
                          <div>{b.gstin || "—"}</div>
                          {b.udyam && <div className="text-[10px] text-accent mt-0.5">{b.udyam}</div>}
                        </td>
                        <td className="px-6 py-4 text-slate max-w-[220px]">
                          <div className="truncate font-medium text-ink/80">{b.tender?.title || "—"}</div>
                          <div className="text-[10px] font-mono text-slate">{b.tender?.organization}</div>
                        </td>
                        <td className="px-6 py-4">
                          <StatusBadge status={b.status} size="xs" />
                        </td>
                        <td className="px-6 py-4">
                          <StatusBadge status={b.compliance_status} size="xs" />
                        </td>
                        <td className="px-6 py-4">
                          {b.risk_level ? (
                            <div className="flex items-center gap-2">
                              <StatusBadge status={b.risk_level} size="xs" />
                              <div className="w-10 bg-line h-1.5 rounded-full overflow-hidden shrink-0">
                                <div
                                  className={`h-full rounded-full ${
                                    b.risk_level === "HIGH"
                                      ? "bg-fail"
                                      : b.risk_level === "MEDIUM"
                                      ? "bg-review"
                                      : "bg-pass"
                                  }`}
                                  style={{ width: `${Math.min(100, b.risk_score)}%` }}
                                />
                              </div>
                              <span className="font-mono text-[11px] text-slate font-medium">
                                {b.risk_score}
                              </span>
                            </div>
                          ) : (
                            <span className="text-slate">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <StatusBadge status={b.decision} size="xs" />
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-3">
                            <button
                              onClick={() => navigate(`/officer/bids/${b.bid_id}`)}
                              className="inline-flex items-center gap-1 font-semibold text-accent hover:text-accent2 text-xs transition-colors"
                            >
                              <span>Open</span>
                              <ChevronRight className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={async () => {
                                if (window.confirm("Are you sure you want to remove this bid?")) {
                                  try {
                                    await api.removeBid(b.bid_id);
                                    await load();
                                  } catch (err) {
                                    setError(err.message);
                                  }
                                }
                              }}
                              className="text-fail hover:text-fail/80 text-xs font-semibold transition-colors"
                              title="Remove bid"
                            >
                              Remove
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
      ) : (
        /* Tenders Tab */
        <div className="bg-card border border-line rounded-card overflow-hidden shadow-xs">
          {!tenders && !error && (
            <div className="px-6 py-16 text-center text-sm text-slate">
              <div className="inline-block animate-spin mb-2">⚡</div>
              <div>Loading tenders…</div>
            </div>
          )}
          
          {tenders && tenders.length === 0 && (
            <div className="px-6 py-16 text-center">
              <div className="text-4xl mb-3">📭</div>
              <p className="text-slate font-medium">No tenders created yet</p>
              <p className="text-slate text-sm mt-1">Create your first tender to get started</p>
              <button
                onClick={() => navigate("/officer/tenders/create")}
                className="mt-4 bg-accent text-white font-semibold px-6 py-2 rounded-xl hover:bg-accent2 transition"
              >
                + Create Tender
              </button>
            </div>
          )}

          {tenders && tenders.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-canvas border-b border-line text-slate uppercase font-semibold text-[11px] tracking-wider">
                  <tr>
                    <th className="px-6 py-3.5">Tender Title</th>
                    <th className="px-6 py-3.5">ID</th>
                    <th className="px-6 py-3.5">Version</th>
                    <th className="px-6 py-3.5">Status</th>
                    <th className="px-6 py-3.5">Created</th>
                    <th className="px-6 py-3.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {tenders.map((t) => (
                    <tr key={t.id} className="hover:bg-canvas/70 cursor-pointer transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-bold text-ink text-sm">{t.title || "Untitled Tender"}</div>
                      </td>
                      <td className="px-6 py-4 font-mono text-[11px] text-slate">
                        {t.id?.substring(0, 8)}
                      </td>
                      <td className="px-6 py-4 font-mono text-[11px] text-slate">
                        {t.version_number || "1.0"}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full inline-block ${
                          t.status === "published" 
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-amber-100 text-amber-700"
                        }`}>
                          {t.status === "published" ? "Published" : "Draft"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate text-[11px]">
                        {t.created_at ? new Date(t.created_at).toLocaleDateString() : "—"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className="inline-flex items-center gap-1 font-semibold text-accent hover:text-accent2 text-xs">
                          <span>View</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </>
  );
}
