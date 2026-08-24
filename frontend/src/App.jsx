import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/auth.jsx";
import Login from "./pages/Login.jsx";
import OfficerDashboard from "./pages/OfficerDashboard.jsx";
import BidDetail from "./pages/BidDetail.jsx";
import AuditTrail from "./pages/AuditTrail.jsx";
import BidderTenders from "./pages/BidderTenders.jsx";
import BidderReadiness from "./pages/BidderReadiness.jsx";

function RequireRole({ role, children }) {
  const { session } = useAuth();
  if (!session) return <Navigate to="/login" replace />;
  if (session.role !== role) return <Navigate to={session.role === "officer" ? "/officer" : "/bidder"} replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route path="/officer" element={<RequireRole role="officer"><OfficerDashboard /></RequireRole>} />
      <Route path="/officer/bids/:bidId" element={<RequireRole role="officer"><BidDetail /></RequireRole>} />
      <Route path="/officer/audit" element={<RequireRole role="officer"><AuditTrail /></RequireRole>} />

      <Route path="/bidder" element={<RequireRole role="bidder"><BidderTenders /></RequireRole>} />
      <Route path="/bidder/readiness" element={<RequireRole role="bidder"><BidderReadiness /></RequireRole>} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
