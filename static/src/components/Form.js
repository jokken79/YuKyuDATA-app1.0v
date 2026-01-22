/**
 * Form Component - YuKyuDATA Design System
 * Dynamic form builder with validation and accessibility
 *
 * @module components/Form
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * Field definition
 * @typedef {Object} FieldDef
 * @property {string} name - Field name
 * @property {string} [type='text'] - Input type: text, number, email, tel, date, select, textarea, checkbox, radio
 * @property {string} label - Field label (Japanese)
 * @property {string} [placeholder] - Placeholder text
 * @property {*} [value] - Default value
 * @property {boolean} [required=false] - Required field
 * @property {boolean} [disabled=false] - Disabled field
 * @property {boolean} [readonly=false] - Read-only field
 * @property {Array} [options] - Options for select/radio (value, label)
 * @property {Object} [validation] - Validation rules
 * @property {string} [help] - Help text
 * @property {number} [min] - Minimum value (number/date)
 * @property {number} [max] - Maximum value (number/date)
 * @property {number} [step] - Step value (number)
 * @property {number} [minLength] - Minimum length
 * @property {number} [maxLength] - Maximum length
 * @property {string} [pattern] - Regex pattern
 * @property {string} [className] - Additional CSS classes
 * @property {number} [rows] - Textarea rows
 * @property {string} [autocomplete] - Autocomplete attribute
 */

/**
 * Form options
 * @typedef {Object} FormOptions
 * @property {FieldDef[]} fields - Field definitions
 * @property {Object} [values={}] - Initial values
 * @property {boolean} [validateOnChange=true] - Validate on input change
 * @property {boolean} [validateOnBlur=true] - Validate on field blur
 * @property {boolean} [showErrors=true] - Show error messages
 * @property {Function} [onSubmit] - Submit callback (values, form)
 * @property {Function} [onChange] - Change callback (name, value, values)
 * @property {string} [submitLabel='送信'] - Submit button label
 * @property {string} [cancelLabel='キャンセル'] - Cancel button label
 * @property {boolean} [showCancel=false] - Show cancel button
 * @property {Function} [onCancel] - Cancel callback
 * @property {string} [layout='vertical'] - Layout: 'vertical' | 'horizontal' | 'inline'
 * @property {string} [className=''] - Additional form classes
 */

/**
 * Validation rules
 * @typedef {Object} ValidationRules
 * @property {boolean} [required] - Required field
 * @property {number} [min] - Minimum value/length
 * @property {number} [max] - Maximum value/length
 * @property {number} [minLength] - Minimum string length
 * @property {number} [maxLength] - Maximum string length
 * @property {string|RegExp} [pattern] - Regex pattern
 * @property {Function} [custom] - Custom validation (value) => string|null
 * @property {string} [email] - Email validation
 * @property {string} [url] - URL validation
 */

/**
 * Form component class
 * @class
 */
export class Form {
  /**
   * Built-in validation messages (Japanese)
   */
  static MESSAGES = {
    required: 'この項目は必須です',
    email: '有効なメールアドレスを入力してください',
    url: '有効なURLを入力してください',
    min: (val) => `${val}以上の値を入力してください`,
    max: (val) => `${val}以下の値を入力してください`,
    minLength: (val) => `${val}文字以上で入力してください`,
    maxLength: (val) => `${val}文字以内で入力してください`,
    pattern: '正しい形式で入力してください',
    number: '数値を入力してください',
    integer: '整数を入力してください',
    date: '有効な日付を入力してください'
  };

