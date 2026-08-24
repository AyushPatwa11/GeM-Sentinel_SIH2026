import React, { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";

export default function BidderReadiness() {
  const [searchParams] = useSearchParams();
  const [bidId, setBidId] = useState(searchParams.get("bidId") || "bid-northline");
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
    load(bidId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bidId]);

  useEffect(() => {
    let cancelled = false;
    async function refreshStatus() {
      try {
        const status = await api.bidderBidStatus(bidId);
        if (!cancelled) {
          setBidStatus(status);
          setSubmitted(status.status === "SUBMITTED");
        }
      } catch {
        // The readiness flow already shows API errors; keep polling quiet.
      }
    }
    refreshStatus();
    const refreshTimer = window.setInterval(refreshStatus, 4000);
    return () => {
      cancelled = true;
      window.clearInterval(refreshTimer);
    };
  }, [bidId]);

  useEffect(() => {
    api.bidderBids().then(setBids);
  }, []);

  const ICON = {
    SATISFIED: "✓",
    MISSING: "✕",
    WEAK_EVIDENCE: "⚠",
    REVIEW: "⚠",
  };

  const canSubmit = readiness && !readiness.items.some((i) => i.status === "MISSING");

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
      setMessage({ type: "success", text: `${uploaded.length} document${uploaded.length === 1 ? "" : "s"} uploaded. Readiness has been updated for this bid only.` });
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
      setMessage({ type: "success", text: `Bid submitted successfully with ${result.document_count} uploaded document${result.document_count === 1 ? "" : "s"}.` });
    } catch (error) {
      setMessage({ type: "error", text: error.message });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold text-ink mb-1">Pre-submission compliance check</h1>
      <p className="text-sm text-slate mb-6">Run this before submitting to catch avoidable rejections. You cannot change tender requirements here.</p>

      <select
        value={bidId}
        onChange={(e) => setBidId(e.target.value)}
        className="mb-5 text-sm border border-line rounded-lg px-3 py-2 bg-white"
      >
        {bids.map((bid) => (
          <option key={bid.id} value={bid.id}>{bid.tender.title} · {bid.status.replaceAll("_", " ")}</option>
        ))}
      </select>

      <div className="bg-card border border-line rounded-card px-5 py-5 max-w-lg">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-ink">Compliance readiness</span>
          <span className="font-display text-2xl font-semibold text-ink">
            {loading ? "…" : `${readiness?.readiness_percent ?? 0}%`}
          </span>
        </div>
        <p className="text-xs text-slate mb-4">{readiness?.tender?.title || "Loading tender…"} · v{readiness?.tender?.version || "—"}</p>

        {bidStatus && (
          <div className="mb-4 flex items-center justify-between rounded-lg bg-canvas px-3 py-2">
            <span className="text-xs text-slate">Bid status</span>
            <StatusBadge status={bidStatus.status} />
          </div>
        )}
        {bidStatus?.decision && (
          <p className="mb-4 text-xs text-slate">
            Officer decision: <span className="font-medium text-ink">{bidStatus.decision.final_decision.replaceAll("_", " ")}</span>
            {bidStatus.decision.override_reason ? ` — ${bidStatus.decision.override_reason}` : ""}
          </p>
        )}

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

        <input ref={fileInputRef} type="file" multiple className="sr-only" onChange={handleUpload} />
        {documents.length > 0 && (
          <p className="mt-3 text-xs text-slate">
            Uploaded: {documents.map((document) => document.filename).join(", ")}
          </p>
        )}
        {message && (
          <p className={`mt-3 text-xs ${message.type === "error" ? "text-fail" : "text-pass"}`} role="status">
            {message.text}
          </p>
        )}

        <div className="flex gap-2 mt-5 pt-4 border-t border-line">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading || submitted || ["VERIFIED", "NON_COMPLIANT"].includes(bidStatus?.status)}
            className="flex-1 text-xs font-medium border border-line text-ink rounded-lg py-2.5 hover:bg-canvas transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {uploading ? "Uploading…" : "Upload documents"}
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit || submitting || submitted || ["VERIFIED", "NON_COMPLIANT", "CLARIFICATION_REQUIRED"].includes(bidStatus?.status)}
            className="flex-1 text-xs font-medium bg-accent text-white rounded-lg py-2.5 hover:bg-accent2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title={!canSubmit ? "Resolve mandatory items first" : ""}
          >
            {submitted ? "Bid submitted" : submitting ? "Submitting…" : "Submit bid"}
          </button>
        </div>
      </div>
    </Shell>
  );
}
