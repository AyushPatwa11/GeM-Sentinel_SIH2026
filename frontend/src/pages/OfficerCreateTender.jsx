import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, AlertCircle, CheckCircle2, Loader, Trash2 } from "lucide-react";
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

      const response = await api.officerCreateTender(formData);
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
    setError(null);

    try {
      await api.officerPublishTender(createdTenderId);
      setTimeout(() => {
        navigate("/officer");
      }, 1500);
    } catch (err) {
      setError(err.message || "Failed to publish tender");
    }
  };

  if (success && createdTenderId) {
    return (
      <>
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold text-ink tracking-tight">Create New Tender</h1>
        </div>
        <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl">
          <div className="flex items-start gap-4">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-emerald-900 mb-1">Tender Created Successfully!</h3>
              <p className="text-sm text-emerald-800 mb-4">
                Your tender with custom rules and eligibility criteria has been created. Publish it to make it visible to bidders.
              </p>
              <button
                onClick={handlePublishTender}
                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition-colors"
              >
                <CheckCircle2 className="w-4 h-4" />
                Publish Tender
              </button>
            </div>
          </div>
        </div>
      </>
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
