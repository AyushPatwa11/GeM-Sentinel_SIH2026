import React from "react";

const STYLES = {
  PASS: "bg-passBg text-pass",
  VERIFIED: "bg-passBg text-pass",
  COMPLIANT: "bg-passBg text-pass",
  SATISFIED: "bg-passBg text-pass",
  LOW: "bg-passBg text-pass",

  FAIL: "bg-failBg text-fail",
  NON_COMPLIANT: "bg-failBg text-fail",
  MISSING: "bg-failBg text-fail",
  HIGH: "bg-failBg text-fail",

  REVIEW: "bg-reviewBg text-review",
  WEAK_EVIDENCE: "bg-reviewBg text-review",
  NEEDS_CLARIFICATION: "bg-reviewBg text-review",
  CLARIFICATION_REQUIRED: "bg-reviewBg text-review",
  COMPLIANT_WITH_FLAGS: "bg-reviewBg text-review",
  MEDIUM: "bg-reviewBg text-review",
  PENDING: "bg-reviewBg text-review",

  WAIVED: "bg-[#EAF0FF] text-accent2",
  NOT_EVALUATED: "bg-line text-slate",
};

export default function StatusBadge({ status, label }) {
  const cls = STYLES[status] || "bg-line text-slate";
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${cls}`}>
      {label || status?.replaceAll("_", " ")}
    </span>
  );
}
