import React from "react";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";

const variantConfig = {
  error: {
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
    iconColor: "text-red-600",
    textColor: "text-red-900",
    subColor: "text-red-700",
    icon: AlertCircle,
  },
  warning: {
    bgColor: "bg-amber-50",
    borderColor: "border-amber-200",
    iconColor: "text-amber-600",
    textColor: "text-amber-900",
    subColor: "text-amber-700",
    icon: AlertCircle,
  },
  info: {
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    iconColor: "text-blue-600",
    textColor: "text-blue-900",
    subColor: "text-blue-700",
    icon: Info,
  },
  success: {
    bgColor: "bg-green-50",
    borderColor: "border-green-200",
    iconColor: "text-green-600",
    textColor: "text-green-900",
    subColor: "text-green-700",
    icon: CheckCircle2,
  },
};

export default function AlertBox({ variant = "info", title, description, action, actionLabel }) {
  const config = variantConfig[variant];
  const Icon = config.icon;

  return (
    <div className={`p-4 ${config.bgColor} border ${config.borderColor} rounded-lg`}>
      <div className="flex items-start gap-3">
        <Icon className={`${config.iconColor} w-5 h-5 flex-shrink-0 mt-0.5`} />
        <div className="flex-1">
          <h3 className={`font-semibold ${config.textColor} text-sm`}>{title}</h3>
          {description && <p className={`text-xs ${config.subColor} mt-1`}>{description}</p>}
        </div>
      </div>
      {action && (
        <button
          onClick={action}
          className={`w-full mt-3 px-3 py-2 text-xs font-semibold rounded-lg transition-colors ${
            variant === "error"
              ? "bg-red-600 hover:bg-red-700 text-white"
              : variant === "warning"
              ? "bg-amber-600 hover:bg-amber-700 text-white"
              : variant === "success"
              ? "bg-green-600 hover:bg-green-700 text-white"
              : "bg-blue-600 hover:bg-blue-700 text-white"
          }`}
        >
          {actionLabel || "Action"}
        </button>
      )}
    </div>
  );
}
