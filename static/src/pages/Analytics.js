/**
 * Analytics Page Module
 * Estadisticas y reportes avanzados
 * @version 1.0.0
 */

import { getState, subscribe } from '../store/state.js';
import { API_BASE_URL, CHART_COLORS } from '../config/constants.js';

// ========================================
// STATE
// ========================================

let isInitialized = false;
let charts = {};

// ========================================
// INITIALIZATION
// ========================================

/**
 * Initialize analytics page
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
    if (newState.currentView === 'analytics') {
        loadDashboard();
    }
}

// ========================================
// DATA LOADING
// ========================================

/**
 * Load analytics dashboard
 */
export async function loadDashboard() {
    const state = getState();
    const year = state.year || new Date().getFullYear();

    showLoading();

    try {
        const res = await fetch(`${API_BASE_URL}/analytics/dashboard/${year}`);
        const json = await res.json();

        // Update summary cards
        updateSummaryCards(json.summary);

        // Render charts
        renderDepartmentChart(json.department_stats);
        renderTypeChart(json.type_stats);

        // Render lists
        renderTopUsers(json.top_users);
        renderHighBalance(json.high_balance);

        // Load predictions
        loadPredictions(year);

    } catch (e) {
        showToast('error', 'Failed to load analytics data');
    } finally {
        hideLoading();
    }
}

/**
 * Update summary cards
 * @param {Object} summary
 */
function updateSummaryCards(summary) {
    const updates = {
        'ana-total-emp': summary.total_employees,
        'ana-total-granted': summary.total_granted.toLocaleString(),
        'ana-total-used': summary.total_used.toLocaleString(),
        'ana-avg-rate': summary.average_rate + '%'
    };

    Object.entries(updates).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    });
}

// ========================================
// CHARTS
// ========================================

/**
 * Render department stats chart
 * @param {Array} deptStats
 */
export function renderDepartmentChart(deptStats) {
    const ctx = document.getElementById('chart-department');
    if (!ctx) return;

    if (charts['department']) {
        charts['department'].destroy();
    }

    const data = deptStats.slice(0, 10);
    charts['department'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.name.length > 15 ? d.name.substring(0, 15) + '...' : d.name),
            datasets: [{
                label: 'Days Used',
                data: data.map(d => d.total_used),
                backgroundColor: 'rgba(6, 182, 212, 0.5)',
                borderColor: '#06b6d4',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#64748b' } },
                y: { grid: { display: false }, ticks: { color: '#64748b' } }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

/**
 * Render employee type chart
 * @param {Object} typeStats
 */
export function renderTypeChart(typeStats) {
    const ctx = document.getElementById('chart-employee-type');
    if (!ctx) return;

    if (charts['type']) {
        charts['type'].destroy();
    }

    const data = [
        { label: 'Dispatch', value: typeStats.haken?.total_used || 0, color: CHART_COLORS.types.haken },
        { label: 'Contract', value: typeStats.ukeoi?.total_used || 0, color: CHART_COLORS.types.ukeoi },
        { label: 'Staff', value: typeStats.staff?.total_used || 0, color: CHART_COLORS.types.staff }
    ];

    charts['type'] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.label),
            datasets: [{
                data: data.map(d => d.value),
                backgroundColor: data.map(d => d.color),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8' }
                }
            }
        }
    });
}

/**
 * Render top users list
 * @param {Array} topUsers
 */
function renderTopUsers(topUsers) {
    const container = document.getElementById('top-users-list');
    if (!container) return;

    if (topUsers && topUsers.length > 0) {
        container.innerHTML = topUsers.slice(0, 10).map((user, idx) => {
            const safeName = escapeHtml(user.name);
            const safeUsed = safeNumber(user.used).toFixed(1);
            return `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px; margin-bottom: 0.25rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: var(--primary); font-weight: 600;">#${idx + 1}</span>
                        <span>${safeName}</span>
                    </div>
                    <span style="font-weight: 600; color: var(--success);">${safeUsed} days</span>
                </div>
            `;
        }).join('');
    } else {
        container.innerHTML = '<div class="text-center text-muted p-md">No data</div>';
    }
}

/**
 * Render high balance list
 * @param {Array} highBalance
 */
function renderHighBalance(highBalance) {
    const container = document.getElementById('high-balance-list');
    if (!container) return;

    if (highBalance && highBalance.length > 0) {
        container.innerHTML = highBalance.slice(0, 10).map(user => {
            const safeName = escapeHtml(user.name);
            const safeBalance = safeNumber(user.balance).toFixed(1);
            return `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px; margin-bottom: 0.25rem;">
                    <span>${safeName}</span>
                    <span style="font-weight: 600; color: var(--warning);">${safeBalance} days</span>
                </div>
            `;
        }).join('');
    } else {
        container.innerHTML = '<div class="text-center text-muted p-md">No data</div>';
    }
}

