const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

function getAuthHeader() {
  const session = sessionStorage.getItem("gem-sentinel-session");
  if (!session) return {};
  
  try {
    const data = JSON.parse(session);
    if (data.access_token) {
      return { "Authorization": `Bearer ${data.access_token}` };
    }
  } catch (e) {
    console.error("Failed to parse session:", e);
  }
  
  return {};
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
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
  const res = await fetch(`${BASE}${path}`, { 
    method: "POST", 
    body: formData,
    headers: getAuthHeader(),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed: ${res.status}`);
  }
  return res.json();
}

async function uploadSingle(path, file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE}${path}`, { 
    method: "POST", 
    body: formData,
    headers: getAuthHeader(),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  
  register: (email, password, organization_name, role) =>
    request("/auth/register", { 
      method: "POST", 
      body: JSON.stringify({ email, password, organization_name, role }) 
    }),

  userProfile: () => request("/user/profile"),

  // Tenders
  tenders: () => request("/tenders"),
  tenderDetail: (tenderId) => request(`/bidder/tenders/${tenderId}`),

  // Officer endpoints - Tender Management
  officerTenders: () => request("/officer/tenders"),
  officerCreateTender: (data) =>
    request("/officer/tenders", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  officerPublishTender: (tenderId) =>
    request(`/officer/tenders/${tenderId}/publish`, { method: "POST" }),
  officerClauses: (tenderId) => request(`/officer/tenders/${tenderId}/clauses`),
  
  // Officer endpoints - Bid Management
  officerBids: () => request("/officer/bids"),
  officerBidDetail: (bidId) => request(`/officer/bids/${bidId}`),
  officerEvaluate: (bidId) => request(`/officer/bids/${bidId}/evaluate`, { method: "POST" }),
  
  // Officer endpoints - Compliance
  getComplianceRules: () => request("/compliance/rules"),
  evaluateCompliance: (bidId) =>
    request(`/officer/bids/${bidId}/evaluate-compliance`, { method: "POST" }),
  getComplianceSummary: (bidId) =>
    request(`/officer/bids/${bidId}/compliance-summary`),
  createEvidenceChain: (complianceResultId) =>
    request(`/officer/compliance/${complianceResultId}/create-evidence-chain`, { method: "POST" }),
  traceEvidence: (complianceResultId) =>
    request(`/officer/compliance/${complianceResultId}/trace-evidence`),
  createRiskSignal: (complianceResultId) =>
    request(`/officer/compliance/${complianceResultId}/create-risk-signal`, { method: "POST" }),
  
  // Officer endpoints - Verification (Phase 5)
  verifyExternalData: (bidId) =>
    request(`/officer/bids/${bidId}/verify-external-data`, { method: "POST" }),
  verifySingleFact: (bidId, factType, factValue) =>
    request(`/officer/verify-single-fact`, {
      method: "POST",
      body: JSON.stringify({ bid_id: bidId, fact_type: factType, fact_value: factValue }),
    }),
  getVerificationHistory: (bidId) =>
    request(`/officer/verification-history?bid_id=${bidId}`),
  testNameMatching: (docName, authName) =>
    request(`/officer/test-name-matching`, {
      method: "POST",
      body: JSON.stringify({ document_name: docName, authority_name: authName }),
    }),
  getAdapterStatus: () => request(`/officer/adapters/status`),
  
  // Officer endpoints - Risk Assessment (Phase 6)
  assessRisk: (bidId) =>
    request(`/officer/bids/${bidId}/assess-risk`, { method: "POST" }),
  getRiskAssessment: (bidId) =>
    request(`/officer/bids/${bidId}/risk-assessment`),
  getRiskSignals: (bidId) =>
    request(`/officer/bids/${bidId}/risk-signals`),
  decomposeRisk: (bidId) =>
    request(`/officer/bids/${bidId}/decompose-risk`, { method: "POST" }),
  getRiskRecommendations: (bidId) =>
    request(`/officer/bids/${bidId}/risk-recommendations`, { method: "POST" }),
  
  // Officer endpoints - Decision Support (Phase 7)
  getRecommendation: (bidId) =>
    request(`/officer/bids/${bidId}/get-recommendation`, { method: "POST" }),
  getDecisionReadiness: (bidId) =>
    request(`/officer/bids/${bidId}/decision-readiness`),
  requestClarification: (bidId, details) =>
    request(`/officer/bids/${bidId}/request-clarification-v2`, {
      method: "POST",
      body: JSON.stringify(details),
    }),
  getClarifications: (bidId) =>
    request(`/officer/bids/${bidId}/clarifications-v2`),
  makeDecision: (bidId, decision, reason) =>
    request(`/officer/bids/${bidId}/make-decision-v2`, {
      method: "POST",
      body: JSON.stringify({ decision_result: decision, override_reason: reason }),
    }),
  getDashboardSummary: (bidId) =>
    request(`/officer/bids/${bidId}/dashboard-summary`),
  
  // Officer legacy endpoints (kept for backward compatibility)
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
      body: JSON.stringify({ 
        ai_recommendation: finalDecision, 
        final_decision: finalDecision, 
        override_reason: overrideReason || null 
      }),
    }),
  officerAudit: (bidId) => request(`/bids/${bidId}/audit`),
  allAudit: () => request("/officer/audit"),
  removeBid: (bidId) => request(`/officer/bids/${bidId}`, { method: "DELETE" }),

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
  bidderDocuments: (bidId) => request(`/bidder/bids/${bidId}/documents/list`),
  bidderUploadDocument: (bidId, file) =>
    uploadSingle(`/bidder/bids/${bidId}/documents/upload`, file),
  bidderUploadDocuments: (bidId, files) => 
    upload(`/bidder/bids/${bidId}/documents/upload`, files),
  bidderDeleteDocument: (bidId, docId) =>
    request(`/bidder/bids/${bidId}/documents/${docId}`, { method: "DELETE" }),
  getOCRStatus: (docId) =>
    request(`/bidder/documents/${docId}/ocr-status`),
  bidderVerifyStage1: (bidId) => 
    request(`/bidder/bids/${bidId}/verify-stage1`, { method: "POST" }),
  updateBid: (bidId, data) =>
    request(`/bidder/bids/${bidId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  bidderVerifyStage2: (bidId) => 
    request(`/bidder/bids/${bidId}/verify-stage2`, { method: "POST" }),
  bidderReadiness: (bidId) => 
    request(`/bidder/bids/${bidId}/readiness`),
  bidderSubmit: (bidId) => 
    request(`/bidder/bids/${bidId}/submit`, { method: "POST" }),
  bidderBidStatus: (bidId) => 
    request(`/bidder/bids/${bidId}/status`),
  
  // System Health & Audit
  systemHealth: () => request("/health"),
  getAuditTrail: (filters = {}) => {
    const params = new URLSearchParams(filters).toString();
    return request(`/audit-trail${params ? '?' + params : ''}`);
  },

  // NEW: Extract company details from documents (OCR-based auto-population)
  bidderExtractDocuments: (bidId) =>
    request(`/bidder/bids/${bidId}/extract-documents`, { method: "POST" }),
  
  // NEW: Government database verification APIs
  verifyGSTIN: (data) =>
    request(`/verify/gstin`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  verifyPAN: (data) =>
    request(`/verify/pan`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  verifyCIN: (data) =>
    request(`/verify/cin`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  verifyUdyam: (data) =>
    request(`/verify/udyam`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
