/**
 * Select Component - YuKyuDATA Design System
 * Accessible select dropdown with search functionality
 *
 * @module components/Select
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * Select option
 * @typedef {Object} SelectOption
 * @property {string|number} value - Option value
 * @property {string} label - Display label
 * @property {boolean} [disabled=false] - Disabled option
 * @property {string} [group] - Option group name
 */

/**
 * Select options
 * @typedef {Object} SelectOptions
 * @property {SelectOption[]} options - Available options
 * @property {string} [name=''] - Select name
 * @property {string} [label=''] - Label text
 * @property {string} [placeholder='選択してください'] - Placeholder text
 * @property {string|number} [value] - Initial value
 * @property {boolean} [required=false] - Required field
 * @property {boolean} [disabled=false] - Disabled state
 * @property {boolean} [searchable=false] - Enable search
 * @property {boolean} [clearable=false] - Allow clearing
 * @property {boolean} [multiple=false] - Allow multiple selection
 * @property {string} [help=''] - Help text
 * @property {string} [error=''] - Error message
 * @property {string} [size='medium'] - Size: small, medium, large
 * @property {Function} [onChange] - Change callback (value, option)
 * @property {Function} [onSearch] - Search callback (query)
 * @property {string} [className=''] - Additional CSS classes
 */

/**
 * Select component class
 * @class
 */
