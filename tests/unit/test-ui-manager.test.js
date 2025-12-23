import UIManager from '../../static/js/modules/ui-manager.js';

describe('UIManager', () => {
    let state;
    let config;
    let visualizations;
    let chartManager;
    let ui;
    let originalFetch;

    const sampleData = [
        {
            employeeNum: '001',
            name: 'Alice',
            haken: 'Factory A',
            granted: 10,
            used: 5,
            balance: 5,
            usageRate: 50,
            year: 2024,
            employeeType: 'staff',
            type: 'staff'
        },
        {
            employeeNum: '002',
            name: 'Bob',
            haken: 'Factory B',
            granted: 8,
            used: 2,
            balance: 6,
            usageRate: 25,
            year: 2024,
            employeeType: 'genzai',
            type: 'haken'
        }
    ];

    beforeEach(() => {
        state = {
            data: [...sampleData],
            year: 2024,
            availableYears: [2023, 2024],
            currentView: 'dashboard',
            typeFilter: 'all'
        };
        config = { apiBase: '/api' };
        visualizations = {
            animateRing: jest.fn(),
            updateGauge: jest.fn(),
            updateExpiringDays: jest.fn()
        };
        chartManager = {
            renderDistribution: jest.fn(),
            renderTrends: jest.fn().mockResolvedValue(undefined),
            renderFactoryChart: jest.fn(),
            renderTypes: jest.fn().mockResolvedValue(undefined),
            renderTop10: jest.fn().mockResolvedValue(undefined)
        };
        ui = new UIManager(state, config, visualizations, chartManager);

        originalFetch = global.fetch;
        global.fetch = jest.fn();
    });

    afterEach(() => {
        global.fetch = originalFetch;
        delete global.ModernUI;
        jest.restoreAllMocks();
    });

    it('updates KPIs from API and falls back on error', async () => {
        document.body.innerHTML = `
            <span id="kpi-used"></span>
            <span id="kpi-balance"></span>
            <span id="kpi-rate"></span>
            <span id="kpi-total"></span>
        `;

        global.fetch.mockResolvedValueOnce({
            json: async () => ({
                status: 'success',
                total_used: 7,
                total_balance: 3,
                usage_rate: 70
            })
        });
        await ui.renderKPIs();

        expect(document.getElementById('kpi-used').innerText).toBe('7');
        expect(visualizations.animateRing).toHaveBeenCalled();

        global.fetch.mockRejectedValueOnce(new Error('fail'));
        await ui.renderKPIs();
        expect(Number(document.getElementById('kpi-total').innerText)).toBe(sampleData.length);
    });

    it('renders tables and handles empty results', () => {
        document.body.innerHTML = `
            <table>
                <tbody id="table-body"></tbody>
            </table>
        `;
        ui.renderTable('alice', 'all');
        expect(document.querySelectorAll('tr').length).toBeGreaterThan(0);

        ui.renderTable('no-match', 'all', () => []);
        expect(document.getElementById('table-body').textContent).toContain('No matching records');
    });

    it('renders table badges and rate styles for multiple branches', () => {
        document.body.innerHTML = `
            <table>
                <tbody id="table-body"></tbody>
            </table>
        `;
        state.data = [
            { employeeNum: 'A', name: 'Alpha', haken: null, granted: 10, used: 12, balance: -2, usageRate: 90, employeeType: 'genzai' },
            { employeeNum: 'B', name: 'Beta', haken: '', granted: 8, used: 4, balance: 2, usageRate: 60, employeeType: 'ukeoi' },
            { employeeNum: 'C', name: 'Gamma', haken: 'X', granted: 5, used: 1, balance: 5, usageRate: 20, employeeType: 'other' }
        ];

        ui.renderTable('', 'all');
        const html = document.getElementById('table-body').innerHTML;
        expect(html).toContain('badge-critical');
        expect(html).toContain('badge-danger');
        expect(html).toContain('badge-success');
        expect(html).toContain('type-genzai');
        expect(html).toContain('type-ukeoi');
        expect(html).toContain('type-staff');
    });

    it('returns early when table body is missing', () => {
        document.body.innerHTML = '';
        expect(() => ui.renderTable('', 'all')).not.toThrow();
    });

    it('handles search and type filtering', () => {
        document.body.innerHTML = `
            <input id="search-input" value="bob" />
            <button class="type-tab" data-type="all"></button>
            <button class="type-tab" data-type="genzai"></button>
            <tbody id="table-body"></tbody>
        `;

        const employeeTypes = {
            data: { all: [sampleData[0]] },
            renderTable: jest.fn()
        };
        ui.handleSearch('test', employeeTypes);
        expect(employeeTypes.renderTable).toHaveBeenCalled();

        const renderSpy = jest.spyOn(ui, 'renderTable').mockImplementation(() => {});
        ui.filterByType('genzai');
        expect(renderSpy).toHaveBeenCalled();

        ui.handleSearch('fallback');
    });

    it('updates counts, year filter, and charts', async () => {
        document.body.innerHTML = `
            <span id="count-all"></span>
            <span id="count-genzai"></span>
            <span id="count-ukeoi"></span>
            <span id="count-staff"></span>
            <div id="year-filter"></div>
        `;

        ui.updateTypeCounts(() => sampleData);
        expect(document.getElementById('count-all').textContent).toBe('2');

        ui.updateYearFilter();
        expect(document.querySelectorAll('#year-filter button').length).toBe(2);

        await ui.renderCharts(() => sampleData, () => [['Factory', 3]]);
        expect(chartManager.renderDistribution).toHaveBeenCalled();
        expect(chartManager.renderFactoryChart).toHaveBeenCalled();

        const noChartUi = new UIManager(state, config, visualizations, null);
        await noChartUi.renderCharts(() => sampleData);
    });

    it('renders charts without factory stats', async () => {
        const chartManagerSpy = {
            renderDistribution: jest.fn(),
            renderTrends: jest.fn().mockResolvedValue(undefined),
            renderFactoryChart: jest.fn(),
            renderTypes: jest.fn().mockResolvedValue(undefined),
            renderTop10: jest.fn().mockResolvedValue(undefined)
        };
        const uiLocal = new UIManager(state, config, visualizations, chartManagerSpy);
        await uiLocal.renderCharts(() => sampleData);
        expect(chartManagerSpy.renderFactoryChart).not.toHaveBeenCalled();
    });

    it('switches views and calls modules', () => {
        jest.useFakeTimers();
        document.body.innerHTML = `
            <div class="view-section" id="view-factories"></div>
            <div class="view-section" id="view-requests"></div>
            <div class="view-section" id="view-calendar"></div>
            <div class="view-section" id="view-compliance"></div>
            <div class="view-section" id="view-analytics"></div>
            <div class="view-section" id="view-reports"></div>
            <div class="view-section" id="view-settings"></div>
            <div class="view-section" id="view-employees"></div>
            <div class="nav-item" data-view="factories"></div>
            <div class="nav-item" data-view="requests"></div>
            <div class="nav-item" data-view="calendar"></div>
            <div class="nav-item" data-view="compliance"></div>
            <div class="nav-item" data-view="analytics"></div>
            <div class="nav-item" data-view="reports"></div>
            <div class="nav-item" data-view="settings"></div>
            <div class="nav-item" data-view="employees"></div>
            <div id="page-title"></div>
        `;

        const modules = {
            animations: { transitionView: jest.fn() },
            chartManager,
            getFactoryStats: jest.fn().mockReturnValue([['A', 1]]),
            requests: { loadFactories: jest.fn(), loadPending: jest.fn(), loadHistory: jest.fn() },
            calendar: { loadEvents: jest.fn() },
            compliance: { loadAlerts: jest.fn() },
            analytics: { loadDashboard: jest.fn() },
            reports: { init: jest.fn() },
            settings: { loadSnapshot: jest.fn() },
            employeeTypes: { loadData: jest.fn() }
        };

        ui.switchView('factories', modules);
        ui.switchView('requests', modules);
        ui.switchView('calendar', modules);
        ui.switchView('compliance', modules);
        ui.switchView('analytics', modules);
        ui.switchView('reports', modules);
        ui.switchView('settings', modules);
        ui.switchView('employees', modules);

        jest.runAllTimers();
        expect(modules.requests.loadFactories).toHaveBeenCalled();
        expect(modules.calendar.loadEvents).toHaveBeenCalled();
        expect(modules.animations.transitionView).toHaveBeenCalled();
        jest.useRealTimers();
    });

    it('toggles the mobile menu', () => {
        document.body.innerHTML = `
            <button id="mobile-menu-toggle"></button>
            <aside id="sidebar"></aside>
            <div id="sidebar-overlay"></div>
        `;

        ui.toggleMobileMenu();
        expect(document.getElementById('sidebar').classList.contains('is-open')).toBe(true);

        ui.toggleMobileMenu();
        ui.closeMobileMenu();
        expect(document.getElementById('sidebar').classList.contains('is-open')).toBe(false);
    });

    it('shows toasts with ModernUI and fallback', () => {
        global.ModernUI = { Toast: { show: jest.fn() } };
        ui.showToast('success', 'Hello', 1000);
        expect(global.ModernUI.Toast.show).toHaveBeenCalled();

        ui.showToast('success', '🚀 Done', 1000);
        expect(global.ModernUI.Toast.show).toHaveBeenCalledWith(expect.objectContaining({
            title: '🚀',
            message: 'Done'
        }));

        ui.showToast('info', '✅ Done', 1000);
        expect(global.ModernUI.Toast.show).toHaveBeenCalled();

        delete global.ModernUI;
        document.body.innerHTML = '<div id="toast-container"></div>';
        jest.useFakeTimers();
        ui.showToast('success', 'Saved', 10);
        expect(document.querySelectorAll('.toast').length).toBe(1);
        jest.runAllTimers();
        expect(document.querySelectorAll('.toast').length).toBe(0);
        jest.useRealTimers();
    });

    it('opens and closes employee modal', async () => {
        document.body.innerHTML = `
            <div id="detail-modal"></div>
            <h3 id="modal-title"></h3>
            <div id="modal-content"></div>
        `;

        global.fetch.mockResolvedValueOnce({
            json: async () => ({
                status: 'success',
                employee: { status: 'active' },
                yukyu_history: [{ year: 2023, usage_rate: 60, granted: 10, used: 6, balance: 4 }],
                usage_history: [{ date: '2024-01-10', days: 1 }],
                total_available: 4
            })
        });

        await ui.openModal('001');
        expect(document.getElementById('detail-modal').classList.contains('active')).toBe(true);
        expect(document.getElementById('modal-content').innerHTML).toContain('001');

        global.fetch.mockResolvedValueOnce({
            json: async () => ({ status: 'error' })
        });
        await ui.openModal('002');
        expect(document.getElementById('modal-content').innerHTML).toContain('Balance');

        ui.closeModal();
        expect(document.getElementById('detail-modal').classList.contains('active')).toBe(false);
    });

    it('handles loading state and button state', () => {
        document.body.innerHTML = `
            <div id="loader"></div>
            <button id="btn"></button>
        `;

        ui.showLoading();
        expect(document.getElementById('loader').classList.contains('active')).toBe(true);
        ui.hideLoading();
        expect(document.getElementById('loader').classList.contains('active')).toBe(false);

        const btn = document.getElementById('btn');
        ui.setBtnLoading(btn, true);
        expect(btn.disabled).toBe(true);
        ui.setBtnLoading(btn, false);
        expect(btn.disabled).toBe(false);
    });

    it('handles missing KPI year and visualizations', async () => {
        state.year = null;
        ui.visualizations = null;
        document.body.innerHTML = `
            <span id="kpi-used"></span>
            <span id="kpi-balance"></span>
            <span id="kpi-rate"></span>
            <span id="kpi-total"></span>
        `;

        await ui.renderKPIs();
        expect(global.fetch).not.toHaveBeenCalled();
        expect(document.getElementById('kpi-used').innerText).toBe('0');
    });

    it('ignores non-success KPI responses', async () => {
        document.body.innerHTML = `
            <span id="kpi-used"></span>
            <span id="kpi-balance"></span>
            <span id="kpi-rate"></span>
            <span id="kpi-total"></span>
        `;

        global.fetch.mockResolvedValueOnce({
            json: async () => ({ status: 'error' })
        });

        await ui.renderKPIs();
        expect(document.getElementById('kpi-rate').innerText).toContain('%');
    });

    it('skips year filter when container is missing', () => {
        document.body.innerHTML = '';
        state.availableYears = [2024];
        ui.updateYearFilter();
    });

    it('skips button loading when button is missing', () => {
        expect(() => ui.setBtnLoading(null, true)).not.toThrow();
    });

    it('toggles menu safely when elements are missing', () => {
        document.body.innerHTML = '';
        expect(() => ui.toggleMobileMenu()).not.toThrow();
    });

    it('returns early for missing year filter and missing employee', async () => {
        document.body.innerHTML = '';
        state.availableYears = [];
        ui.updateYearFilter();

        await ui.openModal('missing');
    });

    it('opens modal with empty history data', async () => {
        document.body.innerHTML = `
            <div id="detail-modal"></div>
            <h3 id="modal-title"></h3>
            <div id="modal-content"></div>
        `;

        state.data.push({
            employeeNum: '003',
            name: 'Cara',
            haken: 'Plant',
            granted: 1,
            used: 0,
            balance: 1,
            usageRate: 0,
            employeeType: 'ukeoi',
            type: 'ukeoi'
        });

        global.fetch.mockResolvedValueOnce({
            json: async () => ({
                status: 'success',
                employee: { status: '在職中' },
                yukyu_history: [],
                usage_history: [],
                total_available: 0
            })
        });

        await ui.openModal('003');
        expect(document.getElementById('modal-title').innerText).toBe('Cara');
    });

    it('updates all UI sections', async () => {
        document.body.innerHTML = '<span id="emp-count-badge"></span>';
        jest.spyOn(ui, 'renderKPIs').mockResolvedValue(undefined);
        jest.spyOn(ui, 'renderTable').mockImplementation(() => {});
        jest.spyOn(ui, 'renderCharts').mockResolvedValue(undefined);
        jest.spyOn(ui, 'updateYearFilter').mockImplementation(() => {});
        jest.spyOn(ui, 'updateTypeCounts').mockImplementation(() => {});

        await ui.updateAll(() => sampleData, () => [['A', 1]]);
        expect(document.getElementById('emp-count-badge').innerText).toContain('Employees');
    });

    it('filters table by employee type', () => {
        document.body.innerHTML = `
            <table>
                <tbody id="table-body"></tbody>
            </table>
        `;
        ui.renderTable('', 'genzai');
        expect(document.querySelectorAll('tr').length).toBeGreaterThan(0);
    });
});
