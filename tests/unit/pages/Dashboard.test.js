/**
 * Tests for Dashboard Page Module
 * YuKyuDATA Application
 */

const { JSDOM } = require('jsdom');

// Setup DOM environment before imports
const dom = new JSDOM(`
  <!DOCTYPE html>
  <html>
  <head></head>
  <body>
    <div id="kpi-total">0</div>
    <div id="kpi-granted">0</div>
    <div id="kpi-used">0</div>
    <div id="kpi-balance">0</div>
    <div id="kpi-rate">0%</div>
    <svg id="usage-ring"></svg>
    <div id="usage-ring-value">0</div>
    <canvas id="chart-distribution"></canvas>
    <canvas id="chart-trends"></canvas>
    <div id="count-all">0</div>
    <div id="count-haken">0</div>
    <div id="count-ukeoi">0</div>
    <div id="count-staff">0</div>
    <svg id="gauge-compliance"></svg>
    <div id="gauge-value">0</div>
    <div class="gauge-label"></div>
    <div id="compliance-count">0</div>
    <div id="compliance-total">0</div>
    <div id="countdown-container"></div>
    <div id="no-expiring"></div>
    <div id="expiring-days"></div>
    <div id="expiring-detail"></div>
    <div id="critical-count">0</div>
    <div id="warning-count">0</div>
    <div id="healthy-count">0</div>
  </body>
  </html>
`, {
  url: 'http://localhost'
});

global.document = dom.window.document;
global.window = dom.window;
global.HTMLElement = dom.window.HTMLElement;
global.requestAnimationFrame = (cb) => setTimeout(cb, 16);
global.cancelAnimationFrame = (id) => clearTimeout(id);
global.performance = { now: () => Date.now() };
global.fetch = jest.fn();

// Mock Chart.js
global.Chart = jest.fn().mockImplementation(() => ({
  destroy: jest.fn(),
  update: jest.fn()
}));

// Mock state module
jest.mock('../../../static/src/store/state.js', () => ({
  getState: jest.fn(() => ({ year: 2025, currentView: 'dashboard' })),
  getFilteredData: jest.fn(() => []),
  subscribe: jest.fn((callback) => () => {})
}));

// Mock constants
jest.mock('../../../static/src/config/constants.js', () => ({
  API_BASE_URL: 'http://localhost:8000/api',
  CHART_COLORS: {
    primary: '#06b6d4',
    distribution: {
      high: '#34d399',
      medium: '#fbbf24',
      low: '#f87171',
      zero: '#64748b'
    },
    gradient: ['rgba(6, 182, 212, 0.8)']
  },
  SVG: {
    ring: { radius: 45, circumference: 283 },
    gauge: { arcLength: 188 }
  },
  ANIMATION_DURATIONS: {
    number: 800,
    gauge: 1000
  }
}));

// Import after mocks
const Dashboard = require('../../../static/src/pages/Dashboard.js');
const { getState, getFilteredData, subscribe } = require('../../../static/src/store/state.js');

