/**
 * Accessibility Module - WCAG 2.1 AA Compliance Utilities
 * Provides focus trap, ARIA live regions, and keyboard navigation
 * @module accessibility
 */

/**
 * Focus Trap Manager - Traps focus within a modal/dialog
 * Implements WCAG 2.4.3 Focus Order
 */
export class FocusTrap {
    constructor(container) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;
        this.previouslyFocused = null;
        this.isActive = false;
        this._handleKeyDown = this._handleKeyDown.bind(this);
        this._handleFocusOut = this._handleFocusOut.bind(this);
    }

    /**
     * Get all focusable elements within the container
     * @returns {HTMLElement[]} Array of focusable elements
     */
    getFocusableElements() {
        const selector = [
            'a[href]:not([disabled])',
            'button:not([disabled])',
            'textarea:not([disabled])',
            'input:not([disabled]):not([type="hidden"])',
            'select:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]'
        ].join(',');

        return Array.from(this.container.querySelectorAll(selector))
            .filter(el => {
                // Check if element is visible
                const style = window.getComputedStyle(el);
                return style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       el.offsetParent !== null;
            });
    }

    /**
     * Activate the focus trap
     */
    activate() {
        if (this.isActive || !this.container) return;

        // Store currently focused element
        this.previouslyFocused = document.activeElement;
        this.isActive = true;

        // Add event listeners
        document.addEventListener('keydown', this._handleKeyDown);
        this.container.addEventListener('focusout', this._handleFocusOut);

        // Set ARIA attributes
        this.container.setAttribute('aria-modal', 'true');
        this.container.setAttribute('role', 'dialog');

        // Focus first focusable element or container
        requestAnimationFrame(() => {
            const focusable = this.getFocusableElements();
            if (focusable.length > 0) {
                focusable[0].focus();
            } else {
                // Make container focusable if no elements
                this.container.setAttribute('tabindex', '-1');
                this.container.focus();
            }
        });
    }

    /**
     * Deactivate the focus trap
     */
    deactivate() {
        if (!this.isActive) return;

        this.isActive = false;

        // Remove event listeners
        document.removeEventListener('keydown', this._handleKeyDown);
        this.container.removeEventListener('focusout', this._handleFocusOut);

        // Remove ARIA attributes
        this.container.removeAttribute('aria-modal');

        // Restore focus to previously focused element
        if (this.previouslyFocused && typeof this.previouslyFocused.focus === 'function') {
            this.previouslyFocused.focus();
        }
    }

    /**
     * Handle keydown events for Tab and Escape
     * @param {KeyboardEvent} event
     * @private
     */
    _handleKeyDown(event) {
        if (!this.isActive) return;

        if (event.key === 'Escape') {
            // Dispatch custom event for modal close
            this.container.dispatchEvent(new CustomEvent('focustrap:escape', {
                bubbles: true
            }));
            return;
        }

        if (event.key !== 'Tab') return;

        const focusable = this.getFocusableElements();
        if (focusable.length === 0) return;

        const firstElement = focusable[0];
        const lastElement = focusable[focusable.length - 1];
        const activeElement = document.activeElement;

        // Shift+Tab from first element -> go to last
        if (event.shiftKey && activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
        }
        // Tab from last element -> go to first
        else if (!event.shiftKey && activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
        }
    }

    /**
     * Handle focus leaving the container
     * @param {FocusEvent} event
     * @private
     */
    _handleFocusOut(event) {
        if (!this.isActive) return;

        // Check if focus is moving outside the container
        requestAnimationFrame(() => {
            if (!this.container.contains(document.activeElement)) {
                const focusable = this.getFocusableElements();
                if (focusable.length > 0) {
                    focusable[0].focus();
                }
            }
        });
    }
}

/**
 * ARIA Live Region Manager
 * Implements WCAG 4.1.3 Status Messages
 */
export class LiveRegion {
    constructor(options = {}) {
        this.politeness = options.politeness || 'polite'; // 'polite', 'assertive', or 'off'
        this.atomic = options.atomic !== false;
        this.relevant = options.relevant || 'additions text';
        this.element = this._createRegion();
    }

    /**
     * Create the live region element
     * @private
     */
    _createRegion() {
        // Check if region already exists
        let region = document.getElementById('a11y-live-region-' + this.politeness);

        if (!region) {
            region = document.createElement('div');
            region.id = 'a11y-live-region-' + this.politeness;
            region.setAttribute('role', 'status');
            region.setAttribute('aria-live', this.politeness);
            region.setAttribute('aria-atomic', this.atomic.toString());
            region.setAttribute('aria-relevant', this.relevant);

            // Visually hidden but accessible to screen readers
            Object.assign(region.style, {
                position: 'absolute',
                width: '1px',
                height: '1px',
                padding: '0',
                margin: '-1px',
                overflow: 'hidden',
                clip: 'rect(0, 0, 0, 0)',
                whiteSpace: 'nowrap',
                border: '0'
            });

            document.body.appendChild(region);
        }

        return region;
    }

    /**
     * Announce a message to screen readers
     * @param {string} message - The message to announce
     */
    announce(message) {
        if (!message) return;

        // Clear existing content
        this.element.textContent = '';

        // Use timeout to ensure screen readers detect the change
        setTimeout(() => {
            this.element.textContent = message;
        }, 100);
    }

    /**
     * Clear the live region
     */
    clear() {
        this.element.textContent = '';
    }
}

/**
 * Singleton instances for global use
 */
export const liveRegionPolite = new LiveRegion({ politeness: 'polite' });
export const liveRegionAssertive = new LiveRegion({ politeness: 'assertive' });

