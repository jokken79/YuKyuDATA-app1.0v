/**
 * Employees Page Module
 * Lista y gestion de empleados
 * @version 1.0.0
 */

import { getState, getFilteredData, setState, subscribe } from '../store/state.js';
import { API_BASE_URL, BADGE_CLASSES, TYPE_LABELS } from '../config/constants.js';

// ========================================
// EMPLOYEES STATE
// ========================================

let isInitialized = false;
let currentTab = 'all';
let activeOnly = true;
let employeeData = {
    haken: [],
    ukeoi: [],
    staff: [],
    all: []
};

// ========================================
// INITIALIZATION
// ========================================

/**
 * Initialize employees page
 */
export function init() {
    if (isInitialized) return;

    // Subscribe to state changes
    subscribe(onStateChange, ['year', 'data']);

    isInitialized = true;
}

/**
 * Handle state changes
 */
function onStateChange(newState, prevState) {
    if (newState.currentView === 'employees') {
        loadData();
    }
}

// ========================================
// DATA LOADING
// ========================================

/**
 * Load employee data by type
 */
export async function loadData() {
    const state = getState();

    try {
        const year = state.year || new Date().getFullYear();
        const res = await fetch(
            `${API_BASE_URL}/employees/by-type?year=${year}&active_only=${activeOnly}&filter_by_year=true`
        );
        const json = await res.json();

        if (json.status === 'success') {
            employeeData.haken = json.haken.employees || [];
            employeeData.ukeoi = json.ukeoi.employees || [];
            employeeData.staff = json.staff.employees || [];
            employeeData.all = [...employeeData.haken, ...employeeData.ukeoi, ...employeeData.staff];

            updateTypeCounts(json);
            updateSummaryCards(json);
            renderTable();
        }
    } catch (e) {
        console.error('Failed to load employee types:', e);
        showToast('error', 'Failed to load employee data');
    }
}

/**
 * Update type tab counts
 * @param {Object} json - API response
 */
function updateTypeCounts(json) {
    const counts = {
        'count-type-all': employeeData.all.length,
        'count-type-haken': employeeData.haken.length,
        'count-type-ukeoi': employeeData.ukeoi.length,
        'count-type-staff': employeeData.staff.length
    };

    Object.entries(counts).forEach(([id, count]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = count;
    });
}

/**
 * Update summary cards
 * @param {Object} json - API response
 */
function updateSummaryCards(json) {
    const updates = {
        'haken-used': Math.round(json.haken.total_used),
        'ukeoi-used': Math.round(json.ukeoi.total_used),
        'staff-used': Math.round(json.staff.total_used),
        'total-type-used': Math.round(
            json.haken.total_used + json.ukeoi.total_used + json.staff.total_used
        )
    };

    Object.entries(updates).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    });
}

// ========================================
// TAB MANAGEMENT
// ========================================

/**
 * Switch between employee type tabs
 * @param {string} tab - Tab name (all, haken, ukeoi, staff)
 */
export function switchTab(tab) {
    currentTab = tab;

    // Update tab buttons
    document.querySelectorAll('.employee-tabs .btn').forEach(btn => {
        btn.classList.remove('active', 'btn-primary');
    });

    const activeTab = document.getElementById(`tab-${tab}`);
    if (activeTab) {
        activeTab.classList.add('active', 'btn-primary');
    }

    renderTable();
}

/**
 * Toggle active employees filter
 */
export function toggleActiveFilter() {
    const toggle = document.getElementById('active-only-toggle');
    if (toggle) {
        activeOnly = toggle.checked;
        loadData();
    }
}

// ========================================
// TABLE RENDERING
// ========================================

/**
 * Render employees table
 * @param {string} filterText - Search filter text
 */
export function renderTable(filterText = '') {
    const tbody = document.getElementById('table-body');
    if (!tbody) return;

    let data = employeeData[currentTab] || [];

    // Apply search filter
    if (filterText) {
        const q = filterText.toLowerCase();
        data = data.filter(e =>
            (e.name && e.name.toLowerCase().includes(q)) ||
            (e.employee_num && String(e.employee_num).includes(q)) ||
            (e.haken && e.haken.toLowerCase().includes(q)) ||
            (e.dispatch_name && e.dispatch_name.toLowerCase().includes(q)) ||
            (e.contract_business && e.contract_business.toLowerCase().includes(q))
        );
    }

    // Update count badge
    const countBadge = document.getElementById('emp-count-badge');
    if (countBadge) {
        countBadge.textContent = `${data.length} Employees`;
    }

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 2rem;">No data available</td></tr>';
        return;
    }

    tbody.innerHTML = data.map(e => renderEmployeeRow(e)).join('');
}

