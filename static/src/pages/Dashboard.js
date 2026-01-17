/**
 * Dashboard Page Module
 * Vista principal con graficos y KPIs
 * @version 1.0.0
 */

import { getState, getFilteredData, subscribe } from '../store/state.js';
import { API_BASE_URL, CHART_COLORS, SVG, ANIMATION_DURATIONS } from '../config/constants.js';

// ========================================
// DASHBOARD STATE
// ========================================

let isInitialized = false;
let charts = {};

// ========================================
// INITIALIZATION
// ========================================

/**
 * Initialize dashboard
 */
export function init() {
    if (isInitialized) return;

    // Subscribe to state changes
    subscribe(onStateChange, ['data', 'year']);

    isInitialized = true;
}

/**
 * Handle state changes
 * @param {Object} newState
 * @param {Object} prevState
 */
function onStateChange(newState, prevState) {
    if (newState.currentView === 'dashboard') {
        render();
    }
}

// ========================================
// RENDERING
// ========================================

/**
 * Render the dashboard
 */
export async function render() {
    const state = getState();
    const data = getFilteredData();

    await renderKPIs(data, state.year);
    renderCharts(data);
    updateTypeCounts(data);
}

/**
 * Render KPI cards
 * @param {Array} data - Employee data
 * @param {number} year - Current year
 */
async function renderKPIs(data, year) {
    const total = data.length;
    const granted = data.reduce((s, e) => s + safeNumber(e.granted), 0);

    // Fetch TRUE usage from individual dates API
    let used = 0;
    let balance = 0;
    let rate = 0;

    try {
        if (year) {
            const res = await fetch(`${API_BASE_URL}/yukyu/kpi-stats/${year}`);
            const kpi = await res.json();

            if (kpi.status === 'success') {
                used = kpi.total_used || 0;
                balance = kpi.total_balance || 0;
                rate = kpi.usage_rate || 0;
            }
        }
    } catch (e) {
        // Fallback to local calculation
        used = data.reduce((s, e) => s + safeNumber(e.used), 0);
        balance = data.reduce((s, e) => s + safeNumber(e.balance), 0);
        rate = granted > 0 ? Math.round((used / granted) * 100) : 0;
    }

    // Fallback if API returns 0
    if (used === 0) {
        used = data.reduce((s, e) => s + safeNumber(e.used), 0);
        balance = data.reduce((s, e) => s + safeNumber(e.balance), 0);
        rate = granted > 0 ? Math.round((used / granted) * 100) : 0;
    }

    // Update KPI elements
    updateKPIElement('kpi-total', total);
    updateKPIElement('kpi-granted', granted.toFixed(1));
    updateKPIElement('kpi-used', used.toFixed(1));
    updateKPIElement('kpi-balance', balance.toFixed(1));
    updateKPIElement('kpi-rate', rate + '%');

    // Update progress ring
    animateProgressRing('usage-ring', 'usage-ring-value', rate, 100);
}

/**
 * Update a KPI element with animation
 * @param {string} elementId
 * @param {*} value
 */
function updateKPIElement(elementId, value) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = value;
    }
}

/**
 * Render all dashboard charts
 * @param {Array} data - Employee data
 */
function renderCharts(data) {
    renderDistributionChart(data);
    renderTrendsChart(data);
}

/**
 * Render balance distribution chart
 * @param {Array} data - Employee data
 */
