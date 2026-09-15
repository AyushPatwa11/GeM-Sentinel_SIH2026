import React from "react";
import { AlertCircle, CheckCircle, Info, AlertTriangle } from "lucide-react";

export default function Alert({ variant = "info", title, children, className = "" }) {
  const variants = {
    info: {
      bg: "bg-blue-50 border-blue-200",
      icon: "text-blue-600",
      title: "text-blue-900",
      text: "text-blue-800",
      Icon: Info,
    },
    success: {
      bg: "bg-green-50 border-green-200",
      icon: "text-green-600",
      title: "text-green-900",
      text: "text-green-800",
      Icon: CheckCircle,
    },
    warning: {
      bg: "bg-amber-50 border-amber-200",
      icon: "text-amber-600",
      title: "text-amber-900",
      text: "text-amber-800",
      Icon: AlertTriangle,
    },
    error: {
      bg: "bg-red-50 border-red-200",
      icon: "text-red-600",
      title: "text-red-900",
      text: "text-red-800",
      Icon: AlertCircle,
    },
  };

  const style = variants[variant] || variants.info;

  return (
    <div className={`rounded-lg border p-4 ${style.bg} ${className}`}>
      <div className="flex items-start gap-3">
        <style.Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${style.icon}`} />
        <div>
          {title && <h3 className={`font-semibold ${style.title}`}>{title}</h3>}
          <div className={style.text}>{children}</div>
        </div>
      </div>
    </div>
  );
}