// ========================================
// PREDICTIONS
// ========================================

/**
 * Load usage predictions
 * @param {number} year
 */
export async function loadPredictions(year) {
    try {
        const res = await fetch(`${API_BASE_URL}/analytics/predictions/${year}`);
        const json = await res.json();

        const container = document.getElementById('predictions-container');
        if (!container) return;

        if (json.predictions) {
            const p = json.predictions;
            container.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                    <div style="padding: 1rem; background: rgba(34, 197, 94, 0.1); border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.8rem; color: var(--muted);">Expected Usage</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--success);">${p.expected_usage?.toFixed(0) || '-'} days</div>
                    </div>
                    <div style="padding: 1rem; background: rgba(234, 179, 8, 0.1); border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.8rem; color: var(--muted);">Year-End Balance</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--warning);">${p.projected_balance?.toFixed(0) || '-'} days</div>
                    </div>
                    <div style="padding: 1rem; background: rgba(6, 182, 212, 0.1); border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.8rem; color: var(--muted);">Trend</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--info);">${p.trend || '-'}</div>
                    </div>
                    <div style="padding: 1rem; background: rgba(239, 68, 68, 0.1); border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.8rem; color: var(--muted);">At Risk</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--danger);">${p.at_risk_count || 0}</div>
                    </div>
                </div>
            `;
        }
    } catch (e) {
        console.error('Failed to load predictions:', e);
    }
}

// ========================================
// YEAR COMPARISON
// ========================================

/**
 * Load year comparison data
 * @param {number} year1
 * @param {number} year2
 */
export async function loadYearComparison(year1, year2) {
    showLoading();

    try {
        const [res1, res2] = await Promise.all([
            fetch(`${API_BASE_URL}/analytics/dashboard/${year1}`),
            fetch(`${API_BASE_URL}/analytics/dashboard/${year2}`)
        ]);

        const data1 = await res1.json();
        const data2 = await res2.json();

        renderComparisonChart(year1, data1.summary, year2, data2.summary);
    } catch (e) {
        showToast('error', 'Failed to load comparison data');
    } finally {
        hideLoading();
    }
}

/**
 * Render comparison chart
 */
function renderComparisonChart(year1, summary1, year2, summary2) {
    const ctx = document.getElementById('chart-comparison');
    if (!ctx) return;

    if (charts['comparison']) {
        charts['comparison'].destroy();
    }

    charts['comparison'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Employees', 'Granted', 'Used', 'Rate %'],
            datasets: [
                {
                    label: year1.toString(),
                    data: [summary1.total_employees, summary1.total_granted, summary1.total_used, summary1.average_rate],
                    backgroundColor: CHART_COLORS.primary,
                    borderRadius: 4
                },
                {
                    label: year2.toString(),
                    data: [summary2.total_employees, summary2.total_granted, summary2.total_used, summary2.average_rate],
                    backgroundColor: CHART_COLORS.secondary,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: 'rgba(0,0,0,0.05)' } }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#94a3b8' }
                }
            }
        }
    });
}

// ========================================
// MONTHLY TRENDS
// ========================================

/**
 * Load monthly trend data
 * @param {number} year
 */
export async function loadMonthlyTrend(year) {
    try {
        const res = await fetch(`${API_BASE_URL}/analytics/monthly-trend/${year}`);
        const json = await res.json();

        renderMonthlyTrendChart(json.months || []);
    } catch (e) {
        console.error('Failed to load monthly trend:', e);
    }
}

/**
 * Render monthly trend chart
 * @param {Array} months
 */
function renderMonthlyTrendChart(months) {
    const ctx = document.getElementById('chart-monthly-trend');
    if (!ctx) return;

    if (charts['monthlyTrend']) {
        charts['monthlyTrend'].destroy();
    }

    const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    charts['monthlyTrend'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthLabels,
            datasets: [{
                label: 'Days Used',
                data: months.map(m => m.used || 0),
                borderColor: CHART_COLORS.primary,
                backgroundColor: CHART_COLORS.gradient[0],
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.05)' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
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
 * Destroy all charts
 */
export function destroyCharts() {
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    charts = {};
}

/**
 * Cleanup
 */
export function cleanup() {
    destroyCharts();
}

// Export default
export default {
    init,
    loadDashboard,
    renderDepartmentChart,
    renderTypeChart,
    loadPredictions,
    loadYearComparison,
    loadMonthlyTrend,
    destroyCharts,
    cleanup
};
