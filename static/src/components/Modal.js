/**
 * Modal Component - YuKyuDATA Design System
 * Accessible modal dialog with glass morphism design
 *
 * @module components/Modal
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * Modal configuration options
 * @typedef {Object} ModalOptions
 * @property {string} [title=''] - Modal title (Japanese supported)
 * @property {string|HTMLElement} [content=''] - Modal body content
 * @property {string} [size='medium'] - Size: 'small' | 'medium' | 'large' | 'fullscreen'
 * @property {boolean} [closable=true] - Allow closing via X button and backdrop
 * @property {boolean} [closeOnEscape=true] - Close on ESC key
 * @property {boolean} [closeOnBackdrop=true] - Close on backdrop click
 * @property {string} [id=''] - Custom ID for the modal
 * @property {string} [className=''] - Additional CSS classes
 * @property {Function} [onOpen] - Callback when modal opens
 * @property {Function} [onClose] - Callback when modal closes
 * @property {Function} [onConfirm] - Callback for confirm button
 * @property {Array} [buttons] - Custom footer buttons
 * @property {string} [ariaLabel] - ARIA label for screen readers
 */

/**
 * Modal component class
 * @class
 */
export class Modal {
  /** @type {Map<string, Modal>} Active modals registry */
  static activeModals = new Map();

  /** @type {number} Z-index counter for stacking */
  static zIndexCounter = 10000;

  /**
   * Create a modal instance
   * @param {ModalOptions} options - Modal configuration
   */
  constructor(options = {}) {
    this.id = options.id || `modal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    this.title = options.title || '';
    this.content = options.content || '';
    this.size = options.size || 'medium';
    this.closable = options.closable !== false;
    this.closeOnEscape = options.closeOnEscape !== false;
    this.closeOnBackdrop = options.closeOnBackdrop !== false;
    this.className = options.className || '';
    this.buttons = options.buttons || [];
    this.ariaLabel = options.ariaLabel || this.title;

    // Callbacks
    this.onOpen = options.onOpen || (() => {});
    this.onClose = options.onClose || (() => {});
    this.onConfirm = options.onConfirm || null;

    // Internal state
    this.element = null;
    this.backdrop = null;
    this.isOpen = false;
    this.previousActiveElement = null;
    this.focusableElements = [];

    // Bound handlers
    this._handleKeyDown = this._handleKeyDown.bind(this);
    this._handleBackdropClick = this._handleBackdropClick.bind(this);
  }

  /**
   * Size mapping to CSS classes and max-widths
   * @private
   */
  static get SIZES() {
    return {
      small: { class: 'modal-sm', maxWidth: '360px' },
      medium: { class: 'modal-md', maxWidth: '480px' },
      large: { class: 'modal-lg', maxWidth: '640px' },
      xlarge: { class: 'modal-xl', maxWidth: '800px' },
      fullscreen: { class: 'modal-fullscreen', maxWidth: '95vw' }
    };
  }

  /**
   * Create the modal DOM structure
   * @private
   * @returns {HTMLElement} Modal element
   */
  _createModalElement() {
    const sizeConfig = Modal.SIZES[this.size] || Modal.SIZES.medium;

    // Create backdrop
    this.backdrop = document.createElement('div');
    this.backdrop.className = 'modal-backdrop';
    this.backdrop.setAttribute('data-modal-id', this.id);

    // Create modal container
    const modal = document.createElement('div');
    modal.id = this.id;
    modal.className = `modal ${sizeConfig.class} ${this.className}`.trim();
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', `${this.id}-title`);
    modal.setAttribute('aria-describedby', `${this.id}-content`);
    if (this.ariaLabel) {
      modal.setAttribute('aria-label', this.ariaLabel);
    }
    modal.style.maxWidth = sizeConfig.maxWidth;
    modal.tabIndex = -1;

    // Header
    const header = document.createElement('div');
    header.className = 'modal-header';

    const titleEl = document.createElement('h2');
    titleEl.id = `${this.id}-title`;
    titleEl.className = 'modal-title';
    titleEl.textContent = this.title;
    header.appendChild(titleEl);

    if (this.closable) {
      const closeBtn = document.createElement('button');
      closeBtn.type = 'button';
      closeBtn.className = 'modal-close';
      closeBtn.setAttribute('aria-label', '閉じる');
      closeBtn.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      `;
      closeBtn.addEventListener('click', () => this.close());
      header.appendChild(closeBtn);
    }

