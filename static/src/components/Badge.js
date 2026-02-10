/**
 * Badge Component - YuKyuDATA Design System
 * Status badges and labels with variants
 *
 * @module components/Badge
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * Badge options
 * @typedef {Object} BadgeOptions
 * @property {string} text - Badge text
 * @property {string} [variant='neutral'] - Variant: success, warning, error, info, neutral, primary
 * @property {string} [size='medium'] - Size: small, medium, large
 * @property {string} [icon] - Icon SVG string
 * @property {boolean} [pulse=false] - Pulse animation (for critical badges)
 * @property {boolean} [dot=false] - Show as dot only (no text)
 * @property {string} [className=''] - Additional CSS classes
 */

/**
 * Status mapping for Japanese leave request statuses
 */
export const STATUS_VARIANTS = {
  APPROVED: { variant: 'success', text: '承認済み' },
  PENDING: { variant: 'warning', text: '申請中' },
  REJECTED: { variant: 'error', text: '却下' },
  CANCELLED: { variant: 'neutral', text: 'キャンセル' },
  DRAFT: { variant: 'info', text: '下書き' }
};

/**
 * Create a badge element
 * @param {BadgeOptions} options - Badge configuration
 * @returns {HTMLSpanElement} Badge element
 */
export function Badge(options = {}) {
  const {
    text = '',
    variant = 'neutral',
    size = 'medium',
    icon = null,
    pulse = false,
    dot = false,
    className = ''
  } = options;

  // Inject styles once
  injectBadgeStyles();

  // Create badge element
  const badge = document.createElement('span');

  const classes = [
    'badge',
    `badge-${variant}`,
    `badge-${size}`,
    pulse ? 'badge-pulse' : '',
    dot ? 'badge-dot' : '',
    className
  ].filter(Boolean).join(' ');

  badge.className = classes;

  // Build content
  let content = '';

  if (dot) {
    content = '<span class="badge-dot-indicator" aria-hidden="true"></span>';
    badge.setAttribute('aria-label', text);
  } else {
    if (icon) {
      content += `<span class="badge-icon" aria-hidden="true">${icon}</span>`;
    }
    content += `<span class="badge-text">${escapeHtml(text)}</span>`;
  }

  badge.innerHTML = content;

  return badge;
}

/**
 * Create a status badge from status code
 * @param {string} status - Status code (APPROVED, PENDING, etc.)
 * @param {Object} [options={}] - Additional options
 * @returns {HTMLSpanElement} Badge element
 */
export function StatusBadge(status, options = {}) {
  const statusConfig = STATUS_VARIANTS[status] || { variant: 'neutral', text: status };

  return Badge({
    text: statusConfig.text,
    variant: statusConfig.variant,
    ...options
  });
}

/**
 * Create a numeric badge (e.g., notification count)
 * @param {number} count - Count to display
 * @param {Object} [options={}] - Additional options
 * @returns {HTMLSpanElement} Badge element
 */
export function CountBadge(count, options = {}) {
  const displayCount = count > 99 ? '99+' : String(count);

  return Badge({
    text: displayCount,
    variant: options.variant || (count > 0 ? 'error' : 'neutral'),
    size: 'small',
    ...options,
    className: `badge-count ${options.className || ''}`
  });
}

/**
 * Create a badge group
 * @param {HTMLSpanElement[]} badges - Array of badge elements
 * @param {Object} [options={}] - Group options
 * @returns {HTMLDivElement} Badge group element
 */
export function BadgeGroup(badges, options = {}) {
  const { gap = '0.5rem', className = '' } = options;

  const group = document.createElement('div');
  group.className = `badge-group ${className}`.trim();
  group.style.display = 'inline-flex';
  group.style.alignItems = 'center';
  group.style.gap = gap;
  group.style.flexWrap = 'wrap';

  badges.forEach(badge => group.appendChild(badge));

  return group;
}

/**
 * Inject badge styles
 * @private
 */
