/**
 * GEM Sentinel UI Component Library
 * Reusable components for the enterprise procurement platform
 */

import React from 'react';
import { colors, spacing, radius } from '../../styles/designSystem';

// ==================== BADGES & BADGES ====================

export const ComplianceScoreBadge = ({ score }) => {
  const getColor = () => {
    if (score >= 80) return colors.success[500];
    if (score >= 60) return colors.warning[500];
    return colors.error[500];
  };
  
  return (
    <div className="flex flex-col items-center gap-1">
      <div 
        className="w-24 h-24 rounded-full flex items-center justify-center text-2xl font-bold text-white"
        style={{ backgroundColor: getColor() }}
      >
        {score}
      </div>
      <span className="text-xs font-medium text-neutral-600">Compliance Score</span>
    </div>
  );
};

export const StatusBadge = ({ status, variant = 'default' }) => {
  const getStyles = () => {
    switch(status) {
      case 'compliant':
      case 'verified':
        return {
          bg: colors.success[50],
          text: colors.success[700],
          border: colors.success[200],
        };
      case 'warning':
      case 'review':
        return {
          bg: colors.warning[50],
          text: colors.warning[700],
          border: colors.warning[200],
        };
      case 'non-compliant':
      case 'rejected':
        return {
          bg: colors.error[50],
          text: colors.error[700],
          border: colors.error[200],
        };
      case 'pending':
        return {
          bg: colors.info[50],
          text: colors.info[700],
          border: colors.info[200],
        };
      default:
        return {
          bg: colors.neutral[50],
          text: colors.neutral[700],
          border: colors.neutral[200],
        };
    }
  };

  const styles = getStyles();
  const labels = {
    compliant: '✓ Compliant',
    verified: '✓ Verified',
    warning: '⚠ Review Required',
    review: '⚠ Under Review',
    'non-compliant': '✕ Non-Compliant',
    rejected: '✕ Rejected',
    pending: '○ Pending',
  };

  return (
    <span 
      className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border"
      style={{
        backgroundColor: styles.bg,
        color: styles.text,
        borderColor: styles.border,
      }}
    >
      {labels[status] || status}
    </span>
  );
};

export const RiskBadge = ({ level }) => {
  const levels = {
    low: { bg: colors.success[50], text: colors.success[700], border: colors.success[200] },
    medium: { bg: colors.warning[50], text: colors.warning[700], border: colors.warning[200] },
    high: { bg: colors.error[50], text: colors.error[700], border: colors.error[200] },
  };
  
  const style = levels[level] || levels.low;
  
  return (
    <span 
      className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border capitalize"
      style={{ ...style }}
    >
      {level} Risk
    </span>
  );
};

// ==================== KPI CARDS ====================

