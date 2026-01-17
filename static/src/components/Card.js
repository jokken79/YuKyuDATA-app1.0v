/**
 * Card Component - YuKyuDATA Design System
 * Glass morphism card containers
 *
 * @module components/Card
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * Card options
 * @typedef {Object} CardOptions
 * @property {string} [title=''] - Card title
 * @property {string} [subtitle=''] - Card subtitle
 * @property {string|HTMLElement} [content=''] - Card body content
 * @property {string|HTMLElement} [footer=''] - Card footer content
 * @property {string} [icon=''] - Header icon SVG
 * @property {string} [variant='default'] - Variant: default, glass, elevated, outlined
 * @property {boolean} [hoverable=false] - Add hover effect
 * @property {boolean} [clickable=false] - Make entire card clickable
 * @property {boolean} [collapsible=false] - Allow collapse
 * @property {boolean} [collapsed=false] - Initial collapsed state
 * @property {string} [className=''] - Additional CSS classes
 * @property {Object} [headerAction] - Header action button { text, icon, onClick }
 * @property {Function} [onClick] - Card click handler
 */

/**
 * Create a card element
 * @param {CardOptions} options - Card configuration
 * @returns {HTMLElement} Card element
 */
export function Card(options = {}) {
  const {
    title = '',
    subtitle = '',
    content = '',
    footer = '',
    icon = '',
    variant = 'default',
    hoverable = false,
    clickable = false,
    collapsible = false,
    collapsed = false,
    className = '',
    headerAction = null,
    onClick = null
  } = options;

  injectCardStyles();

  const card = document.createElement('div');
  card.className = [
    'card',
    `card-${variant}`,
    hoverable ? 'card-hoverable' : '',
    clickable ? 'card-clickable' : '',
    collapsible ? 'card-collapsible' : '',
    collapsed ? 'card-collapsed' : '',
    className
  ].filter(Boolean).join(' ');

  if (clickable) {
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');
  }

  let html = '';

  // Header
  if (title || icon || headerAction) {
    html += '<div class="card-header">';

    if (icon) {
      html += `<div class="card-icon" aria-hidden="true">${icon}</div>`;
    }

    html += '<div class="card-header-content">';
    if (title) {
      html += `<h3 class="card-title">${escapeHtml(title)}</h3>`;
    }
    if (subtitle) {
      html += `<p class="card-subtitle">${escapeHtml(subtitle)}</p>`;
    }
    html += '</div>';

    if (headerAction) {
      html += `
        <button type="button" class="card-header-action" aria-label="${escapeHtml(headerAction.text || '')}">
          ${headerAction.icon || headerAction.text}
        </button>
      `;
    }

    if (collapsible) {
      html += `
        <button type="button" class="card-collapse-btn" aria-expanded="${!collapsed}" aria-label="展開/折りたたみ">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
      `;
    }

    html += '</div>';
  }

  // Body
  if (content) {
    html += '<div class="card-body">';
    if (typeof content === 'string') {
      html += content;
    }
    html += '</div>';
  }

  // Footer
  if (footer) {
    html += '<div class="card-footer">';
    if (typeof footer === 'string') {
      html += footer;
    }
    html += '</div>';
  }

  card.innerHTML = html;

  // Append HTMLElement content
  if (content instanceof HTMLElement) {
    const body = card.querySelector('.card-body');
    if (body) body.appendChild(content);
  }

  if (footer instanceof HTMLElement) {
    const footerEl = card.querySelector('.card-footer');
    if (footerEl) footerEl.appendChild(footer);
  }

  // Event handlers
  if (clickable && onClick) {
    card.addEventListener('click', onClick);
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onClick(e);
      }
    });
  }

  if (headerAction && headerAction.onClick) {
    const actionBtn = card.querySelector('.card-header-action');
    if (actionBtn) {
      actionBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        headerAction.onClick(e);
      });
    }
  }

  if (collapsible) {
    const collapseBtn = card.querySelector('.card-collapse-btn');
    if (collapseBtn) {
      collapseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        card.classList.toggle('card-collapsed');
        const isExpanded = !card.classList.contains('card-collapsed');
        collapseBtn.setAttribute('aria-expanded', isExpanded);
      });
    }
  }

  return card;
}