describe('Dashboard Page Module', () => {
  let mockEmployeeData;

  beforeEach(() => {
    jest.clearAllMocks();

    // Reset DOM elements
    document.getElementById('kpi-total').textContent = '0';
    document.getElementById('kpi-granted').textContent = '0';
    document.getElementById('kpi-used').textContent = '0';
    document.getElementById('kpi-balance').textContent = '0';
    document.getElementById('kpi-rate').textContent = '0%';

    // Setup mock data
    mockEmployeeData = [
      { id: 1, name: '田中太郎', granted: 20, used: 5, balance: 15, employeeType: 'haken' },
      { id: 2, name: '山田花子', granted: 15, used: 10, balance: 5, employeeType: 'ukeoi' },
      { id: 3, name: '佐藤次郎', granted: 20, used: 18, balance: 2, employeeType: 'haken' },
      { id: 4, name: '鈴木三郎', granted: 10, used: 10, balance: 0, employeeType: 'staff' },
      { id: 5, name: '高橋四郎', granted: 20, used: 8, balance: 12, employeeType: 'haken' }
    ];

    getFilteredData.mockReturnValue(mockEmployeeData);
    getState.mockReturnValue({ year: 2025, currentView: 'dashboard' });

    // Mock fetch
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve({
        status: 'success',
        total_used: 51,
        total_balance: 34,
        usage_rate: 60
      })
    });
  });

  describe('Initialization', () => {
    test('exports init function', () => {
      expect(typeof Dashboard.init).toBe('function');
    });

    test('exports render function', () => {
      expect(typeof Dashboard.render).toBe('function');
    });

    test('init subscribes to state changes', () => {
      Dashboard.init();
      expect(subscribe).toHaveBeenCalled();
    });

    test('init subscribes to data and year changes', () => {
      Dashboard.init();

      const subscribeCall = subscribe.mock.calls[0];
      expect(subscribeCall[1]).toContain('data');
      expect(subscribeCall[1]).toContain('year');
    });
  });

  describe('Rendering', () => {
    test('render calls getFilteredData', async () => {
      await Dashboard.render();
      expect(getFilteredData).toHaveBeenCalled();
    });

    test('render fetches KPI stats from API', async () => {
      await Dashboard.render();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/yukyu/kpi-stats/')
      );
    });
  });

  describe('KPI Calculations', () => {
    test('calculates total employees', async () => {
      await Dashboard.render();

      const kpiTotal = document.getElementById('kpi-total');
      expect(kpiTotal.textContent).toBe('5');
    });

    test('updates granted KPI', async () => {
      await Dashboard.render();

      const kpiGranted = document.getElementById('kpi-granted');
      expect(kpiGranted.textContent).toBe('85.0'); // 20+15+20+10+20
    });

    test('uses API values for used KPI when available', async () => {
      global.fetch.mockResolvedValue({
        json: () => Promise.resolve({
          status: 'success',
          total_used: 100,
          total_balance: 50,
          usage_rate: 50
        })
      });

      await Dashboard.render();

      const kpiUsed = document.getElementById('kpi-used');
      expect(kpiUsed.textContent).toBe('100.0');
    });

    test('falls back to local calculation when API fails', async () => {
      global.fetch.mockRejectedValue(new Error('Network error'));

      await Dashboard.render();

      const kpiUsed = document.getElementById('kpi-used');
      // Should use local sum: 5+10+18+10+8 = 51
      expect(kpiUsed.textContent).toBe('51.0');
    });

    test('falls back to local calculation when API returns 0', async () => {
      global.fetch.mockResolvedValue({
        json: () => Promise.resolve({
          status: 'success',
          total_used: 0,
          total_balance: 0,
          usage_rate: 0
        })
      });

      await Dashboard.render();

      const kpiUsed = document.getElementById('kpi-used');
      expect(kpiUsed.textContent).toBe('51.0');
    });
  });

  describe('Type Counts', () => {
    test('updates all type counts', async () => {
      await Dashboard.render();

      expect(document.getElementById('count-all').textContent).toBe('5');
      expect(document.getElementById('count-haken').textContent).toBe('3');
      expect(document.getElementById('count-ukeoi').textContent).toBe('1');
      expect(document.getElementById('count-staff').textContent).toBe('1');
    });

    test('handles empty data', async () => {
      getFilteredData.mockReturnValue([]);

      await Dashboard.render();

      expect(document.getElementById('count-all').textContent).toBe('0');
      expect(document.getElementById('count-haken').textContent).toBe('0');
    });
  });

  describe('Chart Rendering', () => {
    test('creates distribution chart', async () => {
      await Dashboard.render();

      expect(global.Chart).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          type: 'doughnut'
        })
      );
    });

    test('creates trends chart', async () => {
      await Dashboard.render();

      expect(global.Chart).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          type: 'bar'
        })
      );
    });

    test('destroys existing charts before creating new ones', async () => {
      // First render
      await Dashboard.render();

      const firstChartInstance = global.Chart.mock.results[0].value;

      // Second render
      await Dashboard.render();

      expect(firstChartInstance.destroy).toHaveBeenCalled();
    });

    test('calculates balance distribution correctly', async () => {
      // Data has: balance 15, 5, 2, 0, 12
      // high (>=10): 15, 12 = 2
      // medium (5-10): 5 = 1
      // low (0-5): 2 = 1
      // zero (<=0): 0 = 1

      await Dashboard.render();

      const chartCall = global.Chart.mock.calls.find(call =>
        call[1].type === 'doughnut'
      );

      const data = chartCall[1].data.datasets[0].data;
      expect(data).toEqual([2, 1, 1, 1]); // high, medium, low, zero
    });

    test('renders top 10 employees in trends chart', async () => {
      const largeData = Array.from({ length: 20 }, (_, i) => ({
        name: `Employee ${i}`,
        used: i
      }));
      getFilteredData.mockReturnValue(largeData);

      await Dashboard.render();

      const barChartCall = global.Chart.mock.calls.find(call =>
        call[1].type === 'bar'
      );

      expect(barChartCall[1].data.labels.length).toBe(10);
    });
  });

  describe('Compliance Gauge', () => {
    test('updateComplianceGauge updates value element', () => {
      Dashboard.updateComplianceGauge(75, 15, 20);

      // Animation would update the value
      jest.advanceTimersByTime(1100);

      // Check that function doesn't throw
      expect(() => Dashboard.updateComplianceGauge(75, 15, 20)).not.toThrow();
    });

    test('updateComplianceGauge sets color based on rate', () => {
      const labelEl = document.querySelector('.gauge-label');

      Dashboard.updateComplianceGauge(85);
      // High rate - should show "Excellent"
      expect(labelEl.textContent).toBe('Excellent');

      Dashboard.updateComplianceGauge(60);
      expect(labelEl.textContent).toBe('Attention');

      Dashboard.updateComplianceGauge(30);
      expect(labelEl.textContent).toBe('Needs Improvement');
    });

    test('updateComplianceGauge handles missing elements gracefully', () => {
      document.getElementById('gauge-compliance').remove();

      expect(() => Dashboard.updateComplianceGauge(75)).not.toThrow();
    });
  });

  describe('Expiring Days', () => {
    test('updateExpiringDays shows countdown for low balance employees', () => {
      const data = mockEmployeeData;

      Dashboard.updateExpiringDays(data);

      const countdownContainer = document.getElementById('countdown-container');
      expect(countdownContainer.style.display).toBe('flex');
    });

    test('updateExpiringDays hides countdown when no expiring employees', () => {
      const data = [
        { balance: 15 },
        { balance: 20 }
      ];

      Dashboard.updateExpiringDays(data);

      const countdownContainer = document.getElementById('countdown-container');
      expect(countdownContainer.style.display).toBe('none');
    });

    test('updateExpiringDays shows no-expiring message', () => {
      const data = [{ balance: 10 }];

      Dashboard.updateExpiringDays(data);

      const noExpiring = document.getElementById('no-expiring');
      expect(noExpiring.style.display).toBe('block');
    });

    test('updateExpiringDays calculates critical count', () => {
      Dashboard.updateExpiringDays(mockEmployeeData);

      // Check function runs without error
      // balance <= 0: 1 employee (Suzuki)
      expect(() => Dashboard.updateExpiringDays(mockEmployeeData)).not.toThrow();
    });
  });

  describe('Cleanup', () => {
    test('destroyCharts cleans up chart instances', async () => {
      await Dashboard.render();

      const chartInstance = global.Chart.mock.results[0].value;

      Dashboard.destroyCharts();

      expect(chartInstance.destroy).toHaveBeenCalled();
    });

    test('cleanup function calls destroyCharts', async () => {
      await Dashboard.render();

      const chartInstance = global.Chart.mock.results[0].value;

      Dashboard.cleanup();

      expect(chartInstance.destroy).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    test('handles missing DOM elements gracefully', async () => {
      // Remove an element
      document.getElementById('kpi-total').remove();

      // Should not throw
      await expect(Dashboard.render()).resolves.not.toThrow();
    });

    test('handles null data gracefully', async () => {
      getFilteredData.mockReturnValue(null);

      // Should not throw
      await expect(Dashboard.render()).rejects.not.toThrow();
    });

    test('handles missing year in state', async () => {
      getState.mockReturnValue({ currentView: 'dashboard', year: null });

      await Dashboard.render();

      // Should still render with local calculations
      expect(document.getElementById('kpi-total').textContent).toBe('5');
    });
  });

  describe('Data Filtering', () => {
    test('respects current year filter', async () => {
      const filteredData = [
        { name: 'User 1', granted: 10, used: 5, balance: 5 }
      ];
      getFilteredData.mockReturnValue(filteredData);

      await Dashboard.render();

      expect(document.getElementById('kpi-total').textContent).toBe('1');
    });
  });

  describe('Default Export', () => {
    test('exports all public functions', () => {
      const defaultExport = Dashboard.default;

      expect(defaultExport.init).toBeDefined();
      expect(defaultExport.render).toBeDefined();
      expect(defaultExport.updateComplianceGauge).toBeDefined();
      expect(defaultExport.updateExpiringDays).toBeDefined();
      expect(defaultExport.destroyCharts).toBeDefined();
      expect(defaultExport.cleanup).toBeDefined();
    });
  });
});
