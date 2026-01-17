/**
 * Tooltip Component - YuKyuDATA Design System
 * Accessible tooltip with positioning and animations
 *
 * @module components/Tooltip
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * Tooltip options
 * @typedef {Object} TooltipOptions
 * @property {string} content - Tooltip content
 * @property {string} [position='top'] - Position: top, bottom, left, right
 * @property {string} [trigger='hover'] - Trigger: hover, click, focus
 * @property {number} [delay=200] - Show delay (ms)
 * @property {number} [hideDelay=0] - Hide delay (ms)
 * @property {boolean} [arrow=true] - Show arrow
 * @property {string} [className=''] - Additional CSS classes
 * @property {number} [offset=8] - Distance from target
 * @property {boolean} [interactive=false] - Allow interaction with tooltip
 */

/**
 * Tooltip manager for imperative creation
 */
const tooltipInstances = new WeakMap();

/**
 * Create and attach a tooltip to an element
 * @param {HTMLElement|string} target - Target element or selector
 * @param {TooltipOptions} options - Tooltip configuration
 * @returns {Object} Tooltip controller { show, hide, destroy }
 */
export function Tooltip(target, options = {}) {
  const element = typeof target === 'string'
    ? document.querySelector(target)
    : target;

  if (!element) {
    throw new Error('Tooltip: Target element not found');
  }

  // Check if already has tooltip
  if (tooltipInstances.has(element)) {
    return tooltipInstances.get(element);
  }

  const {
    content,
    position = 'top',
    trigger = 'hover',
    delay = 200,
    hideDelay = 0,
    arrow = true,
    className = '',
    offset = 8,
    interactive = false
  } = options;

  injectTooltipStyles();

  // State
  let tooltipEl = null;
  let showTimeout = null;
  let hideTimeout = null;
  let isVisible = false;

  // Generate unique ID
  const id = `tooltip-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Create tooltip element
  function createTooltip() {
    tooltipEl = document.createElement('div');
    tooltipEl.id = id;
    tooltipEl.className = `tooltip tooltip-${position} ${className}`.trim();
    tooltipEl.setAttribute('role', 'tooltip');
    tooltipEl.innerHTML = `
      <div class="tooltip-content">${escapeHtml(content)}</div>
      ${arrow ? '<div class="tooltip-arrow"></div>' : ''}
    `;

    document.body.appendChild(tooltipEl);

    if (interactive) {
      tooltipEl.addEventListener('mouseenter', cancelHide);
      tooltipEl.addEventListener('mouseleave', hide);
    }
  }

  // Position tooltip
  function positionTooltip() {
    if (!tooltipEl) return;

    const targetRect = element.getBoundingClientRect();
    const tooltipRect = tooltipEl.getBoundingClientRect();
    const scrollX = window.scrollX;
    const scrollY = window.scrollY;

    let top, left;

    switch (position) {
      case 'top':
        top = targetRect.top + scrollY - tooltipRect.height - offset;
        left = targetRect.left + scrollX + (targetRect.width - tooltipRect.width) / 2;
        break;
      case 'bottom':
        top = targetRect.bottom + scrollY + offset;
        left = targetRect.left + scrollX + (targetRect.width - tooltipRect.width) / 2;
        break;
      case 'left':
        top = targetRect.top + scrollY + (targetRect.height - tooltipRect.height) / 2;
        left = targetRect.left + scrollX - tooltipRect.width - offset;
        break;
      case 'right':
        top = targetRect.top + scrollY + (targetRect.height - tooltipRect.height) / 2;
        left = targetRect.right + scrollX + offset;
        break;
    }

    // Boundary checks
    const padding = 10;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    if (left < padding) left = padding;
    if (left + tooltipRect.width > viewportWidth - padding) {
      left = viewportWidth - tooltipRect.width - padding;
    }
    if (top < padding) top = padding;
    if (top + tooltipRect.height > viewportHeight + scrollY - padding) {
      top = viewportHeight + scrollY - tooltipRect.height - padding;
    }

    tooltipEl.style.top = `${top}px`;
    tooltipEl.style.left = `${left}px`;
  }

  // Show tooltip
  function show() {
    if (isVisible) return;

    clearTimeout(hideTimeout);

    showTimeout = setTimeout(() => {
      if (!tooltipEl) {
        createTooltip();
      }

      // Set ARIA
      element.setAttribute('aria-describedby', id);

      // Position and show
      requestAnimationFrame(() => {
        positionTooltip();
        tooltipEl.classList.add('visible');
        isVisible = true;
      });
    }, delay);
  }

  // Hide tooltip
  function hide() {
    clearTimeout(showTimeout);

    hideTimeout = setTimeout(() => {
      if (tooltipEl) {
        tooltipEl.classList.remove('visible');
        element.removeAttribute('aria-describedby');
        isVisible = false;
      }
    }, hideDelay);
  }

  // Cancel hide
  function cancelHide() {
    clearTimeout(hideTimeout);
  }

  // Destroy tooltip
  function destroy() {
    clearTimeout(showTimeout);
    clearTimeout(hideTimeout);

    // Remove event listeners
    element.removeEventListener('mouseenter', show);
    element.removeEventListener('mouseleave', hide);
    element.removeEventListener('focus', show);
    element.removeEventListener('blur', hide);
    element.removeEventListener('click', toggle);

    // ✅ AGREGAR: Remover listeners del tooltip si es interactivo
    if (tooltipEl && interactive) {
      tooltipEl.removeEventListener('mouseenter', cancelHide);
      tooltipEl.removeEventListener('mouseleave', hide);
    }

    // ✅ MEJORAR: Usar parentNode check robusto
    if (tooltipEl && tooltipEl.parentNode) {
      tooltipEl.parentNode.removeChild(tooltipEl);
    }

    element.removeAttribute('aria-describedby');
    tooltipEl = null;
    tooltipInstances.delete(element);
  }

  // Toggle for click trigger
  function toggle() {
    if (isVisible) {
      hide();
    } else {
      show();
    }
  }

  // Update content
  function setContent(newContent) {
    if (tooltipEl) {
      const contentEl = tooltipEl.querySelector('.tooltip-content');
      if (contentEl) {
        contentEl.textContent = newContent;
        positionTooltip();
      }
    }
  }

  // Bind events based on trigger
  switch (trigger) {
    case 'hover':
      element.addEventListener('mouseenter', show);
      element.addEventListener('mouseleave', hide);
      element.addEventListener('focus', show);
      element.addEventListener('blur', hide);
      break;
    case 'click':
      element.addEventListener('click', toggle);
      break;
    case 'focus':
      element.addEventListener('focus', show);
      element.addEventListener('blur', hide);
      break;
  }

  // Controller object
  const controller = {
    show,
    hide,
    destroy,
    setContent,
    get isVisible() { return isVisible; }
  };

  tooltipInstances.set(element, controller);
  return controller;
}

/**
 * Initialize tooltips from data attributes
 * @param {string} [selector='[data-tooltip]'] - Selector for tooltip triggers
 */
export function initTooltips(selector = '[data-tooltip]') {
  document.querySelectorAll(selector).forEach(el => {
    const content = el.dataset.tooltip;
    const position = el.dataset.tooltipPosition || 'top';
    const trigger = el.dataset.tooltipTrigger || 'hover';

    if (content) {
      Tooltip(el, { content, position, trigger });
    }
  });
}

/**
 * Destroy all tooltips
 */
export function destroyAllTooltips() {
  document.querySelectorAll('[aria-describedby^="tooltip-"]').forEach(el => {
    const controller = tooltipInstances.get(el);
    if (controller) {
      controller.destroy();
    }
  });
}

/**
 * Inject tooltip styles
 * @private
 */
function injectTooltipStyles() {
  if (document.getElementById('tooltip-component-styles')) return;

  const styles = document.createElement('style');
  styles.id = 'tooltip-component-styles';
  styles.textContent = `
    .tooltip {
      position: absolute;
      z-index: 9999;
      pointer-events: none;
      opacity: 0;
      transform: scale(0.95);
      transition: opacity 0.15s ease, transform 0.15s ease;
    }

    .tooltip.visible {
      opacity: 1;
      transform: scale(1);
    }

    .tooltip-content {
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      color: #f8fafc;
      padding: 8px 12px;
      border-radius: 8px;
      font-size: var(--font-size-sm, 0.875rem);
      line-height: 1.4;
      max-width: 300px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .tooltip-arrow {
      position: absolute;
      width: 8px;
      height: 8px;
      background: inherit;
      transform: rotate(45deg);
    }

    /* Arrow positioning */
    .tooltip-top .tooltip-arrow {
      bottom: -4px;
      left: 50%;
      margin-left: -4px;
      background: rgba(15, 23, 42, 0.95);
      border-right: 1px solid rgba(255, 255, 255, 0.1);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .tooltip-bottom .tooltip-arrow {
      top: -4px;
      left: 50%;
      margin-left: -4px;
      background: rgba(15, 23, 42, 0.95);
      border-left: 1px solid rgba(255, 255, 255, 0.1);
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .tooltip-left .tooltip-arrow {
      right: -4px;
      top: 50%;
      margin-top: -4px;
      background: rgba(15, 23, 42, 0.95);
      border-right: 1px solid rgba(255, 255, 255, 0.1);
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .tooltip-right .tooltip-arrow {
      left: -4px;
      top: 50%;
      margin-top: -4px;
      background: rgba(15, 23, 42, 0.95);
      border-left: 1px solid rgba(255, 255, 255, 0.1);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Interactive tooltip */
    .tooltip.interactive {
      pointer-events: auto;
    }

    /* Light theme */
    [data-theme="light"] .tooltip-content {
      background: rgba(255, 255, 255, 0.98);
      color: #1e293b;
      border-color: rgba(0, 0, 0, 0.1);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    [data-theme="light"] .tooltip-arrow {
      background: rgba(255, 255, 255, 0.98);
    }

    [data-theme="light"] .tooltip-top .tooltip-arrow {
      border-color: rgba(0, 0, 0, 0.1);
    }

    [data-theme="light"] .tooltip-bottom .tooltip-arrow {
      border-color: rgba(0, 0, 0, 0.1);
    }

    [data-theme="light"] .tooltip-left .tooltip-arrow {
      border-color: rgba(0, 0, 0, 0.1);
    }

    [data-theme="light"] .tooltip-right .tooltip-arrow {
      border-color: rgba(0, 0, 0, 0.1);
    }

    /* Reduced motion */
    @media (prefers-reduced-motion: reduce) {
      .tooltip {
        transition: opacity 0.01ms;
        transform: none !important;
      }
    }
  `;
  document.head.appendChild(styles);
}

export default Tooltip;
