/**
 * UI Enhancements Module - Sprint 1, 2 & 3 Improvements
 *
 * Features:
 * - Form Validation System (HTML5 + real-time JS)
 * - Loading States & Spinners
 * - Confirmation Dialogs for destructive actions
 * - Focus Trap for modals
 * - Tooltip System
 * - Progress Indicators
 *
 * @module ui-enhancements
 * @version 2.7
 */

import { escapeHtml } from './utils.js';

// ============================================
// SPRINT 1: FORM VALIDATION SYSTEM
// ============================================

/**
 * FormValidator - Comprehensive form validation with real-time feedback
 */
export class FormValidator {
    constructor(formElement, options = {}) {
        this.form = typeof formElement === 'string'
            ? document.querySelector(formElement)
            : formElement;

        if (!this.form) {
            console.error('FormValidator: Form element not found');
            return;
        }

        this.options = {
            validateOnBlur: true,
            validateOnInput: true,
            showSuccessState: true,
            scrollToError: true,
            customValidators: {},
            messages: {
                required: 'Este campo es obligatorio',
                email: 'Ingrese un email válido',
                minlength: 'Mínimo {min} caracteres',
                maxlength: 'Máximo {max} caracteres',
                pattern: 'Formato inválido',
                min: 'Valor mínimo: {min}',
                max: 'Valor máximo: {max}',
                number: 'Ingrese un número válido',
                date: 'Ingrese una fecha válida',
                match: 'Los campos no coinciden'
            },
            ...options
        };

        this.errors = new Map();
        this.init();
    }

    init() {
        // Add novalidate to use custom validation
        this.form.setAttribute('novalidate', 'true');

        // Setup field listeners
        const fields = this.form.querySelectorAll('input, textarea, select');
        fields.forEach(field => {
            if (this.options.validateOnBlur) {
                field.addEventListener('blur', () => this.validateField(field));
            }
            if (this.options.validateOnInput) {
                field.addEventListener('input', () => {
                    // Debounce input validation
                    clearTimeout(field._validationTimeout);
                    field._validationTimeout = setTimeout(() => {
                        this.validateField(field);
                    }, 300);
                });
            }
        });

        // Setup form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    /**
     * Validate a single field
     */
    validateField(field) {
        const errors = [];
        const value = field.value.trim();
        const fieldName = field.getAttribute('data-label') || field.name || field.id;

        // Required validation
        if (field.hasAttribute('required') && !value) {
            errors.push(this.options.messages.required);
        }

        // Only continue if there's a value
        if (value) {
            // Email validation
            if (field.type === 'email') {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(value)) {
                    errors.push(this.options.messages.email);
                }
            }

            // Min length
            if (field.hasAttribute('minlength')) {
                const minLen = parseInt(field.getAttribute('minlength'));
                if (value.length < minLen) {
                    errors.push(this.options.messages.minlength.replace('{min}', minLen));
                }
            }

            // Max length
            if (field.hasAttribute('maxlength')) {
                const maxLen = parseInt(field.getAttribute('maxlength'));
                if (value.length > maxLen) {
                    errors.push(this.options.messages.maxlength.replace('{max}', maxLen));
                }
            }

            // Pattern validation
            if (field.hasAttribute('pattern')) {
                const pattern = new RegExp(field.getAttribute('pattern'));
                if (!pattern.test(value)) {
                    const customMsg = field.getAttribute('data-pattern-message');
                    errors.push(customMsg || this.options.messages.pattern);
                }
            }

            // Number validation
            if (field.type === 'number') {
                const num = parseFloat(value);
                if (isNaN(num)) {
                    errors.push(this.options.messages.number);
                } else {
                    if (field.hasAttribute('min')) {
                        const min = parseFloat(field.getAttribute('min'));
                        if (num < min) {
                            errors.push(this.options.messages.min.replace('{min}', min));
                        }
                    }
                    if (field.hasAttribute('max')) {
                        const max = parseFloat(field.getAttribute('max'));
                        if (num > max) {
                            errors.push(this.options.messages.max.replace('{max}', max));
                        }
                    }
                }
            }

            // Date validation
            if (field.type === 'date') {
                const date = new Date(value);
                if (isNaN(date.getTime())) {
                    errors.push(this.options.messages.date);
                }
            }

            // Match validation (for password confirmation)
            if (field.hasAttribute('data-match')) {
                const matchField = this.form.querySelector(field.getAttribute('data-match'));
                if (matchField && value !== matchField.value) {
                    errors.push(this.options.messages.match);
                }
            }

            // Custom validators
            const customValidator = field.getAttribute('data-validator');
            if (customValidator && this.options.customValidators[customValidator]) {
                const customError = this.options.customValidators[customValidator](value, field);
                if (customError) {
                    errors.push(customError);
                }
            }
        }

        // Update UI
        this.displayFieldState(field, errors);
        this.errors.set(field.name || field.id, errors);

        return errors.length === 0;
    }

