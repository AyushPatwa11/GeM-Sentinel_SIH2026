import React from "react";
import StatusBadge from "../StatusBadge.jsx";
import { Activity } from "lucide-react";

export default function ActivityTimeline({ items }) {
  if (items.length === 0) {
    return (
      <div className="p-8 bg-slate-50 rounded-lg border border-slate-200 text-center">
        <Activity className="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p className="text-slate-600 text-sm">No recent activity</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item, i) => {
        const Icon = item.icon;
        return (
          <div key={i} className="flex items-start gap-3 pb-3 border-b border-slate-100 last:border-0 last:pb-0">
            <div className="mt-1">
              <Icon className="w-4 h-4 text-slate-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-900">{item.title}</p>
              <p className="text-xs text-slate-500">{item.time}</p>
            </div>
            {item.status && <StatusBadge status={item.status} size="xs" />}
          </div>
        );
      })}
    </div>
  );
}
