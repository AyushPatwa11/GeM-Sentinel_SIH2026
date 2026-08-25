import React from "react";
import { CheckCircle2, XCircle, AlertTriangle, Clock, ShieldAlert, ShieldCheck, MinusCircle, FileCheck } from "lucide-react";

const CONFIG = {
  PASS: { cls: "bg-passBg/80 text-pass border-pass/30", icon: CheckCircle2 },
  VERIFIED: { cls: "bg-passBg/80 text-pass border-pass/30", icon: ShieldCheck },
  COMPLIANT: { cls: "bg-passBg/80 text-pass border-pass/30", icon: CheckCircle2 },
  SATISFIED: { cls: "bg-passBg/80 text-pass border-pass/30", icon: CheckCircle2 },
  LOW: { cls: "bg-passBg/80 text-pass border-pass/30", icon: CheckCircle2 },

  FAIL: { cls: "bg-failBg/80 text-fail border-fail/30", icon: XCircle },
  NON_COMPLIANT: { cls: "bg-failBg/80 text-fail border-fail/30", icon: ShieldAlert },
  MISSING: { cls: "bg-failBg/80 text-fail border-fail/30", icon: XCircle },
  HIGH: { cls: "bg-failBg/80 text-fail border-fail/30", icon: ShieldAlert },

  REVIEW: { cls: "bg-reviewBg/80 text-review border-review/30", icon: AlertTriangle },
  WEAK_EVIDENCE: { cls: "bg-reviewBg/80 text-review border-review/30", icon: AlertTriangle },
  NEEDS_CLARIFICATION: { cls: "bg-reviewBg/80 text-review border-review/30", icon: AlertTriangle },
  CLARIFICATION_REQUIRED: { cls: "bg-reviewBg/80 text-review border-review/30", icon: AlertTriangle },
  COMPLIANT_WITH_FLAGS: { cls: "bg-reviewBg/80 text-review border-review/30", icon: AlertTriangle },
  MEDIUM: { cls: "bg-reviewBg/80 text-review border-review/30", icon: AlertTriangle },
  PENDING: { cls: "bg-canvas text-slate border-line", icon: Clock },
  SUBMITTED: { cls: "bg-accent/10 text-accent border-accent/30", icon: FileCheck },
  DRAFT: { cls: "bg-canvas text-slate border-line", icon: Clock },

  WAIVED: { cls: "bg-accent/10 text-accent border-accent/30", icon: CheckCircle2 },
  NOT_EVALUATED: { cls: "bg-canvas text-slate border-line", icon: MinusCircle },
};

export default function StatusBadge({ status, label, showIcon = true, size = "sm" }) {
  const norm = (status || "").toUpperCase();
  const cfg = CONFIG[norm] || { cls: "bg-canvas text-slate border-line", icon: MinusCircle };
  const Icon = cfg.icon;

  const sizeClasses = size === "xs" 
    ? "px-2 py-0.5 text-[10px] gap-1"
    : "px-2.5 py-1 text-xs gap-1.5";

  const iconSizes = size === "xs" ? "w-3 h-3" : "w-3.5 h-3.5";

  return (
    <span className={`inline-flex items-center font-medium rounded-full border shadow-xs ${cfg.cls} ${sizeClasses}`}>
      {showIcon && <Icon className={`shrink-0 ${iconSizes}`} />}
      <span>{label || status?.replaceAll("_", " ")}</span>
    </span>
  );
}