    /**
     * Display field validation state
     */
    displayFieldState(field, errors) {
        const container = field.closest('.form-group') || field.parentElement;
        let errorElement = container.querySelector('.field-error');

        // Create error element if doesn't exist
        if (!errorElement) {
            errorElement = document.createElement('span');
            errorElement.className = 'field-error';
            errorElement.setAttribute('role', 'alert');
            errorElement.setAttribute('aria-live', 'polite');
            container.appendChild(errorElement);
        }

        if (errors.length > 0) {
            // Invalid state
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
            field.setAttribute('aria-invalid', 'true');
            errorElement.textContent = errors[0];
            errorElement.classList.add('visible');
        } else if (field.value.trim() && this.options.showSuccessState) {
            // Valid state
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
            field.setAttribute('aria-invalid', 'false');
            errorElement.textContent = '';
            errorElement.classList.remove('visible');
        } else {
            // Neutral state
            field.classList.remove('is-invalid', 'is-valid');
            field.removeAttribute('aria-invalid');
            errorElement.textContent = '';
            errorElement.classList.remove('visible');
        }
    }

    /**
     * Validate entire form
     */
    validate() {
        let isValid = true;
        const fields = this.form.querySelectorAll('input, textarea, select');

        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        // Scroll to first error
        if (!isValid && this.options.scrollToError) {
            const firstError = this.form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        }

        return isValid;
    }

    /**
     * Handle form submission
     */
    handleSubmit(e) {
        if (!this.validate()) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
        // Let form submit naturally or handle via onSubmit callback
        if (this.options.onSubmit) {
            e.preventDefault();
            this.options.onSubmit(new FormData(this.form), this.form);
        }
    }

    /**
     * Reset form validation state
     */
    reset() {
        this.errors.clear();
        const fields = this.form.querySelectorAll('input, textarea, select');
        fields.forEach(field => {
            field.classList.remove('is-invalid', 'is-valid');
            field.removeAttribute('aria-invalid');
        });
        const errorElements = this.form.querySelectorAll('.field-error');
        errorElements.forEach(el => {
            el.textContent = '';
            el.classList.remove('visible');
        });
    }
}


// ============================================
// SPRINT 1: LOADING STATES & SPINNERS
// ============================================

/**
 * LoadingState - Manages loading states for buttons and elements
 */
