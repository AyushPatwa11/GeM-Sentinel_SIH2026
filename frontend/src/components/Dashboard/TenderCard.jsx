import React from "react";
import StatusBadge from "../StatusBadge.jsx";
import { FileText, Calendar, ArrowRight } from "lucide-react";

export default function TenderCard({ tender, existingBid, onViewDetails, onTrackStatus }) {
  return (
    <div className="border border-slate-200 rounded-lg p-5 bg-white hover:shadow-md hover:border-blue-300 transition-all duration-200">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="text-xs font-semibold px-2 py-1 bg-blue-100 text-blue-700 rounded">
              {tender.organization}
            </span>
            <span className="text-xs font-mono text-slate-500">{tender.id?.substring(0, 12)}</span>
          </div>
          <h3 className="text-base font-semibold text-slate-900 leading-tight">{tender.title}</h3>
        </div>
      </div>

      <div className="space-y-2 mb-4 text-sm text-slate-600">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-slate-400" />
          <span>{tender.clause_count || 3} Clauses</span>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span>Closes: {tender.closing_date || "TBD"}</span>
        </div>
      </div>

      <div className="flex items-center gap-2 pt-3 border-t border-slate-100">
        {existingBid ? (
          <>
            <div className="flex-1">
              <div className="text-xs text-slate-500 mb-1">Your Bid</div>
              <div className="flex items-center gap-2">
                <StatusBadge status={existingBid.status} size="xs" />
              </div>
            </div>
            <button
              onClick={() => onTrackStatus(existingBid.id)}
              className="px-3 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors flex items-center gap-1"
            >
              Track <ArrowRight className="w-3 h-3" />
            </button>
          </>
        ) : null}
        <button
          onClick={() => onViewDetails(tender.id)}
          className="px-4 py-2 text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-1"
        >
          Apply <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