  /**
   * Create a Form instance
   * @param {HTMLElement|string} container - Container element or selector
   * @param {FormOptions} options - Form configuration
   */
  constructor(container, options = {}) {
    this.container = typeof container === 'string'
      ? document.querySelector(container)
      : container;

    if (!this.container) {
      throw new Error('Form: Container element not found');
    }

    // Configuration
    this.fields = options.fields || [];
    this.values = { ...options.values } || {};
    this.validateOnChange = options.validateOnChange !== false;
    this.validateOnBlur = options.validateOnBlur !== false;
    this.showErrors = options.showErrors !== false;
    this.submitLabel = options.submitLabel || '送信';
    this.cancelLabel = options.cancelLabel || 'キャンセル';
    this.showCancel = options.showCancel || false;
    this.layout = options.layout || 'vertical';
    this.className = options.className || '';

    // Callbacks
    this.onSubmit = options.onSubmit || null;
    this.onChange = options.onChange || null;
    this.onCancel = options.onCancel || null;

    // State
    this.errors = {};
    this.touched = {};
    this.isSubmitting = false;

    // Element references
    this.formElement = null;
    this.fieldElements = {};

    // Initialize
    this._injectStyles();
    this.render();
  }

  /**
   * Inject form styles
   * @private
   */
  _injectStyles() {
    if (document.getElementById('form-component-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'form-component-styles';
    styles.textContent = `
      .form-component {
        width: 100%;
      }

      .form-group {
        margin-bottom: var(--space-5, 1.25rem);
        position: relative;
      }

      .form-group-horizontal {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
      }

      .form-group-horizontal .form-label {
        width: 120px;
        flex-shrink: 0;
        padding-top: 0.75rem;
      }

      .form-group-horizontal .form-control-wrapper {
        flex: 1;
      }

      .form-label {
        display: block;
        margin-bottom: var(--space-2, 0.5rem);
        font-size: var(--font-size-sm, 0.875rem);
        font-weight: var(--font-weight-medium, 500);
        color: var(--color-text-secondary, #94a3b8);
      }

      .form-label .required-indicator {
        color: var(--color-danger, #f87171);
        margin-left: 0.25rem;
      }

      .form-control {
        width: 100%;
        padding: var(--input-padding-y, 0.75rem) var(--input-padding-x, 1rem);
        background: var(--input-bg, rgba(0, 0, 0, 0.2));
        border: var(--input-border, 1px solid rgba(255, 255, 255, 0.1));
        border-radius: var(--input-radius, 12px);
        color: var(--color-text-primary, #f8fafc);
        font-family: var(--font-family-main);
        font-size: var(--font-size-base, 1rem);
        transition: all var(--transition-smooth, 0.2s ease);
        outline: none;
      }

      .form-control:hover {
        border-color: rgba(255, 255, 255, 0.15);
        background: rgba(0, 0, 0, 0.25);
      }

      .form-control:focus-visible {
        border-color: var(--color-primary, #06b6d4);
        background: rgba(0, 0, 0, 0.3);
        box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.15);
      }

      .form-control:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .form-control:read-only {
        background: rgba(0, 0, 0, 0.1);
        cursor: default;
      }

      .form-control.is-invalid {
        border-color: var(--color-danger, #f87171) !important;
        box-shadow: 0 0 0 3px rgba(248, 113, 113, 0.15);
      }

      .form-control.is-valid {
        border-color: var(--color-success, #34d399) !important;
      }

      /* Select */
      select.form-control {
        appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2306b6d4' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 1rem center;
        padding-right: 2.5rem;
        cursor: pointer;
      }

      /* Textarea */
      textarea.form-control {
        resize: vertical;
        min-height: 100px;
        font-family: var(--font-family-main);
      }

      /* Checkbox & Radio */
      .form-check {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
      }

      .form-check-input {
        width: 18px;
        height: 18px;
        cursor: pointer;
        accent-color: var(--color-primary, #06b6d4);
      }

      .form-check-label {
        font-size: var(--font-size-base, 1rem);
        color: var(--color-text-primary, #f8fafc);
        cursor: pointer;
        user-select: none;
      }

      /* Radio group */
      .form-radio-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }

      .form-radio-group.horizontal {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 1rem;
      }

      /* Help text */
      .form-help {
        margin-top: var(--space-1, 0.25rem);
        font-size: var(--font-size-xs, 0.75rem);
        color: var(--color-text-muted, #64748b);
      }

      /* Error text */
      .form-error {
        margin-top: var(--space-1, 0.25rem);
        font-size: var(--font-size-xs, 0.75rem);
        color: var(--color-danger, #f87171);
        display: flex;
        align-items: center;
        gap: 0.25rem;
      }

      .form-error-icon {
        width: 14px;
        height: 14px;
        flex-shrink: 0;
      }

      /* Form actions */
      .form-actions {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 0.75rem;
        margin-top: var(--space-6, 1.5rem);
        padding-top: var(--space-6, 1.5rem);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
      }

      .form-actions.inline {
        border-top: none;
        padding-top: 0;
      }

      /* Inline layout */
      .form-component.inline {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        flex-wrap: wrap;
      }

      .form-component.inline .form-group {
        margin-bottom: 0;
        flex: 1;
        min-width: 150px;
      }

      .form-component.inline .form-actions {
        margin-top: 0;
        padding-top: 0;
        border-top: none;
        align-self: flex-end;
      }

      /* Light theme */
      [data-theme="light"] .form-control {
        background: rgba(255, 255, 255, 0.9);
        border-color: rgba(0, 0, 0, 0.15);
        color: #1e293b;
      }

      [data-theme="light"] .form-control:hover {
        background: #ffffff;
        border-color: rgba(0, 0, 0, 0.2);
      }

      [data-theme="light"] .form-control:focus-visible {
        background: #ffffff;
      }

      [data-theme="light"] .form-label {
        color: #64748b;
      }

      [data-theme="light"] .form-check-label {
        color: #1e293b;
      }

      /* Responsive */
      @media (max-width: 640px) {
        .form-group-horizontal {
          flex-direction: column;
        }

        .form-group-horizontal .form-label {
          width: auto;
          padding-top: 0;
        }

        .form-actions {
          flex-direction: column-reverse;
        }

        .form-actions button {
          width: 100%;
        }
      }
    `;
    document.head.appendChild(styles);
  }

  /**
   * Generate unique ID
   * @private
   * @param {string} name - Field name
   * @returns {string} Unique ID
   */
  _generateId(name) {
    return `form-${Date.now()}-${name}`;
  }

  /**
   * Render a single field
   * @private
   * @param {FieldDef} field - Field definition
   * @returns {string} Field HTML
   */
  _renderField(field) {
    const id = this._generateId(field.name);
    const value = this.values[field.name] ?? field.value ?? '';
    const error = this.errors[field.name];
    const touched = this.touched[field.name];
    const hasError = touched && error;
    const isHorizontal = this.layout === 'horizontal';

    let inputHtml = '';

    switch (field.type) {
      case 'select':
        inputHtml = this._renderSelect(field, id, value, hasError);
        break;
      case 'textarea':
        inputHtml = this._renderTextarea(field, id, value, hasError);
        break;
      case 'checkbox':
        inputHtml = this._renderCheckbox(field, id, value);
        break;
      case 'radio':
        inputHtml = this._renderRadioGroup(field, id, value);
        break;
      default:
        inputHtml = this._renderInput(field, id, value, hasError);
    }

    const labelHtml = field.type !== 'checkbox' ? `
      <label for="${id}" class="form-label">
        ${escapeHtml(field.label)}
        ${field.required ? '<span class="required-indicator" aria-hidden="true">*</span>' : ''}
      </label>
    ` : '';

    const helpHtml = field.help ? `
      <div id="${id}-help" class="form-help">${escapeHtml(field.help)}</div>
    ` : '';

    const errorHtml = hasError ? `
      <div id="${id}-error" class="form-error" role="alert">
        <svg class="form-error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        ${escapeHtml(error)}
      </div>
    ` : '';

    if (isHorizontal && field.type !== 'checkbox') {
      return `
        <div class="form-group form-group-horizontal ${field.className || ''}">
          ${labelHtml}
          <div class="form-control-wrapper">
            ${inputHtml}
            ${helpHtml}
            ${errorHtml}
          </div>
        </div>
      `;
    }

    return `
      <div class="form-group ${field.className || ''}">
        ${labelHtml}
        ${inputHtml}
        ${helpHtml}
        ${errorHtml}
      </div>
    `;
  }

  /**
   * Render input field
   * @private
   */
  _renderInput(field, id, value, hasError) {
    const type = field.type || 'text';
    const attrs = [
      `type="${type}"`,
      `id="${id}"`,
      `name="${field.name}"`,
      `class="form-control ${hasError ? 'is-invalid' : ''}"`,
      `value="${escapeHtml(String(value))}"`,
      field.placeholder ? `placeholder="${escapeHtml(field.placeholder)}"` : '',
      field.required ? 'required aria-required="true"' : '',
      field.disabled ? 'disabled' : '',
      field.readonly ? 'readonly' : '',
      field.min !== undefined ? `min="${field.min}"` : '',
      field.max !== undefined ? `max="${field.max}"` : '',
      field.step !== undefined ? `step="${field.step}"` : '',
      field.minLength !== undefined ? `minlength="${field.minLength}"` : '',
      field.maxLength !== undefined ? `maxlength="${field.maxLength}"` : '',
      field.pattern ? `pattern="${field.pattern}"` : '',
      field.autocomplete ? `autocomplete="${field.autocomplete}"` : '',
      field.help ? `aria-describedby="${id}-help"` : '',
      hasError ? `aria-invalid="true" aria-describedby="${id}-error"` : ''
    ].filter(Boolean).join(' ');

    return `<input ${attrs}>`;
  }

  /**
   * Render select field
   * @private
   */
  _renderSelect(field, id, value, hasError) {
    const options = (field.options || []).map(opt => {
      const optValue = typeof opt === 'object' ? opt.value : opt;
      const optLabel = typeof opt === 'object' ? opt.label : opt;
      const selected = String(value) === String(optValue) ? 'selected' : '';
      return `<option value="${escapeHtml(String(optValue))}" ${selected}>${escapeHtml(optLabel)}</option>`;
    }).join('');

    const attrs = [
      `id="${id}"`,
      `name="${field.name}"`,
      `class="form-control ${hasError ? 'is-invalid' : ''}"`,
      field.required ? 'required aria-required="true"' : '',
      field.disabled ? 'disabled' : '',
      field.help ? `aria-describedby="${id}-help"` : '',
      hasError ? `aria-invalid="true" aria-describedby="${id}-error"` : ''
    ].filter(Boolean).join(' ');

    return `
      <select ${attrs}>
        ${field.placeholder ? `<option value="">${escapeHtml(field.placeholder)}</option>` : ''}
        ${options}
      </select>
    `;
  }

  /**
   * Render textarea field
   * @private
   */
  _renderTextarea(field, id, value, hasError) {
    const attrs = [
      `id="${id}"`,
      `name="${field.name}"`,
      `class="form-control ${hasError ? 'is-invalid' : ''}"`,
      `rows="${field.rows || 4}"`,
      field.placeholder ? `placeholder="${escapeHtml(field.placeholder)}"` : '',
      field.required ? 'required aria-required="true"' : '',
      field.disabled ? 'disabled' : '',
      field.readonly ? 'readonly' : '',
      field.minLength !== undefined ? `minlength="${field.minLength}"` : '',
      field.maxLength !== undefined ? `maxlength="${field.maxLength}"` : '',
      field.help ? `aria-describedby="${id}-help"` : '',
      hasError ? `aria-invalid="true" aria-describedby="${id}-error"` : ''
    ].filter(Boolean).join(' ');

    return `<textarea ${attrs}>${escapeHtml(String(value))}</textarea>`;
  }

  /**
   * Render checkbox field
   * @private
   */
  _renderCheckbox(field, id, value) {
    const checked = value === true || value === 'true' || value === 1 ? 'checked' : '';

    return `
      <div class="form-check">
        <input type="checkbox"
               id="${id}"
               name="${field.name}"
               class="form-check-input"
               ${checked}
               ${field.required ? 'required aria-required="true"' : ''}
               ${field.disabled ? 'disabled' : ''}>
        <label for="${id}" class="form-check-label">
          ${escapeHtml(field.label)}
          ${field.required ? '<span class="required-indicator" aria-hidden="true">*</span>' : ''}
        </label>
      </div>
    `;
  }

  /**
   * Render radio group
   * @private
   */
  _renderRadioGroup(field, id, value) {
    const options = (field.options || []).map((opt, index) => {
      const optValue = typeof opt === 'object' ? opt.value : opt;
      const optLabel = typeof opt === 'object' ? opt.label : opt;
      const checked = String(value) === String(optValue) ? 'checked' : '';
      const radioId = `${id}-${index}`;

      return `
        <div class="form-check">
          <input type="radio"
                 id="${radioId}"
                 name="${field.name}"
                 value="${escapeHtml(String(optValue))}"
                 class="form-check-input"
                 ${checked}
                 ${field.required ? 'required' : ''}
                 ${field.disabled ? 'disabled' : ''}>
          <label for="${radioId}" class="form-check-label">${escapeHtml(optLabel)}</label>
        </div>
      `;
    }).join('');

    const direction = field.horizontal ? 'horizontal' : '';

    return `
      <div class="form-radio-group ${direction}" role="radiogroup" aria-label="${escapeHtml(field.label)}">
        ${options}
      </div>
    `;
  }

  /**
   * Render form actions
   * @private
   * @returns {string} Actions HTML
   */
  _renderActions() {
    const inline = this.layout === 'inline' ? 'inline' : '';

    return `
      <div class="form-actions ${inline}">
        ${this.showCancel ? `
          <button type="button" class="btn btn-ghost form-cancel-btn">
            ${escapeHtml(this.cancelLabel)}
          </button>
        ` : ''}
        <button type="submit" class="btn btn-primary form-submit-btn" ${this.isSubmitting ? 'disabled' : ''}>
          ${this.isSubmitting ? `
            <span class="btn-loading-spinner"></span>
            処理中...
          ` : escapeHtml(this.submitLabel)}
        </button>
      </div>
    `;
  }

  /**
   * Render the complete form
   */
  render() {
    const layoutClass = this.layout === 'inline' ? 'inline' : '';

    const fieldsHtml = this.fields.map(field => this._renderField(field)).join('');

    this.container.innerHTML = `
      <form class="form-component ${layoutClass} ${this.className}" novalidate>
        ${fieldsHtml}
        ${this._renderActions()}
      </form>
    `;

    this.formElement = this.container.querySelector('form');
    this._cacheFieldElements();
    this._bindEvents();
  }

  /**
   * Cache field element references
   * @private
   */
  _cacheFieldElements() {
    this.fieldElements = {};
    this.fields.forEach(field => {
      const el = this.formElement.querySelector(`[name="${field.name}"]`);
      if (el) {
        this.fieldElements[field.name] = el;
      }
    });
  }

  /**
   * Bind event listeners
   * @private
   */
  _bindEvents() {
    // Submit
    this.formElement.addEventListener('submit', (e) => {
      e.preventDefault();
      this._handleSubmit();
    });

    // Cancel
    const cancelBtn = this.formElement.querySelector('.form-cancel-btn');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        if (this.onCancel) this.onCancel(this);
      });
    }