function injectBadgeStyles() {
  if (document.getElementById('badge-component-styles')) return;

  const styles = document.createElement('style');
  styles.id = 'badge-component-styles';
  styles.textContent = `
    .badge {
      display: inline-flex;
      align-items: center;
      gap: var(--space-1, 0.25rem);
      padding: var(--badge-padding-y, 0.25rem) var(--badge-padding-x, 0.75rem);
      border-radius: var(--badge-radius, 9999px);
      font-size: var(--badge-font-size, 0.75rem);
      font-weight: var(--badge-font-weight, 600);
      line-height: 1;
      white-space: nowrap;
      transition: all var(--transition-base, 0.2s ease);
    }

    /* Sizes */
    .badge-small {
      padding: 0.15rem 0.5rem;
      font-size: 0.65rem;
    }

    .badge-medium {
      padding: 0.25rem 0.75rem;
      font-size: 0.75rem;
    }

    .badge-large {
      padding: 0.35rem 1rem;
      font-size: 0.85rem;
    }

    /* Icon */
    .badge-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 12px;
      height: 12px;
      flex-shrink: 0;
    }

    .badge-icon svg {
      width: 100%;
      height: 100%;
    }

    .badge-large .badge-icon {
      width: 14px;
      height: 14px;
    }

    /* Dot badge */
    .badge-dot {
      padding: 0;
      width: 8px;
      height: 8px;
      min-width: 8px;
    }

    .badge-dot .badge-dot-indicator {
      width: 100%;
      height: 100%;
      border-radius: 50%;
      background: currentColor;
    }

    .badge-dot.badge-small {
      width: 6px;
      height: 6px;
      min-width: 6px;
    }

    .badge-dot.badge-large {
      width: 10px;
      height: 10px;
      min-width: 10px;
    }

    /* Count badge */
    .badge-count {
      min-width: 20px;
      height: 20px;
      padding: 0 6px;
      justify-content: center;
      font-weight: 700;
    }

    .badge-count.badge-small {
      min-width: 16px;
      height: 16px;
      padding: 0 4px;
    }

    /* Variants - Dark theme (default) */
    .badge-success {
      background: rgba(52, 211, 153, 0.2);
      color: #34d399;
      border: 1px solid rgba(52, 211, 153, 0.3);
    }

    .badge-warning {
      background: rgba(251, 191, 36, 0.2);
      color: #fbbf24;
      border: 1px solid rgba(251, 191, 36, 0.3);
    }

    .badge-error {
      background: rgba(248, 113, 113, 0.2);
      color: #f87171;
      border: 1px solid rgba(248, 113, 113, 0.3);
    }

    .badge-info {
      background: rgba(56, 189, 248, 0.2);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }

    .badge-neutral {
      background: rgba(148, 163, 184, 0.2);
      color: #94a3b8;
      border: 1px solid rgba(148, 163, 184, 0.3);
    }

    .badge-primary {
      background: rgba(37, 99, 235, 0.2);
      color: #2563eb;
      border: 1px solid rgba(37, 99, 235, 0.3);
    }

    /* Light theme */
    [data-theme="light"] .badge-success {
      background: rgba(22, 163, 74, 0.12);
      color: #15803d;
      border-color: rgba(22, 163, 74, 0.25);
    }

    [data-theme="light"] .badge-warning {
      background: rgba(217, 119, 6, 0.12);
      color: #b45309;
      border-color: rgba(217, 119, 6, 0.25);
    }

    [data-theme="light"] .badge-error {
      background: rgba(220, 38, 38, 0.12);
      color: #b91c1c;
      border-color: rgba(220, 38, 38, 0.25);
    }

    [data-theme="light"] .badge-info {
      background: rgba(14, 116, 144, 0.12);
      color: #1e40af;
      border-color: rgba(14, 116, 144, 0.25);
    }

    [data-theme="light"] .badge-neutral {
      background: rgba(100, 116, 139, 0.12);
      color: #475569;
      border-color: rgba(100, 116, 139, 0.25);
    }

    [data-theme="light"] .badge-primary {
      background: rgba(8, 145, 178, 0.12);
      color: #1d4ed8;
      border-color: rgba(8, 145, 178, 0.25);
    }

    /* Pulse animation */
    .badge-pulse {
      animation: badge-pulse-anim 1.5s ease-in-out infinite;
    }

    @keyframes badge-pulse-anim {
      0%, 100% {
        opacity: 1;
        transform: scale(1);
      }
      50% {
        opacity: 0.7;
        transform: scale(1.05);
      }
    }

    /* With glow effect in dark mode */
    [data-theme="dark"] .badge-success {
      box-shadow: 0 0 12px rgba(52, 211, 153, 0.3);
    }

    [data-theme="dark"] .badge-warning {
      box-shadow: 0 0 12px rgba(251, 191, 36, 0.3);
    }

    [data-theme="dark"] .badge-error {
      box-shadow: 0 0 12px rgba(248, 113, 113, 0.3);
    }

    [data-theme="dark"] .badge-info {
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.2);
    }

    [data-theme="dark"] .badge-primary {
      box-shadow: 0 0 12px rgba(37, 99, 235, 0.3);
    }

    /* Reduced motion */
    @media (prefers-reduced-motion: reduce) {
      .badge-pulse {
        animation: none;
      }
    }
  `;
  document.head.appendChild(styles);
}

/**
 * Employee type badge variants
 */
export const EMPLOYEE_TYPE_VARIANTS = {
  genzai: { variant: 'info', text: '派遣' },
  ukeoi: { variant: 'warning', text: '請負' },
  staff: { variant: 'success', text: 'スタッフ' }
};

/**
 * Create an employee type badge
 * @param {string} type - Employee type (genzai, ukeoi, staff)
 * @param {Object} [options={}] - Additional options
 * @returns {HTMLSpanElement} Badge element
 */
export function EmployeeTypeBadge(type, options = {}) {
  const typeConfig = EMPLOYEE_TYPE_VARIANTS[type] || { variant: 'neutral', text: type };

  return Badge({
    text: typeConfig.text,
    variant: typeConfig.variant,
    size: 'small',
    ...options,
    className: `badge-type ${options.className || ''}`
  });
}

export default Badge;
