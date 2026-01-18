/**
 * Page Coordinator
 * Coordinates page manager lifecycle and switching
 * @version 1.0.0
 */

import { DashboardManager } from './DashboardManager.js';
import { EmployeesManager } from './EmployeesManager.js';
import { LeaveRequestsManager } from './LeaveRequestsManager.js';
import { AnalyticsManager } from './AnalyticsManager.js';
import { ComplianceManager } from './ComplianceManager.js';

export class PageCoordinator {
    constructor(unifiedState) {
        this.state = unifiedState;

        // Initialize all managers
        this.managers = {
            dashboard: new DashboardManager(unifiedState),
            employees: new EmployeesManager(unifiedState),
            requests: new LeaveRequestsManager(unifiedState),
            analytics: new AnalyticsManager(unifiedState),
            compliance: new ComplianceManager(unifiedState)
        };

        this.currentPage = null;
        this.currentManager = null;
    }

    /**
     * Switch to a different page/manager
     * @param {string} pageName - Name of the page (dashboard, employees, requests, analytics, compliance)
     * @param {Object} [options] - Additional options
     */
    async switchPage(pageName, options = {}) {
        try {
            // Validate page name
            if (!this.managers[pageName]) {
                console.error(`Unknown page: ${pageName}`);
                return;
            }

            // Cleanup current manager
            if (this.currentManager && this.currentManager.cleanup) {
                this.currentManager.cleanup();
            }

            // Show page element and hide others
            this._showPage(pageName);

            // Update state
            this.state.set('currentView', pageName);

            // Initialize new manager
            const manager = this.managers[pageName];
            await manager.init();

            this.currentPage = pageName;
            this.currentManager = manager;

            // Update navigation
            this._updateNavigation(pageName);

            // Update page title
            this._updatePageTitle(pageName);

        } catch (error) {
            console.error(`Failed to switch to page ${pageName}:`, error);
        }
    }

    /**
     * Show/hide page elements
     * @private
     */
    _showPage(pageName) {
        // Hide all views
        document.querySelectorAll('.view-section').forEach(el => {
            el.classList.remove('active');
            el.classList.remove('d-block');
            el.classList.add('d-none');
            el.style.display = 'none';
        });

        // Show target view
        const target = document.getElementById(`view-${pageName}`);
        if (target) {
            target.classList.remove('d-none');
            target.classList.add('d-block');
            target.style.display = 'block';
            setTimeout(() => {
                target.classList.add('active');
                // Animate if GSAP available
                if (window.App && window.App.animations && window.App.animations.transitionView) {
                    window.App.animations.transitionView(target);
                }
            }, 10);
        }
    }

    /**
     * Update sidebar navigation
     * @private
     */
    _updateNavigation(pageName) {
        // Remove active class from all nav items
        document.querySelectorAll('.nav-item').forEach(el => {
            el.classList.remove('active');
        });

        // Add active class to current nav item
        const activeNav = document.querySelector(`.nav-item[data-view="${pageName}"]`);
        if (activeNav) {
            activeNav.classList.add('active');
        }
    }

    /**
     * Update page title
     * @private
     */
    _updatePageTitle(pageName) {
        const titleMap = {
            'dashboard': 'ダッシュボード',
            'employees': '従業員一覧',
            'requests': '有給休暇申請',
            'analytics': '詳細分析',
            'compliance': 'コンプライアンス'
        };

        const titleEl = document.getElementById('page-title');
        if (titleEl) {
            titleEl.textContent = titleMap[pageName] || 'Dashboard';
        }
    }

    /**
     * Get current manager
     * @returns {Object} Current manager instance
     */
    getCurrentManager() {
        return this.currentManager;
    }

    /**
     * Get specific manager
     * @param {string} pageName - Page name
     * @returns {Object} Manager instance
     */
    getManager(pageName) {
        return this.managers[pageName];
    }

    /**
     * Get all managers
     * @returns {Object} All managers
     */
    getAllManagers() {
        return { ...this.managers };
    }

    /**
     * Refresh current page
     */
    async refreshCurrentPage() {
        if (this.currentManager && this.currentManager.render) {
            await this.currentManager.render();
        }
    }

    /**
     * Cleanup all managers
     */
    cleanup() {
        try {
            Object.values(this.managers).forEach(manager => {
                if (manager && manager.cleanup) {
                    manager.cleanup();
                }
            });
            this.currentManager = null;
            this.currentPage = null;
        } catch (error) {
            console.error('Cleanup error:', error);
        }
    }
}

export default PageCoordinator;
