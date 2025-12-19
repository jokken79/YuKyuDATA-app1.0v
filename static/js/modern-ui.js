/**
 * Modern UI Enhancements 2025
 * Toast Notifications, Confirmation Dialogs, FAB, Micro-interactions
 */

// ============================================
// TOAST NOTIFICATION SYSTEM
// ============================================
class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create container if not exists
        if (!document.querySelector('.toast-container')) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.querySelector('.toast-container');
        }
    }

    show(options) {
        const {
            type = 'info',
            title = '',
            message = '',
            duration = 4000,
            closable = true
        } = options;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
            error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
            warning: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
            info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type]}</div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                ${message ? `<div class="toast-message">${message}</div>` : ''}
            </div>
            ${closable ? `<button class="toast-close">&times;</button>` : ''}
            <div class="toast-progress"></div>
        `;

        this.container.appendChild(toast);

        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Close button handler
        if (closable) {
            toast.querySelector('.toast-close').addEventListener('click', () => {
                this.hide(toast);
            });
        }

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => {
                this.hide(toast);
            }, duration);
        }

        return toast;
    }

    hide(toast) {
        toast.classList.add('hiding');
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 400);
    }

    success(title, message) {
        return this.show({ type: 'success', title, message });
    }

    error(title, message) {
        return this.show({ type: 'error', title, message });
    }

    warning(title, message) {
        return this.show({ type: 'warning', title, message });
    }

    info(title, message) {
        return this.show({ type: 'info', title, message });
    }
}

// ============================================
// CONFIRMATION DIALOG SYSTEM
// ============================================
class DialogManager {
    constructor() {
        this.overlay = null;
        this.init();
    }

    init() {
        if (!document.querySelector('.dialog-overlay')) {
            this.overlay = document.createElement('div');
            this.overlay.className = 'dialog-overlay';
            this.overlay.innerHTML = `
                <div class="dialog">
                    <div class="dialog-header">
                        <div class="dialog-icon"></div>
                        <div class="dialog-header-text">
                            <h3></h3>
                            <p></p>
                        </div>
                    </div>
                    <div class="dialog-body"></div>
                    <div class="dialog-footer">
                        <button class="dialog-btn dialog-btn-cancel">Cancel</button>
                        <button class="dialog-btn dialog-btn-confirm">Confirm</button>
                    </div>
                </div>
            `;
            document.body.appendChild(this.overlay);

            // Close on overlay click
            this.overlay.addEventListener('click', (e) => {
                if (e.target === this.overlay) {
                    this.close();
                }
            });

            // Close on Escape
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.overlay.classList.contains('active')) {
                    this.close();
                }
            });
        } else {
            this.overlay = document.querySelector('.dialog-overlay');
        }
    }

    show(options) {
        return new Promise((resolve) => {
            const {
                type = 'info',
                title = 'Confirm',
                message = 'Are you sure?',
                confirmText = 'Confirm',
                cancelText = 'Cancel',
                showCancel = true,
                input = null,
                danger = false
            } = options;

            const icons = {
                danger: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
                warning: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
                info: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
            };

            const dialog = this.overlay.querySelector('.dialog');
            const iconEl = dialog.querySelector('.dialog-icon');
            const titleEl = dialog.querySelector('.dialog-header-text h3');
            const messageEl = dialog.querySelector('.dialog-header-text p');
            const bodyEl = dialog.querySelector('.dialog-body');
            const cancelBtn = dialog.querySelector('.dialog-btn-cancel');
            const confirmBtn = dialog.querySelector('.dialog-btn-confirm');

            // Set content
            iconEl.className = `dialog-icon ${type}`;
            iconEl.innerHTML = icons[type] || icons.info;
            titleEl.textContent = title;
            messageEl.textContent = message;

            // Handle input field
            if (input) {
                bodyEl.innerHTML = `<input type="${input.type || 'text'}" class="dialog-input" placeholder="${input.placeholder || ''}" value="${input.value || ''}">`;
                bodyEl.style.display = 'block';
            } else {
                bodyEl.style.display = 'none';
            }

            // Set button text and styles
            cancelBtn.textContent = cancelText;
            cancelBtn.style.display = showCancel ? 'flex' : 'none';

            confirmBtn.textContent = confirmText;
            confirmBtn.className = danger ? 'dialog-btn dialog-btn-danger' : 'dialog-btn dialog-btn-confirm';

            // Button handlers
            const handleConfirm = () => {
                const inputValue = input ? bodyEl.querySelector('.dialog-input').value : null;
                this.close();
                resolve({ confirmed: true, value: inputValue });
                cleanup();
            };

            const handleCancel = () => {
                this.close();
                resolve({ confirmed: false, value: null });
                cleanup();
            };

            const cleanup = () => {
                confirmBtn.removeEventListener('click', handleConfirm);
                cancelBtn.removeEventListener('click', handleCancel);
            };

            confirmBtn.addEventListener('click', handleConfirm);
            cancelBtn.addEventListener('click', handleCancel);

            // Show dialog
            this.overlay.classList.add('active');

            // Focus input if exists
            if (input) {
                setTimeout(() => {
                    bodyEl.querySelector('.dialog-input').focus();
                }, 100);
            }
        });
    }

    close() {
        this.overlay.classList.remove('active');
    }

    confirm(title, message) {
        return this.show({ type: 'info', title, message });
    }

    danger(title, message) {
        return this.show({
            type: 'danger',
            title,
            message,
            confirmText: 'Delete',
            danger: true
        });
    }

    prompt(title, message, placeholder = '') {
        return this.show({
            type: 'info',
            title,
            message,
            input: { type: 'text', placeholder }
        });
    }
}

// ============================================
// FLOATING ACTION BUTTON (FAB)
// ============================================
class FABManager {
    constructor() {
        this.container = null;
        this.isOpen = false;
        this.actions = [];
    }

    init(actions = []) {
        this.actions = actions;

        if (!document.querySelector('.fab-container')) {
            this.container = document.createElement('div');
            this.container.className = 'fab-container';
            this.render();
            document.body.appendChild(this.container);
        }
    }

    render() {
        const actionsHtml = this.actions.map(action => `
            <div class="fab-action" data-action="${action.id}" title="${action.label}">
                <div class="fab-action-icon">${action.icon}</div>
                <span class="fab-action-label">${action.label}</span>
            </div>
        `).join('');

        this.container.innerHTML = `
            <div class="fab-menu">${actionsHtml}</div>
            <button class="fab" aria-label="Quick actions">
                <svg class="fab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
            </button>
        `;

        // FAB toggle
        const fab = this.container.querySelector('.fab');
        fab.addEventListener('click', () => this.toggle());

        // Action clicks
        this.container.querySelectorAll('.fab-action').forEach(el => {
            el.addEventListener('click', () => {
                const actionId = el.dataset.action;
                const action = this.actions.find(a => a.id === actionId);
                if (action && action.onClick) {
                    action.onClick();
                }
                this.close();
            });
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target) && this.isOpen) {
                this.close();
            }
        });
    }

    toggle() {
        this.isOpen = !this.isOpen;
        this.container.classList.toggle('open', this.isOpen);
        this.container.querySelector('.fab').classList.toggle('open', this.isOpen);
    }

    open() {
        this.isOpen = true;
        this.container.classList.add('open');
        this.container.querySelector('.fab').classList.add('open');
    }

    close() {
        this.isOpen = false;
        this.container.classList.remove('open');
        this.container.querySelector('.fab').classList.remove('open');
    }
}

// ============================================
// SKELETON LOADER
// ============================================
class SkeletonLoader {
    static createCard() {
        return `
            <div class="skeleton skeleton-card"></div>
        `;
    }

    static createRow(count = 5) {
        let rows = '';
        for (let i = 0; i < count; i++) {
            rows += `
                <div class="skeleton-row">
                    <div class="skeleton skeleton-avatar"></div>
                    <div style="flex: 1;">
                        <div class="skeleton skeleton-text lg"></div>
                        <div class="skeleton skeleton-text sm"></div>
                    </div>
                    <div class="skeleton skeleton-text" style="width: 80px;"></div>
                </div>
            `;
        }
        return rows;
    }

    static createTable(rows = 10, cols = 5) {
        let headerCells = '';
        let bodyCells = '';

        for (let c = 0; c < cols; c++) {
            headerCells += `<th><div class="skeleton skeleton-text md"></div></th>`;
        }

        for (let r = 0; r < rows; r++) {
            bodyCells += '<tr>';
            for (let c = 0; c < cols; c++) {
                const width = c === 0 ? 'lg' : (c === cols - 1 ? 'sm' : 'md');
                bodyCells += `<td><div class="skeleton skeleton-text ${width}"></div></td>`;
            }
            bodyCells += '</tr>';
        }

        return `
            <table class="skeleton-table" style="width: 100%;">
                <thead><tr>${headerCells}</tr></thead>
                <tbody>${bodyCells}</tbody>
            </table>
        `;
    }

    static createGrid(count = 4) {
        let cards = '';
        for (let i = 0; i < count; i++) {
            cards += `<div class="skeleton skeleton-card"></div>`;
        }
        return `<div class="bento-grid">${cards}</div>`;
    }
}

// ============================================
// MICRO-INTERACTIONS
// ============================================
class MicroInteractions {
    static init() {
        // Ripple effect on buttons
        this.initRipple();

        // Magnetic effect
        this.initMagnetic();

        // Scroll to top button
        this.initScrollTop();

        // Tilt effect on cards
        this.initTiltCards();
    }

    static initRipple() {
        document.addEventListener('click', (e) => {
            const target = e.target.closest('.btn, .nav-item, .fab-action');
            if (!target) return;

            const ripple = document.createElement('span');
            ripple.className = 'ripple';

            const rect = target.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);

            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
            ripple.style.top = `${e.clientY - rect.top - size / 2}px`;

            target.style.position = 'relative';
            target.style.overflow = 'hidden';
            target.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    }

    static initMagnetic() {
        document.querySelectorAll('.magnetic').forEach(el => {
            el.addEventListener('mousemove', (e) => {
                const rect = el.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;

                el.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
            });

            el.addEventListener('mouseleave', () => {
                el.style.transform = 'translate(0, 0)';
            });
        });
    }

    static initScrollTop() {
        // Create scroll to top button if not exists
        if (!document.querySelector('.scroll-top')) {
            const btn = document.createElement('button');
            btn.className = 'scroll-top';
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
            `;
            btn.addEventListener('click', () => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
            document.body.appendChild(btn);
        }

        const scrollBtn = document.querySelector('.scroll-top');

        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                scrollBtn.classList.add('visible');
            } else {
                scrollBtn.classList.remove('visible');
            }
        });
    }

    static initTiltCards() {
        document.querySelectorAll('.tilt-card').forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateX = (y - centerY) / 10;
                const rotateY = (centerX - x) / 10;

                card.style.setProperty('--rotateX', `${rotateX}deg`);
                card.style.setProperty('--rotateY', `${rotateY}deg`);
            });

            card.addEventListener('mouseleave', () => {
                card.style.setProperty('--rotateX', '0deg');
                card.style.setProperty('--rotateY', '0deg');
            });
        });
    }
}

