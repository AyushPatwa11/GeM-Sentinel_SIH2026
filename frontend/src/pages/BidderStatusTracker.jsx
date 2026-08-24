import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";

export default function BidderStatusTracker() {
  const { bidId } = useParams();
  const navigate = useNavigate();
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(new Date());

  async function fetchStatus() {
    try {
      const res = await api.bidderBidStatus(bidId);
      setStatusData(res);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message || "Failed to fetch bid status");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchStatus();
    // Live polling every 3 seconds for immediate real-time sync with officer decisions
    const timer = setInterval(fetchStatus, 3000);
    return () => clearInterval(timer);
  }, [bidId]);

  if (loading) {
    return (
      <Shell>
        <div className="py-12 text-center text-sm text-slate">Loading real-time bid status…</div>
      </Shell>
    );
  }

  if (error || !statusData) {
    return (
      <Shell>
        <div className="bg-failBg text-fail border border-fail/20 p-4 rounded-lg text-sm">
          {error || "Bid not found"}
        </div>
      </Shell>
    );
  }

  const steps = [
    { num: 1, label: "Bid Draft Initialized", done: true },
    { num: 2, label: "Documents Verified & Hashed", done: statusData.current_step >= 2 },
    { num: 3, label: "Submitted & In Review", done: statusData.current_step >= 3 },
    { num: 4, label: "Officer Decision Recorded", done: statusData.current_step >= 4 },
  ];

  return (
    <Shell>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <button
            onClick={() => navigate("/bidder")}
            className="text-xs text-slate hover:text-ink mb-1 inline-flex items-center gap-1 font-medium"
          >
            ← Back to Tenders
          </button>
          <h1 className="font-display text-2xl font-bold text-ink">Live Bid Status Tracker</h1>
          <p className="text-xs text-slate mt-0.5">
            Bidding Entity: <span className="font-semibold text-ink">{statusData.bidder_org_name}</span> · Bid ID: <span className="font-mono text-ink">{bidId}</span>
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate bg-card border border-line px-3 py-1.5 rounded-lg">
          <span className="w-2 h-2 rounded-full bg-pass animate-pulse" />
          Live sync active · Last check: {lastUpdated.toLocaleTimeString()}
        </div>
      </div>

      {/* Main Status Hero Card */}
      <div className="bg-card border border-line rounded-card p-6 mb-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
          <div>
            <div className="text-xs text-slate uppercase font-semibold tracking-wider">Current Status</div>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xl font-bold text-ink">{statusData.status}</span>
              <StatusBadge status={statusData.status} />
              {statusData.decision && (
                <span className="text-xs font-semibold bg-accent/10 text-accent px-2.5 py-1 rounded-full">
                  Decision: {statusData.decision.final_decision}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="text-right">
              <div className="text-slate">AI Compliance State</div>
              <div className="mt-0.5"><StatusBadge status={statusData.compliance_status} /></div>
            </div>
            {statusData.risk_level && (
              <div className="text-right">
                <div className="text-slate">Risk Level</div>
                <div className="mt-0.5"><StatusBadge status={statusData.risk_level} /></div>
              </div>
            )}
          </div>
        </div>

        {/* Stepper Progression */}
        <div className="relative flex items-center justify-between">
          <div className="absolute top-1/2 left-0 right-0 h-1 bg-line -translate-y-1/2 z-0" />
          {steps.map((st) => (
            <div key={st.num} className="relative z-10 flex flex-col items-center bg-card px-2">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs shadow-xs transition-all ${
                  st.done
                    ? "bg-pass text-white ring-4 ring-passBg"
                    : "bg-canvas border-2 border-line text-slate"
                }`}
              >
                {st.done ? "✓" : st.num}
              </div>
              <span className={`text-xs mt-2 font-medium ${st.done ? "text-ink" : "text-slate"}`}>
                {st.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Officer Decision & Inspection Findings */}
        <div className="lg:col-span-2 space-y-6">
          {/* Officer Decision Box */}
          <div className="bg-card border border-line rounded-card p-5">
            <h2 className="text-sm font-bold text-ink mb-3">Procurement Officer Final Decision</h2>
            {statusData.decision ? (
              <div className="p-4 rounded-xl bg-canvas border border-line space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate">Recorded Decision:</span>
                    <StatusBadge status={statusData.decision.final_decision} />
                  </div>
                  <span className="text-xs text-slate">
                    Decided: {new Date(statusData.decision.decided_at).toLocaleString()}
                  </span>
                </div>
                <div className="text-xs text-ink">
                  Officer: <span className="font-semibold">{statusData.decision.decided_by || "Procurement Officer"}</span>
                </div>
                {statusData.decision.override_reason && (
                  <div className="p-3 bg-white border border-line rounded-lg text-xs">
                    <span className="font-semibold text-review">Officer Override Rationale:</span>
                    <p className="text-slate mt-1">{statusData.decision.override_reason}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate bg-canvas/40 rounded-xl border border-dashed border-line">
                ⏳ Your bid is queued and currently under active review by the CPCL Procurement Officer. Decisions and clarification requests will appear here live.
              </div>
            )}
          </div>

          {/* Officer Notes / Inspection Logs */}
          <div className="bg-card border border-line rounded-card p-5">
            <h2 className="text-sm font-bold text-ink mb-3">Officer Inspection Logs & Comments</h2>
            {statusData.officer_notes?.length > 0 ? (
              <div className="space-y-2.5">
                {statusData.officer_notes.map((note) => (
                  <div key={note.id} className="p-3 bg-canvas border border-line rounded-lg text-xs">
                    <div className="flex items-center justify-between text-[11px] text-slate mb-1">
                      <span className="font-semibold text-ink">{note.author}</span>
                      <span>{new Date(note.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-ink">{note.note}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate">No public inspection notes attached yet.</p>
            )}
          </div>
        </div>

        {/* Right Col: Document Flag Alerts & Tender Info */}
        <div className="space-y-6">
          {/* Document Flags / Clarifications */}
          <div className="bg-card border border-line rounded-card p-5">
            <h2 className="text-sm font-bold text-ink mb-3">Clarification Requests</h2>
            {statusData.document_flags?.length > 0 ? (
              <div className="space-y-2.5">
                {statusData.document_flags.map((flag) => (
                  <div key={flag.id} className="p-3 bg-failBg/50 border border-fail/30 rounded-lg text-xs">
                    <div className="font-bold text-fail flex items-center gap-1 mb-1">
                      <span>⚠ Action Required</span>
                    </div>
                    <p className="text-ink font-medium">{flag.reason}</p>
                    <p className="text-[11px] text-slate mt-1">{flag.action_required}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-pass font-medium">✓ No clarification flags raised against your documents.</p>
            )}
          </div>

          {/* Tender Info summary */}
          <div className="bg-card border border-line rounded-card p-5 text-xs space-y-2.5">
            <h2 className="font-bold text-ink mb-1">Tender Summary</h2>
            <div className="text-slate">Title: <span className="text-ink font-medium">{statusData.tender?.title}</span></div>
            <div className="text-slate">Authority: <span className="text-ink font-medium">{statusData.tender?.organization}</span></div>
            <div className="text-slate">Version: <span className="font-mono text-ink">{statusData.tender?.version}</span></div>
            {statusData.submitted_at && (
              <div className="text-slate">Submitted: <span className="text-ink">{new Date(statusData.submitted_at).toLocaleString()}</span></div>
            )}
          </div>
        </div>
      </div>
    </Shell>
  );
}
