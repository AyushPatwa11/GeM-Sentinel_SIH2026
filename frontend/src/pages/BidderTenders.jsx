import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import { api } from "../lib/api.js";

export default function BidderTenders() {
  const [tenders, setTenders] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.bidderTenders().then(setTenders);
  }, []);

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold text-ink mb-1">Published tenders</h1>
      <p className="text-sm text-slate mb-6">Review requirements and check your submission readiness before submitting.</p>

      <div className="space-y-3">
        {tenders?.map((t) => (
          <div key={t.id} className="bg-card border border-line rounded-card px-5 py-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-ink">{t.title}</div>
              <div className="text-xs text-slate mt-1">{t.organization} · v{t.version}</div>
            </div>
            <button
              onClick={() => navigate("/bidder/readiness")}
              className="text-xs font-medium text-white bg-accent hover:bg-accent2 px-3.5 py-2 rounded-lg transition-colors"
            >
              Check readiness
            </button>
          </div>
        ))}
      </div>
    </Shell>
  );
}