/**
 * Render single employee row
 * @param {Object} e - Employee data
 * @returns {string} HTML string
 */
function renderEmployeeRow(e) {
    const empNum = escapeAttr(e.employee_num || '');
    const name = escapeHtml(e.name || '');
    const type = e.type || '';
    const typeLabel = TYPE_LABELS[type] || 'Staff';
    const typeIcon = type === 'haken' ? 'Dispatch' : type === 'ukeoi' ? 'Contract' : 'Staff';
    const typeBadge = BADGE_CLASSES.type[type] || 'badge-warning';
    const factory = escapeHtml(e.dispatch_name || e.contract_business || e.haken || '-');
    const granted = safeNumber(e.granted).toFixed(1);
    const used = safeNumber(e.used).toFixed(1);
    const balance = safeNumber(e.balance);
    const usageRate = e.granted > 0 ? Math.round((e.used / e.granted) * 100) : 0;

    // Balance badge class
    let balanceClass = BADGE_CLASSES.balance.success;
    if (balance < 0) balanceClass = BADGE_CLASSES.balance.critical;
    else if (balance < 5) balanceClass = BADGE_CLASSES.balance.danger;

    // Check if employee is selected (for bulk edit)
    const isSelected = window.App?.bulkEdit?.selectedEmployees?.has(e.employee_num) || false;

    return `
        <tr class="employee-row" data-employee-num="${empNum}" style="cursor: pointer;" onclick="App.ui.openModal('${empNum}')">
            <td class="table-checkbox" onclick="event.stopPropagation();">
                <input type="checkbox"
                    class="employee-select-checkbox"
                    data-employee-num="${empNum}"
                    ${isSelected ? 'checked' : ''}
                    onchange="App.bulkEdit.toggleEmployee('${empNum}', this.checked)"
                    title="Select">
            </td>
            <td><div class="font-bold">${empNum}</div></td>
            <td><div class="font-bold text-white">${name}</div></td>
            <td><span class="badge ${typeBadge}">${typeIcon}</span></td>
            <td><div class="text-sm text-gray-400">${factory}</div></td>
            <td>${granted}</td>
            <td><span class="text-gradient">${used}</span></td>
            <td><span class="badge ${balanceClass}">${balance.toFixed(1)}</span></td>
            <td>
                <div style="width: 100px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                    <div style="width: ${Math.min(usageRate, 100)}%; height: 100%; background: var(--primary);"></div>
                </div>
                <div class="text-xs mt-1 text-right">${usageRate}%</div>
            </td>
        </tr>
    `;
}

// ========================================
// SEARCH
// ========================================

let searchTimeout = null;

/**
 * Search employees
 * @param {string} query - Search query
 */
export function search(query) {
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }

    searchTimeout = setTimeout(() => {
        renderTable(query);
    }, 300);
}

// ========================================
// EMPLOYEE DETAILS
// ========================================

/**
 * Get employee by number
 * @param {string} empNum - Employee number
 * @returns {Object|null} Employee data
 */
export function getEmployee(empNum) {
    return employeeData.all.find(e => e.employee_num === empNum) || null;
}

/**
 * Get employees data
 * @returns {Object} Employee data by type
 */
export function getData() {
    return { ...employeeData };
}

/**
 * Get current tab
 * @returns {string} Current tab name
 */
export function getCurrentTab() {
    return currentTab;
}

// ========================================
// HELPERS
// ========================================

/**
 * Escape HTML to prevent XSS
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

/**
 * Escape attribute values
 * @param {string} str
 * @returns {string}
 */
function escapeAttr(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/'/g, '&#39;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

/**
 * Safe number conversion
 * @param {*} val
 * @param {number} defaultVal
 * @returns {number}
 */
function safeNumber(val, defaultVal = 0) {
    const num = parseFloat(val);
    return Number.isFinite(num) ? num : defaultVal;
}

/**
 * Show toast notification (delegate to main App)
 * @param {string} type
 * @param {string} message
 */
function showToast(type, message) {
    if (window.App?.ui?.showToast) {
        window.App.ui.showToast(type, message);
    }
}

/**
 * Cleanup
 */
export function cleanup() {
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
}

// Export default
export default {
    init,
    loadData,
    switchTab,
    toggleActiveFilter,
    renderTable,
    search,
    getEmployee,
    getData,
    getCurrentTab,
    cleanup
};
