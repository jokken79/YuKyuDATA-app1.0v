/**
 * Compliance Manager
 * Handles compliance/5-day requirement view rendering and interactions
 * @version 1.0.0
 */

export class ComplianceManager {
    constructor(unifiedState) {
        this.state = unifiedState;
        this.isInitialized = false;
        this.subscriptionId = null;
        this.container = null;
        this.alerts = [];
        this.violations = [];
    }

    /**
     * Initialize compliance manager
     */
    async init() {
        if (this.isInitialized) return;

        this.isInitialized = true;

        this.subscriptionId = this.state.subscribe(
            (newState, prevState, changedKeys) => this.onStateChange(newState, prevState, changedKeys),
            ['data', 'year'],
            'ComplianceManager'
        );

        await this.render();
    }

    /**
     * Render compliance view
     */
    async render() {
        try {
            const container = document.getElementById('view-compliance');
            if (!container) return;

            this.container = container;

            // Load compliance data
            await this._loadComplianceData();

            // Render alerts
            this._renderAlerts();

            // Render violations table
            this._renderViolations();

            // Render summary
            this._renderSummary();

            // Attach event listeners
            this._attachEventListeners();

        } catch (error) {
            console.error('Compliance render error:', error);
        }
    }

    /**
     * Load compliance data from server
     * @private
     */
    async _loadComplianceData() {
        try {
            if (window.App && window.App.compliance) {
                if (typeof window.App.compliance.loadAlerts === 'function') {
                    await window.App.compliance.loadAlerts();
                }
            }
        } catch (error) {
            console.error('Failed to load compliance data:', error);
        }
    }

    /**
     * Render compliance alerts
     * @private
     */
    _renderAlerts() {
        const alertsContainer = this.container?.querySelector('[data-section="alerts"]');
        if (!alertsContainer) return;

        // Clear existing alerts
        const alertsList = alertsContainer.querySelector('[data-alerts-list]');
        if (!alertsList) return;

        alertsList.innerHTML = '';

        const year = this.state.get('year');
        const data = this.state.getFilteredData();

        // Check for 5-day compliance violations
        const violations = [];

        data.forEach(emp => {
            // Employee needs 10+ days to have 5-day requirement
            if (parseFloat(emp.granted) >= 10) {
                const used = parseFloat(emp.used) || 0;
                const required = 5;

                if (used < required) {
                    const remaining = required - used;
                    violations.push({
                        empNum: emp.employee_num || emp.num,
                        name: emp.name || emp.氏名,
                        granted: parseFloat(emp.granted),
                        used: used,
                        required: required,
                        remaining: remaining,
                        daysLeft: remaining,
                        severity: remaining > 10 ? 'warning' : 'danger'
                    });
                }
            }
        });

        this.violations = violations;

        if (violations.length === 0) {
            alertsList.innerHTML = '<div class="alert alert-success">問題ありません - 全従業員が5日要件を満たしています</div>';
            return;
        }

        // Render violation alerts
        violations.forEach(violation => {
            const alert = document.createElement('div');
            alert.className = `alert alert-${violation.severity}`;
            alert.innerHTML = `
                <strong>${violation.name} (${violation.empNum})</strong><br/>
                付与: ${violation.granted.toFixed(1)}日
                使用: ${violation.used.toFixed(1)}日
                要件: ${violation.required}日
                残り: ${violation.remaining.toFixed(1)}日
            `;
            alertsList.appendChild(alert);
        });
    }

    /**
     * Render violations table
     * @private
     */
    _renderViolations() {
        const tableContainer = this.container?.querySelector('[data-section="violations"]');
        if (!tableContainer) return;

        const tbody = tableContainer.querySelector('tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        this.violations.forEach(violation => {
            const row = document.createElement('tr');
            row.className = violation.severity === 'danger' ? 'table-danger' : 'table-warning';
            row.innerHTML = `
                <td>${violation.empNum}</td>
                <td>${violation.name}</td>
                <td class="text-right">${violation.granted.toFixed(1)}</td>
                <td class="text-right">${violation.used.toFixed(1)}</td>
                <td class="text-right">${violation.required}</td>
                <td class="text-right font-weight-bold">${violation.remaining.toFixed(1)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" data-action="request-leave" data-emp-num="${violation.empNum}">
                        申請
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    /**
     * Render compliance summary
     * @private
     */
    _renderSummary() {
        const summaryContainer = this.container?.querySelector('[data-section="summary"]');
        if (!summaryContainer) return;

        const data = this.state.getFilteredData();
        const total = data.length;
        const violations = this.violations.length;
        const compliant = total - violations;
        const complianceRate = total > 0 ? Math.round((compliant / total) * 100) : 100;

        summaryContainer.innerHTML = `
            <div class="summary-stat">
                <span class="label">対象従業員数</span>
                <span class="value">${total}</span>
            </div>
            <div class="summary-stat">
                <span class="label">要件満たし</span>
                <span class="value text-success">${compliant}</span>
            </div>
            <div class="summary-stat">
                <span class="label">問題あり</span>
                <span class="value text-danger">${violations}</span>
            </div>
            <div class="summary-stat">
                <span class="label">コンプライアンス率</span>
                <span class="value">${complianceRate}%</span>
            </div>
        `;
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
            console.error('Compliance state change handler error:', error);
        }
    }

    /**
     * Attach event listeners
     * @private
     */
    _attachEventListeners() {
        if (!this.container) return;

        // Request leave buttons
        const requestButtons = this.container.querySelectorAll('[data-action="request-leave"]');
        requestButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const empNum = e.target.dataset.empNum;
                this.onRequestLeave(empNum);
            });
        });

        // Generate report button
        const reportBtn = this.container.querySelector('[data-action="report"]');
        if (reportBtn) {
            reportBtn.addEventListener('click', () => this.onGenerateReport());
        }

        // Export button
        const exportBtn = this.container.querySelector('[data-action="export"]');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.onExportData());
        }

        // Refresh button
        const refreshBtn = this.container.querySelector('[data-action="refresh"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.onRefresh());
        }
    }

    /**
     * Handle request leave for employee
     */
    onRequestLeave(empNum) {
        try {
            if (window.App && window.App.openNewLeaveRequest) {
                window.App.openNewLeaveRequest(empNum);
            }
        } catch (error) {
            console.error('Request leave error:', error);
        }
    }

    /**
     * Handle generate compliance report
     */
    async onGenerateReport() {
        try {
            if (window.App && window.App.reports) {
                const year = this.state.get('year');
                await window.App.reports.generateComplianceReport(year);
            }
        } catch (error) {
            console.error('Generate report error:', error);
        }
    }

    /**
     * Handle export violations data
     */
    async onExportData() {
        try {
            if (window.App && window.App.exportService) {
                await window.App.exportService.toCSV(
                    this.violations,
                    `compliance-violations-${this.state.get('year')}.csv`
                );
            }
        } catch (error) {
            console.error('Export data error:', error);
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

            if (this.container) {
                const allButtons = this.container.querySelectorAll('button');
                allButtons.forEach(btn => {
                    btn.removeEventListener('click', null);
                });
            }

            this.alerts = [];
            this.violations = [];
            this.container = null;
            this.isInitialized = false;
        } catch (error) {
            console.error('Compliance cleanup error:', error);
        }
    }
}

export default ComplianceManager;
