import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";
import {
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  ChevronDown,
  ChevronUp,
  FileCheck,
  Search,
  MessageSquare,
  Lock,
  ExternalLink,
  Info,
  HelpCircle,
} from "lucide-react";

const ADAPTER_SOURCES = [
  { key: "GSTN", label: "GSTN Registry Lookup", desc: "Cross-check legal entity name and return filing status" },
  { key: "MCA", label: "MCA21 Master Data", desc: "Query Ministry of Corporate Affairs for CIN & incorporation status" },
  { key: "UDYAM", label: "Udyam / MSME Portal", desc: "Validate enterprise category (Micro/Small/Medium)" },
  { key: "BLACKLIST", label: "Debarment & Blacklist Registry", desc: "Check CPSE / Ministry debarment lists" },
  { key: "DIGILOCKER", label: "DigiLocker Verification", desc: "Verify cryptographic document hash and issuer stamp" },
  { key: "NSIC", label: "NSIC Registration", desc: "Verify single-point registration for government purchases" },
];

/* Minimal SVG Radial Gauge Component */
function RiskGauge({ score = 0, level = "LOW" }) {
  const radius = 38;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;

  const color = level === "HIGH" ? "#C23B3B" : level === "MEDIUM" ? "#B7791F" : "#1B8A5A";
  const bgTrack = level === "HIGH" ? "#FBEAEA" : level === "MEDIUM" ? "#FDF3E1" : "#E8F6EF";

  return (
    <div className="flex items-center gap-4">
      <div className="relative flex items-center justify-center shrink-0">
        <svg height={radius * 2} width={radius * 2} className="rotate-[-90deg]">
          <circle
            stroke={bgTrack}
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          <circle
            stroke={color}
            fill="transparent"
            strokeWidth={stroke}
            strokeDasharray={`${circumference} ${circumference}`}
            style={{ strokeDashoffset, transition: "stroke-dashoffset 0.6s ease" }}
            strokeLinecap="round"
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className="font-mono text-base font-bold text-ink leading-none">{score}</span>
        </div>
      </div>
      <div>
        <div className="text-[10px] font-mono uppercase tracking-wider text-slate font-semibold">Risk Score</div>
        <div className="font-display font-bold text-sm text-ink">{level} RISK</div>
      </div>
    </div>
  );
}

