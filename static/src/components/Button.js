/**
 * Button Component - YuKyuDATA Design System
 * Accessible button with variants and loading state
 *
 * @module components/Button
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * Button options
 * @typedef {Object} ButtonOptions
 * @property {string} [text=''] - Button text
 * @property {string} [variant='primary'] - Variant: primary, secondary, danger, success, warning, ghost, glass
 * @property {string} [size='medium'] - Size: small, medium, large
 * @property {string} [type='button'] - Button type: button, submit, reset
 * @property {string} [icon] - Icon SVG string (before text)
 * @property {string} [iconAfter] - Icon SVG string (after text)
 * @property {boolean} [iconOnly=false] - Icon-only button
 * @property {boolean} [disabled=false] - Disabled state
 * @property {boolean} [loading=false] - Loading state
 * @property {string} [loadingText=''] - Text shown during loading
 * @property {boolean} [fullWidth=false] - Full width button
 * @property {string} [ariaLabel] - ARIA label for accessibility
 * @property {string} [className=''] - Additional CSS classes
 * @property {Object} [attributes={}] - Additional HTML attributes
 * @property {Function} [onClick] - Click handler
 */

/**
 * Create a button element
 * @param {ButtonOptions} options - Button configuration
 * @returns {HTMLButtonElement} Button element
 */
export function Button(options = {}) {
  const {
    text = '',
    variant = 'primary',
    size = 'medium',
    type = 'button',
    icon = null,
    iconAfter = null,
    iconOnly = false,
    disabled = false,
    loading = false,
    loadingText = '',
    fullWidth = false,
    ariaLabel = '',
    className = '',
    attributes = {},
    onClick = null
  } = options;

  // Inject styles once
  injectButtonStyles();

  // Create button element
  const button = document.createElement('button');
  button.type = type;

  // Build class list
  const classes = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    iconOnly ? 'btn-icon-only' : '',
    fullWidth ? 'btn-full' : '',
    loading ? 'btn-loading' : '',
    className
  ].filter(Boolean).join(' ');

  button.className = classes;

  // Accessibility
  if (ariaLabel || iconOnly) {
    button.setAttribute('aria-label', ariaLabel || text);
  }

  if (loading) {
    button.setAttribute('aria-busy', 'true');
  }

  if (disabled) {
    button.disabled = true;
  }

  // Additional attributes
  Object.entries(attributes).forEach(([key, value]) => {
    button.setAttribute(key, value);
  });

  // Build content
  let content = '';

  // Loading spinner
  if (loading) {
    content += `
      <span class="btn-spinner" aria-hidden="true">
        <svg class="spinner-icon" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-dasharray="32" stroke-linecap="round">
            <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="0.8s" repeatCount="indefinite"/>
          </circle>
        </svg>
      </span>
    `;
  }

  // Leading icon
  if (icon && !loading) {
    content += `<span class="btn-icon" aria-hidden="true">${icon}</span>`;
  }

  // Text
  if (!iconOnly) {
    const displayText = loading && loadingText ? loadingText : text;
    if (displayText) {
      content += `<span class="btn-text">${escapeHtml(displayText)}</span>`;
    }
  }

  // Trailing icon
  if (iconAfter && !loading) {
    content += `<span class="btn-icon btn-icon-after" aria-hidden="true">${iconAfter}</span>`;
  }

  button.innerHTML = content;

  // Event handler
  if (onClick && !disabled && !loading) {
    button.addEventListener('click', onClick);
  }

  // Add helper methods
  button._options = options;

  button.setLoading = (isLoading, newLoadingText) => {
    button._options.loading = isLoading;
    if (newLoadingText !== undefined) {
      button._options.loadingText = newLoadingText;
    }
    updateButton(button, button._options);
  };

  button.setDisabled = (isDisabled) => {
    button._options.disabled = isDisabled;
    button.disabled = isDisabled;
  };

  button.setText = (newText) => {
    button._options.text = newText;
    const textSpan = button.querySelector('.btn-text');
    if (textSpan) {
      textSpan.textContent = newText;
    }
  };

  return button;
}

/**
 * Update button content
 * @param {HTMLButtonElement} button - Button element
 * @param {ButtonOptions} options - New options
 */
