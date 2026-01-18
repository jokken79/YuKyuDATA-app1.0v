/**
 * Leave Requests Manager
 * Handles leave requests view rendering and interactions
 * @version 1.0.0
 */

export class LeaveRequestsManager {
    constructor(unifiedState) {
        this.state = unifiedState;
        this.isInitialized = false;
        this.subscriptionId = null;
        this.container = null;
        this.pendingRequests = [];
        this.approvedRequests = [];
    }

    /**
     * Initialize leave requests manager
     */
    async init() {
        if (this.isInitialized) return;

        this.isInitialized = true;

        this.subscriptionId = this.state.subscribe(
            (newState, prevState, changedKeys) => this.onStateChange(newState, prevState, changedKeys),
            ['data', 'year'],
            'LeaveRequestsManager'
        );

        await this.render();
    }

    /**
     * Render leave requests view
     */
    async render() {
        try {
            const container = document.getElementById('view-requests');
            if (!container) return;

            this.container = container;

            // Load requests data
            await this._loadRequests();

            // Render tabs
            this._renderTabs();

            // Attach event listeners
            this._attachEventListeners();

        } catch (error) {
            console.error('Leave requests render error:', error);
        }
    }

    /**
     * Load requests from server
     * @private
     */
    async _loadRequests() {
        try {
            // Fetch pending and approved requests
            if (window.App && window.App.requests) {
                if (typeof window.App.requests.loadPending === 'function') {
                    await window.App.requests.loadPending();
                }
                if (typeof window.App.requests.loadHistory === 'function') {
                    await window.App.requests.loadHistory();
                }
            }
        } catch (error) {
            console.error('Failed to load requests:', error);
        }
    }

    /**
     * Render request tabs
     * @private
     */
    _renderTabs() {
        const pendingContainer = this.container?.querySelector('[data-tab="pending"]');
        const approvedContainer = this.container?.querySelector('[data-tab="approved"]');

        if (pendingContainer && this.pendingRequests.length > 0) {
            this._renderRequestTable(pendingContainer, this.pendingRequests, 'pending');
        }

        if (approvedContainer && this.approvedRequests.length > 0) {
            this._renderRequestTable(approvedContainer, this.approvedRequests, 'approved');
        }
    }

    /**
     * Render request table
     * @private
     */
    _renderRequestTable(container, requests, status) {
        const tbody = container.querySelector('tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        requests.forEach(req => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${req.employee_num || req.empNum || '-'}</td>
                <td>${req.employee_name || req.name || '-'}</td>
                <td>${req.start_date || req.startDate || '-'}</td>
                <td>${req.end_date || req.endDate || '-'}</td>
                <td class="text-right">${parseFloat(req.days || 0).toFixed(1)}</td>
                <td>${req.reason || req.remarks || '-'}</td>
                <td>
                    ${status === 'pending' ? `
                        <button class="btn btn-sm btn-success" data-action="approve" data-request-id="${req.id}">
                            承認
                        </button>
                        <button class="btn btn-sm btn-danger" data-action="reject" data-request-id="${req.id}">
                            拒否
                        </button>
                    ` : `
                        <span class="badge badge-success">${req.status || 'Approved'}</span>
                    `}
                </td>
            `;
            tbody.appendChild(row);
        });
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
            console.error('Leave requests state change handler error:', error);
        }
    }

    /**
     * Attach event listeners
     * @private
     */
    _attachEventListeners() {
        if (!this.container) return;

        // Tab switching
        const tabButtons = this.container.querySelectorAll('[data-tab-btn]');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tabBtn;
                this._switchTab(tabName);
            });
        });

        // Approve buttons
        const approveButtons = this.container.querySelectorAll('[data-action="approve"]');
        approveButtons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const requestId = e.target.dataset.requestId;
                await this.onApproveRequest(requestId);
            });
        });

        // Reject buttons
        const rejectButtons = this.container.querySelectorAll('[data-action="reject"]');
        rejectButtons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const requestId = e.target.dataset.requestId;
                await this.onRejectRequest(requestId);
            });
        });

        // Create request button
        const createBtn = this.container.querySelector('[data-action="create"]');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.onCreateRequest());
        }
    }

    /**
     * Switch between tabs
     * @private
     */
    _switchTab(tabName) {
        const tabs = this.container?.querySelectorAll('[data-tab]');
        const buttons = this.container?.querySelectorAll('[data-tab-btn]');

        tabs?.forEach(tab => {
            tab.classList.remove('active');
        });

        buttons?.forEach(btn => {
            btn.classList.remove('active');
        });

        const activeTab = this.container?.querySelector(`[data-tab="${tabName}"]`);
        const activeBtn = this.container?.querySelector(`[data-tab-btn="${tabName}"]`);

        if (activeTab) activeTab.classList.add('active');
        if (activeBtn) activeBtn.classList.add('active');
    }

    /**
     * Handle approve request
     */
    async onApproveRequest(requestId) {
        try {
            if (window.App && window.App.requests && window.App.requests.approve) {
                await window.App.requests.approve(requestId);
                await this.render();
            }
        } catch (error) {
            console.error('Approve request error:', error);
        }
    }

    /**
     * Handle reject request
     */
    async onRejectRequest(requestId) {
        try {
            if (window.App && window.App.requests && window.App.requests.reject) {
                await window.App.requests.reject(requestId);
                await this.render();
            }
        } catch (error) {
            console.error('Reject request error:', error);
        }
    }

    /**
     * Handle create request
     */
    onCreateRequest() {
        try {
            if (window.App && window.App.openNewLeaveRequest) {
                window.App.openNewLeaveRequest();
            }
        } catch (error) {
            console.error('Create request error:', error);
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

            this.pendingRequests = [];
            this.approvedRequests = [];
            this.container = null;
            this.isInitialized = false;
        } catch (error) {
            console.error('Leave requests cleanup error:', error);
        }
    }
}

export default LeaveRequestsManager;
