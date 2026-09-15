import React, { useState } from "react";
import GovernmentHeader from "./GovernmentHeader";
import GovernmentSidebar from "./GovernmentSidebar";
import Breadcrumb from "./Breadcrumb";
import GovernmentFooter from "./GovernmentFooter";

export default function GovernmentLayout({ children, user, userRole, onLogout }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleSidebarToggle = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleSidebarClose = () => {
    setIsSidebarOpen(false);
  };

  return (
    <div className="flex flex-col min-h-screen bg-govLight">
      {/* Fixed Header */}
      <GovernmentHeader
        user={user}
        onLogout={onLogout}
        isSidebarOpen={isSidebarOpen}
        onSidebarToggle={handleSidebarToggle}
      />

      {/* Breadcrumb Navigation */}
      <Breadcrumb />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Navigation */}
        <GovernmentSidebar
          userRole={userRole}
          isOpen={isSidebarOpen}
          onClose={handleSidebarClose}
        />

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 py-8">
            {children}
          </div>
        </main>
      </div>

      {/* Fixed Footer */}
      <GovernmentFooter />
    </div>
  );
}
