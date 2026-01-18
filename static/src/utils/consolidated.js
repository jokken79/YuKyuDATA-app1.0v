/**
 * Consolidated Utilities
 * Merges utility functions from modules/utils.js, sanitizer.js, event-delegation.js
 * Single source of truth for common functions
 * @version 1.0.0
 */

/**
 * Escape HTML special characters
 * Prevents XSS attacks by escaping HTML entities
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
export function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return text.toString().replace(/[&<>"']/g, char => map[char]);
}

/**
 * Sanitize user input
 * Removes potentially dangerous content
 * @param {string} input - User input
 * @returns {string} Sanitized input
 */
export function sanitizeInput(input) {
    if (!input) return '';
    return input
        .replace(/[<>]/g, '')
        .replace(/javascript:/gi, '')
        .replace(/on\w+=/gi, '')
        .trim();
}

/**
 * Format date to Japanese format (YYYY年M月D日)
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date
 */
export function formatDateJA(date) {
    if (!date) return '-';

    const d = new Date(date);
    if (isNaN(d.getTime())) return '-';

    const year = d.getFullYear();
    const month = d.getMonth() + 1;
    const day = d.getDate();

    return `${year}年${month}月${day}日`;
}

/**
 * Format date to ISO format (YYYY-MM-DD)
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date
 */
export function formatDateISO(date) {
    if (!date) return '-';

    const d = new Date(date);
    if (isNaN(d.getTime())) return '-';

    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
}

/**
 * Parse date from string
 * Handles multiple formats
 * @param {string} dateStr - Date string
 * @returns {Date|null} Parsed date or null
 */
export function parseDate(dateStr) {
    if (!dateStr) return null;

    // Try ISO format (YYYY-MM-DD)
    const isoMatch = dateStr.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (isoMatch) {
        return new Date(isoMatch[1], parseInt(isoMatch[2]) - 1, isoMatch[3]);
    }

    // Try Japanese format (YYYY年M月D日)
    const jaMatch = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
    if (jaMatch) {
        return new Date(jaMatch[1], parseInt(jaMatch[2]) - 1, jaMatch[3]);
    }

    // Try standard Date parsing
    const parsed = new Date(dateStr);
    return isNaN(parsed.getTime()) ? null : parsed;
}

/**
 * Debounce a function
 * Delays function execution until user stops calling it
 * @param {Function} fn - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(fn, delay = 300) {
    let timeoutId = null;

    return function debounced(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            fn.apply(this, args);
        }, delay);
    };
}

/**
 * Throttle a function
 * Limits function execution frequency
 * @param {Function} fn - Function to throttle
 * @param {number} interval - Interval in milliseconds
 * @returns {Function} Throttled function
 */
export function throttle(fn, interval = 300) {
    let lastCall = 0;

    return function throttled(...args) {
        const now = Date.now();
        if (now - lastCall >= interval) {
            lastCall = now;
            fn.apply(this, args);
        }
    };
}

/**
 * Event delegation
 * Attach event listener to parent and filter by selector
 * @param {Element} element - Parent element
 * @param {string} eventType - Event type (click, change, etc)
 * @param {string} selector - CSS selector to match
 * @param {Function} handler - Event handler
 * @returns {Function} Cleanup function
 */
export function delegate(element, eventType, selector, handler) {
    const listener = (event) => {
        if (event.target.matches(selector)) {
            handler.call(event.target, event);
        }
    };

    element.addEventListener(eventType, listener);

    // Return cleanup function
    return () => {
        element.removeEventListener(eventType, listener);
    };
}

/**
 * Query DOM element(s)
 * Shorthand for querySelector/querySelectorAll
 * @param {string} selector - CSS selector
 * @param {Element} [context] - Search context (default: document)
 * @returns {Element|null} First matching element or null
 */
export function query(selector, context = document) {
    return context.querySelector(selector);
}

/**
 * Query multiple DOM elements
 * @param {string} selector - CSS selector
 * @param {Element} [context] - Search context (default: document)
 * @returns {NodeList} All matching elements
 */
export function queryAll(selector, context = document) {
    return context.querySelectorAll(selector);
}

/**
 * Create DOM element with optional classes and attributes
 * @param {string} tag - HTML tag name
 * @param {Object} [options] - Options object
 * @returns {Element} Created element
 */
export function createElement(tag, options = {}) {
    const el = document.createElement(tag);

    if (options.id) el.id = options.id;
    if (options.class) el.className = options.class;
    if (options.innerHTML) el.innerHTML = escapeHtml(options.innerHTML);
    if (options.textContent) el.textContent = options.textContent;

    if (options.attributes) {
        Object.entries(options.attributes).forEach(([key, value]) => {
            el.setAttribute(key, value);
        });
    }

    if (options.data) {
        Object.entries(options.data).forEach(([key, value]) => {
            el.dataset[key] = value;
        });
    }

    return el;
}

/**
 * Check if element is visible in viewport
 * @param {Element} el - Element to check
 * @returns {boolean} True if visible
 */
export function isInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Add class to element
 * @param {Element} el - Element
 * @param {string} className - Class name
 */
export function addClass(el, className) {
    if (el && className) {
        el.classList.add(...className.split(' '));
    }
}

