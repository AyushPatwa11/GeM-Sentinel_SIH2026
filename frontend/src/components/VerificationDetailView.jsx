/**
 * VerificationDetailView Component
 * 
 * Displays detailed verification information in a modal or panel:
 * - Original extracted value
 * - Normalized values (document & authority)
 * - Match result and score
 * - HTTP status and API reference
 * - Verification timestamp
 * - Verification attempt ID (for audit trail reference)
 * 
 * Features:
 * - Copyable verification_attempt_id for audit trail lookup
 * - Human-readable status explanations
 * - Score visualization as percentage
 * - Error messages (when applicable)
 */
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import './VerificationDetailView.css';

function VerificationDetailView({
  verificationAttemptId,
  onClose,
  isOpen = true,
}) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  // Fetch verification details from API
  useEffect(() => {
    if (!isOpen || !verificationAttemptId) {
      setLoading(false);
      return;
    }

    const fetchDetails = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `/api/verification/${verificationAttemptId}`
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch verification details: ${response.statusText}`);
        }

        const data = await response.json();
        setDetails(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [isOpen, verificationAttemptId]);

  const handleCopyAttemptId = () => {
    navigator.clipboard.writeText(verificationAttemptId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusExplanation = (status) => {
    const explanations = {
      VERIFIED: 'Authority confirmed this identifier matches the organization/person name',
      MISMATCH: 'Authority found this identifier, but the name does not match',
      UNAVAILABLE: 'Verification service is unreachable or timed out',
      ERROR: 'Technical error occurred during verification',
      INCONCLUSIVE: 'No record found in the authority registry',
      PENDING: 'Verification has not yet been attempted',
    };
    return explanations[status] || 'Status unknown';
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="verification-detail-overlay">
      <div className="verification-detail-modal">
        {/* Header */}
        <div className="detail-header">
          <h2>Verification Details</h2>
          <button
            className="close-button"
            onClick={onClose}
            aria-label="Close"
            title="Close details"
          >
            ✕
          </button>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="detail-loading">
            <div className="spinner" />
            <p>Loading verification details...</p>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="detail-error">
            <p className="error-icon">⚠</p>
            <p>{error}</p>
          </div>
        )}

        {/* Details content */}
        {details && !loading && (
          <div className="detail-content">
            {/* Verification Attempt ID */}
            <div className="detail-section">
              <h3>Verification Attempt</h3>
              <div className="attempt-id-row">
                <div className="attempt-id-label">Attempt ID:</div>
                <div className="attempt-id-value">
                  <code>{verificationAttemptId}</code>
                  <button
                    className="copy-button"
                    onClick={handleCopyAttemptId}
                    title="Copy to clipboard"
                  >
                    {copied ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>
              <p className="attempt-id-help">
                Use this ID to reference this verification in audit trails and
                compliance reports.
              </p>
            </div>

            {/* Status and Provider */}
            <div className="detail-section">
              <h3>Verification Status</h3>
              <table className="detail-table">
                <tbody>
                  <tr>
                    <td className="label">Status</td>
                    <td className="value">
                      <span className={`status-badge status-${details.status}`}>
                        {details.status}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="label">Provider</td>
                    <td className="value">{details.provider || 'N/A'}</td>
                  </tr>
                  <tr>
                    <td className="label">Verified</td>
                    <td className="value">
                      {new Date(details.timestamp).toLocaleString()}
                    </td>
                  </tr>
                </tbody>
              </table>
              <div className="status-explanation">
                <p>{getStatusExplanation(details.status)}</p>
              </div>
            </div>

            {/* Identifier Values */}
            <div className="detail-section">
              <h3>Identifier Values</h3>
              <table className="detail-table">
                <tbody>
                  <tr>
                    <td className="label">Extracted Value</td>
                    <td className="value">
                      <code>{details.document_value || 'N/A'}</code>
                    </td>
                  </tr>
                  <tr>
                    <td className="label">Normalized (Document)</td>
                    <td className="value">
                      <code>{details.normalized_document || 'N/A'}</code>
                    </td>
                  </tr>
                  <tr>
                    <td className="label">Authority Value</td>
                    <td className="value">
                      <code>{details.authority_value || 'N/A'}</code>
                    </td>
                  </tr>
                  <tr>
                    <td className="label">Normalized (Authority)</td>
                    <td className="value">
                      <code>{details.normalized_authority || 'N/A'}</code>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Name Matching */}
            {details.match_result && (
              <div className="detail-section">
                <h3>Name Matching</h3>
                <table className="detail-table">
                  <tbody>
                    <tr>
                      <td className="label">Match Result</td>
                      <td className="value">
                        <span className={`match-badge match-${details.match_result}`}>
                          {details.match_result.replace(/_/g, ' ')}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="label">Match Score</td>
                      <td className="value">
                        <div className="score-bar">
                          <div
                            className="score-fill"
                            style={{
                              width: `${(details.match_score || 0) * 100}%`,
                            }}
                          />
                          <div className="score-label">
                            {((details.match_score || 0) * 100).toFixed(1)}%
                          </div>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}

            {/* API Response Details */}
            <div className="detail-section">
              <h3>API Response</h3>
              <table className="detail-table">
                <tbody>
                  <tr>
                    <td className="label">HTTP Status</td>
                    <td className="value">
                      {details.http_status || 'N/A'}
                    </td>
                  </tr>
                  <tr>
                    <td className="label">Reference ID</td>
                    <td className="value">
                      <code>{details.reference_id || 'N/A'}</code>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Error message if present */}
            {details.error && (
              <div className="detail-section">
                <h3>Error Details</h3>
                <div className="error-box">
                  <p>{details.error}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

VerificationDetailView.propTypes = {
  verificationAttemptId: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  isOpen: PropTypes.bool,
};

export default VerificationDetailView;
