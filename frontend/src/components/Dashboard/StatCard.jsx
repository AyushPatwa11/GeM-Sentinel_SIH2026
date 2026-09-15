import React from "react";

const colorVariants = {
  blue: "bg-gradient-to-br from-blue-50 to-blue-25 border-blue-200",
  green: "bg-gradient-to-br from-green-50 to-green-25 border-green-200",
  amber: "bg-gradient-to-br from-amber-50 to-amber-25 border-amber-200",
  red: "bg-gradient-to-br from-red-50 to-red-25 border-red-200",
};

const iconColorVariants = {
  blue: "text-blue-600",
  green: "text-green-600",
  amber: "text-amber-600",
  red: "text-red-600",
};

export default function StatCard({ icon: Icon, value, label, subtext, color = "blue" }) {
  return (
    <div className={`border ${colorVariants[color]} rounded-lg p-5 bg-white hover:shadow-sm transition-shadow`}>
      <div className="flex items-start justify-between mb-3">
        <Icon className={`${iconColorVariants[color]} w-5 h-5`} />
      </div>
      <div className="text-3xl font-bold text-slate-900 mb-1">{value}</div>
      <div className="text-sm font-semibold text-slate-700">{label}</div>
      {subtext && <div className="text-xs text-slate-500 mt-1">{subtext}</div>}
    </div>
  );
}
