/**
 * YuKyu Dashboard v6.0 - Refactored with ES6 Modules
 * Arquitectura modular con separación de responsabilidades
 */

// ========================================
// IMPORTS - Módulos ES6
// ========================================
import * as Utils from './modules/utils.js';
import { ThemeManager } from './modules/theme-manager.js';
import { DataService } from './modules/data-service.js';
import { Visualizations, ChartManager } from './modules/chart-manager.js';
import UIManager from './modules/ui-manager.js';
import { ExportService } from './modules/export-service.js';
import { LeaveRequestsManager } from './modules/leave-requests-manager.js';

// ========================================
// APLICACIÓN PRINCIPAL
// ========================================
const App = {
    // Estado de la aplicación
    state: {
        data: [],
        year: null,
        availableYears: [],
        charts: {},
        currentView: 'dashboard',
        typeFilter: 'all'
    },

    // Configuración
    config: {
        apiBase: 'http://localhost:8000/api'
    },

    // ========================================
    // MÓDULOS REFACTORIZADOS (con adaptadores para compatibilidad)
    // ========================================

    // Utils - Adaptador para mantener compatibilidad con App.utils
    utils: Utils,

    // Theme Manager - Adaptador
    theme: null, // Se inicializa en init()

    // Visualizations - Adaptador
    visualizations: null, // Se inicializa en init()

    // Data Service - Adaptador
    data: {
        _service: null, // Se inicializa en init()

        async fetchEmployees(year = null, activeOnly = true) {
            return this._service.fetchEmployees(
                year,
                activeOnly,
                App.state,
                () => App.ui.updateAll(
                    () => this.getFiltered(),
                    () => this.getFactoryStats()
                ),
                (type, msg) => App.ui.showToast(type, msg)
            );
        },

        async sync() {
            return this._service.sync(
                (btn, loading) => App.ui.setBtnLoading(btn, loading),
                (type, msg, duration) => App.ui.showToast(type, msg, duration),
                () => this.fetchEmployees(App.state.year)
            );
        },

        async syncGenzai() {
            return this._service.syncGenzai(
                (btn, loading) => App.ui.setBtnLoading(btn, loading),
                (type, msg, duration) => App.ui.showToast(type, msg, duration)
            );
        },

        async syncUkeoi() {
            return this._service.syncUkeoi(
                (btn, loading) => App.ui.setBtnLoading(btn, loading),
                (type, msg, duration) => App.ui.showToast(type, msg, duration)
            );
        },

        getFiltered() {
            return this._service.getFiltered(App.state.data, App.state.year);
        },

        getFactoryStats() {
            const filtered = this.getFiltered();
            return this._service.getFactoryStats(filtered);
        }
    },

    // Charts - Adaptador
    charts: {
        _manager: null, // Se inicializa en init()

        destroy(id) {
            return this._manager.destroy(id);
        },

        renderDistribution() {
            const data = App.data.getFiltered();
            return this._manager.renderDistribution(data);
        },

        async renderTrends() {
            return this._manager.renderTrends(App.state.year);
        },

        async renderTypes() {
            return this._manager.renderTypes(App.state.year);
        },

        async renderTop10() {
            const data = App.data.getFiltered();
            return this._manager.renderTop10(App.state.year, data);
        },

        renderFactoryChart() {
            const stats = App.data.getFactoryStats();
            return this._manager.renderFactoryChart(stats);
        }
    },

    // UI Manager - Adaptador
    ui: {
        _manager: null, // Se inicializa en init()

        async updateAll() {
            return this._manager.updateAll(
                () => App.data.getFiltered(),
                () => App.data.getFactoryStats()
            );
        },

        switchView(viewName) {
            return this._manager.switchView(viewName, {
                animations: App.animations,
                requests: App.requests,
                calendar: App.calendar,
                compliance: App.compliance,
                analytics: App.analytics,
                reports: App.reports,
                settings: App.settings,
                employeeTypes: App.employeeTypes,
                chartManager: App.charts._manager,
                getFactoryStats: () => App.data.getFactoryStats()
            });
        },

        async renderKPIs() {
            return this._manager.renderKPIs();
        },

        renderTable(filterText = '', typeFilter = 'all') {
            return this._manager.renderTable(
                filterText,
                typeFilter,
                () => App.data.getFiltered()
            );
        },

        handleSearch(val) {
            return this._manager.handleSearch(val, App.employeeTypes);
        },

        filterByType(type) {
            return this._manager.filterByType(type, () => App.data.getFiltered());
        },

        updateTypeCounts() {
            return this._manager.updateTypeCounts(() => App.data.getFiltered());
        },

        updateYearFilter() {
            return this._manager.updateYearFilter();
        },

        async renderCharts() {
            return this._manager.renderCharts(
                () => App.data.getFiltered(),
                () => App.data.getFactoryStats()
            );
        },

        showLoading() {
            return this._manager.showLoading();
        },

        hideLoading() {
            return this._manager.hideLoading();
        },

        setBtnLoading(btn, isLoading) {
            return this._manager.setBtnLoading(btn, isLoading);
        },

        toggleMobileMenu() {
            return this._manager.toggleMobileMenu();
        },

        closeMobileMenu() {
            return this._manager.closeMobileMenu();
        },

        showToast(type, msg, duration) {
            return this._manager.showToast(type, msg, duration);
        },

        async openModal(id) {
            return this._manager.openModal(id);
        },

        closeModal() {
            return this._manager.closeModal();
        }
    },

    // Export Service - Adaptador
    export: null, // Se inicializa en init()

    // ========================================
    // INICIALIZACIÓN
    // ========================================
    async init() {
        console.log('🚀 Initializing YuKyu Premium Dashboard v6.0 (Modular)...');

        // Inicializar módulos
        this.theme = new ThemeManager();
        this.visualizations = new Visualizations();
        this.data._service = new DataService(this.config.apiBase);
        this.charts._manager = new ChartManager(this.state, this.config.apiBase);
        this.ui._manager = new UIManager(this.state, this.config, this.visualizations, this.charts._manager);
        this.export = new ExportService();

        // Initialize Leave Requests Manager with UI callbacks
        this.requests._manager.init({
            showToast: (type, msg, duration) => this.ui.showToast(type, msg, duration),
            showLoading: () => this.ui.showLoading(),
            hideLoading: () => this.ui.hideLoading()
        });

        this.ui.showLoading();

        // Inicializar tema
        this.theme.init();

        // Fetch inicial de datos
        await this.data.fetchEmployees();

        this.ui.hideLoading();
        this.events.setupListeners();
    },

    // ========================================
    // EVENT LISTENERS
    // ========================================
    events: {
        setupListeners() {
            // Cerrar modal al hacer clic fuera
            const detailModal = document.getElementById('detail-modal');
            if (detailModal) {
                detailModal.addEventListener('click', (e) => {
                    if (e.target.id === 'detail-modal') App.ui.closeModal();
                });
            }

            // Event delegation para filas de empleados (XSS-safe)
            const tableBody = document.getElementById('table-body');
            if (tableBody) {
                tableBody.addEventListener('click', (e) => {
                    const row = e.target.closest('.employee-row');
                    if (row && row.dataset.employeeNum) {
                        App.ui.openModal(row.dataset.employeeNum);
                    }
                });
            }

            // Event delegation para resultados de búsqueda
            const searchResults = document.getElementById('emp-search-results');
            if (searchResults) {
                searchResults.addEventListener('click', (e) => {
                    const item = e.target.closest('.search-result-item');
                    if (item && item.dataset.employeeNum) {
                        App.requests.selectEmployee(item.dataset.employeeNum);
                    }
                });
            }

            // Event delegation para acciones de solicitudes de vacaciones
            const pendingList = document.getElementById('pending-requests');
            if (pendingList) {
                pendingList.addEventListener('click', (e) => {
                    const approveBtn = e.target.closest('.btn-approve');
                    const rejectBtn = e.target.closest('.btn-reject');
                    const cancelBtn = e.target.closest('.btn-cancel');
                    if (approveBtn?.dataset.requestId) {
                        App.requests.approve(parseInt(approveBtn.dataset.requestId));
                    }
                    if (rejectBtn?.dataset.requestId) {
                        App.requests.reject(parseInt(rejectBtn.dataset.requestId));
                    }
                    if (cancelBtn?.dataset.requestId) {
                        App.requests.cancel(parseInt(cancelBtn.dataset.requestId));
                    }
                });
            }

            // Event delegation para tabla de historial (revert)
            const historyTable = document.getElementById('requests-history');
            if (historyTable) {
                historyTable.addEventListener('click', (e) => {
                    const revertBtn = e.target.closest('.btn-revert');
                    if (revertBtn?.dataset.requestId) {
                        App.requests.revert(parseInt(revertBtn.dataset.requestId));
                    }
                });
            }

            // Navegación por teclado
            document.addEventListener('keydown', (e) => {
                // ESC para cerrar modal
                if (e.key === 'Escape') {
                    const modal = document.getElementById('detail-modal');
                    if (modal?.classList.contains('active')) {
                        App.ui.closeModal();
                    }
                    App.ui.closeMobileMenu();
                }
            });

            // Toggle del menú móvil
            const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
            if (mobileMenuToggle) {
                mobileMenuToggle.addEventListener('click', () => {
                    App.ui.toggleMobileMenu();
                });
            }

            // Overlay del sidebar
            const sidebarOverlay = document.getElementById('sidebar-overlay');
            if (sidebarOverlay) {
                sidebarOverlay.addEventListener('click', () => {
                    App.ui.closeMobileMenu();
                });
            }

            // Cerrar menú móvil al hacer clic en item de navegación
            document.querySelectorAll('.nav-item').forEach(item => {
                item.addEventListener('click', () => {
                    App.ui.closeMobileMenu();
                });
            });

            // Event listener para filtros de año (usando event delegation)
            const yearFilter = document.getElementById('year-filter');
            if (yearFilter) {
                yearFilter.addEventListener('click', (e) => {
                    const btn = e.target.closest('button[data-year]');
                    if (btn) {
                        const year = parseInt(btn.dataset.year);
                        App.data.fetchEmployees(year);
                        App.state.year = year;
                    }
                });
            }
        }
    },

    // ========================================
    // MÓDULOS NO REFACTORIZADOS (mantenidos del original)
    // Estos módulos requieren más análisis y testing antes de refactorizar
    // ========================================

    // NOTA: Las siguientes secciones se mantienen del archivo original
    // y deben ser extraídas en futuras iteraciones:
    // - requests (módulo de solicitudes de vacaciones)
    // - compliance (módulo de cumplimiento)
    // - settings (módulo de configuración)
    // - calendar (módulo de calendario)
    // - analytics (módulo de analíticas avanzadas)
    // - reports (módulo de reportes)
    // - employeeTypes (módulo de tipos de empleados)
    // - animations (módulo de animaciones GSAP)

    // Leave Requests Module - Fully implemented via LeaveRequestsManager
    requests: {
        _manager: LeaveRequestsManager,
        get selectedEmployee() { return this._manager.selectedEmployee; },
        set selectedEmployee(val) { this._manager.selectedEmployee = val; },

        async loadFactories() {
            return this._manager.loadFactories();
        },
        async loadPending() {
            return this._manager.loadPending();
        },
        async loadHistory(status = null) {
            return this._manager.loadHistory(status);
        },
        async selectEmployee(id) {
            return this._manager.selectEmployee(id);
        },
        async approve(id) {
            return this._manager.approve(id);
        },
        async reject(id, reason) {
            return this._manager.reject(id, reason);
        },
        async cancel(id) {
            return this._manager.cancel(id);
        },
        async revert(id) {
            return this._manager.revert(id);
        },
        async create(requestData) {
            return this._manager.create(requestData);
        }
    },

    calendar: {
        loadEvents() { console.warn('calendar.loadEvents not implemented'); }
    },

    compliance: {
        loadAlerts() { console.warn('compliance.loadAlerts not implemented'); }
    },

    analytics: {
        loadDashboard() { console.warn('analytics.loadDashboard not implemented'); }
    },

    reports: {
        init() { console.warn('reports.init not implemented'); }
    },

    settings: {
        loadSnapshot() { console.warn('settings.loadSnapshot not implemented'); }
    },

    employeeTypes: {
        data: { all: [] },
        loadData() { console.warn('employeeTypes.loadData not implemented'); },
        renderTable(searchVal) { console.warn('employeeTypes.renderTable not implemented:', searchVal); }
    },

    animations: {
        init() { console.warn('animations.init not implemented'); },
        transitionView(target) { console.warn('animations.transitionView not implemented:', target); }
    }
};

// ========================================
// WINDOW GLOBAL (para compatibilidad)
// ========================================
window.App = App;

// ========================================
// INICIALIZACIÓN AL CARGAR DOM
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    App.init();

    // Inicializar animaciones GSAP después de un delay
    setTimeout(() => {
        if (App.animations) {
            App.animations.init();
        }
    }, 300);
});

// Export para uso como módulo ES6
export default App;
