/**
 * Dashboard Manager
 * Handles dashboard view rendering and interactions
 * @version 1.0.0
 */

export class DashboardManager {
    constructor(unifiedState) {
        this.state = unifiedState;
        this.isInitialized = false;
        this.charts = {};
        this.subscriptionId = null;
        this.container = null;
    }

    /**
     * Initialize dashboard manager
     */
    async init() {
        if (this.isInitialized) return;

        this.isInitialized = true;

        // Subscribe to relevant state changes
        this.subscriptionId = this.state.subscribe(
            (newState, prevState, changedKeys) => this.onStateChange(newState, prevState, changedKeys),
            ['data', 'year', 'typeFilter'],
            'DashboardManager'
        );

        // Render dashboard
        await this.render();
    }

    /**
     * Render dashboard content
     */
    async render() {
        try {
            const container = document.getElementById('view-dashboard');
            if (!container) return;

            this.container = container;

            // Get statistics from state
            const stats = this.state.getStatistics();

            // Render KPI cards
            this._renderKPICards(stats);

            // Initialize charts
            await this._initializeCharts();

            // Attach event listeners
            this._attachEventListeners();

        } catch (error) {
            console.error('Dashboard render error:', error);
        }
    }

    /**
     * Render KPI cards
     * @private
     */
    _renderKPICards(stats) {
        // Update KPI values in DOM
        const kpiMap = {
            'kpi-employees': stats.total,
            'kpi-granted': stats.granted.toFixed(1),
            'kpi-used': stats.used.toFixed(1),
            'kpi-balance': stats.balance.toFixed(1),
            'kpi-rate': `${stats.avgRate}%`
        };

        Object.entries(kpiMap).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = value;
            }
        });
    }

    /**
     * Initialize charts (Chart.js, ApexCharts)
     * @private
     */
    async _initializeCharts() {
        try {
            // Get chart containers
            const distributionContainer = document.getElementById('chart-distribution');
            const trendsContainer = document.getElementById('chart-trends');

            if (!distributionContainer || !trendsContainer) {
                return;
            }

            // Charts will be managed by external chart manager
            // This manager ensures containers are ready
            if (window.App && window.App.charts) {
                if (typeof window.App.charts.renderDistribution === 'function') {
                    window.App.charts.renderDistribution();
                }
                if (typeof window.App.charts.renderTrends === 'function') {
                    window.App.charts.renderTrends();
                }
            }
        } catch (error) {
            console.error('Chart initialization error:', error);
        }
    }

    /**
     * Handle state changes
     * @private
     */
    onStateChange(newState, prevState, changedKeys) {
        try {
            // Re-render if data or year changed
            if (changedKeys.includes('data') || changedKeys.includes('year')) {
                this._renderKPICards(this.state.getStatistics());

                // Re-initialize charts with new data
                this._initializeCharts();
            }
        } catch (error) {
            console.error('Dashboard state change handler error:', error);
        }
    }

    /**
     * Attach event listeners
     * @private
     */
    _attachEventListeners() {
        if (!this.container) return;

        // Add dashboard-specific event listeners here
        // Example: refresh button
        const refreshBtn = this.container.querySelector('[data-action="refresh"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.onRefresh());
        }
    }

    /**
     * Handle refresh action
     */
    async onRefresh() {
        try {
            this.state.set('isLoading', true);

            // Fetch updated data
            if (window.App && window.App.sync) {
                await window.App.sync();
            }

            await this.render();

            this.state.set('isLoading', false);
        } catch (error) {
            console.error('Refresh error:', error);
            this.state.set('isLoading', false);
        }
    }

    /**
     * Clean up resources
     */
    cleanup() {
        try {
            // Unsubscribe from state changes
            if (this.subscriptionId) {
                this.subscriptionId();
                this.subscriptionId = null;
            }

            // Destroy charts
            Object.values(this.charts).forEach(chart => {
                if (chart && typeof chart.destroy === 'function') {
                    chart.destroy();
                }
            });
            this.charts = {};

            // Remove event listeners
            if (this.container) {
                const refreshBtn = this.container.querySelector('[data-action="refresh"]');
                if (refreshBtn) {
                    refreshBtn.removeEventListener('click', () => this.onRefresh());
                }
            }

            this.container = null;
            this.isInitialized = false;
        } catch (error) {
            console.error('Dashboard cleanup error:', error);
        }
    }
}

export default DashboardManager;
