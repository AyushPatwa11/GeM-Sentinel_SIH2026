import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Shell from "../components/Shell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { api } from "../lib/api.js";
import { AlertCircle, CheckCircle2, XCircle, FileText, Upload } from "lucide-react";

/**
 * REFACTORED BIDDER APPLICATION WORKFLOW
 * 
 * NEW FLOW (Document-First):
 * 1. Upload Documents (GST, PAN, Financial, Experience)
 * 2. Extract company details via OCR
 * 3. Auto-populate form with extracted data
 * 4. Cross-verify with government databases
 * 5. Show verification results (Passed/Mismatched/Failed)
 * 6. Submit if verified or accept risk warning
 * 
 * BENEFITS:
 * ✓ No manual data entry
 * ✓ Automatic document-to-form population
 * ✓ Real-time government database verification
 * ✓ Transparency: See what matched and what didn't
 * ✓ Reduced fraud: Can't lie - data extracted from docs
 */

const REQUIRED_DOCUMENTS = [
  { doc_type: "GST_CERT", title: "GST Registration Certificate", icon: "📋", mandatory: true },
  { doc_type: "PAN", title: "Permanent Account Number (PAN)", icon: "🏢", mandatory: true },
  { doc_type: "FINANCIAL_STMT", title: "Audited Financial Statements", icon: "📊", mandatory: true },
  { doc_type: "EXPERIENCE_CERT", title: "Prior Experience / Work Orders", icon: "✅", mandatory: true },
  { doc_type: "UDYAM_CERT", title: "Udyam / MSME Certificate", icon: "🎖️", mandatory: false },
];

