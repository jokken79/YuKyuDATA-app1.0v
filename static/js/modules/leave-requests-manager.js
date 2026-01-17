/**
 * Leave Requests Manager Module
 * Handles leave request operations: create, approve, reject, cancel, revert
 */

import { escapeHtml } from './utils.js';

const API_BASE = 'http://localhost:8000/api';

/**
 * LeaveRequestsManager - Singleton for managing leave requests
 */
export const LeaveRequestsManager = {
    selectedEmployee: null,
    factories: [],
    pendingRequests: [],
    historyRequests: [],

    /**
     * Initialize the manager with UI callbacks
     * @param {Object} callbacks - UI callback functions
     */
    init(callbacks = {}) {
        this.showToast = callbacks.showToast || (() => {});
        this.showLoading = callbacks.showLoading || (() => {});
        this.hideLoading = callbacks.hideLoading || (() => {});
    },

    /**
     * Load factories/departments for filtering
     */
    async loadFactories() {
        try {
            const response = await fetch(`${API_BASE}/stats/factory`);
            if (!response.ok) throw new Error('Failed to fetch factories');

            const data = await response.json();
            this.factories = data.data || data || [];
            this._renderFactoryFilter();
            return this.factories;
        } catch (error) {
            console.error('Error loading factories:', error);
            this.showToast('error', 'Error cargando fábricas');
            return [];
        }
    },

    /**
     * Load pending leave requests
     */
    async loadPending() {
        try {
            const response = await fetch(`${API_BASE}/leave-requests?status=PENDING`);
            if (!response.ok) throw new Error('Failed to fetch pending requests');

            const data = await response.json();
            this.pendingRequests = data.data || data || [];
            this._renderPendingRequests();
            return this.pendingRequests;
        } catch (error) {
            console.error('Error loading pending requests:', error);
            this.showToast('error', 'Error cargando solicitudes pendientes');
            return [];
        }
    },

    /**
     * Load request history
     * @param {string} status - Filter by status (APPROVED, REJECTED, etc.)
     */
    async loadHistory(status = null) {
        try {
            let url = `${API_BASE}/leave-requests`;
            if (status) {
                url += `?status=${status}`;
            }

            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to fetch request history');

            const data = await response.json();
            this.historyRequests = data.data || data || [];
            this._renderHistoryTable();
            return this.historyRequests;
        } catch (error) {
            console.error('Error loading history:', error);
            this.showToast('error', 'Error cargando historial');
            return [];
        }
    },

    /**
     * Select an employee for creating a new request
     * @param {string} employeeNum - Employee number
     */
    async selectEmployee(employeeNum) {
        try {
            this.selectedEmployee = employeeNum;

            // Fetch employee details for the form
            const response = await fetch(`${API_BASE}/employees/${employeeNum}/leave-info`);
            if (response.ok) {
                const data = await response.json();
                this._updateEmployeeInfo(data);
            }

            // Update UI to show selected employee
            const selectedDisplay = document.getElementById('selected-employee');
            if (selectedDisplay) {
                selectedDisplay.textContent = employeeNum;
            }

            // Clear search results
            const searchResults = document.getElementById('emp-search-results');
            if (searchResults) {
                searchResults.innerHTML = '';
            }

            return true;
        } catch (error) {
            console.error('Error selecting employee:', error);
            return false;
        }
    },

    /**
     * Create a new leave request
     * @param {Object} requestData - Leave request data
     */
    async create(requestData) {
        try {
            this.showLoading();

            const response = await fetch(`${API_BASE}/leave-requests`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    employee_num: requestData.employee_num || this.selectedEmployee,
                    leave_start_date: requestData.start_date,
                    leave_end_date: requestData.end_date,
                    days_requested: requestData.days,
                    leave_type: requestData.type || 'full',
                    reason: requestData.reason || ''
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create request');
            }

            const result = await response.json();
            this.showToast('success', 'Solicitud creada exitosamente');
            await this.loadPending();
            return result;
        } catch (error) {
            console.error('Error creating request:', error);
            this.showToast('error', `Error: ${error.message}`);
            return null;
        } finally {
            this.hideLoading();
        }
    },

    /**
     * Approve a leave request
     * @param {number} requestId - Request ID to approve
     */
    async approve(requestId) {
        try {
            this.showLoading();

            const response = await fetch(`${API_BASE}/leave-requests/${requestId}/approve`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    approved_by: 'manager' // Could be dynamic based on logged-in user
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to approve request');
            }

            const result = await response.json();
            this.showToast('success', 'Solicitud aprobada - Días deducidos del balance');
            await this.loadPending();
            await this.loadHistory('APPROVED');
            return result;
        } catch (error) {
            console.error('Error approving request:', error);
            this.showToast('error', `Error: ${error.message}`);
            return null;
        } finally {
            this.hideLoading();
        }
    },

    /**
     * Reject a leave request
     * @param {number} requestId - Request ID to reject
     * @param {string} reason - Rejection reason
     */
    async reject(requestId, reason = '') {
        try {
            this.showLoading();

            // Prompt for reason if not provided
            if (!reason) {
                reason = prompt('Motivo del rechazo (opcional):') || '';
            }

            const response = await fetch(`${API_BASE}/leave-requests/${requestId}/reject`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    reason: reason
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to reject request');
            }

            const result = await response.json();
            this.showToast('info', 'Solicitud rechazada');
            await this.loadPending();
            return result;
        } catch (error) {
            console.error('Error rejecting request:', error);
            this.showToast('error', `Error: ${error.message}`);
            return null;
        } finally {
            this.hideLoading();
        }
    },

    /**
     * Cancel a pending request
     * @param {number} requestId - Request ID to cancel
     */
    async cancel(requestId) {
        try {
            if (!confirm('¿Seguro que desea cancelar esta solicitud?')) {
                return null;
            }

            this.showLoading();

            const response = await fetch(`${API_BASE}/leave-requests/${requestId}/cancel`, {
                method: 'POST'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to cancel request');
            }

            const result = await response.json();
            this.showToast('info', 'Solicitud cancelada');
            await this.loadPending();
            return result;
        } catch (error) {
            console.error('Error canceling request:', error);
            this.showToast('error', `Error: ${error.message}`);
            return null;
        } finally {
            this.hideLoading();
        }
    },

    /**
     * Revert an approved request (restore balance)
     * @param {number} requestId - Request ID to revert
     */
    async revert(requestId) {
        try {
            if (!confirm('¿Seguro que desea revertir esta aprobación? Los días serán restaurados al balance del empleado.')) {
                return null;
            }

            this.showLoading();

            const response = await fetch(`${API_BASE}/leave-requests/${requestId}/revert`, {
                method: 'PATCH'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to revert request');
            }

            const result = await response.json();
            this.showToast('success', 'Aprobación revertida - Días restaurados al balance');
            await this.loadPending();
            await this.loadHistory();
            return result;
        } catch (error) {
            console.error('Error reverting request:', error);
            this.showToast('error', `Error: ${error.message}`);
            return null;
        } finally {
            this.hideLoading();
        }
    },

    // ========================================
    // PRIVATE RENDER METHODS
    // ========================================

    _renderFactoryFilter() {
        const container = document.getElementById('factory-filter');
        if (!container || !this.factories.length) return;

        const options = this.factories.map(f =>
            `<option value="${escapeHtml(f.haken || f.name)}">${escapeHtml(f.haken || f.name)}</option>`
        ).join('');

        container.innerHTML = `
            <option value="">Todas las fábricas</option>
            ${options}
        `;
    },

    _renderPendingRequests() {
        const container = document.getElementById('pending-requests');
        if (!container) return;

        if (!this.pendingRequests.length) {
            container.innerHTML = '<p class="text-muted text-center">No hay solicitudes pendientes</p>';
            return;
        }

        const html = this.pendingRequests.map(req => `
            <div class="request-card pending" data-request-id="${req.id}">
                <div class="request-header">
                    <span class="employee-name">${escapeHtml(req.employee_name || req.employee_num)}</span>
                    <span class="badge badge-warning">PENDIENTE</span>
                </div>
                <div class="request-details">
                    <div><strong>Fechas:</strong> ${escapeHtml(req.leave_start_date)} - ${escapeHtml(req.leave_end_date || req.leave_start_date)}</div>
                    <div><strong>Días:</strong> ${req.days_requested}</div>
                    <div><strong>Tipo:</strong> ${escapeHtml(req.leave_type || 'completo')}</div>
                    ${req.reason ? `<div><strong>Motivo:</strong> ${escapeHtml(req.reason)}</div>` : ''}
                </div>
                <div class="request-actions">
                    <button class="btn btn-success btn-sm btn-approve" data-request-id="${req.id}">
                        Aprobar
                    </button>
                    <button class="btn btn-danger btn-sm btn-reject" data-request-id="${req.id}">
                        Rechazar
                    </button>
                    <button class="btn btn-secondary btn-sm btn-cancel" data-request-id="${req.id}">
                        Cancelar
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    },

    _renderHistoryTable() {
        const container = document.getElementById('requests-history');
        if (!container) return;

        if (!this.historyRequests.length) {
            container.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Sin historial</td></tr>';
            return;
        }

        const html = this.historyRequests.map(req => {
            const statusClass = req.status === 'APPROVED' ? 'success' :
                               req.status === 'REJECTED' ? 'danger' : 'secondary';

            const statusText = req.status === 'APPROVED' ? 'Aprobada' :
                              req.status === 'REJECTED' ? 'Rechazada' : req.status;

            const canRevert = req.status === 'APPROVED';

            return `
                <tr>
                    <td>${escapeHtml(req.employee_num)}</td>
                    <td>${escapeHtml(req.employee_name || '-')}</td>
                    <td>${escapeHtml(req.leave_start_date)}</td>
                    <td>${req.days_requested}</td>
                    <td><span class="badge badge-${statusClass}">${statusText}</span></td>
                    <td>
                        ${canRevert ? `
                            <button class="btn btn-warning btn-sm btn-revert" data-request-id="${req.id}">
                                Revertir
                            </button>
                        ` : '-'}
                    </td>
                </tr>
            `;
        }).join('');

        container.innerHTML = html;
    },

    _updateEmployeeInfo(data) {
        const infoContainer = document.getElementById('selected-employee-info');
        if (!infoContainer) return;

        infoContainer.innerHTML = `
            <div class="employee-info-card">
                <p><strong>Nombre:</strong> ${escapeHtml(data.name || '-')}</p>
                <p><strong>Balance:</strong> ${data.balance || 0} días</p>
                <p><strong>Usado:</strong> ${data.used || 0} días</p>
                <p><strong>Otorgado:</strong> ${data.granted || 0} días</p>
            </div>
        `;
    }
};

export default LeaveRequestsManager;
