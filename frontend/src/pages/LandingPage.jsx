import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

export default function LandingPage() {
  const navigate = useNavigate();
  const [activeTickerIndex, setActiveTickerIndex] = useState(0);
  const [isTickerPaused, setIsTickerPaused] = useState(false);

  const newsItems = [
    {
      tag: "PIB Press Release — July 2026",
      title: "CCI Penalizes HP India for GeM Tender Manipulation",
      category: "Enforcement & Anti-Collusion",
      summary:
        "In 2026 the Competition Commission of India fined HP India ₹126.87 crore, plus penalties on five of its resellers, after finding the company had been dictating bid prices and blocking reseller participation in GeM tenders to benefit itself — exactly the kind of statutory/eligibility manipulation this platform is built to surface.",
      source: "Press Information Bureau (PIB)",
      url: "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2284274&reg=3&lang=1",
      badgeColor: "text-fail bg-failBg border-fail/20",
    },
    {
      tag: "Times of India — Regional Report",
      title: "Smart Classroom Tender Fraud Investigation",
      category: "Tender Fraud & Document Integrity",
      summary:
        "Cases of tender and procurement-linked fraud continue to surface in local reporting — a reminder that manual, document-based verification leaves room for manipulation at every stage of the process.",
      source: "Times of India (Indore)",
      url: "https://timesofindia.indiatimes.com/city/indore/programmer-firm-owner-booked-for-smart-classroom-tender-fraud/articleshowprint/132871490.cms",
      badgeColor: "text-review bg-reviewBg border-review/20",
    },
    {
      tag: "PIB Press Release — August 2026",
      title: "GeM Marks 10 Years: ₹20 Lakh Cr+ Cumulative GMV",
      category: "Scale & Economic Impact",
      summary:
        "GeM marked ten years of operation in August 2026 with a cumulative Gross Merchandise Value exceeding ₹20 lakh crore across more than 3.78 crore orders — annual GMV alone crossed ₹5 lakh crore in each of the last two fiscal years, with an IIT Delhi study estimating ₹1.76 lakh crore in net social savings through the platform. At this scale, even small percentage gains in verification speed and accuracy translate into enormous absolute time and cost savings.",
      source: "Press Information Bureau (PIB)",
      url: "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2296138&reg=48&lang=1",
      badgeColor: "text-accent bg-accent/10 border-accent/20",
    },
  ];

  // Auto rotate news strip when not paused
  useEffect(() => {
    if (isTickerPaused) return;
    const interval = setInterval(() => {
      setActiveTickerIndex((prev) => (prev + 1) % newsItems.length);
    }, 6000);
    return () => clearInterval(interval);
  }, [isTickerPaused, newsItems.length]);

  return (
    <div className="min-h-screen bg-canvas text-ink font-body selection:bg-accent/20">
      {/* ─────────────────────────────────────────────────────────────
          NAVBAR
      ───────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-ink/95 backdrop-blur-md border-b border-white/10 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center shadow-md shadow-accent/30">
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" className="w-5 h-5">
                <path d="M12 2 4 6v6c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V6l-8-4Z" />
                <path d="m9 12 2 2 4-4" />
              </svg>
            </div>
            <div>
              <span className="font-display font-bold text-lg tracking-tight">GeM Sentinel</span>
              <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-accent/20 text-blue-200 border border-accent/30">
                SIH 2026 • PS #26100
              </span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-7 text-sm font-medium text-white/70">
            <a href="#problem" className="hover:text-white transition-colors">The Problem</a>
            <a href="#evidence" className="hover:text-white transition-colors">Verified Cases</a>
            <a href="#solution" className="hover:text-white transition-colors">Architecture</a>
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#workflow" className="hover:text-white transition-colors">Workflow</a>
            <a href="#roadmap" className="hover:text-white transition-colors">Tech & Roadmap</a>
            <a href="#impact" className="hover:text-white transition-colors">Impact</a>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="text-sm font-medium text-white/80 hover:text-white px-3 py-1.5 rounded-lg transition-colors hidden sm:block"
            >
              Sign In
            </Link>
            <Link
              to="/login"
              className="bg-accent hover:bg-accent2 text-white text-sm font-medium px-4 py-2 rounded-lg shadow-sm shadow-accent/20 transition-all hover:scale-[1.02]"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 1: HERO
      ───────────────────────────────────────────────────────────── */}
      <section className="relative bg-ink text-white overflow-hidden pt-14 pb-20 lg:pt-20 lg:pb-28 border-b border-white/10">
        {/* Dotted Grid Background Texture */}
        <div
          className="absolute inset-0 opacity-[0.08]"
          style={{
            backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />

        {/* Ambient Gradient Glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-accent/20 rounded-full blur-[120px] pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/15 text-xs font-medium text-white/90 mb-6 backdrop-blur-sm">
                <span className="w-2 h-2 rounded-full bg-pass animate-pulse" />
                <span>Next-Gen Procurement Compliance & Risk Shield</span>
              </div>

              <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.08] tracking-tight">
                AI-Powered Bid Compliance Verification for GeM Procurement.
              </h1>

              <p className="mt-6 text-lg sm:text-xl text-white/75 leading-relaxed max-w-2xl font-light">
                <strong className="text-white font-semibold">AI assists, authoritative sources verify, deterministic rules decide</strong> — and the procurement officer always retains final authority. Zero blind trust in LLMs.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-4">
                <button
                  onClick={() => navigate("/login")}
                  className="bg-accent hover:bg-accent2 text-white font-medium px-6 py-3.5 rounded-xl shadow-lg shadow-accent/30 transition-all hover:scale-[1.02] flex items-center gap-2 text-base"
                >
                  <span>Get Started</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="w-4 h-4">
                    <path d="M5 12h14m-7-7 7 7-7 7" />
                  </svg>
                </button>

                <a
                  href="#workflow"
                  className="bg-white/10 hover:bg-white/15 text-white border border-white/20 font-medium px-5 py-3.5 rounded-xl transition-all flex items-center gap-2 text-base"
                >
                  <span>See How It Works</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
                    <path d="m6 9 6 6 6-6" />
                  </svg>
                </a>
              </div>

              {/* Quick Pillars under Hero */}
              <div className="mt-12 pt-8 border-t border-white/10 grid grid-cols-2 sm:grid-cols-3 gap-6 text-xs text-white/70">
                <div>
                  <div className="text-white font-semibold text-sm mb-1 flex items-center gap-1.5">
                    <span className="text-pass">✓</span> Deterministic Rules
                  </div>
                  <span>AND/OR logic & waivers evaluated with 100% mathematical precision.</span>
                </div>
                <div>
                  <div className="text-white font-semibold text-sm mb-1 flex items-center gap-1.5">
                    <span className="text-pass">✓</span> Evidence-Linked
                  </div>
                  <span>Every verdict cites exact source records, page numbers, and APIs.</span>
                </div>
                <div>
                  <div className="text-white font-semibold text-sm mb-1 flex items-center gap-1.5">
                    <span className="text-pass">✓</span> Tamper-Evident
                  </div>
                  <span>Database-enforced, append-only logs for every officer decision.</span>
                </div>
              </div>
            </div>

            {/* Interactive Hero Visual Showcase */}
            <div className="lg:col-span-5">
              <div className="bg-ink2/90 border border-white/15 rounded-2xl p-6 shadow-2xl backdrop-blur-xl relative overflow-hidden">
                <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-5">
                  <div className="flex items-center gap-2.5">
                    <span className="w-3 h-3 rounded-full bg-red-500/80 inline-block" />
                    <span className="w-3 h-3 rounded-full bg-yellow-500/80 inline-block" />
                    <span className="w-3 h-3 rounded-full bg-green-500/80 inline-block" />
                    <span className="text-xs font-mono text-white/60 ml-2">Tender GeM/2026/T-101</span>
                  </div>
                  <span className="px-2.5 py-1 rounded text-[11px] font-mono bg-pass/20 text-pass border border-pass/30 font-medium">
                    STAGE 2 PASS
                  </span>
                </div>

                {/* Sample Verification Card */}
                <div className="space-y-3.5">
                  <div className="bg-white/5 rounded-xl p-3.5 border border-white/10">
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-semibold text-white">Bidder #101: Bharat ElectroTech Pvt Ltd</span>
                      <span className="text-emerald-400 font-mono font-medium">Compliance: 100%</span>
                    </div>
                    <div className="text-[11px] text-white/60">
                      MSME / UDYAM-MH-01-0023456 • GSTIN: 27AABCB1234F1Z5
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-white/5 p-3 rounded-lg border border-white/10">
                      <div className="text-[11px] text-white/50 mb-1">EMD Deposit Requirement</div>
                      <div className="flex items-center gap-1.5 text-xs text-white font-medium">
                        <span className="text-pass">●</span>
                        <span>Exempt (MSME Valid)</span>
                      </div>
                    </div>
                    <div className="bg-white/5 p-3 rounded-lg border border-white/10">
                      <div className="text-[11px] text-white/50 mb-1">Independent Risk Score</div>
                      <div className="flex items-center gap-1.5 text-xs text-amber-300 font-medium">
                        <span>●</span>
                        <span>Low Risk (12/100)</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-xl p-3.5 border border-white/10 text-xs space-y-2">
                    <div className="text-[11px] font-mono text-white/50 uppercase tracking-wider">
                      Authoritative Adapter Verification
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-white/80 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-pass" /> MCA Company Master Data (Live data.gov.in)
                      </span>
                      <span className="text-emerald-400 font-mono">ACTIVE</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-white/80 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-pass" /> GSTN Active & 3Y Returns Filed
                      </span>
                      <span className="text-emerald-400 font-mono">VERIFIED</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-white/80 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-pass" /> GeM Central Debarment / Blacklist
                      </span>
                      <span className="text-emerald-400 font-mono">CLEAR</span>
                    </div>
                  </div>

                  <div className="p-2.5 bg-accent/20 border border-accent/30 rounded-lg text-[11px] text-blue-200 flex items-center justify-between">
                    <span>Officer Action Required:</span>
                    <span className="font-semibold text-white">Review & Affirm</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 2: THE PROBLEM (REAL, SOURCED, NOT INVENTED)
      ───────────────────────────────────────────────────────────── */}
      <section id="problem" className="py-20 bg-white border-b border-line">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-3 py-1 rounded-full border border-accent/20">
              The Reality of Public Procurement
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3">
              Why Manual Verification Fails at GeM Scale
            </h2>
            <p className="mt-4 text-base sm:text-lg text-slate leading-relaxed">
              Grounded in the problem defined in <strong className="text-ink">Problem Statement #26100</strong>: Procurement officers are forced to manually cross-check hundreds of bidder documents across isolated, disparate government portals.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-canvas p-7 rounded-card border border-line flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-failBg text-fail flex items-center justify-center font-display font-bold text-xl mb-5">
                  60-80%
                </div>
                <h3 className="font-display font-semibold text-lg text-ink mb-2">
                  Crippling Verification Overhead
                </h3>
                <p className="text-sm text-slate leading-relaxed">
                  Evaluating a single multi-crore tender with dozens of bidders requires hundreds of manual portal visits across Udyam, GSTN, PAN/IT, EPFO/ESIC, NSIC, Startup India, and DigiLocker.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-line/80 text-xs font-mono text-slate">
                Bottleneck in tender award lifecycle
              </div>
            </div>

            <div className="bg-canvas p-7 rounded-card border border-line flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-reviewBg text-review flex items-center justify-center font-display font-bold text-xl mb-5">
                  8+
                </div>
                <h3 className="font-display font-semibold text-lg text-ink mb-2">
                  Disconnected Government Silos
                </h3>
                <p className="text-sm text-slate leading-relaxed">
                  No single unified verification layer exists. Officers must manually correlate GST returns, MSME classifications, and debarment registries, leaving critical gaps for fraud and cartelization.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-line/80 text-xs font-mono text-slate">
                Vulnerable to forged certificates
              </div>
            </div>

            <div className="bg-canvas p-7 rounded-card border border-line flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-accent/10 text-accent flex items-center justify-center font-display font-bold text-xl mb-5">
                  Zero
                </div>
                <h3 className="font-display font-semibold text-lg text-ink mb-2">
                  Auditability in Black-Box LLMs
                </h3>
                <p className="text-sm text-slate leading-relaxed">
                  Generic AI models hallucinate compliance rules, miss subtle MSME exemption clauses, and fail to provide the statutory, tamper-evident audit trails legally demanded by procurement law.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-line/80 text-xs font-mono text-slate">
                High legal & scrutiny risk
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 3: NEWS TICKER / VERIFIED REFERENCE STRIP
      ───────────────────────────────────────────────────────────── */}
      <section id="evidence" className="py-16 bg-canvas border-b border-line">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-fail mb-1">
                <span className="w-2 h-2 rounded-full bg-fail" />
                <span>Verified Incidents & Procurement Scale</span>
              </div>
              <h2 className="font-display text-2xl sm:text-3xl font-bold text-ink">
                Documented Evidence & Real-World Precedents
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate mr-2">Click cards to view verified government sources</span>
              <div className="flex gap-1">
                {newsItems.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveTickerIndex(i)}
                    className={`w-2.5 h-2.5 rounded-full transition-all ${
                      activeTickerIndex === i ? "w-6 bg-accent" : "bg-line hover:bg-slate"
                    }`}
                    aria-label={`Go to slide ${i + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Cards Grid / Ticker */}
          <div
            className="grid md:grid-cols-3 gap-6"
            onMouseEnter={() => setIsTickerPaused(true)}
            onMouseLeave={() => setIsTickerPaused(false)}
          >
            {newsItems.map((item, idx) => {
              const isActive = activeTickerIndex === idx;
              return (
                <div
                  key={idx}
                  className={`bg-card border rounded-card p-6 flex flex-col justify-between transition-all duration-300 ${
                    isActive ? "border-accent ring-2 ring-accent/20 shadow-md -translate-y-1" : "border-line hover:border-slate/40"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-md border ${item.badgeColor}`}>
                        {item.category}
                      </span>
                    </div>

                    <h3 className="font-display font-semibold text-base text-ink mb-2.5">
                      {item.title}
                    </h3>

                    <p className="text-xs text-slate leading-relaxed mb-4">
                      {item.summary}
                    </p>
                  </div>

                  <div className="pt-4 border-t border-line flex items-center justify-between text-xs">
                    <span className="font-mono text-[11px] text-slate">{item.source}</span>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent hover:text-accent2 font-medium inline-flex items-center gap-1 group"
                    >
                      <span>Official Source</span>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                        <path d="M15 3h6v6" />
                        <path d="M10 14 21 3" />
                      </svg>
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 4: THE SOLUTION
      ───────────────────────────────────────────────────────────── */}
      <section id="solution" className="py-20 bg-white border-b border-line">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-semibold uppercase tracking-wider text-pass bg-passBg px-3 py-1 rounded-full border border-pass/20">
              The Architectural Answer
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3">
              Deterministic Verification with Swappable Source Adapters
            </h2>
            <p className="mt-4 text-base sm:text-lg text-slate leading-relaxed">
              We replace manual scrutiny and black-box AI hallucinations with a structured, verifiable pipeline that turns tender clauses into formal logic and checks live government databases.
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            <div className="p-6 rounded-card bg-canvas border border-line relative group hover:border-accent transition-colors">
              <div className="w-10 h-10 rounded-lg bg-ink text-white flex items-center justify-center font-mono font-bold text-sm mb-4">
                01
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-2">
                Clause Extraction into Formal Logic
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Tender requirements are decomposed into structured evaluation rules (turnover thresholds, MSME waivers, experience, EMD logic) with strict syntax.
              </p>
            </div>

            <div className="p-6 rounded-card bg-canvas border border-line relative group hover:border-accent transition-colors">
              <div className="w-10 h-10 rounded-lg bg-accent text-white flex items-center justify-center font-mono font-bold text-sm mb-4">
                02
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-2">
                Swappable Authoritative Adapters
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Pluggable adapters for GSTN, MCA, Udyam, DigiLocker, and NSIC verify claims directly against authoritative registries, switching effortlessly between mock and live APIs.
              </p>
            </div>

            <div className="p-6 rounded-card bg-canvas border border-line relative group hover:border-accent transition-colors">
              <div className="w-10 h-10 rounded-lg bg-pass text-white flex items-center justify-center font-mono font-bold text-sm mb-4">
                03
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-2">
                Independent Risk & Compliance Scoring
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                A bidder can be 100% compliant but high-risk (e.g. newly incorporated entity bidding on maximum tender size). We never blend these into an ambiguous single score.
              </p>
            </div>

            <div className="p-6 rounded-card bg-canvas border border-line relative group hover:border-accent transition-colors">
              <div className="w-10 h-10 rounded-lg bg-ink2 text-white flex items-center justify-center font-mono font-bold text-sm mb-4">
                04
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-2">
                Evidence-Linked Officer Verdict
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                The platform recommends — the human officer decides. Every verdict links to the exact source document and page, with database-enforced justification for overrides.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 5: FEATURES GRID (WHAT IS ACTUALLY BUILT)
      ───────────────────────────────────────────────────────────── */}
      <section id="features" className="py-20 bg-canvas border-b border-line">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-3 py-1 rounded-full border border-accent/20">
              Core Capabilities
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3">
              Engineered for Compliance, Integrity, and Auditability
            </h2>
            <p className="mt-3 text-base text-slate">
              Every feature below is implemented in the active codebase — strictly grounded in production-grade architecture.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Feature 1 */}
            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-lg bg-accent/10 text-accent flex items-center justify-center mb-4">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <path d="m9 15 2 2 4-4" />
                </svg>
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-1.5">
                Deterministic Rule Engine
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Handles complex AND/OR/NOT and exemption logic (such as statutory MSME/Startup EMD waivers) with verifiable precision, never heuristic guesses.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-lg bg-passBg text-pass flex items-center justify-center mb-4">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                </svg>
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-1.5">
                Evidence-Linked Findings
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Every single compliance result links directly to a verified document, page reference, API payload, or statutory database response.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-lg bg-reviewBg text-review flex items-center justify-center mb-4">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  <path d="M12 8v4" />
                  <path d="M12 16h.01" />
                </svg>
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-1.5">
                Independent Risk Scoring
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Compliance (rule adherence) and Risk (anomalies, concentration, age, capacity) are scored on separate orthogonal axes.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-lg bg-accent/10 text-accent flex items-center justify-center mb-4">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                  <rect width="18" height="18" x="3" y="3" rx="2" />
                  <path d="M7 7h10M7 12h10M7 17h10" />
                </svg>
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-1.5">
                Swappable Adapter Architecture
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Registry pattern supporting live data.gov.in MCA integration, GSTN, Udyam, NSIC, and DigiLocker with seamless mock fallbacks.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-lg bg-failBg text-fail flex items-center justify-center mb-4">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-1.5">
                Two-Stage Verification
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Stage 1 checks document completeness, signatures, and validity; Stage 2 evaluates technical & financial tender rules without conflation.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-lg bg-ink text-white flex items-center justify-center mb-4">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                  <circle cx="12" cy="7" r="4" />
                  <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
                </svg>
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-1.5">
                Human-In-The-Loop Always
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                The platform only provides evidence-linked recommendations. Overriding an automated recommendation mandates entering a signed justification.
              </p>
            </div>

            {/* Feature 7 */}
            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-lg bg-passBg text-pass flex items-center justify-center mb-4">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-1.5">
                Tamper-Evident Audit Trail
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Every evaluation step, adapter response, officer remark, and final verdict is saved in an append-only, legally defensible audit ledger.
              </p>
            </div>

            {/* Feature 8 */}
            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-lg bg-accent/10 text-accent flex items-center justify-center mb-4">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                  <polyline points="9 11 12 14 22 4" />
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                </svg>
              </div>
              <h3 className="font-display font-semibold text-base text-ink mb-1.5">
                Bidder Readiness Pre-Check
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Empowers bidders to diagnose missing documents and compliance gaps before submission, drastically cutting administrative rejections.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 6: WORKFLOW VISUAL
      ───────────────────────────────────────────────────────────── */}
      <section id="workflow" className="py-20 bg-white border-b border-line">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-3 py-1 rounded-full border border-accent/20">
              End-to-End Execution Flow
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3">
              The 6-Step Verification Lifecycle
            </h2>
            <p className="mt-3 text-base text-slate">
              From bid submission to final officer verdict — transparency and accountability at every touchpoint.
            </p>
          </div>

          {/* Flow Diagram Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-canvas p-4 rounded-xl border border-line text-center flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-ink text-white font-mono text-xs flex items-center justify-center font-bold mb-3">
                1
              </div>
              <h4 className="font-display font-semibold text-sm text-ink mb-1">Bidder Submits</h4>
              <p className="text-[11px] text-slate">Documents & identifiers submitted via portal</p>
            </div>

            <div className="bg-canvas p-4 rounded-xl border border-line text-center flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-accent text-white font-mono text-xs flex items-center justify-center font-bold mb-3">
                2
              </div>
              <h4 className="font-display font-semibold text-sm text-ink mb-1">Stage 1 Scrutiny</h4>
              <p className="text-[11px] text-slate">Document completeness, signatures & authenticity</p>
            </div>

            <div className="bg-canvas p-4 rounded-xl border border-line text-center flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-pass text-white font-mono text-xs flex items-center justify-center font-bold mb-3">
                3
              </div>
              <h4 className="font-display font-semibold text-sm text-ink mb-1">Stage 2 Rules</h4>
              <p className="text-[11px] text-slate">Deterministic evaluation against tender criteria</p>
            </div>

            <div className="bg-canvas p-4 rounded-xl border border-line text-center flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-review text-white font-mono text-xs flex items-center justify-center font-bold mb-3">
                4
              </div>
              <h4 className="font-display font-semibold text-sm text-ink mb-1">Risk Scoring</h4>
              <p className="text-[11px] text-slate">Independent anomalies & capacity flags computed</p>
            </div>

            <div className="bg-canvas p-4 rounded-xl border border-line text-center flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-ink2 text-white font-mono text-xs flex items-center justify-center font-bold mb-3">
                5
              </div>
              <h4 className="font-display font-semibold text-sm text-ink mb-1">Officer Verdict</h4>
              <p className="text-[11px] text-slate">Officer reviews evidence and records signed decision</p>
            </div>

            <div className="bg-canvas p-4 rounded-xl border border-line text-center flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-pass text-white font-mono text-xs flex items-center justify-center font-bold mb-3">
                6
              </div>
              <h4 className="font-display font-semibold text-sm text-ink mb-1">Live Reflection</h4>
              <p className="text-[11px] text-slate">Status & audit log updated for bidder & auditors</p>
            </div>
          </div>

          <div className="mt-8 p-4 bg-canvas border border-line rounded-xl text-center text-xs text-slate">
            <strong className="text-ink">Strict Security Invariant:</strong> The automated system delivers recommendations with complete source citation — decisions are made exclusively by authorized procurement officers.
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 7: TECHNOLOGY & ROADMAP (TWO-COLUMN HONEST LAYOUT)
      ───────────────────────────────────────────────────────────── */}
      <section id="roadmap" className="py-20 bg-canvas border-b border-line">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-3 py-1 rounded-full border border-accent/20">
              Technical Architecture & Evolution
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3">
              Technology Stack & Credible Roadmap
            </h2>
            <p className="mt-3 text-base text-slate">
              Clear demarcation between what is live and running in the repository today versus upcoming platform milestones.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Column 1: Built Today */}
            <div className="bg-card p-8 rounded-card border border-line">
              <div className="flex items-center gap-2 mb-6">
                <span className="w-3 h-3 rounded-full bg-pass" />
                <h3 className="font-display font-bold text-xl text-ink">Built & Running Today</h3>
              </div>

              <ul className="space-y-4 text-xs text-slate">
                <li className="flex items-start gap-2.5">
                  <span className="text-pass font-bold text-sm">✓</span>
                  <div>
                    <strong className="text-ink text-sm block">Python / FastAPI Backend</strong>
                    Async REST API with Pydantic validation, structured endpoints, and OpenAPI spec.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-pass font-bold text-sm">✓</span>
                  <div>
                    <strong className="text-ink text-sm block">Deterministic Rule & Risk Engines</strong>
                    Zero LLM dependency in evaluation core — 100% reproducible compliance logic.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-pass font-bold text-sm">✓</span>
                  <div>
                    <strong className="text-ink text-sm block">Live data.gov.in MCA Integration</strong>
                    Real-time adapter querying official Company Master Data API alongside mock adapters for GSTN, Udyam, NSIC, and DigiLocker.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-pass font-bold text-sm">✓</span>
                  <div>
                    <strong className="text-ink text-sm block">React 18 + Vite + Tailwind Frontend</strong>
                    Role-based officer & bidder views, real-time readiness check, and audit trail ledger.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-pass font-bold text-sm">✓</span>
                  <div>
                    <strong className="text-ink text-sm block">Tamper-Evident Audit Schema</strong>
                    Append-only logging of officer verdicts, mandatory override justification, and source evidence.
                  </div>
                </li>
              </ul>
            </div>

            {/* Column 2: Coming Next */}
            <div className="bg-card p-8 rounded-card border border-line">
              <div className="flex items-center gap-2 mb-6">
                <span className="w-3 h-3 rounded-full bg-accent" />
                <h3 className="font-display font-bold text-xl text-ink">Next Phase Roadmap</h3>
              </div>

              <ul className="space-y-4 text-xs text-slate">
                <li className="flex items-start gap-2.5">
                  <span className="text-accent font-bold text-sm">→</span>
                  <div>
                    <strong className="text-ink text-sm block">OCR & Entity Extraction Pipeline</strong>
                    LayoutLM / Tesseract OCR pipeline for extracting unstructured PDF bid documents into verified schema.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-accent font-bold text-sm">→</span>
                  <div>
                    <strong className="text-ink text-sm block">Grounded Tender Clause Extraction</strong>
                    Constrained LLM extraction of complex tender terms validated against an allowable rule grammar.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-accent font-bold text-sm">→</span>
                  <div>
                    <strong className="text-ink text-sm block">Real DigiLocker Partner API</strong>
                    Production DigiLocker gateway integration for cryptographically authentic document fetching.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-accent font-bold text-sm">→</span>
                  <div>
                    <strong className="text-ink text-sm block">Corrigendum Impact Engine</strong>
                    Automated re-evaluation of all submitted bids whenever tender amendments or corrigenda are published.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-accent font-bold text-sm">→</span>
                  <div>
                    <strong className="text-ink text-sm block">Tender Quality Assistant</strong>
                    Pre-publishing clause ambiguity and anti-competitive clause detector for tender drafting officers.
                  </div>
                </li>
              </ul>
            </div>
          </div>

          {/* Honest Boundaries Disclaimer */}
          <div className="mt-6 p-4 rounded-xl bg-ink text-white/80 text-xs flex items-start gap-3 border border-white/10">
            <span className="text-accent font-bold text-base">ℹ</span>
            <div className="leading-relaxed">
              <strong className="text-white">Explicit Project Scope Boundaries:</strong> Forged physical document forensics beyond identifier cross-checking, full multilingual handwritten OCR, and speculative fraud-prediction neural nets are explicitly outside the current project scope to maintain 100% legal defensibility.
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 8: MARKET VALUE & IMPACT (REAL VERIFIED NUMBERS)
      ───────────────────────────────────────────────────────────── */}
      <section id="impact" className="py-20 bg-white border-b border-line">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-pass bg-passBg px-3 py-1 rounded-full border border-pass/20">
              Measurable Economic Impact
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3">
              GeM Scale: Where Fractions of Time Compound into Crores
            </h2>
            <p className="mt-3 text-base text-slate">
              Economic justification grounded in officially published government statistics (PIB August 2026).
            </p>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            <div className="bg-canvas p-6 rounded-card border border-line">
              <div className="font-display font-bold text-3xl text-ink mb-1">₹20L+ Cr</div>
              <div className="text-xs font-semibold text-slate uppercase tracking-wider mb-2">Cumulative GMV</div>
              <p className="text-[11px] text-slate">Over 3.78 crore orders placed since GeM inception.</p>
            </div>

            <div className="bg-canvas p-6 rounded-card border border-line">
              <div className="font-display font-bold text-3xl text-ink mb-1">₹5L+ Cr</div>
              <div className="text-xs font-semibold text-slate uppercase tracking-wider mb-2">Annual GMV</div>
              <p className="text-[11px] text-slate">Crossed ₹5 lakh crore in each of the last two fiscal years.</p>
            </div>

            <div className="bg-canvas p-6 rounded-card border border-line">
              <div className="font-display font-bold text-3xl text-accent mb-1">₹1.76L Cr</div>
              <div className="text-xs font-semibold text-slate uppercase tracking-wider mb-2">Social Savings</div>
              <p className="text-[11px] text-slate">Net social savings estimated by independent IIT Delhi study.</p>
            </div>

            <div className="bg-canvas p-6 rounded-card border border-line">
              <div className="font-display font-bold text-3xl text-pass mb-1">25.45L+</div>
              <div className="text-xs font-semibold text-slate uppercase tracking-wider mb-2">Sellers on GeM</div>
              <p className="text-[11px] text-slate">Including 12.25 lakh MSEs & 1.37 lakh buyer orgs.</p>
            </div>
          </div>

          <div className="bg-accent/5 border border-accent/20 rounded-2xl p-8 flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <h3 className="font-display font-bold text-xl text-ink mb-2">
                Compounding Savings: PS26100 Target (60–80% Effort Reduction)
              </h3>
              <p className="text-sm text-slate max-w-3xl leading-relaxed">
                At millions of bids annually, automating authoritative cross-checks directly saves hundreds of thousands of officer hours, eliminates tender award delays, prevents bid rigging, and ensures genuine MSMEs receive statutory tender benefits instantly.
              </p>
            </div>
            <button
              onClick={() => navigate("/login")}
              className="whitespace-nowrap bg-accent hover:bg-accent2 text-white font-medium px-6 py-3 rounded-xl transition-all shadow-md shadow-accent/20"
            >
              Explore Live Prototype
            </button>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 9: FINAL CTA & FOOTER
      ───────────────────────────────────────────────────────────── */}
      <section className="bg-ink text-white py-20 relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.08]"
          style={{
            backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />

        <div className="relative max-w-4xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/15 text-xs text-white/80 mb-6">
            <span>Ready for live evaluation</span>
          </div>

          <h2 className="font-display text-4xl sm:text-5xl font-bold tracking-tight mb-6">
            Test the GeM Sentinel Prototype
          </h2>

          <p className="text-lg text-white/70 max-w-2xl mx-auto mb-10 leading-relaxed font-light">
            Sign in as a <strong className="text-white">Procurement Officer</strong> to audit bids with evidence links, or as a <strong className="text-white">Bidder</strong> to run pre-submission compliance readiness checks.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => navigate("/login")}
              className="bg-accent hover:bg-accent2 text-white font-medium px-8 py-4 rounded-xl shadow-xl shadow-accent/30 text-base transition-all hover:scale-105"
            >
              Get Started — Sign In to Demo
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-ink2 text-white/60 py-12 border-t border-white/10 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" className="w-4 h-4">
                <path d="M12 2 4 6v6c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V6l-8-4Z" />
                <path d="m9 12 2 2 4-4" />
              </svg>
            </div>
            <div>
              <span className="font-display font-semibold text-sm text-white">GeM Sentinel</span>
              <span className="ml-2 text-[11px] text-white/40">Smart India Hackathon 2026 • PS #26100</span>
            </div>
          </div>

          <div className="text-center sm:text-right text-[11px] text-white/40 max-w-md">
            Hackathon prototype for demonstration purposes. Not an official Government of India or GeM portal product.
          </div>

          <div className="flex items-center gap-4">
            <a
              href="https://github.com/AyushPatwa11/GeM-Sentinel_SIH2026"
              target="_blank"
              rel="noopener noreferrer"
              className="text-white/70 hover:text-white transition-colors flex items-center gap-1.5 text-xs"
            >
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              <span>GitHub</span>
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
