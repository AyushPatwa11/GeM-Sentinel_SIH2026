import React, { useState } from "react";
import GovernmentHeader from "./GovernmentHeader";
import GovernmentSidebar from "./GovernmentSidebar";
import GovernmentFooter from "./GovernmentFooter";

export default function GovernmentLayout({ children, user, userRole, onLogout }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleSidebarToggle = () => setIsSidebarOpen((p) => !p);
  const handleSidebarClose = () => setIsSidebarOpen(false);

  return (
    <div className="min-h-screen bg-govLight flex flex-col">
      {/* Fixed Header — height ~88px (blue banner 40px + nav 48px) */}
      <GovernmentHeader
        user={user}
        onLogout={onLogout}
        isSidebarOpen={isSidebarOpen}
        onSidebarToggle={handleSidebarToggle}
      />

      {/* Push content below the fixed header (Banner 38px + Header 60px) */}
      <div className="flex flex-1 pt-[98px]">
        {/* Sidebar: fixed on mobile, sticky column on desktop */}
        <GovernmentSidebar
          userRole={userRole}
          isOpen={isSidebarOpen}
          onClose={handleSidebarClose}
        />

        {/* Main scrollable content */}
        <main className="flex-1 min-w-0 flex flex-col">
          {/* Breadcrumb strip */}
          <BreadcrumbStrip />

          <div className="flex-1 px-4 md:px-8 py-6">
            {children}
          </div>

          <GovernmentFooter />
        </main>
      </div>
    </div>
  );
}

// Inline breadcrumb – no more import cycle, keeps it simple
import { Link, useLocation } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

function BreadcrumbStrip() {
  const location = useLocation();
  const pathname = location.pathname;

  if (pathname === "/" || pathname === "/login") return null;

  const labels = {
    officer: "Officer Dashboard",
    bids: "Bids",
    audit: "Audit Trail",
    bidder: "Bidder Portal",
    tenders: "Tenders",
    status: "Bid Status",
    readiness: "Readiness Check",
    apply: "Apply",
    create: "Create Tender",
  };

  const parts = pathname.split("/").filter(Boolean);
  const crumbs = [{ label: "Home", path: "/" }];
  let currentPath = "";
  parts.forEach((part) => {
    currentPath += `/${part}`;
    const isUUID = /^[0-9a-f-]{36}$/i.test(part);
    if (!isUUID) {
      crumbs.push({
        label: labels[part] || part.charAt(0).toUpperCase() + part.slice(1),
        path: currentPath,
      });
    }
  });

  return (
    <nav className="bg-white border-b border-line px-4 md:px-8 py-2.5" aria-label="Breadcrumb">
      <ol className="flex items-center gap-1.5 text-xs flex-wrap">
        {crumbs.map((crumb, i) => (
          <React.Fragment key={crumb.path}>
            {i > 0 && <ChevronRight size={12} className="text-slate-400 shrink-0" />}
            <li>
              {i === crumbs.length - 1 ? (
                <span className="font-semibold text-govDark">{crumb.label}</span>
              ) : (
                <Link to={crumb.path} className="text-govBlue hover:text-govSaffron transition font-medium flex items-center gap-0.5">
                  {i === 0 && <Home size={12} className="inline mr-0.5" />}
                  {crumb.label}
                </Link>
              )}
            </li>
          </React.Fragment>
        ))}
      </ol>
    </nav>
  );
}
