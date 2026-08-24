import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";

const ADAPTER_SOURCES = [
  { key: "GSTN", label: "GSTN Registry Lookup", desc: "Cross-check legal entity name and return filing status" },
  { key: "MCA", label: "MCA21 Master Data", desc: "Query Ministry of Corporate Affairs for CIN & incorporation status" },
  { key: "UDYAM", label: "Udyam / MSME Portal", desc: "Validate enterprise category (Micro/Small/Medium)" },
  { key: "BLACKLIST", label: "Debarment & Blacklist Registry", desc: "Check CPSE / Ministry debarment lists" },
  { key: "DIGILOCKER", label: "DigiLocker Verification", desc: "Verify cryptographic document hash and issuer stamp" },
  { key: "NSIC", label: "NSIC Registration", desc: "Verify single-point registration for government purchases" },
];

export default function BidDetail() {
  const { bidId } = useParams();
  const navigate = useNavigate();
  const [bid, setBid] = useState(null);
  const [error, setError] = useState("");
  const [decisionBusy, setDecisionBusy] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [pendingDecision, setPendingDecision] = useState(null);

  // Additional Verification Action State
  const [selectedAdapter, setSelectedAdapter] = useState("GSTN");
  const [runningVerification, setRunningVerification] = useState(false);
  const [verificationFeedback, setVerificationFeedback] = useState(null);

  // Notes & Flags State
  const [newNote, setNewNote] = useState("");
  const [noteCategory, setNoteCategory] = useState("GENERAL");
  const [savingNote, setSavingNote] = useState(false);

  const [flagDocId, setFlagDocId] = useState("");
  const [flagReason, setFlagReason] = useState("");
  const [flagAction, setFlagAction] = useState("Provide updated clearance certificate");
  const [savingFlag, setSavingFlag] = useState(false);

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
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
  }, [bidId]);

  async function handleTriggerVerification() {
    setRunningVerification(true);
    setVerificationFeedback(null);
    try {
      const res = await api.officerTriggerVerification(bidId, selectedAdapter);
      setVerificationFeedback(res);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setRunningVerification(false);
    }
  }

  async function handleAddNote(e) {
    e.preventDefault();
    if (!newNote.trim()) return;
    setSavingNote(true);
    try {
      await api.officerAddNote(bidId, newNote, noteCategory);
      setNewNote("");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingNote(false);
    }
  }

  async function handleFlagDocument(e) {
    e.preventDefault();
    if (!flagDocId || !flagReason.trim()) return;
    setSavingFlag(true);
    try {
      await api.officerFlagDocument(bidId, flagDocId, flagReason, flagAction);
      setFlagReason("");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingFlag(false);
    }
  }

  async function submitDecision(decision) {
    const diverges = decision !== bid.ai_recommendation;
    if (diverges && !overrideReason.trim() && pendingDecision !== decision) {
      setPendingDecision(decision);
      return;
    }
    setDecisionBusy(true);
    try {
      await api.officerDecide(bidId, decision, diverges ? overrideReason : undefined);
      setPendingDecision(null);
      setOverrideReason("");
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setDecisionBusy(false);
    }
  }

  if (error) return <Shell><div className="text-fail text-sm p-4 bg-failBg rounded-lg">{error}</div></Shell>;
  if (!bid) return <Shell><div className="text-sm text-slate py-12 text-center">Loading bid evaluation…</div></Shell>;

  return (
    <Shell>
      <button
        onClick={() => navigate("/officer")}
        className="text-xs text-slate hover:text-ink mb-4 inline-flex items-center gap-1 font-medium"
      >
        ← Back to Officer Queue
      </button>

      {/* Header Banner */}
      <div className="bg-card border border-line rounded-card p-6 mb-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-2.5 py-0.5 rounded-full">
                {bid.tender?.organization || "CPCL"}
              </span>
              <span className="text-xs font-mono text-slate">Bid: {bidId}</span>
            </div>
            <h1 className="font-display text-2xl font-bold text-ink">{bid.bidder_org_name}</h1>
            <p className="text-xs text-slate mt-1">
              Tender: <span className="text-ink font-medium">{bid.tender?.title}</span> (v{bid.tender?.version})
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="text-right">
              <div className="text-[11px] text-slate font-medium">Compliance Gating</div>
              <div className="mt-0.5"><StatusBadge status={bid.compliance_status} /></div>
            </div>
            <div className="text-right">
              <div className="text-[11px] text-slate font-medium">AI Risk Level</div>
              <div className="mt-0.5"><StatusBadge status={bid.risk_assessment.risk_level} /></div>
            </div>
            <div className="text-right">
              <div className="text-[11px] text-slate font-medium">Current Decision</div>
              <div className="mt-0.5"><StatusBadge status={bid.decision?.final_decision || "PENDING"} /></div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Clause-by-clause Compliance & Risk Signals */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI Recommendation Banner */}
          <div className="bg-card border border-accent/30 rounded-card p-4 shadow-xs bg-gradient-to-r from-accent/5 to-transparent">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-accent uppercase tracking-wider">Explainable AI Recommendation</span>
                <div className="text-lg font-bold text-ink mt-0.5">
                  Recommended Action: <span className="text-accent">{bid.ai_recommendation}</span>
                </div>
              </div>
              <span className="text-xs font-mono text-slate">
                Risk Score: {bid.risk_assessment.total_score} ({bid.risk_assessment.policy_version})
              </span>
            </div>
            <p className="text-xs text-slate mt-2 leading-relaxed">
              Based on deterministic evaluation of tender logic trees, MSME exemptions, and live cross-source adapter verification. The procurement officer retains final decision authority.
            </p>
          </div>

          {/* Clause Compliance Table */}
          <div className="bg-card border border-line rounded-card p-5 shadow-xs">
            <h2 className="text-sm font-bold text-ink mb-1">Deterministic Clause-by-Clause Compliance</h2>
            <p className="text-xs text-slate mb-4">
              Evaluated strictly by pure logic engine without LLM intervention. Every result links to document spans.
            </p>

            <div className="space-y-3">
              {bid.compliance_results.map((c) => (
                <div key={c.clause_id} className="p-4 border border-line rounded-xl bg-canvas/40">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="text-xs font-semibold text-ink">{c.clause_text}</div>
                      <div className="flex items-center gap-2 mt-1 text-[11px] text-slate">
                        <span className="font-mono">{c.clause_id}</span>
                        <span>·</span>
                        <span className={c.mandatory ? "text-fail font-semibold" : "text-slate"}>
                          {c.mandatory ? "Mandatory Hard-Gate" : "Optional / Conditional"}
                        </span>
                      </div>
                    </div>
                    <StatusBadge status={c.status} />
                  </div>

                  {c.reasoning_chain && c.reasoning_chain.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-line/60">
                      <div className="text-[11px] font-semibold text-slate mb-1">Logic Engine Reasoning Chain:</div>
                      <div className="space-y-1 text-xs text-slate pl-2.5 border-l-2 border-accent/40">
                        {c.reasoning_chain.map((r, i) => (
                          <div key={i}>{r}</div>
                        ))}
                      </div>
                    </div>
                  )}

                  {c.evidence_refs && c.evidence_refs.length > 0 && (
                    <div className="mt-2 text-[11px] text-accent font-mono bg-accent/5 p-1.5 rounded">
                      Linked Evidence Spans: {c.evidence_refs.join(", ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Extensible Additional Verification Action Framework */}
          <div className="bg-card border border-line rounded-card p-5 shadow-xs">
            <h2 className="text-sm font-bold text-ink mb-1">⚡ On-Demand Extensible Verification Actions</h2>
            <p className="text-xs text-slate mb-4">
              Execute live on-demand queries against authoritative government registries to confirm claims or investigate flags.
            </p>

            <div className="flex flex-wrap items-center gap-3 mb-4">
              <select
                value={selectedAdapter}
                onChange={(e) => setSelectedAdapter(e.target.value)}
                className="bg-canvas border border-line rounded-lg px-3 py-2 text-xs font-semibold text-ink focus:outline-none focus:border-accent"
              >
                {ADAPTER_SOURCES.map((a) => (
                  <option key={a.key} value={a.key}>
                    {a.label} ({a.key})
                  </option>
                ))}
              </select>

              <button
                onClick={handleTriggerVerification}
                disabled={runningVerification}
                className="bg-accent hover:bg-accent2 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-xs transition-colors disabled:opacity-50"
              >
                {runningVerification ? "Querying Registry…" : "Trigger Verification Check →"}
              </button>
            </div>

            {verificationFeedback && (
              <div className="p-3.5 bg-passBg/40 border border-pass/30 rounded-lg text-xs mb-4">
                <div className="flex items-center justify-between font-bold">
                  <span className="text-pass">Source: {verificationFeedback.source}</span>
                  <StatusBadge status={verificationFeedback.status} />
                </div>
                <div className="text-ink mt-1 font-medium">{verificationFeedback.evidence}</div>
                {verificationFeedback.data && (
                  <pre className="mt-2 text-[10px] bg-white p-2 rounded border border-line font-mono text-slate overflow-x-auto">
                    {JSON.stringify(verificationFeedback.data, null, 2)}
                  </pre>
                )}
              </div>
            )}

            {bid.custom_verifications?.length > 0 && (
              <div className="space-y-2 mt-3">
                <div className="text-xs font-semibold text-ink">Recorded Verification Checks:</div>
                {bid.custom_verifications.map((v) => (
                  <div key={v.id} className="p-2.5 bg-canvas border border-line rounded-lg text-xs flex items-center justify-between">
                    <div>
                      <span className="font-bold text-ink">{v.source}</span>: <span className="text-slate">{v.evidence}</span>
                    </div>
                    <StatusBadge status={v.status} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Risk Signals, Officer Notes, Document Flags & Decision */}
        <div className="space-y-6">
          {/* Risk Signal Breakdown Card */}
          <div className="bg-card border border-line rounded-card p-5 shadow-xs">
            <h2 className="text-sm font-bold text-ink mb-1">AI Risk Signals Breakdown</h2>
            <div className="flex items-center justify-between my-3 p-2.5 bg-canvas rounded-lg text-xs">
              <span className="text-slate">Total Calculated Risk:</span>
              <div className="flex items-center gap-1.5">
                <StatusBadge status={bid.risk_assessment.risk_level} />
                <span className="font-bold font-mono text-ink">{bid.risk_assessment.total_score}</span>
              </div>
            </div>

            {bid.risk_assessment.signals?.length > 0 ? (
              <div className="space-y-2">
                {bid.risk_assessment.signals.map((sig, i) => (
                  <div key={i} className="p-2.5 bg-failBg/20 border border-fail/20 rounded-lg text-xs">
                    <div className="flex justify-between font-bold text-ink">
                      <span>{sig.signal_type}</span>
                      <span className="text-fail font-mono">+{sig.contribution}</span>
                    </div>
                    <div className="text-[11px] text-slate mt-1 font-mono">{sig.evidence_ref}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-pass font-medium p-3 bg-passBg rounded-lg text-center">
                ✓ No adverse risk signals detected
              </div>
            )}
          </div>

          {/* Officer Decision Panel (Gating) */}
          <div className="bg-card border-2 border-accent/40 rounded-card p-5 shadow-sm">
            <h2 className="text-sm font-bold text-ink mb-1">Procurement Officer Final Decision</h2>
            <p className="text-xs text-slate mb-4">
              AI recommendations assist the officer; human officers retain statutory decision authority.
            </p>

            {pendingDecision && pendingDecision !== bid.ai_recommendation && (
              <div className="mb-4 p-3 bg-reviewBg/40 border border-review/30 rounded-lg text-xs">
                <span className="font-bold text-review">Mandatory Override Reason Required:</span>
                <p className="text-slate text-[11px] mt-0.5">
                  Your decision ({pendingDecision}) diverges from the AI recommendation ({bid.ai_recommendation}). Please document statutory justification for the immutable audit trail.
                </p>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="State reason for overriding AI recommendation…"
                  className="w-full mt-2 bg-white border border-line rounded-lg p-2 text-xs text-ink focus:outline-none focus:border-accent"
                  rows={2}
                />
              </div>
            )}

            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => submitDecision("VERIFIED")}
                disabled={decisionBusy}
                className="bg-pass hover:bg-pass/90 text-white font-semibold text-xs py-2.5 px-2 rounded-lg shadow-xs transition-colors text-center disabled:opacity-50"
              >
                Mark Verified
              </button>
              <button
                onClick={() => submitDecision("NEEDS_CLARIFICATION")}
                disabled={decisionBusy}
                className="bg-review hover:bg-review/90 text-white font-semibold text-xs py-2.5 px-2 rounded-lg shadow-xs transition-colors text-center disabled:opacity-50"
              >
                Request Info
              </button>
              <button
                onClick={() => submitDecision("NON_COMPLIANT")}
                disabled={decisionBusy}
                className="bg-fail hover:bg-fail/90 text-white font-semibold text-xs py-2.5 px-2 rounded-lg shadow-xs transition-colors text-center disabled:opacity-50"
              >
                Non-Compliant
              </button>
            </div>
          </div>

          {/* Add Inspection Notes */}
          <div className="bg-card border border-line rounded-card p-5 shadow-xs">
            <h2 className="text-sm font-bold text-ink mb-2">Inspection Notes & Findings</h2>
            <form onSubmit={handleAddNote} className="space-y-2 mb-3">
              <textarea
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Add inspection remark or observation…"
                className="w-full bg-canvas border border-line rounded-lg p-2.5 text-xs text-ink focus:outline-none focus:border-accent"
                rows={2}
              />
              <div className="flex justify-between items-center">
                <select
                  value={noteCategory}
                  onChange={(e) => setNoteCategory(e.target.value)}
                  className="bg-white border border-line rounded px-2 py-1 text-[11px] text-ink"
                >
                  <option value="GENERAL">General</option>
                  <option value="COMPLIANCE">Compliance</option>
                  <option value="RISK">Risk Signal</option>
                </select>
                <button
                  type="submit"
                  disabled={savingNote || !newNote.trim()}
                  className="bg-accent text-white text-xs font-semibold px-3 py-1.5 rounded-lg disabled:opacity-50"
                >
                  {savingNote ? "Saving…" : "Add Note"}
                </button>
              </div>
            </form>

            <div className="space-y-2 max-h-48 overflow-y-auto">
              {bid.notes?.map((n) => (
                <div key={n.id} className="p-2 bg-canvas rounded border border-line text-xs">
                  <div className="flex justify-between text-[10px] text-slate mb-0.5">
                    <span className="font-semibold text-ink">{n.category}</span>
                    <span>{new Date(n.created_at).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-ink">{n.note}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
