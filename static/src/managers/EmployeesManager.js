/**
 * Employees Manager
 * Handles employees list view rendering and interactions
 * @version 1.0.0
 */

export class EmployeesManager {
    constructor(unifiedState) {
        this.state = unifiedState;
        this.isInitialized = false;
        this.subscriptionId = null;
        this.container = null;
        this.table = null;
        this.currentFilter = 'all';
    }

    /**
     * Initialize employees manager
     */
    async init() {
        if (this.isInitialized) return;

        this.isInitialized = true;

        // Subscribe to state changes
        this.subscriptionId = this.state.subscribe(
            (newState, prevState, changedKeys) => this.onStateChange(newState, prevState, changedKeys),
            ['data', 'year', 'typeFilter'],
            'EmployeesManager'
        );

        await this.render();
    }

    /**
     * Render employees list
     */
    async render() {
        try {
            const container = document.getElementById('view-employees');
            if (!container) return;

            this.container = container;

            // Get filtered data
            const employees = this.state.getFilteredData();

            // Render table
            this._renderTable(employees);

            // Attach event listeners
            this._attachEventListeners();

        } catch (error) {
            console.error('Employees render error:', error);
        }
    }

    /**
     * Render employees table
     * @private
     */
    _renderTable(employees) {
        const tableBody = this.container?.querySelector('tbody');
        if (!tableBody) return;

        // Clear existing rows
        tableBody.innerHTML = '';

        // Get filter preference
        const typeFilter = this.state.get('typeFilter') || 'all';

        // Filter employees by type
        const filtered = typeFilter === 'all'
            ? employees
            : employees.filter(e => {
                const empType = e.employeeType || e.type;
                return empType === typeFilter;
            });

        // Create rows
        filtered.forEach(emp => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${emp.employee_num || emp.num || '-'}</td>
                <td>${emp.name || emp.氏名 || '-'}</td>
                <td class="text-right">${parseFloat(emp.granted || 0).toFixed(1)}</td>
                <td class="text-right">${parseFloat(emp.used || 0).toFixed(1)}</td>
                <td class="text-right font-weight-bold">${parseFloat(emp.balance || 0).toFixed(1)}</td>
                <td>${emp.employeeType || emp.type || 'staff'}</td>
                <td>
                    <button class="btn btn-sm btn-ghost" data-action="edit" data-emp-num="${emp.employee_num || emp.num}">
                        編集
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });

        // Update employee count badge
        const badge = this.container?.querySelector('.badge');
        if (badge) {
            badge.textContent = `${filtered.length} Employees`;
        }
    }

    /**
     * Handle state changes
     * @private
     */
    onStateChange(newState, prevState, changedKeys) {
        try {
            if (changedKeys.includes('data') || changedKeys.includes('year') || changedKeys.includes('typeFilter')) {
                const employees = this.state.getFilteredData();
                this._renderTable(employees);
            }
        } catch (error) {
            console.error('Employees state change handler error:', error);
        }
    }

    /**
     * Attach event listeners
     * @private
     */
    _attachEventListeners() {
        if (!this.container) return;

        // Type filter buttons
        const filterButtons = this.container.querySelectorAll('[data-filter]');
        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.target.dataset.filter;
                this.state.set('typeFilter', filter);
            });
        });

        // Edit buttons
        const editButtons = this.container.querySelectorAll('[data-action="edit"]');
        editButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const empNum = e.target.dataset.empNum;
                this.onEditEmployee(empNum);
            });
        });

        // Refresh button
        const refreshBtn = this.container.querySelector('[data-action="refresh"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.onRefresh());
        }
    }

    /**
     * Handle employee edit
     */
    onEditEmployee(empNum) {
        try {
            // Delegate to App.editYukyu if available
            if (window.App && window.App.editYukyu) {
                window.App.editYukyu(empNum);
            }
        } catch (error) {
            console.error('Edit employee error:', error);
        }
    }

    /**
     * Handle refresh action
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

            // Remove event listeners
            if (this.container) {
                const filterButtons = this.container.querySelectorAll('[data-filter]');
                filterButtons.forEach(btn => {
                    btn.removeEventListener('click', null);
                });

                const editButtons = this.container.querySelectorAll('[data-action="edit"]');
                editButtons.forEach(btn => {
                    btn.removeEventListener('click', null);
                });

                const refreshBtn = this.container.querySelector('[data-action="refresh"]');
                if (refreshBtn) {
                    refreshBtn.removeEventListener('click', null);
                }
            }

            this.container = null;
            this.table = null;
            this.isInitialized = false;
        } catch (error) {
            console.error('Employees cleanup error:', error);
        }
    }
}

export default EmployeesManager;