export default function BidDetail() {
  const { bidId } = useParams();
  const navigate = useNavigate();
  const [bid, setBid] = useState(null);
  const [error, setError] = useState("");
  const [decisionBusy, setDecisionBusy] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [pendingDecision, setPendingDecision] = useState(null);
  const [expandedReasoning, setExpandedReasoning] = useState({});

  // Additional Verification Action State
  const [selectedAdapter, setSelectedAdapter] = useState("GSTN");
  const [runningVerification, setRunningVerification] = useState(false);
  const [verificationFeedback, setVerificationFeedback] = useState(null);

  // Notes State
  const [newNote, setNewNote] = useState("");
  const [noteCategory, setNoteCategory] = useState("GENERAL");
  const [savingNote, setSavingNote] = useState(false);

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

  function toggleReasoning(clauseId) {
    setExpandedReasoning((prev) => ({ ...prev, [clauseId]: !prev[clauseId] }));
  }

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

  async function submitDecision(decision) {
    const diverges = decision !== (bid?.ai_recommendation || "REVIEW");
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

  if (error) {
    return (
      <Shell>
        <div className="text-fail text-sm p-4 bg-failBg rounded-xl border border-fail/20 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      </Shell>
    );
  }

  if (!bid) {
    return (
      <Shell>
        <div className="text-sm text-slate py-20 text-center">
          <div className="inline-block animate-spin mb-2">⚡</div>
          <div>Loading bid verification records…</div>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      {/* Back button */}
      <button
        onClick={() => navigate("/officer")}
        className="text-xs text-slate hover:text-ink mb-5 inline-flex items-center gap-1.5 font-semibold transition-colors cursor-pointer"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Officer Queue</span>
      </button>

      {/* Header Banner */}
      <div className="bg-card border border-line rounded-card p-6 mb-8 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-2.5 py-0.5 rounded-full border border-accent/20">
                {bid.tender?.organization || "CPCL"}
              </span>
              <span className="text-xs font-mono text-slate">Bid ID: {bidId}</span>
            </div>
            <h1 className="font-display text-2xl sm:text-3xl font-bold text-ink tracking-tight">
              {bid.bidder_org_name}
            </h1>
            <p className="text-xs sm:text-sm text-slate mt-1">
              Target Tender: <span className="text-ink font-semibold">{bid.tender?.title}</span> (v{bid.tender?.version})
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-6 pt-2 sm:pt-0">
            {/* Radial Risk Gauge */}
            <RiskGauge
              score={bid.risk_assessment?.total_score || 0}
              level={bid.risk_assessment?.risk_level || "UNKNOWN"}
            />

            <div className="h-10 w-[1px] bg-line hidden sm:block" />

            <div className="space-y-1 text-right">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate font-semibold">Compliance</div>
              <div><StatusBadge status={bid.compliance_status || "PENDING"} /></div>
            </div>

            <div className="space-y-1 text-right">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate font-semibold">Decision</div>
              <div><StatusBadge status={bid.decision?.final_decision || "PENDING"} /></div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Clause-by-Clause Evaluation & Extensible Verifications */}
        <div className="lg:col-span-8 space-y-6">
          {/* AI Recommendation Banner */}
          <div className="bg-gradient-to-r from-accent/10 via-card to-card border border-accent/30 rounded-card p-5 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <div className="inline-flex items-center gap-1.5 text-xs font-bold text-accent uppercase tracking-wider">
                <Sparkles className="w-4 h-4" />
                <span>Explainable AI Recommendation</span>
              </div>
              <span className="text-xs font-mono text-slate">
                Policy: {bid.risk_assessment?.policy_version || "v1.0"}
              </span>
            </div>

            <div className="text-xl font-display font-bold text-ink">
              Recommended Verdict: <span className="text-accent">{bid.ai_recommendation || "REVIEW"}</span>
            </div>

            <p className="text-xs text-slate mt-2 leading-relaxed">
              Synthesized through deterministic evaluation of tender logic trees, statutory MSME waivers, and live registry checks. The procurement officer retains final statutory authority.
            </p>
          </div>

          {/* Documents Section */}
          <div className="bg-card border border-line rounded-card p-6 shadow-xs">
            <h2 className="text-base font-bold text-ink mb-1">Submitted Documents</h2>
            <p className="text-xs text-slate mb-4">
              All documents submitted by the bidder with verification status
            </p>

            {bid.documents && bid.documents.length > 0 ? (
              <div className="space-y-3">
                {bid.documents.map((doc) => (
                  <div key={doc.id} className="p-4 bg-canvas border border-line rounded-lg">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <FileCheck className="w-4 h-4 text-slate" />
                          <span className="font-semibold text-ink text-sm truncate">{doc.name || doc.file_name || "Document"}</span>
                          <span className="text-[10px] font-mono text-slate bg-white px-1.5 py-0.5 rounded border border-line">
                            {doc.document_type || "GENERAL"}
                          </span>
                        </div>
                        <div className="text-xs text-slate mt-1">
                          Uploaded: {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleString() : "Unknown"}
                        </div>
                      </div>
                      {doc.status ? (
                        <StatusBadge status={doc.status} size="xs" />
                      ) : (
                        <span className="text-[10px] font-mono text-slate px-2.5 py-1 bg-white rounded-md border border-line">
                          Uploaded
                        </span>
                      )}
                    </div>

                    {/* OCR Status */}
                    {doc.ocr_status && (
                      <div className="mt-2 text-xs text-slate">
                        OCR Status: <span className="font-semibold text-ink">{doc.ocr_status}</span>
                      </div>
                    )}

                    {/* Extracted Fields */}
                    {doc.extracted_fields && Object.keys(doc.extracted_fields).length > 0 && (
                      <div className="mt-3 p-2.5 bg-white border border-line rounded-lg text-xs space-y-1">
                        <div className="font-semibold text-ink mb-1">Extracted Data:</div>
                        {Object.entries(doc.extracted_fields).map(([key, value]) => (
                          <div key={key} className="flex justify-between gap-2">
                            <span className="text-slate font-mono">{key}:</span>
                            <span className="text-ink font-semibold">{value}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 text-center bg-canvas/50 rounded-lg border border-dashed border-line">
                <p className="text-xs text-slate">No documents submitted yet</p>
              </div>
            )}
          </div>

          {/* Clause-by-Clause Evaluation Rows */}
          <div className="bg-card border border-line rounded-card p-6 shadow-xs">
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-base font-bold text-ink">Deterministic Clause Verification</h2>
              <span className="text-xs font-mono text-slate">
                {(bid.compliance_results || []).filter((c) => c.status === "PASS").length}/{(bid.compliance_results || []).length} Passing
              </span>
            </div>
            <p className="text-xs text-slate mb-5">
              Evaluated strictly by logic engine without LLM intervention. Every rule links to document evidence.
            </p>

            <div className="space-y-3">
              {(bid.compliance_results || []).map((c) => {
                const isPass = c.status === "PASS";
                const isFail = c.status === "FAIL";
                const isExpanded = expandedReasoning[c.clause_id];

                const bgTint = isPass
                  ? "bg-passBg/30 border-pass/30"
                  : isFail
                  ? "bg-failBg/30 border-fail/30"
                  : "bg-reviewBg/30 border-review/30";

                const StatusIcon = isPass ? CheckCircle2 : isFail ? XCircle : AlertTriangle;
                const statusColor = isPass ? "text-pass" : isFail ? "text-fail" : "text-review";

                return (
                  <div
                    key={c.clause_id}
                    className={`border rounded-xl p-4 transition-all ${bgTint}`}
                  >
                    <div className="flex items-start gap-3.5">
                      <div className={`mt-0.5 shrink-0 ${statusColor}`}>
                        <StatusIcon className="w-5 h-5" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-ink leading-snug">{c.clause_text}</span>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                                c.mandatory ? "bg-failBg text-fail border border-fail/20" : "bg-canvas text-slate border border-line"
                              }`}
                            >
                              {c.mandatory ? "Mandatory" : "Optional"}
                            </span>
                          </div>
                          <StatusBadge status={c.status} size="xs" />
                        </div>

                        <div className="text-[11px] font-mono text-slate mt-1">
                          Clause Ref: {c.clause_id}
                        </div>

                        {/* Evidence References */}
                        {c.evidence_refs && c.evidence_refs.length > 0 && (
                          <div className="mt-2 text-[11px] text-accent font-mono bg-white/80 border border-line px-2.5 py-1 rounded-md inline-block">
                            Source Citation: {c.evidence_refs.join(", ")}
                          </div>
                        )}

                        {/* Expandable Reasoning */}
                        {c.reasoning_chain && c.reasoning_chain.length > 0 && (
                          <div className="mt-2.5">
                            <button
                              type="button"
                              onClick={() => toggleReasoning(c.clause_id)}
                              className="text-[11px] font-semibold text-slate hover:text-ink inline-flex items-center gap-1 cursor-pointer"
                            >
                              <span>{isExpanded ? "Hide reasoning" : "View logic reasoning"}</span>
                              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            </button>

                            {isExpanded && (
                              <div className="mt-2 p-3 bg-white rounded-lg border border-line text-xs text-slate space-y-1 pl-3 border-l-2 border-l-accent">
                                {c.reasoning_chain.map((r, i) => (
                                  <div key={i} className="flex items-start gap-1.5">
                                    <span className="text-accent font-mono">›</span>
                                    <span>{r}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Extensible Additional Verification Actions */}
          <div className="bg-card border border-line rounded-card p-6 shadow-xs">
            <h2 className="text-base font-bold text-ink mb-1">On-Demand Registry Verifications</h2>
            <p className="text-xs text-slate mb-4">
              Query live government portals to confirm credentials, check blacklists, or inspect filings.
            </p>

            <div className="flex flex-wrap items-center gap-3 mb-4">
              <select
                value={selectedAdapter}
                onChange={(e) => setSelectedAdapter(e.target.value)}
                className="bg-canvas border border-line rounded-xl px-3.5 py-2 text-xs font-semibold text-ink focus:outline-none focus:border-accent"
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
                className="bg-accent hover:bg-accent2 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-xs transition-all hover:scale-[1.02] disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
              >
                <Search className="w-3.5 h-3.5" />
                <span>{runningVerification ? "Querying Registry…" : "Trigger Check"}</span>
              </button>
            </div>

            {verificationFeedback && (
              <div className="p-4 bg-passBg/40 border border-pass/30 rounded-xl text-xs mb-4">
                <div className="flex items-center justify-between font-bold">
                  <span className="text-pass flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Source: {verificationFeedback.source}</span>
                  </span>
                  <StatusBadge status={verificationFeedback.status} size="xs" />
                </div>
                <div className="text-ink mt-1.5 font-medium">{verificationFeedback.evidence}</div>
                {verificationFeedback.data && (
                  <pre className="mt-2.5 text-[10px] bg-white p-3 rounded-lg border border-line font-mono text-slate overflow-x-auto">
                    {JSON.stringify(verificationFeedback.data, null, 2)}
                  </pre>
                )}
              </div>
            )}

            {bid.custom_verifications?.length > 0 && (
              <div className="space-y-2 mt-4 pt-4 border-t border-line">
                <div className="text-xs font-bold text-ink">Recorded Verification Audit:</div>
                {bid.custom_verifications.map((v) => (
                  <div key={v.id} className="p-3 bg-canvas border border-line rounded-xl text-xs flex items-center justify-between">
                    <div>
                      <span className="font-bold text-ink">{v.source}</span>: <span className="text-slate">{v.evidence}</span>
                    </div>
                    <StatusBadge status={v.status} size="xs" />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Risk Signals, Officer Decision, Inspection Notes */}
        <div className="lg:col-span-4 space-y-6">
          {/* Risk Signals Panel with Horizontal Visual Bars */}
          <div className="bg-card border border-line rounded-card p-6 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-bold text-ink">Risk Signals</h2>
              <StatusBadge status={bid.risk_assessment?.risk_level || "UNKNOWN"} size="xs" />
            </div>

            {(bid.risk_assessment?.signals || []).length > 0 ? (
              <div className="space-y-3.5">
                {bid.risk_assessment.signals.map((sig, i) => {
                  const contrib = sig.contribution || 10;
                  const barWidth = Math.min(100, Math.max(15, contrib * 3));

                  return (
                    <div key={i} className="p-3 bg-failBg/20 border border-fail/20 rounded-xl text-xs space-y-2">
                      <div className="flex justify-between items-center font-bold text-ink">
                        <span>{sig.signal_type}</span>
                        <span className="text-fail font-mono">+{contrib}</span>
                      </div>

                      {/* Visual Contribution Bar */}
                      <div className="w-full bg-line/80 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-fail h-full rounded-full" style={{ width: `${barWidth}%` }} />
                      </div>

                      <div className="text-[11px] text-slate font-mono flex items-center gap-1">
                        <Info className="w-3 h-3 text-slate shrink-0" />
                        <span className="truncate">{sig.evidence_ref}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-xs text-pass font-semibold p-4 bg-passBg rounded-xl text-center flex items-center justify-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>No adverse risk signals detected</span>
              </div>
            )}
          </div>

          {/* Officer Decision Panel (Gating) */}
          <div className="bg-card border-2 border-accent/40 rounded-card p-6 shadow-md relative">
            <div className="flex items-center gap-2 mb-1">
              <Lock className="w-4 h-4 text-accent" />
              <h2 className="text-base font-bold text-ink">Procurement Officer Decision</h2>
            </div>
            <p className="text-xs text-slate mb-5">
              Officer decision is binding and cryptographically logged to the audit ledger.
            </p>

            {pendingDecision && pendingDecision !== (bid?.ai_recommendation || "REVIEW") && (
              <div className="mb-4 p-3.5 bg-reviewBg/60 border border-review/40 rounded-xl text-xs space-y-2">
                <div className="font-bold text-review flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>Mandatory Override Justification</span>
                </div>
                <p className="text-slate text-[11px] leading-relaxed">
                  You are selecting <strong>{pendingDecision}</strong> which diverges from AI recommendation <strong>{bid?.ai_recommendation || "REVIEW"}</strong>. Enter statutory justification below:
                </p>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="Record justification for immutable audit trail…"
                  className="w-full bg-white border border-line rounded-lg p-2.5 text-xs text-ink focus:outline-none focus:border-accent"
                  rows={2}
                />
              </div>
            )}

            <div className="grid grid-cols-1 gap-2.5">
              <button
                onClick={() => submitDecision("VERIFIED")}
                disabled={decisionBusy}
                className="w-full bg-pass hover:bg-pass/90 text-white font-semibold text-xs py-3 px-4 rounded-xl shadow-xs transition-all hover:scale-[1.01] flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Approve & Mark Verified</span>
              </button>

              <button
                onClick={() => submitDecision("NEEDS_CLARIFICATION")}
                disabled={decisionBusy}
                className="w-full bg-review hover:bg-review/90 text-white font-semibold text-xs py-3 px-4 rounded-xl shadow-xs transition-all hover:scale-[1.01] flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                <HelpCircle className="w-4 h-4" />
                <span>Request Clarification</span>
              </button>

              <button
                onClick={() => submitDecision("NON_COMPLIANT")}
                disabled={decisionBusy}
                className="w-full bg-fail hover:bg-fail/90 text-white font-semibold text-xs py-3 px-4 rounded-xl shadow-xs transition-all hover:scale-[1.01] flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                <ShieldAlert className="w-4 h-4" />
                <span>Reject as Non-Compliant</span>
              </button>
            </div>
          </div>

          {/* Add Inspection Notes */}
          <div className="bg-card border border-line rounded-card p-6 shadow-xs">
            <h2 className="text-base font-bold text-ink mb-2">Inspection Notes</h2>
            <form onSubmit={handleAddNote} className="space-y-3 mb-4">
              <textarea
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Add inspection remark or observation…"
                className="w-full bg-canvas border border-line rounded-xl p-3 text-xs text-ink focus:outline-none focus:border-accent"
                rows={2}
              />
              <div className="flex justify-between items-center">
                <select
                  value={noteCategory}
                  onChange={(e) => setNoteCategory(e.target.value)}
                  className="bg-white border border-line rounded-lg px-2.5 py-1.5 text-xs text-ink"
                >
                  <option value="GENERAL">General</option>
                  <option value="COMPLIANCE">Compliance</option>
                  <option value="RISK">Risk Signal</option>
                </select>
                <button
                  type="submit"
                  disabled={savingNote || !newNote.trim()}
                  className="bg-accent hover:bg-accent2 text-white text-xs font-semibold px-4 py-1.5 rounded-lg disabled:opacity-50 cursor-pointer transition-colors"
                >
                  {savingNote ? "Saving…" : "Add Note"}
                </button>
              </div>
            </form>

            <div className="space-y-2 max-h-52 overflow-y-auto">
              {bid.notes?.map((n) => (
                <div key={n.id} className="p-3 bg-canvas rounded-xl border border-line text-xs">
                  <div className="flex justify-between text-[10px] text-slate mb-1">
                    <span className="font-bold text-ink uppercase tracking-wider">{n.category}</span>
                    <span>{new Date(n.created_at).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-ink leading-relaxed">{n.note}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
