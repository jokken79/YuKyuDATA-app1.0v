/**
 * Leave Requests Page Module
 * Workflow de solicitudes de vacaciones
 * @version 1.0.0
 */

import { getState, subscribe } from '../store/state.js';
import { API_BASE_URL, REQUEST_STATUS, LEAVE_TYPE_LABELS } from '../config/constants.js';

// ========================================
// STATE
// ========================================

let isInitialized = false;
let selectedEmployee = null;
let searchTimeout = null;
let factories = [];

// ========================================
// INITIALIZATION
// ========================================

/**
 * Initialize leave requests page
 */
export function init() {
    if (isInitialized) return;

    subscribe(onStateChange, ['currentView']);
    isInitialized = true;
}

/**
 * Handle state changes
 */
function onStateChange(newState, prevState) {
    if (newState.currentView === 'requests') {
        loadFactories();
        loadPending();
        loadHistory();
    }
}

// ========================================
// DATA LOADING
// ========================================

/**
 * Load factories for filter dropdown
 */
export async function loadFactories() {
    try {
        const res = await fetch(`${API_BASE_URL}/factories?status=Active`);
        const json = await res.json();

        if (json.data) {
            factories = json.data;
            const select = document.getElementById('factory-filter');
            if (select) {
                select.innerHTML = '<option value="">All Factories</option>';
                factories.forEach(factory => {
                    const opt = document.createElement('option');
                    opt.value = factory;
                    opt.textContent = factory;
                    select.appendChild(opt);
                });
            }
        }
    } catch (e) {
        console.error('Failed to load factories:', e);
    }
}

/**
 * Load pending requests
 */
export async function loadPending() {
    try {
        const res = await fetch(`${API_BASE_URL}/leave-requests?status=pending`);
        const json = await res.json();

        const container = document.getElementById('pending-requests-container');
        if (!container) return;

        if (json.requests && json.requests.length > 0) {
            container.innerHTML = json.requests.map(req => renderPendingRequest(req)).join('');
            attachPendingEventListeners();
        } else {
            container.innerHTML = '<div class="text-center text-muted p-lg">No pending requests</div>';
        }

        // Update count badge
        const badge = document.getElementById('pending-count');
        if (badge) badge.textContent = json.requests?.length || 0;
    } catch (e) {
        console.error('Failed to load pending requests:', e);
    }
}

/**
 * Load request history
 */
