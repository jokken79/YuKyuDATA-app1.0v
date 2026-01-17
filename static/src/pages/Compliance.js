/**
 * Compliance Page Module
 * Verificacion de cumplimiento (5 dias obligatorios)
 * @version 1.0.0
 */

import { getState, subscribe } from '../store/state.js';
import { API_BASE_URL } from '../config/constants.js';

// ========================================
// STATE
// ========================================

let isInitialized = false;

// ========================================
// INITIALIZATION
// ========================================

/**
 * Initialize compliance page
 */
export function init() {
    if (isInitialized) return;

    subscribe(onStateChange, ['currentView', 'year']);
    isInitialized = true;
}

/**
 * Handle state changes
 */
function onStateChange(newState, prevState) {
    if (newState.currentView === 'compliance') {
        loadAlerts();
    }
}

// ========================================
// DATA LOADING
// ========================================

/**
 * Load compliance alerts
 */
export async function loadAlerts() {
    try {
        const res = await fetch(`${API_BASE_URL}/compliance/alerts`);
        const json = await res.json();

        const container = document.getElementById('alerts-container');
        if (!container) return;

        if (json.alerts && json.alerts.length > 0) {
            container.innerHTML = json.alerts.map(alert => {
                const levelIcon = alert.level === 'critical' ? 'CRITICAL' :
                                 alert.level === 'warning' ? 'WARNING' : 'INFO';
                const safeName = escapeHtml(alert.employee_name);
                const safeMessage = escapeHtml(alert.message_ja);
                const safeAction = escapeHtml(alert.action_required || '-');

                return `
                    <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem;">
                        <div style="font-weight: 600;">${levelIcon} ${safeName}</div>
                        <div style="font-size: 0.9rem; margin-top: 0.25rem;">${safeMessage}</div>
                        <div style="font-size: 0.8rem; color: var(--muted); margin-top: 0.5rem;">
                            Action: ${safeAction}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--success);">No alerts</div>';
        }
    } catch (e) {
        console.error('Failed to load alerts:', e);
    }
}

/**
 * Check 5-day compliance for year
 */
export async function check5Day() {
    const state = getState();
    const year = state.year || new Date().getFullYear();

    showLoading();

    try {
        const res = await fetch(`${API_BASE_URL}/compliance/5day-check/${year}`);
        const json = await res.json();

        // Update summary cards
        document.getElementById('comp-total').textContent = json.summary.total_checked;
        document.getElementById('comp-compliant').textContent = json.summary.compliant;
        document.getElementById('comp-atrisk').textContent = json.summary.at_risk;
        document.getElementById('comp-noncompliant').textContent = json.summary.non_compliant;

        // Render non-compliant list
        renderNonCompliantList(json.non_compliant_employees);

        showToast('success', `Compliance check completed for ${year}`);
    } catch (e) {
        showToast('error', 'Compliance check failed');
    } finally {
        hideLoading();
    }
}

/**
 * Render non-compliant employees list
 * @param {Array} employees
 */
function renderNonCompliantList(employees) {
    const container = document.getElementById('compliance-list');
    if (!container) return;

    if (employees && employees.length > 0) {
        container.innerHTML = employees.map(emp => {
            const statusColor = emp.status === 'non_compliant' ? 'var(--danger)' : 'var(--warning)';
            const safeName = escapeHtml(emp.name);
            const safeEmpNum = escapeHtml(emp.employee_num);
            const safeDaysUsed = safeNumber(emp.days_used).toFixed(1);
            const safeDaysRemaining = safeNumber(emp.days_remaining).toFixed(1);

            return `
                <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid ${statusColor};">
                    <div class="flex-between">
                        <div>
                            <div style="font-weight: 600;">${safeName}</div>
                            <div style="font-size: 0.85rem; color: var(--muted);">${safeEmpNum}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.1rem; font-weight: 700; color: ${statusColor};">${safeDaysUsed} days</div>
                            <div style="font-size: 0.8rem; color: var(--muted);">${safeDaysRemaining} days needed</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--success);">All employees have met the 5-day requirement</div>';
    }
}

/**
 * Load annual ledger
 */
export async function loadLedger() {
    const state = getState();
    const year = state.year || new Date().getFullYear();

    showLoading();

    try {
        const res = await fetch(`${API_BASE_URL}/compliance/annual-ledger/${year}`);
        const json = await res.json();

        const container = document.getElementById('ledger-container');
        if (!container) return;

        if (json.entries && json.entries.length > 0) {
            container.innerHTML = `
                <table class="modern-table">
                    <thead>
                        <tr>
                            <th>Employee No.</th>
                            <th>Name</th>
                            <th>Grant Date</th>
                            <th>Granted</th>
                            <th>Used</th>
                            <th>Remaining</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${json.entries.map(e => {
                            const safeEmpNum = escapeHtml(e.employee_num);
                            const safeName = escapeHtml(e.employee_name);
                            const safeGrantDate = escapeHtml(e.grant_date);
                            const safeGranted = safeNumber(e.granted_days);
                            const safeUsed = safeNumber(e.used_days);
                            const safeRemaining = safeNumber(e.remaining_days);
                            return `
                                <tr>
                                    <td>${safeEmpNum}</td>
                                    <td>${safeName}</td>
                                    <td>${safeGrantDate}</td>
                                    <td>${safeGranted}</td>
                                    <td>${safeUsed}</td>
                                    <td>${safeRemaining}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            `;
        } else {
            container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--muted);">No data available</div>';
        }
    } catch (e) {
        showToast('error', 'Failed to load ledger');
    } finally {
        hideLoading();
    }
}

/**
 * Export ledger
 * @param {string} format - 'csv' or 'excel'
 */
export async function exportLedger(format = 'csv') {
    const state = getState();
    const year = state.year || new Date().getFullYear();

    showLoading();

    try {
        const res = await fetch(`${API_BASE_URL}/compliance/export-ledger/${year}?format=${format}`, {
            method: 'POST'
        });
        const json = await res.json();

        if (json.status === 'success') {
            showToast('success', `Annual ledger exported: ${json.filename}`);
            if (json.download_url) {
                window.open(json.download_url, '_blank');
            }
        }
    } catch (e) {
        showToast('error', 'Export failed');
    } finally {
        hideLoading();
    }
}

// ========================================
// EXPIRING DAYS
// ========================================

/**
 * Load employees with expiring days
 */
export async function loadExpiringDays() {
    const state = getState();
    const year = state.year || new Date().getFullYear();

    try {
        const res = await fetch(`${API_BASE_URL}/expiring-soon?year=${year}&threshold_months=3`);
        const json = await res.json();

        const container = document.getElementById('expiring-container');
        if (!container) return;

        if (json.employees && json.employees.length > 0) {
            container.innerHTML = json.employees.map(emp => {
                const safeName = escapeHtml(emp.name);
                const safeBalance = safeNumber(emp.balance).toFixed(1);
                const safeExpiry = escapeHtml(emp.expiry_date);

                return `
                    <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem;">
                        <div class="flex-between">
                            <div>
                                <div style="font-weight: 600;">${safeName}</div>
                                <div style="font-size: 0.8rem; color: var(--muted);">Expires: ${safeExpiry}</div>
                            </div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: var(--warning);">
                                ${safeBalance} days
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--success);">No expiring days</div>';
        }
    } catch (e) {
        console.error('Failed to load expiring days:', e);
    }
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

function safeNumber(val, defaultVal = 0) {
    const num = parseFloat(val);
    return Number.isFinite(num) ? num : defaultVal;
}

function showLoading() {
    if (window.App?.ui?.showLoading) {
        window.App.ui.showLoading();
    }
}

function hideLoading() {
    if (window.App?.ui?.hideLoading) {
        window.App.ui.hideLoading();
    }
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
    // Nothing to clean up
}

// Export default
export default {
    init,
    loadAlerts,
    check5Day,
    loadLedger,
    exportLedger,
    loadExpiringDays,
    cleanup
};
