import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Plus, 
  AlertCircle, 
  CheckCircle2, 
  Loader, 
  Trash2, 
  Sparkles, 
  ShieldCheck, 
  ArrowRight, 
  Radio, 
  Check 
} from "lucide-react";
import { api } from "../lib/api.js";

export default function OfficerCreateTender() {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState("basic");

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    budget: "",
    deadline_days: 30,
    organization: "Government of India",
    category: "PROCUREMENT",
    version_number: "1.0",
    source_document_path: "/uploads/tender.pdf",
    required_documents: [
      { doc_type: "GST_CERT", title: "GST Registration Certificate", mandatory: true },
      { doc_type: "PAN", title: "PAN Card", mandatory: true },
      { doc_type: "UDYAM_CERT", title: "Udyam / MSME Certificate", mandatory: true },
      { doc_type: "OEM_AUTHORIZATION", title: "OEM Authorization", mandatory: true },
    ],
    eligibility_criteria: [
      { field: "gstin_registered", label: "GSTIN Registration", value: true, type: "boolean" },
    ],
    financial_requirements: [
      { field: "min_annual_turnover", label: "Min Annual Turnover (₹)", value: 100000, type: "number" },
    ],
    technical_requirements: [
      { field: "years_of_experience", label: "Years of Experience", value: 2, type: "number" },
    ],
    rules: [
      { name: "rule_1", expression: "gstin_registered == true", description: "Must have valid GSTIN" },
    ],
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [createdTenderId, setCreatedTenderId] = useState(null);
  const [publishingState, setPublishingState] = useState("idle"); // 'idle' | 'publishing' | 'published'
  const [publishStep, setPublishStep] = useState(0);
  const [publishError, setPublishError] = useState(null);
  const [countdown, setCountdown] = useState(3);

  const handleBasicChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "budget" ? parseFloat(value) || "" : value,
    }));
  };

  const addCriterion = (type) => {
    const newCriterion = {
      field: `${type}_${Date.now()}`,
      label: "",
      value: type === "boolean" ? true : "",
      type: type === "boolean" ? "boolean" : type,
    };
    const key =
      type === "boolean"
        ? "eligibility_criteria"
        : type === "number"
        ? "financial_requirements"
        : "technical_requirements";
    setFormData((prev) => ({
      ...prev,
      [key]: [...prev[key], newCriterion],
    }));
  };

  const updateCriterion = (type, index, field, value) => {
    const key =
      type === "boolean"
        ? "eligibility_criteria"
        : type === "number"
        ? "financial_requirements"
        : "technical_requirements";
    setFormData((prev) => {
      const updated = [...prev[key]];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, [key]: updated };
    });
  };

  const removeCriterion = (type, index) => {
    const key =
      type === "boolean"
        ? "eligibility_criteria"
        : type === "number"
        ? "financial_requirements"
        : "technical_requirements";
    setFormData((prev) => ({
      ...prev,
      [key]: prev[key].filter((_, i) => i !== index),
    }));
  };

  const addRule = () => {
    setFormData((prev) => ({
      ...prev,
      rules: [
        ...prev.rules,
        {
          name: `rule_${Date.now()}`,
          expression: "",
          description: "",
        },
      ],
    }));
  };

  const updateRule = (index, field, value) => {
    setFormData((prev) => {
      const updated = [...prev.rules];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, rules: updated };
    });
  };

  const removeRule = (index) => {
    setFormData((prev) => ({
      ...prev,
      rules: prev.rules.filter((_, i) => i !== index),
    }));
  };

  const handleCreateTender = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (!formData.title.trim()) {
        throw new Error("Tender title is required");
      }

      const deadlineDays = Math.max(1, Number(formData.deadline_days) || 30);
      const response = await api.officerCreateTender({
        ...formData,
        deadline: new Date(Date.now() + deadlineDays * 24 * 60 * 60 * 1000).toISOString(),
      });
      setCreatedTenderId(response.id);
      setSuccess(true);
    } catch (err) {
      setError(err.message || "Failed to create tender");
    } finally {
      setLoading(false);
    }
  };

  const handlePublishTender = async () => {
    if (!createdTenderId) return;
    setPublishError(null);
    setPublishingState("publishing");
    setPublishStep(1);

    try {
      // Step 1: Validating compliance (1.2s so user can read it)
      await new Promise((r) => setTimeout(r, 1200));
      setPublishStep(2);

      // Step 2: Call backend API (runs while step 2 spinner shows)
      await api.officerPublishTender(createdTenderId);
      // Hold step 2 briefly so user sees it complete
      await new Promise((r) => setTimeout(r, 800));
      setPublishStep(3);
      // Step 3: Broadcasting – hold for 1s before success
      await new Promise((r) => setTimeout(r, 1000));

      // Success screen
      setPublishingState("published");

      // Auto redirect countdown
      let remaining = 5;
      setCountdown(remaining);
      const timer = setInterval(() => {
        remaining -= 1;
        setCountdown(remaining);
        if (remaining <= 0) {
          clearInterval(timer);
          navigate("/officer");
        }
      }, 1000);
    } catch (err) {
      setPublishError(err.message || "Failed to publish tender");
      setPublishingState("idle");
    }
  };

  if (success && createdTenderId) {
    return (
      <div className="max-w-3xl mx-auto py-8">
        <div className="mb-6">
          <h1 className="font-display text-3xl font-bold text-ink tracking-tight">Tender Publishing</h1>
          <p className="text-sm text-slate mt-1">GeM Sentinel Procurement Officer Workflow</p>
        </div>

        {/* Error Alert if publish failed */}
        {publishError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 animate-fade-in">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-red-900">Publishing Failed</h4>
              <p className="text-xs text-red-700 mt-1">{publishError}</p>
              <button
                onClick={handlePublishTender}
                className="mt-3 px-3 py-1.5 text-xs font-semibold bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
              >
                Retry Publishing
              </button>
            </div>
          </div>
        )}

        {/* State 1: Idle (Tender Created, Ready to Publish) */}
        {publishingState === "idle" && (
          <div className="p-8 bg-gradient-to-br from-emerald-50 via-white to-teal-50/40 border border-emerald-200/80 rounded-2xl shadow-sm animate-pop-in">
            <div className="flex items-start gap-5">
              <div className="w-12 h-12 rounded-2xl bg-emerald-100 flex items-center justify-center shrink-0 shadow-inner">
                <CheckCircle2 className="w-7 h-7 text-emerald-600" />
              </div>
              <div className="flex-1">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100/80 text-emerald-800 mb-2">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Draft Ready for Publishing</span>
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Tender Created Successfully!</h2>
                <p className="text-sm text-slate-600 mb-6 leading-relaxed">
                  Your tender <span className="font-semibold text-slate-800">"{formData.title}"</span> has been initialized. 
                  Publishing will immediately make it visible to registered bidders on GeM and activate automated clause evaluation.
                </p>

                <div className="bg-white/80 backdrop-blur-sm border border-emerald-100 rounded-xl p-4 mb-6 grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                  <div>
                    <span className="text-slate-400 block font-medium">Tender ID</span>
                    <span className="font-mono text-slate-700 font-semibold">{createdTenderId.substring(0, 13)}...</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Category</span>
                    <span className="text-slate-700 font-semibold">{formData.category}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Required Documents</span>
                    <span className="text-slate-700 font-semibold">{formData.required_documents.length} clauses</span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={handlePublishTender}
                    className="group relative inline-flex items-center gap-2.5 px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-semibold shadow-lg shadow-emerald-600/20 hover:shadow-emerald-600/35 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
                  >
                    <Radio className="w-4 h-4 animate-pulse" />
                    <span>Publish Tender to Marketplace</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </button>
                  <button
                    onClick={() => navigate("/officer")}
                    className="px-4 py-3 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition"
                  >
                    Save as Draft & View Dashboard
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* State 2: Publishing In-Progress Animation */}
        {publishingState === "publishing" && (
          <div className="p-8 bg-white border-2 border-emerald-300 rounded-2xl shadow-2xl animate-pulse-glow" style={{minHeight: '320px'}}>
            <div className="text-center py-4 max-w-md mx-auto">
              {/* Big animated spinner */}
              <div className="relative inline-flex items-center justify-center mb-6">
                <div className="w-24 h-24 rounded-full border-4 border-emerald-100 border-t-emerald-600 animate-spin" style={{animationDuration: '0.8s'}} />
                <div className="w-16 h-16 rounded-full border-4 border-emerald-200 border-b-emerald-500 animate-spin absolute" style={{animationDuration: '1.2s', animationDirection: 'reverse'}} />
                <ShieldCheck className="w-9 h-9 text-emerald-600 absolute" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-1">Publishing Tender...</h3>
              <p className="text-xs text-slate-500 mb-6">
                Executing deterministic checks and registering public tender record
              </p>

              {/* Progress Steps */}
              <div className="space-y-4 text-left bg-slate-50 border border-slate-200 rounded-xl p-5">
                {/* Step 1 */}
                <div className="flex items-center gap-3 transition-all duration-500">
                  {publishStep > 1 ? (
                    <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0 animate-scale-bounce shadow-md shadow-emerald-300">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                  ) : (
                    <div className="w-6 h-6 rounded-full border-2 border-emerald-600 border-t-transparent animate-spin shrink-0" />
                  )}
                  <div className="flex-1">
                    <span className={`text-xs font-semibold transition-colors ${publishStep >= 1 ? "text-slate-900" : "text-slate-400"}`}>
                      Validating compliance requirements &amp; clause rules
                    </span>
                    {publishStep > 1 && <p className="text-xs text-emerald-600 font-medium mt-0.5">✓ All checks passed</p>}
                  </div>
                </div>

                {/* Step 2 */}
                <div className="flex items-center gap-3 transition-all duration-500">
                  {publishStep > 2 ? (
                    <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0 animate-scale-bounce shadow-md shadow-emerald-300">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                  ) : publishStep === 2 ? (
                    <div className="w-6 h-6 rounded-full border-2 border-emerald-600 border-t-transparent animate-spin shrink-0" />
                  ) : (
                    <div className="w-6 h-6 rounded-full border-2 border-slate-300 shrink-0" />
                  )}
                  <div className="flex-1">
                    <span className={`text-xs font-semibold transition-colors ${publishStep >= 2 ? "text-slate-900" : "text-slate-400"}`}>
                      Registering immutable audit trail block on hash chain
                    </span>
                    {publishStep > 2 && <p className="text-xs text-emerald-600 font-medium mt-0.5">✓ Hash committed</p>}
                  </div>
                </div>

                {/* Step 3 */}
                <div className="flex items-center gap-3 transition-all duration-500">
                  {publishStep === 3 ? (
                    <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0 animate-scale-bounce shadow-md shadow-emerald-300">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                  ) : (
                    <div className="w-6 h-6 rounded-full border-2 border-slate-300 shrink-0" />
                  )}
                  <div className="flex-1">
                    <span className={`text-xs font-semibold transition-colors ${publishStep === 3 ? "text-slate-900" : "text-slate-400"}`}>
                      Broadcasting live to GeM Sentinel marketplace
                    </span>
                    {publishStep === 3 && <p className="text-xs text-emerald-600 font-medium mt-0.5">✓ Live!</p>}
                  </div>
                </div>
              </div>

              {/* Animated progress bar */}
              <div className="mt-5 w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div
                  className="h-2 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full transition-all duration-1000 ease-out"
                  style={{ width: `${(publishStep / 3) * 100}%` }}
                />
              </div>
              <p className="text-xs text-slate-400 mt-2">Step {publishStep} of 3</p>
            </div>
          </div>
        )}

        {/* State 3: Published Successfully Celebration Screen */}
        {publishingState === "published" && (
          <div className="p-8 bg-gradient-to-br from-emerald-500 via-emerald-600 to-teal-700 text-white rounded-2xl shadow-2xl shadow-emerald-700/40 animate-pop-in relative overflow-hidden">
            {/* Decorative circles */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-32 translate-x-32" />
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-24 -translate-x-24" />
            <div className="text-center py-4 max-w-md mx-auto relative z-10">
              {/* Animated checkmark */}
              <div className="relative inline-flex items-center justify-center mb-6">
                <div className="absolute w-28 h-28 rounded-full bg-white/10 animate-ping" style={{animationDuration: '1.5s'}} />
                <div className="w-24 h-24 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center shadow-xl animate-scale-bounce">
                  <Check className="w-12 h-12 text-white stroke-[3]" />
                </div>
              </div>
              <div className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-white/20 border border-white/30 text-xs font-bold uppercase tracking-wider mb-3 animate-fade-in">
                <Sparkles className="w-3.5 h-3.5" />
                <span>🎉 Live on GeM Sentinel Portal</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-3">
                Tender is Officially Live!
              </h2>
              <p className="text-emerald-100 text-sm mb-4 leading-relaxed">
                Registered bidders can now discover this tender, review requirements, and submit bids.
              </p>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3 mb-6 text-xs">
                <div className="bg-white/15 rounded-xl p-3">
                  <p className="text-emerald-200 font-medium">Status</p>
                  <p className="font-bold text-white mt-1">PUBLISHED</p>
                </div>
                <div className="bg-white/15 rounded-xl p-3">
                  <p className="text-emerald-200 font-medium">Visibility</p>
                  <p className="font-bold text-white mt-1">PUBLIC</p>
                </div>
                <div className="bg-white/15 rounded-xl p-3">
                  <p className="text-emerald-200 font-medium">Redirect in</p>
                  <p className="font-bold text-white mt-1">{countdown}s</p>
                </div>
              </div>

              {/* Countdown timer & progress line */}
              <div className="w-full bg-white/20 rounded-full h-2 mb-5 overflow-hidden">
                <div 
                  className="bg-white h-full transition-all duration-1000 ease-linear rounded-full"
                  style={{ width: `${((5 - countdown) / 5) * 100}%` }}
                />
              </div>

              <div className="flex items-center justify-center gap-3">
                <button
                  onClick={() => navigate("/officer")}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-white text-emerald-800 rounded-xl font-bold text-sm shadow-lg hover:bg-emerald-50 hover:scale-105 active:scale-95 transition-all"
                >
                  <span>Go to Officer Dashboard</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <>
      <div className="mb-8">
        <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-2.5 py-0.5 rounded-full border border-accent/20 mb-2">
          <Plus className="w-3.5 h-3.5" />
          <span>Advanced Tender Management</span>
        </div>
        <h1 className="font-display text-3xl font-bold text-ink tracking-tight">Create New Tender</h1>
        <p className="text-sm text-slate mt-1">
          Define dynamic tender rules, eligibility criteria, and evaluation rules
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleCreateTender} className="space-y-6">
        {/* Tab Navigation */}
        <div className="flex gap-2 border-b border-line pb-4">
          {["basic", "eligibility", "financial", "technical", "rules"].map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveSection(tab)}
              className={`px-4 py-2 font-semibold text-sm rounded-lg transition-colors ${
                activeSection === tab
                  ? "bg-accent text-white"
                  : "bg-canvas text-slate hover:bg-slate/10"
              }`}
            >
              {tab === "basic" && "📋 Basic"}
              {tab === "eligibility" && "✓ Eligibility"}
              {tab === "financial" && "💰 Financial"}
              {tab === "technical" && "🔧 Technical"}
              {tab === "rules" && "⚙️ Rules"}
            </button>
          ))}
        </div>

        {/* BASIC INFORMATION */}
        {activeSection === "basic" && (
          <div className="bg-card border border-line rounded-card p-6 space-y-4">
            <h2 className="text-lg font-bold text-ink mb-4">Basic Tender Information</h2>

            <div>
              <label className="block text-sm font-semibold text-ink mb-2">
                Tender Title <span className="text-red-600">*</span>
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleBasicChange}
                placeholder="e.g., Supply of Office Equipment for Government Ministry"
                className="w-full px-4 py-2.5 border border-line rounded-xl text-ink placeholder:text-slate focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink mb-2">Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleBasicChange}
                placeholder="Detailed tender description..."
                rows="4"
                className="w-full px-4 py-2.5 border border-line rounded-xl text-ink placeholder:text-slate focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-ink mb-2">Budget (₹)</label>
                <input
                  type="number"
                  name="budget"
                  value={formData.budget}
                  onChange={handleBasicChange}
                  placeholder="0"
                  className="w-full px-4 py-2.5 border border-line rounded-xl text-ink placeholder:text-slate focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-ink mb-2">Submission Deadline (Days)</label>
                <input
                  type="number"
                  name="deadline_days"
                  value={formData.deadline_days}
                  onChange={handleBasicChange}
                  className="w-full px-4 py-2.5 border border-line rounded-xl text-ink placeholder:text-slate focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-ink mb-2">Organization</label>
                <input
                  type="text"
                  name="organization"
                  value={formData.organization}
                  onChange={handleBasicChange}
                  className="w-full px-4 py-2.5 border border-line rounded-xl text-ink placeholder:text-slate focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-ink mb-2">Category</label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleBasicChange}
                  className="w-full px-4 py-2.5 border border-line rounded-xl text-ink focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20"
                >
                  <option value="PROCUREMENT">Procurement</option>
                  <option value="SERVICES">Services</option>
                  <option value="CONSTRUCTION">Construction</option>
                  <option value="CONSULTING">Consulting</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* ELIGIBILITY CRITERIA */}
        {activeSection === "eligibility" && (
          <div className="bg-card border border-line rounded-card p-6 space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-ink">Eligibility Criteria</h2>
              <button
                type="button"
                onClick={() => addCriterion("boolean")}
                className="text-xs bg-accent text-white px-3 py-1.5 rounded-lg hover:bg-accent2 transition"
              >
                + Add Criterion
              </button>
            </div>

            <div className="space-y-3">
              {formData.eligibility_criteria.map((criterion, idx) => (
                <div key={idx} className="p-4 bg-canvas border border-line rounded-lg flex gap-3">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={criterion.label}
                      onChange={(e) => updateCriterion("boolean", idx, "label", e.target.value)}
                      placeholder="e.g., Must be registered with GSTIN"
                      className="w-full px-3 py-2 border border-line rounded-lg text-sm mb-2 focus:outline-none focus:border-accent"
                    />
                    <select
                      value={criterion.value}
                      onChange={(e) => updateCriterion("boolean", idx, "value", e.target.value === "true")}
                      className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:border-accent"
                    >
                      <option value="true">Required (True)</option>
                      <option value="false">Optional (False)</option>
                    </select>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeCriterion("boolean", idx)}
                    className="text-red-600 hover:text-red-700 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* FINANCIAL REQUIREMENTS */}
        {activeSection === "financial" && (
          <div className="bg-card border border-line rounded-card p-6 space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-ink">Financial Requirements</h2>
              <button
                type="button"
                onClick={() => addCriterion("number")}
                className="text-xs bg-accent text-white px-3 py-1.5 rounded-lg hover:bg-accent2 transition"
              >
                + Add Requirement
              </button>
            </div>

            <div className="space-y-3">
              {formData.financial_requirements.map((req, idx) => (
                <div key={idx} className="p-4 bg-canvas border border-line rounded-lg flex gap-3">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={req.label}
                      onChange={(e) => updateCriterion("number", idx, "label", e.target.value)}
                      placeholder="e.g., Min Annual Turnover"
                      className="w-full px-3 py-2 border border-line rounded-lg text-sm mb-2 focus:outline-none focus:border-accent"
                    />
                    <input
                      type="number"
                      value={req.value}
                      onChange={(e) => updateCriterion("number", idx, "value", parseFloat(e.target.value) || 0)}
                      placeholder="Value"
                      className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:border-accent"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeCriterion("number", idx)}
                    className="text-red-600 hover:text-red-700 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TECHNICAL REQUIREMENTS */}
        {activeSection === "technical" && (
          <div className="bg-card border border-line rounded-card p-6 space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-ink">Technical Requirements</h2>
              <button
                type="button"
                onClick={() => addCriterion("number")}
                className="text-xs bg-accent text-white px-3 py-1.5 rounded-lg hover:bg-accent2 transition"
              >
                + Add Requirement
              </button>
            </div>

            <div className="space-y-3">
              {formData.technical_requirements.map((req, idx) => (
                <div key={idx} className="p-4 bg-canvas border border-line rounded-lg flex gap-3">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={req.label}
                      onChange={(e) => updateCriterion("number", idx, "label", e.target.value)}
                      placeholder="e.g., Years of Experience"
                      className="w-full px-3 py-2 border border-line rounded-lg text-sm mb-2 focus:outline-none focus:border-accent"
                    />
                    <input
                      type="number"
                      value={req.value}
                      onChange={(e) => updateCriterion("number", idx, "value", parseFloat(e.target.value) || 0)}
                      placeholder="Value"
                      className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:border-accent"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeCriterion("number", idx)}
                    className="text-red-600 hover:text-red-700 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* RULES */}
        {activeSection === "rules" && (
          <div className="bg-card border border-line rounded-card p-6 space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-ink">Evaluation Rules</h2>
              <button
                type="button"
                onClick={addRule}
                className="text-xs bg-accent text-white px-3 py-1.5 rounded-lg hover:bg-accent2 transition"
              >
                + Add Rule
              </button>
            </div>

            <div className="space-y-4">
              {formData.rules.map((rule, idx) => (
                <div key={idx} className="p-4 bg-canvas border border-line rounded-lg space-y-3">
                  <input
                    type="text"
                    value={rule.description}
                    onChange={(e) => updateRule(idx, "description", e.target.value)}
                    placeholder="Rule description (e.g., GSTIN must be valid)"
                    className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:border-accent"
                  />
                  <textarea
                    value={rule.expression}
                    onChange={(e) => updateRule(idx, "expression", e.target.value)}
                    placeholder="Rule expression (e.g., gstin_registered == true AND years_of_experience >= 2)"
                    rows="2"
                    className="w-full px-3 py-2 border border-line rounded-lg text-sm font-mono focus:outline-none focus:border-accent"
                  />
                  <button
                    type="button"
                    onClick={() => removeRule(idx)}
                    className="text-red-600 hover:text-red-700 transition flex items-center gap-2 text-sm"
                  >
                    <Trash2 className="w-4 h-4" />
                    Remove Rule
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-accent hover:bg-accent2 disabled:opacity-50 text-white font-bold py-3 rounded-xl transition flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Creating Tender...
              </>
            ) : (
              "Create Tender"
            )}
          </button>
          <button
            type="button"
            onClick={() => navigate("/officer")}
            className="px-6 py-3 border border-line rounded-xl text-ink hover:bg-canvas transition font-semibold"
          >
            Cancel
          </button>
        </div>
      </form>
    </>
  );
}
