/**
 * YuKyu UI Module
 * Handles DOM manipulation, rendering, and interaction.
 */
import { Utils } from './utils.js';
import { Visualizations } from './visualizations.js';

export const UI = {
    // Cache DOM elements
    elements: {
        appContainer: document.getElementById('app'),
        views: {
            dashboard: document.getElementById('view-dashboard'),
            employees: document.getElementById('view-employees'),
            companies: document.getElementById('view-companies'),
            import: document.getElementById('view-import'),
            settings: document.getElementById('view-settings')
        },
        sidebarItems: document.querySelectorAll('.sidebar-item'),
        loadingOverlay: document.getElementById('loading-overlay')
    },

    init() {
        this.setupEventListeners();
    },

    setupEventListeners() {
        // Mobile menu toggle
        const menuToggle = document.getElementById('mobile-menu-toggle');
        const sidebar = document.querySelector('.sidebar');

        if (menuToggle && sidebar) {
            menuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('active');
            });

            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', (e) => {
                if (window.innerWidth <= 768 &&
                    sidebar.classList.contains('active') &&
                    !sidebar.contains(e.target) &&
                    !menuToggle.contains(e.target)) {
                    sidebar.classList.remove('active');
                }
            });
        }
    },

    showLoading() {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.classList.remove('d-none');
        }
    },

    hideLoading() {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.classList.add('d-none');
        }
    },

    setBtnLoading(btn, isLoading) {
        if (!btn) return;
        if (isLoading) {
            btn.dataset.originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading-spinner-sm"></span> Processing...';
            btn.disabled = true;
        } else {
            btn.innerHTML = btn.dataset.originalText || btn.textContent;
            btn.disabled = false;
        }
    },

    showToast(type, message, duration = 3000) {
        // Remove existing toasts
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = `toast toast-${type} glass-card`;

        // Icon based on type
        let icon = '';
        if (type === 'success') icon = '✓';
        if (type === 'error') icon = '✕';
        if (type === 'info') icon = 'ℹ';
        if (type === 'warning') icon = '⚠';

        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icon}</span>
                <span class="toast-message">${Utils.escapeHtml(message)}</span>
            </div>
        `;

        document.body.appendChild(toast);

        // Trigger animation
        requestAnimationFrame(() => toast.classList.add('show'));

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    switchView(viewName) {
        // Hide all views
        Object.values(this.elements.views).forEach(el => {
            if (el) el.classList.add('d-none');
        });

        // Show target view
        const target = this.elements.views[viewName];
        if (target) {
            target.classList.remove('d-none');
            target.classList.add('fade-in');
        }

        // Update sidebar
        this.elements.sidebarItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href') === `#${viewName}`) {
                item.classList.add('active');
            }
        });

        // Update window title
        document.title = `YuKyu Dashboard - ${viewName.charAt(0).toUpperCase() + viewName.slice(1)}`;
    },

    renderEmployeesTable(employees) {
        const tbody = document.querySelector('#employees-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (!employees || employees.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4">No data found</td></tr>`;
            return;
        }

        const fragment = document.createDocumentFragment();

        employees.forEach(emp => {
            const tr = document.createElement('tr');
            tr.className = 'fade-in';

            // Logic for status classes
            const usageRate = emp.used_days > 0 ? (emp.used_days / emp.total_days * 100) : 0;
            let statusClass = 'status-good';
            if (usageRate >= 80) statusClass = 'status-critical';
            else if (usageRate >= 50) statusClass = 'status-warning';

            tr.innerHTML = `
                <td><span class="emp-id">${Utils.escapeHtml(emp.employee_id)}</span></td>
                <td>
                    <div class="emp-name-container">
                        <span class="emp-name">${Utils.escapeHtml(emp.name)}</span>
                        ${emp.name_kana ? `<span class="emp-kana text-xs text-muted">${Utils.escapeHtml(emp.name_kana)}</span>` : ''}
                    </div>
                </td>
                <td>${Utils.escapeHtml(emp.company || '-')}</td>
                <td class="text-right font-mono">${Utils.safeNumber(emp.total_days).toFixed(1)}</td>
                <td class="text-right font-mono">${Utils.safeNumber(emp.used_days).toFixed(1)}</td>
                <td class="text-right font-mono font-bold ${emp.remaining_days < 5 ? 'text-danger' : 'text-success'}">
                    ${Utils.safeNumber(emp.remaining_days).toFixed(1)}
                </td>
                <td class="text-center">
                   <span class="status-badge ${statusClass}">${usageRate.toFixed(0)}%</span>
                </td>
                <td class="text-right">
                    <button class="btn-icon btn-sm" data-action="edit" data-id="${emp.id}" title="Edit">
                        ✎
                    </button>
                    <button class="btn-icon btn-sm text-danger" data-action="delete" data-id="${emp.id}" title="Delete">
                        ✕
                    </button>
                </td>
            `;
            fragment.appendChild(tr);
        });

        tbody.appendChild(fragment);

        // Update count
        const countEl = document.getElementById('total-employees-count');
        if (countEl) countEl.textContent = employees.length;
    },

    // Render Stats Cards with Visualizations
    renderStats(stats) {
        Visualizations.animateNumber(
            document.getElementById('stat-total-employees'),
            0,
            stats.totalEmployees,
            1000
        );

        Visualizations.updateGauge(
            stats.complianceRate,
            stats.compliantCount,
            stats.totalEmployees
        );

        // Update other specific stat elements...
    },

    updateStats(stats) {
        // Update simple text stats
        this.setElementText('kpi-total', stats.totalEmployees);
        this.setElementText('qs-haken', stats.hakenCount);
        this.setElementText('qs-ukeoi', stats.ukeoiCount);
        this.setElementText('qs-staff', stats.staffCount);

        // Update details
        this.setElementText('kpi-used-detail', `${Math.round(stats.totalUsed)} days used`);
        this.setElementText('kpi-balance-detail', `${Math.round(stats.totalBalance)} days left`);
        this.setElementText('kpi-rate-detail', `${stats.utilizationRate.toFixed(1)}% avg rate`);
    },

    /**
     * Helper to calculate and update stats from raw employee data
     * Used by the modular App
     */
    updateStatsFromData(employees) {
        if (!employees) return;

        let totalUsed = 0;
        let totalGranted = 0;
        let hakenCount = 0;
        let ukeoiCount = 0;
        let staffCount = 0;

        employees.forEach(emp => {
            totalUsed += parseFloat(emp.used_days || 0);
            totalGranted += parseFloat(emp.total_days || 0);

            const type = (emp.employee_type || '').toLowerCase();
            if (type.includes('haken') || type.includes('dispatch')) hakenCount++;
            else if (type.includes('ukeoi') || type.includes('contract')) ukeoiCount++;
            else staffCount++;
        });

        const stats = {
            totalEmployees: employees.length,
            totalUsed,
            totalGranted,
            totalBalance: totalGranted - totalUsed,
            utilizationRate: totalGranted > 0 ? (totalUsed / totalGranted) * 100 : 0,
            hakenCount,
            ukeoiCount,
            staffCount
        };

        this.updateStats(stats);
        return stats;
    },

    setElementText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    },

    populateYearSelector(currentYear, availableYears = [], onChangeCallback) {
        const select = document.getElementById('year-selector');
        if (!select) return;

        select.innerHTML = '';

        // If no years provided, default to current and past 3
        const years = availableYears.length > 0
            ? [...availableYears].sort((a, b) => b - a)
            : [currentYear, currentYear - 1, currentYear - 2, currentYear - 3];

        years.forEach(y => {
            const option = document.createElement('option');
            option.value = y;
            option.textContent = y + '年';
            if (parseInt(y) === parseInt(currentYear)) option.selected = true;
            select.appendChild(option);
        });

        // Add event listener once
        if (!select.dataset.listenerAdded) {
            select.addEventListener('change', (e) => {
                onChangeCallback(parseInt(e.target.value));
            });
            select.dataset.listenerAdded = 'true';
        }
    },

    openModal(id) {
        console.log('Opening modal for id:', id);
        // Implement real modal logic here if needed
    }
};
