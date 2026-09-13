import React from "react";
import { Mail, Phone, Share2, MessageCircle } from "lucide-react";

export default function GovernmentFooter() {
  const currentDate = new Date().toLocaleDateString("en-IN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <footer className="bg-govDark text-white mt-12 border-t border-line">
      {/* Main Footer Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* About Section */}
          <div>
            <h3 className="font-semibold text-lg mb-4 text-govSaffron">
              GeM Sentinel
            </h3>
            <p className="text-sm text-gray-300 leading-relaxed">
              AI-powered bid compliance verification platform for Government e-Marketplace tender evaluation.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-semibold text-sm mb-4 text-govSaffron">
              Quick Links
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="#"
                  className="text-gray-300 hover:text-govSaffron transition"
                >
                  About Us
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-300 hover:text-govSaffron transition"
                >
                  Contact Us
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-300 hover:text-govSaffron transition"
                >
                  Feedback
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-300 hover:text-govSaffron transition"
                >
                  FAQs
                </a>
              </li>
            </ul>
          </div>

          {/* Help & Support */}
          <div>
            <h4 className="font-semibold text-sm mb-4 text-govSaffron">
              Help & Support
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="#"
                  className="text-gray-300 hover:text-govSaffron transition"
                >
                  Help Center
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-300 hover:text-govSaffron transition"
                >
                  Documentation
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-300 hover:text-govSaffron transition"
                >
                  Report Issue
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-300 hover:text-govSaffron transition"
                >
                  Terms & Policy
                </a>
              </li>
            </ul>
          </div>

          {/* Social & Contact */}
          <div>
            <h4 className="font-semibold text-sm mb-4 text-govSaffron">
              Connect With Us
            </h4>
            <div className="flex gap-3 mb-4">
              <a
                href="#"
                className="p-2 bg-govBlue rounded-lg hover:bg-govSaffron transition"
                aria-label="Share"
              >
                <Share2 size={16} />
              </a>
              <a
                href="#"
                className="p-2 bg-govBlue rounded-lg hover:bg-govSaffron transition"
                aria-label="Message"
              >
                <MessageCircle size={16} />
              </a>
              <a
                href="#"
                className="p-2 bg-govBlue rounded-lg hover:bg-govSaffron transition"
                aria-label="Email"
              >
                <Mail size={16} />
              </a>
              <a
                href="#"
                className="p-2 bg-govBlue rounded-lg hover:bg-govSaffron transition"
                aria-label="Phone"
              >
                <Phone size={16} />
              </a>
            </div>
          </div>
        </div>

        {/* Divider */}
        <hr className="border-gray-700 my-8" />

        {/* Bottom Section */}
        <div className="flex flex-col md:flex-row items-center justify-between text-xs text-gray-300">
          <div>
            <p>© 2026 Government of India. All rights reserved.</p>
            <p className="mt-1">
              Powered by Ministry of Petroleum & Natural Gas | Developed by National Informatics Centre (NIC)
            </p>
          </div>
          <div className="mt-4 md:mt-0 text-right">
            <p>
              <strong>Last updated:</strong> {currentDate}
            </p>
            <div className="mt-2 space-x-4">
              <a href="#" className="hover:text-govSaffron transition">
                Website Policy
              </a>
              <a href="#" className="hover:text-govSaffron transition">
                Disclaimer
              </a>
              <a href="#" className="hover:text-govSaffron transition">
                Accessibility
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* NIC Logo Section */}
      <div className="bg-black bg-opacity-30 px-4 py-4 border-t border-gray-700">
        <div className="container mx-auto flex flex-col sm:flex-row items-center justify-center gap-4 text-xs text-gray-400">
          <span>🏛️ Designed & Developed by</span>
          <span className="font-semibold text-govSaffron">
            National Informatics Centre (NIC)
          </span>
          <span>| Ministry of Electronics & Information Technology</span>
        </div>
      </div>
    </footer>
  );
}
