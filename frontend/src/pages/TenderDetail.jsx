import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";

export default function TenderDetail() {
  const { tenderId } = useParams();
  const navigate = useNavigate();
  const [tender, setTender] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [startingBid, setStartingBid] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.tenderDetail(tenderId);
        setTender(data);
      } catch (err) {
        setError(err.message || "Failed to load tender details");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [tenderId]);

  async function handleApply() {
    setStartingBid(true);
    try {
      const res = await api.bidderCreateBid(tenderId);
      navigate(`/bidder/apply/${res.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setStartingBid(false);
    }
  }

  if (loading) {
    return (
      <Shell>
        <div className="py-12 text-center text-sm text-slate">Loading tender details…</div>
      </Shell>
    );
  }

  if (error || !tender) {
    return (
      <Shell>
        <div className="bg-failBg text-fail border border-fail/20 p-4 rounded-lg text-sm">
          {error || "Tender not found"}
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <button
        onClick={() => navigate("/bidder")}
        className="text-xs text-slate hover:text-ink mb-4 inline-flex items-center gap-1 font-medium transition-colors"
      >
        ← Back to published tenders
      </button>

      <div className="bg-card border border-line rounded-card p-6 mb-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-2.5 py-0.5 rounded-full">
                {tender.organization}
              </span>
              <span className="text-xs text-slate">Version {tender.version}</span>
            </div>
            <h1 className="font-display text-2xl font-bold text-ink">{tender.title}</h1>
            <p className="text-sm text-slate mt-1">
              Tender ID: <span className="font-mono text-ink font-medium">{tender.id}</span> · Status: Published
            </p>
          </div>
          <button
            onClick={handleApply}
            disabled={startingBid}
            className="bg-accent hover:bg-accent2 text-white font-medium text-sm px-6 py-3 rounded-lg shadow-sm transition-all transform active:scale-95 disabled:opacity-50"
          >
            {startingBid ? "Creating Workspace…" : "Apply / Prepare Bid Submission →"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Eligibility Requirements */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card border border-line rounded-card p-5">
            <h2 className="text-base font-semibold text-ink mb-1">Tender Eligibility Requirements</h2>
            <p className="text-xs text-slate mb-4">
              Deterministic rule engine clauses evaluated for this tender. All mandatory clauses must be satisfied.
            </p>

            <div className="space-y-3">
              {tender.clauses?.map((c, idx) => (
                <div key={c.clause_id} className="p-3.5 border border-line/60 rounded-lg bg-canvas/40 flex items-start gap-3">
                  <div className="h-6 w-6 rounded-full bg-accent/10 text-accent font-mono text-xs flex items-center justify-center font-bold shrink-0 mt-0.5">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-ink">{c.raw_text}</div>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-slate">
                      <span className="bg-white border border-line px-2 py-0.5 rounded font-mono text-[11px]">
                        {c.category}
                      </span>
                      {c.mandatory ? (
                        <span className="text-fail font-medium">Mandatory Hard Gate</span>
                      ) : (
                        <span className="text-slate">Conditional / Optional</span>
                      )}
                      {c.ambiguity_flag && (
                        <span className="text-review font-medium">⚠ Ambiguity Flagged</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Required Documents Checklist */}
        <div className="space-y-6">
          <div className="bg-card border border-line rounded-card p-5">
            <h2 className="text-base font-semibold text-ink mb-1">Required Document Slots</h2>
            <p className="text-xs text-slate mb-4">
              You will need to upload verifiable documents for the following slots:
            </p>

            <div className="space-y-2.5">
              {tender.required_documents?.map((d) => (
                <div key={d.doc_type} className="p-3 border border-line rounded-lg bg-canvas/30">
                  <div className="flex items-center justify-between">
                    <div className="text-xs font-semibold text-ink">{d.title}</div>
                    {d.mandatory ? (
                      <span className="text-[10px] uppercase font-bold text-fail bg-failBg px-1.5 py-0.5 rounded">
                        Mandatory
                      </span>
                    ) : (
                      <span className="text-[10px] uppercase font-bold text-slate bg-canvas px-1.5 py-0.5 rounded">
                        Exemption
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate mt-1 leading-snug">{d.description}</p>
                </div>
              ))}
            </div>

            <div className="mt-5 pt-4 border-t border-line">
              <button
                onClick={handleApply}
                disabled={startingBid}
                className="w-full bg-accent hover:bg-accent2 text-white font-medium text-sm py-2.5 rounded-lg shadow-sm transition-colors text-center block"
              >
                Proceed to Document Upload →
              </button>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
