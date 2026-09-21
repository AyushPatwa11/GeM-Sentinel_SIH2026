import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  ArrowRight,
  RefreshCw,
} from "lucide-react";

// Inline TenderCard component
const TenderCard = ({ tender, existingBid, onViewDetails, onApply }) => {
  const clauseCount = tender.eligibility_criteria?.length || 0;
  const closingDate = new Date(tender.bid_submission_end_date);
  const daysLeft = Math.ceil((closingDate - new Date()) / (1000 * 60 * 60 * 24));

  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow">
      <div className="space-y-3">
        <div>
          <p className="text-xs font-mono text-slate-500 mb-1">{tender.id?.substring(0, 8)}...</p>
          <h3 className="text-sm font-semibold text-slate-900">{tender.title}</h3>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs text-slate-600">
          <div>
            <span className="text-slate-500">Organization</span>
            <p className="font-medium text-slate-900">{tender.organization_name || "—"}</p>
          </div>
          <div>
            <span className="text-slate-500">Clauses</span>
            <p className="font-medium text-slate-900">{clauseCount}</p>
          </div>
          <div className="col-span-2">
            <span className="text-slate-500">Closing</span>
            <p className="font-medium text-slate-900">
              {closingDate.toLocaleDateString()} ({daysLeft} days left)
            </p>
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <button
            onClick={() => onViewDetails(tender.id)}
            className="flex-1 px-3 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition-colors"
          >
            View Details
          </button>
          {!existingBid && (
            <button
              onClick={() => onApply(tender.id)}
              className="flex-1 px-3 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors"
            >
              Apply
            </button>
          )}
          {existingBid && (
            <button
              onClick={() => onViewDetails(tender.id)}
              className="flex-1 px-3 py-2 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded transition-colors"
            >
              View Bid
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Inline BidRow component
const BidRow = ({ bid, onViewDetails }) => (
  <tr className="border-b border-slate-200 hover:bg-slate-50 transition-colors">
    <td className="px-4 py-3">
      <span className="font-mono text-xs text-slate-900 font-medium">
        {bid.tender?.title?.substring(0, 30) || "Tender"}
      </span>
    </td>
    <td className="px-4 py-3 text-xs text-slate-600">
      {bid.id?.substring(0, 8)}...
    </td>
    <td className="px-4 py-3">
      <StatusBadge status={bid.status} size="xs" />
    </td>
    <td className="px-4 py-3">
      <StatusBadge status={bid.compliance_status} size="xs" />
    </td>
    <td className="px-4 py-3 text-right">
      <button
        onClick={() => onViewDetails(bid.id)}
        className="text-blue-600 hover:text-blue-700 font-medium text-xs flex items-center gap-1 ml-auto"
      >
        View <ArrowRight className="w-3 h-3" />
      </button>
    </td>
  </tr>
);

export default function BidderTenders() {
  const { session } = useAuth();
  const [tenders, setTenders] = useState([]);
  const [myBids, setMyBids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function loadData() {
    try {
      // Load tenders and bids independently so a bids auth error
      // does not prevent tenders from being displayed
      const [tResult, bResult] = await Promise.allSettled([
        api.bidderTenders(),
        api.bidderBids(),
      ]);

      if (tResult.status === "fulfilled") {
        setTenders(tResult.value || []);
      } else {
        setError(tResult.reason?.message || "Failed to load tenders");
      }

      if (bResult.status === "fulfilled") {
        setMyBids(bResult.value || []);
      }
      // Silently ignore bids auth error — user may not have any bids
    } catch (err) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 6000);
    return () => clearInterval(interval);
  }, []);

  // Bid categorization
  const clarificationNeeded = myBids.filter(
    (b) => b.status === "CLARIFICATION" || b.status === "CLARIFICATION_REQUIRED"
  );
  const activeBids = myBids.filter((b) => b.status === "DRAFT" || b.status === "SUBMITTED");
  const underReview = myBids.filter((b) => b.status === "VERIFYING" || b.status === "REVIEW");
  const completed = myBids.filter((b) => b.status === "DECIDED");

  return (
    <>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-600 text-sm mt-1">
            Welcome, {session?.name || "Bidder"}
          </p>
        </div>

        {/* Error State */}
        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-900">{error}</p>
              <button
                onClick={loadData}
                className="text-xs font-medium text-red-600 hover:text-red-700 mt-2"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <RefreshCw className="w-6 h-6 text-blue-600 animate-spin mx-auto mb-2" />
              <p className="text-slate-600 text-sm">Loading dashboard…</p>
            </div>
          </div>
        )}

        {!loading && (
          <div className="space-y-6">
            {/* Action Required Alert */}
            {clarificationNeeded.length > 0 && (
              <div className="border-l-4 border-amber-500 bg-amber-50 p-4 rounded">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-semibold text-amber-900">Action Required</p>
                    <p className="text-xs text-amber-800 mt-1">
                      Officer requested clarification on {clarificationNeeded.length} bid{clarificationNeeded.length !== 1 ? "s" : ""}. Please respond as soon as possible.
                    </p>
                  </div>
                  <button
                    onClick={() => navigate(`/bidder/status/${clarificationNeeded[0].id}`)}
                    className="text-xs font-medium text-amber-700 hover:text-amber-900 flex-shrink-0"
                  >
                    Respond →
                  </button>
                </div>
              </div>
            )}

            {/* Bid Status Summary - Only show if myBids.length > 0 */}
            {myBids.length > 0 && (
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-xs text-blue-600 font-medium">Active</p>
                  <p className="text-lg font-bold text-blue-900">{activeBids.length}</p>
                </div>
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-xs text-amber-600 font-medium">Under Review</p>
                  <p className="text-lg font-bold text-amber-900">{underReview.length}</p>
                </div>
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-xs text-green-600 font-medium">Completed</p>
                  <p className="text-lg font-bold text-green-900">{completed.length}</p>
                </div>
              </div>
            )}

            {/* Available Tenders */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-900">Available Tenders</h2>
                <span className="text-xs font-medium text-slate-500">
                  {tenders.length} open
                </span>
              </div>

              {tenders.length === 0 ? (
                <div className="p-8 bg-slate-50 rounded-lg border border-slate-200 text-center">
                  <FileText className="w-6 h-6 text-slate-300 mx-auto mb-2" />
                  <p className="text-sm text-slate-600 font-medium">No active tenders</p>
                  <p className="text-xs text-slate-500 mt-1">Check back soon</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {tenders.map((t) => {
                    const existingBid = myBids.find(
                      (b) => b.tender_version_id === t.id || b.tender?.id === t.id
                    );
                    return (
                      <TenderCard
                        key={t.id}
                        tender={t}
                        existingBid={existingBid}
                        onViewDetails={(tenderId) =>
                          navigate(`/bidder/tenders/${tenderId}`)
                        }
                        onApply={(tenderId) => navigate(`/bidder/tenders/${tenderId}`)}
                      />
                    );
                  })}
                </div>
              )}
            </div>

            {/* My Bids Table - Only show if myBids.length > 0 */}
            {myBids.length > 0 && (
              <div className="space-y-3">
                <h2 className="text-sm font-semibold text-slate-900">My Bids</h2>
                <div className="border border-slate-200 rounded-lg overflow-hidden bg-white">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 border-b border-slate-200">
                        <tr>
                          <th className="px-4 py-3 text-left font-semibold text-slate-900 text-xs">
                            Tender
                          </th>
                          <th className="px-4 py-3 text-left font-semibold text-slate-900 text-xs">
                            Bid ID
                          </th>
                          <th className="px-4 py-3 text-left font-semibold text-slate-900 text-xs">
                            Status
                          </th>
                          <th className="px-4 py-3 text-left font-semibold text-slate-900 text-xs">
                            Compliance
                          </th>
                          <th className="px-4 py-3 text-right font-semibold text-slate-900 text-xs">
                            Action
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {myBids.map((b) => (
                          <BidRow
                            key={b.id}
                            bid={b}
                            onViewDetails={(bidId) =>
                              navigate(`/bidder/status/${bidId}`)
                            }
                          />
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Empty State - Only show if myBids.length === 0 && tenders.length > 0 */}
            {myBids.length === 0 && tenders.length > 0 && (
              <div className="p-8 bg-slate-50 rounded-lg border border-slate-200 text-center">
                <CheckCircle2 className="w-6 h-6 text-slate-400 mx-auto mb-2" />
                <p className="text-sm text-slate-600 font-medium">No active bids yet</p>
                <p className="text-xs text-slate-500 mt-1">
                  Explore available tenders and submit your first bid above
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