function updateButton(button, options) {
  const {
    text = '',
    icon = null,
    iconAfter = null,
    iconOnly = false,
    loading = false,
    loadingText = ''
  } = options;

  button.classList.toggle('btn-loading', loading);
  button.setAttribute('aria-busy', loading ? 'true' : 'false');

  let content = '';

  if (loading) {
    content += `
      <span class="btn-spinner" aria-hidden="true">
        <svg class="spinner-icon" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-dasharray="32" stroke-linecap="round">
            <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="0.8s" repeatCount="indefinite"/>
          </circle>
        </svg>
      </span>
    `;
  }

  if (icon && !loading) {
    content += `<span class="btn-icon" aria-hidden="true">${icon}</span>`;
  }

  if (!iconOnly) {
    const displayText = loading && loadingText ? loadingText : text;
    if (displayText) {
      content += `<span class="btn-text">${escapeHtml(displayText)}</span>`;
    }
  }

  if (iconAfter && !loading) {
    content += `<span class="btn-icon btn-icon-after" aria-hidden="true">${iconAfter}</span>`;
  }

  button.innerHTML = content;
}

/**
 * Inject button styles
 * @private
 */
function injectButtonStyles() {
  if (document.getElementById('button-component-styles')) return;

  const styles = document.createElement('style');
  styles.id = 'button-component-styles';
  styles.textContent = `
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: var(--btn-padding-y, 0.75rem) var(--btn-padding-x, 1.5rem);
      border-radius: var(--btn-radius, 12px);
      font-weight: var(--btn-font-weight, 600);
      font-family: var(--font-family-main);
      font-size: var(--font-size-base, 1rem);
      line-height: 1;
      border: none;
      cursor: pointer;
      transition: all var(--transition-smooth, 0.2s ease);
      position: relative;
      overflow: hidden;
      text-decoration: none;
      user-select: none;
      white-space: nowrap;
    }

    .btn:focus-visible {
      outline: var(--focus-outline, 3px solid var(--color-primary));
      outline-offset: var(--focus-outline-offset, 2px);
    }

    .btn:disabled,
    .btn.disabled {
      opacity: 0.5;
      cursor: not-allowed;
      pointer-events: none;
    }

    /* Variants */
    .btn-primary {
      background: linear-gradient(135deg, var(--color-primary, #06b6d4), var(--color-secondary, #0891b2));
      color: #000;
      box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
    }

    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(6, 182, 212, 0.4);
    }

    .btn-primary:active {
      transform: translateY(0);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.1);
      color: var(--color-text-primary, #f8fafc);
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.15);
      border-color: rgba(255, 255, 255, 0.3);
    }

    .btn-danger {
      background: linear-gradient(135deg, var(--color-danger, #f87171), #ef4444);
      color: #fff;
      box-shadow: 0 4px 15px rgba(248, 113, 113, 0.3);
    }

    .btn-danger:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(248, 113, 113, 0.4);
    }

    .btn-success {
      background: linear-gradient(135deg, var(--color-success, #34d399), #10b981);
      color: #000;
      box-shadow: 0 4px 15px rgba(52, 211, 153, 0.3);
    }

    .btn-success:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(52, 211, 153, 0.4);
    }

    .btn-warning {
      background: linear-gradient(135deg, var(--color-warning, #fbbf24), #f59e0b);
      color: #000;
      box-shadow: 0 4px 15px rgba(251, 191, 36, 0.3);
    }

    .btn-warning:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(251, 191, 36, 0.4);
    }

    .btn-ghost {
      background: transparent;
      color: var(--color-text-secondary, #94a3b8);
      border: 1px solid transparent;
    }

    .btn-ghost:hover {
      background: rgba(255, 255, 255, 0.05);
      color: var(--color-text-primary, #f8fafc);
    }

    .btn-glass {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      color: var(--color-text-primary, #f8fafc);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .btn-glass:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.2);
      transform: translateY(-2px);
    }

    /* Sizes */
    .btn-small {
      padding: 0.5rem 1rem;
      font-size: var(--font-size-sm, 0.875rem);
      border-radius: 8px;
    }

    .btn-medium {
      padding: 0.75rem 1.5rem;
      font-size: var(--font-size-base, 1rem);
    }

    .btn-large {
      padding: 1rem 2rem;
      font-size: var(--font-size-lg, 1.125rem);
      border-radius: 14px;
    }

    /* Icon button */
    .btn-icon-only {
      padding: 0.75rem;
      aspect-ratio: 1;
    }

    .btn-icon-only.btn-small {
      padding: 0.5rem;
    }

    .btn-icon-only.btn-large {
      padding: 1rem;
    }

    /* Full width */
    .btn-full {
      width: 100%;
    }

    /* Icons */
    .btn-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      flex-shrink: 0;
    }

    .btn-icon svg {
      width: 100%;
      height: 100%;
    }

    .btn-small .btn-icon {
      width: 16px;
      height: 16px;
    }

    .btn-large .btn-icon {
      width: 24px;
      height: 24px;
    }

    /* Loading */
    .btn-loading {
      pointer-events: none;
    }

    .btn-spinner {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .spinner-icon {
      width: 20px;
      height: 20px;
      animation: btn-spin 0.8s linear infinite;
    }

    @keyframes btn-spin {
      to { transform: rotate(360deg); }
    }

    /* Light theme */
    [data-theme="light"] .btn-secondary {
      background: rgba(0, 0, 0, 0.05);
      color: #1e293b;
      border-color: rgba(0, 0, 0, 0.1);
    }

    [data-theme="light"] .btn-secondary:hover {
      background: rgba(0, 0, 0, 0.1);
      border-color: rgba(0, 0, 0, 0.2);
    }

    [data-theme="light"] .btn-ghost {
      color: #64748b;
    }

    [data-theme="light"] .btn-ghost:hover {
      background: rgba(0, 0, 0, 0.05);
      color: #1e293b;
    }

    [data-theme="light"] .btn-glass {
      background: rgba(255, 255, 255, 0.9);
      color: #1e293b;
      border-color: rgba(0, 0, 0, 0.1);
    }

    /* Reduced motion */
    @media (prefers-reduced-motion: reduce) {
      .btn {
        transition: opacity 0.01ms;
      }

      .btn:hover {
        transform: none;
      }

      .spinner-icon {
        animation: none;
      }
    }
  `;
  document.head.appendChild(styles);
}