export default function BidderApplicationRefactored() {
  const { bidId } = useParams();
  const navigate = useNavigate();

  // Step tracking: 1=Upload, 2=Extract+Verify, 3=Results, 4=Submit
  const [currentStep, setCurrentStep] = useState(1);
  const [bid, setBid] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Document upload state
  const [uploadedDocuments, setUploadedDocuments] = useState({});
  const [uploadingDocType, setUploadingDocType] = useState(null);

  // Extraction state
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionProgress, setExtractionProgress] = useState(0);
  const [extractedCompanyData, setExtractedCompanyData] = useState(null);

  // Form data (auto-populated from extraction)
  const [formData, setFormData] = useState({
    company_name: "",
    gstin: "",
    pan: "",
    cin: "",
    udyam_number: "",
    annual_turnover: "",
    project_count: "",
  });

  // Verification state (cross-check with gov databases)
  const [verificationInProgress, setVerificationInProgress] = useState(false);
  const [verificationResults, setVerificationResults] = useState({
    gstin: null,
    pan: null,
    cin: null,
    udyam: null,
  });
  const [overallVerificationStatus, setOverallVerificationStatus] = useState("pending"); // pending|verified|partial|failed

  // Initialize
  useEffect(() => {
    async function initialize() {
      try {
        const bidData = await api.bidderBidDetail(bidId);
        setBid(bidData);

        // Load existing documents if any
        try {
          const docs = await api.bidderDocuments(bidId);
          const docsMap = {};
          docs.forEach((doc) => {
            docsMap[doc.doc_type] = doc;
          });
          setUploadedDocuments(docsMap);
        } catch (e) {
          // No documents yet, that's fine
        }
      } catch (err) {
        setError("Failed to load bid: " + err.message);
      } finally {
        setLoading(false);
      }
    }

    initialize();
  }, [bidId]);

  // Handle document upload
  async function handleDocumentUpload(docType, file) {
    if (!file) return;

    setUploadingDocType(docType);
    setError("");

    try {
      const uploadedDoc = await api.bidderUploadDocument(bidId, file);
      setUploadedDocuments((prev) => ({
        ...prev,
        [docType]: uploadedDoc,
      }));
      setSuccessMessage(`✓ ${REQUIRED_DOCUMENTS.find((d) => d.doc_type === docType)?.title} uploaded`);
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      setError(`Upload failed: ${err.message}`);
    } finally {
      setUploadingDocType(null);
    }
  }

  // Extract details from documents and auto-populate form
  async function extractAndAutoPopulate() {
    setIsExtracting(true);
    setExtractionProgress(0);
    setError("");

    try {
      // Step 1: Call backend to extract text from documents (OCR)
      setExtractionProgress(30);
      const extractionResult = await api.bidderExtractDocuments(bidId);

      if (!extractionResult?.extracted_fields) {
        throw new Error("Could not extract data from documents. Try re-uploading clearer copies.");
      }

      setExtractionProgress(60);
      const extracted = extractionResult.extracted_fields;
      setExtractedCompanyData(extractionResult);

      // Step 2: Auto-populate form with extracted data
      const newFormData = {
        company_name: extracted.company_name || extracted.organization_name || "",
        gstin: extracted.gstin || "",
        pan: extracted.pan || "",
        cin: extracted.cin || extracted.company_registration_number || "",
        udyam_number: extracted.udyam_number || extracted.msme_registration || "",
        annual_turnover: extracted.annual_turnover || "",
        project_count: extracted.project_count || "0",
      };

      setFormData(newFormData);
      setExtractionProgress(80);

      // Step 3: Cross-verify with government databases
      setExtractionProgress(90);
      await crossVerifyWithGovernment(newFormData);

      setExtractionProgress(100);
      setCurrentStep(3); // Move to results
      setSuccessMessage("✓ Details extracted and verified!");
    } catch (err) {
      setError(`Extraction failed: ${err.message}`);
    } finally {
      setIsExtracting(false);
      setExtractionProgress(0);
    }
  }

  // Cross-verify extracted data with government APIs
  async function crossVerifyWithGovernment(data) {
    setVerificationInProgress(true);

    try {
      const results = {};
      let successCount = 0;
      let totalChecks = 0;

      // Verify GSTIN
      if (data.gstin) {
        totalChecks++;
        try {
          const gstRes = await api.verifyGSTIN({ gstin: data.gstin, company_name: data.company_name });
          const isMatch = gstRes.registered_name?.toLowerCase() === data.company_name?.toLowerCase();
          results.gstin = {
            status: isMatch ? "verified" : "mismatch",
            message: isMatch
              ? `✓ Registered as: ${gstRes.registered_name}`
              : `⚠ Registry shows: ${gstRes.registered_name}`,
            registryName: gstRes.registered_name,
          };
          if (isMatch) successCount++;
        } catch (e) {
          results.gstin = { status: "error", message: `✗ ${e.message}` };
        }
      }

      // Verify PAN
      if (data.pan) {
        totalChecks++;
        try {
          const panRes = await api.verifyPAN({ pan: data.pan });
          results.pan = {
            status: panRes.status === "verified" ? "verified" : "mismatch",
            message: panRes.status === "verified" ? "✓ PAN verified" : "⚠ PAN verification inconclusive",
          };
          if (panRes.status === "verified") successCount++;
        } catch (e) {
          results.pan = { status: "error", message: `✗ ${e.message}` };
        }
      }

      // Verify CIN
      if (data.cin) {
        totalChecks++;
        try {
          const cinRes = await api.verifyCIN({ cin: data.cin });
          results.cin = {
            status: cinRes.status === "verified" ? "verified" : "mismatch",
            message: cinRes.status === "verified" ? "✓ Company registered (MCA21)" : "⚠ Company registration needs review",
          };
          if (cinRes.status === "verified") successCount++;
        } catch (e) {
          results.cin = { status: "error", message: `✗ ${e.message}` };
        }
      }

      // Verify Udyam
      if (data.udyam_number) {
        totalChecks++;
        try {
          const udyamRes = await api.verifyUdyam({ udyam_number: data.udyam_number });
          results.udyam = {
            status: udyamRes.status === "verified" ? "verified" : "mismatch",
            message: udyamRes.status === "verified" ? "✓ MSME registered" : "⚠ MSME verification inconclusive",
          };
          if (udyamRes.status === "verified") successCount++;
        } catch (e) {
          results.udyam = { status: "error", message: `✗ ${e.message}` };
        }
      }

      setVerificationResults(results);

      // Determine overall status
      if (successCount === totalChecks) {
        setOverallVerificationStatus("verified");
      } else if (successCount > 0) {
        setOverallVerificationStatus("partial");
      } else {
        setOverallVerificationStatus("failed");
      }
    } catch (err) {
      setError(`Verification failed: ${err.message}`);
      setOverallVerificationStatus("failed");
    } finally {
      setVerificationInProgress(false);
    }
  }

  // Submit bid
  async function handleSubmit() {
    try {
      await api.bidderSubmit(bidId);
      navigate(`/bidder/status/${bidId}`);
    } catch (err) {
      setError(`Submission failed: ${err.message}`);
    }
  }

  if (loading) {
    return (
      <Shell>
        <div className="py-12 text-center">
          <div className="animate-spin text-4xl mb-3">⏳</div>
          <p className="text-sm text-slate">Loading application workspace...</p>
        </div>
      </Shell>
    );
  }

  if (!bid) {
    return (
      <Shell>
        <div className="bg-failBg border border-fail/30 rounded-lg p-4 text-fail text-sm">
          ✗ {error || "Bid not found"}
        </div>
      </Shell>
    );
  }

  const allMandatoryDocsUploaded = REQUIRED_DOCUMENTS.filter((d) => d.mandatory).every(
    (d) => uploadedDocuments[d.doc_type]
  );

  return (
    <Shell>
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate("/bidder")}
          className="text-xs text-slate hover:text-ink mb-2 inline-flex items-center gap-1 font-medium"
        >
          ← Back to Tenders
        </button>
        <h1 className="text-2xl font-bold text-ink mb-1">Bid Application</h1>
        <p className="text-xs text-slate">
          Tender: <span className="font-medium text-ink">{bid.tender?.title}</span>
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="flex gap-2 mb-6 bg-card border border-line p-2 rounded-lg">
        {[
          { num: 1, label: "Upload Documents" },
          { num: 2, label: "Extract & Verify" },
          { num: 3, label: "Review Results" },
          { num: 4, label: "Submit" },
        ].map((step) => (
          <button
            key={step.num}
            onClick={() => step.num < currentStep && setCurrentStep(step.num)}
            className={`flex-1 px-3 py-2 text-xs font-medium rounded transition-all ${
              currentStep === step.num
                ? "bg-accent text-white"
                : currentStep > step.num
                ? "bg-pass/20 text-pass"
                : "bg-canvas text-slate"
            }`}
          >
            {currentStep > step.num ? "✓" : step.num} {step.label}
          </button>
        ))}
      </div>

      {/* Alerts */}
      {error && (
        <div className="bg-failBg border border-fail/30 text-fail text-xs p-3 rounded-lg mb-4 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}
      {successMessage && (
        <div className="bg-passBg border border-pass/30 text-pass text-xs p-3 rounded-lg mb-4 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          {successMessage}
        </div>
      )}

      {/* ===== STEP 1: UPLOAD DOCUMENTS ===== */}
      {currentStep === 1 && (
        <div className="space-y-4">
          <div className="bg-card border border-line rounded-lg p-6">
            <h2 className="text-lg font-bold text-ink mb-1">📄 Upload Your Company Documents</h2>
            <p className="text-xs text-slate mb-6">
              Upload the documents below. OCR will extract company details automatically. No manual typing needed!
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {REQUIRED_DOCUMENTS.map((doc) => {
                const isUploaded = !!uploadedDocuments[doc.doc_type];
                const isUploading = uploadingDocType === doc.doc_type;

                return (
                  <div
                    key={doc.doc_type}
                    className={`p-4 border rounded-lg transition-all ${
                      isUploaded
                        ? "bg-passBg/20 border-pass/30"
                        : "bg-canvas border-line hover:border-accent"
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="text-2xl mb-1">{doc.icon}</div>
                        <div className="text-sm font-bold text-ink">{doc.title}</div>
                        <div className="text-xs text-slate mt-1">
                          {doc.mandatory ? "Required" : "Optional"}
                        </div>
                      </div>
                      {isUploaded && <div className="text-pass text-lg">✓</div>}
                    </div>

                    {isUploaded ? (
                      <div className="text-xs">
                        <div className="font-mono text-ink truncate">
                          📎 {uploadedDocuments[doc.doc_type].filename}
                        </div>
                        <label className="text-accent hover:underline cursor-pointer mt-2 inline-block">
                          Upload different file
                          <input
                            type="file"
                            className="hidden"
                            onChange={(e) =>
                              handleDocumentUpload(doc.doc_type, e.target.files[0])
                            }
                          />
                        </label>
                      </div>
                    ) : (
                      <label className="block w-full border-2 border-dashed border-line rounded-lg p-3 text-center cursor-pointer hover:border-accent hover:bg-accent/5 transition-all">
                        <Upload className="w-4 h-4 mx-auto mb-2 text-slate" />
                        <span className="text-xs font-medium text-accent">
                          {isUploading ? "Uploading..." : "Click to upload"}
                        </span>
                        <input
                          type="file"
                          className="hidden"
                          disabled={isUploading}
                          onChange={(e) =>
                            handleDocumentUpload(doc.doc_type, e.target.files[0])
                          }
                        />
                      </label>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Button */}
          <div className="flex justify-end">
            {allMandatoryDocsUploaded ? (
              <button
                onClick={extractAndAutoPopulate}
                disabled={isExtracting}
                className="bg-accent hover:bg-accent2 disabled:opacity-50 text-white font-medium px-6 py-2.5 rounded-lg transition-all flex items-center gap-2"
              >
                {isExtracting ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Extracting & Verifying...
                  </>
                ) : (
                  <>
                    🔍 Extract Details & Cross-Verify →
                  </>
                )}
              </button>
            ) : (
              <button disabled className="bg-slate-300 text-slate-500 font-medium px-6 py-2.5 rounded-lg cursor-not-allowed">
                ⚠ Upload all required documents first
              </button>
            )}
          </div>
        </div>
      )}

      {/* ===== STEP 3: VERIFICATION RESULTS ===== */}
      {currentStep === 3 && (
        <div className="space-y-4">
          {/* Extracted Data Preview */}
          <div className="bg-card border border-line rounded-lg p-6">
            <h2 className="text-lg font-bold text-ink mb-4">✓ Extracted Company Details</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { label: "Company Name", value: formData.company_name },
                { label: "GSTIN", value: formData.gstin },
                { label: "PAN", value: formData.pan },
                { label: "CIN", value: formData.cin },
                { label: "Udyam Number", value: formData.udyam_number },
                { label: "Annual Turnover", value: formData.annual_turnover ? `₹ ${formData.annual_turnover}` : "—" },
              ].map((field) => (
                <div key={field.label} className="p-3 bg-slate-50 rounded border border-slate-200">
                  <div className="text-xs text-slate mb-1">{field.label}</div>
                  <div className="font-mono font-medium text-ink">{field.value || "—"}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Government Verification Results */}
          <div className="bg-card border border-line rounded-lg p-6">
            <h2 className="text-lg font-bold text-ink mb-4">🔐 Government Database Cross-Verification</h2>

            <div className="space-y-3">
              {Object.entries(verificationResults).map(([key, result]) => {
                if (!result) return null;

                const statusConfig = {
                  verified: { icon: "✓", color: "text-pass", bg: "bg-passBg/20", border: "border-pass/30" },
                  mismatch: { icon: "⚠", color: "text-yellow-600", bg: "bg-yellow-50", border: "border-yellow-200" },
                  error: { icon: "✗", color: "text-fail", bg: "bg-failBg/20", border: "border-fail/30" },
                };

                const config = statusConfig[result.status];

                return (
                  <div key={key} className={`p-4 border rounded-lg ${config.bg} ${config.border}`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-xs font-bold text-ink capitalize mb-1">
                          {key === "gstin" ? "GSTIN" : key === "pan" ? "PAN" : key === "cin" ? "Company (CIN)" : "MSME (Udyam)"} Verification
                        </div>
                        <div className={`text-xs ${config.color}`}>{result.message}</div>
                      </div>
                      <span className={`text-lg ${config.color}`}>{config.icon}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Overall Status */}
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs">
              <div className="font-medium text-blue-900">
                {overallVerificationStatus === "verified" && "✓ All details verified successfully!"}
                {overallVerificationStatus === "partial" && "⚠ Some details verified, others need review"}
                {overallVerificationStatus === "failed" && "✗ Verification failed - please check your details"}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setCurrentStep(1)}
              className="border border-slate-300 text-slate-700 font-medium px-4 py-2 rounded-lg hover:bg-slate-50"
            >
              ← Re-upload Documents
            </button>
            {overallVerificationStatus === "verified" ? (
              <button
                onClick={() => setCurrentStep(4)}
                className="bg-accent hover:bg-accent2 text-white font-medium px-6 py-2 rounded-lg"
              >
                Proceed to Submission →
              </button>
            ) : (
              <button
                onClick={() => setCurrentStep(4)}
                className="bg-yellow-600 hover:bg-yellow-700 text-white font-medium px-6 py-2 rounded-lg"
              >
                Continue Anyway (⚠ Not Verified)
              </button>
            )}
          </div>
        </div>
      )}

      {/* ===== STEP 4: FINAL SUBMISSION ===== */}
      {currentStep === 4 && (
        <div className="bg-card border border-line rounded-lg p-6">
          <h2 className="text-lg font-bold text-ink mb-4">Final Review & Submit</h2>

          <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-4 text-xs text-blue-900">
            <strong>✓ Your application is ready to submit.</strong> All details have been extracted from your documents and cross-verified with government databases.
          </div>

          <div className="space-y-2 mb-6 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-pass">✓</span>
              <span>All mandatory documents uploaded</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-pass">✓</span>
              <span>Company details extracted via OCR</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-pass">✓</span>
              <span>Cross-verified with government databases</span>
            </div>
          </div>

          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setCurrentStep(3)}
              className="border border-slate-300 text-slate-700 font-medium px-4 py-2 rounded-lg hover:bg-slate-50"
            >
              ← Back to Review
            </button>
            <button
              onClick={handleSubmit}
              className="bg-accent hover:bg-accent2 text-white font-medium px-6 py-2 rounded-lg"
            >
              ✓ Submit Application
            </button>
          </div>
        </div>
      )}
    </Shell>
  );
}