function renderDistributionChart(data) {
    const ctx = document.getElementById('chart-distribution');
    if (!ctx) return;

    // Destroy existing chart
    if (charts['distribution']) {
        charts['distribution'].destroy();
    }

    // Calculate distribution
    const distribution = {
        high: data.filter(e => e.balance >= 10).length,
        medium: data.filter(e => e.balance >= 5 && e.balance < 10).length,
        low: data.filter(e => e.balance > 0 && e.balance < 5).length,
        zero: data.filter(e => e.balance <= 0).length
    };

    charts['distribution'] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['10+ days', '5-10 days', '1-5 days', '0 days'],
            datasets: [{
                data: [distribution.high, distribution.medium, distribution.low, distribution.zero],
                backgroundColor: [
                    CHART_COLORS.distribution.high,
                    CHART_COLORS.distribution.medium,
                    CHART_COLORS.distribution.low,
                    CHART_COLORS.distribution.zero
                ],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#94a3b8',
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(0, 212, 255, 0.3)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percent = total > 0 ? Math.round((context.raw / total) * 100) : 0;
                            return `${context.label}: ${context.raw} (${percent}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Render usage trends chart
 * @param {Array} data - Employee data
 */
function renderTrendsChart(data) {
    const ctx = document.getElementById('chart-trends');
    if (!ctx) return;

    // Destroy existing chart
    if (charts['trends']) {
        charts['trends'].destroy();
    }

    // Get top 10 employees by usage
    const sortedData = [...data].sort((a, b) => b.used - a.used).slice(0, 10);

    charts['trends'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedData.map(e => e.name ? e.name.substring(0, 8) : e.employee_num),
            datasets: [{
                label: 'Days Used',
                data: sortedData.map(e => e.used || 0),
                backgroundColor: CHART_COLORS.gradient[0],
                borderColor: CHART_COLORS.primary,
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#94a3b8'
                }
            }
        }
    });
}

/**
 * Update employee type counts in filter tabs
 * @param {Array} data - Employee data
 */
function updateTypeCounts(data) {
    const counts = {
        all: data.length,
        haken: data.filter(e => e.employeeType === 'haken' || e.type === 'haken').length,
        ukeoi: data.filter(e => e.employeeType === 'ukeoi' || e.type === 'ukeoi').length,
        staff: data.filter(e => e.employeeType === 'staff' || e.type === 'staff').length
    };

    Object.entries(counts).forEach(([type, count]) => {
        const el = document.getElementById(`count-${type}`);
        if (el) el.textContent = count;
    });
}

// ========================================
// VISUALIZATIONS
// ========================================

/**
 * Animate a progress ring SVG
 * @param {string} ringId - Ring element ID
 * @param {string} valueId - Value text element ID
 * @param {number} value - Current value
 * @param {number} maxValue - Maximum value
 */
function animateProgressRing(ringId, valueId, value, maxValue) {
    const ring = document.getElementById(ringId);
    const valueEl = document.getElementById(valueId);
    if (!ring || !valueEl) return;

    const { radius, circumference } = SVG.ring;
    const percent = Math.min(value / maxValue, 1);
    const offset = circumference - (percent * circumference);

    // Set initial state
    ring.style.strokeDasharray = circumference;
    ring.style.strokeDashoffset = circumference;

    // Trigger animation
    setTimeout(() => {
        ring.style.strokeDashoffset = offset;
    }, 100);

    // Animate number
    animateNumber(valueEl, 0, value, ANIMATION_DURATIONS.number);
}

/**
 * Animate number counting up
 * @param {HTMLElement} element - Target element
 * @param {number} start - Start value
 * @param {number} end - End value
 * @param {number} duration - Animation duration in ms
 */
function animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    const isFloat = !Number.isInteger(end);

    const animate = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out cubic
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = start + (end - start) * easeOut;

        if (isFloat) {
            element.textContent = current.toFixed(1);
        } else {
            element.textContent = Math.round(current).toLocaleString();
        }

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    };

    requestAnimationFrame(animate);
}

/**
 * Update compliance gauge
 * @param {number} complianceRate - Rate percentage
 * @param {number} compliant - Compliant count
 * @param {number} total - Total count
 */
export function updateComplianceGauge(complianceRate, compliant = 0, total = 0) {
    const gauge = document.getElementById('gauge-compliance');
    const valueEl = document.getElementById('gauge-value');
    const labelEl = document.querySelector('.gauge-label');
    const countEl = document.getElementById('compliance-count');
    const totalEl = document.getElementById('compliance-total');

    if (!gauge) return;

    const arcLength = SVG.gauge.arcLength;
    const percent = Math.min(complianceRate / 100, 1);
    const offset = arcLength - (percent * arcLength);

    // Set color based on compliance
    let color = 'var(--danger)';
    if (complianceRate >= 80) color = 'var(--success)';
    else if (complianceRate >= 50) color = 'var(--warning)';

    gauge.style.stroke = color;
    gauge.style.strokeDasharray = arcLength;
    gauge.style.strokeDashoffset = arcLength;

    setTimeout(() => {
        gauge.style.strokeDashoffset = offset;
    }, 200);

    if (valueEl) {
        animateNumber(valueEl, 0, complianceRate, ANIMATION_DURATIONS.gauge);
        setTimeout(() => {
            valueEl.textContent = Math.round(complianceRate) + '%';
        }, ANIMATION_DURATIONS.gauge + 100);
    }

    if (countEl) countEl.textContent = compliant;
    if (totalEl) totalEl.textContent = total;

    if (labelEl) {
        if (complianceRate >= 80) {
            labelEl.textContent = 'Excellent';
            labelEl.style.color = 'var(--success)';
        } else if (complianceRate >= 50) {
            labelEl.textContent = 'Attention';
            labelEl.style.color = 'var(--warning)';
        } else {
            labelEl.textContent = 'Needs Improvement';
            labelEl.style.color = 'var(--danger)';
        }
    }
}

/**
 * Update expiring days countdown
 * @param {Array} data - Employee data
 */
export function updateExpiringDays(data) {
    const countdownContainer = document.getElementById('countdown-container');
    const noExpiring = document.getElementById('no-expiring');
    const expiringDays = document.getElementById('expiring-days');
    const expiringDetail = document.getElementById('expiring-detail');
    const criticalCount = document.getElementById('critical-count');
    const warningCount = document.getElementById('warning-count');
    const healthyCount = document.getElementById('healthy-count');

    // Calculate categories
    const critical = data.filter(e => e.balance <= 0).length;
    const warning = data.filter(e => e.balance > 0 && e.balance < 3).length;
    const healthy = data.filter(e => e.balance >= 5).length;

    // Update counts with animation
    if (criticalCount) animateNumber(criticalCount, 0, critical, 800);
    if (warningCount) animateNumber(warningCount, 0, warning, 800);
    if (healthyCount) animateNumber(healthyCount, 0, healthy, 800);

    // Filter employees with low balance
    const expiring = data
        .filter(e => e.balance < 5 && e.balance > 0)
        .sort((a, b) => a.balance - b.balance);

    const totalExpiringDays = expiring.reduce((sum, e) => sum + e.balance, 0);

    if (expiring.length === 0) {
        if (countdownContainer) countdownContainer.style.display = 'none';
        if (noExpiring) noExpiring.style.display = 'block';
    } else {
        if (countdownContainer) countdownContainer.style.display = 'flex';
        if (noExpiring) noExpiring.style.display = 'none';
        if (expiringDays) expiringDays.textContent = totalExpiringDays.toFixed(1) + ' days';
        if (expiringDetail) expiringDetail.textContent = `from ${expiring.length} employees`;
    }
}

// ========================================
// HELPERS
// ========================================

/**
 * Safely convert to number
 * @param {*} val - Value to convert
 * @param {number} defaultVal - Default value
 * @returns {number}
 */
function safeNumber(val, defaultVal = 0) {
    const num = parseFloat(val);
    return Number.isFinite(num) ? num : defaultVal;
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
 * Cleanup on page leave
 */
export function cleanup() {
    destroyCharts();
}

// Export default
export default {
    init,
    render,
    updateComplianceGauge,
    updateExpiringDays,
    destroyCharts,
    cleanup
};
