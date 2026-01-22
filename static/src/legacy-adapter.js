/**
 * Legacy Adapter - Bridges legacy app.js with modern ES6 modules
 *
 * This adapter allows gradual migration from the legacy SPA (app.js)
 * to the modern component-based architecture (static/src/).
 */

export class LegacyAdapter {
    constructor(legacyApp) {
        this.legacyApp = legacyApp;
        this.modernComponents = new Map();
        this.eventBridge = new EventTarget();
    }

    /**
     * Initialize the adapter and attach to legacy app
     */
    init() {
        if (!this.legacyApp) {
            console.warn('[LegacyAdapter] No legacy app instance provided');
            return;
        }

        // Expose modern utilities to legacy app
        this._exposeModernUtilities();

        // Listen for legacy app events
        this._setupEventBridge();

        console.log('[LegacyAdapter] Initialized successfully');
    }

    /**
     * Expose modern utilities to the legacy app namespace
     */
    _exposeModernUtilities() {
        if (!this.legacyApp) return;

        // Add modern alert system if not present
        if (!this.legacyApp.modernAlert) {
            this.legacyApp.modernAlert = {
                success: (msg) => this._showAlert('success', msg),
                error: (msg) => this._showAlert('error', msg),
                warning: (msg) => this._showAlert('warning', msg),
                info: (msg) => this._showAlert('info', msg)
            };
        }

        // Add modern confirmation dialog
        if (!this.legacyApp.modernConfirm) {
            this.legacyApp.modernConfirm = (options) => this._showConfirm(options);
        }
    }

    /**
     * Setup event bridge between legacy and modern systems
     */
    _setupEventBridge() {
        // Forward custom events from legacy to modern
        const legacyEvents = [
            'dataLoaded',
            'employeeSelected',
            'yearChanged',
            'viewChanged',
            'themeChanged'
        ];

        legacyEvents.forEach(eventName => {
            document.addEventListener(eventName, (e) => {
                this.eventBridge.dispatchEvent(new CustomEvent(`legacy:${eventName}`, {
                    detail: e.detail
                }));
            });
        });
    }

    /**
     * Register a modern component for use in legacy templates
     */
    registerComponent(name, component) {
        this.modernComponents.set(name, component);
    }

    /**
     * Render a modern component into a legacy container
     */
    renderComponent(name, containerId, props = {}) {
        const component = this.modernComponents.get(name);
        const container = document.getElementById(containerId);

        if (!component || !container) {
            console.warn(`[LegacyAdapter] Cannot render ${name} into ${containerId}`);
            return null;
        }

        return component.render(container, props);
    }

    /**
     * Show a modern alert
     */
    _showAlert(type, message) {
        // Try to use modern Alert component if available
        try {
            import('./components/Alert.js').then(({ Alert }) => {
                Alert[type](message);
            }).catch(() => {
                // Fallback to console
                console[type === 'error' ? 'error' : 'log'](`[${type.toUpperCase()}] ${message}`);
            });
        } catch {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    /**
     * Show a modern confirmation dialog
     */
    async _showConfirm(options) {
        const { title, message, confirmText = 'OK', cancelText = 'Cancel' } = options;

        // Try to use modern Modal component if available
        try {
            const { showConfirmModal } = await import('./components/Modal.js');
            return showConfirmModal({ title, message, confirmText, cancelText });
        } catch {
            // Fallback to native confirm
            return window.confirm(`${title}\n\n${message}`);
        }
    }

    /**
     * Subscribe to bridged events
     */
    on(eventName, callback) {
        this.eventBridge.addEventListener(eventName, callback);
        return () => this.eventBridge.removeEventListener(eventName, callback);
    }

    /**
     * Get legacy app state safely
     */
    getLegacyState(key) {
        if (!this.legacyApp || !this.legacyApp.state) return null;
        return key ? this.legacyApp.state[key] : this.legacyApp.state;
    }

    /**
     * Update legacy app state
     */
    setLegacyState(key, value) {
        if (!this.legacyApp || !this.legacyApp.state) return;
        this.legacyApp.state[key] = value;

        // Trigger legacy state change event
        document.dispatchEvent(new CustomEvent('stateChanged', {
            detail: { key, value }
        }));
    }
}

export default LegacyAdapter;
