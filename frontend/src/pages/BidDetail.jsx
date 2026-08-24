import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";

export default function BidDetail() {
  const { bidId } = useParams();
  const navigate = useNavigate();
  const [bid, setBid] = useState(null);
  const [error, setError] = useState("");
  const [decisionBusy, setDecisionBusy] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [pendingDecision, setPendingDecision] = useState(null);

  async function load() {
    try {
      const data = await api.officerBidDetail(bidId);
      setBid(data);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bidId]);

  async function submitDecision(decision) {
    const diverges = decision !== bid.ai_recommendation;
    if (diverges && !overrideReason && pendingDecision !== decision) {
      setPendingDecision(decision);
      return; // show reason box first
    }
    setDecisionBusy(true);
    try {
      await api.officerDecide(bidId, decision, diverges ? overrideReason : undefined);
      setPendingDecision(null);
      setOverrideReason("");
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setDecisionBusy(false);
    }
  }

  if (error) return <Shell><div className="text-fail text-sm">{error}</div></Shell>;
  if (!bid) return <Shell><div className="text-sm text-slate">Loading…</div></Shell>;

  return (
    <Shell>
      <button onClick={() => navigate("/officer")} className="text-xs text-slate hover:text-ink mb-4 inline-flex items-center gap-1">
        ← Back to dashboard
      </button>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">{bid.bidder_org_name}</h1>
          <div className="flex items-center gap-2 mt-2">
            <StatusBadge status={bid.compliance_status} />
            <StatusBadge status={bid.risk_assessment.risk_level} />
            <span className="text-xs text-slate">risk score {bid.risk_assessment.total_score} · {bid.risk_assessment.policy_version}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-3">
          <div className="text-sm font-medium text-ink mb-2">Clause-by-clause compliance</div>
          {bid.compliance_results.map((c) => (
            <div key={c.clause_id} className="bg-card border border-line rounded-card px-4 py-3.5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="text-sm text-ink">{c.clause_text}</div>
                  <div className="text-xs text-slate mt-1">{c.mandatory ? "Mandatory" : "Optional"}</div>
                </div>
                <StatusBadge status={c.status} />
              </div>
              <details className="mt-2">
                <summary className="text-xs text-accent cursor-pointer select-none">View reasoning & evidence</summary>
                <div className="mt-2 pl-3 border-l-2 border-line space-y-1">
                  {c.reasoning_chain.map((r, i) => (
                    <div key={i} className="text-xs text-slate">{r}</div>
                  ))}
                  {c.evidence_refs.length > 0 && (
                    <div className="text-xs text-accent2 mt-1.5">
                      Evidence: {c.evidence_refs.join(", ")}
                    </div>
                  )}
                </div>
              </details>
            </div>
          ))}
        </div>

        <div className="space-y-4">
          <div className="bg-card border border-line rounded-card px-4 py-4">
            <div className="text-sm font-medium text-ink mb-3">Risk signals</div>
            {bid.risk_assessment.signals.length === 0 && (
              <div className="text-xs text-slate">No risk signals detected.</div>
            )}
            <div className="space-y-2">
              {bid.risk_assessment.signals.map((s, i) => (
                <div key={i} className="text-xs">
                  <div className="font-medium text-ink">{s.signal_type.replaceAll("_", " ")}</div>
                  <div className="text-slate">weight {s.weight} × severity {s.severity} = {s.contribution}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-card border border-line rounded-card px-4 py-4">
            <div className="text-sm font-medium text-ink mb-1">AI recommendation</div>
            <div className="text-xs text-slate mb-3">Advisory only — officer retains final authority.</div>
            <StatusBadge status={bid.ai_recommendation} />

            <div className="mt-4 pt-4 border-t border-line space-y-2">
              {bid.decision ? (
                <div className="text-xs text-slate">
                  Decided: <StatusBadge status={bid.decision.final_decision} />
                  {bid.decision.override_reason && (
                    <div className="mt-1.5 text-ink">Reason: {bid.decision.override_reason}</div>
                  )}
                </div>
              ) : (
                <>
                  {pendingDecision && (
                    <div className="mb-2">
                      <label className="block text-xs text-slate mb-1">
                        Override reason required (diverges from AI recommendation)
                      </label>
                      <textarea
                        value={overrideReason}
                        onChange={(e) => setOverrideReason(e.target.value)}
                        rows={2}
                        className="w-full text-xs border border-line rounded-lg px-2.5 py-2 focus:outline-none focus:ring-2 focus:ring-accent/30"
                        placeholder="Explain why you're overriding…"
                      />
                    </div>
                  )}
                  <button
                    disabled={decisionBusy}
                    onClick={() => submitDecision("VERIFIED")}
                    className="w-full text-xs font-medium bg-pass/10 text-pass hover:bg-pass/20 rounded-lg py-2 transition-colors"
                  >
                    Mark verified
                  </button>
                  <button
                    disabled={decisionBusy}
                    onClick={() => submitDecision("NEEDS_CLARIFICATION")}
                    className="w-full text-xs font-medium bg-review/10 text-review hover:bg-review/20 rounded-lg py-2 transition-colors"
                  >
                    Request clarification
                  </button>
                  <button
                    disabled={decisionBusy}
                    onClick={() => submitDecision("NON_COMPLIANT")}
                    className="w-full text-xs font-medium bg-fail/10 text-fail hover:bg-fail/20 rounded-lg py-2 transition-colors"
                  >
                    Mark non-compliant
                  </button>
                  {pendingDecision && (
                    <button
                      onClick={() => submitDecision(pendingDecision)}
                      disabled={!overrideReason || decisionBusy}
                      className="w-full text-xs font-medium bg-accent text-white hover:bg-accent2 rounded-lg py-2 transition-colors disabled:opacity-50"
                    >
                      Confirm with reason
                    </button>
                  )}
                </>
              )}
            </div>
          </div>

          <div className="bg-card border border-line rounded-card px-4 py-4">
            <div className="text-sm font-medium text-ink mb-2">Documents</div>
            <div className="space-y-1.5">
              {bid.documents.map((d) => (
                <div key={d.id} className="text-xs flex justify-between">
                  <span className="text-ink">{d.doc_type.replaceAll("_", " ")}</span>
                  <span className="text-slate">{d.ocr_status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