/**
 * Announce a message politely (doesn't interrupt)
 * @param {string} message
 */
export function announcePolite(message) {
    liveRegionPolite.announce(message);
}

/**
 * Announce a message assertively (interrupts current speech)
 * @param {string} message
 */
export function announceAssertive(message) {
    liveRegionAssertive.announce(message);
}

/**
 * Add scope attributes to table headers
 * Implements WCAG 1.3.1 Info and Relationships
 * @param {HTMLTableElement|string} table - Table element or selector
 */
export function addTableScopes(table) {
    const tableEl = typeof table === 'string'
        ? document.querySelector(table)
        : table;

    if (!tableEl) return;

    // Add scope="col" to th elements in thead
    const theadHeaders = tableEl.querySelectorAll('thead th');
    theadHeaders.forEach(th => {
        if (!th.hasAttribute('scope')) {
            th.setAttribute('scope', 'col');
        }
    });

    // Add scope="row" to first th in each tbody tr
    const tbodyRows = tableEl.querySelectorAll('tbody tr');
    tbodyRows.forEach(tr => {
        const firstTh = tr.querySelector('th:first-child');
        if (firstTh && !firstTh.hasAttribute('scope')) {
            firstTh.setAttribute('scope', 'row');
        }
    });
}

/**
 * Initialize accessibility for all tables on the page
 */
export function initTableAccessibility() {
    document.querySelectorAll('table').forEach(addTableScopes);
}

/**
 * Check color contrast ratio
 * @param {string} foreground - Foreground color (hex or rgb)
 * @param {string} background - Background color (hex or rgb)
 * @returns {number} Contrast ratio
 */
export function getContrastRatio(foreground, background) {
    const getLuminance = (color) => {
        // Convert color to RGB values
        let r, g, b;

        if (color.startsWith('#')) {
            const hex = color.slice(1);
            r = parseInt(hex.substr(0, 2), 16) / 255;
            g = parseInt(hex.substr(2, 2), 16) / 255;
            b = parseInt(hex.substr(4, 2), 16) / 255;
        } else if (color.startsWith('rgb')) {
            const matches = color.match(/\d+/g);
            [r, g, b] = matches.map(n => parseInt(n) / 255);
        } else {
            return 0;
        }

        // Apply gamma correction
        const adjust = (c) => c <= 0.03928
            ? c / 12.92
            : Math.pow((c + 0.055) / 1.055, 2.4);

        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b);
    };

    const l1 = getLuminance(foreground);
    const l2 = getLuminance(background);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);

    return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check if contrast meets WCAG AA requirements
 * @param {number} ratio - Contrast ratio
 * @param {boolean} isLargeText - Whether text is large (18pt+ or 14pt+ bold)
 * @returns {boolean}
 */
export function meetsContrastAA(ratio, isLargeText = false) {
    return isLargeText ? ratio >= 3 : ratio >= 4.5;
}

/**
 * Modal accessibility helper
 * Combines focus trap with proper ARIA setup
 */
export class AccessibleModal {
    constructor(modalElement, options = {}) {
        this.modal = typeof modalElement === 'string'
            ? document.querySelector(modalElement)
            : modalElement;

        this.options = {
            closeOnEscape: true,
            closeOnBackdrop: true,
            labelledBy: options.labelledBy || null,
            describedBy: options.describedBy || null,
            onClose: options.onClose || null,
            ...options
        };

        this.focusTrap = new FocusTrap(this.modal);
        this._setupListeners();
    }

    _setupListeners() {
        // Handle escape key via focus trap event
        this.modal.addEventListener('focustrap:escape', () => {
            if (this.options.closeOnEscape) {
                this.close();
            }
        });

        // Handle backdrop click
        if (this.options.closeOnBackdrop) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.close();
                }
            });
        }
    }

    /**
     * Open the modal
     */
    open() {
        // Set ARIA attributes
        if (this.options.labelledBy) {
            this.modal.setAttribute('aria-labelledby', this.options.labelledBy);
        }
        if (this.options.describedBy) {
            this.modal.setAttribute('aria-describedby', this.options.describedBy);
        }

        // Show modal
        this.modal.classList.add('active');
        this.modal.setAttribute('aria-hidden', 'false');

        // Prevent body scroll
        document.body.style.overflow = 'hidden';

        // Activate focus trap
        this.focusTrap.activate();

        // Announce to screen readers
        announcePolite('ダイアログが開きました');
    }

    /**
     * Close the modal
     */
    close() {
        // Deactivate focus trap (restores previous focus)
        this.focusTrap.deactivate();

        // Hide modal
        this.modal.classList.remove('active');
        this.modal.setAttribute('aria-hidden', 'true');

        // Restore body scroll
        document.body.style.overflow = '';

        // Announce to screen readers
        announcePolite('ダイアログが閉じました');

        // Call onClose callback
        if (typeof this.options.onClose === 'function') {
            this.options.onClose();
        }
    }
}

/**
 * Initialize accessibility features globally
 */
export function initAccessibility() {
    // Add table scopes
    initTableAccessibility();

    // Create live regions
    liveRegionPolite;
    liveRegionAssertive;

    // Add keyboard navigation hints
    document.addEventListener('keydown', (e) => {
        // Show focus indicator when using keyboard
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });

    document.addEventListener('mousedown', () => {
        document.body.classList.remove('keyboard-navigation');
    });
}

export default {
    FocusTrap,
    LiveRegion,
    AccessibleModal,
    announcePolite,
    announceAssertive,
    addTableScopes,
    initTableAccessibility,
    getContrastRatio,
    meetsContrastAA,
    initAccessibility
};
