/**
 * Alert Component - YuKyuDATA Design System
 * Toast notifications and confirmation dialogs
 *
 * @module components/Alert
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * Toast options
 * @typedef {Object} ToastOptions
 * @property {string} message - Toast message
 * @property {string} [title] - Toast title
 * @property {string} [type='info'] - Type: success, error, warning, info
 * @property {number} [duration=4000] - Auto-dismiss duration (ms), 0 for persistent
 * @property {boolean} [closable=true] - Show close button
 * @property {string} [position='top-right'] - Position: top-right, top-left, bottom-right, bottom-left, top-center, bottom-center
 * @property {Function} [onClose] - Close callback
 * @property {Object} [action] - Action button { text, onClick }
 */

/**
 * Confirm dialog options
 * @typedef {Object} ConfirmOptions
 * @property {string} message - Dialog message
 * @property {string} [title] - Dialog title
 * @property {string} [type='warning'] - Type: info, warning, danger
 * @property {string} [confirmText='確認'] - Confirm button text
 * @property {string} [cancelText='キャンセル'] - Cancel button text
 * @property {string} [confirmVariant='primary'] - Confirm button variant
 * @property {boolean} [dangerous=false] - Mark as dangerous action
 */

/**
 * Alert class with static toast and dialog methods
 * @class
 */
export class Alert {
  /** @type {Map<string, HTMLElement>} Active toast containers */
  static containers = new Map();

  /** @type {Map<string, HTMLElement>} Active toasts */
  static activeToasts = new Map();

  /**
   * Toast icons SVG
   * @private
   */
  static ICONS = {
    success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
      <polyline points="22 4 12 14.01 9 11.01"/>
    </svg>`,
    error: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="15" y1="9" x2="9" y2="15"/>
      <line x1="9" y1="9" x2="15" y2="15"/>
    </svg>`,
    warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>`,
    info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="16" x2="12" y2="12"/>
      <line x1="12" y1="8" x2="12.01" y2="8"/>
    </svg>`
  };