/**
 * Create a stat card for dashboard
 * @param {Object} options - Stat card options
 * @param {string} options.label - Stat label
 * @param {string|number} options.value - Stat value
 * @param {string} [options.unit=''] - Value unit
 * @param {string} [options.icon=''] - Icon SVG
 * @param {string} [options.trend=''] - Trend indicator (up, down, neutral)
 * @param {string} [options.trendValue=''] - Trend value text
 * @param {string} [options.variant='default'] - Color variant
 * @returns {HTMLElement} Stat card element
 */
export function StatCard(options = {}) {
  const {
    label,
    value,
    unit = '',
    icon = '',
    trend = '',
    trendValue = '',
    variant = 'default'
  } = options;

  injectCardStyles();

  const card = document.createElement('div');
  card.className = `stat-card stat-card-${variant}`;

  const trendIcon = {
    up: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    down: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>',
    neutral: ''
  };

  card.innerHTML = `
    ${icon ? `<div class="stat-icon" aria-hidden="true">${icon}</div>` : ''}
    <div class="stat-content">
      <div class="stat-value-wrapper">
        <span class="stat-value">${escapeHtml(String(value))}</span>
        ${unit ? `<span class="stat-unit">${escapeHtml(unit)}</span>` : ''}
      </div>
      <div class="stat-label">${escapeHtml(label)}</div>
      ${trend ? `
        <div class="stat-trend stat-trend-${trend}">
          ${trendIcon[trend] || ''}
          <span>${escapeHtml(trendValue)}</span>
        </div>
      ` : ''}
    </div>
  `;

  return card;
}

/**
 * Create a card group
 * @param {HTMLElement[]} cards - Array of card elements
 * @param {Object} [options={}] - Group options
 * @returns {HTMLDivElement} Card group element
 */
export function CardGroup(cards, options = {}) {
  const {
    columns = 'auto',
    gap = '1.5rem',
    className = ''
  } = options;

  const group = document.createElement('div');
  group.className = `card-group ${className}`.trim();

  if (columns === 'auto') {
    group.style.display = 'grid';
    group.style.gridTemplateColumns = 'repeat(auto-fill, minmax(280px, 1fr))';
  } else {
    group.style.display = 'grid';
    group.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
  }

  group.style.gap = gap;

  cards.forEach(card => group.appendChild(card));

  return group;
}

/**
 * Inject card styles
 * @private
 */
