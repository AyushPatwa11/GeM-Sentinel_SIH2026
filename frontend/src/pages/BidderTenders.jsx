import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";

export default function BidderTenders() {
  const [tenders, setTenders] = useState([]);
  const [myBids, setMyBids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function loadData() {
    try {
      const [tList, bList] = await Promise.all([
        api.bidderTenders(),
        api.bidderBids(),
      ]);
      setTenders(tList || []);
      setMyBids(bList || []);
    } catch (err) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Shell>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold text-ink">GeM Procurement Opportunities</h1>
          <p className="text-sm text-slate mt-0.5">
            Published tenders open for AI-verified bid submission with deterministic compliance checking.
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-failBg text-fail text-xs p-3 rounded-lg border border-fail/20 mb-6">
          {error}
        </div>
      )}

      {/* Published Tenders */}
      <div className="space-y-4 mb-10">
        <h2 className="text-base font-bold text-ink flex items-center gap-2">
          <span>Active Published Tenders</span>
          <span className="text-xs font-semibold bg-accent/10 text-accent px-2 py-0.5 rounded-full">
            {tenders.length} Open
          </span>
        </h2>

        <div className="grid grid-cols-1 gap-4">
          {tenders.map((t) => {
            const existingBid = myBids.find((b) => b.tender?.id === t.id);

            return (
              <div
                key={t.id}
                className="bg-card border border-line hover:border-accent/40 rounded-card p-5 transition-all shadow-xs flex flex-wrap items-center justify-between gap-4"
              >
                <div className="flex-1 min-w-[280px]">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-2 py-0.5 rounded">
                      {t.organization}
                    </span>
                    <span className="text-xs font-mono text-slate">Tender: {t.id} · v{t.version}</span>
                  </div>
                  <h3 className="text-base font-bold text-ink">{t.title}</h3>
                  <div className="flex items-center gap-4 mt-2 text-xs text-slate">
                    <span>📋 {t.clause_count || 3} Statutory & Technical Clauses</span>
                    <span>📂 {t.required_documents?.length || 5} Document Slots Required</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {existingBid ? (
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="text-[11px] text-slate">Your Submission</div>
                        <div className="mt-0.5"><StatusBadge status={existingBid.status} /></div>
                      </div>
                      <button
                        onClick={() => navigate(`/bidder/status/${existingBid.id}`)}
                        className="bg-accent/10 hover:bg-accent/20 text-accent font-semibold text-xs px-4 py-2.5 rounded-lg transition-colors"
                      >
                        Track Status →
                      </button>
                    </div>
                  ) : null}

                  <button
                    onClick={() => navigate(`/bidder/tenders/${t.id}`)}
                    className="bg-accent hover:bg-accent2 text-white font-medium text-xs px-4 py-2.5 rounded-lg transition-colors shadow-xs"
                  >
                    View Details & Apply →
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Submissions Section */}
      {myBids.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-base font-bold text-ink">My Submitted & In-Progress Bids</h2>
          <div className="bg-card border border-line rounded-card overflow-hidden shadow-xs">
            <table className="w-full text-left text-xs">
              <thead className="bg-canvas border-b border-line text-slate uppercase font-semibold">
                <tr>
                  <th className="px-5 py-3">Bid ID</th>
                  <th className="px-5 py-3">Bidding Entity</th>
                  <th className="px-5 py-3">Tender</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">AI Verdict</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {myBids.map((b) => (
                  <tr key={b.id} className="hover:bg-canvas/50 transition-colors">
                    <td className="px-5 py-3 font-mono font-medium text-ink">{b.id}</td>
                    <td className="px-5 py-3 font-medium text-ink">{b.bidder_org_name}</td>
                    <td className="px-5 py-3 text-slate">{b.tender?.title}</td>
                    <td className="px-5 py-3"><StatusBadge status={b.status} /></td>
                    <td className="px-5 py-3"><StatusBadge status={b.compliance_status} /></td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => navigate(`/bidder/status/${b.id}`)}
                        className="text-accent hover:underline font-semibold"
                      >
                        Open Tracker →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Shell>
  );
}
