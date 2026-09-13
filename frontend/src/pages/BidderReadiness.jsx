import React, { useEffect, useRef, useState } from "react";
import { useSearchParams, useNavigate, useParams } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  UploadCloud,
  Send,
  Lock,
  FileCheck2,
  Sparkles,
  ArrowRight,
  HelpCircle,
} from "lucide-react";

/* Minimal SVG Progress Ring Component */
function ReadinessRing({ percent = 0, isComplete = false }) {
  const radius = 48;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, percent)) / 100) * circumference;

  const color = isComplete ? "#1B8A5A" : percent > 60 ? "#2F5DE8" : "#C23B3B";
  const bgTrack = isComplete ? "#E8F6EF" : "#E4E8F1";

  return (
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
          style={{ strokeDashoffset, transition: "stroke-dashoffset 0.8s ease" }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-mono text-xl font-bold text-ink leading-none">{percent}%</span>
        <span className="text-[9px] uppercase font-mono text-slate mt-0.5 font-medium">Ready</span>
      </div>
    </div>
  );
}

export default function BidderReadiness() {
  const { bidId: routeBidId } = useParams();
  const [searchParams] = useSearchParams();
  const [bidId, setBidId] = useState(routeBidId || searchParams.get("bidId"));
  const [bids, setBids] = useState([]);
  const [readiness, setReadiness] = useState(null);
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const [bidStatus, setBidStatus] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  // Load bids and set default if bidId not provided
  useEffect(() => {
    api.bidderBids().then((bidList) => {
      setBids(bidList);
      if (!bidId && bidList.length > 0) {
        setBidId(bidList[0].id);
      }
    });
  }, []);

  async function load(id) {
    setLoading(true);
    try {
      const [data, uploadedDocuments] = await Promise.all([
        api.bidderReadiness(id),
        api.bidderDocuments(id),
      ]);
      setReadiness(data);
      setDocuments(uploadedDocuments);
      setSubmitted(false);
      setMessage(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (bidId) {
      load(bidId);
    }
  }, [bidId]);

  useEffect(() => {
    if (!bidId) return;

    let cancelled = false;
    async function refreshStatus() {
      try {
        const status = await api.bidderBidStatus(bidId);
        if (!cancelled) {
          setBidStatus(status);
          setSubmitted(status.status === "SUBMITTED");
        }
      } catch {
        // quiet polling
      }
    }
    refreshStatus();
    const refreshTimer = window.setInterval(refreshStatus, 4000);
    return () => {
      cancelled = true;
      window.clearInterval(refreshTimer);
    };
  }, [bidId]);

  const missingItems = readiness?.items.filter((i) => i.status === "MISSING") || [];
  const reviewItems = readiness?.items.filter((i) => i.status === "REVIEW" || i.status === "WEAK_EVIDENCE") || [];
  const satisfiedItems = readiness?.items.filter((i) => i.status === "SATISFIED") || [];

  const canSubmit = readiness && missingItems.length === 0;

  async function handleUpload(event) {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    if (!files.length) return;

    setUploading(true);
    setMessage(null);
    try {
      const uploaded = await api.bidderUploadDocuments(bidId, files);
      setDocuments((current) => [...current, ...uploaded]);
      await load(bidId);
      setMessage({
        type: "success",
        text: `${uploaded.length} document${uploaded.length === 1 ? "" : "s"} uploaded. Readiness recalculation complete.`,
      });
    } catch (error) {
      setMessage({ type: "error", text: error.message });
    } finally {
      setUploading(false);
    }
  }

  async function handleSubmit() {
    if (!canSubmit || submitted) return;
    setSubmitting(true);
    setMessage(null);
    try {
      const result = await api.bidderSubmit(bidId);
      setSubmitted(true);
      setBidStatus((current) => ({ ...current, status: result.status }));
      setMessage({
        type: "success",
        text: `Bid submitted successfully. Track your evaluation in real-time.`,
      });
    } catch (error) {
      setMessage({ type: "error", text: error.message });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Shell>
      {/* Page Header */}
      <div className="mb-8">
        <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-2.5 py-0.5 rounded-full border border-accent/20 mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Bidder Diagnostic Studio</span>
        </div>
        <h1 className="font-display text-3xl font-bold text-ink tracking-tight">
          Pre-Submission Compliance Check
        </h1>
        <p className="text-sm text-slate mt-1">
          Verify tender requirements and diagnose missing records before final submission to prevent administrative disqualification.
        </p>
      </div>

      {/* Tender / Bid Selector */}
      <div className="mb-8">
        <label className="block text-xs font-bold text-slate uppercase tracking-wider mb-2">
          Select Active Bidding Profile:
        </label>
        <select
          value={bidId}
          onChange={(e) => setBidId(e.target.value)}
          className="text-sm border border-line rounded-xl px-4 py-2.5 bg-white text-ink font-semibold focus:outline-none focus:border-accent w-full max-w-md shadow-xs"
        >
          {bids.map((bid) => (
            <option key={bid.id} value={bid.id}>
              {bid.tender.title} — {bid.status.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 max-w-5xl">
        {/* Main Readiness Gauge & Actions Card */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-card border border-line rounded-card p-6 shadow-xs">
            <div className="flex items-center justify-between gap-4 pb-6 border-b border-line">
              <div>
                <div className="text-[11px] uppercase font-mono text-slate font-semibold">Diagnostic Score</div>
                <h3 className="text-lg font-bold text-ink mt-0.5">Compliance Gauge</h3>
                <p className="text-xs text-slate mt-1">
                  {missingItems.length === 0 ? "All mandatory items clear" : `${missingItems.length} mandatory item(s) pending`}
                </p>
              </div>

              <ReadinessRing
                percent={readiness?.readiness_percent ?? 0}
                isComplete={canSubmit}
              />
            </div>

            {/* Target Tender Summary */}
            <div className="py-4 border-b border-line space-y-1.5 text-xs">
              <div className="text-slate flex justify-between">
                <span>Tender:</span>
                <span className="font-semibold text-ink text-right truncate max-w-[180px]">
                  {readiness?.tender?.title || "Loading…"}
                </span>
              </div>
              <div className="text-slate flex justify-between">
                <span>Version:</span>
                <span className="font-mono text-ink">v{readiness?.tender?.version || "1.0"}</span>
              </div>
              {bidStatus && (
                <div className="text-slate flex justify-between items-center pt-1">
                  <span>Current State:</span>
                  <StatusBadge status={bidStatus.status} size="xs" />
                </div>
              )}
            </div>

            {/* Upload & Submission Form */}
            <div className="pt-6 space-y-3">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                className="sr-only"
                onChange={handleUpload}
              />

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading || submitted || ["VERIFIED", "NON_COMPLIANT"].includes(bidStatus?.status)}
                className="w-full text-xs font-semibold border border-line text-ink rounded-xl py-3 hover:bg-canvas transition-all flex items-center justify-center gap-2 disabled:opacity-40 cursor-pointer shadow-xs"
              >
                <UploadCloud className="w-4 h-4 text-accent" />
                <span>{uploading ? "Uploading Documents…" : "Upload Compliance Documents"}</span>
              </button>

              <button
                type="button"
                onClick={handleSubmit}
                disabled={!canSubmit || submitting || submitted || ["VERIFIED", "NON_COMPLIANT"].includes(bidStatus?.status)}
                className={`w-full text-xs font-semibold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer shadow-sm ${
                  canSubmit && !submitted
                    ? "bg-accent hover:bg-accent2 text-white hover:scale-[1.01]"
                    : "bg-line text-slate cursor-not-allowed"
                }`}
              >
                {!canSubmit ? (
                  <>
                    <Lock className="w-4 h-4 text-slate" />
                    <span>Resolve Mandatory Gaps to Submit</span>
                  </>
                ) : submitted ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-pass" />
                    <span>Bid Submitted Successfully</span>
                  </>
                ) : submitting ? (
                  <span>Submitting Bid…</span>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Submit Bid to Officer Queue</span>
                  </>
                )}
              </button>

              {message && (
                <div
                  className={`p-3 rounded-xl text-xs flex items-start gap-2 ${
                    message.type === "error"
                      ? "bg-failBg text-fail border border-fail/20"
                      : "bg-passBg text-pass border border-pass/20"
                  }`}
                >
                  {message.type === "error" ? (
                    <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                  )}
                  <span>{message.text}</span>
                </div>
              )}
            </div>
          </div>

          {/* Uploaded Documents List */}
          {documents.length > 0 && (
            <div className="bg-card border border-line rounded-card p-5 shadow-xs">
              <h4 className="text-xs font-bold text-ink uppercase tracking-wider mb-2.5">
                Attached Bid Documents ({documents.length})
              </h4>
              <div className="space-y-1.5 max-h-40 overflow-y-auto">
                {documents.map((doc, i) => (
                  <div key={i} className="text-xs font-mono text-slate p-2 bg-canvas rounded-lg border border-line flex items-center gap-2">
                    <FileCheck2 className="w-3.5 h-3.5 text-accent shrink-0" />
                    <span className="truncate">{doc.filename}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Grouped Checklist (Action Items First) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Missing Mandatory Action Items */}
          {missingItems.length > 0 && (
            <div className="bg-failBg/30 border border-fail/30 rounded-card p-6 shadow-xs">
              <div className="flex items-center gap-2 mb-1">
                <XCircle className="w-5 h-5 text-fail" />
                <h3 className="text-base font-bold text-ink">Action Required: Missing Mandatory Items</h3>
              </div>
              <p className="text-xs text-slate mb-4">
                These statutory hard-gates must be fulfilled before the portal permits bid submission.
              </p>

              <div className="space-y-2.5">
                {missingItems.map((item) => (
                  <div
                    key={item.clause_id}
                    className="p-3.5 bg-white border border-fail/30 rounded-xl flex items-start gap-3 shadow-xs"
                  >
                    <XCircle className="w-4 h-4 text-fail shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="text-xs font-bold text-ink leading-tight">
                        {item.requirement_summary}
                      </div>
                      <div className="text-[10px] font-mono text-fail font-semibold mt-1">
                        Clause: {item.clause_id} • Missing Attachment / Verification
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Items Needing Review / Weak Evidence */}
          {reviewItems.length > 0 && (
            <div className="bg-reviewBg/30 border border-review/30 rounded-card p-6 shadow-xs">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-5 h-5 text-review" />
                <h3 className="text-base font-bold text-ink">Attention: Conditional / Review Items</h3>
              </div>
              <p className="text-xs text-slate mb-4">
                Evidence provided may require clarification during officer review.
              </p>

              <div className="space-y-2.5">
                {reviewItems.map((item) => (
                  <div
                    key={item.clause_id}
                    className="p-3.5 bg-white border border-review/30 rounded-xl flex items-start gap-3 shadow-xs"
                  >
                    <AlertTriangle className="w-4 h-4 text-review shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="text-xs font-bold text-ink leading-tight">
                        {item.requirement_summary}
                      </div>
                      <div className="text-[10px] font-mono text-review font-semibold mt-1">
                        Clause: {item.clause_id} • Review Flagged
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Satisfied Criteria */}
          <div className="bg-card border border-line rounded-card p-6 shadow-xs">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="w-5 h-5 text-pass" />
              <h3 className="text-base font-bold text-ink">Satisfied Requirements ({satisfiedItems.length})</h3>
            </div>
            <p className="text-xs text-slate mb-4">
              Validated against attached documents and authoritative government records.
            </p>

            <div className="space-y-2">
              {satisfiedItems.map((item) => (
                <div
                  key={item.clause_id}
                  className="p-3 bg-passBg/20 border border-pass/20 rounded-xl flex items-start gap-3"
                >
                  <CheckCircle2 className="w-4 h-4 text-pass shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <span className="text-xs text-ink leading-tight font-medium">
                      {item.requirement_summary}
                    </span>
                    <div className="text-[10px] font-mono text-pass font-semibold mt-0.5">
                      Clause: {item.clause_id} • Verified
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
