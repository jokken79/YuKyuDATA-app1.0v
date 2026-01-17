/**
 * Pages Index
 * Exporta todas las paginas para uso centralizado
 * @version 1.0.0
 */

// Import all pages
import * as Dashboard from './Dashboard.js';
import * as Employees from './Employees.js';
import * as LeaveRequests from './LeaveRequests.js';
import * as Analytics from './Analytics.js';
import * as Compliance from './Compliance.js';
import * as Notifications from './Notifications.js';
import * as Settings from './Settings.js';

// Re-export pages
export {
    Dashboard,
    Employees,
    LeaveRequests,
    Analytics,
    Compliance,
    Notifications,
    Settings
};

// Page registry for dynamic loading
export const pages = {
    dashboard: Dashboard,
    employees: Employees,
    requests: LeaveRequests,
    analytics: Analytics,
    compliance: Compliance,
    notifications: Notifications,
    settings: Settings
};

/**
 * Get page module by name
 * @param {string} pageName
 * @returns {Object|null} Page module
 */
export function getPage(pageName) {
    return pages[pageName] || null;
}

/**
 * Initialize all pages
 */
export function initAllPages() {
    Object.values(pages).forEach(page => {
        if (page.init) {
            page.init();
        }
    });
}

/**
 * Cleanup all pages
 */
export function cleanupAllPages() {
    Object.values(pages).forEach(page => {
        if (page.cleanup) {
            page.cleanup();
        }
    });
}

// Export default
export default {
    Dashboard,
    Employees,
    LeaveRequests,
    Analytics,
    Compliance,
    Notifications,
    Settings,
    pages,
    getPage,
    initAllPages,
    cleanupAllPages
};
