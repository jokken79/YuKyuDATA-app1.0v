/**
 * Utility Functions
 *
 * Common utility functions used across components.
 *
 * @version 1.0.0
 */

/**
 * Merge class names conditionally (like clsx + tailwind-merge)
 * For production, use 'clsx' and 'tailwind-merge' packages.
 *
 * @param {...(string|object|array)} inputs - Class names or conditions
 * @returns {string} Merged class names
 *
 * @example
 * cn('base-class', isActive && 'active-class', { 'conditional-class': condition })
 */
export function cn(...inputs) {
  const classes = [];

  for (const input of inputs) {
    if (!input) continue;

    if (typeof input === 'string') {
      classes.push(input);
    } else if (Array.isArray(input)) {
      classes.push(cn(...input));
    } else if (typeof input === 'object') {
      for (const [key, value] of Object.entries(input)) {
        if (value) classes.push(key);
      }
    }
  }

  return classes.join(' ');
}

/**
 * Format number as Japanese Yen
 *
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
export function formatYen(amount) {
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: 'JPY',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Format number with Japanese locale
 *
 * @param {number} num - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number string
 */
export function formatNumber(num, decimals = 0) {
  return new Intl.NumberFormat('ja-JP', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

/**
 * Format percentage
 *
 * @param {number} num - Number to format as percentage
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
export function formatPercent(num, decimals = 1) {
  return `${num.toFixed(decimals)}%`;
}

/**
 * Get color class based on profit margin
 *
 * @param {number} margin - Profit margin percentage
 * @returns {string} Tailwind text color class
 */
export function getProfitColor(margin) {
  if (margin >= 10) return 'text-emerald-500';
  if (margin >= 7) return 'text-green-500';
  if (margin >= 3) return 'text-amber-500';
  return 'text-red-500';
}

/**
 * Get background color class based on profit margin
 *
 * @param {number} margin - Profit margin percentage
 * @returns {string} Tailwind background/border color classes
 */
export function getProfitBgColor(margin) {
  if (margin >= 10) return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
  if (margin >= 7) return 'bg-green-500/10 text-green-500 border-green-500/20';
  if (margin >= 3) return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
  return 'bg-red-500/10 text-red-500 border-red-500/20';
}

/**
 * Delay utility for animations
 *
 * @param {number} ms - Milliseconds to delay
 * @returns {Promise<void>}
 */
export function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Generate unique ID
 *
 * @returns {string} Random ID string
 */
export function generateId() {
  return Math.random().toString(36).substring(2, 9);
}

/**
 * Debounce function
 *
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle function
 *
 * @param {Function} func - Function to throttle
 * @param {number} limit - Limit in milliseconds
 * @returns {Function} Throttled function
 */
export function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}
