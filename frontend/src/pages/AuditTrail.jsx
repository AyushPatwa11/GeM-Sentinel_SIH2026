import React, { useEffect, useState } from "react";
import Shell from "../components/Shell.jsx";
import { api } from "../lib/api.js";
import { History, ShieldCheck, FileText, CheckCircle2, AlertTriangle, Clock } from "lucide-react";

export default function AuditTrail() {
  const [bidId, setBidId] = useState("bid-meridian");
  const [events, setEvents] = useState([]);

  useEffect(() => {
    api.officerAudit(bidId).then(setEvents).catch(() => setEvents([]));
  }, [bidId]);

  return (
    <Shell>
      <div className="mb-8">
        <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-2.5 py-0.5 rounded-full border border-accent/20 mb-2">
          <History className="w-3.5 h-3.5" />
          <span>Statutory Compliance Ledger</span>
        </div>
        <h1 className="font-display text-3xl font-bold text-ink tracking-tight">Immutable Audit Trail</h1>
        <p className="text-sm text-slate mt-1">
          Cryptographically timestamped, append-only record of every evaluation step, API check, and officer verdict.
        </p>
      </div>

      <div className="mb-6 max-w-md">
        <label className="block text-xs font-bold text-slate uppercase tracking-wider mb-2">
          Select Target Bid Ledger:
        </label>
        <select
          value={bidId}
          onChange={(e) => setBidId(e.target.value)}
          className="text-sm border border-line rounded-xl px-4 py-2.5 bg-white text-ink font-semibold focus:outline-none focus:border-accent w-full shadow-xs"
        >
          <option value="bid-northline">Northline Engineering Pvt Ltd (bid-northline)</option>
          <option value="bid-coastal">Coastal Agro Supplies (bid-coastal)</option>
          <option value="bid-meridian">Meridian Textiles Pvt Ltd (bid-meridian)</option>
        </select>
      </div>

      <div className="bg-card border border-line rounded-card divide-y divide-line shadow-xs overflow-hidden">
        {events.length === 0 && (
          <div className="px-6 py-12 text-center text-sm text-slate">
            <Clock className="w-6 h-6 text-slate/50 mx-auto mb-2" />
            <div>No logged events yet — trigger an evaluation check first.</div>
          </div>
        )}
        {events.map((e) => (
          <div key={e.id} className="p-5 hover:bg-canvas/50 transition-colors">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent" />
                <span className="text-sm font-bold text-ink font-mono">{e.event_type.replaceAll("_", " ")}</span>
              </div>
              <span className="text-xs text-slate font-mono bg-canvas px-2.5 py-1 rounded-md border border-line">
                {new Date(e.created_at).toLocaleString()}
              </span>
            </div>
            <pre className="text-xs text-slate mt-2 font-mono bg-canvas/80 p-3 rounded-lg border border-line/60 overflow-x-auto">
              {JSON.stringify(e.payload, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </Shell>
  );
}
