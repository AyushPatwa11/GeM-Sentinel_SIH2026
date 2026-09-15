/**
 * VerificationBadge Component
 * 
 * Displays verification status with visual indicators:
 * - VERIFIED (✓, green)
 * - MISMATCH (✕, red)
 * - UNAVAILABLE (⚠, gray)
 * - ERROR (✕, red)
 * - INCONCLUSIVE (◌, orange)
 * - PENDING (◷, blue)
 * 
 * Features:
 * - Hover tooltip with provider, timestamp, reference_id
 * - Visual distinction between LIVE (Real) and MOCK (Fallback) verification
 * - Click handler for detailed view modal
 * - Compact badge design
 */
import React from 'react';
import PropTypes from 'prop-types';
import './VerificationBadge.css';

const statusConfig = {
  VERIFIED: {
    icon: '✓',
    color: '#4CAF50',
    bgColor: '#E8F5E9',
    label: 'VERIFIED',
    description: 'Verified by authority',
  },
  MISMATCH: {
    icon: '✕',
    color: '#F44336',
    bgColor: '#FFEBEE',
    label: 'MISMATCH',
    description: 'Name mismatch with authority record',
  },
  UNAVAILABLE: {
    icon: '⚠',
    color: '#9E9E9E',
    bgColor: '#F5F5F5',
    label: 'UNAVAILABLE',
    description: 'Verification service unreachable',
  },
  ERROR: {
    icon: '✕',
    color: '#F44336',
    bgColor: '#FFEBEE',
    label: 'ERROR',
    description: 'Verification error occurred',
  },
  INCONCLUSIVE: {
    icon: '◌',
    color: '#FF9800',
    bgColor: '#FFF3E0',
    label: 'INCONCLUSIVE',
    description: 'No record found in authority',
  },
  PENDING: {
    icon: '◷',
    color: '#2196F3',
    bgColor: '#E3F2FD',
    label: 'PENDING',
    description: 'Verification pending',
  },
};

function VerificationBadge({
  status = 'PENDING',
  verificationAttemptId,
  timestamp,
  apiReferenceId,
  fallbackUsed = false,
  provider,
  matchScore,
  onDetailClick,
  className = '',
}) {
  const config = statusConfig[status] || statusConfig.PENDING;

  // Format timestamp for display
  const formattedTimestamp = timestamp
    ? new Date(timestamp).toLocaleString()
    : 'N/A';

  // Build tooltip text
  const tooltipLines = [
    `Provider: ${fallbackUsed ? 'Mock (Fallback)' : 'Real (Live)'}`,
    `Status: ${config.label}`,
    `Verified: ${formattedTimestamp}`,
  ];

  if (apiReferenceId) {
    tooltipLines.push(`Reference ID: ${apiReferenceId}`);
  }

  if (matchScore !== undefined && matchScore !== null) {
    tooltipLines.push(`Match Score: ${(matchScore * 100).toFixed(1)}%`);
  }

  if (provider) {
    tooltipLines.push(`Provider: ${provider}`);
  }

  const tooltip = tooltipLines.join('\n');

  // Handle click to open detail view
  const handleClick = () => {
    if (onDetailClick && verificationAttemptId) {
      onDetailClick(verificationAttemptId);
    }
  };

  return (
    <div
      className={`verification-badge ${className}`}
      style={{
        backgroundColor: config.bgColor,
        borderColor: config.color,
        color: config.color,
        cursor: onDetailClick ? 'pointer' : 'default',
      }}
      title={tooltip}
      onClick={handleClick}
      role="button"
      tabIndex={onDetailClick ? 0 : -1}
      onKeyDown={(e) => {
        if (onDetailClick && (e.key === 'Enter' || e.key === ' ')) {
          handleClick();
        }
      }}
    >
      <span className="badge-icon" aria-label={config.label}>
        {config.icon}
      </span>
      <span className="badge-label">{config.label}</span>
      {fallbackUsed && (
        <span className="fallback-indicator" title="Mock/Fallback adapter used">
          [Mock]
        </span>
      )}
    </div>
  );
}

VerificationBadge.propTypes = {
  status: PropTypes.oneOf([
    'VERIFIED',
    'MISMATCH',
    'UNAVAILABLE',
    'ERROR',
    'INCONCLUSIVE',
    'PENDING',
  ]),
  verificationAttemptId: PropTypes.string,
  timestamp: PropTypes.string,
  apiReferenceId: PropTypes.string,
  fallbackUsed: PropTypes.bool,
  provider: PropTypes.string,
  matchScore: PropTypes.number,
  onDetailClick: PropTypes.func,
  className: PropTypes.string,
};

export default VerificationBadge;
