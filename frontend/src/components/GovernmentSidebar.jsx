import React from "react";
import { Link } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  ClipboardList,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  ChevronDown,
  Home,
} from "lucide-react";

export default function GovernmentSidebar({ userRole, isOpen, onClose }) {
  const [expandedSections, setExpandedSections] = React.useState({
    officer: userRole === "officer",
    bidder: userRole === "bidder",
  });

  const toggleSection = (section) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const officerServices = [
    { label: "Dashboard", icon: LayoutDashboard, path: "/officer" },
    { label: "All Bids", icon: FileText, path: "/officer/bids" },
    { label: "Audit Trail", icon: ClipboardList, path: "/officer/audit" },
  ];

  const bidderServices = [
    { label: "Available Tenders", icon: FileText, path: "/bidder" },
    { label: "My Bids", icon: CheckCircle, path: "/bidder/status" },
    { label: "Readiness Check", icon: AlertCircle, path: "/bidder/readiness" },
  ];

  const isOfficer = userRole === "officer";
  const services = isOfficer ? officerServices : bidderServices;

  return (
    <>
      {/* Backdrop (Mobile) */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:relative left-0 top-0 pt-20 md:pt-0 h-screen w-64 bg-white border-r border-line transition-transform duration-300 z-30 md:z-0 overflow-y-auto ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <nav className="py-4">
          {/* Home Link */}
          <Link
            to="/"
            className="px-4 py-3 flex items-center gap-3 text-govDark hover:bg-govLight hover:text-govBlue transition font-medium text-sm"
            onClick={onClose}
          >
            <Home size={18} />
            Home
          </Link>

          {/* Officer Section */}
          {isOfficer && (
            <div className="mt-2">
              <button
                onClick={() => toggleSection("officer")}
                className="w-full px-4 py-3 flex items-center justify-between text-govDark hover:bg-govLight hover:text-govBlue transition font-semibold text-sm"
              >
                <span>Officer Portal</span>
                <ChevronDown
                  size={16}
                  className={`transform transition ${
                    expandedSections.officer ? "rotate-180" : ""
                  }`}
                />
              </button>
              {expandedSections.officer && (
                <div className="pl-4 space-y-1">
                  {officerServices.map((service) => (
                    <Link
                      key={service.path}
                      to={service.path}
                      className="px-4 py-2 flex items-center gap-3 text-slate-600 hover:text-govBlue hover:bg-govLight transition text-sm rounded-md"
                      onClick={onClose}
                    >
                      <service.icon size={16} />
                      {service.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Bidder Section */}
          {!isOfficer && (
            <div className="mt-2">
              <button
                onClick={() => toggleSection("bidder")}
                className="w-full px-4 py-3 flex items-center justify-between text-govDark hover:bg-govLight hover:text-govBlue transition font-semibold text-sm"
              >
                <span>Bidder Portal</span>
                <ChevronDown
                  size={16}
                  className={`transform transition ${
                    expandedSections.bidder ? "rotate-180" : ""
                  }`}
                />
              </button>
              {expandedSections.bidder && (
                <div className="pl-4 space-y-1">
                  {bidderServices.map((service) => (
                    <Link
                      key={service.path}
                      to={service.path}
                      className="px-4 py-2 flex items-center gap-3 text-slate-600 hover:text-govBlue hover:bg-govLight transition text-sm rounded-md"
                      onClick={onClose}
                    >
                      <service.icon size={16} />
                      {service.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}


        </nav>
      </aside>
    </>
  );
}