    // Body
    const body = document.createElement('div');
    body.id = `${this.id}-content`;
    body.className = 'modal-body';

    if (typeof this.content === 'string') {
      body.innerHTML = this.content;
    } else if (this.content instanceof HTMLElement) {
      body.appendChild(this.content);
    }

    // Footer (if buttons provided)
    let footer = null;
    if (this.buttons.length > 0 || this.onConfirm) {
      footer = document.createElement('div');
      footer.className = 'modal-footer';

      // Default buttons if onConfirm is set
      if (this.onConfirm && this.buttons.length === 0) {
        this.buttons = [
          { text: 'キャンセル', variant: 'ghost', action: 'cancel' },
          { text: '確認', variant: 'primary', action: 'confirm' }
        ];
      }

      this.buttons.forEach(btn => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `btn btn-${btn.variant || 'ghost'}`;
        button.textContent = btn.text;
        if (btn.disabled) button.disabled = true;

        button.addEventListener('click', () => {
          if (btn.action === 'confirm' && this.onConfirm) {
            this.onConfirm(this);
          } else if (btn.action === 'cancel') {
            this.close();
          } else if (btn.onClick) {
            btn.onClick(this);
          }
        });

        footer.appendChild(button);
      });
    }

    // Assemble modal
    modal.appendChild(header);
    modal.appendChild(body);
    if (footer) modal.appendChild(footer);

    // Add backdrop click handler
    this.backdrop.appendChild(modal);

    return this.backdrop;
  }

  /**
   * Handle keyboard events
   * @private
   * @param {KeyboardEvent} e - Keyboard event
   */
  _handleKeyDown(e) {
    if (e.key === 'Escape' && this.closeOnEscape && this.closable) {
      e.preventDefault();
      this.close();
    }

    // Focus trap
    if (e.key === 'Tab') {
      this._trapFocus(e);
    }
  }

  /**
   * Handle backdrop click
   * @private
   * @param {MouseEvent} e - Click event
   */
  _handleBackdropClick(e) {
    if (e.target === this.backdrop && this.closeOnBackdrop && this.closable) {
      this.close();
    }
  }

  /**
   * Trap focus within modal
   * @private
   * @param {KeyboardEvent} e - Keyboard event
   */
  _trapFocus(e) {
    const modal = this.backdrop.querySelector('.modal');
    this.focusableElements = modal.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    const firstFocusable = this.focusableElements[0];
    const lastFocusable = this.focusableElements[this.focusableElements.length - 1];

    if (e.shiftKey && document.activeElement === firstFocusable) {
      e.preventDefault();
      lastFocusable.focus();
    } else if (!e.shiftKey && document.activeElement === lastFocusable) {
      e.preventDefault();
      firstFocusable.focus();
    }
  }

  /**
   * Inject modal styles if not present
   * @private
   */
  _injectStyles() {
    if (document.getElementById('modal-component-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'modal-component-styles';
    styles.textContent = `
      .modal-backdrop {
        position: fixed;
        inset: 0;
        background: var(--overlay-dark, rgba(2, 6, 23, 0.85));
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: var(--z-modal-backdrop, 9000);
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease, visibility 0.3s ease;
        padding: 1rem;
      }

      .modal-backdrop.active {
        opacity: 1;
        visibility: visible;
      }

      .modal {
        background: var(--modal-content-bg, rgba(15, 15, 15, 0.95));
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--modal-radius, 16px);
        box-shadow: 0 40px 80px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05) inset;
        width: 100%;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        transform: scale(0.9) translateY(20px);
        opacity: 0;
        transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
      }

      .modal-backdrop.active .modal {
        transform: scale(1) translateY(0);
        opacity: 1;
      }

      .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--modal-padding, 1.5rem);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        flex-shrink: 0;
      }

      .modal-title {
        font-size: var(--font-size-xl, 1.25rem);
        font-weight: var(--font-weight-bold, 700);
        color: var(--color-text-primary, #f8fafc);
        margin: 0;
      }

      .modal-close {
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.1);
        border: none;
        border-radius: 10px;
        color: var(--color-text-secondary, #94a3b8);
        cursor: pointer;
        transition: all 0.2s ease;
        flex-shrink: 0;
      }

      .modal-close:hover {
        background: rgba(248, 113, 113, 0.2);
        color: var(--color-danger, #f87171);
      }

      .modal-close:focus {
        outline: var(--focus-outline, 3px solid var(--color-primary));
        outline-offset: var(--focus-outline-offset, 2px);
      }

      .modal-body {
        padding: var(--modal-padding, 1.5rem);
        overflow-y: auto;
        flex: 1;
        color: var(--color-text-secondary, #cbd5e1);
        line-height: 1.6;
      }

      .modal-footer {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 0.75rem;
        padding: var(--modal-padding, 1.5rem);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        flex-shrink: 0;
      }

      /* Size variants */
      .modal-sm { max-width: 360px; }
      .modal-md { max-width: 480px; }
      .modal-lg { max-width: 640px; }
      .modal-xl { max-width: 800px; }
      .modal-fullscreen {
        max-width: 95vw;
        max-height: 95vh;
      }

      /* Light theme */
      [data-theme="light"] .modal-backdrop {
        background: rgba(0, 0, 0, 0.5);
      }

      [data-theme="light"] .modal {
        background: rgba(255, 255, 255, 0.98);
        border-color: rgba(0, 0, 0, 0.1);
        box-shadow: 0 40px 80px rgba(0, 0, 0, 0.2);
      }

      [data-theme="light"] .modal-header,
      [data-theme="light"] .modal-footer {
        border-color: rgba(0, 0, 0, 0.1);
      }

      [data-theme="light"] .modal-title {
        color: var(--color-text-primary, #1e293b);
      }

      [data-theme="light"] .modal-close {
        background: rgba(0, 0, 0, 0.05);
        color: #64748b;
      }

      [data-theme="light"] .modal-close:hover {
        background: rgba(239, 68, 68, 0.1);
        color: #ef4444;
      }

      /* Responsive */
      @media (max-width: 640px) {
        .modal-backdrop {
          padding: 0.5rem;
        }

        .modal {
          max-width: 100% !important;
          max-height: 100vh;
          border-radius: 12px;
        }

        .modal-fullscreen {
          border-radius: 0;
          max-height: 100vh;
        }
      }

      /* Reduced motion */
      @media (prefers-reduced-motion: reduce) {
        .modal-backdrop,
        .modal {
          transition: opacity 0.01ms;
        }
        .modal {
          transform: none;
        }
      }
    `;
    document.head.appendChild(styles);
  }

  /**
   * Open the modal
   * @returns {Modal} Modal instance for chaining
   */
  open() {
    if (this.isOpen) return this;

    this._injectStyles();
    this.element = this._createModalElement();

    // Store previous focus
    this.previousActiveElement = document.activeElement;

    // Set z-index for stacking
    Modal.zIndexCounter += 1;
    this.element.style.zIndex = Modal.zIndexCounter;

    // Add to DOM
    document.body.appendChild(this.element);

    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    // Add event listeners
    document.addEventListener('keydown', this._handleKeyDown);
    this.element.addEventListener('click', this._handleBackdropClick);

    // Trigger open animation
    requestAnimationFrame(() => {
      this.element.classList.add('active');

      // Focus modal
      const modal = this.element.querySelector('.modal');
      modal.focus();
    });

    this.isOpen = true;
    Modal.activeModals.set(this.id, this);

    this.onOpen(this);

    // Dispatch custom event
    this.element.dispatchEvent(new CustomEvent('modal:open', { detail: { modal: this } }));

    return this;
  }

  /**
   * Close the modal
   * @returns {Modal} Modal instance for chaining
   */
  close() {
    if (!this.isOpen) return this;

    // Trigger close animation
    this.element.classList.remove('active');

    // Wait for animation
    setTimeout(() => {
      // Remove event listeners
      document.removeEventListener('keydown', this._handleKeyDown);
      this.element.removeEventListener('click', this._handleBackdropClick);

      // Remove from DOM
      if (this.element.parentNode) {
        this.element.parentNode.removeChild(this.element);
      }

      // Restore body scroll if no other modals
      Modal.activeModals.delete(this.id);
      if (Modal.activeModals.size === 0) {
        document.body.style.overflow = '';
      }

      // Restore focus
      if (this.previousActiveElement) {
        this.previousActiveElement.focus();
      }

      this.isOpen = false;
      this.onClose(this);

      // Dispatch custom event
      document.dispatchEvent(new CustomEvent('modal:close', { detail: { modal: this } }));
    }, 300);

    return this;
  }

  /**
   * Update modal content
   * @param {string|HTMLElement} content - New content
   * @returns {Modal} Modal instance for chaining
   */
  setContent(content) {
    this.content = content;

    if (this.isOpen) {
      const body = this.element.querySelector('.modal-body');
      if (body) {
        if (typeof content === 'string') {
          body.innerHTML = content;
        } else if (content instanceof HTMLElement) {
          body.innerHTML = '';
          body.appendChild(content);
        }
      }
    }

    return this;
  }

  /**
   * Update modal title
   * @param {string} title - New title
   * @returns {Modal} Modal instance for chaining
   */
  setTitle(title) {
    this.title = title;

    if (this.isOpen) {
      const titleEl = this.element.querySelector('.modal-title');
      if (titleEl) {
        titleEl.textContent = title;
      }
    }

    return this;
  }

  /**
   * Add loading state to modal
   * @param {boolean} loading - Loading state
   * @returns {Modal} Modal instance for chaining
   */
  setLoading(loading) {
    if (!this.isOpen) return this;

    const modal = this.element.querySelector('.modal');
    const buttons = modal.querySelectorAll('.modal-footer button');

    if (loading) {
      modal.classList.add('is-loading');
      buttons.forEach(btn => btn.disabled = true);
    } else {
      modal.classList.remove('is-loading');
      buttons.forEach(btn => btn.disabled = false);
    }

    return this;
  }

  /**
   * Destroy modal instance
   */
  destroy() {
    if (this.isOpen) {
      this.close();
    }

    // ✅ AGREGAR: Remover todos los event listeners
    document.removeEventListener('keydown', this._handleKeyDown);

    if (this.element) {
      this.element.removeEventListener('click', this._handleBackdropClick);
      this.element.remove();
      this.element = null;
    }

    if (this.backdrop) {
      this.backdrop.remove();
      this.backdrop = null;
    }

    // Limpiar referencias
    this.previousActiveElement = null;
    this.focusableElements = [];

    // Remover del registry
    Modal.activeModals.delete(this.id);
  }

  // Static factory methods

  /**
   * Create and open a simple alert modal
   * @param {string} message - Alert message
   * @param {string} [title='通知'] - Alert title
   * @returns {Promise<void>} Resolves when closed
   */
  static alert(message, title = '通知') {
    return new Promise(resolve => {
      const modal = new Modal({
        title,
        content: `<p>${escapeHtml(message)}</p>`,
        size: 'small',
        buttons: [
          { text: 'OK', variant: 'primary', onClick: m => { m.close(); resolve(); } }
        ]
      });
      modal.open();
    });
  }

  /**
   * Create and open a confirm dialog
   * @param {string} message - Confirm message
   * @param {string} [title='確認'] - Confirm title
   * @returns {Promise<boolean>} Resolves with true/false
   */
  static confirm(message, title = '確認') {
    return new Promise(resolve => {
      const modal = new Modal({
        title,
        content: `<p>${escapeHtml(message)}</p>`,
        size: 'small',
        closeOnBackdrop: false,
        closeOnEscape: false,
        closable: false,
        buttons: [
          { text: 'キャンセル', variant: 'ghost', onClick: m => { m.close(); resolve(false); } },
          { text: '確認', variant: 'primary', onClick: m => { m.close(); resolve(true); } }
        ]
      });
      modal.open();
    });
  }

  /**
   * Create and open a prompt dialog
   * @param {string} message - Prompt message
   * @param {string} [defaultValue=''] - Default input value
   * @param {string} [title='入力'] - Prompt title
   * @returns {Promise<string|null>} Resolves with input value or null
   */
  static prompt(message, defaultValue = '', title = '入力') {
    return new Promise(resolve => {
      const inputId = `prompt-input-${Date.now()}`;
      const modal = new Modal({
        title,
        content: `
          <p style="margin-bottom: 1rem;">${escapeHtml(message)}</p>
          <input type="text" id="${inputId}" class="input-glass" value="${escapeHtml(defaultValue)}" style="width: 100%;">
        `,
        size: 'small',
        buttons: [
          { text: 'キャンセル', variant: 'ghost', onClick: m => { m.close(); resolve(null); } },
          {
            text: '確認',
            variant: 'primary',
            onClick: m => {
              const input = document.getElementById(inputId);
              m.close();
              resolve(input ? input.value : '');
            }
          }
        ],
        onOpen: () => {
          setTimeout(() => {
            const input = document.getElementById(inputId);
            if (input) input.focus();
          }, 100);
        }
      });
      modal.open();
    });
  }

  /**
   * Close all active modals
   */
  static closeAll() {
    Modal.activeModals.forEach(modal => modal.close());
  }
}

export default Modal;
