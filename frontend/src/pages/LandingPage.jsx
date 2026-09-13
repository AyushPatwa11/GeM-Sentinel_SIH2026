import React, { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Shield, Zap, CheckCircle, Play } from "lucide-react";

export default function LandingPage() {
  const [hoveredCard, setHoveredCard] = useState(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const videoRef = useRef(null);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.play();
    }
  }, []);

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden">
      {/* Full-Frame Video Hero */}
      <section className="relative w-full h-screen flex items-center justify-center bg-black">
        {/* Video Background */}
        <video
          ref={videoRef}
          autoPlay
          muted
          loop
          className="absolute inset-0 w-full h-full object-cover"
          playsInline
        >
          <source src="/landing-demo.mp4" type="video/mp4" />
        </video>

        {/* Dark Overlay */}
        <div className="absolute inset-0 bg-black/40"></div>

        {/* Navigation - Overlay on Video */}
        <nav className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-6 lg:px-12 py-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/10 backdrop-blur-md rounded-xl flex items-center justify-center border border-white/20">
              <span className="text-2xl">🛡️</span>
            </div>
            <div>
              <div className="text-xl font-bold">GeM Sentinel</div>
              <div className="text-xs text-blue-200">Bid Compliance</div>
            </div>
          </div>
          <Link
            to="/login"
            className="bg-white text-blue-900 font-bold px-6 py-2.5 rounded-lg hover:shadow-lg hover:scale-105 transition-all duration-300"
          >
            Sign In
          </Link>
        </nav>

        {/* Hero Content - Centered on Video */}
        <div className="relative z-10 max-w-4xl mx-auto px-6 lg:px-12 text-center flex flex-col items-center justify-center h-full">
          {/* Animated Badge */}
          <div className="inline-block mb-6 px-4 py-2 bg-white/20 border border-white/40 rounded-full backdrop-blur-md animate-fade-in">
            <span className="text-sm font-semibold">✨ Government of India Official Portal</span>
          </div>

          {/* Main Heading */}
          <h1 className="text-5xl lg:text-7xl font-bold mb-6 tracking-tight animate-slide-up drop-shadow-2xl">
            Bid Compliance Made Simple
          </h1>

          {/* Subheading */}
          <p className="text-lg lg:text-xl text-blue-100 mb-12 max-w-3xl leading-relaxed animate-slide-up animation-delay-200 drop-shadow-lg">
            Real-time verification, automated compliance checks, and transparent decision-making for Government e-Marketplace procurements
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up animation-delay-400">
            <Link
              to="/login"
              className="bg-white text-blue-900 font-bold px-8 py-4 rounded-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2"
            >
              Officer Portal
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/login"
              className="border-2 border-white text-white font-bold px-8 py-4 rounded-xl hover:bg-white/10 hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2"
            >
              Bidder Portal
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-20 animate-bounce">
          <div className="text-white text-center">
            <p className="text-xs text-blue-200 mb-2">Scroll to explore</p>
            <svg className="w-6 h-6 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </div>
        </div>
      </section>

      {/* Content Sections - Blue Gradient Background */}
      <div className="bg-gradient-to-br from-blue-900 via-blue-800 to-blue-600 text-white">
        {/* Features Section */}
        <section className="relative z-10 max-w-6xl mx-auto px-6 lg:px-12 py-16">
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Officer Portal */}
          <div className="backdrop-blur-xl bg-white/5 border border-white/20 rounded-2xl p-8 hover:bg-white/10 transition-all duration-300">
            <div className="text-4xl mb-4">👨‍⚖️</div>
            <h2 className="text-2xl font-bold mb-4">For Officers</h2>
            <ul className="space-y-3 text-blue-100">
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Risk-ranked bid dashboard with instant analysis</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Automated compliance verification with evidence links</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Complete immutable audit trail for transparency</span>
              </li>
            </ul>
            <Link
              to="/login"
              className="mt-6 block bg-white text-blue-900 font-bold text-center py-3 rounded-xl hover:shadow-lg hover:scale-105 transition-all"
            >
              Access Officer Portal
            </Link>
          </div>

          {/* Bidder Portal */}
          <div className="backdrop-blur-xl bg-white/5 border border-white/20 rounded-2xl p-8 hover:bg-white/10 transition-all duration-300">
            <div className="text-4xl mb-4">🏢</div>
            <h2 className="text-2xl font-bold mb-4">For Bidders</h2>
            <ul className="space-y-3 text-blue-100">
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Browse active government tender opportunities</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Pre-submission readiness checklist for compliance</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Real-time bid status tracking and notifications</span>
              </li>
            </ul>
            <Link
              to="/login"
              className="mt-6 block bg-white text-blue-900 font-bold text-center py-3 rounded-xl hover:shadow-lg hover:scale-105 transition-all"
            >
              Access Bidder Portal
            </Link>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {[
            { icon: Shield, title: "Verified Data", desc: "Real government authority verification" },
            { icon: Zap, title: "Instant Results", desc: "Automated compliance checks in seconds" },
            { icon: CheckCircle, title: "Transparent", desc: "Complete audit trail for every decision" },
          ].map((feature, idx) => (
            <div
              key={idx}
              onMouseEnter={() => setHoveredCard(idx)}
              onMouseLeave={() => setHoveredCard(null)}
              className={`backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-8 transition-all duration-300 transform ${
                hoveredCard === idx ? "bg-white/20 scale-105 shadow-2xl" : "hover:bg-white/15"
              }`}
            >
              <feature.icon className="w-12 h-12 mb-4 text-blue-200" />
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-blue-100 text-sm">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="relative z-10 max-w-6xl mx-auto px-6 lg:px-12 py-16">
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Officer Portal */}
          <div className="backdrop-blur-xl bg-white/5 border border-white/20 rounded-2xl p-8 hover:bg-white/10 transition-all duration-300">
            <div className="text-4xl mb-4">👨‍⚖️</div>
            <h2 className="text-2xl font-bold mb-4">For Officers</h2>
            <ul className="space-y-3 text-blue-100">
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Risk-ranked bid dashboard with instant analysis</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Automated compliance verification with evidence links</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Complete immutable audit trail for transparency</span>
              </li>
            </ul>
            <Link
              to="/login"
              className="mt-6 block bg-white text-blue-900 font-bold text-center py-3 rounded-xl hover:shadow-lg hover:scale-105 transition-all"
            >
              Access Officer Portal
            </Link>
          </div>

          {/* Bidder Portal */}
          <div className="backdrop-blur-xl bg-white/5 border border-white/20 rounded-2xl p-8 hover:bg-white/10 transition-all duration-300">
            <div className="text-4xl mb-4">🏢</div>
            <h2 className="text-2xl font-bold mb-4">For Bidders</h2>
            <ul className="space-y-3 text-blue-100">
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Browse active government tender opportunities</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Pre-submission readiness checklist for compliance</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-blue-300">✓</span>
                <span>Real-time bid status tracking and notifications</span>
              </li>
            </ul>
            <Link
              to="/login"
              className="mt-6 block bg-white text-blue-900 font-bold text-center py-3 rounded-xl hover:shadow-lg hover:scale-105 transition-all"
            >
              Access Bidder Portal
            </Link>
          </div>
        </div>
      </section>

      {/* Why Choose Section */}
      <section className="relative z-10 max-w-6xl mx-auto px-6 lg:px-12 py-16 text-center">
        <h2 className="text-3xl lg:text-4xl font-bold mb-12">Why GeM Sentinel?</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { num: "100%", label: "Deterministic Rules" },
            { num: "Real-time", label: "Verification" },
            { num: "Zero", label: "Manual Review" },
          ].map((stat, idx) => (
            <div key={idx} className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-xl p-6">
              <div className="text-4xl font-bold text-blue-200 mb-2">{stat.num}</div>
              <div className="text-lg font-semibold">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Why Choose Section */}
      <section className="relative z-10 max-w-6xl mx-auto px-6 lg:px-12 py-16 text-center">
        <h2 className="text-3xl lg:text-4xl font-bold mb-12">Why GeM Sentinel?</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { num: "100%", label: "Deterministic Rules" },
            { num: "Real-time", label: "Verification" },
            { num: "Zero", label: "Manual Review" },
          ].map((stat, idx) => (
            <div key={idx} className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-xl p-6">
              <div className="text-4xl font-bold text-blue-200 mb-2">{stat.num}</div>
              <div className="text-lg font-semibold">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Footer */}
      <section className="relative z-10 max-w-4xl mx-auto px-6 lg:px-12 py-16 text-center">
        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-12">
          <h3 className="text-3xl font-bold mb-4">Ready to Transform Your Procurement?</h3>
          <p className="text-blue-100 mb-8 text-lg">Join Government of India in modernizing tender evaluation with real-time compliance verification</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/login"
              className="bg-white text-blue-900 font-bold px-8 py-4 rounded-xl hover:shadow-2xl hover:scale-105 transition-all duration-300"
            >
              Get Started Now
            </Link>
            <a
              href="#"
              className="border-2 border-white text-white font-bold px-8 py-4 rounded-xl hover:bg-white/10 transition-all"
            >
              Learn More
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 mt-16 py-8 text-center text-blue-100 text-sm">
        <p>© 2026 GeM Sentinel • Government of India • Ministry of Petroleum & Natural Gas</p>
      </footer>
      </div>

      {/* CSS for animations */}
      <style>{`
        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slide-up {
          from { 
            opacity: 0;
            transform: translateY(30px);
          }
          to { 
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        .animation-delay-200 {
          animation-delay: 200ms;
        }
        .animation-delay-400 {
          animation-delay: 400ms;
        }
        .animation-delay-600 {
          animation-delay: 600ms;
        }
        .animate-fade-in {
          animation: fade-in 0.8s ease-out;
        }
        .animate-slide-up {
          animation: slide-up 0.8s ease-out both;
        }
      `}</style>
    </div>
  );
}