export class LoadingState {
    /**
     * Set element to loading state
     * @param {HTMLElement|string} element - Element or selector
     * @param {string} loadingText - Optional text while loading
     */
    static start(element, loadingText = null) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el) return;

        // Store original state
        el._originalText = el.innerHTML;
        el._originalDisabled = el.disabled;

        // Apply loading state
        el.classList.add('is-loading');
        el.setAttribute('aria-busy', 'true');
        el.disabled = true;

        if (loadingText) {
            el.innerHTML = `<span class="spinner"></span> ${escapeHtml(loadingText)}`;
        } else {
            // Preserve text but add spinner
            const text = el.textContent.trim();
            el.innerHTML = `<span class="spinner"></span> ${escapeHtml(text)}`;
        }
    }

    /**
     * Remove loading state from element
     * @param {HTMLElement|string} element - Element or selector
     * @param {string} successText - Optional success text (shows briefly)
     */
    static stop(element, successText = null) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el) return;

        el.classList.remove('is-loading');
        el.setAttribute('aria-busy', 'false');
        el.disabled = el._originalDisabled || false;

        if (successText) {
            el.classList.add('is-success');
            el.innerHTML = `<span class="icon-success"></span> ${escapeHtml(successText)}`;

            setTimeout(() => {
                el.classList.remove('is-success');
                el.innerHTML = el._originalText || el.textContent;
            }, 2000);
        } else {
            el.innerHTML = el._originalText || el.textContent;
        }
    }

    /**
     * Set error state
     * @param {HTMLElement|string} element - Element or selector
     * @param {string} errorText - Error text to display
     */
    static error(element, errorText = 'Error') {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el) return;

        el.classList.remove('is-loading');
        el.classList.add('is-error');
        el.setAttribute('aria-busy', 'false');
        el.disabled = el._originalDisabled || false;
        el.innerHTML = `<span class="icon-error"></span> ${escapeHtml(errorText)}`;

        setTimeout(() => {
            el.classList.remove('is-error');
            el.innerHTML = el._originalText || el.textContent;
        }, 3000);
    }

    /**
     * Wrap an async function with loading state
     * @param {HTMLElement|string} element - Button/element to show loading on
     * @param {Function} asyncFn - Async function to execute
     * @param {Object} options - Options (loadingText, successText, errorText)
     */
    static async wrap(element, asyncFn, options = {}) {
        const {
            loadingText = 'Procesando...',
            successText = null,
            errorText = 'Error'
        } = options;

        LoadingState.start(element, loadingText);

        try {
            const result = await asyncFn();
            LoadingState.stop(element, successText);
            return result;
        } catch (error) {
            LoadingState.error(element, errorText);
            throw error;
        }
    }
}


// ============================================
// SPRINT 1: CONFIRMATION DIALOGS
// ============================================

/**
 * ConfirmDialog - Accessible confirmation dialogs for destructive actions
 */
export class ConfirmDialog {
    /**
     * Show a confirmation dialog
     * @param {Object} options - Dialog options
     * @returns {Promise<boolean>} - User's choice
     */
    static async confirm(options = {}) {
        const {
            title = '確認 / Confirmar',
            message = 'この操作を実行しますか？ / ¿Desea continuar?',
            confirmText = '確認 / Confirmar',
            cancelText = 'キャンセル / Cancelar',
            type = 'warning', // 'warning', 'danger', 'info'
            icon = null
        } = options;

        return new Promise((resolve) => {
            // Create dialog element
            const dialog = document.createElement('dialog');
            dialog.className = `confirm-dialog confirm-dialog--${type}`;
            dialog.setAttribute('aria-labelledby', 'confirm-dialog-title');
            dialog.setAttribute('aria-describedby', 'confirm-dialog-message');
            dialog.setAttribute('role', 'alertdialog');

            // Icon based on type
            const iconMap = {
                warning: '⚠️',
                danger: '🗑️',
                info: 'ℹ️'
            };
            const displayIcon = icon || iconMap[type] || '❓';

            dialog.innerHTML = `
                <div class="confirm-dialog__content">
                    <div class="confirm-dialog__icon">${displayIcon}</div>
                    <h2 id="confirm-dialog-title" class="confirm-dialog__title">${escapeHtml(title)}</h2>
                    <p id="confirm-dialog-message" class="confirm-dialog__message">${escapeHtml(message)}</p>
                    <div class="confirm-dialog__actions">
                        <button type="button" class="btn btn-glass" data-action="cancel">
                            ${escapeHtml(cancelText)}
                        </button>
                        <button type="button" class="btn btn-${type === 'danger' ? 'danger' : 'primary'}" data-action="confirm">
                            ${escapeHtml(confirmText)}
                        </button>
                    </div>
                </div>
            `;

            // Event handlers
            const closeDialog = (result) => {
                dialog.close();
                document.body.removeChild(dialog);
                resolve(result);
            };

            dialog.querySelector('[data-action="cancel"]').addEventListener('click', () => closeDialog(false));
            dialog.querySelector('[data-action="confirm"]').addEventListener('click', () => closeDialog(true));

            // Close on Escape
            dialog.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    closeDialog(false);
                }
            });

