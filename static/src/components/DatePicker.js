/**
 * DatePicker Component - YuKyuDATA Design System
 * Japanese-localized date picker with fiscal year support
 *
 * @module components/DatePicker
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * DatePicker options
 * @typedef {Object} DatePickerOptions
 * @property {string} [format='YYYY-MM-DD'] - Date format
 * @property {string} [locale='ja-JP'] - Locale for formatting
 * @property {boolean} [fiscalYear=false] - Use fiscal year (starts day 21)
 * @property {Date|string} [minDate] - Minimum selectable date
 * @property {Date|string} [maxDate] - Maximum selectable date
 * @property {Date|string} [value] - Initial value
 * @property {boolean} [disabled=false] - Disabled state
 * @property {boolean} [required=false] - Required field
 * @property {boolean} [clearable=true] - Show clear button
 * @property {string} [placeholder='日付を選択'] - Placeholder text
 * @property {Function} [onChange] - Change callback (date, formatted)
 * @property {Array<Date>} [disabledDates=[]] - Specific disabled dates
 * @property {Function} [isDateDisabled] - Custom date disable function
 * @property {boolean} [showWeekNumbers=false] - Show week numbers
 * @property {string} [className=''] - Additional CSS classes
 */

/**
 * DatePicker component class
 * @class
 */
export class DatePicker {
  /**
   * Japanese weekday names
   */
  static WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土'];

  /**
   * Japanese month names
   */
  static MONTHS = [
    '1月', '2月', '3月', '4月', '5月', '6月',
    '7月', '8月', '9月', '10月', '11月', '12月'
  ];

  /**
   * Create a DatePicker instance
   * @param {HTMLInputElement|string} input - Input element or selector
   * @param {DatePickerOptions} options - DatePicker configuration
   */
  constructor(input, options = {}) {
    this.input = typeof input === 'string'
      ? document.querySelector(input)
      : input;

    if (!this.input) {
      throw new Error('DatePicker: Input element not found');
    }

    // Configuration
    this.format = options.format || 'YYYY-MM-DD';
    this.locale = options.locale || 'ja-JP';
    this.fiscalYear = options.fiscalYear || false;
    this.minDate = options.minDate ? this._parseDate(options.minDate) : null;
    this.maxDate = options.maxDate ? this._parseDate(options.maxDate) : null;
    this.disabled = options.disabled || false;
    this.required = options.required || false;
    this.clearable = options.clearable !== false;
    this.placeholder = options.placeholder || '日付を選択';
    this.disabledDates = (options.disabledDates || []).map(d => this._parseDate(d));
    this.isDateDisabled = options.isDateDisabled || null;
    this.showWeekNumbers = options.showWeekNumbers || false;
    this.className = options.className || '';

    // Callbacks
    this.onChange = options.onChange || null;

    // State
    this.value = options.value ? this._parseDate(options.value) : null;
    this.viewDate = new Date(this.value || new Date());
    this.isOpen = false;

    // Element references
    this.container = null;
    this.calendar = null;

    // Bound handlers
    this._handleInputClick = this._handleInputClick.bind(this);
    this._handleDocumentClick = this._handleDocumentClick.bind(this);
    this._handleKeyDown = this._handleKeyDown.bind(this);

    // Initialize
    this._injectStyles();
    this._createWrapper();
    this._bindEvents();

    // Set initial value
    if (this.value) {
      this.input.value = this._formatDate(this.value);
    }
  }

  /**
   * Parse date from various formats
   * @private
   * @param {Date|string} date - Date to parse
   * @returns {Date|null} Parsed date
   */
  _parseDate(date) {
    if (!date) return null;
    if (date instanceof Date) return new Date(date);
    const parsed = new Date(date);
    return isNaN(parsed.getTime()) ? null : parsed;
  }

  /**
   * Format date according to format string
   * @private
   * @param {Date} date - Date to format
   * @returns {string} Formatted date
   */
  _formatDate(date) {
    if (!date) return '';

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    return this.format
      .replace('YYYY', year)
      .replace('MM', month)
      .replace('DD', day);
  }

  /**
   * Format for display (Japanese format)
   * @private
   * @param {Date} date - Date to format
   * @returns {string} Display formatted date
   */
  _formatDisplay(date) {
    if (!date) return '';

    return new Intl.DateTimeFormat(this.locale, {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }).format(date);
  }

