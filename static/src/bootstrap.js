/**
 * YuKyu Modern UI Bootstrap
 * Inicializador que conecta static/src/ con la aplicacion principal
 *
 * Este archivo detecta el entorno y decide si usar:
 * - Arquitectura moderna (static/src/)
 * - Arquitectura legacy (app.js)
 * - Modo hibrido (ambas)
 *
 * @module bootstrap
 * @version 1.0.0
 */

// Feature detection flags
const FEATURES = {
    modules: 'noModule' in document.createElement('script'),
    customElements: 'customElements' in window,
    shadowDOM: 'attachShadow' in Element.prototype,
    intersectionObserver: 'IntersectionObserver' in window,
    resizeObserver: 'ResizeObserver' in window
};

// Configuration
const CONFIG = {
    // Use modern architecture if browser supports all features
    useModernUI: FEATURES.modules && FEATURES.customElements,
    // Enable hybrid mode (both legacy and modern coexist)
    hybridMode: true,
    // Debug mode
    debug: localStorage.getItem('yukyu_debug') === 'true',
    // Version
    version: '1.0.0'
};

/**
 * Log helper (only in debug mode)
 */
function log(...args) {
    if (CONFIG.debug) {
        console.log('[Bootstrap]', ...args);
    }
}

/**
 * Initialize modern UI components
 * @param {Object} legacyApp - The existing App object from app.js
 */
export async function initModernUI(legacyApp) {
    log('Initializing modern UI...');
    log('Browser features:', FEATURES);

    if (!CONFIG.useModernUI) {
        log('Modern UI disabled - browser not supported');
        return { success: false, reason: 'browser-not-supported' };
    }

    try {
        // Dynamically import the modern modules
        const [
            { default: YuKyuApp, integrateWithLegacyApp, State },
            { LegacyAdapter }
        ] = await Promise.all([
            import('./index.js'),
            import('./legacy-adapter.js')
        ]);

        // Create adapter instance
        const adapter = new LegacyAdapter(legacyApp);

        // Initialize adapter (attaches components to legacy App)
        adapter.init();

        // Integrate with legacy App if in hybrid mode
        if (CONFIG.hybridMode && legacyApp) {
            integrateWithLegacyApp(legacyApp);

            // Sync initial state from legacy App
            if (legacyApp.state) {
                State.setState({
                    data: legacyApp.state.data || [],
                    year: legacyApp.state.year,
                    availableYears: legacyApp.state.availableYears || [],
                    currentView: legacyApp.state.currentView || 'dashboard',
                    theme: legacyApp.state.theme || 'dark'
                });
            }
        }

        // Expose to global scope
        window.YuKyuModern = {
            App: YuKyuApp,
            State,
            adapter,
            config: CONFIG,
            features: FEATURES
        };

        // Dispatch ready event
        window.dispatchEvent(new CustomEvent('yukyu:modern-ready', {
            detail: { YuKyuApp, adapter, State }
        }));

        log('Modern UI initialized successfully');
        return { success: true, YuKyuApp, adapter };

    } catch (error) {
        console.error('[Bootstrap] Failed to initialize modern UI:', error);
        return { success: false, reason: 'initialization-error', error };
    }
}

/**
 * Initialize page router for modern pages
 * @param {string} initialPage - Initial page to show
 */
export async function initRouter(initialPage = 'dashboard') {
    log('Initializing router...');

    try {
        const { default: YuKyuApp } = await import('./index.js');

        // Navigate to initial page
        YuKyuApp.navigate(initialPage);

        // Listen for navigation events from legacy App
        document.addEventListener('click', (e) => {
            const navItem = e.target.closest('[data-view]');
            if (navItem) {
                const viewName = navItem.dataset.view;
                log('Navigation to:', viewName);
                // YuKyuApp.navigate(viewName);
            }
        });

        return true;
    } catch (error) {
        console.error('[Bootstrap] Failed to initialize router:', error);
        return false;
    }
}

/**
 * Load components on demand
 * @param {string[]} componentNames - Component names to load
 * @returns {Object} Loaded components
 */
export async function loadComponents(componentNames) {
    log('Loading components:', componentNames);

    const components = {};

    try {
        const module = await import('./components/index.js');

        componentNames.forEach(name => {
            if (module[name]) {
                components[name] = module[name];
            } else {
                console.warn(`[Bootstrap] Component "${name}" not found`);
            }
        });

        return components;
    } catch (error) {
        console.error('[Bootstrap] Failed to load components:', error);
        return components;
    }
}

/**
 * Check if modern UI is ready
 * @returns {boolean} True if modern UI is initialized
 */
export function isModernUIReady() {
    return window.YuKyuModern !== undefined;
}

/**
 * Wait for modern UI to be ready
 * @param {number} timeout - Timeout in ms
 * @returns {Promise} Resolves when ready
 */
export function waitForModernUI(timeout = 5000) {
    return new Promise((resolve, reject) => {
        if (isModernUIReady()) {
            resolve(window.YuKyuModern);
            return;
        }

        const startTime = Date.now();
        const check = setInterval(() => {
            if (isModernUIReady()) {
                clearInterval(check);
                resolve(window.YuKyuModern);
            } else if (Date.now() - startTime > timeout) {
                clearInterval(check);
                reject(new Error('Modern UI initialization timeout'));
            }
        }, 100);
    });
}

/**
 * Enable debug mode
 */
export function enableDebug() {
    localStorage.setItem('yukyu_debug', 'true');
    CONFIG.debug = true;
    console.log('[Bootstrap] Debug mode enabled. Reload page to see debug logs.');
}

/**
 * Disable debug mode
 */
export function disableDebug() {
    localStorage.removeItem('yukyu_debug');
    CONFIG.debug = false;
    console.log('[Bootstrap] Debug mode disabled.');
}

// Export configuration
export { CONFIG, FEATURES };

// Default export
export default {
    initModernUI,
    initRouter,
    loadComponents,
    isModernUIReady,
    waitForModernUI,
    enableDebug,
    disableDebug,
    CONFIG,
    FEATURES
};
