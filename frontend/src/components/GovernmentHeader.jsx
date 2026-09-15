import React, { useState } from "react";
import { Menu, X, Search, LogOut, User } from "lucide-react";

export default function GovernmentHeader({ user, onLogout, isSidebarOpen, onSidebarToggle }) {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-line shadow-sm">
      {/* Official Government Banner */}
      <div className="bg-govBlue text-white px-4 py-2 text-center text-sm font-semibold">
        Government of India — Ministry of Petroleum & Natural Gas
      </div>

      {/* Main Header */}
      <div className="bg-white px-4 py-3 flex items-center justify-between">
        {/* Left: Logo & Portal Title */}
        <div className="flex items-center gap-3">
          {/* Hamburger for Sidebar (Mobile) */}
          <button
            onClick={onSidebarToggle}
            className="md:hidden p-1 hover:bg-canvas rounded-md transition"
            aria-label="Toggle sidebar"
          >
            {isSidebarOpen ? (
              <X size={24} className="text-govBlue" />
            ) : (
              <Menu size={24} className="text-govBlue" />
            )}
          </button>

          {/* Portal Logo & Name */}
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-govSaffron rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">🛡️</span>
            </div>
            <div className="hidden sm:block">
              <div className="text-lg font-bold text-govBlue">GeM Sentinel</div>
              <div className="text-xs text-slate-600">Bid Compliance Portal</div>
            </div>
          </div>
        </div>

        {/* Center: Horizontal Navigation (Desktop only) */}
        <nav className="hidden lg:flex items-center gap-6 mx-auto">
          <a href="/" className="text-sm font-medium text-govDark hover:text-govBlue transition">
            Home
          </a>
          <a href="#" className="text-sm font-medium text-govDark hover:text-govBlue transition">
            Services
          </a>
          <a href="#" className="text-sm font-medium text-govDark hover:text-govBlue transition">
            Schemes
          </a>
          <a href="#" className="text-sm font-medium text-govDark hover:text-govBlue transition">
            News
          </a>
          <a href="#" className="text-sm font-medium text-govDark hover:text-govBlue transition">
            Help
          </a>
        </nav>

        {/* Right: Search & User Session */}
        <div className="flex items-center gap-4">
          {/* Search Button */}
          <button
            onClick={() => setIsSearchOpen(!isSearchOpen)}
            className="p-1 hover:bg-canvas rounded-md transition"
            aria-label="Search"
          >
            <Search size={20} className="text-govBlue" />
          </button>

          {/* User Session Dropdown */}
          <div className="relative">
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-canvas transition text-sm"
            >
              <User size={18} className="text-govBlue" />
              <span className="hidden sm:inline text-govDark font-medium truncate max-w-xs">
                {user?.name || "User"}
              </span>
            </button>

            {/* User Dropdown Menu */}
            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-line animate-fade-in">
                <div className="px-4 py-3 border-b border-line">
                  <p className="text-sm font-semibold text-govDark">{user?.name || "User"}</p>
                  <p className="text-xs text-slate-600">{user?.email || "user@gov.in"}</p>
                </div>
                <button
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    onLogout();
                  }}
                  className="w-full px-4 py-3 text-left text-sm text-fail hover:bg-canvas flex items-center gap-2 transition font-medium"
                >
                  <LogOut size={16} />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Search Bar (Expanded) */}
      {isSearchOpen && (
        <div className="bg-govLight border-t border-line px-4 py-3 animate-slide-in-down">
          <input
            type="text"
            placeholder="Search tenders, bids, schemes..."
            className="w-full px-4 py-2 border border-line rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-govBlue focus:ring-opacity-50"
            autoFocus
          />
        </div>
      )}
    </header>
  );
}