  /**
   * Check if a date is disabled
   * @private
   * @param {Date} date - Date to check
   * @returns {boolean} Is disabled
   */
  _isDisabled(date) {
    if (this.minDate && date < this.minDate) return true;
    if (this.maxDate && date > this.maxDate) return true;

    // Check specific disabled dates
    const dateStr = this._formatDate(date);
    for (const disabled of this.disabledDates) {
      if (this._formatDate(disabled) === dateStr) return true;
    }

    // Custom disable function
    if (this.isDateDisabled && this.isDateDisabled(date)) return true;

    return false;
  }

  /**
   * Check if date is today
   * @private
   * @param {Date} date - Date to check
   * @returns {boolean} Is today
   */
  _isToday(date) {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  }

  /**
   * Check if date is selected
   * @private
   * @param {Date} date - Date to check
   * @returns {boolean} Is selected
   */
  _isSelected(date) {
    if (!this.value) return false;
    return date.toDateString() === this.value.toDateString();
  }

  /**
   * Get fiscal year period for a date
   * @private
   * @param {Date} date - Date to check
   * @returns {Object} Fiscal year info { year, startDate, endDate }
   */
  _getFiscalYear(date) {
    const year = date.getFullYear();
    const month = date.getMonth();
    const day = date.getDate();

    // Fiscal year starts on the 21st
    let fiscalYear;
    if (month === 0 && day < 21) {
      // January before 21st belongs to previous fiscal year
      fiscalYear = year - 1;
    } else if (month >= 3 && day >= 21) {
      // April 21st onwards is new fiscal year
      fiscalYear = year;
    } else if (month < 3 || (month === 3 && day < 21)) {
      // January 21st to April 20th
      fiscalYear = year - 1;
    } else {
      fiscalYear = year;
    }

    return {
      year: fiscalYear,
      startDate: new Date(fiscalYear, 3, 21), // April 21
      endDate: new Date(fiscalYear + 1, 3, 20) // April 20 next year
    };
  }

