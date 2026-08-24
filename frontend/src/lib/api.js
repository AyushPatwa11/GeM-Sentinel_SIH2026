const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  login: (email, password, role) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password, role }) }),

  officerTenders: () => request("/officer/tenders"),
  officerClauses: (tenderId) => request(`/officer/tenders/${tenderId}/clauses`),
  officerBids: () => request("/officer/bids"),
  officerBidDetail: (bidId) => request(`/officer/bids/${bidId}`),
  officerEvaluate: (bidId) => request(`/officer/bids/${bidId}/evaluate`, { method: "POST" }),
  officerDecide: (bidId, finalDecision, overrideReason) =>
    request(`/officer/bids/${bidId}/decision`, {
      method: "POST",
      body: JSON.stringify({ final_decision: finalDecision, override_reason: overrideReason || null }),
    }),
  officerAudit: (bidId) => request(`/officer/audit/bids/${bidId}`),

  bidderTenders: () => request("/bidder/tenders"),
  bidderRequirements: (tenderId) => request(`/bidder/tenders/${tenderId}/requirements`),
  bidderReadiness: (bidId) => request(`/bidder/bids/${bidId}/readiness`),
};
