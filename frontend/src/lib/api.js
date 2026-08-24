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

async function upload(path, files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const res = await fetch(`${BASE}${path}`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed: ${res.status}`);
  }
  return res.json();
}

async function uploadSingle(path, file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE}${path}`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  login: (email, password, role) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password, role }) }),

  // Tenders
  tenders: () => request("/tenders"),
  tenderDetail: (tenderId) => request(`/tenders/${tenderId}`),

  // Officer endpoints
  officerTenders: () => request("/officer/tenders"),
  officerClauses: (tenderId) => request(`/officer/tenders/${tenderId}/clauses`),
  officerBids: () => request("/officer/bids"),
  officerBidDetail: (bidId) => request(`/officer/bids/${bidId}`),
  officerEvaluate: (bidId) => request(`/officer/bids/${bidId}/evaluate`, { method: "POST" }),
  officerTriggerVerification: (bidId, sourceName) =>
    request(`/officer/bids/${bidId}/verify-source`, {
      method: "POST",
      body: JSON.stringify({ source_name: sourceName }),
    }),
  officerAddNote: (bidId, note, category = "GENERAL") =>
    request(`/officer/bids/${bidId}/notes`, {
      method: "POST",
      body: JSON.stringify({ note, category }),
    }),
  officerFlagDocument: (bidId, docId, reason, actionRequired) =>
    request(`/officer/bids/${bidId}/flag-document`, {
      method: "POST",
      body: JSON.stringify({ doc_id: docId, reason, action_required: actionRequired }),
    }),
  officerDecide: (bidId, finalDecision, overrideReason) =>
    request(`/officer/bids/${bidId}/decision`, {
      method: "POST",
      body: JSON.stringify({ final_decision: finalDecision, override_reason: overrideReason || null }),
    }),
  officerAudit: (bidId) => request(`/officer/audit/bids/${bidId}`),
  allAudit: () => request("/officer/audit"),

  // Bidder endpoints
  bidderTenders: () => request("/bidder/tenders"),
  bidderTenderDetail: (tenderId) => request(`/bidder/tenders/${tenderId}`),
  bidderRequirements: (tenderId) => request(`/bidder/tenders/${tenderId}/requirements`),
  bidderBids: () => request("/bidder/bids"),
  bidderBidDetail: (bidId) => request(`/bidder/bids/${bidId}`),
  bidderCreateBid: (tenderId, form = null) =>
    request(`/bidder/tenders/${tenderId}/bids`, {
      method: "POST",
      body: form ? JSON.stringify(form) : undefined,
    }),
  bidderDocuments: (bidId) => request(`/bidder/bids/${bidId}/documents`),
  bidderUploadDocumentSlot: (bidId, docType, file) =>
    uploadSingle(`/bidder/bids/${bidId}/documents/${docType}`, file),
  bidderUploadDocuments: (bidId, files) => upload(`/bidder/bids/${bidId}/documents`, files),
  bidderDeleteDocument: (bidId, docId) =>
    request(`/bidder/bids/${bidId}/documents/${docId}`, { method: "DELETE" }),
  bidderVerifyStage1: (bidId) => request(`/bidder/bids/${bidId}/verify-stage1`, { method: "POST" }),
  bidderVerifyStage2: (bidId) => request(`/bidder/bids/${bidId}/verify-stage2`, { method: "POST" }),
  bidderReadiness: (bidId) => request(`/bidder/bids/${bidId}/readiness`),
  bidderSubmit: (bidId) => request(`/bidder/bids/${bidId}/submit`, { method: "POST" }),
  bidderBidStatus: (bidId) => request(`/bidder/bids/${bidId}/status`),
};
