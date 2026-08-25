import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/auth.jsx";
import Login from "./pages/Login.jsx";
import LandingPage from "./pages/LandingPage.jsx";
import OfficerDashboard from "./pages/OfficerDashboard.jsx";
import BidDetail from "./pages/BidDetail.jsx";
import AuditTrail from "./pages/AuditTrail.jsx";
import BidderTenders from "./pages/BidderTenders.jsx";
import TenderDetail from "./pages/TenderDetail.jsx";
import BidderSubmissionFlow from "./pages/BidderSubmissionFlow.jsx";
import BidderStatusTracker from "./pages/BidderStatusTracker.jsx";

function RequireRole({ role, children }) {
  const { session } = useAuth();
  if (!session) return <Navigate to="/login" replace />;
  if (session.role !== role) return <Navigate to={session.role === "officer" ? "/officer" : "/bidder"} replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Landing Page */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />

      {/* Officer Portal */}
      <Route path="/officer" element={<RequireRole role="officer"><OfficerDashboard /></RequireRole>} />
      <Route path="/officer/bids/:bidId" element={<RequireRole role="officer"><BidDetail /></RequireRole>} />
      <Route path="/officer/audit" element={<RequireRole role="officer"><AuditTrail /></RequireRole>} />

      {/* Bidder Portal (Complete Connected Workflow) */}
      <Route path="/bidder" element={<RequireRole role="bidder"><BidderTenders /></RequireRole>} />
      <Route path="/bidder/tenders/:tenderId" element={<RequireRole role="bidder"><TenderDetail /></RequireRole>} />
      <Route path="/bidder/apply/:bidId" element={<RequireRole role="bidder"><BidderSubmissionFlow /></RequireRole>} />
      <Route path="/bidder/bids/:bidId/submit" element={<RequireRole role="bidder"><BidderSubmissionFlow /></RequireRole>} />
      <Route path="/bidder/readiness" element={<RequireRole role="bidder"><BidderSubmissionFlow /></RequireRole>} />
      <Route path="/bidder/status/:bidId" element={<RequireRole role="bidder"><BidderStatusTracker /></RequireRole>} />

      <Route path="*" element={<Navigate to="/" replace />} />
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
