import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";
import { LayoutDashboard, FileText, History, ShieldCheck, LogOut, CheckCircle2 } from "lucide-react";

export default function Shell({ children }) {
  const { session, logout } = useAuth();
  const navigate = useNavigate();
  const isOfficer = session?.role === "officer";

  const links = isOfficer
    ? [
        { to: "/officer", label: "Dashboard", icon: LayoutDashboard },
        { to: "/officer/audit", label: "Audit Trail", icon: History },
      ]
    : [
        { to: "/bidder", label: "Tenders", icon: FileText },
        { to: "/bidder/readiness", label: "Readiness Check", icon: CheckCircle2 },
      ];

  return (
    <div className="min-h-screen flex bg-canvas font-body text-ink antialiased selection:bg-accent/20">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 bg-ink text-white flex flex-col justify-between border-r border-white/10 select-none">
        <div>
          {/* Logo Brand Header */}
          <div className="px-6 py-6 flex items-center gap-3 border-b border-white/10">
            <div className="w-9 h-9 rounded-xl bg-accent flex items-center justify-center shrink-0 shadow-md shadow-accent/30">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-display font-bold text-base tracking-tight leading-tight">GeM Sentinel</div>
              <div className="text-[11px] text-white/50 font-medium">Procurement Verification</div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-3 py-5 space-y-1.5">
            {links.map((l) => {
              const Icon = l.icon;
              return (
                <NavLink
                  key={l.to}
                  to={l.to}
                  end={l.to === "/officer" || l.to === "/bidder"}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? "bg-accent text-white shadow-sm shadow-accent/30 font-semibold"
                        : "text-white/70 hover:bg-white/5 hover:text-white"
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{l.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* User Session Footer */}
        <div className="p-4 m-3 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
          <div className="text-[10px] uppercase font-mono font-semibold text-white/40 tracking-wider">
            {isOfficer ? "Procurement Officer" : "Bidder Account"}
          </div>
          <div className="text-sm font-bold text-white truncate mt-0.5">
            {session?.name || (isOfficer ? "Officer Sharma" : "Bidder Portal")}
          </div>
          <div className="text-[11px] text-white/50 truncate font-mono mt-0.5">
            {session?.email || (isOfficer ? "po.sharma@gem.gov.in" : "bidder@gem.gov.in")}
          </div>

          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="w-full mt-3 flex items-center justify-center gap-2 text-xs font-medium text-white/70 hover:text-white bg-white/5 hover:bg-white/10 py-1.5 rounded-lg border border-white/10 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 flex flex-col">
        <div className="max-w-7xl w-full mx-auto px-6 lg:px-10 py-8">{children}</div>
      </main>
    </div>
  );
}