/**
 * Button group component
 * @param {HTMLButtonElement[]} buttons - Array of buttons
 * @param {Object} [options] - Group options
 * @returns {HTMLDivElement} Button group element
 */
export function ButtonGroup(buttons, options = {}) {
  const { direction = 'horizontal', className = '' } = options;

  injectButtonGroupStyles();

  const group = document.createElement('div');
  group.className = `btn-group btn-group-${direction} ${className}`.trim();
  group.setAttribute('role', 'group');

  buttons.forEach(button => {
    group.appendChild(button);
  });

  return group;
}

/**
 * Inject button group styles
 * @private
 */
function injectButtonGroupStyles() {
  if (document.getElementById('button-group-styles')) return;

  const styles = document.createElement('style');
  styles.id = 'button-group-styles';
  styles.textContent = `
    .btn-group {
      display: inline-flex;
    }

    .btn-group-horizontal {
      flex-direction: row;
    }

    .btn-group-horizontal .btn:not(:first-child) {
      border-top-left-radius: 0;
      border-bottom-left-radius: 0;
      margin-left: -1px;
    }

    .btn-group-horizontal .btn:not(:last-child) {
      border-top-right-radius: 0;
      border-bottom-right-radius: 0;
    }

    .btn-group-vertical {
      flex-direction: column;
    }

    .btn-group-vertical .btn:not(:first-child) {
      border-top-left-radius: 0;
      border-top-right-radius: 0;
      margin-top: -1px;
    }

    .btn-group-vertical .btn:not(:last-child) {
      border-bottom-left-radius: 0;
      border-bottom-right-radius: 0;
    }
  `;
  document.head.appendChild(styles);
}

// Common icons as constants
export const ButtonIcons = {
  plus: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
  edit: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  delete: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>`,
  save: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>`,
  download: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
  upload: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
  refresh: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>`,
  search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
  close: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  arrow_left: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>`,
  arrow_right: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`,
  settings: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>`
};

export default Button;