            // Close on backdrop click
            dialog.addEventListener('click', (e) => {
                if (e.target === dialog) {
                    closeDialog(false);
                }
            });

            // Show dialog
            document.body.appendChild(dialog);
            dialog.showModal();

            // Focus confirm button
            dialog.querySelector('[data-action="confirm"]').focus();
        });
    }

    /**
     * Shorthand for danger confirmation
     */
    static async confirmDelete(itemName = 'este elemento') {
        return this.confirm({
            title: '削除確認 / Confirmar eliminación',
            message: `¿Está seguro de eliminar ${itemName}? Esta acción no se puede deshacer.`,
            confirmText: '削除 / Eliminar',
            cancelText: 'キャンセル / Cancelar',
            type: 'danger'
        });
    }

    /**
     * Shorthand for reset confirmation
     */
    static async confirmReset(dataType = 'todos los datos') {
        return this.confirm({
            title: 'リセット確認 / Confirmar reinicio',
            message: `¿Está seguro de reiniciar ${dataType}? Todos los registros serán eliminados.`,
            confirmText: 'リセット / Reiniciar',
            cancelText: 'キャンセル / Cancelar',
            type: 'danger',
            icon: '🔄'
        });
    }
}


// ============================================
// SPRINT 2: FOCUS TRAP FOR MODALS
// ============================================

/**
 * FocusTrap - Traps focus within a container (for modals/dialogs)
 */
export class FocusTrap {
    constructor(container) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;
        this.previousFocus = null;
        this.boundHandleKeydown = this.handleKeydown.bind(this);
    }

    /**
     * Get all focusable elements within container
     */
    getFocusableElements() {
        return this.container.querySelectorAll(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), ' +
            'textarea:not([disabled]), [tabindex]:not([tabindex="-1"]), [contenteditable]'
        );
    }

    /**
     * Activate the focus trap
     */
    activate() {
        this.previousFocus = document.activeElement;

        const focusable = this.getFocusableElements();
        if (focusable.length > 0) {
            focusable[0].focus();
        }

        document.addEventListener('keydown', this.boundHandleKeydown);
    }

    /**
     * Deactivate the focus trap
     */
    deactivate() {
        document.removeEventListener('keydown', this.boundHandleKeydown);

        if (this.previousFocus && this.previousFocus.focus) {
            this.previousFocus.focus();
        }
    }

    /**
     * Handle Tab key to trap focus
     */
    handleKeydown(e) {
        if (e.key !== 'Tab') return;

        const focusable = this.getFocusableElements();
        if (focusable.length === 0) return;

        const firstFocusable = focusable[0];
        const lastFocusable = focusable[focusable.length - 1];

        if (e.shiftKey) {
            // Shift+Tab: go to last if on first
            if (document.activeElement === firstFocusable) {
                e.preventDefault();
                lastFocusable.focus();
            }
        } else {
            // Tab: go to first if on last
            if (document.activeElement === lastFocusable) {
                e.preventDefault();
                firstFocusable.focus();
            }
        }
    }
}


// ============================================
// SPRINT 3: TOOLTIP SYSTEM
// ============================================

/**
 * Tooltip - Accessible tooltip system
 */
export class Tooltip {
    static initialized = false;
    static activeTooltip = null;