  /**
   * Inject datepicker styles
   * @private
   */
  _injectStyles() {
    if (document.getElementById('datepicker-component-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'datepicker-component-styles';
    styles.textContent = `
      .datepicker-wrapper {
        position: relative;
        display: inline-block;
        width: 100%;
      }

      .datepicker-input-container {
        position: relative;
        display: flex;
        align-items: center;
      }

      .datepicker-input {
        width: 100%;
        padding: var(--input-padding-y, 0.75rem) var(--input-padding-x, 1rem);
        padding-right: 2.5rem;
        background: var(--input-bg, rgba(0, 0, 0, 0.2));
        border: var(--input-border, 1px solid rgba(255, 255, 255, 0.1));
        border-radius: var(--input-radius, 12px);
        color: var(--color-text-primary, #f8fafc);
        font-family: var(--font-family-main);
        font-size: var(--font-size-base, 1rem);
        transition: all var(--transition-smooth, 0.2s ease);
        cursor: pointer;
        outline: none;
      }

      .datepicker-input:hover {
        border-color: rgba(255, 255, 255, 0.2);
      }

      .datepicker-input:focus {
        border-color: var(--color-primary, #06b6d4);
        box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.15);
      }

      .datepicker-input:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .datepicker-icon {
        position: absolute;
        right: 12px;
        top: 50%;
        transform: translateY(-50%);
        width: 20px;
        height: 20px;
        color: var(--color-text-muted, #64748b);
        pointer-events: none;
      }

      .datepicker-clear {
        position: absolute;
        right: 36px;
        top: 50%;
        transform: translateY(-50%);
        width: 20px;
        height: 20px;
        padding: 0;
        background: none;
        border: none;
        color: var(--color-text-muted, #64748b);
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.2s ease;
      }

      .datepicker-wrapper:hover .datepicker-clear,
      .datepicker-input:focus ~ .datepicker-clear {
        opacity: 1;
      }

      .datepicker-clear:hover {
        color: var(--color-danger, #f87171);
      }

      .datepicker-calendar {
        position: absolute;
        top: calc(100% + 8px);
        left: 0;
        z-index: 1000;
        background: var(--color-bg-card, rgba(15, 15, 15, 0.95));
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        padding: 16px;
        min-width: 280px;
        opacity: 0;
        visibility: hidden;
        transform: translateY(-10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }

      .datepicker-calendar.open {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
      }

      .datepicker-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
      }

      .datepicker-nav-btn {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: var(--color-text-secondary, #94a3b8);
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .datepicker-nav-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        color: var(--color-text-primary, #f8fafc);
      }

      .datepicker-nav-btn:focus {
        outline: var(--focus-outline, 3px solid var(--color-primary));
        outline-offset: 2px;
      }

      .datepicker-title {
        font-size: var(--font-size-base, 1rem);
        font-weight: 600;
        color: var(--color-text-primary, #f8fafc);
      }

      .datepicker-weekdays {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
        margin-bottom: 8px;
      }

      .datepicker-weekday {
        font-size: var(--font-size-xs, 0.75rem);
        font-weight: 600;
        color: var(--color-text-muted, #64748b);
        text-align: center;
        padding: 8px 0;
      }

      .datepicker-weekday:first-child {
        color: var(--color-danger, #f87171);
      }

      .datepicker-weekday:last-child {
        color: var(--color-info, #38bdf8);
      }

      .datepicker-days {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
      }

      .datepicker-day {
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: var(--font-size-sm, 0.875rem);
        color: var(--color-text-primary, #f8fafc);
        background: transparent;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .datepicker-day:hover:not(.disabled):not(.selected) {
        background: rgba(255, 255, 255, 0.1);
      }

      .datepicker-day:focus {
        outline: var(--focus-outline, 3px solid var(--color-primary));
        outline-offset: -2px;
      }

      .datepicker-day.other-month {
        color: var(--color-text-muted, #64748b);
        opacity: 0.5;
      }

      .datepicker-day.today {
        border: 2px solid var(--color-primary, #06b6d4);
      }

      .datepicker-day.selected {
        background: linear-gradient(135deg, var(--color-primary, #06b6d4), var(--color-secondary, #0891b2));
        color: #000;
        font-weight: 600;
      }

      .datepicker-day.disabled {
        color: var(--color-text-muted, #64748b);
        opacity: 0.3;
        cursor: not-allowed;
      }

      .datepicker-day.sunday {
        color: var(--color-danger, #f87171);
      }

      .datepicker-day.saturday {
        color: var(--color-info, #38bdf8);
      }

      .datepicker-day.selected.sunday,
      .datepicker-day.selected.saturday {
        color: #000;
      }

      .datepicker-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
      }

      .datepicker-today-btn {
        padding: 8px 16px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: var(--color-text-secondary, #94a3b8);
        font-size: var(--font-size-sm, 0.875rem);
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .datepicker-today-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        color: var(--color-text-primary, #f8fafc);
      }

      .datepicker-today-btn:focus {
        outline: var(--focus-outline, 3px solid var(--color-primary));
        outline-offset: 2px;
      }

      /* Light theme */
      [data-theme="light"] .datepicker-input {
        background: rgba(255, 255, 255, 0.9);
        border-color: rgba(0, 0, 0, 0.15);
        color: #1e293b;
      }

      [data-theme="light"] .datepicker-calendar {
        background: rgba(255, 255, 255, 0.98);
        border-color: rgba(0, 0, 0, 0.1);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
      }

      [data-theme="light"] .datepicker-day {
        color: #1e293b;
      }

      [data-theme="light"] .datepicker-day:hover:not(.disabled):not(.selected) {
        background: rgba(0, 0, 0, 0.05);
      }

      [data-theme="light"] .datepicker-nav-btn,
      [data-theme="light"] .datepicker-today-btn {
        background: rgba(0, 0, 0, 0.05);
        border-color: rgba(0, 0, 0, 0.1);
      }

      /* Responsive */
      @media (max-width: 640px) {
        .datepicker-calendar {
          position: fixed;
          top: auto;
          bottom: 0;
          left: 0;
          right: 0;
          border-radius: 16px 16px 0 0;
          padding: 20px;
        }
      }

      /* Reduced motion */
      @media (prefers-reduced-motion: reduce) {
        .datepicker-calendar {
          transition: opacity 0.01ms;
          transform: none;
        }
      }
    `;
    document.head.appendChild(styles);
  }

  /**
   * Create wrapper structure
   * @private
   */
  _createWrapper() {
    // Create wrapper
    this.container = document.createElement('div');
    this.container.className = `datepicker-wrapper ${this.className}`.trim();

    // Wrap input
    this.input.parentNode.insertBefore(this.container, this.input);

    const inputContainer = document.createElement('div');
    inputContainer.className = 'datepicker-input-container';

    // Move input
    this.input.classList.add('datepicker-input');
    this.input.setAttribute('readonly', 'readonly');
    this.input.setAttribute('placeholder', this.placeholder);
    if (this.required) {
      this.input.setAttribute('required', 'required');
      this.input.setAttribute('aria-required', 'true');
    }
    if (this.disabled) {
      this.input.setAttribute('disabled', 'disabled');
    }

    inputContainer.appendChild(this.input);

    // Clear button
    if (this.clearable) {
      const clearBtn = document.createElement('button');
      clearBtn.type = 'button';
      clearBtn.className = 'datepicker-clear';
      clearBtn.setAttribute('aria-label', 'クリア');
      clearBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>`;
      clearBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.clear();
      });
      inputContainer.appendChild(clearBtn);
    }

    // Calendar icon
    const icon = document.createElement('span');
    icon.className = 'datepicker-icon';
    icon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <line x1="8" y1="2" x2="8" y2="6"/>
      <line x1="3" y1="10" x2="21" y2="10"/>
    </svg>`;
    inputContainer.appendChild(icon);

    this.container.appendChild(inputContainer);

    // Create calendar dropdown
    this._createCalendar();
  }

  /**
   * Create calendar element
   * @private
   */
  _createCalendar() {
    this.calendar = document.createElement('div');
    this.calendar.className = 'datepicker-calendar';
    this.calendar.setAttribute('role', 'dialog');
    this.calendar.setAttribute('aria-label', 'カレンダー');
    this.container.appendChild(this.calendar);

    this._renderCalendar();
  }

  /**
   * Render calendar content
   * @private
   */
  _renderCalendar() {
    const year = this.viewDate.getFullYear();
    const month = this.viewDate.getMonth();

    // Header
    let html = `
      <div class="datepicker-header">
        <button type="button" class="datepicker-nav-btn" data-action="prev-month" aria-label="前月">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <span class="datepicker-title">${year}年 ${DatePicker.MONTHS[month]}</span>
        <button type="button" class="datepicker-nav-btn" data-action="next-month" aria-label="来月">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>
    `;

    // Weekdays
    html += '<div class="datepicker-weekdays">';
    DatePicker.WEEKDAYS.forEach(day => {
      html += `<span class="datepicker-weekday">${day}</span>`;
    });
    html += '</div>';

    // Days grid
    html += '<div class="datepicker-days">';

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPadding = firstDay.getDay();
    const daysInMonth = lastDay.getDate();

    // Previous month padding
    const prevMonth = new Date(year, month, 0);
    for (let i = startPadding - 1; i >= 0; i--) {
      const day = prevMonth.getDate() - i;
      const date = new Date(year, month - 1, day);
      html += this._renderDay(date, true);
    }

    // Current month
    for (let i = 1; i <= daysInMonth; i++) {
      const date = new Date(year, month, i);
      html += this._renderDay(date, false);
    }

    // Next month padding
    const endPadding = 42 - (startPadding + daysInMonth);
    for (let i = 1; i <= endPadding; i++) {
      const date = new Date(year, month + 1, i);
      html += this._renderDay(date, true);
    }

    html += '</div>';

    // Footer
    html += `
      <div class="datepicker-footer">
        <button type="button" class="datepicker-today-btn" data-action="today">今日</button>
        ${this.fiscalYear ? `<span style="font-size: 0.75rem; color: var(--color-text-muted);">年度: ${this._getFiscalYear(new Date()).year}</span>` : ''}
      </div>
    `;

    this.calendar.innerHTML = html;
    this._bindCalendarEvents();
  }

  /**
   * Render a single day cell
   * @private
   * @param {Date} date - Date to render
   * @param {boolean} otherMonth - Is from other month
   * @returns {string} Day HTML
   */
  _renderDay(date, otherMonth) {
    const dayOfWeek = date.getDay();
    const isDisabled = this._isDisabled(date);
    const isToday = this._isToday(date);
    const isSelected = this._isSelected(date);

    const classes = [
      'datepicker-day',
      otherMonth ? 'other-month' : '',
      isDisabled ? 'disabled' : '',
      isToday ? 'today' : '',
      isSelected ? 'selected' : '',
      dayOfWeek === 0 ? 'sunday' : '',
      dayOfWeek === 6 ? 'saturday' : ''
    ].filter(Boolean).join(' ');

    return `
      <button type="button"
              class="${classes}"
              data-date="${this._formatDate(date)}"
              ${isDisabled ? 'disabled' : ''}
              tabindex="${isSelected ? '0' : '-1'}">
        ${date.getDate()}
      </button>
    `;
  }

  /**
   * Bind calendar event listeners
   * @private
   */
  _bindCalendarEvents() {
    // Navigation
    this.calendar.querySelectorAll('.datepicker-nav-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const action = btn.dataset.action;
        if (action === 'prev-month') {
          this.viewDate.setMonth(this.viewDate.getMonth() - 1);
        } else if (action === 'next-month') {
          this.viewDate.setMonth(this.viewDate.getMonth() + 1);
        }
        this._renderCalendar();
      });
    });

    // Day selection
    this.calendar.querySelectorAll('.datepicker-day:not(.disabled)').forEach(day => {
      day.addEventListener('click', (e) => {
        e.stopPropagation();
        const dateStr = day.dataset.date;
        this.setValue(dateStr);
        this.close();
      });
    });

    // Today button
    const todayBtn = this.calendar.querySelector('[data-action="today"]');
    if (todayBtn) {
      todayBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const today = new Date();
        if (!this._isDisabled(today)) {
          this.setValue(today);
          this.close();
        } else {
          this.viewDate = new Date(today);
          this._renderCalendar();
        }
      });
    }
  }

  /**
   * Bind main event listeners
   * @private
   */
  _bindEvents() {
    this.input.addEventListener('click', this._handleInputClick);
    this.input.addEventListener('keydown', this._handleKeyDown);
    document.addEventListener('click', this._handleDocumentClick);
  }

  /**
   * Handle input click
   * @private
   */
  _handleInputClick(e) {
    e.stopPropagation();
    if (!this.disabled) {
      this.toggle();
    }
  }

  /**
   * Handle document click (close on outside click)
   * @private
   */
  _handleDocumentClick(e) {
    if (!this.container.contains(e.target) && this.isOpen) {
      this.close();
    }
  }

  /**
   * Handle keyboard navigation
   * @private
   * @param {KeyboardEvent} e - Keyboard event
   */
  _handleKeyDown(e) {
    if (e.key === 'Escape' && this.isOpen) {
      this.close();
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      this.toggle();
    }
  }

  // Public API

  /**
   * Open calendar
   */
  open() {
    if (this.disabled) return;

    this.isOpen = true;
    this.calendar.classList.add('open');
    this.input.setAttribute('aria-expanded', 'true');
  }

  /**
   * Close calendar
   */
  close() {
    this.isOpen = false;
    this.calendar.classList.remove('open');
    this.input.setAttribute('aria-expanded', 'false');
  }

  /**
   * Toggle calendar
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
   * @returns {Date|null} Current date value
   */
  getValue() {
    return this.value;
  }

  /**
   * Get formatted value
   * @returns {string} Formatted date string
   */
  getFormattedValue() {
    return this._formatDate(this.value);
  }

  /**
   * Set value
   * @param {Date|string} date - New date value
   */
  setValue(date) {
    const parsedDate = this._parseDate(date);

    if (parsedDate && !this._isDisabled(parsedDate)) {
      this.value = parsedDate;
      this.viewDate = new Date(parsedDate);
      this.input.value = this._formatDate(parsedDate);

      if (this.onChange) {
        this.onChange(this.value, this._formatDate(this.value));
      }

      this._renderCalendar();
    }
  }

  /**
   * Clear value
   */
  clear() {
    this.value = null;
    this.input.value = '';

    if (this.onChange) {
      this.onChange(null, '');
    }

    this._renderCalendar();
  }

  /**
   * Set disabled state
   * @param {boolean} disabled - Disabled state
   */
  setDisabled(disabled) {
    this.disabled = disabled;
    this.input.disabled = disabled;
    if (disabled) {
      this.close();
    }
  }

  /**
   * Destroy datepicker
   */
  destroy() {
    document.removeEventListener('click', this._handleDocumentClick);
    this.input.removeEventListener('click', this._handleInputClick);
    this.input.removeEventListener('keydown', this._handleKeyDown);

    // Restore input
    this.input.classList.remove('datepicker-input');
    this.input.removeAttribute('readonly');
    this.container.parentNode.insertBefore(this.input, this.container);
    this.container.remove();
  }
}

export default DatePicker;
