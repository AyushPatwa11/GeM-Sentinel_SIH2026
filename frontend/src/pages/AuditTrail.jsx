import React, { useEffect, useState } from "react";
import Shell from "../components/Shell.jsx";
import { api } from "../lib/api.js";

export default function AuditTrail() {
  const [bidId, setBidId] = useState("bid-meridian");
  const [events, setEvents] = useState([]);

  useEffect(() => {
    api.officerAudit(bidId).then(setEvents).catch(() => setEvents([]));
  }, [bidId]);

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold text-ink mb-1">Audit trail</h1>
      <p className="text-sm text-slate mb-6">Append-only record of every evaluation and officer decision.</p>

      <select
        value={bidId}
        onChange={(e) => setBidId(e.target.value)}
        className="mb-4 text-sm border border-line rounded-lg px-3 py-2 bg-white"
      >
        <option value="bid-northline">Northline Engineering Pvt Ltd</option>
        <option value="bid-coastal">Coastal Agro Supplies</option>
        <option value="bid-meridian">Meridian Textiles Pvt Ltd</option>
      </select>

      <div className="bg-card border border-line rounded-card divide-y divide-line">
        {events.length === 0 && <div className="px-5 py-6 text-sm text-slate">No events yet — run an evaluation first.</div>}
        {events.map((e) => (
          <div key={e.id} className="px-5 py-3.5">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-ink">{e.event_type.replaceAll("_", " ")}</span>
              <span className="text-xs text-slate font-mono">{new Date(e.created_at).toLocaleString()}</span>
            </div>
            <pre className="text-xs text-slate mt-1 font-mono">{JSON.stringify(e.payload, null, 0)}</pre>
          </div>
        ))}
      </div>
    </Shell>
  );
}