export class Select {
  /**
   * Create a Select instance
   * @param {HTMLElement|string} container - Container element or selector
   * @param {SelectOptions} options - Select configuration
   */
  constructor(container, options = {}) {
    this.container = typeof container === 'string'
      ? document.querySelector(container)
      : container;

    if (!this.container) {
      throw new Error('Select: Container element not found');
    }

    // Configuration
    this.options = options.options || [];
    this.name = options.name || '';
    this.label = options.label || '';
    this.placeholder = options.placeholder || '選択してください';
    this.required = options.required || false;
    this.disabled = options.disabled || false;
    this.searchable = options.searchable || false;
    this.clearable = options.clearable || false;
    this.multiple = options.multiple || false;
    this.help = options.help || '';
    this.error = options.error || '';
    this.size = options.size || 'medium';
    this.className = options.className || '';

    // Callbacks
    this.onChange = options.onChange || null;
    this.onSearch = options.onSearch || null;

    // State
    this.value = options.value !== undefined ? options.value : (this.multiple ? [] : null);
    this.isOpen = false;
    this.searchQuery = '';
    this.highlightedIndex = -1;
    this.filteredOptions = [...this.options];

    // Element references
    this.wrapper = null;
    this.trigger = null;
    this.dropdown = null;
    this.searchInput = null;
    this.hiddenInput = null;

    // Unique ID
    this.id = `select-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Bound handlers
    this._handleDocumentClick = this._handleDocumentClick.bind(this);
    this._handleKeyDown = this._handleKeyDown.bind(this);

    // Initialize
    this._injectStyles();
    this._render();
    this._bindEvents();
  }

  /**
   * Inject select styles
   * @private
   */
  _injectStyles() {
    if (document.getElementById('select-component-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'select-component-styles';
    styles.textContent = `
      .select-wrapper {
        position: relative;
      }

      .select-label {
        display: block;
        margin-bottom: var(--space-2, 0.5rem);
        font-size: var(--font-size-sm, 0.875rem);
        font-weight: var(--font-weight-medium, 500);
        color: var(--color-text-secondary, #94a3b8);
      }

      .select-required {
        color: var(--color-danger, #f87171);
        margin-left: 0.25rem;
      }

      .select-trigger {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        padding: var(--input-padding-y, 0.75rem) var(--input-padding-x, 1rem);
        background: var(--input-bg, rgba(0, 0, 0, 0.2));
        border: var(--input-border, 1px solid rgba(255, 255, 255, 0.1));
        border-radius: var(--input-radius, 12px);
        color: var(--color-text-primary, #f8fafc);
        font-family: var(--font-family-main);
        font-size: var(--font-size-base, 1rem);
        cursor: pointer;
        transition: all var(--transition-smooth, 0.2s ease);
        outline: none;
        text-align: left;
      }

      .select-trigger:hover:not(:disabled) {
        border-color: rgba(255, 255, 255, 0.2);
        background: rgba(0, 0, 0, 0.25);
      }

      .select-trigger:focus-visible {
        border-color: var(--color-primary, #2563eb);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
      }

      .select-trigger:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .select-trigger.is-invalid {
        border-color: var(--color-danger, #f87171) !important;
      }

      .select-trigger.is-open {
        border-color: var(--color-primary, #2563eb);
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
      }

      .select-value {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .select-placeholder {
        color: var(--color-text-muted, #64748b);
      }

      .select-icons {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        flex-shrink: 0;
      }

      .select-clear,
      .select-arrow {
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--color-text-muted, #64748b);
        transition: all 0.2s ease;
      }

      .select-clear {
        background: none;
        border: none;
        cursor: pointer;
        border-radius: 4px;
        padding: 0;
      }

      .select-clear:hover {
        color: var(--color-danger, #f87171);
        background: rgba(248, 113, 113, 0.1);
      }

      .select-arrow {
        transition: transform 0.2s ease;
      }

      .select-trigger.is-open .select-arrow {
        transform: rotate(180deg);
      }

      .select-dropdown {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        z-index: 1000;
        background: var(--color-bg-card, rgba(15, 15, 15, 0.98));
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: none;
        border-radius: 0 0 12px 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        max-height: 280px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        opacity: 0;
        visibility: hidden;
        transform: translateY(-10px);
        transition: all 0.2s ease;
      }

      .select-dropdown.is-open {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
      }

      .select-search {
        padding: 0.75rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        flex-shrink: 0;
      }

      .select-search-input {
        width: 100%;
        padding: 0.5rem 0.75rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: var(--color-text-primary, #f8fafc);
        font-size: var(--font-size-sm, 0.875rem);
        outline: none;
      }

      .select-search-input:focus-visible {
        border-color: var(--color-primary, #2563eb);
      }

      .select-search-input::placeholder {
        color: var(--color-text-muted, #64748b);
      }

      .select-options {
        overflow-y: auto;
        padding: 0.5rem;
        flex: 1;
      }

      .select-option {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.15s ease;
        color: var(--color-text-primary, #f8fafc);
        font-size: var(--font-size-sm, 0.875rem);
      }

      .select-option:hover,
      .select-option.is-highlighted {
        background: rgba(255, 255, 255, 0.05);
      }

      .select-option.is-selected {
        background: rgba(37, 99, 235, 0.15);
        color: var(--color-primary, #2563eb);
      }

      .select-option.is-disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .select-option-check {
        width: 18px;
        height: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--color-primary, #2563eb);
        opacity: 0;
      }

      .select-option.is-selected .select-option-check {
        opacity: 1;
      }

      .select-group-label {
        padding: 0.5rem 1rem;
        font-size: var(--font-size-xs, 0.75rem);
        font-weight: 600;
        color: var(--color-text-muted, #64748b);
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      .select-empty {
        padding: 1.5rem;
        text-align: center;
        color: var(--color-text-muted, #64748b);
        font-size: var(--font-size-sm, 0.875rem);
      }

      .select-help {
        display: block;
        margin-top: var(--space-1, 0.25rem);
        font-size: var(--font-size-xs, 0.75rem);
        color: var(--color-text-muted, #64748b);
      }

      .select-error {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        margin-top: var(--space-1, 0.25rem);
        font-size: var(--font-size-xs, 0.75rem);
        color: var(--color-danger, #f87171);
      }

      /* Multiple selection tags */
      .select-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.25rem;
        flex: 1;
        min-width: 0;
      }

      .select-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.5rem;
        background: rgba(37, 99, 235, 0.2);
        border-radius: 6px;
        font-size: var(--font-size-xs, 0.75rem);
        color: var(--color-primary, #2563eb);
      }

      .select-tag-remove {
        width: 14px;
        height: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: none;
        border: none;
        color: inherit;
        cursor: pointer;
        padding: 0;
        opacity: 0.7;
      }

      .select-tag-remove:hover {
        opacity: 1;
      }

      /* Light theme */
      [data-theme="light"] .select-trigger {
        background: rgba(255, 255, 255, 0.9);
        border-color: rgba(0, 0, 0, 0.15);
        color: #1e293b;
      }

      [data-theme="light"] .select-dropdown {
        background: rgba(255, 255, 255, 0.98);
        border-color: rgba(0, 0, 0, 0.1);
      }

      [data-theme="light"] .select-option {
        color: #1e293b;
      }

      [data-theme="light"] .select-option:hover,
      [data-theme="light"] .select-option.is-highlighted {
        background: rgba(0, 0, 0, 0.05);
      }

      /* Sizes */
      .select-small .select-trigger {
        padding: 0.5rem 0.75rem;
        font-size: var(--font-size-sm, 0.875rem);
      }

      .select-large .select-trigger {
        padding: 1rem 1.25rem;
        font-size: var(--font-size-lg, 1.125rem);
      }
    `;
    document.head.appendChild(styles);
  }

  /**
   * Render the select component
   * @private
   */
  _render() {
    this.wrapper = document.createElement('div');
    this.wrapper.className = `select-wrapper select-${this.size} ${this.className}`.trim();

    // Label
    if (this.label) {
      const label = document.createElement('label');
      label.className = 'select-label';
      label.htmlFor = this.id;
      label.innerHTML = `
        ${escapeHtml(this.label)}
        ${this.required ? '<span class="select-required" aria-hidden="true">*</span>' : ''}
      `;
      this.wrapper.appendChild(label);
    }

    // Trigger button
    this.trigger = document.createElement('button');
    this.trigger.type = 'button';
    this.trigger.id = this.id;
    this.trigger.className = `select-trigger ${this.error ? 'is-invalid' : ''}`;
    this.trigger.disabled = this.disabled;
    this.trigger.setAttribute('aria-haspopup', 'listbox');
    this.trigger.setAttribute('aria-expanded', 'false');

    this._updateTrigger();
    this.wrapper.appendChild(this.trigger);

    // Hidden input for form submission
    this.hiddenInput = document.createElement('input');
    this.hiddenInput.type = 'hidden';
    this.hiddenInput.name = this.name;
    this.hiddenInput.value = this.multiple ? JSON.stringify(this.value) : (this.value || '');
    this.wrapper.appendChild(this.hiddenInput);

    // Dropdown
    this.dropdown = document.createElement('div');
    this.dropdown.className = 'select-dropdown';
    this.dropdown.setAttribute('role', 'listbox');
    this._renderDropdown();
    this.wrapper.appendChild(this.dropdown);

    // Help/Error text
    if (this.help && !this.error) {
      const helpEl = document.createElement('span');
      helpEl.className = 'select-help';
      helpEl.textContent = this.help;
      this.wrapper.appendChild(helpEl);
    }

    if (this.error) {
      const errorEl = document.createElement('span');
      errorEl.className = 'select-error';
      errorEl.setAttribute('role', 'alert');
      errorEl.textContent = this.error;
      this.wrapper.appendChild(errorEl);
    }

    this.container.appendChild(this.wrapper);
  }

  /**
   * Update trigger content
   * @private
   */
  _updateTrigger() {
    const selectedOptions = this._getSelectedOptions();

    let valueHtml = '';
    if (selectedOptions.length === 0) {
      valueHtml = `<span class="select-value select-placeholder">${escapeHtml(this.placeholder)}</span>`;
    } else if (this.multiple) {
      valueHtml = '<div class="select-tags">';
      selectedOptions.forEach(opt => {
        valueHtml += `
          <span class="select-tag">
            ${escapeHtml(opt.label)}
            <button type="button" class="select-tag-remove" data-value="${escapeHtml(String(opt.value))}" aria-label="削除">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </span>
        `;
      });
      valueHtml += '</div>';
    } else {
      valueHtml = `<span class="select-value">${escapeHtml(selectedOptions[0].label)}</span>`;
    }

    const clearable = this.clearable && selectedOptions.length > 0 && !this.disabled;

    this.trigger.innerHTML = `
      ${valueHtml}
      <span class="select-icons">
        ${clearable ? `
          <button type="button" class="select-clear" aria-label="クリア">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        ` : ''}
        <span class="select-arrow">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </span>
      </span>
    `;

    // Bind clear button
    const clearBtn = this.trigger.querySelector('.select-clear');
    if (clearBtn) {
      clearBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.clear();
      });
    }

    // Bind tag remove buttons
    this.trigger.querySelectorAll('.select-tag-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const val = btn.dataset.value;
        this._removeValue(val);
      });
    });
  }

  /**
   * Render dropdown content
   * @private
   */
  _renderDropdown() {
    let html = '';

    if (this.searchable) {
      html += `
        <div class="select-search">
          <input type="text" class="select-search-input" placeholder="検索..." aria-label="検索">
        </div>
      `;
    }

    html += '<div class="select-options">';

    if (this.filteredOptions.length === 0) {
      html += '<div class="select-empty">オプションがありません</div>';
    } else {
      // Group options
      const groups = new Map();
      this.filteredOptions.forEach(opt => {
        const group = opt.group || '';
        if (!groups.has(group)) {
          groups.set(group, []);
        }
        groups.get(group).push(opt);
      });

      groups.forEach((options, groupName) => {
        if (groupName) {
          html += `<div class="select-group-label">${escapeHtml(groupName)}</div>`;
        }

        options.forEach((opt, index) => {
          const isSelected = this._isSelected(opt.value);
          const isDisabled = opt.disabled;

          html += `
            <div class="select-option ${isSelected ? 'is-selected' : ''} ${isDisabled ? 'is-disabled' : ''}"
                 role="option"
                 data-value="${escapeHtml(String(opt.value))}"
                 data-index="${index}"
                 aria-selected="${isSelected}">
              <span class="select-option-check">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </span>
              <span>${escapeHtml(opt.label)}</span>
            </div>
          `;
        });
      });
    }

    html += '</div>';
    this.dropdown.innerHTML = html;

    // Bind search input
    if (this.searchable) {
      this.searchInput = this.dropdown.querySelector('.select-search-input');
      this.searchInput.addEventListener('input', (e) => {
        this._handleSearch(e.target.value);
      });
    }

    // Bind option clicks
    this.dropdown.querySelectorAll('.select-option:not(.is-disabled)').forEach(opt => {
      opt.addEventListener('click', () => {
        const value = opt.dataset.value;
        this._selectValue(value);
      });
    });
  }

  /**
   * Get selected options
   * @private
   * @returns {SelectOption[]} Selected options
   */
  _getSelectedOptions() {
    if (this.multiple) {
      return this.options.filter(opt => this.value.includes(opt.value));
    }
    return this.options.filter(opt => opt.value === this.value);
  }

  /**
   * Check if value is selected
   * @private
   * @param {*} value - Value to check
   * @returns {boolean} Is selected
   */
  _isSelected(value) {
    if (this.multiple) {
      return this.value.includes(value);
    }
    return this.value === value;
  }

  /**
   * Select a value
   * @private
   * @param {string} value - Value to select
   */
  _selectValue(value) {
    // Convert value type
    const option = this.options.find(opt => String(opt.value) === value);
    if (!option) return;

    const typedValue = option.value;

    if (this.multiple) {
      if (this.value.includes(typedValue)) {
        this.value = this.value.filter(v => v !== typedValue);
      } else {
        this.value = [...this.value, typedValue];
      }
    } else {
      this.value = typedValue;
      this.close();
    }

    this._update();

    if (this.onChange) {
      this.onChange(this.value, this.multiple ? this._getSelectedOptions() : option);
    }
  }

  /**
   * Remove a value (for multiple)
   * @private
   * @param {string} value - Value to remove
   */
  _removeValue(value) {
    if (!this.multiple) return;

    const option = this.options.find(opt => String(opt.value) === value);
    if (!option) return;

    this.value = this.value.filter(v => v !== option.value);
    this._update();

    if (this.onChange) {
      this.onChange(this.value, this._getSelectedOptions());
    }
  }

  /**
   * Handle search input
   * @private
   * @param {string} query - Search query
   */
  _handleSearch(query) {
    this.searchQuery = query.toLowerCase();

    if (this.onSearch) {
      this.onSearch(query);
    }

    this.filteredOptions = this.options.filter(opt =>
      opt.label.toLowerCase().includes(this.searchQuery)
    );

    this._renderDropdown();
  }

  /**
   * Update component state
   * @private
   */
  _update() {
    this._updateTrigger();
    this._renderDropdown();
    this.hiddenInput.value = this.multiple ? JSON.stringify(this.value) : (this.value || '');
  }

  /**
   * Bind event listeners
   * @private
   */
  _bindEvents() {
    this.trigger.addEventListener('click', (e) => {
      if (e.target.closest('.select-clear') || e.target.closest('.select-tag-remove')) return;
      this.toggle();
    });

    this.trigger.addEventListener('keydown', this._handleKeyDown);
    document.addEventListener('click', this._handleDocumentClick);
  }

  /**
   * Handle document click
   * @private
   * @param {MouseEvent} e - Click event
   */
  _handleDocumentClick(e) {
    if (!this.wrapper.contains(e.target) && this.isOpen) {
      this.close();
    }
  }

  /**
   * Handle keyboard navigation
   * @private
   * @param {KeyboardEvent} e - Keyboard event
   */
  _handleKeyDown(e) {
    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (this.isOpen) {
          if (this.highlightedIndex >= 0) {
            const options = this.dropdown.querySelectorAll('.select-option:not(.is-disabled)');
            const opt = options[this.highlightedIndex];
            if (opt) {
              this._selectValue(opt.dataset.value);
            }
          }
        } else {
          this.open();
        }
        break;

      case 'Escape':
        this.close();
        break;

      case 'ArrowDown':
        e.preventDefault();
        if (!this.isOpen) {
          this.open();
        } else {
          this._highlightNext();
        }
        break;

      case 'ArrowUp':
        e.preventDefault();
        if (this.isOpen) {
          this._highlightPrev();
        }
        break;
    }
  }

  /**
   * Highlight next option
   * @private
   */
  _highlightNext() {
    const options = this.dropdown.querySelectorAll('.select-option:not(.is-disabled)');
    this.highlightedIndex = Math.min(this.highlightedIndex + 1, options.length - 1);
    this._updateHighlight(options);
  }

  /**
   * Highlight previous option
   * @private
   */
  _highlightPrev() {
    const options = this.dropdown.querySelectorAll('.select-option:not(.is-disabled)');
    this.highlightedIndex = Math.max(this.highlightedIndex - 1, 0);
    this._updateHighlight(options);
  }

  /**
   * Update highlight state
   * @private
   * @param {NodeList} options - Option elements
   */
  _updateHighlight(options) {
    options.forEach((opt, i) => {
      opt.classList.toggle('is-highlighted', i === this.highlightedIndex);
      if (i === this.highlightedIndex) {
        opt.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  // Public API

  /**
   * Open dropdown
   */
  open() {
    if (this.disabled) return;

    this.isOpen = true;
    this.trigger.classList.add('is-open');
    this.trigger.setAttribute('aria-expanded', 'true');
    this.dropdown.classList.add('is-open');
    this.highlightedIndex = -1;

    if (this.searchable && this.searchInput) {
      setTimeout(() => this.searchInput.focus(), 50);
    }
  }

  /**
   * Close dropdown
   */
  close() {
    this.isOpen = false;
    this.trigger.classList.remove('is-open');
    this.trigger.setAttribute('aria-expanded', 'false');
    this.dropdown.classList.remove('is-open');

    if (this.searchable) {
      this.searchQuery = '';
      this.filteredOptions = [...this.options];
      this._renderDropdown();
    }
  }

  /**
   * Toggle dropdown
   */
  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  /**
   * Get current value
   * @returns {*} Current value
   */
  getValue() {
    return this.value;
  }

  /**
   * Set value
   * @param {*} value - New value
   */
  setValue(value) {
    this.value = value;
    this._update();
  }

  /**
   * Clear value
   */
  clear() {
    this.value = this.multiple ? [] : null;
    this._update();

    if (this.onChange) {
      this.onChange(this.value, null);
    }
  }

  /**
   * Set options
   * @param {SelectOption[]} options - New options
   */
  setOptions(options) {
    this.options = options;
    this.filteredOptions = [...options];
    this._update();
  }

  /**
   * Set disabled state
   * @param {boolean} disabled - Disabled state
   */
  setDisabled(disabled) {
    this.disabled = disabled;
    this.trigger.disabled = disabled;
    if (disabled) this.close();
  }

  /**
   * Set error message
   * @param {string} error - Error message
   */
  setError(error) {
    this.error = error;
    this.trigger.classList.toggle('is-invalid', !!error);

    const existingError = this.wrapper.querySelector('.select-error');
    if (existingError) existingError.remove();

    if (error) {
      const errorEl = document.createElement('span');
      errorEl.className = 'select-error';
      errorEl.setAttribute('role', 'alert');
      errorEl.textContent = error;
      this.wrapper.appendChild(errorEl);
    }
  }

  /**
   * Destroy component
   */
  destroy() {
    // ✅ AGREGAR: Remover listeners de document
    document.removeEventListener('click', this._handleDocumentClick);

    // ✅ AGREGAR: Remover listeners del trigger
    if (this.trigger) {
      this.trigger.removeEventListener('keydown', this._handleKeyDown);
    }

    // ✅ AGREGAR: Remover elementos del DOM
    if (this.dropdown) {
      this.dropdown.remove();
      this.dropdown = null;
    }

    if (this.wrapper) {
      this.wrapper.remove();
      this.wrapper = null;
    }

    // Limpiar referencias
    this.filteredOptions = [];
    this.selectedOptions = new Set();
    this.searchInput = null;
    this.trigger = null;
    this.hiddenInput = null;
  }
}

export default Select;
