/**
 * Input Component - YuKyuDATA Design System
 * Accessible input fields with validation
 *
 * @module components/Input
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * Input options
 * @typedef {Object} InputOptions
 * @property {string} [type='text'] - Input type
 * @property {string} [name=''] - Input name
 * @property {string} [label=''] - Label text (Japanese)
 * @property {string} [placeholder=''] - Placeholder text
 * @property {string} [value=''] - Initial value
 * @property {boolean} [required=false] - Required field
 * @property {boolean} [disabled=false] - Disabled state
 * @property {boolean} [readonly=false] - Read-only state
 * @property {string} [help=''] - Help text
 * @property {string} [error=''] - Error message
 * @property {string} [icon=''] - Leading icon SVG
 * @property {string} [iconAfter=''] - Trailing icon SVG
 * @property {string} [size='medium'] - Size: small, medium, large
 * @property {boolean} [clearable=false] - Show clear button
 * @property {string} [autocomplete=''] - Autocomplete attribute
 * @property {number} [minLength] - Minimum length
 * @property {number} [maxLength] - Maximum length
 * @property {string} [pattern] - Validation pattern
 * @property {Function} [onInput] - Input event handler
 * @property {Function} [onChange] - Change event handler
 * @property {Function} [onClear] - Clear button handler
 * @property {string} [className=''] - Additional CSS classes
 */

/**
 * Create an input field with label and validation
 * @param {InputOptions} options - Input configuration
 * @returns {HTMLDivElement} Input group element
 */
export function Input(options = {}) {
  const {
    type = 'text',
    name = '',
    label = '',
    placeholder = '',
    value = '',
    required = false,
    disabled = false,
    readonly = false,
    help = '',
    error = '',
    icon = '',
    iconAfter = '',
    size = 'medium',
    clearable = false,
    autocomplete = '',
    minLength,
    maxLength,
    pattern,
    onInput,
    onChange,
    onClear,
    className = ''
  } = options;

  injectInputStyles();

  const id = `input-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const hasError = !!error;

  // Create wrapper
  const wrapper = document.createElement('div');
  wrapper.className = `input-group input-group-${size} ${className}`.trim();

  // Label
  if (label) {
    const labelEl = document.createElement('label');
    labelEl.htmlFor = id;
    labelEl.className = 'input-label';
    labelEl.innerHTML = `
      ${escapeHtml(label)}
      ${required ? '<span class="input-required" aria-hidden="true">*</span>' : ''}
    `;
    wrapper.appendChild(labelEl);
  }

  // Input container
  const container = document.createElement('div');
  container.className = [
    'input-container',
    icon ? 'has-icon-left' : '',
    iconAfter || clearable ? 'has-icon-right' : '',
    hasError ? 'has-error' : ''
  ].filter(Boolean).join(' ');

  // Leading icon
  if (icon) {
    const iconEl = document.createElement('span');
    iconEl.className = 'input-icon input-icon-left';
    iconEl.setAttribute('aria-hidden', 'true');
    iconEl.innerHTML = icon;
    container.appendChild(iconEl);
  }

  // Input element
  const input = document.createElement('input');
  input.type = type;
  input.id = id;
  input.name = name;
  input.className = `input input-${size}`;
  input.value = value;
  input.placeholder = placeholder;
  input.disabled = disabled;
  input.readOnly = readonly;

  if (required) {
    input.required = true;
    input.setAttribute('aria-required', 'true');
  }
  if (autocomplete) input.autocomplete = autocomplete;
  if (minLength !== undefined) input.minLength = minLength;
  if (maxLength !== undefined) input.maxLength = maxLength;
  if (pattern) input.pattern = pattern;
  if (help) input.setAttribute('aria-describedby', `${id}-help`);
  if (hasError) {
    input.setAttribute('aria-invalid', 'true');
    input.setAttribute('aria-describedby', `${id}-error`);
    input.classList.add('is-invalid');
  }

  container.appendChild(input);

  // Clear button
  if (clearable && !disabled && !readonly) {
    const clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.className = 'input-clear';
    clearBtn.setAttribute('aria-label', 'クリア');
    clearBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    `;
    clearBtn.addEventListener('click', () => {
      input.value = '';
      input.focus();
      if (onClear) onClear();
      if (onInput) onInput({ target: input });
    });
    container.appendChild(clearBtn);
  }

  // Trailing icon
  if (iconAfter && !clearable) {
    const iconEl = document.createElement('span');
    iconEl.className = 'input-icon input-icon-right';
    iconEl.setAttribute('aria-hidden', 'true');
    iconEl.innerHTML = iconAfter;
    container.appendChild(iconEl);
  }

  wrapper.appendChild(container);

  // Help text
  if (help && !hasError) {
    const helpEl = document.createElement('span');
    helpEl.id = `${id}-help`;
    helpEl.className = 'input-help';
    helpEl.textContent = help;
    wrapper.appendChild(helpEl);
  }

  // Error message
  if (hasError) {
    const errorEl = document.createElement('span');
    errorEl.id = `${id}-error`;
    errorEl.className = 'input-error';
    errorEl.setAttribute('role', 'alert');
    errorEl.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      ${escapeHtml(error)}
    `;
    wrapper.appendChild(errorEl);
  }

  // Event handlers
  if (onInput) {
    input.addEventListener('input', onInput);
  }
  if (onChange) {
    input.addEventListener('change', onChange);
  }

  // Helper methods
  wrapper.getValue = () => input.value;
  wrapper.setValue = (val) => { input.value = val; };
  wrapper.setError = (msg) => {
    const existingError = wrapper.querySelector('.input-error');
    if (existingError) existingError.remove();

    if (msg) {
      input.classList.add('is-invalid');
      input.setAttribute('aria-invalid', 'true');
      container.classList.add('has-error');

      const errorEl = document.createElement('span');
      errorEl.id = `${id}-error`;
      errorEl.className = 'input-error';
      errorEl.setAttribute('role', 'alert');
      errorEl.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        ${escapeHtml(msg)}
      `;
      wrapper.appendChild(errorEl);
    } else {
      input.classList.remove('is-invalid');
      input.removeAttribute('aria-invalid');
      container.classList.remove('has-error');
    }
  };
  wrapper.focus = () => input.focus();
  wrapper.getInputElement = () => input;

  return wrapper;
}