function injectCardStyles() {
  if (document.getElementById('card-component-styles')) return;

  const styles = document.createElement('style');
  styles.id = 'card-component-styles';
  styles.textContent = `
    .card {
      background: var(--card-bg, rgba(15, 15, 15, 0.85));
      backdrop-filter: blur(20px) saturate(180%);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
      border: var(--card-border, 1px solid rgba(255, 255, 255, 0.1));
      border-radius: var(--card-radius, 16px);
      overflow: hidden;
      transition: all var(--transition-smooth, 0.3s ease);
    }

    .card-glass {
      background: rgba(255, 255, 255, 0.05);
    }

    .card-elevated {
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    .card-outlined {
      background: transparent;
      backdrop-filter: none;
      border: 2px solid rgba(255, 255, 255, 0.15);
    }

    .card-hoverable {
      cursor: pointer;
    }

    .card-hoverable:hover {
      transform: translateY(-4px);
      border-color: rgba(255, 255, 255, 0.2);
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }

    .card-clickable {
      cursor: pointer;
    }

    .card-clickable:focus {
      outline: var(--focus-outline, 3px solid var(--color-primary));
      outline-offset: 2px;
    }

    .card-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: var(--card-padding, 1.5rem);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .card-icon {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(8, 145, 178, 0.1));
      border-radius: 12px;
      color: var(--color-primary, #06b6d4);
      flex-shrink: 0;
    }

    .card-icon svg {
      width: 24px;
      height: 24px;
    }

    .card-header-content {
      flex: 1;
      min-width: 0;
    }

    .card-title {
      font-size: var(--font-size-lg, 1.125rem);
      font-weight: var(--font-weight-semibold, 600);
      color: var(--color-text-primary, #f8fafc);
      margin: 0;
    }

    .card-subtitle {
      font-size: var(--font-size-sm, 0.875rem);
      color: var(--color-text-muted, #64748b);
      margin: 0.25rem 0 0 0;
    }

    .card-header-action {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 10px;
      color: var(--color-text-secondary, #94a3b8);
      cursor: pointer;
      transition: all 0.2s ease;
      flex-shrink: 0;
    }

    .card-header-action:hover {
      background: rgba(255, 255, 255, 0.1);
      color: var(--color-text-primary, #f8fafc);
    }

    .card-header-action:focus {
      outline: var(--focus-outline, 3px solid var(--color-primary));
      outline-offset: 2px;
    }

    .card-collapse-btn {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
      color: var(--color-text-secondary, #94a3b8);
      cursor: pointer;
      transition: transform 0.3s ease;
      flex-shrink: 0;
    }

    .card-collapse-btn:hover {
      color: var(--color-text-primary, #f8fafc);
    }

    .card-collapse-btn:focus {
      outline: var(--focus-outline, 3px solid var(--color-primary));
      outline-offset: 2px;
    }

    .card-collapsed .card-collapse-btn {
      transform: rotate(-90deg);
    }

    .card-body {
      padding: var(--card-padding, 1.5rem);
    }

    .card-collapsed .card-body {
      display: none;
    }

    .card-footer {
      padding: var(--card-padding, 1.5rem);
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      background: rgba(0, 0, 0, 0.1);
    }

    .card-collapsed .card-footer {
      display: none;
    }

    /* Stat Card */
    .stat-card {
      background: var(--card-bg, rgba(15, 15, 15, 0.85));
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 1.5rem;
      display: flex;
      align-items: flex-start;
      gap: 1rem;
      transition: all 0.3s ease;
    }

    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }

    .stat-icon {
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(8, 145, 178, 0.1));
      border-radius: 14px;
      color: var(--color-primary, #06b6d4);
      flex-shrink: 0;
    }

    .stat-icon svg {
      width: 24px;
      height: 24px;
    }

    .stat-content {
      flex: 1;
      min-width: 0;
    }

    .stat-value-wrapper {
      display: flex;
      align-items: baseline;
      gap: 0.25rem;
    }

    .stat-value {
      font-size: 2rem;
      font-weight: 800;
      color: var(--color-text-primary, #f8fafc);
      line-height: 1;
    }

    .stat-unit {
      font-size: 1rem;
      font-weight: 600;
      color: var(--color-text-secondary, #94a3b8);
    }

    .stat-label {
      font-size: var(--font-size-sm, 0.875rem);
      color: var(--color-text-muted, #64748b);
      margin-top: 0.5rem;
    }

    .stat-trend {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      font-size: var(--font-size-xs, 0.75rem);
      font-weight: 600;
      margin-top: 0.5rem;
      padding: 0.25rem 0.5rem;
      border-radius: 6px;
    }

    .stat-trend-up {
      background: rgba(52, 211, 153, 0.15);
      color: #34d399;
    }

    .stat-trend-down {
      background: rgba(248, 113, 113, 0.15);
      color: #f87171;
    }

    .stat-trend-neutral {
      background: rgba(148, 163, 184, 0.15);
      color: #94a3b8;
    }

    /* Stat card variants */
    .stat-card-success .stat-icon {
      background: linear-gradient(135deg, rgba(52, 211, 153, 0.2), rgba(16, 185, 129, 0.1));
      color: #34d399;
    }

    .stat-card-warning .stat-icon {
      background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.1));
      color: #fbbf24;
    }

    .stat-card-danger .stat-icon {
      background: linear-gradient(135deg, rgba(248, 113, 113, 0.2), rgba(239, 68, 68, 0.1));
      color: #f87171;
    }

    /* Light theme */
    [data-theme="light"] .card,
    [data-theme="light"] .stat-card {
      background: rgba(255, 255, 255, 0.95);
      border-color: rgba(0, 0, 0, 0.1);
    }

    [data-theme="light"] .card-hoverable:hover {
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    }

    [data-theme="light"] .card-title {
      color: #1e293b;
    }

    [data-theme="light"] .card-header,
    [data-theme="light"] .card-footer {
      border-color: rgba(0, 0, 0, 0.05);
    }

    [data-theme="light"] .stat-value {
      color: #1e293b;
    }

    /* Responsive */
    @media (max-width: 640px) {
      .card-header {
        padding: 1rem;
      }

      .card-body,
      .card-footer {
        padding: 1rem;
      }

      .stat-card {
        padding: 1rem;
      }

      .stat-value {
        font-size: 1.5rem;
      }
    }

    /* Reduced motion */
    @media (prefers-reduced-motion: reduce) {
      .card,
      .stat-card {
        transition: none;
      }

      .card-hoverable:hover,
      .stat-card:hover {
        transform: none;
      }
    }
  `;
  document.head.appendChild(styles);
}

export default Card;
