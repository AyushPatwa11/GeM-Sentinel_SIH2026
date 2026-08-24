import React, { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";

const PRESET_SCENARIOS = [
  {
    key: "clean",
    name: "Scenario A: Clean Pass",
    desc: "Northline style — Active GST, matching entity name, high turnover, 4 projects, low risk.",
    data: {
      bidder_org_name: "Northline Engineering Pvt Ltd",
      gstin: "22ABCDE1234F1Z5",
      pan: "ABCDE1234F",
      cin: "U17124CT2015PTC098765",
      udyam_number: "",
      annual_turnover: 18500000,
      similar_project_count: 4,
      emd_paid: true,
      msme_exemption: false,
    },
  },
  {
    key: "msme",
    name: "Scenario B: MSME Exemption & Defaulter",
    desc: "Coastal style — MSME Micro certificate waives EMD; turnover borderline, filing defaulter risk signal.",
    data: {
      bidder_org_name: "Coastal Agro Supplies",
      gstin: "27PQRSX5678K1Z2",
      pan: "PQRSX5678K",
      cin: "U74999MH2018PTC311122",
      udyam_number: "UDYAM-CT-02-0012345",
      annual_turnover: 4200000,
      similar_project_count: 1,
      emd_paid: false,
      msme_exemption: true,
    },
  },
  {
    key: "mismatch",
    name: "Scenario C: GSTN Identity Contradiction",
    desc: "Meridian style — GSTIN belongs to 'Zenith Textile Traders', caught live by GSTN adapter.",
    data: {
      bidder_org_name: "Meridian Textiles Pvt Ltd",
      gstin: "09MERID1122M1Z9",
      pan: "MERID1122M",
      cin: "U17124CT2015PTC098765",
      udyam_number: "UDYAM-CT-02-0099887",
      annual_turnover: 22000000,
      similar_project_count: 3,
      emd_paid: true,
      msme_exemption: false,
    },
  },
];

const REQUIRED_SLOTS = [
  { doc_type: "GST_CERT", title: "GST Registration Certificate", mandatory: true, sample: "gst_certificate_reg06.pdf" },
  { doc_type: "PAN", title: "Permanent Account Number (PAN)", mandatory: true, sample: "company_pan_card.pdf" },
  { doc_type: "FINANCIAL_STMT", title: "Audited Financial Statements", mandatory: true, sample: "audited_balance_sheet_2026.pdf" },
  { doc_type: "EXPERIENCE_CERT", title: "Prior Experience / Work Orders", mandatory: true, sample: "completion_certificates.pdf" },
  { doc_type: "UDYAM_CERT", title: "Udyam / MSME Certificate", mandatory: false, sample: "udyam_registration_cert.pdf" },
];

export default function BidderSubmissionFlow() {
  const { bidId } = useParams();
  const navigate = useNavigate();

  const [step, setStep] = useState(1); // 1: Entity Info, 2: Upload Docs, 3: Two-Stage Verification, 4: Submit
  const [bid, setBid] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    bidder_org_name: "Northline Engineering Pvt Ltd",
    gstin: "22ABCDE1234F1Z5",
    pan: "ABCDE1234F",
    cin: "U17124CT2015PTC098765",
    udyam_number: "UDYAM-CT-02-0012345",
    annual_turnover: 18500000,
    similar_project_count: 4,
    emd_paid: true,
    msme_exemption: false,
  });

  // Documents State
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [uploadingSlot, setUploadingSlot] = useState(null);

  // Verification State
  const [stage1, setStage1] = useState(null);
  const [stage2, setStage2] = useState(null);
  const [verifyingStage1, setVerifyingStage1] = useState(false);
  const [verifyingStage2, setVerifyingStage2] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function init() {
      try {
        const data = await api.bidderBidDetail(bidId);
        setBid(data);
        setFormData({
          bidder_org_name: data.bidder_org_name || "",
          gstin: data.gstin || "",
          pan: data.pan || "",
          cin: data.cin || "",
          udyam_number: data.udyam_number || "",
          annual_turnover: data.annual_turnover || 18500000,
          similar_project_count: data.similar_project_count || 3,
          emd_paid: data.emd_paid ?? true,
          msme_exemption: data.msme_exemption ?? false,
        });
        const docs = await api.bidderDocuments(bidId);
        setUploadedDocs(docs);
      } catch (err) {
        setError(err.message || "Failed to load bid workspace");
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [bidId]);

  function applyPreset(preset) {
    setFormData((prev) => ({ ...prev, ...preset.data }));
    setNotice(`Applied preset: ${preset.name}`);
  }

  async function handleFileUpload(slotType, file) {
    if (!file) return;
    setUploadingSlot(slotType);
    setNotice(null);
    try {
      const doc = await api.bidderUploadDocumentSlot(bidId, slotType, file);
      setUploadedDocs((prev) => [
        ...prev.filter((d) => d.doc_type !== slotType),
        doc,
      ]);
      setNotice(`Uploaded ${file.name} for ${slotType}`);
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setUploadingSlot(null);
    }
  }

  function handleAutoFillSampleDocs() {
    // Quick-populate dummy document metadata for demo speed
    const mockFiles = REQUIRED_SLOTS.map((s) => ({
      id: `doc-${s.doc_type.toLowerCase()}-auto`,
      doc_type: s.doc_type,
      filename: s.sample,
      size_bytes: 425600,
      content_type: "application/pdf",
      file_hash: `sha256_mock_${s.doc_type}_verified`,
      classification_confidence: 0.98,
      ocr_status: "DONE",
      authenticity_status: "VERIFIED",
      uploaded_at: new Date().toISOString(),
    }));

    // Upload one by one or batch
    const syntheticFile = new File(["dummy pdf binary content"], "verified_doc.pdf", { type: "application/pdf" });
    REQUIRED_SLOTS.forEach((s) => {
      handleFileUpload(s.doc_type, syntheticFile);
    });
  }

  async function runStage1() {
    setVerifyingStage1(true);
    setError("");
    try {
      const res = await api.bidderVerifyStage1(bidId);
      setStage1(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setVerifyingStage1(false);
    }
  }

  async function runStage2() {
    setVerifyingStage2(true);
    setError("");
    try {
      const res = await api.bidderVerifyStage2(bidId);
      setStage2(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setVerifyingStage2(false);
    }
  }

  async function handleSubmitBid() {
    setSubmitting(true);
    setError("");
    try {
      const submission = await api.bidderSubmit(bidId);
      navigate(`/bidder/status/${bidId}`);
    } catch (err) {
      setError(err.message || "Submission failed");
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <Shell>
        <div className="py-12 text-center text-sm text-slate">Loading bid submission workspace…</div>
      </Shell>
    );
  }

  if (!bid) {
    return (
      <Shell>
        <div className="text-fail text-sm">{error || "Bid workspace not found"}</div>
      </Shell>
    );
  }

  const mandatorySlotsFilled = REQUIRED_SLOTS.filter((s) => s.mandatory).every((s) =>
    uploadedDocs.some((d) => d.doc_type === s.doc_type)
  );

  return (
    <Shell>
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <button
            onClick={() => navigate("/bidder")}
            className="text-xs text-slate hover:text-ink mb-1 inline-flex items-center gap-1 font-medium"
          >
            ← Back to Tenders
          </button>
          <h1 className="font-display text-2xl font-bold text-ink">Bid Submission Workspace</h1>
          <p className="text-xs text-slate mt-0.5">
            Tender: <span className="text-ink font-medium">{bid.tender?.title}</span> ({bid.tender?.id}) · Bid ID: <span className="font-mono text-ink">{bidId}</span>
          </p>
        </div>

        {/* Stepper Header */}
        <div className="flex items-center gap-2 bg-card border border-line p-1.5 rounded-xl shadow-xs">
          {[
            { num: 1, label: "Entity Profile" },
            { num: 2, label: "Document Upload" },
            { num: 3, label: "Two-Stage Verification" },
            { num: 4, label: "Final Review & Submit" },
          ].map((s) => (
            <button
              key={s.num}
              onClick={() => setStep(s.num)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                step === s.num
                  ? "bg-accent text-white shadow-xs"
                  : step > s.num
                  ? "text-pass bg-passBg"
                  : "text-slate hover:text-ink"
              }`}
            >
              <span
                className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                  step === s.num ? "bg-white/20 text-white" : step > s.num ? "bg-pass text-white" : "bg-canvas text-slate"
                }`}
              >
                {step > s.num ? "✓" : s.num}
              </span>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {notice && (
        <div className="bg-accent/10 border border-accent/20 text-accent text-xs p-3 rounded-lg mb-4 flex items-center justify-between">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)} className="text-accent hover:underline text-xs">Dismiss</button>
        </div>
      )}

      {error && (
        <div className="bg-failBg border border-fail/20 text-fail text-xs p-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* ================= STEP 1: Entity Info ================= */}
      {step === 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-card border border-line rounded-card p-6 shadow-sm">
            <h2 className="text-base font-bold text-ink mb-1">1. Bidding Entity Profile & Declarations</h2>
            <p className="text-xs text-slate mb-6">
              Enter your registered legal entity details. These identifiers will be cross-verified live against authoritative registries (GSTN, MCA21, Udyam, Debarment lists).
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-ink mb-1">Legal Company / Organization Name</label>
                <input
                  type="text"
                  value={formData.bidder_org_name}
                  onChange={(e) => setFormData({ ...formData, bidder_org_name: e.target.value })}
                  className="w-full bg-canvas border border-line rounded-lg px-3.5 py-2 text-sm text-ink focus:outline-none focus:border-accent"
                  placeholder="e.g. Northline Engineering Pvt Ltd"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">GSTIN (15 Digits)</label>
                <input
                  type="text"
                  value={formData.gstin}
                  onChange={(e) => setFormData({ ...formData, gstin: e.target.value.toUpperCase() })}
                  className="w-full bg-canvas border border-line rounded-lg px-3.5 py-2 font-mono text-sm text-ink focus:outline-none focus:border-accent uppercase"
                  placeholder="22ABCDE1234F1Z5"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Permanent Account Number (PAN)</label>
                <input
                  type="text"
                  value={formData.pan}
                  onChange={(e) => setFormData({ ...formData, pan: e.target.value.toUpperCase() })}
                  className="w-full bg-canvas border border-line rounded-lg px-3.5 py-2 font-mono text-sm text-ink focus:outline-none focus:border-accent uppercase"
                  placeholder="ABCDE1234F"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Corporate Identity Number (CIN)</label>
                <input
                  type="text"
                  value={formData.cin}
                  onChange={(e) => setFormData({ ...formData, cin: e.target.value.toUpperCase() })}
                  className="w-full bg-canvas border border-line rounded-lg px-3.5 py-2 font-mono text-sm text-ink focus:outline-none focus:border-accent uppercase"
                  placeholder="U17124CT2015PTC098765"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Udyam Registration No. (Optional)</label>
                <input
                  type="text"
                  value={formData.udyam_number}
                  onChange={(e) => setFormData({ ...formData, udyam_number: e.target.value.toUpperCase() })}
                  className="w-full bg-canvas border border-line rounded-lg px-3.5 py-2 font-mono text-sm text-ink focus:outline-none focus:border-accent uppercase"
                  placeholder="UDYAM-CT-02-0012345"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Annual Turnover (₹ in INR)</label>
                <input
                  type="number"
                  value={formData.annual_turnover}
                  onChange={(e) => setFormData({ ...formData, annual_turnover: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-canvas border border-line rounded-lg px-3.5 py-2 font-mono text-sm text-ink focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Similar Completed Projects Count</label>
                <input
                  type="number"
                  value={formData.similar_project_count}
                  onChange={(e) => setFormData({ ...formData, similar_project_count: parseInt(e.target.value, 10) || 0 })}
                  className="w-full bg-canvas border border-line rounded-lg px-3.5 py-2 font-mono text-sm text-ink focus:outline-none focus:border-accent"
                />
              </div>
            </div>

            <div className="mt-6 pt-5 border-t border-line flex items-center justify-between">
              <span className="text-xs text-slate">Step 1 of 4</span>
              <button
                onClick={() => setStep(2)}
                className="bg-accent hover:bg-accent2 text-white text-sm font-medium px-6 py-2.5 rounded-lg shadow-sm transition-colors"
              >
                Proceed to Document Upload →
              </button>
            </div>
          </div>

          {/* Quick Demo Pre-sets */}
          <div className="space-y-4">
            <div className="bg-card border border-line rounded-card p-5">
              <h3 className="text-sm font-bold text-ink mb-1">⚡ Quick Fill Demo Scenarios</h3>
              <p className="text-xs text-slate mb-4">
                Click any scenario below to auto-populate test data demonstrating various real-world compliance outcomes:
              </p>
              <div className="space-y-2.5">
                {PRESET_SCENARIOS.map((p) => (
                  <div
                    key={p.key}
                    onClick={() => applyPreset(p)}
                    className="p-3 border border-line hover:border-accent/50 bg-canvas/40 hover:bg-accent/5 rounded-lg cursor-pointer transition-all"
                  >
                    <div className="text-xs font-bold text-accent">{p.name}</div>
                    <div className="text-[11px] text-slate mt-1 leading-snug">{p.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================= STEP 2: Document Upload Slots ================= */}
      {step === 2 && (
        <div className="bg-card border border-line rounded-card p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-ink mb-0.5">2. Mandatory & Supporting Document Upload Slots</h2>
              <p className="text-xs text-slate">
                Attach one document per designated slot. Files will undergo OCR text extraction, entity resolution, and DigiLocker authenticity hashing.
              </p>
            </div>
            <button
              onClick={handleAutoFillSampleDocs}
              className="text-xs font-medium text-accent hover:text-accent2 border border-accent/30 bg-accent/5 px-3 py-1.5 rounded-lg transition-colors"
            >
              + Quick-Fill All Sample Documents
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
            {REQUIRED_SLOTS.map((slot) => {
              const uploaded = uploadedDocs.find((d) => d.doc_type === slot.doc_type);
              const isUploading = uploadingSlot === slot.doc_type;

              return (
                <div
                  key={slot.doc_type}
                  className={`p-4 rounded-xl border transition-all ${
                    uploaded
                      ? "bg-passBg/30 border-pass/30"
                      : slot.mandatory
                      ? "bg-canvas border-line"
                      : "bg-canvas/50 border-line/60"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-xs font-bold text-ink">{slot.title}</div>
                      <div className="text-[11px] text-slate mt-0.5">
                        Slot: <span className="font-mono text-accent">{slot.doc_type}</span> ·{" "}
                        {slot.mandatory ? (
                          <span className="text-fail font-semibold">Mandatory</span>
                        ) : (
                          <span className="text-slate">Exemption Optional</span>
                        )}
                      </div>
                    </div>
                    {uploaded ? (
                      <span className="text-[11px] bg-pass text-white font-semibold px-2 py-0.5 rounded-full flex items-center gap-1">
                        ✓ Uploaded
                      </span>
                    ) : slot.mandatory ? (
                      <span className="text-[11px] bg-failBg text-fail font-semibold px-2 py-0.5 rounded-full">
                        Required
                      </span>
                    ) : (
                      <span className="text-[11px] bg-canvas text-slate px-2 py-0.5 rounded-full">
                        Optional
                      </span>
                    )}
                  </div>

                  {uploaded ? (
                    <div className="mt-3 pt-3 border-t border-pass/20 text-xs">
                      <div className="flex items-center justify-between font-mono text-ink text-[11px]">
                        <span className="truncate max-w-[200px]">📄 {uploaded.filename}</span>
                        <span className="text-slate">{(uploaded.size_bytes / 1024).toFixed(1)} KB</span>
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[11px] text-slate">
                        <span className="text-pass font-medium">Verified Hashed: {uploaded.authenticity_status || "VERIFIED"}</span>
                        <label className="text-accent hover:underline cursor-pointer">
                          Replace file
                          <input
                            type="file"
                            className="hidden"
                            onChange={(e) => handleFileUpload(slot.doc_type, e.target.files[0])}
                          />
                        </label>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-3 pt-3 border-t border-line/60">
                      <label className="w-full flex flex-col items-center justify-center border-2 border-dashed border-line hover:border-accent rounded-lg p-3 cursor-pointer bg-white/60 hover:bg-accent/5 transition-all">
                        <span className="text-xs text-accent font-medium">
                          {isUploading ? "Uploading & Hashing…" : "+ Choose or Drop Document"}
                        </span>
                        <span className="text-[10px] text-slate mt-0.5">PDF, PNG, JPG (Max 10MB)</span>
                        <input
                          type="file"
                          disabled={isUploading}
                          className="hidden"
                          onChange={(e) => handleFileUpload(slot.doc_type, e.target.files[0])}
                        />
                      </label>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="mt-8 pt-5 border-t border-line flex items-center justify-between">
            <button
              onClick={() => setStep(1)}
              className="text-xs text-slate hover:text-ink font-medium"
            >
              ← Back to Entity Profile
            </button>
            <button
              onClick={() => {
                setStep(3);
                runStage1();
                runStage2();
              }}
              disabled={!mandatorySlotsFilled}
              className="bg-accent hover:bg-accent2 text-white text-sm font-medium px-6 py-2.5 rounded-lg shadow-sm transition-colors disabled:opacity-50"
            >
              Proceed to Two-Stage Verification →
            </button>
          </div>
        </div>
      )}

      {/* ================= STEP 3: Two-Stage Verification ================= */}
      {step === 3 && (
        <div className="space-y-6">
          {/* Stage 1 Card */}
          <div className="bg-card border border-line rounded-card p-6 shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="inline-flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold uppercase tracking-wider bg-accent/10 text-accent px-2 py-0.5 rounded">
                    Stage 1
                  </span>
                  <h2 className="text-base font-bold text-ink">Document Completeness & Authenticity Check</h2>
                </div>
                <p className="text-xs text-slate">
                  Verifies file integrity, classification confidence, format validity, and DigiLocker authenticity before evaluating eligibility clauses.
                </p>
              </div>
              <button
                onClick={runStage1}
                disabled={verifyingStage1}
                className="text-xs bg-canvas hover:bg-line text-ink font-medium px-3 py-1.5 rounded-lg border border-line transition-colors"
              >
                {verifyingStage1 ? "Checking…" : "Re-check Stage 1"}
              </button>
            </div>

            {verifyingStage1 && (
              <div className="py-8 text-center text-xs text-slate">Evaluating document hashes and authenticity…</div>
            )}

            {stage1 && !verifyingStage1 && (
              <div className="space-y-3 mt-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-canvas border border-line text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`w-3 h-3 rounded-full ${stage1.passed ? "bg-pass" : "bg-fail"}`} />
                    <span className="font-semibold text-ink">
                      Mandatory Document Completeness: {stage1.uploaded_mandatory} / {stage1.total_mandatory} slots validated
                    </span>
                  </div>
                  <span className={`font-bold px-2 py-0.5 rounded text-[11px] ${stage1.passed ? "bg-passBg text-pass" : "bg-failBg text-fail"}`}>
                    {stage1.passed ? "STAGE 1 PASSED" : "INCOMPLETE DOCUMENTS"}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {stage1.slots.map((s) => (
                    <div key={s.doc_type} className="p-3 border border-line rounded-lg text-xs flex items-center justify-between bg-white">
                      <div>
                        <div className="font-medium text-ink">{s.title}</div>
                        <div className="text-[11px] text-slate mt-0.5">
                          {s.filename ? `File: ${s.filename}` : "No document attached"}
                        </div>
                      </div>
                      <StatusBadge status={s.status === "VALIDATED" ? "VERIFIED" : s.mandatory ? "FAIL" : "NOT_REQUIRED"} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Stage 2 Card */}
          <div className="bg-card border border-line rounded-card p-6 shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="inline-flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold uppercase tracking-wider bg-accent/10 text-accent px-2 py-0.5 rounded">
                    Stage 2
                  </span>
                  <h2 className="text-base font-bold text-ink">Eligibility & Statutory Validity Check (Rule Engine)</h2>
                </div>
                <p className="text-xs text-slate">
                  Executes deterministic logic trees, MSME waivers, and live registry adapter queries (GSTN, Debarment).
                </p>
              </div>
              <button
                onClick={runStage2}
                disabled={verifyingStage2}
                className="text-xs bg-canvas hover:bg-line text-ink font-medium px-3 py-1.5 rounded-lg border border-line transition-colors"
              >
                {verifyingStage2 ? "Evaluating…" : "Re-run Rule Engine"}
              </button>
            </div>

            {verifyingStage2 && (
              <div className="py-8 text-center text-xs text-slate">Executing rule engine logic trees and adapter checks…</div>
            )}

            {stage2 && !verifyingStage2 && (
              <div className="space-y-4 mt-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-canvas border border-line text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-ink">Overall Tender Compliance Verdict:</span>
                    <StatusBadge status={stage2.compliance_status} />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-slate">AI Recommendation:</span>
                    <span className="font-bold text-accent">{stage2.ai_recommendation}</span>
                  </div>
                </div>

                <div className="space-y-2.5">
                  {stage2.clause_results.map((c) => (
                    <div key={c.clause_id} className="p-3.5 border border-line rounded-lg bg-white">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <div className="text-xs font-medium text-ink">{c.clause_text}</div>
                          <div className="text-[11px] text-slate mt-1">
                            {c.mandatory ? "Mandatory hard-gate clause" : "Optional / Conditional"}
                          </div>
                        </div>
                        <StatusBadge status={c.status} />
                      </div>
                      {c.reasoning_chain && (
                        <div className="mt-2 text-[11px] text-slate pl-2 border-l-2 border-line space-y-0.5">
                          {c.reasoning_chain.map((r, i) => (
                            <div key={i}>{r}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Risk Signal Breakdown */}
                {stage2.risk_assessment && (
                  <div className="p-4 rounded-xl bg-canvas border border-line">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-ink">AI Risk Assessment Score</span>
                      <div className="flex items-center gap-2">
                        <StatusBadge status={stage2.risk_assessment.risk_level} />
                        <span className="font-mono text-xs font-bold text-ink">
                          Score: {stage2.risk_assessment.total_score}
                        </span>
                      </div>
                    </div>
                    {stage2.risk_assessment.signals?.length > 0 ? (
                      <div className="space-y-1.5 mt-2">
                        {stage2.risk_assessment.signals.map((sig, i) => (
                          <div key={i} className="text-[11px] text-slate flex items-center justify-between bg-white px-2.5 py-1.5 rounded border border-line">
                            <span className="font-medium text-ink">{sig.signal_type}</span>
                            <span className="text-fail font-mono">+{sig.contribution}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[11px] text-pass font-medium">✓ No adverse risk signals detected.</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="bg-card border border-line rounded-card p-4 flex items-center justify-between">
            <button
              onClick={() => setStep(2)}
              className="text-xs text-slate hover:text-ink font-medium"
            >
              ← Back to Documents
            </button>
            <button
              onClick={() => setStep(4)}
              disabled={!stage1?.passed}
              className="bg-accent hover:bg-accent2 text-white text-sm font-medium px-6 py-2.5 rounded-lg shadow-sm transition-colors disabled:opacity-50"
            >
              Proceed to Final Review & Submit →
            </button>
          </div>
        </div>
      )}

      {/* ================= STEP 4: Review & Submit ================= */}
      {step === 4 && (
        <div className="bg-card border border-line rounded-card p-6 shadow-sm max-w-2xl mx-auto">
          <h2 className="text-lg font-bold text-ink mb-1">4. Confirm & Submit Bid</h2>
          <p className="text-xs text-slate mb-6">
            Review your submission summary. Once submitted, your bid will be entered into the GeM Sentinel procurement queue for officer review and logged to the immutable audit trail.
          </p>

          <div className="bg-canvas border border-line rounded-xl p-4 space-y-3 text-xs mb-6">
            <div className="flex justify-between">
              <span className="text-slate">Bidding Entity:</span>
              <span className="font-semibold text-ink">{formData.bidder_org_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate">GSTIN:</span>
              <span className="font-mono text-ink">{formData.gstin}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate">PAN:</span>
              <span className="font-mono text-ink">{formData.pan}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate">Uploaded Documents:</span>
              <span className="font-semibold text-pass">{uploadedDocs.length} Verified Files</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate">Two-Stage Verification:</span>
              <span className="font-bold text-pass">✓ Stage 1 & Stage 2 Cleared</span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-line">
            <button
              onClick={() => setStep(3)}
              className="text-xs text-slate hover:text-ink font-medium"
            >
              ← Back to Verification
            </button>
            <button
              onClick={handleSubmitBid}
              disabled={submitting}
              className="bg-pass hover:bg-pass/90 text-white text-sm font-bold px-8 py-3 rounded-lg shadow-sm transition-all transform active:scale-95 disabled:opacity-50"
            >
              {submitting ? "Submitting Bid to GeM Sentinel…" : "🚀 Submit Bid to GeM Sentinel"}
            </button>
          </div>
        </div>
      )}
    </Shell>
  );
}