// ============================================
// VIEW TRANSITIONS
// ============================================
class ViewTransitions {
    static async switchView(oldView, newView) {
        if (oldView) {
            oldView.classList.add('view-exit');
            await new Promise(r => setTimeout(r, 200));
            oldView.classList.remove('active', 'view-exit');
        }

        newView.classList.add('active');

        // Stagger children animation
        const children = newView.querySelectorAll('.stagger-child');
        children.forEach((child, i) => {
            child.style.animationDelay = `${i * 0.05}s`;
        });
    }
}

// ============================================
// LOADING MANAGER
// ============================================
class LoadingManager {
    static showButton(btn) {
        const text = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.btn-spinner');

        if (text) text.style.opacity = '0';
        if (spinner) {
            spinner.style.display = 'block';
            spinner.innerHTML = `
                <div class="loading-dots">
                    <span></span><span></span><span></span>
                </div>
            `;
        }
        btn.disabled = true;
    }

    static hideButton(btn) {
        const text = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.btn-spinner');

        if (text) text.style.opacity = '1';
        if (spinner) spinner.style.display = 'none';
        btn.disabled = false;
    }

    static showTable(container) {
        container.innerHTML = SkeletonLoader.createTable(10, 5);
    }

    static showCards(container, count = 4) {
        container.innerHTML = SkeletonLoader.createGrid(count);
    }
}

