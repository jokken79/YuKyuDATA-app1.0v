/**
 * YuKyu Application Entry Point (Modular)
 * Replaces the monolithic app.js
 */

import { Auth } from './modules/auth.js';
import { Visualizations } from './modules/visualizations.js';
import { I18n } from './modules/i18n.js';
import { Router } from './modules/router.js';
import { UI } from './modules/ui.js';
import { Utils } from './modules/utils.js';
import { dataService } from './modules/data-service.js';

const App = {
    state: {
        employees: [],
        currentYear: new Date().getFullYear(),
        loading: false,
        availableYears: []
    },

    config: {
        apiBase: '/api/v1'
    },

    async init() {
        console.log('🚀 YuKyu Dashboard Initializing (Modular Ver)...');

        UI.init();

        // Initialize Auth with UI callback
        Auth.init(async (isLoggedIn) => {
            if (isLoggedIn) {
                document.body.classList.add('logged-in');

                // Configure data service with auth token
                dataService.apiBase = this.config.apiBase;

                await this.loadData();
            } else {
                document.body.classList.remove('logged-in');
                Auth.showLogin();
            }
        });

        await I18n.init();

        Router.init((route) => {
            console.log('Navigating to:', route);
            UI.switchView(route);
        });

        this.bindGlobalEvents();
        UI.hideLoading();
    },

    bindGlobalEvents() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;

            const action = btn.dataset.action;
            const id = btn.dataset.id;
            const view = btn.dataset.view;

            if (action === 'ui.switchView' && view) Router.navigate(view);
            if (action === 'theme.toggle') UI.toggleTheme();
            if (action === 'auth.showLogin') Auth.showLogin();
            if (action === 'auth.logout') Auth.logout();
            if (action === 'data.sync') this.handleSync();

            if (action === 'edit' && id) this.handleEdit(id);
            if (action === 'delete' && id) this.handleDelete(id);
        });
    },

    async loadData() {
        if (!Auth.token) return;

        UI.showLoading();
        try {
            // Use real DataService for fetching
            await dataService.fetchEmployees(
                this.state.currentYear,
                true,
                this.state,
                () => this.render(),
                (type, msg) => UI.showToast(type, msg)
            );

            // Populate year selector if we have years
            if (this.state.availableYears.length > 0) {
                UI.populateYearSelector(this.state.currentYear, this.state.availableYears, (newYear) => {
                    this.state.currentYear = newYear;
                    this.loadData();
                });
            }

        } catch (error) {
            console.error(error);
            UI.showToast('error', 'Error loading data: ' + error.message);
        } finally {
            UI.hideLoading();
        }
    },

    render() {
        // Render statistics components
        UI.updateStatsFromData(this.state.employees);

        // Update Visualizations (Rings and Charts)
        Visualizations.updateStatsFromEmployees(this.state.employees);

        // Render Employees Table
        UI.renderEmployeesTable(this.state.employees);
    },

    async handleSync() {
        await dataService.sync(
            (btn, loading) => UI.setBtnLoading(btn, loading),
            (type, msg) => UI.showToast(type, msg),
            () => this.loadData()
        );
    },

    handleEdit(id) {
        console.log('Edit employee', id);
        UI.openModal(id);
    },

    handleDelete(id) {
        if (confirm('Are you sure?')) {
            // Implement delete via dataService if needed
            console.log('Delete employee', id);
        }
    }
};

// Make App global for legacy debugging if needed, but encourage module use
window.App = App;

// Start
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
