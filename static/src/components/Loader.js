/**
 * Loader Component - YuKyuDATA Design System
 * Loading spinners and skeleton screens
 *
 * @module components/Loader
 * @version 1.0.0
 */

/**
 * Loader options
 * @typedef {Object} LoaderOptions
 * @property {string} [type='spinner'] - Type: spinner, dots, pulse, skeleton
 * @property {string} [size='medium'] - Size: small, medium, large
 * @property {string} [color] - Custom color
 * @property {string} [text] - Loading text
 * @property {boolean} [overlay=false] - Show as overlay
 * @property {string} [className=''] - Additional CSS classes
 */

/**
 * Create a loader element
 * @param {LoaderOptions} options - Loader configuration
 * @returns {HTMLElement} Loader element
 */
export function Loader(options = {}) {
  const {
    type = 'spinner',
    size = 'medium',
    color = null,
    text = '',
    overlay = false,
    className = ''
  } = options;

  injectLoaderStyles();

  const loader = document.createElement('div');
  loader.className = `loader loader-${type} loader-${size} ${className}`.trim();
  loader.setAttribute('role', 'status');
  loader.setAttribute('aria-live', 'polite');
  loader.setAttribute('aria-label', text || '読み込み中');

  if (color) {
    loader.style.setProperty('--loader-color', color);
  }

  let content = '';

  switch (type) {
    case 'spinner':
      content = `
        <div class="loader-spinner" aria-hidden="true">
          <svg viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="80" stroke-linecap="round">
              <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="0.8s" repeatCount="indefinite"/>
            </circle>
          </svg>
        </div>
      `;
      break;

    case 'dots':
      content = `
        <div class="loader-dots" aria-hidden="true">
          <span class="loader-dot"></span>
          <span class="loader-dot"></span>
          <span class="loader-dot"></span>
        </div>
      `;
      break;

    case 'pulse':
      content = `
        <div class="loader-pulse" aria-hidden="true">
          <span class="loader-pulse-ring"></span>
          <span class="loader-pulse-ring"></span>
          <span class="loader-pulse-dot"></span>
        </div>
      `;
      break;

    case 'skeleton':
      content = `<div class="loader-skeleton" aria-hidden="true"></div>`;
      break;
  }

  if (text) {
    content += `<span class="loader-text">${text}</span>`;
  }

  // Screen reader text
  content += '<span class="sr-only">読み込み中...</span>';

  loader.innerHTML = content;

  if (overlay) {
    const wrapper = document.createElement('div');
    wrapper.className = 'loader-overlay';
    wrapper.appendChild(loader);
    return wrapper;
  }

  return loader;
}

/**
 * Create a skeleton loader
 * @param {string} variant - Variant: text, circle, rect, card, table
 * @param {Object} [options={}] - Options
 * @returns {HTMLElement} Skeleton element
 */
export function Skeleton(variant = 'text', options = {}) {
  const {
    width,
    height,
    lines = 3,
    className = ''
  } = options;

  injectLoaderStyles();

  const skeleton = document.createElement('div');
  skeleton.className = `skeleton skeleton-${variant} ${className}`.trim();
  skeleton.setAttribute('aria-hidden', 'true');

  if (width) skeleton.style.width = width;
  if (height) skeleton.style.height = height;

  // Multiple lines for text variant
  if (variant === 'text' && lines > 1) {
    skeleton.innerHTML = Array(lines).fill('<div class="skeleton-line"></div>').join('');
  }

  // Table skeleton
  if (variant === 'table') {
    const rows = options.rows || 5;
    const cols = options.cols || 4;

    let tableHtml = '<div class="skeleton-table-header">';
    for (let i = 0; i < cols; i++) {
      tableHtml += '<div class="skeleton-cell"></div>';
    }
    tableHtml += '</div>';

    for (let r = 0; r < rows; r++) {
      tableHtml += '<div class="skeleton-table-row">';
      for (let c = 0; c < cols; c++) {
        tableHtml += '<div class="skeleton-cell"></div>';
      }
      tableHtml += '</div>';
    }

    skeleton.innerHTML = tableHtml;
  }

  // Card skeleton
  if (variant === 'card') {
    skeleton.innerHTML = `
      <div class="skeleton-card-image"></div>
      <div class="skeleton-card-content">
        <div class="skeleton-line skeleton-line-lg"></div>
        <div class="skeleton-line skeleton-line-md"></div>
        <div class="skeleton-line skeleton-line-sm"></div>
      </div>
    `;
  }

  return skeleton;
}

