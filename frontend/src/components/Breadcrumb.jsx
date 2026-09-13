import React from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

export default function Breadcrumb() {
  const location = useLocation();
  const pathname = location.pathname;

  // Function to convert path to breadcrumb label
  const pathToLabel = (path) => {
    const labels = {
      officer: "Officer Dashboard",
      bids: "Bids",
      audit: "Audit Trail",
      bidder: "Bidder Portal",
      tenders: "Tenders",
      status: "Bid Status",
      readiness: "Readiness Check",
      apply: "Apply to Tender",
      submit: "Submit Bid",
      "bidder/readiness": "Pre-submission Readiness",
    };

    return labels[path] || path.charAt(0).toUpperCase() + path.slice(1);
  };

  // Parse breadcrumbs from pathname
  const parseBreadcrumbs = () => {
    const parts = pathname.split("/").filter((p) => p);

    const breadcrumbs = [
      { label: "Home", path: "/" },
    ];

    let currentPath = "";
    parts.forEach((part) => {
      currentPath += `/${part}`;

      // Skip numeric IDs and certain internal paths
      if (!/^\d+$/.test(part) && !["submit", "apply"].includes(part)) {
        breadcrumbs.push({
          label: pathToLabel(part),
          path: currentPath,
        });
      }
    });

    return breadcrumbs;
  };

  const breadcrumbs = parseBreadcrumbs();

  // Hide breadcrumb on home page
  if (pathname === "/" || pathname === "/login") {
    return null;
  }

  return (
    <nav className="bg-govLight border-b border-line px-4 py-3 mt-0 pt-20 md:pt-3" aria-label="Breadcrumb">
      <div className="container mx-auto">
        <ol className="flex items-center gap-2 text-sm">
          {breadcrumbs.map((breadcrumb, index) => (
            <React.Fragment key={breadcrumb.path}>
              {index > 0 && (
                <li className="text-slate-400">
                  <ChevronRight size={16} className="inline" />
                </li>
              )}
              <li>
                {index === breadcrumbs.length - 1 ? (
                  // Current page (not clickable)
                  <span className="font-semibold text-govDark">
                    {breadcrumb.label}
                  </span>
                ) : (
                  // Clickable parent links
                  <Link
                    to={breadcrumb.path}
                    className="text-govBlue hover:text-govSaffron transition font-medium"
                  >
                    {index === 0 ? (
                      <Home size={16} className="inline mr-1" />
                    ) : null}
                    {breadcrumb.label}
                  </Link>
                )}
              </li>
            </React.Fragment>
          ))}
        </ol>
      </div>
    </nav>
  );
}
