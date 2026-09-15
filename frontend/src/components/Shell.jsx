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
    <div className="min-h-screen flex bg-gray-50 font-body text-gray-900 antialiased">
      {/* Sidebar - Compact */}
      <aside className="w-56 shrink-0 bg-slate-900 text-white flex flex-col justify-between border-r border-slate-800 select-none">
        <div>
          {/* Logo Brand Header - Compact */}
          <div className="px-4 py-4 flex items-center gap-2.5 border-b border-slate-800">
            <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center shrink-0 shadow-md">
              <ShieldCheck className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="font-bold text-sm tracking-tight leading-tight">GeM Sentinel</div>
              <div className="text-[10px] text-slate-400 font-medium">Bid Verification</div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-2 py-4 space-y-1">
            {links.map((l) => {
              const Icon = l.icon;
              return (
                <NavLink
                  key={l.to}
                  to={l.to}
                  end={l.to === "/officer" || l.to === "/bidder"}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all text-slate-300 hover:bg-slate-800 hover:text-white"
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span className="truncate">{l.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* User Session Footer - Compact */}
        <div className="p-3 m-2 rounded-lg bg-slate-800 border border-slate-700">
          <div className="text-[9px] uppercase font-mono font-semibold text-slate-400 tracking-wider">
            {isOfficer ? "Officer" : "Bidder"}
          </div>
          <div className="text-xs font-bold text-white truncate mt-1">
            {session?.name || (isOfficer ? "Officer Sharma" : "Bidder")}
          </div>
          <div className="text-[10px] text-slate-400 truncate font-mono mt-0.5">
            {session?.email || (isOfficer ? "officer@gem.gov.in" : "bidder@gem.gov.in")}
          </div>

          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="w-full mt-2 flex items-center justify-center gap-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-700 hover:bg-slate-600 py-1.5 rounded transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area - Full Width */}
      <main className="flex-1 min-w-0 flex flex-col bg-white">
        <div className="w-full px-6 lg:px-8 py-6 overflow-auto">{children}</div>
      </main>
    </div>
  );
}