// ============================================
// INITIALIZE GLOBAL INSTANCES
// ============================================
const Toast = new ToastManager();
const Dialog = new DialogManager();
const FAB = new FABManager();

// Export for global use
window.ModernUI = {
    Toast,
    Dialog,
    FAB,
    SkeletonLoader,
    MicroInteractions,
    ViewTransitions,
    LoadingManager
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    MicroInteractions.init();

    // Initialize FAB with default actions
    FAB.init([
        {
            id: 'sync',
            label: 'Sync Data',
            icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>`,
            onClick: () => {
                if (typeof App !== 'undefined' && App.data) {
                    App.data.sync();
                }
            }
        },
        {
            id: 'export',
            label: 'Export CSV',
            icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`,
            onClick: () => {
                if (typeof App !== 'undefined' && App.export) {
                    App.export.csv();
                }
            }
        },
        {
            id: 'scroll-top',
            label: 'Back to Top',
            icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"></polyline></svg>`,
            onClick: () => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }
    ]);
});

// ============================================
// INTEGRATION HELPERS
// ============================================

/**
 * Wrap dangerous actions with confirmation
 * @param {Function} action - The action to perform
 * @param {string} title - Dialog title
 * @param {string} message - Dialog message
 */
async function confirmAction(action, title = 'Confirm Action', message = 'Are you sure?') {
    const result = await Dialog.show({
        type: 'warning',
        title,
        message,
        confirmText: 'Yes, Continue',
        cancelText: 'Cancel'
    });

    if (result.confirmed) {
        return action();
    }
    return null;
}

/**
 * Wrap dangerous delete actions with confirmation
 * @param {Function} action - The delete action
 * @param {string} itemName - Name of item being deleted
 */
async function confirmDelete(action, itemName = 'this item') {
    const result = await Dialog.danger(
        'Delete Confirmation',
        `Are you sure you want to delete ${itemName}? This action cannot be undone.`
    );

    if (result.confirmed) {
        return action();
    }
    return null;
}

// Export helper functions
window.confirmAction = confirmAction;
window.confirmDelete = confirmDelete;
