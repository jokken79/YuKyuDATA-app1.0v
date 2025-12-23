/**
 * Sanitizer Module - XSS Prevention
 * Provides safe HTML escaping and DOM manipulation utilities
 *
 * SECURITY GUIDELINES:
 * - Use escapeHtml() for user input before displaying
 * - Use setTextContent() instead of innerHTML for plain text
 * - Use createElement() for safe DOM manipulation
 * - Only use setInnerHTML() with TRUSTED content (not user input)
 *
 * Usage:
 *   sanitizer.setTextContent(element, userInput);
 *   const link = sanitizer.createSafeLink('Click me', '/safe-url');
 *   const escaped = sanitizer.escapeHtml(userInput);
 */

const sanitizer = (() => {
  'use strict';

  /**
   * Escape HTML special characters to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped text safe for HTML
   */
  function escapeHtml(text) {
    if (!text) return '';

    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
      '/': '&#x2F;'
    };

    return String(text).replace(/[&<>"'\/]/g, char => map[char]);
  }

  /**
   * Escape HTML attribute values
   * @param {string} text - Attribute value
   * @returns {string} Safe attribute value
   */
  function escapeAttr(text) {
    if (!text) return '';
    return String(text).replace(/[&<>"']/g, char => {
      const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      };
      return map[char];
    });
  }

  /**
   * Safely set element text content (no HTML parsing)
   * @param {Element} element - DOM element
   * @param {string} text - Text to set
   */
  function setTextContent(element, text) {
    if (!element) return;
    if (typeof text !== 'string') {
      text = String(text || '');
    }
    element.textContent = text;
  }

  /**
   * Create a DOM element with safe attributes
   * @param {string} tag - HTML tag name
   * @param {Object} attributes - Element attributes
   * @param {string|Element|Array} content - Element content
   * @returns {Element} Created element
   */
  function createElement(tag, attributes = {}, content = '') {
    const element = document.createElement(tag);

    Object.entries(attributes).forEach(([key, value]) => {
      if (value === null || value === undefined) return;
      element.setAttribute(key, escapeAttr(String(value)));
    });

    if (content) {
      if (typeof content === 'string') {
        setTextContent(element, content);
      } else if (content instanceof Element) {
        element.appendChild(content);
      }
    }

    return element;
  }

  /**
   * Sanitize user input for display
   * @param {string} input - User input
   * @returns {string} Sanitized string
   */
  function sanitizeInput(input) {
    return escapeHtml(input);
  }

  /**
   * Create a safe toast/notification
   * @param {string} message - Message text
   * @param {string} type - Message type
   * @returns {Element} Toast element
   */
  function createSafeToast(message, type = 'info') {
    const toast = createElement('div', {
      class: `toast toast-${escapeAttr(type)}`,
      role: 'alert'
    });
    setTextContent(toast, message);
    return toast;
  }

  /**
   * Create a safe table cell
   * @param {string} text - Cell text
   * @param {boolean} isHeader - Is header cell
   * @returns {Element} TD or TH element
   */
  function createSafeTableCell(text, isHeader = false) {
    const tag = isHeader ? 'th' : 'td';
    const cell = createElement(tag);
    setTextContent(cell, text);
    return cell;
  }

  /**
   * Create a safe hyperlink
   * @param {string} text - Link text
   * @param {string} url - Link URL
   * @returns {Element} A element
   */
  function createSafeLink(text, url = '') {
    if (url && (url.startsWith('javascript:') || url.startsWith('data:'))) {
      url = '#';
    }
    const link = createElement('a', { href: url });
    setTextContent(link, text);
    return link;
  }

  return {
    escapeHtml,
    escapeAttr,
    setTextContent,
    createElement,
    sanitizeInput,
    createSafeToast,
    createSafeTableCell,
    createSafeLink
  };
})();