export const KPICard = ({ label, value, change, icon: Icon, color = 'primary' }) => {
  const colorMap = {
    primary: colors.primary[500],
    accent: colors.accent[500],
    success: colors.success[500],
    warning: colors.warning[500],
  };

  const isPositive = change >= 0;

  return (
    <div 
      className="p-6 rounded-lg border bg-white"
      style={{ borderColor: colors.neutral[200] }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-neutral-600">{label}</p>
          <p className="text-3xl font-bold text-neutral-900 mt-2">{value}</p>
          {change !== undefined && (
            <p className="text-xs mt-2" style={{ color: isPositive ? colors.success[600] : colors.error[600] }}>
              {isPositive ? '↑' : '↓'} {Math.abs(change)}% from last month
            </p>
          )}
        </div>
        {Icon && (
          <div 
            className="p-3 rounded-lg"
            style={{ backgroundColor: colorMap, color: 'white' }}
          >
            <Icon size={24} />
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== PROGRESS INDICATOR ====================

export const ProgressBar = ({ percentage, showLabel = true }) => {
  return (
    <div className="w-full">
      <div 
        className="h-2 rounded-full bg-neutral-200 overflow-hidden"
      >
        <div 
          className="h-full transition-all duration-500"
          style={{
            width: `${percentage}%`,
            backgroundColor: percentage >= 80 ? colors.success[500] : 
                           percentage >= 60 ? colors.warning[500] : 
                           colors.error[500]
          }}
        />
      </div>
      {showLabel && (
        <p className="text-xs font-medium text-neutral-600 mt-1">{percentage}% Complete</p>
      )}
    </div>
  );
};

// ==================== VERIFICATION CARD ====================

export const VerificationCard = ({ title, status, value, source, confidence }) => {
  return (
    <div 
      className="p-4 rounded-lg border bg-white"
      style={{ borderColor: colors.neutral[200] }}
    >
      <div className="flex items-start justify-between mb-3">
        <h4 className="font-medium text-neutral-900">{title}</h4>
        <StatusBadge status={status} />
      </div>
      
      <div className="space-y-2">
        {value && (
          <div>
            <p className="text-xs text-neutral-500">Extracted Value</p>
            <p className="text-sm font-mono text-neutral-900">{value}</p>
          </div>
        )}
        
        {source && (
          <div>
            <p className="text-xs text-neutral-500">Verification Source</p>
            <p className="text-sm text-neutral-700">{source}</p>
          </div>
        )}
        
        {confidence && (
          <div>
            <p className="text-xs text-neutral-500">Confidence Score</p>
            <div className="flex items-center gap-2 mt-1">
              <div className="h-1.5 flex-1 rounded-full bg-neutral-200">
                <div 
                  className="h-full rounded-full"
                  style={{
                    width: `${confidence}%`,
                    backgroundColor: colors.accent[500]
                  }}
                />
              </div>
              <span className="text-xs font-medium text-neutral-900">{confidence}%</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== AI RECOMMENDATION ====================

export const AIRecommendationPanel = ({ 
  title = 'AI Assessment',
  recommendation,
  confidence,
  findings = [],
  actions = [],
  onAction
}) => {
  return (
    <div 
      className="p-6 rounded-lg border"
      style={{ 
        borderColor: colors.accent[200],
        backgroundColor: colors.accent[50]
      }}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-semibold text-neutral-900">{title}</h3>
          <p className="text-sm text-neutral-600 mt-1">{recommendation}</p>
        </div>
        <div 
          className="px-3 py-1 rounded-full text-xs font-bold text-white"
          style={{ backgroundColor: colors.accent[500] }}
        >
          {confidence}% Confidence
        </div>
      </div>

      {findings.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs font-semibold uppercase text-neutral-600 mb-2">Key Findings</h4>
          <ul className="space-y-1">
            {findings.map((finding, i) => (
              <li key={i} className="text-sm text-neutral-700">
                {finding.passed ? '✓ ' : '⚠ '}{finding.text}
              </li>
            ))}
          </ul>
        </div>
      )}

      {actions.length > 0 && (
        <div className="flex gap-2 pt-4 border-t" style={{ borderColor: colors.accent[200] }}>
          {actions.map((action, i) => (
            <button
              key={i}
              onClick={() => onAction?.(action.id)}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                backgroundColor: action.primary ? colors.primary[600] : colors.neutral[100],
                color: action.primary ? 'white' : colors.neutral[900],
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}

      <p className="text-xs text-neutral-500 mt-4 italic">
        💡 AI provides recommendations. Procurement officer makes the final decision.
      </p>
    </div>
  );
};

// ==================== REQUIREMENT CARD ====================

export const RequirementCard = ({ 
  title, 
  description, 
  status, 
  evidence,
  onClick 
}) => {
  const getStatusColor = () => {
    switch(status) {
      case 'satisfied': return { bg: colors.success[50], border: colors.success[200], icon: '✓' };
      case 'review': return { bg: colors.warning[50], border: colors.warning[200], icon: '⚠' };
      case 'missing': return { bg: colors.error[50], border: colors.error[200], icon: '✕' };
      default: return { bg: colors.neutral[50], border: colors.neutral[200], icon: '○' };
    }
  };

  const statusStyle = getStatusColor();

  return (
    <div 
      className="p-4 rounded-lg border cursor-pointer hover:shadow-md transition-all"
      style={{ borderColor: statusStyle.border, backgroundColor: statusStyle.bg }}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <span className="text-lg font-bold text-neutral-900">{statusStyle.icon}</span>
        <div className="flex-1">
          <h4 className="font-semibold text-neutral-900">{title}</h4>
          {description && <p className="text-xs text-neutral-600 mt-1">{description}</p>}
          {evidence && <p className="text-xs text-neutral-500 mt-1">Evidence: {evidence}</p>}
        </div>
      </div>
    </div>
  );
};

// ==================== DATA TABLE ====================

export const DataTable = ({ columns, rows, onRowClick }) => {
  return (
    <div className="overflow-x-auto rounded-lg border" style={{ borderColor: colors.neutral[200] }}>
      <table className="w-full">
        <thead 
          style={{ backgroundColor: colors.neutral[50] }}
        >
          <tr>
            {columns.map((col) => (
              <th 
                key={col.key}
                className="px-6 py-3 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr 
              key={i}
              className="border-t hover:bg-neutral-50 cursor-pointer transition-colors"
              style={{ borderColor: colors.neutral[200] }}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((col) => (
                <td key={col.key} className="px-6 py-4 text-sm text-neutral-900">
                  {col.render ? col.render(row[col.key], row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ==================== TIMELINE ====================

export const Timeline = ({ events }) => {
  return (
    <div className="relative">
      {events.map((event, i) => (
        <div key={i} className="flex gap-4 pb-6 relative">
          {/* Timeline dot */}
          <div className="flex flex-col items-center">
            <div 
              className="w-3 h-3 rounded-full border-2"
              style={{
                backgroundColor: event.color || colors.primary[500],
                borderColor: event.color || colors.primary[500],
              }}
            />
            {i < events.length - 1 && (
              <div 
                className="w-0.5 h-12 mt-2"
                style={{ backgroundColor: colors.neutral[200] }}
              />
            )}
          </div>

          {/* Event content */}
          <div className="flex-1">
            <h4 className="font-semibold text-neutral-900">{event.title}</h4>
            <p className="text-xs text-neutral-500 mt-0.5">{event.time}</p>
            {event.description && <p className="text-sm text-neutral-700 mt-2">{event.description}</p>}
            {event.metadata && (
              <div className="mt-2 text-xs text-neutral-600">
                {Object.entries(event.metadata).map(([key, val]) => (
                  <p key={key}><span className="font-medium">{key}:</span> {val}</p>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

// ==================== LOADING & EMPTY STATES ====================

export const LoadingSpinner = () => (
  <div className="flex items-center justify-center py-12">
    <div className="relative w-12 h-12">
      <div 
        className="absolute inset-0 rounded-full border-4 border-neutral-200"
      />
      <div 
        className="absolute inset-0 rounded-full border-4 border-transparent animate-spin"
        style={{
          borderTopColor: colors.primary[500],
          borderRightColor: colors.accent[500],
        }}
      />
    </div>
  </div>
);

export const EmptyState = ({ title, description, icon: Icon, action }) => (
  <div className="py-12 text-center">
    {Icon && <Icon className="mx-auto mb-4 text-neutral-400" size={48} />}
    <h3 className="text-lg font-semibold text-neutral-900">{title}</h3>
    <p className="text-sm text-neutral-600 mt-1 max-w-md mx-auto">{description}</p>
    {action && (
      <button 
        className="mt-4 px-4 py-2 rounded-lg font-medium text-white"
        style={{ backgroundColor: colors.primary[600] }}
        onClick={action.onClick}
      >
        {action.label}
      </button>
    )}
  </div>
);

export default {
  ComplianceScoreBadge,
  StatusBadge,
  RiskBadge,
  KPICard,
  ProgressBar,
  VerificationCard,
  AIRecommendationPanel,
  RequirementCard,
  DataTable,
  Timeline,
  LoadingSpinner,
  EmptyState,
};