    /**
     * Initialize tooltip system (call once on page load)
     */
    static init() {
        if (Tooltip.initialized) return;

        // Create tooltip container
        const tooltipEl = document.createElement('div');
        tooltipEl.id = 'tooltip-container';
        tooltipEl.className = 'tooltip';
        tooltipEl.setAttribute('role', 'tooltip');
        tooltipEl.setAttribute('aria-hidden', 'true');
        document.body.appendChild(tooltipEl);

        // Event delegation for elements with data-tooltip
        document.addEventListener('mouseenter', (e) => {
            if (!e.target || typeof e.target.closest !== 'function') return;
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                Tooltip.show(target);
            }
        }, true);

        document.addEventListener('mouseleave', (e) => {
            if (!e.target || typeof e.target.closest !== 'function') return;
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                Tooltip.hide();
            }
        }, true);

        // Also handle focus for accessibility
        document.addEventListener('focusin', (e) => {
            if (!e.target || typeof e.target.closest !== 'function') return;
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                Tooltip.show(target);
            }
        });

        document.addEventListener('focusout', (e) => {
            if (!e.target || typeof e.target.closest !== 'function') return;
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                Tooltip.hide();
            }
        });

        Tooltip.initialized = true;
    }

    /**
     * Show tooltip for an element
     */
    static show(element) {
        const tooltipEl = document.getElementById('tooltip-container');
        if (!tooltipEl) return;

        const text = element.getAttribute('data-tooltip');
        if (!text) return;

        tooltipEl.textContent = text;
        tooltipEl.setAttribute('aria-hidden', 'false');
        tooltipEl.classList.add('visible');

        // Position tooltip
        const rect = element.getBoundingClientRect();
        const position = element.getAttribute('data-tooltip-position') || 'top';

        const tooltipRect = tooltipEl.getBoundingClientRect();
        let top, left;

        switch (position) {
            case 'bottom':
                top = rect.bottom + 8;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'left':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.left - tooltipRect.width - 8;
                break;
            case 'right':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.right + 8;
                break;
            default: // top
                top = rect.top - tooltipRect.height - 8;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
        }

        // Keep within viewport
        left = Math.max(8, Math.min(left, window.innerWidth - tooltipRect.width - 8));
        top = Math.max(8, top);

        tooltipEl.style.top = `${top}px`;
        tooltipEl.style.left = `${left}px`;
        tooltipEl.setAttribute('data-position', position);

        // Link tooltip to element for accessibility
        const tooltipId = 'tooltip-' + Date.now();
        tooltipEl.id = tooltipId;
        element.setAttribute('aria-describedby', tooltipId);

        Tooltip.activeTooltip = element;
    }

    /**
     * Hide tooltip
     */
    static hide() {
        const tooltipEl = document.getElementById('tooltip-container');
        if (!tooltipEl) return;

        tooltipEl.classList.remove('visible');
        tooltipEl.setAttribute('aria-hidden', 'true');

        if (Tooltip.activeTooltip) {
            Tooltip.activeTooltip.removeAttribute('aria-describedby');
            Tooltip.activeTooltip = null;
        }
    }

    /**
     * Manually add tooltip to an element
     */
    static attach(element, text, position = 'top') {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el) return;

        el.setAttribute('data-tooltip', text);
        el.setAttribute('data-tooltip-position', position);
    }
}


// ============================================
// SPRINT 3: PROGRESS INDICATORS
// ============================================

/**
 * ProgressIndicator - Visual progress feedback for long operations
 */
export class ProgressIndicator {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        this.options = {
            showPercentage: true,
            showText: true,
            animated: true,
            ...options
        };