/**
 * Create a textarea element
 * @param {Object} options - Textarea options
 * @returns {HTMLDivElement} Textarea group element
 */
export function Textarea(options = {}) {
  const {
    name = '',
    label = '',
    placeholder = '',
    value = '',
    required = false,
    disabled = false,
    readonly = false,
    help = '',
    error = '',
    rows = 4,
    resize = 'vertical',
    onInput,
    onChange,
    className = ''
  } = options;

  injectInputStyles();

  const id = `textarea-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const hasError = !!error;

  const wrapper = document.createElement('div');
  wrapper.className = `input-group ${className}`.trim();

  if (label) {
    const labelEl = document.createElement('label');
    labelEl.htmlFor = id;
    labelEl.className = 'input-label';
    labelEl.innerHTML = `
      ${escapeHtml(label)}
      ${required ? '<span class="input-required" aria-hidden="true">*</span>' : ''}
    `;
    wrapper.appendChild(labelEl);
  }

  const textarea = document.createElement('textarea');
  textarea.id = id;
  textarea.name = name;
  textarea.className = `input textarea ${hasError ? 'is-invalid' : ''}`;
  textarea.value = value;
  textarea.placeholder = placeholder;
  textarea.rows = rows;
  textarea.disabled = disabled;
  textarea.readOnly = readonly;
  textarea.style.resize = resize;

  if (required) {
    textarea.required = true;
    textarea.setAttribute('aria-required', 'true');
  }
  if (hasError) {
    textarea.setAttribute('aria-invalid', 'true');
    textarea.setAttribute('aria-describedby', `${id}-error`);
  }

  wrapper.appendChild(textarea);

  if (help && !hasError) {
    const helpEl = document.createElement('span');
    helpEl.id = `${id}-help`;
    helpEl.className = 'input-help';
    helpEl.textContent = help;
    wrapper.appendChild(helpEl);
  }

  if (hasError) {
    const errorEl = document.createElement('span');
    errorEl.id = `${id}-error`;
    errorEl.className = 'input-error';
    errorEl.setAttribute('role', 'alert');
    errorEl.textContent = error;
    wrapper.appendChild(errorEl);
  }

  if (onInput) textarea.addEventListener('input', onInput);
  if (onChange) textarea.addEventListener('change', onChange);

  wrapper.getValue = () => textarea.value;
  wrapper.setValue = (val) => { textarea.value = val; };
  wrapper.focus = () => textarea.focus();
  wrapper.getInputElement = () => textarea;

  return wrapper;
}

/**
 * Inject input styles
 * @private
 */
function injectInputStyles() {
  if (document.getElementById('input-component-styles')) return;

  const styles = document.createElement('style');
  styles.id = 'input-component-styles';
  styles.textContent = `
    .input-group {
      margin-bottom: var(--space-5, 1.25rem);
    }

    .input-label {
      display: block;
      margin-bottom: var(--space-2, 0.5rem);
      font-size: var(--font-size-sm, 0.875rem);
      font-weight: var(--font-weight-medium, 500);
      color: var(--color-text-secondary, #94a3b8);
    }

    .input-required {
      color: var(--color-danger, #f87171);
      margin-left: 0.25rem;
    }

    .input-container {
      position: relative;
      display: flex;
      align-items: center;
    }

    .input {
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

    .input:hover:not(:disabled) {
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(0, 0, 0, 0.25);
    }

    .input:focus-visible {
      border-color: var(--color-primary, #06b6d4);
      background: rgba(0, 0, 0, 0.3);
      box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.15);
    }

    .input:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .input:read-only {
      background: rgba(0, 0, 0, 0.1);
      cursor: default;
    }

    .input::placeholder {
      color: var(--color-text-muted, #64748b);
      opacity: 0.8;
    }

    .input.is-invalid {
      border-color: var(--color-danger, #f87171) !important;
      box-shadow: 0 0 0 3px rgba(248, 113, 113, 0.15);
    }

    .input.is-valid {
      border-color: var(--color-success, #34d399) !important;
    }

    /* Sizes */
    .input-small {
      padding: 0.5rem 0.75rem;
      font-size: var(--font-size-sm, 0.875rem);
      border-radius: 8px;
    }

    .input-large {
      padding: 1rem 1.25rem;
      font-size: var(--font-size-lg, 1.125rem);
      border-radius: 14px;
    }

    /* Icons */
    .input-container.has-icon-left .input {
      padding-left: 2.75rem;
    }

    .input-container.has-icon-right .input {
      padding-right: 2.75rem;
    }

    .input-icon {
      position: absolute;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      color: var(--color-text-muted, #64748b);
      pointer-events: none;
    }

    .input-icon-left {
      left: 1rem;
    }

    .input-icon-right {
      right: 1rem;
    }

    .input-icon svg {
      width: 100%;
      height: 100%;
    }

    /* Clear button */
    .input-clear {
      position: absolute;
      right: 0.75rem;
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.1);
      border: none;
      border-radius: 6px;
      color: var(--color-text-muted, #64748b);
      cursor: pointer;
      opacity: 0;
      transition: all 0.2s ease;
    }

    .input-container:hover .input-clear,
    .input:focus ~ .input-clear {
      opacity: 1;
    }

    .input-clear:hover {
      background: rgba(248, 113, 113, 0.2);
      color: var(--color-danger, #f87171);
    }

    .input-clear:focus-visible {
      outline: var(--focus-outline, 3px solid var(--color-primary));
      outline-offset: 2px;
      opacity: 1;
    }

    /* Help text */
    .input-help {
      display: block;
      margin-top: var(--space-1, 0.25rem);
      font-size: var(--font-size-xs, 0.75rem);
      color: var(--color-text-muted, #64748b);
    }

    /* Error text */
    .input-error {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      margin-top: var(--space-1, 0.25rem);
      font-size: var(--font-size-xs, 0.75rem);
      color: var(--color-danger, #f87171);
    }

    /* Textarea */
    .textarea {
      min-height: 100px;
      resize: vertical;
      font-family: var(--font-family-main);
    }

    /* Light theme */
    [data-theme="light"] .input {
      background: rgba(255, 255, 255, 0.9);
      border-color: rgba(0, 0, 0, 0.15);
      color: #1e293b;
    }

    [data-theme="light"] .input:hover:not(:disabled) {
      background: #ffffff;
      border-color: rgba(0, 0, 0, 0.2);
    }

    [data-theme="light"] .input:focus-visible {
      background: #ffffff;
    }

    [data-theme="light"] .input-label {
      color: #64748b;
    }

    [data-theme="light"] .input-clear {
      background: rgba(0, 0, 0, 0.05);
    }

    [data-theme="light"] .input-clear:hover {
      background: rgba(239, 68, 68, 0.1);
    }
  `;
  document.head.appendChild(styles);
}

export default Input;
