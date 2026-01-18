/**
 * YuKyu Frontend Entry Point
 * Punto de entrada principal que importa y coordina todos los modulos
 * @version 1.0.0
 */

// Store
import * as State from './store/state.js';
import { UnifiedState, getUnifiedState } from './store/unified-state.js';

// Config
import * as Constants from './config/constants.js';

// Managers (TAREA 3-4)
import { PageCoordinator } from './managers/PageCoordinator.js';
import {
    DashboardManager,
    EmployeesManager,
    LeaveRequestsManager,
    AnalyticsManager,
    ComplianceManager
} from './managers/index.js';

// Legacy Bridge (TAREA 4)
import {
    initUnifiedStateBridge,
    switchPageModern,
    subscribeToState,
    getPageCoordinator
} from './legacy-bridge/unified-state-bridge.js';

// Consolidated Utils (TAREA 5)
import * as Utils from './utils/consolidated.js';

// Pages
import {
    Dashboard,
    Employees,
    LeaveRequests,
    Analytics,
    Compliance,
    Notifications,
    Settings,
    pages,
    initAllPages,
    cleanupAllPages
} from './pages/index.js';

// ========================================
// APPLICATION COORDINATOR
// ========================================

/**
 * YuKyu Application Module
 * Coordina todos los modulos de la aplicacion
 */
const YuKyuApp = {
    // Version
    version: '1.0.0',

    // Expose modules
    State,
    Constants,

    // Modern Managers (TAREA 3)
    managers: {
        Dashboard: DashboardManager,
        Employees: EmployeesManager,
        LeaveRequests: LeaveRequestsManager,
        Analytics: AnalyticsManager,
        Compliance: ComplianceManager,
        PageCoordinator
    },

    // State Management (TAREA 4)
    UnifiedState,
    getUnifiedState,
    initUnifiedStateBridge,
    switchPageModern,

    // Utilities (TAREA 5)
    Utils,

    // Pages (Legacy)
    pages: {
        Dashboard,
        Employees,
        LeaveRequests,
        Analytics,
        Compliance,
        Notifications,
        Settings
    },

    // Current page
    currentPage: null,

    /**
     * Initialize application
     */
    async init() {
        console.log('YuKyu Frontend v' + this.version + ' initializing...');

        // Initialize all page modules
        initAllPages();

        // Initialize notifications (for badge polling)
        Notifications.init();

        // Set initial page
        const initialView = State.getStateValue('currentView') || 'dashboard';
        this.navigate(initialView);

        console.log('YuKyu Frontend initialized');
    },

    /**
     * Navigate to a page
     * @param {string} pageName - Page name
     */
    navigate(pageName) {
        // Get page module
        const page = pages[pageName];
        if (!page) {
            console.warn(`Page "${pageName}" not found`);
            return;
        }

        // Cleanup current page if exists
        if (this.currentPage && this.currentPage.cleanup) {
            this.currentPage.cleanup();
        }

        // Update state
        State.setStateValue('currentView', pageName);

        // Set new current page
        this.currentPage = page;

        // Initialize/render new page
        if (page.init) {
            page.init();
        }
        if (page.render) {
            page.render();
        }

        console.log(`Navigated to: ${pageName}`);
    },

    /**
     * Get state helper
     */
    getState() {
        return State.getState();
    },

    /**
     * Set state helper
     * @param {Object} updates
     */
    setState(updates) {
        State.setState(updates);
    },

    /**
     * Cleanup on destroy
     */
    destroy() {
        cleanupAllPages();
        console.log('YuKyu Frontend destroyed');
    }
};

// ========================================
// INTEGRATION WITH EXISTING APP
// ========================================

/**
 * Bridge module for backwards compatibility with existing App object
 * This allows gradual migration from app.js to the new modular structure
 */
export function integrateWithLegacyApp(App) {
    if (!App) {
        console.warn('Legacy App object not found');
        return;
    }

    // Attach new modules to legacy App
    App.pages = YuKyuApp.pages;
    App.State = State;
    App.Constants = Constants;

    // Override or extend specific functions
    const originalSwitchView = App.ui?.switchView;
    if (originalSwitchView) {
        App.ui.switchView = function(viewName) {
            // Call original
            originalSwitchView.call(App.ui, viewName);

            // Also trigger new page module
            YuKyuApp.navigate(viewName);
        };
    }

    console.log('YuKyu modules integrated with legacy App');
}

// ========================================
// EXPORTS
// ========================================

// Named exports
export {
    // State Management
    State,
    UnifiedState,
    getUnifiedState,
    initUnifiedStateBridge,

    // Managers (TAREA 3-4)
    PageCoordinator,
    DashboardManager,
    EmployeesManager,
    LeaveRequestsManager,
    AnalyticsManager,
    ComplianceManager,

    // Config
    Constants,

    // Utils (TAREA 5)
    Utils,

    // Pages (Legacy)
    Dashboard,
    Employees,
    LeaveRequests,
    Analytics,
    Compliance,
    Notifications,
    Settings,
    pages,
    initAllPages,
    cleanupAllPages
};

// Default export
export default YuKyuApp;

// Auto-initialize when DOM is ready
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            // Check if we should auto-initialize
            if (window.__YUKYU_AUTO_INIT__) {
                YuKyuApp.init();
            }
        });
    }
}

// Expose to window for debugging
if (typeof window !== 'undefined') {
    window.YuKyuApp = YuKyuApp;
}
