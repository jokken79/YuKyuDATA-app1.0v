/**
 * Analytics Manager
 * Handles analytics view rendering and interactions
 * @version 1.0.0
 */

export class AnalyticsManager {
    constructor(unifiedState) {
        this.state = unifiedState;
        this.isInitialized = false;
        this.subscriptionId = null;
        this.container = null;
        this.charts = {};
    }

    /**
     * Initialize analytics manager
     */
    async init() {
        if (this.isInitialized) return;

        this.isInitialized = true;

        this.subscriptionId = this.state.subscribe(
            (newState, prevState, changedKeys) => this.onStateChange(newState, prevState, changedKeys),
            ['data', 'year'],
            'AnalyticsManager'
        );

        await this.render();
    }

    /**
     * Render analytics view
     */
    async render() {
        try {
            const container = document.getElementById('view-analytics');
            if (!container) return;

            this.container = container;

            // Render statistics
            this._renderStatistics();

            // Render factory charts
            this._renderFactoryCharts();

            // Render type distribution
            this._renderTypeDistribution();

            // Attach event listeners
            this._attachEventListeners();

        } catch (error) {
            console.error('Analytics render error:', error);
        }
    }

    /**
     * Render statistics section
     * @private
     */
    _renderStatistics() {
        const statsContainer = this.container?.querySelector('[data-section="statistics"]');
        if (!statsContainer) return;

        const stats = this.state.getStatistics();
        const factoryStats = this.state.getFactoryStats();

        // Update stat cards
        const statCards = {
            'stat-employees': { value: stats.total, label: '従業員数' },
            'stat-granted': { value: stats.granted.toFixed(1), label: '付与日数' },
            'stat-used': { value: stats.used.toFixed(1), label: '使用日数' },
            'stat-balance': { value: stats.balance.toFixed(1), label: '残日数' },
            'stat-rate': { value: `${stats.avgRate}%`, label: '平均使用率' }
        };

        Object.entries(statCards).forEach(([id, data]) => {
            const card = statsContainer.querySelector(`#${id}`);
            if (card) {
                const valueEl = card.querySelector('[data-value]');
                if (valueEl) valueEl.textContent = data.value;
            }
        });

        // Top 5 factories
        const topFactories = factoryStats.slice(0, 5);
        const factoryList = statsContainer.querySelector('[data-factory-list]');
        if (factoryList) {
            factoryList.innerHTML = topFactory.map(([factory, days]) => `
                <div class="factory-item">
                    <span>${factory}</span>
                    <span class="days">${days.toFixed(1)}</span>
                </div>
            `).join('');
        }
    }

    /**
     * Render factory charts
     * @private
     */
    _renderFactoryCharts() {
        try {
            if (window.App && window.App.charts) {
                if (typeof window.App.charts.renderFactoryChart === 'function') {
                    window.App.charts.renderFactoryChart();
                }
            }
        } catch (error) {
            console.error('Factory chart render error:', error);
        }
    }

    /**
     * Render type distribution
     * @private
     */
    _renderTypeDistribution() {
        try {
            if (window.App && window.App.charts) {
                if (typeof window.App.charts.renderTypes === 'function') {
                    window.App.charts.renderTypes();
                }
            }
        } catch (error) {
            console.error('Type distribution render error:', error);
        }
    }

    /**
     * Handle state changes
     * @private
     */
    onStateChange(newState, prevState, changedKeys) {
        try {
            if (changedKeys.includes('data') || changedKeys.includes('year')) {
                this.render();
            }
        } catch (error) {
            console.error('Analytics state change handler error:', error);
        }
    }

    /**
     * Attach event listeners
     * @private
     */
    _attachEventListeners() {
        if (!this.container) return;

        // Download buttons
        const downloadBtn = this.container.querySelector('[data-action="download"]');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.onDownloadAnalytics());
        }

        // Refresh button
        const refreshBtn = this.container.querySelector('[data-action="refresh"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.onRefresh());
        }

        // Export PDF button
        const exportPdfBtn = this.container.querySelector('[data-action="export-pdf"]');
        if (exportPdfBtn) {
            exportPdfBtn.addEventListener('click', () => this.onExportPDF());
        }
    }

    /**
     * Handle download analytics
     */
    async onDownloadAnalytics() {
        try {
            if (window.App && window.App.exportService) {
                const data = this.state.getFilteredData();
                await window.App.exportService.toCSV(data, `analytics-${this.state.get('year')}.csv`);
            }
        } catch (error) {
            console.error('Download error:', error);
        }
    }

    /**
     * Handle export to PDF
     */
    async onExportPDF() {
        try {
            if (window.App && window.App.reports) {
                await window.App.reports.generateAnalyticsPDF(this.state.get('year'));
            }
        } catch (error) {
            console.error('Export PDF error:', error);
        }
    }

    /**
     * Handle refresh
     */
    async onRefresh() {
        try {
            this.state.set('isLoading', true);
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
            if (this.subscriptionId) {
                this.subscriptionId();
                this.subscriptionId = null;
            }

            Object.values(this.charts).forEach(chart => {
                if (chart && typeof chart.destroy === 'function') {
                    chart.destroy();
                }
            });
            this.charts = {};

            if (this.container) {
                const allButtons = this.container.querySelectorAll('button');
                allButtons.forEach(btn => {
                    btn.removeEventListener('click', null);
                });
            }

            this.container = null;
            this.isInitialized = false;
        } catch (error) {
            console.error('Analytics cleanup error:', error);
        }
    }
}

export default AnalyticsManager;