  /**
   * Inject alert styles
   * @private
   */
  static _injectStyles() {
    if (document.getElementById('alert-component-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'alert-component-styles';
    styles.textContent = `
      /* Toast Container */
      .toast-container {
        position: fixed;
        z-index: var(--z-toast, 10000);
        display: flex;
        flex-direction: column;
        gap: 12px;
        pointer-events: none;
        padding: 24px;
        max-width: 420px;
        width: 100%;
      }

      .toast-container.top-right {
        top: 0;
        right: 0;
      }

      .toast-container.top-left {
        top: 0;
        left: 0;
      }

      .toast-container.bottom-right {
        bottom: 0;
        right: 0;
      }

      .toast-container.bottom-left {
        bottom: 0;
        left: 0;
      }

      .toast-container.top-center {
        top: 0;
        left: 50%;
        transform: translateX(-50%);
      }

      .toast-container.bottom-center {
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
      }

      /* Toast */
      .toast {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 16px 20px;
        background: rgba(15, 15, 15, 0.95);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05) inset;
        transform: translateX(120%);
        opacity: 0;
        pointer-events: auto;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        position: relative;
        overflow: hidden;
      }

      .toast-container.top-left .toast,
      .toast-container.bottom-left .toast {
        transform: translateX(-120%);
      }

      .toast-container.top-center .toast,
      .toast-container.bottom-center .toast {
        transform: translateY(-30px);
      }

      .toast.show {
        transform: translateX(0) translateY(0);
        opacity: 1;
      }

      .toast.hiding {
        transform: translateX(120%);
        opacity: 0;
      }

      .toast-container.top-left .toast.hiding,
      .toast-container.bottom-left .toast.hiding {
        transform: translateX(-120%);
      }

      .toast-container.top-center .toast.hiding,
      .toast-container.bottom-center .toast.hiding {
        transform: translateY(-30px);
      }

      /* Toast Icon */
      .toast-icon {
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        flex-shrink: 0;
        padding: 4px;
      }

      .toast-icon svg {
        width: 100%;
        height: 100%;
      }

      /* Toast Content */
      .toast-content {
        flex: 1;
        min-width: 0;
      }

      .toast-title {
        font-weight: 600;
        font-size: 0.95rem;
        color: #ffffff;
        margin-bottom: 2px;
      }

      .toast-message {
        font-size: 0.85rem;
        color: #94a3b8;
        line-height: 1.4;
        word-break: break-word;
      }

      /* Toast Close */
      .toast-close {
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.1);
        border: none;
        border-radius: 8px;
        color: #94a3b8;
        cursor: pointer;
        transition: all 0.2s ease;
        flex-shrink: 0;
        margin-top: -4px;
        margin-right: -4px;
      }

      .toast-close:hover {
        background: rgba(255, 255, 255, 0.15);
        color: #ffffff;
      }

      .toast-close:focus-visible {
        outline: var(--focus-outline, 3px solid var(--color-primary));
        outline-offset: 2px;
      }

      .toast-close svg {
        width: 14px;
        height: 14px;
      }

      /* Toast Action */
      .toast-action {
        margin-top: 8px;
      }

      .toast-action-btn {
        padding: 6px 12px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 6px;
        color: #f8fafc;
        font-size: 0.8rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .toast-action-btn:hover {
        background: rgba(255, 255, 255, 0.15);
        border-color: rgba(255, 255, 255, 0.3);
      }

      /* Toast Progress */
      .toast-progress {
        position: absolute;
        bottom: 0;
        left: 0;
        height: 3px;
        border-radius: 0 0 16px 16px;
        animation: toast-progress-anim linear forwards;
      }

      @keyframes toast-progress-anim {
        from { width: 100%; }
        to { width: 0%; }
      }

      /* Toast Types */
      .toast.success {
        border-color: rgba(52, 211, 153, 0.3);
      }

      .toast.success .toast-icon {
        background: rgba(52, 211, 153, 0.2);
        color: #34d399;
      }

      .toast.success .toast-progress {
        background: linear-gradient(90deg, #34d399, #10b981);
      }

      .toast.error {
        border-color: rgba(248, 113, 113, 0.3);
      }

      .toast.error .toast-icon {
        background: rgba(248, 113, 113, 0.2);
        color: #f87171;
      }

      .toast.error .toast-progress {
        background: linear-gradient(90deg, #f87171, #ef4444);
      }

      .toast.warning {
        border-color: rgba(251, 191, 36, 0.3);
      }

      .toast.warning .toast-icon {
        background: rgba(251, 191, 36, 0.2);
        color: #fbbf24;
      }

      .toast.warning .toast-progress {
        background: linear-gradient(90deg, #fbbf24, #f59e0b);
      }

      .toast.info {
        border-color: rgba(37, 99, 235, 0.3);
      }

      .toast.info .toast-icon {
        background: rgba(37, 99, 235, 0.2);
        color: #2563eb;
      }

      .toast.info .toast-progress {
        background: linear-gradient(90deg, #2563eb, #1d4ed8);
      }

      /* Light theme */
      [data-theme="light"] .toast {
        background: rgba(255, 255, 255, 0.98);
        border-color: rgba(0, 0, 0, 0.1);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
      }

      [data-theme="light"] .toast-title {
        color: #1e293b;
      }

      [data-theme="light"] .toast-message {
        color: #64748b;
      }

      [data-theme="light"] .toast-close {
        background: rgba(0, 0, 0, 0.05);
        color: #64748b;
      }

      [data-theme="light"] .toast-close:hover {
        background: rgba(0, 0, 0, 0.1);
        color: #1e293b;
      }

      /* Confirm Dialog */
      .confirm-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        z-index: 10001;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        padding: 1rem;
      }

      .confirm-overlay.active {
        opacity: 1;
        visibility: visible;
      }

      .confirm-dialog {
        background: rgba(15, 15, 15, 0.98);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 40px 80px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05) inset;
        width: 90%;
        max-width: 420px;
        transform: scale(0.9) translateY(20px);
        opacity: 0;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        overflow: hidden;
      }

      .confirm-overlay.active .confirm-dialog {
        transform: scale(1) translateY(0);
        opacity: 1;
      }

      .confirm-header {
        padding: 24px 24px 16px;
        display: flex;
        align-items: flex-start;
        gap: 16px;
      }

      .confirm-icon {
        width: 48px;
        height: 48px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }

      .confirm-icon svg {
        width: 24px;
        height: 24px;
      }

      .confirm-icon.info {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.2), rgba(8, 145, 178, 0.1));
        color: #2563eb;
      }

      .confirm-icon.warning {
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.1));
        color: #fbbf24;
      }

      .confirm-icon.danger {
        background: linear-gradient(135deg, rgba(248, 113, 113, 0.2), rgba(239, 68, 68, 0.1));
        color: #f87171;
      }

      .confirm-header-text h3 {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0 0 4px 0;
      }

      .confirm-header-text p {
        font-size: 0.9rem;
        color: #94a3b8;
        line-height: 1.5;
        margin: 0;
      }

      .confirm-footer {
        padding: 16px 24px 24px;
        display: flex;
        gap: 12px;
        justify-content: flex-end;
      }

      .confirm-btn {
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .confirm-btn:focus-visible {
        outline: var(--focus-outline, 3px solid var(--color-primary));
        outline-offset: 2px;
      }

      .confirm-btn-cancel {
        background: rgba(255, 255, 255, 0.1);
        color: #94a3b8;
      }

      .confirm-btn-cancel:hover {
        background: rgba(255, 255, 255, 0.15);
        color: #ffffff;
      }

      .confirm-btn-confirm {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: #000000;
      }

      .confirm-btn-confirm:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(37, 99, 235, 0.4);
      }

      .confirm-btn-danger {
        background: linear-gradient(135deg, #f87171, #ef4444);
        color: #ffffff;
      }

      .confirm-btn-danger:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(248, 113, 113, 0.4);
      }

      /* Light theme confirm */
      [data-theme="light"] .confirm-dialog {
        background: rgba(255, 255, 255, 0.98);
        border-color: rgba(0, 0, 0, 0.1);
      }

      [data-theme="light"] .confirm-header-text h3 {
        color: #1e293b;
      }

      [data-theme="light"] .confirm-header-text p {
        color: #64748b;
      }

      [data-theme="light"] .confirm-btn-cancel {
        background: rgba(0, 0, 0, 0.05);
        color: #64748b;
      }

      [data-theme="light"] .confirm-btn-cancel:hover {
        background: rgba(0, 0, 0, 0.1);
        color: #1e293b;
      }

      /* Responsive */
      @media (max-width: 640px) {
        .toast-container {
          padding: 16px;
          max-width: 100%;
        }

        .toast-container.top-right,
        .toast-container.top-left,
        .toast-container.top-center {
          left: 0;
          right: 0;
          transform: none;
        }

        .toast-container.bottom-right,
        .toast-container.bottom-left,
        .toast-container.bottom-center {
          left: 0;
          right: 0;
          transform: none;
        }

        .confirm-footer {
          flex-direction: column-reverse;
        }

        .confirm-btn {
          width: 100%;
          justify-content: center;
        }
      }

      /* Reduced motion */
      @media (prefers-reduced-motion: reduce) {
        .toast,
        .confirm-overlay,
        .confirm-dialog {
          transition: opacity 0.01ms;
        }

        .toast {
          transform: none !important;
        }

        .confirm-dialog {
          transform: none !important;
        }

        .toast-progress {
          animation: none;
          width: 0;
        }
      }
    `;
    document.head.appendChild(styles);
  }

  /**
   * Get or create toast container for position
   * @private
   * @param {string} position - Container position
   * @returns {HTMLElement} Container element
   */
  static _getContainer(position) {
    if (Alert.containers.has(position)) {
      return Alert.containers.get(position);
    }

    Alert._injectStyles();

    const container = document.createElement('div');
    container.className = `toast-container ${position}`;
    container.setAttribute('role', 'region');
    container.setAttribute('aria-label', '通知');
    container.setAttribute('aria-live', 'polite');
    document.body.appendChild(container);

    Alert.containers.set(position, container);
    return container;
  }

  /**
   * Show a toast notification
   * @param {ToastOptions} options - Toast options
   * @returns {string} Toast ID for manual dismissal
   */
  static toast(options) {
    const {
      message,
      title = '',
      type = 'info',
      duration = 4000,
      closable = true,
      position = 'top-right',
      onClose = null,
      action = null
    } = options;

    const container = Alert._getContainer(position);
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    const toast = document.createElement('div');
    toast.id = id;
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-atomic', 'true');

    const closeIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>`;

    toast.innerHTML = `
      <div class="toast-icon" aria-hidden="true">${Alert.ICONS[type]}</div>
      <div class="toast-content">
        ${title ? `<div class="toast-title">${escapeHtml(title)}</div>` : ''}
        <div class="toast-message">${escapeHtml(message)}</div>
        ${action ? `
          <div class="toast-action">
            <button class="toast-action-btn">${escapeHtml(action.text)}</button>
          </div>
        ` : ''}
      </div>
      ${closable ? `
        <button class="toast-close" aria-label="閉じる">${closeIcon}</button>
      ` : ''}
      ${duration > 0 ? `<div class="toast-progress" style="animation-duration: ${duration}ms"></div>` : ''}
    `;

    // Event handlers
    const dismiss = () => {
      toast.classList.remove('show');
      toast.classList.add('hiding');

      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
        Alert.activeToasts.delete(id);
        if (onClose) onClose();
      }, 400);
    };

    if (closable) {
      const closeBtn = toast.querySelector('.toast-close');
      closeBtn.addEventListener('click', dismiss);
    }

    if (action && action.onClick) {
      const actionBtn = toast.querySelector('.toast-action-btn');
      actionBtn.addEventListener('click', () => {
        action.onClick();
        dismiss();
      });
    }

    // Add to container
    container.appendChild(toast);
    Alert.activeToasts.set(id, toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    // Auto dismiss
    if (duration > 0) {
      setTimeout(dismiss, duration);
    }

    return id;
  }

  /**
   * Show success toast
   * @param {string} message - Message
   * @param {string} [title] - Title
   * @param {number} [duration=3000] - Duration
   * @returns {string} Toast ID
   */
  static success(message, title = '', duration = 3000) {
    return Alert.toast({ message, title, type: 'success', duration });
  }

  /**
   * Show error toast
   * @param {string} message - Message
   * @param {string} [title] - Title
   * @param {number} [duration=5000] - Duration
   * @returns {string} Toast ID
   */
  static error(message, title = '', duration = 5000) {
    return Alert.toast({ message, title, type: 'error', duration });
  }

  /**
   * Show warning toast
   * @param {string} message - Message
   * @param {string} [title] - Title
   * @param {number} [duration=4000] - Duration
   * @returns {string} Toast ID
   */
  static warning(message, title = '', duration = 4000) {
    return Alert.toast({ message, title, type: 'warning', duration });
  }

  /**
   * Show info toast
   * @param {string} message - Message
   * @param {string} [title] - Title
   * @param {number} [duration=3000] - Duration
   * @returns {string} Toast ID
   */
  static info(message, title = '', duration = 3000) {
    return Alert.toast({ message, title, type: 'info', duration });
  }

  /**
   * Dismiss a specific toast
   * @param {string} id - Toast ID
   */
  static dismiss(id) {
    const toast = Alert.activeToasts.get(id);
    if (toast) {
      const closeBtn = toast.querySelector('.toast-close');
      if (closeBtn) {
        closeBtn.click();
      } else {
        toast.remove();
        Alert.activeToasts.delete(id);
      }
    }
  }

  /**
   * Dismiss all toasts
   */
  static dismissAll() {
    Alert.activeToasts.forEach((toast, id) => {
      Alert.dismiss(id);
    });
  }

  /**
   * Show confirmation dialog
   * @param {ConfirmOptions} options - Dialog options
   * @returns {Promise<boolean>} True if confirmed, false if cancelled
   */
  static confirm(options) {
    const {
      message,
      title = '確認',
      type = 'warning',
      confirmText = '確認',
      cancelText = 'キャンセル',
      confirmVariant = 'primary',
      dangerous = false
    } = options;

    Alert._injectStyles();

    return new Promise((resolve) => {
      const overlay = document.createElement('div');
      overlay.className = 'confirm-overlay';
      overlay.setAttribute('role', 'dialog');
      overlay.setAttribute('aria-modal', 'true');
      overlay.setAttribute('aria-labelledby', 'confirm-title');
      overlay.setAttribute('aria-describedby', 'confirm-message');

      const iconType = dangerous ? 'danger' : type;
      const btnClass = dangerous ? 'confirm-btn-danger' : 'confirm-btn-confirm';

      overlay.innerHTML = `
        <div class="confirm-dialog">
          <div class="confirm-header">
            <div class="confirm-icon ${iconType}" aria-hidden="true">
              ${Alert.ICONS[iconType === 'danger' ? 'error' : iconType]}
            </div>
            <div class="confirm-header-text">
              <h3 id="confirm-title">${escapeHtml(title)}</h3>
              <p id="confirm-message">${escapeHtml(message)}</p>
            </div>
          </div>
          <div class="confirm-footer">
            <button class="confirm-btn confirm-btn-cancel" data-action="cancel">
              ${escapeHtml(cancelText)}
            </button>
            <button class="confirm-btn ${btnClass}" data-action="confirm">
              ${escapeHtml(confirmText)}
            </button>
          </div>
        </div>
      `;

      const close = (result) => {
        overlay.classList.remove('active');
        setTimeout(() => {
          overlay.remove();
          resolve(result);
        }, 300);
      };

      // Button handlers
      overlay.querySelector('[data-action="cancel"]').addEventListener('click', () => close(false));
      overlay.querySelector('[data-action="confirm"]').addEventListener('click', () => close(true));

      // Backdrop click
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close(false);
      });

      // Escape key
      const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
          close(false);
          document.removeEventListener('keydown', handleKeyDown);
        }
      };
      document.addEventListener('keydown', handleKeyDown);

      // Focus management
      document.body.appendChild(overlay);

      requestAnimationFrame(() => {
        overlay.classList.add('active');
        overlay.querySelector('[data-action="confirm"]').focus();
      });
    });
  }

  /**
   * Show dangerous confirmation dialog
   * @param {string} message - Message
   * @param {string} [title='警告'] - Title
   * @returns {Promise<boolean>} True if confirmed
   */
  static confirmDanger(message, title = '警告') {
    return Alert.confirm({
      message,
      title,
      type: 'danger',
      dangerous: true,
      confirmText: '削除',
      confirmVariant: 'danger'
    });
  }
}

export default Alert;