/**
 * Remove class from element
 * @param {Element} el - Element
 * @param {string} className - Class name
 */
export function removeClass(el, className) {
    if (el && className) {
        el.classList.remove(...className.split(' '));
    }
}

/**
 * Toggle class on element
 * @param {Element} el - Element
 * @param {string} className - Class name
 * @returns {boolean} True if class was added
 */
export function toggleClass(el, className) {
    if (el && className) {
        return el.classList.toggle(className);
    }
    return false;
}

/**
 * Check if element has class
 * @param {Element} el - Element
 * @param {string} className - Class name
 * @returns {boolean} True if element has class
 */
export function hasClass(el, className) {
    return el && el.classList.contains(className);
}

/**
 * Get element attribute
 * @param {Element} el - Element
 * @param {string} attr - Attribute name
 * @returns {string|null} Attribute value
 */
export function getAttr(el, attr) {
    return el ? el.getAttribute(attr) : null;
}

/**
 * Set element attribute
 * @param {Element} el - Element
 * @param {string} attr - Attribute name
 * @param {string} value - Attribute value
 */
export function setAttr(el, attr, value) {
    if (el) {
        el.setAttribute(attr, value);
    }
}

/**
 * Get element data attribute
 * @param {Element} el - Element
 * @param {string} key - Data key
 * @returns {*} Data value
 */
export function getData(el, key) {
    return el ? el.dataset[key] : null;
}

/**
 * Set element data attribute
 * @param {Element} el - Element
 * @param {string} key - Data key
 * @param {*} value - Data value
 */
export function setData(el, key, value) {
    if (el) {
        el.dataset[key] = value;
    }
}

/**
 * Get element text
 * @param {Element} el - Element
 * @returns {string} Text content
 */
export function getText(el) {
    return el ? el.textContent : '';
}

/**
 * Set element text
 * @param {Element} el - Element
 * @param {string} text - Text content
 */
export function setText(el, text) {
    if (el) {
        el.textContent = text;
    }
}

/**
 * Get element HTML
 * @param {Element} el - Element
 * @returns {string} HTML content
 */
export function getHTML(el) {
    return el ? el.innerHTML : '';
}

/**
 * Set element HTML (with escaping)
 * @param {Element} el - Element
 * @param {string} html - HTML content
 */
export function setHTML(el, html) {
    if (el) {
        el.innerHTML = escapeHtml(html);
    }
}

/**
 * Sleep/delay execution
 * @param {number} ms - Milliseconds to delay
 * @returns {Promise} Resolves after delay
 */
export function sleep(ms = 0) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Clone object (shallow)
 * @param {Object} obj - Object to clone
 * @returns {Object} Cloned object
 */
export function cloneObject(obj) {
    return { ...obj };
}

/**
 * Merge objects
 * @param {...Object} objects - Objects to merge
 * @returns {Object} Merged object
 */
export function mergeObjects(...objects) {
    return Object.assign({}, ...objects);
}

/**
 * Get unique array values
 * @param {Array} arr - Input array
 * @returns {Array} Array with unique values
 */
export function unique(arr) {
    return [...new Set(arr)];
}

/**
 * Flatten nested array
 * @param {Array} arr - Input array
 * @returns {Array} Flattened array
 */
export function flatten(arr) {
    return arr.reduce((flat, item) => {
        return flat.concat(Array.isArray(item) ? flatten(item) : item);
    }, []);
}

/**
 * Group array by key function
 * @param {Array} arr - Input array
 * @param {Function} fn - Key function
 * @returns {Object} Grouped object
 */
export function groupBy(arr, fn) {
    return arr.reduce((acc, item) => {
        const key = fn(item);
        if (!acc[key]) acc[key] = [];
        acc[key].push(item);
        return acc;
    }, {});
}

/**
 * Get random array item
 * @param {Array} arr - Input array
 * @returns {*} Random item
 */
export function randomItem(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

/**
 * Capitalize string
 * @param {string} str - Input string
 * @returns {string} Capitalized string
 */
export function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Convert number to percentage
 * @param {number} value - Numeric value
 * @param {number} [total] - Total value (default: 100)
 * @param {number} [decimals] - Decimal places (default: 0)
 * @returns {string} Percentage string
 */
export function toPercentage(value, total = 100, decimals = 0) {
    const percent = (value / total) * 100;
    return percent.toFixed(decimals) + '%';
}

/**
 * Format number with separators
 * @param {number} num - Number to format
 * @param {number} [decimals] - Decimal places
 * @returns {string} Formatted number
 */
export function formatNumber(num, decimals = 0) {
    return parseFloat(num).toLocaleString('ja-JP', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

export default {
    escapeHtml,
    sanitizeInput,
    formatDateJA,
    formatDateISO,
    parseDate,
    debounce,
    throttle,
    delegate,
    query,
    queryAll,
    createElement,
    isInViewport,
    addClass,
    removeClass,
    toggleClass,
    hasClass,
    getAttr,
    setAttr,
    getData,
    setData,
    getText,
    setText,
    getHTML,
    setHTML,
    sleep,
    cloneObject,
    mergeObjects,
    unique,
    flatten,
    groupBy,
    randomItem,
    capitalize,
    toPercentage,
    formatNumber
};