/**
 * Show loading overlay on a target element
 * @param {HTMLElement|string} target - Target element or selector
 * @param {Object} [options={}] - Loader options
 * @returns {Function} Function to remove overlay
 */
export function showLoading(target, options = {}) {
  const element = typeof target === 'string'
    ? document.querySelector(target)
    : target;

  if (!element) return () => {};

  injectLoaderStyles();

  // Add positioning context if needed
  const position = getComputedStyle(element).position;
  if (position === 'static') {
    element.style.position = 'relative';
  }

  const overlay = document.createElement('div');
  overlay.className = 'loader-target-overlay';
  overlay.innerHTML = Loader({ ...options, type: 'spinner' }).outerHTML;

  element.appendChild(overlay);
  element.setAttribute('aria-busy', 'true');

  return function hideLoading() {
    overlay.remove();
    element.setAttribute('aria-busy', 'false');
    if (position === 'static') {
      element.style.position = '';
    }
  };
}

/**
 * Full page loading screen
 * @param {string} [text='読み込み中...'] - Loading text
 * @returns {Function} Function to hide loading
 */
export function showFullPageLoading(text = '読み込み中...') {
  injectLoaderStyles();

  const overlay = document.createElement('div');
  overlay.className = 'loader-fullpage';
  overlay.id = 'fullpage-loader';
  overlay.setAttribute('role', 'alert');
  overlay.setAttribute('aria-live', 'assertive');

  overlay.innerHTML = `
    <div class="loader-fullpage-content">
      ${Loader({ type: 'spinner', size: 'large' }).outerHTML}
      <p class="loader-fullpage-text">${text}</p>
    </div>
  `;

  document.body.appendChild(overlay);
  document.body.style.overflow = 'hidden';

  return function hideFullPageLoading() {
    const el = document.getElementById('fullpage-loader');
    if (el) {
      el.classList.add('hiding');
      setTimeout(() => {
        el.remove();
        document.body.style.overflow = '';
      }, 300);
    }
  };
}

/**
 * Inject loader styles
 * @private
 */
