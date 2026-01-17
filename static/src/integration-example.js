/**
 * Integration Example
 * Shows how to gradually migrate from app.js to modular structure
 *
 * Usage in HTML:
 * <script type="module" src="/static/src/integration-example.js"></script>
 *
 * This should be loaded AFTER app.js
 */

// Import new modular structure
import YuKyuApp, {
    State,
    Constants,
    Dashboard,
    Employees,
    LeaveRequests,
    Analytics,
    Compliance,
    Notifications,
    Settings,
    integrateWithLegacyApp
} from './index.js';

/**
 * Wait for legacy App to be available
 */
function waitForLegacyApp(timeout = 5000) {
    return new Promise((resolve, reject) => {
        if (window.App) {
            resolve(window.App);
            return;
        }

        const startTime = Date.now();
        const check = setInterval(() => {
            if (window.App) {
                clearInterval(check);
                resolve(window.App);
            } else if (Date.now() - startTime > timeout) {
                clearInterval(check);
                reject(new Error('Legacy App not found'));
            }
        }, 100);
    });
}

/**
 * Setup integration
 */
async function setup() {
    try {
        // Wait for legacy App
        const App = await waitForLegacyApp();

        console.log('[Integration] Legacy App found, setting up bridge...');

        // Integrate new modules with legacy App
        integrateWithLegacyApp(App);

        // Sync state from legacy App
        if (App.state) {
            State.setState({
                data: App.state.data || [],
                year: App.state.year,
                availableYears: App.state.availableYears || [],
                currentView: App.state.currentView || 'dashboard',
                typeFilter: App.state.typeFilter || 'all'
            });
        }

        // Subscribe to state changes and sync back to legacy
        State.subscribe((newState, prevState) => {
            // Only sync specific properties back to legacy App
            if (newState.year !== prevState.year && App.state) {
                App.state.year = newState.year;
            }
            if (newState.currentView !== prevState.currentView && App.state) {
                App.state.currentView = newState.currentView;
            }
        });

        // Extend legacy App with helper methods
        App.src = {
            // Access to new page modules
            pages: YuKyuApp.pages,

            // State management
            getState: State.getState,
            setState: State.setState,
            subscribe: State.subscribe,

            // Constants
            API_BASE_URL: Constants.API_BASE_URL,
            ENDPOINTS: Constants.ENDPOINTS,
            CHART_COLORS: Constants.CHART_COLORS,

            // Navigate using new system
            navigate: (viewName) => YuKyuApp.navigate(viewName)
        };

        // Initialize notification polling
        Notifications.init();

        console.log('[Integration] Bridge setup complete!');
        console.log('[Integration] Access new modules via App.src.*');
        console.log('[Integration] Example: App.src.pages.Dashboard.render()');

        // Dispatch event for other scripts to know integration is ready
        window.dispatchEvent(new CustomEvent('yukyu:integration-ready', {
            detail: { App, YuKyuApp, State }
        }));

    } catch (error) {
        console.error('[Integration] Setup failed:', error);
    }
}

// Run setup when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
} else {
    setup();
}

// Export for manual use
export { waitForLegacyApp, setup };
export default { waitForLegacyApp, setup };
