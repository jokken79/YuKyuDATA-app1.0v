/**
 * Accessibility Utilities - WCAG AA Compliance
 * Provides utilities for keyboard navigation, screen readers, and focus management
 */

/**
 * Focus management for modals and dialogs
 */
export const FocusManager = {
  /**
   * Trap focus within an element
   * @param {HTMLElement} element - Container element
   * @param {Function} onEscape - Callback for Escape key
   */
  trapFocus(element, onEscape) {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (event) => {
      // Escape key
      if (event.key === 'Escape' && onEscape) {
        onEscape();
        return;
      }

      // Tab key
      if (event.key === 'Tab') {
        if (event.shiftKey) {
          // Shift + Tab
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          // Tab
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    element.addEventListener('keydown', handleKeyDown);

    // Focus first element
    if (firstElement) {
      firstElement.focus();
    }

    // Return cleanup function
    return () => {
      element.removeEventListener('keydown', handleKeyDown);
    };
  },

  /**
   * Move focus to element with smooth scroll
   * @param {HTMLElement} element - Target element
   */
  moveFocusTo(element) {
    element.focus({ preventScroll: false });
    if (element.scrollIntoView) {
      element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  },

  /**
   * Store and restore focus
   */
  createFocusRestorer() {
    let previouslyFocused = null;

    return {
      save() {
        previouslyFocused = document.activeElement;
      },
      restore() {
        if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
          previouslyFocused.focus();
        }
      },
    };
  },
};

/**
 * ARIA label management
 */
export const AriaManager = {
  /**
   * Set ARIA label (Japanese)
   * @param {HTMLElement} element - Target element
   * @param {string} label - Japanese label
   */
  setLabel(element, label) {
    element.setAttribute('aria-label', label);
  },

  /**
   * Set ARIA description (Japanese)
   * @param {HTMLElement} element - Target element
   * @param {string} description - Japanese description
   */
  setDescription(element, description) {
    const id = `aria-desc-${Math.random().toString(36).substr(2, 9)}`;
    const descElement = document.createElement('span');
    descElement.id = id;
    descElement.className = 'sr-only';
    descElement.textContent = description;
    document.body.appendChild(descElement);
    element.setAttribute('aria-describedby', id);
    return id;
  },

  /**
   * Set ARIA alert
   * @param {HTMLElement} element - Target element
   * @param {string} message - Alert message
   */
  announce(element, message) {
    const id = `aria-alert-${Math.random().toString(36).substr(2, 9)}`;
    const alertElement = document.createElement('div');
    alertElement.id = id;
    alertElement.setAttribute('role', 'alert');
    alertElement.setAttribute('aria-live', 'polite');
    alertElement.className = 'sr-only';
    alertElement.textContent = message;
    document.body.appendChild(alertElement);

    setTimeout(() => {
      alertElement.remove();
    }, 5000);
  },

  /**
   * Set form validation error
   * @param {HTMLElement} input - Input element
   * @param {string} errorMessage - Error message
   */
  setValidationError(input, errorMessage) {
    const errorId = `error-${input.id || Math.random().toString(36).substr(2, 9)}`;
    input.setAttribute('aria-invalid', 'true');
    input.setAttribute('aria-describedby', errorId);

    // Create error message element
    const errorElement = document.getElementById(errorId) || document.createElement('div');
    errorElement.id = errorId;
    errorElement.role = 'alert';
    errorElement.className = 'form-error';
    errorElement.textContent = errorMessage;

    if (!document.getElementById(errorId)) {
      input.parentElement?.appendChild(errorElement);
    }
  },

  /**
   * Clear validation error
   * @param {HTMLElement} input - Input element
   */
  clearValidationError(input) {
    input.removeAttribute('aria-invalid');
    input.removeAttribute('aria-describedby');
    const errorId = `error-${input.id}`;
    document.getElementById(errorId)?.remove();
  },
};

/**
 * Keyboard navigation helpers
 */
export const KeyboardNav = {
  /**
   * Handle arrow key navigation for lists
   * @param {HTMLElement} container - List container
   * @param {string} itemSelector - Selector for list items
   */
  setupArrowKeyNavigation(container, itemSelector = 'li') {
    const items = Array.from(container.querySelectorAll(itemSelector));

    const handleKeyDown = (event) => {
      const currentIndex = items.findIndex(
        (item) => item.contains(document.activeElement)
      );

      if (currentIndex === -1) return;

      let nextIndex = currentIndex;

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          nextIndex = (currentIndex + 1) % items.length;
          break;
        case 'ArrowUp':
          event.preventDefault();
          nextIndex = (currentIndex - 1 + items.length) % items.length;
          break;
        case 'Home':
          event.preventDefault();
          nextIndex = 0;
          break;
        case 'End':
          event.preventDefault();
          nextIndex = items.length - 1;
          break;
        default:
          return;
      }

      const nextItem = items[nextIndex];
      if (nextItem) {
        const focusable = nextItem.querySelector('a, button, [tabindex]');
        if (focusable) {
          focusable.focus();
        } else {
          nextItem.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  },

  /**
   * Handle Enter/Space key activation
   * @param {HTMLElement} element - Target element
   * @param {Function} callback - Activation callback
   */
  setupActivationKey(element, callback) {
    const handleKeyDown = (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        callback();
      }
    };

    element.addEventListener('keydown', handleKeyDown);

    return () => {
      element.removeEventListener('keydown', handleKeyDown);
    };
  },
};

/**
 * Screen reader only content
 */
export const ScreenReaderOnly = {
  /**
   * Hide element visually but keep for screen readers
   * @param {HTMLElement} element - Target element
   */
  show(element) {
    element.classList.add('sr-only');
  },

  /**
   * Show element visually
   * @param {HTMLElement} element - Target element
   */
  hide(element) {
    element.classList.remove('sr-only');
  },

  /**
   * Create screen reader only span
   * @param {string} text - Text content
   * @returns {HTMLElement} - Created element
   */
  create(text) {
    const element = document.createElement('span');
    element.className = 'sr-only';
    element.textContent = text;
    return element;
  },
};

/**
 * Skip link for keyboard navigation
 */
export const SkipLink = {
  /**
   * Create and inject skip link
   * @param {HTMLElement} container - Target container (usually body)
   */
  create(container = document.body) {
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.textContent = 'メインコンテンツに移動';
    skipLink.className = 'skip-link';
    skipLink.setAttribute('aria-label', 'メインコンテンツに移動');

    container.insertBefore(skipLink, container.firstChild);

    return skipLink;
  },
};

/**
 * Color contrast checker
 */
export const ContrastChecker = {
  /**
   * Calculate relative luminance
   * @param {string} hex - Hex color
   * @returns {number} - Luminance value
   */
  getLuminance(hex) {
    const rgb = parseInt(hex.slice(1), 16);
    const r = (rgb >> 16) & 0xff;
    const g = (rgb >> 8) & 0xff;
    const b = (rgb >> 0) & 0xff;

    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance;
  },

  /**
   * Calculate contrast ratio
   * @param {string} foreground - Foreground color (hex)
   * @param {string} background - Background color (hex)
   * @returns {number} - Contrast ratio
   */
  getContrastRatio(foreground, background) {
    const l1 = this.getLuminance(foreground);
    const l2 = this.getLuminance(background);

    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);

    return (lighter + 0.05) / (darker + 0.05);
  },

  /**
   * Check WCAG AA compliance
   * @param {number} ratio - Contrast ratio
   * @param {string} level - 'AA' or 'AAA'
   * @returns {boolean} - Is compliant
   */
  isCompliant(ratio, level = 'AA') {
    if (level === 'AAA') {
      return ratio >= 7;
    }
    return ratio >= 4.5;
  },

  /**
   * Verify all text elements on page
   * @returns {Array} - List of non-compliant elements
   */
  verifyPage() {
    const results = [];
    const textElements = document.querySelectorAll('p, span, button, a, h1, h2, h3, h4, h5, h6');

    textElements.forEach((element) => {
      const computedStyle = window.getComputedStyle(element);
      const color = computedStyle.color;
      const backgroundColor = computedStyle.backgroundColor;

      // Parse RGB to hex
      const rgbToHex = (rgb) => {
        const matches = rgb.match(/\d+/g);
        if (!matches || matches.length < 3) return '#ffffff';
        return `#${matches.slice(0, 3).map((x) => {
          const hex = parseInt(x).toString(16);
          return hex.length === 1 ? `0${hex}` : hex;
        }).join('')}`;
      };

      const fgHex = rgbToHex(color);
      const bgHex = rgbToHex(backgroundColor);

      const ratio = this.getContrastRatio(fgHex, bgHex);
      if (!this.isCompliant(ratio)) {
        results.push({
          element,
          ratio,
          foreground: fgHex,
          background: bgHex,
        });
      }
    });

    return results;
  },
};

/**
 * Reduced motion support
 */
export const ReducedMotion = {
  /**
   * Check if user prefers reduced motion
   * @returns {boolean} - User prefers reduced motion
   */
  prefersReduced() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  },

  /**
   * Apply reduced motion styles to element
   * @param {HTMLElement} element - Target element
   */
  applyToElement(element) {
    if (this.prefersReduced()) {
      element.style.transition = 'none';
      element.style.animation = 'none';
    }
  },

  /**
   * Disable animations globally if needed
   */
  disableAnimations() {
    if (!this.prefersReduced()) return;

    const style = document.createElement('style');
    style.textContent = `
      * {
        animation: none !important;
        transition: none !important;
      }
    `;
    document.head.appendChild(style);
  },

  /**
   * Watch for motion preference changes
   * @param {Function} callback - Callback when preference changes
   */
  watch(callback) {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    mediaQuery.addEventListener('change', (e) => {
      callback(e.matches);
    });
  },
};

/**
 * Page title announcer for SPAs
 */
export const PageTitle = {
  /**
   * Announce page change to screen readers
   * @param {string} pageTitle - New page title
   * @param {string} region - Region description
   */
  announce(pageTitle, region = 'main') {
    document.title = pageTitle;

    // Create announcement element
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = `ページ読み込み完了: ${pageTitle}。${region} 領域`;

    document.body.appendChild(announcement);

    setTimeout(() => {
      announcement.remove();
    }, 1000);
  },
};

export default {
  FocusManager,
  AriaManager,
  KeyboardNav,
  ScreenReaderOnly,
  SkipLink,
  ContrastChecker,
  ReducedMotion,
  PageTitle,
};