export async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE_URL}/leave-requests?status=all&limit=50`);
        const json = await res.json();

        const container = document.getElementById('request-history-container');
        if (!container) return;

        if (json.requests && json.requests.length > 0) {
            container.innerHTML = json.requests.map(req => renderHistoryRequest(req)).join('');
        } else {
            container.innerHTML = '<div class="text-center text-muted p-lg">No request history</div>';
        }
    } catch (e) {
        console.error('Failed to load request history:', e);
    }
}

// ========================================
// RENDERING
// ========================================

/**
 * Render a pending request card
 * @param {Object} req - Request data
 * @returns {string} HTML string
 */
function renderPendingRequest(req) {
    const safeName = escapeHtml(req.employee_name);
    const safeEmpNum = escapeHtml(req.employee_num);
    const safeStartDate = escapeHtml(req.start_date);
    const safeEndDate = escapeHtml(req.end_date);
    const safeDays = safeNumber(req.days_requested).toFixed(1);
    const safeReason = escapeHtml(req.reason || '-');
    const typeLabel = LEAVE_TYPE_LABELS[req.leave_type] || 'Full Day';

    return `
        <div class="request-card pending" data-request-id="${req.id}">
            <div class="request-header">
                <div>
                    <div class="request-employee">${safeName}</div>
                    <div class="request-empnum">${safeEmpNum}</div>
                </div>
                <span class="badge badge-warning">Pending</span>
            </div>
            <div class="request-details">
                <div class="request-dates">
                    <span>${safeStartDate}</span>
                    <span>-</span>
                    <span>${safeEndDate}</span>
                </div>
                <div class="request-days">${safeDays} days (${typeLabel})</div>
                <div class="request-reason">Reason: ${safeReason}</div>
            </div>
            <div class="request-actions">
                <button class="btn btn-success btn-sm approve-btn" data-request-id="${req.id}">
                    Approve
                </button>
                <button class="btn btn-danger btn-sm reject-btn" data-request-id="${req.id}">
                    Reject
                </button>
            </div>
        </div>
    `;
}

/**
 * Render a history request item
 * @param {Object} req - Request data
 * @returns {string} HTML string
 */
function renderHistoryRequest(req) {
    const safeName = escapeHtml(req.employee_name);
    const safeStartDate = escapeHtml(req.start_date);
    const safeEndDate = escapeHtml(req.end_date);
    const safeDays = safeNumber(req.days_requested).toFixed(1);
    const status = req.status;

    let statusBadge = 'badge-info';
    let statusLabel = 'Unknown';
    if (status === REQUEST_STATUS.APPROVED) {
        statusBadge = 'badge-success';
        statusLabel = 'Approved';
    } else if (status === REQUEST_STATUS.REJECTED) {
        statusBadge = 'badge-danger';
        statusLabel = 'Rejected';
    } else if (status === REQUEST_STATUS.PENDING) {
        statusBadge = 'badge-warning';
        statusLabel = 'Pending';
    } else if (status === REQUEST_STATUS.CANCELLED) {
        statusBadge = 'badge-secondary';
        statusLabel = 'Cancelled';
    }

    return `
        <div class="history-item" data-request-id="${req.id}">
            <div class="history-info">
                <span class="history-name">${safeName}</span>
                <span class="history-dates">${safeStartDate} - ${safeEndDate}</span>
                <span class="history-days">${safeDays} days</span>
            </div>
            <span class="badge ${statusBadge}">${statusLabel}</span>
        </div>
    `;
}

/**
 * Attach event listeners to pending request buttons
 */
function attachPendingEventListeners() {
    document.querySelectorAll('.approve-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = btn.dataset.requestId;
            approveRequest(id);
        });
    });

    document.querySelectorAll('.reject-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = btn.dataset.requestId;
            rejectRequest(id);
        });
    });
}

// ========================================
// EMPLOYEE SEARCH
// ========================================

/**
 * Search employees for request form
 * @param {string} query - Search query
 */
export function searchEmployee(query) {
    if (searchTimeout) clearTimeout(searchTimeout);

    const factory = document.getElementById('factory-filter')?.value || '';

    if (!factory && (!query || query.length < 2)) {
        document.getElementById('emp-search-results').innerHTML = '';
        return;
    }

    searchTimeout = setTimeout(async () => {
        try {
            let url = `${API_BASE_URL}/employees/search?status=Active`;
            if (query) url += `&q=${encodeURIComponent(query)}`;
            if (factory) url += `&factory=${encodeURIComponent(factory)}`;

            const res = await fetch(url);
            const json = await res.json();

            const container = document.getElementById('emp-search-results');
            if (json.data && json.data.length > 0) {
                container.innerHTML = json.data.slice(0, 15).map(emp => {
                    const empNum = escapeAttr(emp.employee_num);
                    const name = escapeHtml(emp.name);
                    const empFactory = escapeHtml(emp.factory || '-');
                    const type = escapeHtml(emp.type);
                    return `
                        <div class="search-result-item" data-employee-num="${empNum}"
                             style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; cursor: pointer;">
                            <div style="font-weight: 600;">${name}</div>
                            <div style="font-size: 0.85rem; color: var(--muted);">${empNum} | ${empFactory} | ${type}</div>
                        </div>
                    `;
                }).join('');

                // Attach click listeners
                container.querySelectorAll('.search-result-item').forEach(item => {
                    item.addEventListener('click', () => {
                        selectEmployee(item.dataset.employeeNum);
                    });
                });
            } else {
                container.innerHTML = '<div style="padding: 1rem; color: var(--muted); text-align: center;">No results found</div>';
            }
        } catch (e) {
            console.error('Search error:', e);
        }
    }, 300);
}

/**
 * Select an employee for the request
 * @param {string} empNum - Employee number
 */
export async function selectEmployee(empNum) {
    try {
        const res = await fetch(`${API_BASE_URL}/employees/${empNum}/leave-info`);
        const json = await res.json();

        if (json.employee) {
            selectedEmployee = json;

            // Update UI
            const infoEl = document.getElementById('selected-emp-info');
            if (infoEl) infoEl.style.display = 'block';

            document.getElementById('selected-emp-name').textContent = json.employee.name;
            document.getElementById('selected-emp-details').textContent =
                `${json.employee.employee_num} | ${json.employee.factory || '-'} | ${json.employee.type}`;
            document.getElementById('selected-emp-balance').textContent = json.total_available.toFixed(1) + ' days';

            // Clear search
            const searchInput = document.getElementById('emp-search');
            if (searchInput) {
                searchInput.value = json.employee.name;
                searchInput.classList.add('is-valid');
            }
            document.getElementById('emp-search-results').innerHTML = '';

            updateProgressSteps(2);
        }
    } catch (e) {
        showToast('error', 'Failed to load employee info');
    }
}

/**
 * Get selected employee
 * @returns {Object|null}
 */
export function getSelectedEmployee() {
    return selectedEmployee;
}

// ========================================
// REQUEST ACTIONS
// ========================================

/**
 * Submit a new leave request
 */
export async function submitRequest() {
    if (!selectedEmployee) {
        showToast('error', 'Please select an employee');
        return;
    }

    const startDate = document.getElementById('start-date')?.value;
    const endDate = document.getElementById('end-date')?.value;
    const leaveType = document.getElementById('leave-type')?.value || 'full';
    const daysRequested = parseFloat(document.getElementById('days-requested')?.value) || 1;
    const reason = document.getElementById('request-reason')?.value || '';

    if (!startDate || !endDate) {
        showToast('error', 'Please select dates');
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/leave-requests`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                employee_num: selectedEmployee.employee.employee_num,
                start_date: startDate,
                end_date: endDate,
                leave_type: leaveType,
                days_requested: daysRequested,
                reason: reason
            })
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to submit request');
        }

        showToast('success', 'Request submitted successfully');
        resetForm();
        loadPending();
        loadHistory();
    } catch (e) {
        showToast('error', e.message);
    }
}

