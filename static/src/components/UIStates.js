/**
 * UI States Component
 * Provides consistent loading, empty, and error state UI patterns
 * Uses unified-design-system.css tokens
 * Uses safe DOM methods (no innerHTML with user content)
 * @version 1.0.0
 */

/**
 * Helper: Create element with attributes
 * @param {string} tag - Tag name
 * @param {Object} attrs - Attributes
 * @param {string|HTMLElement|Array} children - Children
 * @returns {HTMLElement}
 */
function createElement(tag, attrs = {}, children = null) {
    const el = document.createElement(tag);

    Object.entries(attrs).forEach(([key, value]) => {
        if (key === 'className') {
            el.className = value;
        } else if (key === 'style' && typeof value === 'object') {
            Object.assign(el.style, value);
        } else if (key.startsWith('data')) {
            el.setAttribute(key.replace(/([A-Z])/g, '-$1').toLowerCase(), value);
        } else {
            el.setAttribute(key, value);
        }
    });

    if (children) {
        if (Array.isArray(children)) {
            children.forEach(child => {
                if (typeof child === 'string') {
                    el.appendChild(document.createTextNode(child));
                } else if (child) {
                    el.appendChild(child);
                }
            });
        } else if (typeof children === 'string') {
            el.textContent = children;
        } else {
            el.appendChild(children);
        }
    }

    return el;
}

/**
 * Create SVG element
 * @param {string} pathD - SVG path data
 * @param {Object} options - SVG options
 * @returns {SVGElement}
 */
function createSvgIcon(pathD, options = {}) {
    const { width = 24, height = 24, stroke = 'currentColor', fill = 'none' } = options;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('fill', fill);
    svg.setAttribute('stroke', stroke);
    svg.setAttribute('stroke-width', '1.5');

    if (Array.isArray(pathD)) {
        pathD.forEach(d => {
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', d);
            svg.appendChild(path);
        });
    } else {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', pathD);
        svg.appendChild(path);
    }

    return svg;
}

// SVG icon paths
const ICONS = {
    spinner: 'M12 2C6.48 2 2 6.48 2 12',
    inbox: ['M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4'],
    search: ['M21 21l-4.35-4.35', 'M11 19a8 8 0 100-16 8 8 0 000 16z'],
    users: ['M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2', 'M9 7a4 4 0 100-8 4 4 0 000 8z'],
    calendar: ['M19 4H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2z', 'M16 2v4', 'M8 2v4', 'M3 10h18'],
    error: ['M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z', 'M12 8v4', 'M12 16h.01'],
    retry: ['M23 4v6h-6', 'M20.49 15a9 9 0 11-2.12-9.36L23 10']
};

/**
 * Loading state component
 * @param {Object} options - Configuration options
 * @returns {HTMLElement} Loading element
 */
export function createLoadingState(options = {}) {
    const {
        message = '読み込み中...',
        size = 'medium',
        overlay = false
    } = options;

    const sizes = {
        small: { spinner: '1rem', text: 'var(--text-sm)' },
        medium: { spinner: '2rem', text: 'var(--text-base)' },
        large: { spinner: '3rem', text: 'var(--text-lg)' }
    };

    const sizeConfig = sizes[size] || sizes.medium;

    const container = createElement('div', {
        className: `ui-state ui-state-loading ${overlay ? 'ui-state-overlay' : ''}`,
        role: 'status',
        'aria-live': 'polite',
        'aria-busy': 'true'
    });

    const spinnerWrapper = createElement('div', {
        className: 'ui-state-spinner',
        style: { width: sizeConfig.spinner, height: sizeConfig.spinner }
    });

    // Create spinner SVG
    const spinnerSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    spinnerSvg.setAttribute('viewBox', '0 0 24 24');
    spinnerSvg.setAttribute('fill', 'none');

    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '12');
    circle.setAttribute('cy', '12');
    circle.setAttribute('r', '10');
    circle.setAttribute('stroke', 'currentColor');
    circle.setAttribute('stroke-width', '3');
    circle.setAttribute('stroke-opacity', '0.2');

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', ICONS.spinner);
    path.setAttribute('stroke', 'currentColor');
    path.setAttribute('stroke-width', '3');
    path.setAttribute('stroke-linecap', 'round');

    spinnerSvg.appendChild(circle);
    spinnerSvg.appendChild(path);
    spinnerWrapper.appendChild(spinnerSvg);

    const messageEl = createElement('p', {
        className: 'ui-state-message',
        style: { fontSize: sizeConfig.text }
    }, message);

    const content = createElement('div', { className: 'ui-state-content' }, [
        spinnerWrapper,
        messageEl
    ]);

    container.appendChild(content);
    return container;
}

/**
 * Empty state component
 * @param {Object} options - Configuration options
 * @returns {HTMLElement} Empty state element
 */
export function createEmptyState(options = {}) {
    const {
        title = 'データがありません',
        message = '',
        icon = 'inbox',
        action = null
    } = options;

    const container = createElement('div', {
        className: 'ui-state ui-state-empty',
        role: 'status'
    });

    const iconWrapper = createElement('div', { className: 'ui-state-icon' });
    iconWrapper.appendChild(createSvgIcon(ICONS[icon] || ICONS.inbox));

    const titleEl = createElement('h3', { className: 'ui-state-title' }, title);

    const children = [iconWrapper, titleEl];

    if (message) {
        children.push(createElement('p', { className: 'ui-state-message' }, message));
    }

    if (action && action.label) {
        const btn = createElement('button', {
            className: 'ui-state-action btn btn-primary',
            type: 'button'
        }, action.label);

        if (action.onClick) {
            btn.addEventListener('click', action.onClick);
        }
        children.push(btn);
    }

    const content = createElement('div', { className: 'ui-state-content' }, children);
    container.appendChild(content);
    return container;
}