    // Field events
    this.fields.forEach(field => {
      const el = this.fieldElements[field.name];
      if (!el) return;

      // Change
      const changeEvent = field.type === 'checkbox' || field.type === 'radio' ? 'change' : 'input';
      el.addEventListener(changeEvent, (e) => {
        const value = field.type === 'checkbox' ? e.target.checked : e.target.value;
        this.values[field.name] = value;

        if (this.validateOnChange) {
          this._validateField(field);
        }

        if (this.onChange) {
          this.onChange(field.name, value, this.values);
        }
      });

      // Blur
      if (this.validateOnBlur) {
        el.addEventListener('blur', () => {
          this.touched[field.name] = true;
          this._validateField(field);
          this._updateFieldUI(field);
        });
      }
    });
  }

  /**
   * Validate a single field
   * @private
   * @param {FieldDef} field - Field definition
   * @returns {boolean} Is valid
   */
  _validateField(field) {
    const value = this.values[field.name];
    const validation = field.validation || {};
    let error = null;

    // Required
    if (field.required || validation.required) {
      if (value === undefined || value === null || value === '' ||
          (field.type === 'checkbox' && value !== true)) {
        error = validation.requiredMessage || Form.MESSAGES.required;
      }
    }

    if (!error && value !== undefined && value !== null && value !== '') {
      // Min/Max for numbers
      if (field.type === 'number') {
        const numValue = Number(value);
        if (isNaN(numValue)) {
          error = Form.MESSAGES.number;
        } else {
          if (field.min !== undefined && numValue < field.min) {
            error = Form.MESSAGES.min(field.min);
          }
          if (field.max !== undefined && numValue > field.max) {
            error = Form.MESSAGES.max(field.max);
          }
        }
      }

      // Length validation
      if (typeof value === 'string') {
        if (field.minLength !== undefined && value.length < field.minLength) {
          error = Form.MESSAGES.minLength(field.minLength);
        }
        if (field.maxLength !== undefined && value.length > field.maxLength) {
          error = Form.MESSAGES.maxLength(field.maxLength);
        }
      }

      // Pattern
      if (field.pattern && typeof value === 'string') {
        const regex = new RegExp(field.pattern);
        if (!regex.test(value)) {
          error = validation.patternMessage || Form.MESSAGES.pattern;
        }
      }

      // Email
      if (field.type === 'email' && typeof value === 'string') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          error = Form.MESSAGES.email;
        }
      }

      // Custom validation
      if (validation.custom && typeof validation.custom === 'function') {
        const customError = validation.custom(value, this.values);
        if (customError) {
          error = customError;
        }
      }
    }

    if (error) {
      this.errors[field.name] = error;
      return false;
    } else {
      delete this.errors[field.name];
      return true;
    }
  }

  /**
   * Update field UI after validation
   * @private
   * @param {FieldDef} field - Field definition
   */
  _updateFieldUI(field) {
    const el = this.fieldElements[field.name];
    if (!el) return;

    const error = this.errors[field.name];
    const touched = this.touched[field.name];
    const group = el.closest('.form-group');

    // Update input classes
    el.classList.remove('is-valid', 'is-invalid');
    if (touched) {
      el.classList.add(error ? 'is-invalid' : 'is-valid');
    }

    // Update error message
    const existingError = group.querySelector('.form-error');
    if (existingError) {
      existingError.remove();
    }

    if (touched && error && this.showErrors) {
      const errorEl = document.createElement('div');
      errorEl.className = 'form-error';
      errorEl.setAttribute('role', 'alert');
      errorEl.innerHTML = `
        <svg class="form-error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        ${escapeHtml(error)}
      `;

      const wrapper = group.querySelector('.form-control-wrapper') || group;
      wrapper.appendChild(errorEl);
    }
  }

  /**
   * Handle form submission
   * @private
   */
  async _handleSubmit() {
    // Mark all fields as touched
    this.fields.forEach(field => {
      this.touched[field.name] = true;
    });

    // Validate all
    const isValid = this.validate();

    if (!isValid) {
      // Focus first error field
      const firstErrorField = this.fields.find(f => this.errors[f.name]);
      if (firstErrorField) {
        const el = this.fieldElements[firstErrorField.name];
        if (el) el.focus();
      }
      return;
    }

    if (this.onSubmit) {
      this.isSubmitting = true;
      this._updateSubmitButton();

      try {
        await this.onSubmit(this.values, this);
      } catch (error) {
        console.error('Form submission error:', error);
      } finally {
        this.isSubmitting = false;
        this._updateSubmitButton();
      }
    }
  }

  /**
   * Update submit button state
   * @private
   */
  _updateSubmitButton() {
    const submitBtn = this.formElement.querySelector('.form-submit-btn');
    if (submitBtn) {
      submitBtn.disabled = this.isSubmitting;
      submitBtn.innerHTML = this.isSubmitting
        ? '<span class="btn-loading-spinner"></span> 処理中...'
        : escapeHtml(this.submitLabel);
    }
  }

  // Public API

  /**
   * Validate all fields
   * @returns {boolean} Is form valid
   */
  validate() {
    let isValid = true;

    this.fields.forEach(field => {
      const fieldValid = this._validateField(field);
      this._updateFieldUI(field);
      if (!fieldValid) isValid = false;
    });

    return isValid;
  }

  /**
   * Get all form values
   * @returns {Object} Form values
   */
  getValues() {
    return { ...this.values };
  }

  /**
   * Set form values
   * @param {Object} values - New values
   * @returns {Form} Instance for chaining
   */
  setValues(values) {
    this.values = { ...this.values, ...values };

    // Update DOM
    Object.entries(values).forEach(([name, value]) => {
      const el = this.fieldElements[name];
      if (!el) return;

      const field = this.fields.find(f => f.name === name);
      if (!field) return;

      if (field.type === 'checkbox') {
        el.checked = value === true || value === 'true' || value === 1;
      } else if (field.type === 'radio') {
        const radio = this.formElement.querySelector(`[name="${name}"][value="${value}"]`);
        if (radio) radio.checked = true;
      } else {
        el.value = value;
      }
    });

    return this;
  }

  /**
   * Get single field value
   * @param {string} name - Field name
   * @returns {*} Field value
   */
  getValue(name) {
    return this.values[name];
  }

  /**
   * Set single field value
   * @param {string} name - Field name
   * @param {*} value - New value
   * @returns {Form} Instance for chaining
   */
  setValue(name, value) {
    return this.setValues({ [name]: value });
  }

  /**
   * Get form errors
   * @returns {Object} Errors object
   */
  getErrors() {
    return { ...this.errors };
  }

  /**
   * Set field error manually
   * @param {string} name - Field name
   * @param {string} error - Error message
   * @returns {Form} Instance for chaining
   */
  setError(name, error) {
    this.errors[name] = error;
    this.touched[name] = true;

    const field = this.fields.find(f => f.name === name);
    if (field) {
      this._updateFieldUI(field);
    }

    return this;
  }

  /**
   * Clear all errors
   * @returns {Form} Instance for chaining
   */
  clearErrors() {
    this.errors = {};
    this.touched = {};

    this.fields.forEach(field => {
      this._updateFieldUI(field);
    });

    return this;
  }

  /**
   * Reset form to initial state
   * @returns {Form} Instance for chaining
   */
  reset() {
    this.values = {};
    this.errors = {};
    this.touched = {};
    this.isSubmitting = false;

    // Reset fields to default values
    this.fields.forEach(field => {
      if (field.value !== undefined) {
        this.values[field.name] = field.value;
      }
    });

    this.render();
    return this;
  }

  /**
   * Enable/disable form
   * @param {boolean} enabled - Enable state
   * @returns {Form} Instance for chaining
   */
  setEnabled(enabled) {
    Object.values(this.fieldElements).forEach(el => {
      el.disabled = !enabled;
    });

    const submitBtn = this.formElement.querySelector('.form-submit-btn');
    if (submitBtn) submitBtn.disabled = !enabled;

    return this;
  }

  /**
   * Focus specific field
   * @param {string} name - Field name
   * @returns {Form} Instance for chaining
   */
  focus(name) {
    const el = this.fieldElements[name];
    if (el) el.focus();
    return this;
  }

  /**
   * Destroy form instance
   */
  destroy() {
    this.container.innerHTML = '';
    this.formElement = null;
    this.fieldElements = {};
  }
}

export default Form;
