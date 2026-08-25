import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Lock,
  ArrowRight,
  ExternalLink,
  ChevronDown,
  Cpu,
  Layers,
  Search,
  Scale,
  TrendingUp,
  Award,
  Zap,
  Building2,
  Users,
  Check,
  FileCheck2,
  Sparkles,
  Menu,
  X,
} from "lucide-react";

export default function LandingPage() {
  const navigate = useNavigate();
  const [activeTickerIndex, setActiveTickerIndex] = useState(0);
  const [isTickerPaused, setIsTickerPaused] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  const newsItems = [
    {
      tag: "PIB Press Release — July 2026",
      title: "CCI Penalizes HP India for GeM Tender Manipulation",
      category: "Enforcement & Anti-Collusion",
      summary:
        "In 2026 the Competition Commission of India fined HP India ₹126.87 crore, plus penalties on five of its resellers, after finding the company had been dictating bid prices and blocking reseller participation in GeM tenders to benefit itself — exactly the kind of statutory/eligibility manipulation this platform is built to surface.",
      source: "Press Information Bureau (PIB)",
      url: "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2284274&reg=3&lang=1",
      badgeColor: "text-fail bg-failBg/80 border-fail/30",
    },
    {
      tag: "Times of India — Regional Report",
      title: "Smart Classroom Tender Fraud Investigation",
      category: "Tender Fraud & Document Integrity",
      summary:
        "Cases of tender and procurement-linked fraud continue to surface in local reporting — a reminder that manual, document-based verification leaves room for manipulation at every stage of the process.",
      source: "Times of India (Indore)",
      url: "https://timesofindia.indiatimes.com/city/indore/programmer-firm-owner-booked-for-smart-classroom-tender-fraud/articleshowprint/132871490.cms",
      badgeColor: "text-review bg-reviewBg/80 border-review/30",
    },
    {
      tag: "PIB Press Release — August 2026",
      title: "GeM Marks 10 Years: ₹20 Lakh Cr+ Cumulative GMV",
      category: "Scale & Economic Impact",
      summary:
        "GeM marked ten years of operation in August 2026 with a cumulative Gross Merchandise Value exceeding ₹20 lakh crore across more than 3.78 crore orders — annual GMV alone crossed ₹5 lakh crore in each of the last two fiscal years, with an IIT Delhi study estimating ₹1.76 lakh crore in net social savings through the platform. At this scale, even small percentage gains in verification speed and accuracy translate into enormous absolute time and cost savings.",
      source: "Press Information Bureau (PIB)",
      url: "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2296138&reg=48&lang=1",
      badgeColor: "text-accent bg-accent/10 border-accent/30",
    },
  ];

  // Scroll state for navbar glassmorphism
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Auto rotate news strip when not paused
  useEffect(() => {
    if (isTickerPaused) return;
    const interval = setInterval(() => {
      setActiveTickerIndex((prev) => (prev + 1) % newsItems.length);
    }, 6500);
    return () => clearInterval(interval);
  }, [isTickerPaused, newsItems.length]);

  return (
    <div className="min-h-screen bg-canvas text-ink font-body selection:bg-accent/20">
      {/* ─────────────────────────────────────────────────────────────
          NAVBAR (CLEAN, UNCLUTTERED, PROFESSIONAL & ANIMATED)
      ───────────────────────────────────────────────────────────── */}
      <header
        className={`sticky top-0 z-50 transition-all duration-300 ${
          scrolled
            ? "bg-ink/95 backdrop-blur-md border-b border-white/10 shadow-lg shadow-black/10"
            : "bg-ink border-b border-white/10"
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10 h-20 flex items-center justify-between gap-6">
          {/* Logo / Brand Name */}
          <Link
            to="/"
            className="flex items-center gap-3 shrink-0 group transition-transform duration-200 hover:scale-[1.02]"
          >
            <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center shadow-md shadow-accent/30 group-hover:shadow-accent/50 transition-all">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <span className="font-display font-bold text-xl text-white tracking-tight whitespace-nowrap">
              GeM Sentinel
            </span>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-7 xl:gap-9 text-sm font-medium text-white/70">
            {[
              { href: "#problem", label: "Problem" },
              { href: "#evidence", label: "Precedents" },
              { href: "#solution", label: "Architecture" },
              { href: "#features", label: "Features" },
              { href: "#workflow", label: "Workflow" },
              { href: "#roadmap", label: "Roadmap" },
              { href: "#impact", label: "Impact" },
            ].map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="relative py-1 text-white/75 hover:text-white transition-colors duration-200 group text-[13px] xl:text-sm font-medium whitespace-nowrap"
              >
                <span>{link.label}</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-accent rounded-full transition-all duration-300 group-hover:w-full" />
              </a>
            ))}
          </nav>

          {/* Action CTAs */}
          <div className="hidden sm:flex items-center gap-3.5 shrink-0">
            <Link
              to="/login"
              className="text-sm font-medium text-white/80 hover:text-white px-4 py-2 rounded-xl transition-colors whitespace-nowrap"
            >
              Sign In
            </Link>
            <Link
              to="/login"
              className="bg-accent hover:bg-accent2 text-white text-sm font-semibold px-5 py-2.5 rounded-xl shadow-md shadow-accent/30 transition-all duration-200 hover:scale-[1.02] hover:shadow-accent/50 flex items-center gap-2 whitespace-nowrap cursor-pointer"
            >
              <span>Get Started</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex lg:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg bg-white/10 text-white hover:bg-white/15 transition-colors cursor-pointer"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden bg-ink2 border-b border-white/10 px-6 py-6 space-y-4 animate-fadeIn">
            <nav className="flex flex-col space-y-3 text-sm font-medium text-white/80">
              <a
                href="#problem"
                onClick={() => setMobileMenuOpen(false)}
                className="py-1.5 hover:text-accent transition-colors"
              >
                The Problem
              </a>
              <a
                href="#evidence"
                onClick={() => setMobileMenuOpen(false)}
                className="py-1.5 hover:text-accent transition-colors"
              >
                Precedents & Sourcing
              </a>
              <a
                href="#solution"
                onClick={() => setMobileMenuOpen(false)}
                className="py-1.5 hover:text-accent transition-colors"
              >
                Architecture
              </a>
              <a
                href="#features"
                onClick={() => setMobileMenuOpen(false)}
                className="py-1.5 hover:text-accent transition-colors"
              >
                Features & Capabilities
              </a>
              <a
                href="#workflow"
                onClick={() => setMobileMenuOpen(false)}
                className="py-1.5 hover:text-accent transition-colors"
              >
                Workflow
              </a>
              <a
                href="#roadmap"
                onClick={() => setMobileMenuOpen(false)}
                className="py-1.5 hover:text-accent transition-colors"
              >
                Tech & Roadmap
              </a>
              <a
                href="#impact"
                onClick={() => setMobileMenuOpen(false)}
                className="py-1.5 hover:text-accent transition-colors"
              >
                Market Impact
              </a>
            </nav>

            <div className="pt-4 border-t border-white/10 flex flex-col gap-2.5">
              <Link
                to="/login"
                className="w-full text-center text-sm font-medium text-white/80 bg-white/5 py-2.5 rounded-xl border border-white/10"
              >
                Sign In
              </Link>
              <Link
                to="/login"
                className="w-full text-center text-sm font-semibold text-white bg-accent py-2.5 rounded-xl shadow-md shadow-accent/30"
              >
                Get Started
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 1: HERO
      ───────────────────────────────────────────────────────────── */}
      <section className="relative bg-ink text-white overflow-hidden pt-16 pb-24 lg:pt-24 lg:pb-32 border-b border-white/10">
        {/* Dotted Grid Background Texture */}
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />

        {/* Ambient Gradient Glows */}
        <div className="absolute top-1/4 left-1/3 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[380px] bg-accent/20 rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute bottom-10 right-10 w-[450px] h-[320px] bg-pass/10 rounded-full blur-[130px] pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
          <div className="grid lg:grid-cols-12 gap-12 lg:gap-10 items-center">
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 border border-white/15 text-xs font-medium text-white/90 backdrop-blur-sm shadow-xs">
                <Sparkles className="w-3.5 h-3.5 text-blue-300" />
                <span>Deterministic Compliance & Authoritative Risk Shield</span>
              </div>

              <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] tracking-tight">
                AI-Powered Bid Compliance Verification for GeM Procurement.
              </h1>

              <p className="text-lg sm:text-xl text-white/75 leading-relaxed max-w-2xl font-light">
                <strong className="text-white font-semibold">AI assists, authoritative sources verify, deterministic rules decide</strong> — and the procurement officer always retains final authority. Zero blind trust in LLMs.
              </p>

              <div className="pt-2 flex flex-wrap items-center gap-4">
                <button
                  onClick={() => navigate("/login")}
                  className="bg-accent hover:bg-accent2 text-white font-semibold px-7 py-3.5 rounded-xl shadow-lg shadow-accent/30 transition-all duration-200 hover:scale-[1.02] flex items-center gap-2.5 text-sm sm:text-base cursor-pointer"
                >
                  <span>Get Started</span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                <a
                  href="#workflow"
                  className="bg-white/10 hover:bg-white/15 text-white border border-white/20 font-medium px-5 py-3.5 rounded-xl transition-all duration-200 flex items-center gap-2 text-sm sm:text-base cursor-pointer"
                >
                  <span>See How It Works</span>
                  <ChevronDown className="w-4 h-4" />
                </a>
              </div>

              {/* Quick Pillars under Hero */}
              <div className="pt-8 border-t border-white/10 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-white/70">
                <div className="bg-white/5 p-4 rounded-xl border border-white/10 transition-all hover:bg-white/10">
                  <div className="text-white font-semibold text-sm mb-1 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-pass shrink-0" />
                    <span>Deterministic Rules</span>
                  </div>
                  <p className="text-white/60 text-[11px] leading-relaxed">
                    AND/OR logic & statutory waivers evaluated with 100% precision.
                  </p>
                </div>

                <div className="bg-white/5 p-4 rounded-xl border border-white/10 transition-all hover:bg-white/10">
                  <div className="text-white font-semibold text-sm mb-1 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-pass shrink-0" />
                    <span>Evidence-Linked</span>
                  </div>
                  <p className="text-white/60 text-[11px] leading-relaxed">
                    Every verdict cites exact source records, page numbers, and APIs.
                  </p>
                </div>

                <div className="bg-white/5 p-4 rounded-xl border border-white/10 transition-all hover:bg-white/10">
                  <div className="text-white font-semibold text-sm mb-1 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-pass shrink-0" />
                    <span>Tamper-Evident</span>
                  </div>
                  <p className="text-white/60 text-[11px] leading-relaxed">
                    Database-enforced, append-only logs for every officer decision.
                  </p>
                </div>
              </div>
            </div>

            {/* Interactive Hero Visual Showcase */}
            <div className="lg:col-span-5">
              <div className="bg-ink2/95 border border-white/15 rounded-2xl p-6 shadow-2xl backdrop-blur-xl relative overflow-hidden transition-all duration-300 hover:border-white/30 hover:shadow-accent/10">
                <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-5">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-400/80 inline-block" />
                    <span className="w-2.5 h-2.5 rounded-full bg-yellow-400/80 inline-block" />
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/80 inline-block" />
                    <span className="text-xs font-mono text-white/60 ml-2">Tender GeM/2026/T-101</span>
                  </div>
                  <span className="px-2.5 py-1 rounded-md text-[11px] font-mono bg-pass/20 text-emerald-400 border border-pass/30 font-semibold">
                    STAGE 2 PASS
                  </span>
                </div>

                {/* Sample Verification Card */}
                <div className="space-y-3.5">
                  <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-semibold text-white">Bharat ElectroTech Pvt Ltd</span>
                      <span className="text-emerald-400 font-mono font-bold">100% Compliant</span>
                    </div>
                    <div className="text-[11px] text-white/50 font-mono">
                      MSME / UDYAM-MH-01-0023456 • GSTIN: 27AABCB1234F1Z5
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2.5 text-xs">
                    <div className="bg-white/5 p-3 rounded-xl border border-white/10">
                      <div className="text-[10px] uppercase font-mono tracking-wider text-white/40 mb-1">EMD Deposit</div>
                      <div className="flex items-center gap-1.5 text-xs text-white font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5 text-pass shrink-0" />
                        <span>Exempt (MSME Valid)</span>
                      </div>
                    </div>
                    <div className="bg-white/5 p-3 rounded-xl border border-white/10">
                      <div className="text-[10px] uppercase font-mono tracking-wider text-white/40 mb-1">Risk Gauge</div>
                      <div className="flex items-center gap-1.5 text-xs text-emerald-300 font-medium">
                        <ShieldCheck className="w-3.5 h-3.5 text-pass shrink-0" />
                        <span>Low Risk (12/100)</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-xl p-3.5 border border-white/10 text-xs space-y-2">
                    <div className="text-[10px] font-mono text-white/40 uppercase tracking-wider font-semibold">
                      Authoritative Adapter Verification
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-white/80 flex items-center gap-2">
                        <Check className="w-3.5 h-3.5 text-pass" /> MCA Master Data (Live data.gov.in)
                      </span>
                      <span className="text-emerald-400 font-mono font-medium">ACTIVE</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-white/80 flex items-center gap-2">
                        <Check className="w-3.5 h-3.5 text-pass" /> GSTN Active & 3Y Returns Filed
                      </span>
                      <span className="text-emerald-400 font-mono font-medium">VERIFIED</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-white/80 flex items-center gap-2">
                        <Check className="w-3.5 h-3.5 text-pass" /> Central Debarment / Blacklist
                      </span>
                      <span className="text-emerald-400 font-mono font-medium">CLEAR</span>
                    </div>
                  </div>

                  <div className="p-3 bg-accent/20 border border-accent/30 rounded-xl text-xs text-blue-200 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5 text-blue-300" />
                      <span>Officer Authority:</span>
                    </span>
                    <span className="font-semibold text-white">Review & Affirm</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 2: THE PROBLEM
      ───────────────────────────────────────────────────────────── */}
      <section id="problem" className="py-20 bg-white border-b border-line">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
          <div className="max-w-3xl mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-3 py-1 rounded-full border border-accent/20">
              The Reality of Public Procurement
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3 tracking-tight">
              Why Manual Verification Fails at Scale
            </h2>
            <p className="mt-4 text-base sm:text-lg text-slate leading-relaxed">
              Procurement officers are forced to manually cross-check hundreds of bidder documents across isolated, disparate government portals — a slow, document-intensive, and error-prone process.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-canvas p-8 rounded-card border border-line flex flex-col justify-between hover:border-slate/40 transition-colors">
              <div>
                <div className="w-12 h-12 rounded-xl bg-failBg text-fail flex items-center justify-center font-display font-bold text-xl mb-6">
                  60-80%
                </div>
                <h3 className="font-display font-bold text-lg text-ink mb-2">
                  Crippling Verification Overhead
                </h3>
                <p className="text-xs sm:text-sm text-slate leading-relaxed">
                  Evaluating a single multi-crore tender with dozens of bidders requires hundreds of manual portal visits across Udyam, GSTN, PAN/IT, EPFO/ESIC, NSIC, Startup India, and DigiLocker.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-line text-xs font-mono text-slate flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-fail" />
                <span>Bottleneck in tender award lifecycle</span>
              </div>
            </div>

            <div className="bg-canvas p-8 rounded-card border border-line flex flex-col justify-between hover:border-slate/40 transition-colors">
              <div>
                <div className="w-12 h-12 rounded-xl bg-reviewBg text-review flex items-center justify-center font-display font-bold text-xl mb-6">
                  8+
                </div>
                <h3 className="font-display font-bold text-lg text-ink mb-2">
                  Disconnected Government Silos
                </h3>
                <p className="text-xs sm:text-sm text-slate leading-relaxed">
                  No single unified verification layer exists. Officers must manually correlate GST returns, MSME classifications, and debarment registries, leaving critical gaps for fraud and cartelization.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-line text-xs font-mono text-slate flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-review" />
                <span>Vulnerable to forged certificates</span>
              </div>
            </div>

            <div className="bg-canvas p-8 rounded-card border border-line flex flex-col justify-between hover:border-slate/40 transition-colors">
              <div>
                <div className="w-12 h-12 rounded-xl bg-accent/10 text-accent flex items-center justify-center font-display font-bold text-xl mb-6">
                  Zero
                </div>
                <h3 className="font-display font-bold text-lg text-ink mb-2">
                  Auditability in Black-Box LLMs
                </h3>
                <p className="text-xs sm:text-sm text-slate leading-relaxed">
                  Generic AI models hallucinate compliance rules, miss subtle MSME exemption clauses, and fail to provide the statutory, tamper-evident audit trails legally demanded by procurement law.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-line text-xs font-mono text-slate flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-accent" />
                <span>Requires deterministic logic</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 3: NEWS TICKER / VERIFIED REFERENCE STRIP
      ───────────────────────────────────────────────────────────── */}
      <section id="evidence" className="py-16 bg-canvas border-b border-line">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-fail mb-1.5">
                <span className="w-2 h-2 rounded-full bg-fail" />
                <span>Verified Precedents & Scale Data</span>
              </div>
              <h2 className="font-display text-2xl sm:text-3xl font-bold text-ink">
                Documented Evidence & Real-World Precedents
              </h2>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate hidden sm:inline">Click cards to view official records</span>
              <div className="flex gap-1.5">
                {newsItems.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveTickerIndex(i)}
                    className={`h-2 rounded-full transition-all cursor-pointer ${
                      activeTickerIndex === i ? "w-7 bg-accent" : "w-2 bg-line hover:bg-slate"
                    }`}
                    aria-label={`Go to item ${i + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Cards Grid */}
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
                    isActive
                      ? "border-accent ring-2 ring-accent/20 shadow-md -translate-y-1"
                      : "border-line hover:border-slate/40"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-md border ${item.badgeColor}`}>
                        {item.category}
                      </span>
                    </div>

                    <h3 className="font-display font-bold text-base text-ink mb-2.5">
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
                      className="text-accent hover:text-accent2 font-semibold inline-flex items-center gap-1 group"
                    >
                      <span>Official Source</span>
                      <ExternalLink className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
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
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-semibold uppercase tracking-wider text-pass bg-passBg/80 px-3 py-1 rounded-full border border-pass/30">
              The Architectural Answer
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3 tracking-tight">
              Deterministic Verification with Swappable Source Adapters
            </h2>
            <p className="mt-4 text-base sm:text-lg text-slate leading-relaxed">
              We replace manual scrutiny and black-box AI hallucinations with a structured, verifiable pipeline that turns tender clauses into formal logic and checks live government databases.
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            <div className="p-7 rounded-card bg-canvas border border-line relative group hover:border-accent transition-colors">
              <div className="w-10 h-10 rounded-xl bg-ink text-white flex items-center justify-center font-mono font-bold text-sm mb-5 shadow-sm">
                01
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-2">
                Structured Clause Logic
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Tender requirements are decomposed into structured evaluation rules (turnover thresholds, MSME waivers, experience, EMD logic) with strict syntax.
              </p>
            </div>

            <div className="p-7 rounded-card bg-canvas border border-line relative group hover:border-accent transition-colors">
              <div className="w-10 h-10 rounded-xl bg-accent text-white flex items-center justify-center font-mono font-bold text-sm mb-5 shadow-sm shadow-accent/30">
                02
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-2">
                Swappable Adapters
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Pluggable adapters for GSTN, MCA, Udyam, DigiLocker, and NSIC verify claims directly against authoritative registries with live API fallbacks.
              </p>
            </div>

            <div className="p-7 rounded-card bg-canvas border border-line relative group hover:border-accent transition-colors">
              <div className="w-10 h-10 rounded-xl bg-pass text-white flex items-center justify-center font-mono font-bold text-sm mb-5 shadow-sm">
                03
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-2">
                Independent Risk & Rules
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                A bidder can be 100% compliant but high-risk (e.g. newly incorporated entity bidding on maximum tender size). We never blend these into an ambiguous single score.
              </p>
            </div>

            <div className="p-7 rounded-card bg-canvas border border-line relative group hover:border-accent transition-colors">
              <div className="w-10 h-10 rounded-xl bg-ink2 text-white flex items-center justify-center font-mono font-bold text-sm mb-5 shadow-sm">
                04
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-2">
                Evidence-Linked Verdict
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                The platform recommends — the human officer decides. Every verdict links to the exact source document and page, with database-enforced justification.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 5: FEATURES GRID
      ───────────────────────────────────────────────────────────── */}
      <section id="features" className="py-20 bg-canvas border-b border-line">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
          <div className="max-w-3xl mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-3 py-1 rounded-full border border-accent/20">
              Core Capabilities
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3 tracking-tight">
              Engineered for Compliance, Integrity, and Auditability
            </h2>
            <p className="mt-3 text-base text-slate">
              Every feature below is implemented in the active codebase — strictly grounded in production-grade architecture.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md hover:border-accent/40 transition-all">
              <div className="w-10 h-10 rounded-xl bg-accent/10 text-accent flex items-center justify-center mb-4">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-1.5">
                Deterministic Rule Engine
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Handles complex AND/OR/NOT and exemption logic (such as statutory MSME/Startup EMD waivers) with verifiable precision, never heuristic guesses.
              </p>
            </div>

            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md hover:border-pass/40 transition-all">
              <div className="w-10 h-10 rounded-xl bg-passBg text-pass flex items-center justify-center mb-4">
                <FileCheck2 className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-1.5">
                Evidence-Linked Findings
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Every single compliance result links directly to a verified document, page reference, API payload, or statutory database response.
              </p>
            </div>

            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md hover:border-review/40 transition-all">
              <div className="w-10 h-10 rounded-xl bg-reviewBg text-review flex items-center justify-center mb-4">
                <Scale className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-1.5">
                Independent Risk Scoring
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Compliance (rule adherence) and Risk (anomalies, concentration, age, capacity) are scored on separate orthogonal axes.
              </p>
            </div>

            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md hover:border-accent/40 transition-all">
              <div className="w-10 h-10 rounded-xl bg-accent/10 text-accent flex items-center justify-center mb-4">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-1.5">
                Adapter Architecture
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Registry pattern supporting live data.gov.in MCA integration, GSTN, Udyam, NSIC, and DigiLocker with seamless mock fallbacks.
              </p>
            </div>

            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md hover:border-fail/40 transition-all">
              <div className="w-10 h-10 rounded-xl bg-failBg text-fail flex items-center justify-center mb-4">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-1.5">
                Two-Stage Verification
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Stage 1 checks document completeness, signatures, and validity; Stage 2 evaluates technical & financial tender rules without conflation.
              </p>
            </div>

            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md hover:border-ink/40 transition-all">
              <div className="w-10 h-10 rounded-xl bg-ink text-white flex items-center justify-center mb-4">
                <Users className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-1.5">
                Human-In-The-Loop
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                The platform only provides evidence-linked recommendations. Overriding an automated recommendation mandates entering a signed justification.
              </p>
            </div>

            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md hover:border-pass/40 transition-all">
              <div className="w-10 h-10 rounded-xl bg-passBg text-pass flex items-center justify-center mb-4">
                <Lock className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-1.5">
                Tamper-Evident Trail
              </h3>
              <p className="text-xs text-slate leading-relaxed">
                Every evaluation step, adapter response, officer remark, and final verdict is saved in an append-only, legally defensible audit ledger.
              </p>
            </div>

            <div className="bg-card p-6 rounded-card border border-line hover:shadow-md hover:border-accent/40 transition-all">
              <div className="w-10 h-10 rounded-xl bg-accent/10 text-accent flex items-center justify-center mb-4">
                <Zap className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-ink mb-1.5">
                Bidder Readiness Check
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
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-3 py-1 rounded-full border border-accent/20">
              End-to-End Execution Flow
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3 tracking-tight">
              The 6-Step Verification Lifecycle
            </h2>
            <p className="mt-3 text-base text-slate">
              From bid submission to final officer verdict — transparency and accountability at every touchpoint.
            </p>
          </div>

          {/* Flow Diagram Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-canvas p-5 rounded-xl border border-line text-center flex flex-col items-center hover:border-accent/40 transition-colors">
              <div className="w-9 h-9 rounded-xl bg-ink text-white font-mono text-xs flex items-center justify-center font-bold mb-3 shadow-xs">
                1
              </div>
              <h4 className="font-display font-bold text-sm text-ink mb-1">Bidder Submits</h4>
              <p className="text-[11px] text-slate leading-relaxed">Documents & identifiers submitted via portal</p>
            </div>

            <div className="bg-canvas p-5 rounded-xl border border-line text-center flex flex-col items-center hover:border-accent/40 transition-colors">
              <div className="w-9 h-9 rounded-xl bg-accent text-white font-mono text-xs flex items-center justify-center font-bold mb-3 shadow-xs">
                2
              </div>
              <h4 className="font-display font-bold text-sm text-ink mb-1">Stage 1 Scrutiny</h4>
              <p className="text-[11px] text-slate leading-relaxed">Completeness, signatures & authenticity</p>
            </div>

            <div className="bg-canvas p-5 rounded-xl border border-line text-center flex flex-col items-center hover:border-accent/40 transition-colors">
              <div className="w-9 h-9 rounded-xl bg-pass text-white font-mono text-xs flex items-center justify-center font-bold mb-3 shadow-xs">
                3
              </div>
              <h4 className="font-display font-bold text-sm text-ink mb-1">Stage 2 Rules</h4>
              <p className="text-[11px] text-slate leading-relaxed">Deterministic evaluation against tender criteria</p>
            </div>

            <div className="bg-canvas p-5 rounded-xl border border-line text-center flex flex-col items-center hover:border-accent/40 transition-colors">
              <div className="w-9 h-9 rounded-xl bg-review text-white font-mono text-xs flex items-center justify-center font-bold mb-3 shadow-xs">
                4
              </div>
              <h4 className="font-display font-bold text-sm text-ink mb-1">Risk Scoring</h4>
              <p className="text-[11px] text-slate leading-relaxed">Independent anomalies & capacity flags computed</p>
            </div>

            <div className="bg-canvas p-5 rounded-xl border border-line text-center flex flex-col items-center hover:border-accent/40 transition-colors">
              <div className="w-9 h-9 rounded-xl bg-ink2 text-white font-mono text-xs flex items-center justify-center font-bold mb-3 shadow-xs">
                5
              </div>
              <h4 className="font-display font-bold text-sm text-ink mb-1">Officer Verdict</h4>
              <p className="text-[11px] text-slate leading-relaxed">Officer reviews evidence and records decision</p>
            </div>

            <div className="bg-canvas p-5 rounded-xl border border-line text-center flex flex-col items-center hover:border-accent/40 transition-colors">
              <div className="w-9 h-9 rounded-xl bg-pass text-white font-mono text-xs flex items-center justify-center font-bold mb-3 shadow-xs">
                6
              </div>
              <h4 className="font-display font-bold text-sm text-ink mb-1">Live Reflection</h4>
              <p className="text-[11px] text-slate leading-relaxed">Status & audit log updated for bidder & auditors</p>
            </div>
          </div>

          <div className="mt-8 p-4 bg-canvas border border-line rounded-xl text-center text-xs text-slate">
            <strong className="text-ink">Strict Security Invariant:</strong> The automated system delivers recommendations with complete source citation — decisions are made exclusively by authorized procurement officers.
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 7: TECHNOLOGY & ROADMAP
      ───────────────────────────────────────────────────────────── */}
      <section id="roadmap" className="py-20 bg-canvas border-b border-line">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
          <div className="max-w-3xl mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-accent bg-accent/10 px-3 py-1 rounded-full border border-accent/20">
              Technical Architecture & Evolution
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3 tracking-tight">
              Technology Stack & Verified Roadmap
            </h2>
            <p className="mt-3 text-base text-slate">
              Clear demarcation between what is live and running in the repository today versus upcoming platform milestones.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Column 1: Built Today */}
            <div className="bg-card p-8 rounded-card border border-line shadow-xs">
              <div className="flex items-center gap-2.5 mb-6">
                <span className="w-3 h-3 rounded-full bg-pass" />
                <h3 className="font-display font-bold text-xl text-ink">Built & Running Today</h3>
              </div>

              <ul className="space-y-4 text-xs text-slate">
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-pass shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-ink text-sm block">Python / FastAPI Backend</strong>
                    Async REST API with Pydantic validation, structured endpoints, and OpenAPI spec.
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-pass shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-ink text-sm block">Deterministic Rule & Risk Engines</strong>
                    Zero LLM dependency in evaluation core — 100% reproducible compliance logic.
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-pass shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-ink text-sm block">Live data.gov.in MCA Integration</strong>
                    Real-time adapter querying official Company Master Data API alongside mock adapters for GSTN, Udyam, NSIC, and DigiLocker.
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-pass shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-ink text-sm block">React 18 + Vite + Tailwind Frontend</strong>
                    Role-based officer & bidder views, real-time readiness check, and audit trail ledger.
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-pass shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-ink text-sm block">Tamper-Evident Audit Schema</strong>
                    Append-only logging of officer verdicts, mandatory override justification, and source evidence.
                  </div>
                </li>
              </ul>
            </div>

            {/* Column 2: Coming Next */}
            <div className="bg-card p-8 rounded-card border border-line shadow-xs">
              <div className="flex items-center gap-2.5 mb-6">
                <span className="w-3 h-3 rounded-full bg-accent" />
                <h3 className="font-display font-bold text-xl text-ink">Next Phase Roadmap</h3>
              </div>

              <ul className="space-y-4 text-xs text-slate">
                <li className="flex items-start gap-3">
                  <ArrowRight className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-ink text-sm block">OCR & Entity Extraction Pipeline</strong>
                    LayoutLM / Tesseract OCR pipeline for extracting unstructured PDF bid documents into verified schema.
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <ArrowRight className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-ink text-sm block">Grounded Tender Clause Extraction</strong>
                    Constrained LLM extraction of complex tender terms validated against an allowable rule grammar.
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <ArrowRight className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-ink text-sm block">Real DigiLocker Partner API</strong>
                    Production DigiLocker gateway integration for cryptographically authentic document fetching.
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <ArrowRight className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-ink text-sm block">Corrigendum Impact Engine</strong>
                    Automated re-evaluation of all submitted bids whenever tender amendments or corrigenda are published.
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <ArrowRight className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-ink text-sm block">Tender Quality Assistant</strong>
                    Pre-publishing clause ambiguity and anti-competitive clause detector for tender drafting officers.
                  </div>
                </li>
              </ul>
            </div>
          </div>

          {/* Boundaries Note */}
          <div className="mt-6 p-5 rounded-xl bg-ink text-white/80 text-xs flex items-start gap-3 border border-white/10">
            <Lock className="w-4 h-4 text-accent shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <strong className="text-white">Explicit Scope Boundaries:</strong> Forged physical document forensics beyond identifier cross-checking, full multilingual handwritten OCR, and speculative fraud-prediction neural nets are explicitly outside the current project scope to maintain 100% legal defensibility.
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 8: MARKET VALUE & IMPACT
      ───────────────────────────────────────────────────────────── */}
      <section id="impact" className="py-20 bg-white border-b border-line">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
          <div className="max-w-3xl mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-pass bg-passBg px-3 py-1 rounded-full border border-pass/20">
              Measurable Economic Impact
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-ink mt-3 tracking-tight">
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
              <p className="text-[11px] text-slate leading-relaxed">Over 3.78 crore orders placed since GeM inception.</p>
            </div>

            <div className="bg-canvas p-6 rounded-card border border-line">
              <div className="font-display font-bold text-3xl text-ink mb-1">₹5L+ Cr</div>
              <div className="text-xs font-semibold text-slate uppercase tracking-wider mb-2">Annual GMV</div>
              <p className="text-[11px] text-slate leading-relaxed">Crossed ₹5 lakh crore in each of the last two fiscal years.</p>
            </div>

            <div className="bg-canvas p-6 rounded-card border border-line">
              <div className="font-display font-bold text-3xl text-accent mb-1">₹1.76L Cr</div>
              <div className="text-xs font-semibold text-slate uppercase tracking-wider mb-2">Social Savings</div>
              <p className="text-[11px] text-slate leading-relaxed">Net social savings estimated by independent IIT Delhi study.</p>
            </div>

            <div className="bg-canvas p-6 rounded-card border border-line">
              <div className="font-display font-bold text-3xl text-pass mb-1">25.45L+</div>
              <div className="text-xs font-semibold text-slate uppercase tracking-wider mb-2">Sellers on GeM</div>
              <p className="text-[11px] text-slate leading-relaxed">Including 12.25 lakh MSEs & 1.37 lakh buyer orgs.</p>
            </div>
          </div>

          <div className="bg-accent/5 border border-accent/20 rounded-2xl p-8 flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <h3 className="font-display font-bold text-xl text-ink mb-2">
                Compounding Savings: 60–80% Effort Reduction
              </h3>
              <p className="text-sm text-slate max-w-3xl leading-relaxed">
                At millions of bids annually, automating authoritative cross-checks directly saves hundreds of thousands of officer hours, eliminates tender award delays, prevents bid rigging, and ensures genuine MSMEs receive statutory tender benefits instantly.
              </p>
            </div>
            <button
              onClick={() => navigate("/login")}
              className="whitespace-nowrap bg-accent hover:bg-accent2 text-white font-semibold px-6 py-3.5 rounded-xl transition-all shadow-md shadow-accent/20 cursor-pointer"
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

        <div className="relative max-w-4xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/15 text-xs text-white/80 mb-6">
            <Sparkles className="w-3.5 h-3.5 text-blue-300" />
            <span>Ready for live evaluation</span>
          </div>

          <h2 className="font-display text-4xl sm:text-5xl font-bold tracking-tight mb-6">
            Experience GeM Sentinel Live
          </h2>

          <p className="text-lg text-white/70 max-w-2xl mx-auto mb-10 leading-relaxed font-light">
            Sign in as a <strong className="text-white">Procurement Officer</strong> to audit bids with evidence links, or as a <strong className="text-white">Bidder</strong> to run pre-submission compliance readiness checks.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => navigate("/login")}
              className="bg-accent hover:bg-accent2 text-white font-semibold px-8 py-4 rounded-xl shadow-xl shadow-accent/30 text-base transition-all hover:scale-105 cursor-pointer flex items-center gap-2"
            >
              <span>Get Started — Sign In to Platform</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-ink2 text-white/60 py-10 border-t border-white/10 text-xs">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-display font-semibold text-sm text-white">GeM Sentinel</span>
              <span className="ml-2 text-[11px] text-white/40">Procurement Intelligence & Compliance Platform</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <a
              href="https://github.com/AyushPatwa11/GeM-Sentinel_SIH2026"
              target="_blank"
              rel="noopener noreferrer"
              className="text-white/70 hover:text-white transition-colors flex items-center gap-1.5 text-xs"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>GitHub Repository</span>
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