/**
 * Error state component
 * @param {Object} options - Configuration options
 * @returns {HTMLElement} Error state element
 */
export function createErrorState(options = {}) {
    const {
        title = 'エラーが発生しました',
        message = '',
        code = null,
        retry = null
    } = options;

    const container = createElement('div', {
        className: 'ui-state ui-state-error',
        role: 'alert',
        'aria-live': 'assertive'
    });

    const iconWrapper = createElement('div', { className: 'ui-state-icon ui-state-icon-error' });
    iconWrapper.appendChild(createSvgIcon(ICONS.error));

    const titleEl = createElement('h3', { className: 'ui-state-title' }, title);

    const children = [iconWrapper, titleEl];

    if (message) {
        children.push(createElement('p', { className: 'ui-state-message' }, message));
    }

    if (code) {
        children.push(createElement('code', { className: 'ui-state-code' }, `Error: ${code}`));
    }

    if (retry) {
        const retryIcon = createSvgIcon(ICONS.retry);
        retryIcon.setAttribute('width', '16');
        retryIcon.setAttribute('height', '16');
        retryIcon.setAttribute('stroke-width', '2');

        const btn = createElement('button', {
            className: 'ui-state-action btn btn-outline',
            type: 'button'
        }, [retryIcon, document.createTextNode(` ${retry.label || '再試行'}`)]);

        if (retry.onClick) {
            btn.addEventListener('click', retry.onClick);
        }
        children.push(btn);
    }

    const content = createElement('div', { className: 'ui-state-content' }, children);
    container.appendChild(content);
    return container;
}

/**
 * Skeleton loading placeholder
 * @param {Object} options - Configuration options
 * @returns {HTMLElement} Skeleton element
 */
export function createSkeleton(options = {}) {
    const { rows = 3, type = 'text' } = options;

    const container = createElement('div', {
        className: `ui-skeleton ui-skeleton-${type}`,
        'aria-hidden': 'true',
        'aria-label': '読み込み中'
    });

    switch (type) {
        case 'card': {
            const card = createElement('div', { className: 'skeleton-card' });
            card.appendChild(createElement('div', { className: 'skeleton-header' }));
            const body = createElement('div', { className: 'skeleton-body' });
            body.appendChild(createElement('div', { className: 'skeleton-line skeleton-line-full' }));
            body.appendChild(createElement('div', { className: 'skeleton-line skeleton-line-75' }));
            body.appendChild(createElement('div', { className: 'skeleton-line skeleton-line-50' }));
            card.appendChild(body);
            container.appendChild(card);
            break;
        }

        case 'table': {
            const table = createElement('div', { className: 'skeleton-table' });
            const headerRow = createElement('div', { className: 'skeleton-row skeleton-row-header' });
            for (let i = 0; i < 4; i++) {
                headerRow.appendChild(createElement('div', { className: 'skeleton-cell' }));
            }
            table.appendChild(headerRow);

            for (let r = 0; r < rows; r++) {
                const row = createElement('div', { className: 'skeleton-row' });
                for (let i = 0; i < 4; i++) {
                    row.appendChild(createElement('div', { className: 'skeleton-cell' }));
                }
                table.appendChild(row);
            }
            container.appendChild(table);
            break;
        }

        case 'avatar': {
            const group = createElement('div', { className: 'skeleton-avatar-group' });
            group.appendChild(createElement('div', { className: 'skeleton-avatar' }));
            const text = createElement('div', { className: 'skeleton-text' });
            text.appendChild(createElement('div', { className: 'skeleton-line skeleton-line-75' }));
            text.appendChild(createElement('div', { className: 'skeleton-line skeleton-line-50' }));
            group.appendChild(text);
            container.appendChild(group);
            break;
        }

        case 'text':
        default:
            for (let i = 0; i < rows; i++) {
                const width = i === rows - 1 ? '60' : (i === 0 ? '100' : '80');
                container.appendChild(createElement('div', { className: `skeleton-line skeleton-line-${width}` }));
            }
            break;
    }

    return container;
}

/**
 * UIStates class for managing state transitions in containers
 */
export class UIStates {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.currentState = null;
        this.originalContent = null;
    }

    showLoading(options = {}) {
        this._saveContent();
        this._clearContainer();
        this.container.appendChild(createLoadingState(options));
        this.currentState = 'loading';
    }

    showEmpty(options = {}) {
        this._saveContent();
        this._clearContainer();
        this.container.appendChild(createEmptyState(options));
        this.currentState = 'empty';
    }

    showError(options = {}) {
        this._saveContent();
        this._clearContainer();
        this.container.appendChild(createErrorState(options));
        this.currentState = 'error';
    }

    showSkeleton(options = {}) {
        this._saveContent();
        this._clearContainer();
        this.container.appendChild(createSkeleton(options));
        this.currentState = 'skeleton';
    }

    restore() {
        if (this.originalContent) {
            this._clearContainer();
            this.container.appendChild(this.originalContent);
            this.originalContent = null;
        }
        this.currentState = null;
    }

    clear() {
        this._clearContainer();
        this.originalContent = null;
        this.currentState = null;
    }

    _clearContainer() {
        while (this.container.firstChild) {
            this.container.removeChild(this.container.firstChild);
        }
    }

    _saveContent() {
        if (!this.originalContent && this.container.children.length > 0) {
            this.originalContent = document.createDocumentFragment();
            while (this.container.firstChild) {
                this.originalContent.appendChild(this.container.firstChild);
            }
        }
    }

    getState() {
        return this.currentState;
    }
}

export default {
    createLoadingState,
    createEmptyState,
    createErrorState,
    createSkeleton,
    UIStates
};
