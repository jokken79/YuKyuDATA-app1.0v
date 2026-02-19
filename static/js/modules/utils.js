/**
 * YuKyu Security & Utility Module
 * Handles XSS prevention, formatting, and common helpers.
 */

export function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}

export function escapeAttr(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/'/g, '&#39;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

export function safeNumber(val, defaultVal = 0) {
  const num = parseFloat(val);
  return Number.isFinite(num) ? num : defaultVal;
}

export function isValidYear(year) {
  const num = Number(year);
  return Number.isInteger(num) && num >= 2000 && num <= 2100;
}

export function isValidString(value) {
  if (value === null || value === undefined) return false;
  return String(value).trim().length > 0;
}

export function formatNumber(value, decimals = 0) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '0';
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

export function debounce(func, wait) {
  let timeout;
  return function debounced(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function throttle(func, wait) {
  let lastCall = 0;
  let lastResult;
  return function throttled(...args) {
    const now = Date.now();
    if (now - lastCall >= wait) {
      lastCall = now;
      lastResult = func(...args);
    }
    return lastResult;
  };
}

export function rafThrottle(func) {
  let rafId = null;
  return function throttled(...args) {
    if (rafId !== null) return;
    rafId = requestAnimationFrame(() => {
      rafId = null;
      func(...args);
    });
  };
}

export function debounceImmediate(func, wait, immediate = false) {
  let timeout;
  return function debounced(...args) {
    const callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      timeout = null;
      if (!immediate) func(...args);
    }, wait);
    if (callNow) {
      func(...args);
    }
  };
}

export function createCancelableDebounce(func, wait) {
  let timeout;
  return {
    execute: (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        timeout = null;
        func(...args);
      }, wait);
    },
    cancel: () => {
      clearTimeout(timeout);
      timeout = null;
    },
    isPending: () => timeout !== null && timeout !== undefined
  };
}

export function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export function getAnimationDelay(delay) {
  return prefersReducedMotion() ? 0 : delay;
}

export const Utils = {
  escapeHtml,
  escapeAttr,
  safeNumber,
  isValidYear,
  isValidString,
  formatNumber,
  debounce,
  throttle,
  rafThrottle,
  debounceImmediate,
  createCancelableDebounce,
  prefersReducedMotion,
  getAnimationDelay
};

export default Utils;