        this.progress = 0;
        this.text = '';
        this.element = null;
        this.init();
    }

    init() {
        this.element = document.createElement('div');
        this.element.className = 'progress-indicator';
        this.element.setAttribute('role', 'progressbar');
        this.element.setAttribute('aria-valuemin', '0');
        this.element.setAttribute('aria-valuemax', '100');
        this.element.setAttribute('aria-valuenow', '0');

        this.element.innerHTML = `
            <div class="progress-indicator__bar">
                <div class="progress-indicator__fill"></div>
            </div>
            ${this.options.showText ? '<div class="progress-indicator__text"></div>' : ''}
        `;

        this.fillElement = this.element.querySelector('.progress-indicator__fill');
        this.textElement = this.element.querySelector('.progress-indicator__text');
    }

    /**
     * Show the progress indicator
     */
    show() {
        if (this.container && !this.container.contains(this.element)) {
            this.container.appendChild(this.element);
        }
        this.element.classList.add('visible');
    }

    /**
     * Hide the progress indicator
     */
    hide() {
        this.element.classList.remove('visible');
        setTimeout(() => {
            if (this.element.parentNode) {
                this.element.parentNode.removeChild(this.element);
            }
        }, 300);
    }

    /**
     * Update progress
     * @param {number} value - Progress value (0-100)
     * @param {string} text - Status text
     */
    update(value, text = '') {
        this.progress = Math.max(0, Math.min(100, value));
        this.text = text;

        this.fillElement.style.width = `${this.progress}%`;
        this.element.setAttribute('aria-valuenow', this.progress);

        if (this.textElement) {
            const displayText = this.options.showPercentage
                ? `${Math.round(this.progress)}% ${text}`
                : text;
            this.textElement.textContent = displayText;
        }
    }

    /**
     * Set indeterminate state (unknown progress)
     */
    setIndeterminate(text = 'Procesando...') {
        this.element.classList.add('indeterminate');
        this.element.removeAttribute('aria-valuenow');
        if (this.textElement) {
            this.textElement.textContent = text;
        }
    }

    /**
     * Complete the progress with success state
     */
    complete(text = 'Completado') {
        this.update(100, text);
        this.element.classList.add('complete');
        setTimeout(() => this.hide(), 2000);
    }

    /**
     * Show error state
     */
    error(text = 'Error') {
        this.element.classList.add('error');
        if (this.textElement) {
            this.textElement.textContent = text;
        }
        setTimeout(() => this.hide(), 3000);
    }

    /**
     * Static method to create and show a quick progress
     */
    static async track(container, asyncGenerator, options = {}) {
        const indicator = new ProgressIndicator(container, options);
        indicator.show();

        try {
            for await (const { progress, text } of asyncGenerator) {
                indicator.update(progress, text);
            }
            indicator.complete(options.completeText || 'Completado');
        } catch (error) {
            indicator.error(options.errorText || 'Error: ' + error.message);
            throw error;
        }

        return indicator;
    }
}


// ============================================
// AUTO-INITIALIZE COMMON PATTERNS
// ============================================

/**
 * Initialize all UI enhancements
 */
export function initUIEnhancements() {
    // Initialize tooltip system
    Tooltip.init();

    // Auto-apply loading states to buttons with data-loading attribute
    document.querySelectorAll('[data-loading]').forEach(btn => {
        const originalClick = btn.onclick;
        btn.onclick = async function(e) {
            if (btn.classList.contains('is-loading')) return;

            const loadingText = btn.getAttribute('data-loading');
            LoadingState.start(btn, loadingText);

            try {
                if (originalClick) {
                    await originalClick.call(this, e);
                }
            } finally {
                LoadingState.stop(btn);
            }
        };
    });

    // Auto-apply confirmation to destructive buttons
    document.querySelectorAll('[data-confirm]').forEach(btn => {
        const originalClick = btn.onclick;
        btn.onclick = async function(e) {
            e.preventDefault();

            const confirmMessage = btn.getAttribute('data-confirm');
            const confirmType = btn.getAttribute('data-confirm-type') || 'warning';

            const confirmed = await ConfirmDialog.confirm({
                message: confirmMessage,
                type: confirmType
            });

            if (confirmed && originalClick) {
                originalClick.call(this, e);
            }
        };
    });

    // Auto-initialize form validators
    document.querySelectorAll('form[data-validate]').forEach(form => {
        new FormValidator(form);
    });

    // UI Enhancements initialized
}


// ============================================
// EXPORT DEFAULT
// ============================================

export default {
    FormValidator,
    LoadingState,
    ConfirmDialog,
    FocusTrap,
    Tooltip,
    ProgressIndicator,
    initUIEnhancements
};