function injectLoaderStyles() {
  if (document.getElementById('loader-component-styles')) return;

  const styles = document.createElement('style');
  styles.id = 'loader-component-styles';
  styles.textContent = `
    /* Loader Base */
    .loader {
      display: inline-flex;
      flex-direction: column;
      align-items: center;
      gap: 0.75rem;
      --loader-color: var(--color-primary, #06b6d4);
    }

    /* Spinner */
    .loader-spinner {
      animation: loader-rotate 0.8s linear infinite;
    }

    .loader-spinner svg {
      color: var(--loader-color);
    }

    @keyframes loader-rotate {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    /* Sizes */
    .loader-small .loader-spinner svg {
      width: 20px;
      height: 20px;
    }

    .loader-medium .loader-spinner svg {
      width: 32px;
      height: 32px;
    }

    .loader-large .loader-spinner svg {
      width: 48px;
      height: 48px;
    }

    /* Dots */
    .loader-dots {
      display: flex;
      gap: 6px;
    }

    .loader-dot {
      width: 8px;
      height: 8px;
      background: var(--loader-color);
      border-radius: 50%;
      animation: loader-dots-bounce 0.6s ease-in-out infinite;
    }

    .loader-dot:nth-child(2) {
      animation-delay: 0.1s;
    }

    .loader-dot:nth-child(3) {
      animation-delay: 0.2s;
    }

    @keyframes loader-dots-bounce {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-8px); }
    }

    .loader-small .loader-dot {
      width: 6px;
      height: 6px;
    }

    .loader-large .loader-dot {
      width: 12px;
      height: 12px;
    }

    /* Pulse */
    .loader-pulse {
      position: relative;
      width: 40px;
      height: 40px;
    }

    .loader-pulse-ring {
      position: absolute;
      inset: 0;
      border: 3px solid var(--loader-color);
      border-radius: 50%;
      opacity: 0;
      animation: loader-pulse-ring 1.5s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
    }

    .loader-pulse-ring:nth-child(2) {
      animation-delay: 0.5s;
    }

    .loader-pulse-dot {
      position: absolute;
      top: 50%;
      left: 50%;
      width: 12px;
      height: 12px;
      margin: -6px 0 0 -6px;
      background: var(--loader-color);
      border-radius: 50%;
    }

    @keyframes loader-pulse-ring {
      0% {
        transform: scale(0.5);
        opacity: 1;
      }
      100% {
        transform: scale(1.5);
        opacity: 0;
      }
    }

    /* Loading text */
    .loader-text {
      font-size: var(--font-size-sm, 0.875rem);
      color: var(--color-text-muted, #64748b);
    }

    /* Overlay */
    .loader-overlay {
      position: fixed;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.5);
      backdrop-filter: blur(4px);
      -webkit-backdrop-filter: blur(4px);
      z-index: 9999;
    }

    /* Target overlay */
    .loader-target-overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(2px);
      -webkit-backdrop-filter: blur(2px);
      border-radius: inherit;
      z-index: 10;
    }

    /* Full page */
    .loader-fullpage {
      position: fixed;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--color-bg-dark, #000);
      z-index: 99999;
      transition: opacity 0.3s ease;
    }

    .loader-fullpage.hiding {
      opacity: 0;
    }

    .loader-fullpage-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1.5rem;
    }

    .loader-fullpage-text {
      font-size: var(--font-size-lg, 1.125rem);
      color: var(--color-text-secondary, #94a3b8);
    }

    /* Skeleton */
    .skeleton {
      position: relative;
      overflow: hidden;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
    }

    .skeleton::after {
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(255, 255, 255, 0.08) 50%,
        transparent 100%
      );
      animation: skeleton-shimmer 1.5s infinite;
    }

    @keyframes skeleton-shimmer {
      0% { transform: translateX(-100%); }
      100% { transform: translateX(100%); }
    }

    .skeleton-text {
      height: 1rem;
      width: 100%;
    }

    .skeleton-line {
      height: 1rem;
      margin-bottom: 0.75rem;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.05);
    }

    .skeleton-line:last-child {
      margin-bottom: 0;
      width: 70%;
    }

    .skeleton-line-sm { width: 40%; }
    .skeleton-line-md { width: 60%; }
    .skeleton-line-lg { width: 80%; }

    .skeleton-circle {
      width: 48px;
      height: 48px;
      border-radius: 50%;
    }

    .skeleton-rect {
      width: 100%;
      height: 120px;
    }

    /* Skeleton table */
    .skeleton-table {
      width: 100%;
    }

    .skeleton-table-header,
    .skeleton-table-row {
      display: flex;
      gap: 1rem;
      padding: 1rem;
    }

    .skeleton-table-header {
      background: rgba(255, 255, 255, 0.02);
    }

    .skeleton-table-row {
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .skeleton-cell {
      flex: 1;
      height: 1rem;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 4px;
    }

    /* Skeleton card */
    .skeleton-card {
      width: 100%;
    }

    .skeleton-card-image {
      height: 180px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px 8px 0 0;
    }

    .skeleton-card-content {
      padding: 1rem;
    }

    /* Light theme */
    [data-theme="light"] .skeleton {
      background: rgba(0, 0, 0, 0.05);
    }

    [data-theme="light"] .skeleton::after {
      background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(255, 255, 255, 0.5) 50%,
        transparent 100%
      );
    }

    [data-theme="light"] .skeleton-line,
    [data-theme="light"] .skeleton-cell,
    [data-theme="light"] .skeleton-card-image {
      background: rgba(0, 0, 0, 0.08);
    }

    [data-theme="light"] .loader-fullpage {
      background: var(--color-background, #f8fafc);
    }

    /* Reduced motion */
    @media (prefers-reduced-motion: reduce) {
      .loader-spinner,
      .loader-dot,
      .loader-pulse-ring {
        animation: none;
      }

      .skeleton::after {
        animation: none;
        background: rgba(255, 255, 255, 0.1);
      }

      [data-theme="light"] .skeleton::after {
        background: rgba(0, 0, 0, 0.1);
      }
    }

    /* Screen reader */
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }
  `;
  document.head.appendChild(styles);
}

export default Loader;
