/**
 * YuKyu Security & Utility Module
 * Handles XSS prevention, formatting, and common helpers.
 */

export const Utils = {
    /**
     * Escapes HTML to prevent XSS attacks
     * @param {string} str - String to escape
     * @returns {string} Escaped string or safe HTML
     */
    escapeHtml(str) {
        if (str === null || str === undefined) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    },

    /**
     * Escapes attribute values
     */
    escapeAttr(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/'/g, '&#39;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    },

    /**
     * Safely creates a number from input
     */
    safeNumber(val, defaultVal = 0) {
        const num = parseFloat(val);
        return Number.isFinite(num) ? num : defaultVal;
    },

    /**
     * Validates year is within acceptable range
     */
    isValidYear(year) {
        const num = parseInt(year);
        return Number.isInteger(num) && num >= 2000 && num <= 2100;
    },

    /**
     * Debounce function for performance
     */
    debounce(func, wait) {
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
};