/**
 * Approve a pending request with confirmation
 * P0.3 FIX: Added confirmation modal before critical action
 * @param {string|number} requestId
 */
export async function approveRequest(requestId) {
    // Get request info for confirmation message
    const card = document.querySelector(`.request-card[data-request-id="${requestId}"]`);
    const empName = card?.querySelector('.request-employee')?.textContent || 'Unknown';
    const days = card?.querySelector('.request-days')?.textContent || '';

    // Show confirmation modal
    const confirmed = await showConfirmModal({
        title: '承認確認',
        message: `${empName}さんの休暇申請 (${days}) を承認しますか？\n\n承認すると有給残高から差し引かれます。`,
        confirmText: '承認する',
        cancelText: 'キャンセル',
        type: 'success'
    });

    if (!confirmed) return;

    try {
        const res = await fetch(`${API_BASE_URL}/leave-requests/${requestId}/approve`, {
            method: 'PATCH'
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to approve request');
        }

        showToast('success', '申請を承認しました');
        loadPending();
        loadHistory();
    } catch (e) {
        showToast('error', e.message);
    }
}

/**
 * Reject a pending request with confirmation
 * P0.3 FIX: Added confirmation modal before critical action
 * @param {string|number} requestId
 */
export async function rejectRequest(requestId) {
    // Get request info for confirmation message
    const card = document.querySelector(`.request-card[data-request-id="${requestId}"]`);
    const empName = card?.querySelector('.request-employee')?.textContent || 'Unknown';

    // Show confirmation modal
    const confirmed = await showConfirmModal({
        title: '却下確認',
        message: `${empName}さんの休暇申請を却下しますか？`,
        confirmText: '却下する',
        cancelText: 'キャンセル',
        type: 'danger'
    });

    if (!confirmed) return;

    try {
        const res = await fetch(`${API_BASE_URL}/leave-requests/${requestId}/reject`, {
            method: 'PATCH'
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to reject request');
        }

        showToast('success', '申請を却下しました');
        loadPending();
        loadHistory();
    } catch (e) {
        showToast('error', e.message);
    }
}

/**
 * Revert an approved request
 * @param {string|number} requestId
 */
export async function revertRequest(requestId) {
    try {
        const res = await fetch(`${API_BASE_URL}/leave-requests/${requestId}/revert`, {
            method: 'PATCH'
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to revert request');
        }

        showToast('success', 'Request reverted');
        loadPending();
        loadHistory();
    } catch (e) {
        showToast('error', e.message);
    }
}

// ========================================
// FORM HELPERS
// ========================================

/**
 * Reset the request form
 */
export function resetForm() {
    selectedEmployee = null;

    const infoEl = document.getElementById('selected-emp-info');
    if (infoEl) infoEl.style.display = 'none';

    const searchInput = document.getElementById('emp-search');
    if (searchInput) {
        searchInput.value = '';
        searchInput.classList.remove('is-valid');
    }

    document.getElementById('start-date').value = '';
    document.getElementById('end-date').value = '';
    document.getElementById('days-requested').value = '1';
    document.getElementById('request-reason').value = '';

    updateProgressSteps(1);
}

/**
 * Update progress steps UI
 * @param {number} step - Current step (1-3)
 */
function updateProgressSteps(step) {
    for (let i = 1; i <= 3; i++) {
        const el = document.getElementById(`step-${i}`);
        if (el) {
            el.classList.remove('active', 'completed');
            if (i < step) el.classList.add('completed');
            if (i === step) el.classList.add('active');
        }
    }
}

/**
 * Validate dates
 * @returns {boolean}
 */
export function validateDates() {
    const startDate = document.getElementById('start-date');
    const endDate = document.getElementById('end-date');
    let isValid = true;

    const today = new Date().toISOString().split('T')[0];

    if (startDate.value && startDate.value < today) {
        startDate.classList.add('is-invalid');
        isValid = false;
    } else if (startDate.value) {
        startDate.classList.add('is-valid');
    }

    if (endDate.value && startDate.value && endDate.value < startDate.value) {
        endDate.classList.add('is-invalid');
        isValid = false;
    } else if (endDate.value) {
        endDate.classList.add('is-valid');
    }

    return isValid;
}

// ========================================
// CONFIRMATION MODAL (P0.3 FIX)
// ========================================

/**
 * Show a confirmation modal for critical actions
 * @param {Object} options - Modal options
 * @param {string} options.title - Modal title
 * @param {string} options.message - Confirmation message
 * @param {string} options.confirmText - Confirm button text
 * @param {string} options.cancelText - Cancel button text
 * @param {string} options.type - Modal type (success, danger, warning)
 * @returns {Promise<boolean>} - True if confirmed, false otherwise
 */
function showConfirmModal({ title, message, confirmText = '確認', cancelText = 'キャンセル', type = 'info' }) {
    return new Promise((resolve) => {
        // Remove existing modal if any
        const existingModal = document.getElementById('confirm-modal-overlay');
        if (existingModal) existingModal.remove();

        // Color based on type
        const colors = {
            success: { btn: '#10b981', btnHover: '#059669' },
            danger: { btn: '#ef4444', btnHover: '#dc2626' },
            warning: { btn: '#f59e0b', btnHover: '#d97706' },
            info: { btn: '#06b6d4', btnHover: '#0891b2' }
        };
        const color = colors[type] || colors.info;

        // Create modal HTML
        const modalHTML = `
            <div id="confirm-modal-overlay" style="
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px);
                display: flex; align-items: center; justify-content: center;
                z-index: 10000; animation: fadeIn 0.2s ease;
            ">
                <div id="confirm-modal" style="
                    background: var(--glass-bg-dark, #1e293b);
                    border: 1px solid var(--glass-border, rgba(255,255,255,0.1));
                    border-radius: 12px; padding: 24px; max-width: 400px; width: 90%;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                    animation: slideUp 0.3s ease;
                " role="dialog" aria-modal="true" aria-labelledby="confirm-modal-title">
                    <h3 id="confirm-modal-title" style="
                        margin: 0 0 16px 0; font-size: 1.25rem; font-weight: 600;
                        color: var(--text-primary, #f1f5f9);
                    ">${escapeHtml(title)}</h3>
                    <p style="
                        margin: 0 0 24px 0; color: var(--text-secondary, #94a3b8);
                        line-height: 1.6; white-space: pre-line;
                    ">${escapeHtml(message)}</p>
                    <div style="display: flex; gap: 12px; justify-content: flex-end;">
                        <button id="confirm-modal-cancel" style="
                            padding: 10px 20px; border-radius: 8px;
                            border: 1px solid var(--color-neutral-600, #4b5563);
                            background: transparent; color: var(--text-primary, #f1f5f9);
                            cursor: pointer; font-weight: 500; transition: all 0.2s;
                        ">${escapeHtml(cancelText)}</button>
                        <button id="confirm-modal-confirm" style="
                            padding: 10px 20px; border-radius: 8px;
                            border: none; background: ${color.btn}; color: white;
                            cursor: pointer; font-weight: 500; transition: all 0.2s;
                        ">${escapeHtml(confirmText)}</button>
                    </div>
                </div>
            </div>
            <style>
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
                #confirm-modal-cancel:hover { background: var(--color-neutral-700, #374151); }
                #confirm-modal-confirm:hover { background: ${color.btnHover}; }
            </style>
        `;

        // Insert modal into DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        const overlay = document.getElementById('confirm-modal-overlay');
        const confirmBtn = document.getElementById('confirm-modal-confirm');
        const cancelBtn = document.getElementById('confirm-modal-cancel');

        // Focus confirm button for accessibility
        confirmBtn.focus();

        // Handle confirm
        const handleConfirm = () => {
            cleanup();
            resolve(true);
        };

        // Handle cancel
        const handleCancel = () => {
            cleanup();
            resolve(false);
        };

        // Handle escape key
        const handleKeydown = (e) => {
            if (e.key === 'Escape') handleCancel();
            if (e.key === 'Enter') handleConfirm();
        };

        // Cleanup function
        const cleanup = () => {
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
            overlay.removeEventListener('click', handleOverlayClick);
            document.removeEventListener('keydown', handleKeydown);
            overlay.remove();
        };

        // Handle overlay click (close on backdrop)
        const handleOverlayClick = (e) => {
            if (e.target === overlay) handleCancel();
        };

        // Attach event listeners
        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
        overlay.addEventListener('click', handleOverlayClick);
        document.addEventListener('keydown', handleKeydown);
    });
}

// ========================================
// HELPERS
// ========================================

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

function escapeAttr(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/'/g, '&#39;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function safeNumber(val, defaultVal = 0) {
    const num = parseFloat(val);
    return Number.isFinite(num) ? num : defaultVal;
}

function showToast(type, message) {
    if (window.App?.ui?.showToast) {
        window.App.ui.showToast(type, message);
    }
}

/**
 * Cleanup
 */
export function cleanup() {
    if (searchTimeout) clearTimeout(searchTimeout);
    selectedEmployee = null;
}

// Export default
export default {
    init,
    loadFactories,
    loadPending,
    loadHistory,
    searchEmployee,
    selectEmployee,
    getSelectedEmployee,
    submitRequest,
    approveRequest,
    rejectRequest,
    revertRequest,
    resetForm,
    validateDates,
    cleanup
};
