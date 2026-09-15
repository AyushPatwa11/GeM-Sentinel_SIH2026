import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";
import { ArrowLeft, Edit2, Save, X } from "lucide-react";

export default function BidderStatusTracker() {
  const { bidId } = useParams();
  const navigate = useNavigate();
  const [statusData, setStatusData] = useState(null);
  const [bids, setBids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [isEditMode, setIsEditMode] = useState(false);
  const [editData, setEditData] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  async function fetchStatus() {
    try {
      if (bidId) {
        const res = await api.bidderBidStatus(bidId);
        setStatusData(res);
        if (!editData) setEditData(res);
      } else {
        // Fetch all bids if no specific bidId
        const res = await api.bidderBids();
        setBids(res);
      }
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message || "Failed to fetch bid status");
    } finally {
      setLoading(false);
    }
  }

  const handleEditClick = () => {
    setEditData({ ...statusData });
    setIsEditMode(true);
  };

  const handleCancel = () => {
    setIsEditMode(false);
    setEditData(null);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Update bid with edit data
      await api.updateBid(bidId, {
        bidder_org_name: editData.bidder_org_name,
        bid_amount: editData.bid_amount,
        delivery_location: editData.delivery_location,
        technical_specs: editData.technical_specs,
      });
      setStatusData(editData);
      setIsEditMode(false);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to save changes");
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Live polling every 3 seconds for immediate real-time sync with officer decisions
    const timer = setInterval(fetchStatus, 3000);
    return () => clearInterval(timer);
  }, [bidId]);

  if (loading) {
    return (
      <div className="py-12 text-center text-sm text-slate">Loading real-time bid status…</div>
    );
  }

  if (error && bidId) {
    return (
      <div className="bg-failBg text-fail border border-fail/20 p-4 rounded-lg text-sm">
        {error || "Bid not found"}
      </div>
    );
  }

  // Show list of bids if no specific bidId selected
  if (!bidId && bids.length > 0) {
    return (
      <>
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold text-ink tracking-tight">My Bids</h1>
          <p className="text-sm text-slate mt-1">Track the status of all your submitted bids</p>
        </div>
        <div className="grid gap-4">
          {bids.map((bid) => (
            <div
              key={bid.id}
              onClick={() => navigate(`/bidder/status/${bid.id}`)}
              className="bg-card border border-line rounded-lg p-4 cursor-pointer hover:border-accent hover:shadow-md transition-all"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-ink">{bid.tender?.title}</h3>
                  <p className="text-xs text-slate mt-1">Bid ID: {bid.id}</p>
                </div>
                <StatusBadge status={bid.status} />
              </div>
            </div>
          ))}
        </div>
      </>
    );
  }

  if (!statusData && bidId) {
    return (
      <div className="bg-failBg text-fail border border-fail/20 p-4 rounded-lg text-sm">
        Bid not found
      </div>
    );
  }

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <button
            onClick={() => navigate("/bidder")}
            className="text-xs text-slate hover:text-ink mb-1 inline-flex items-center gap-1 font-medium"
          >
            <ArrowLeft className="w-3 h-3" /> Back to Tenders
          </button>
          <h1 className="font-display text-2xl font-bold text-ink">Live Bid Status Tracker</h1>
          <p className="text-xs text-slate mt-0.5">
            Bidding Entity: <span className="font-semibold text-ink">{statusData.bidder_org_name}</span> · Bid ID: <span className="font-mono text-ink">{bidId}</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="text-xs text-slate bg-card border border-line px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-pass animate-pulse inline-block mr-1.5" />
            Live sync active · Last check: {lastUpdated.toLocaleTimeString()}
          </div>
          
          {statusData && !isEditMode && statusData.status !== "VERIFIED" && (
            <button
              onClick={handleEditClick}
              className="bg-accent hover:bg-accent2 text-white text-xs font-semibold px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5 transition-all"
            >
              <Edit2 className="w-3.5 h-3.5" />
              Edit
            </button>
          )}
          
          {isEditMode && (
            <div className="flex items-center gap-2">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="bg-pass hover:bg-pass/90 text-white text-xs font-semibold px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5 transition-all disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                {isSaving ? "Saving…" : "Save"}
              </button>
              <button
                onClick={handleCancel}
                className="bg-slate/20 hover:bg-slate/30 text-slate text-xs font-semibold px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5 transition-all"
              >
                <X className="w-3.5 h-3.5" />
                Cancel
              </button>
            </div>
          )}
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
          {[
            { num: 1, label: "Bid Draft Initialized", done: true },
            { num: 2, label: "Documents Verified & Hashed", done: statusData.current_step >= 2 },
            { num: 3, label: "Submitted & In Review", done: statusData.current_step >= 3 },
            { num: 4, label: "Officer Decision Recorded", done: statusData.current_step >= 4 },
          ].map((st) => (
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
          {/* Edit Mode: Editable Bid Details */}
          {isEditMode && editData && (
            <div className="bg-accent/5 border-2 border-accent rounded-card p-6">
              <h2 className="text-sm font-bold text-ink mb-4">Edit Bid Details</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate uppercase">Bidder Organization Name</label>
                  <input
                    type="text"
                    value={editData.bidder_org_name || ""}
                    onChange={(e) => setEditData({ ...editData, bidder_org_name: e.target.value })}
                    className="w-full mt-1 bg-white border border-line rounded-lg px-3 py-2 text-xs text-ink focus:outline-none focus:border-accent"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-slate uppercase">Bid Amount</label>
                    <input
                      type="number"
                      value={editData.bid_amount || ""}
                      onChange={(e) => setEditData({ ...editData, bid_amount: e.target.value })}
                      className="w-full mt-1 bg-white border border-line rounded-lg px-3 py-2 text-xs text-ink focus:outline-none focus:border-accent"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate uppercase">Delivery Location</label>
                    <input
                      type="text"
                      value={editData.delivery_location || ""}
                      onChange={(e) => setEditData({ ...editData, delivery_location: e.target.value })}
                      className="w-full mt-1 bg-white border border-line rounded-lg px-3 py-2 text-xs text-ink focus:outline-none focus:border-accent"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate uppercase">Technical Specifications</label>
                  <textarea
                    value={editData.technical_specs || ""}
                    onChange={(e) => setEditData({ ...editData, technical_specs: e.target.value })}
                    rows={3}
                    className="w-full mt-1 bg-white border border-line rounded-lg px-3 py-2 text-xs text-ink focus:outline-none focus:border-accent"
                  />
                </div>

                <p className="text-xs text-slate italic">
                  💡 Edit your bid details before the officer makes a final decision. Once verified, editing will be locked.
                </p>
              </div>
            </div>
          )}

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
    </>
  );
}
