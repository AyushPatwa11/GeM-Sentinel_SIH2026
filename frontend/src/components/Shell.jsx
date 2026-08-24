import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";

const ICONS = {
  dashboard: "M4 5h7v7H4V5Zm9 0h7v4h-7V5ZM4 14h7v5H4v-5Zm9-3h7v8h-7v-8Z",
  tender: "M6 3h9l3 3v15H6V3Zm9 0v3h3M9 12h6M9 15h6M9 9h3",
  audit: "M12 3a9 9 0 1 0 9 9M12 3v9l6 3",
};

function Icon({ name, className = "w-4 h-4" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d={ICONS[name]} />
    </svg>
  );
}

export default function Shell({ children }) {
  const { session, logout } = useAuth();
  const navigate = useNavigate();
  const isOfficer = session?.role === "officer";

  const links = isOfficer
    ? [
        { to: "/officer", label: "Dashboard", icon: "dashboard" },
        { to: "/officer/audit", label: "Audit Trail", icon: "audit" },
      ]
    : [
        { to: "/bidder", label: "Tenders", icon: "tender" },
        { to: "/bidder/readiness", label: "Readiness Check", icon: "dashboard" },
      ];

  return (
    <div className="min-h-screen flex bg-canvas">
      <aside className="w-64 shrink-0 bg-ink text-white flex flex-col">
        <div className="px-5 py-6 flex items-center gap-2.5 border-b border-white/10">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center shrink-0">
            <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" className="w-4.5 h-4.5">
              <path d="M12 2 4 6v6c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V6l-8-4Z" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </div>
          <div>
            <div className="font-display font-semibold text-[15px] leading-tight">GeM Sentinel</div>
            <div className="text-[11px] text-white/50 leading-tight">Bid Compliance Verifier</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/officer" || l.to === "/bidder"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive ? "bg-accent text-white" : "text-white/70 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <Icon name={l.icon} />
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-white/10">
          <div className="text-xs text-white/40 uppercase tracking-wide mb-1">Signed in as</div>
          <div className="text-sm font-medium mb-3">{session?.name} · {isOfficer ? "Procurement Officer" : "Bidder"}</div>
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="text-xs text-white/60 hover:text-white transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <div className="max-w-6xl mx-auto px-8 py-8">{children}</div>
      </main>
    </div>
  );
}
