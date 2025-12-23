import { ChartManager, Visualizations } from '../../static/js/modules/chart-manager.js';

describe('ChartManager', () => {
    let originalFetch;
    let state;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="chart-distribution"></div>
            <div id="chart-trends"></div>
            <div id="chart-factories"></div>
            <canvas id="chart-types"></canvas>
            <canvas id="chart-top10"></canvas>
        `;

        state = { charts: {} };

        global.ApexCharts = class {
            constructor(element, options) {
                this.element = element;
                this.options = options;
                this.render = jest.fn();
                this.destroy = jest.fn();
            }
        };

        global.Chart = class {
            constructor(ctx, config) {
                this.ctx = ctx;
                this.config = config;
                this.destroy = jest.fn();
            }
        };

        originalFetch = global.fetch;
        global.fetch = jest.fn();
    });

    afterEach(() => {
        global.fetch = originalFetch;
    });

    it('renders charts and handles fetches', async () => {
        const manager = new ChartManager(state, '/api');

        manager.renderDistribution([
            { usageRate: 10 },
            { usageRate: 40 },
            { usageRate: 60 },
            { usageRate: 90 }
        ]);

        global.fetch
            .mockResolvedValueOnce({
                json: async () => ({ data: [{ month: 1, total_days: 2 }] })
            })
            .mockResolvedValueOnce({
                json: async () => ({
                    data: {
                        hakenshain: { total_used: 3 },
                        ukeoi: { total_used: 2 },
                        staff: { total_used: 1 }
                    }
                })
            })
            .mockRejectedValueOnce(new Error('top10 error'));

        await manager.renderTrends(2024);
        await manager.renderTypes(2024);
        await manager.renderTop10(2024, [
            { name: 'A', used: 3 },
            { name: 'B', used: 1 }
        ]);
        manager.renderFactoryChart([
            ['Factory A', 3.5],
            ['Factory B', 2.0]
        ]);

        const distOptions = state.charts.distribution.options;
        expect(distOptions.plotOptions.pie.donut.labels.total.formatter()).toBe(4);
        expect(distOptions.tooltip.y.formatter(5)).toBe('5 employees');

        const trendsOptions = state.charts.trends.options;
        expect(trendsOptions.yaxis.labels.formatter(2.4)).toBe(2);
        expect(trendsOptions.tooltip.y.formatter(1.23)).toBe('1.2 days');

        const factoriesOptions = state.charts.factories.options;
        expect(factoriesOptions.dataLabels.formatter(1.23)).toBe('1.2');
        expect(factoriesOptions.tooltip.y.formatter(2.34)).toBe('2.3 days');

        expect(state.charts.distribution).toBeTruthy();
        expect(state.charts.trends).toBeTruthy();
        expect(state.charts.types).toBeTruthy();
        expect(state.charts.top10).toBeTruthy();
        expect(state.charts.factories).toBeTruthy();

        manager.destroy('distribution');
        expect(state.charts.distribution.destroy).toHaveBeenCalled();
    });

    it('handles missing containers and alternate data paths', async () => {
        document.body.innerHTML = '';
        const manager = new ChartManager(state, '/api');

        manager.renderDistribution([{ usageRate: 10 }]);
        manager.renderFactoryChart([['Factory', 1]]);

        document.body.innerHTML = `
            <div id="chart-trends"></div>
            <canvas id="chart-types"></canvas>
            <canvas id="chart-top10"></canvas>
        `;

        global.fetch
            .mockRejectedValueOnce(new Error('trends error'))
            .mockResolvedValueOnce({
                json: async () => ({
                    breakdown: {
                        hakenshain: { total_used: 4 },
                        ukeoi: { total_used: 3 },
                        staff: { total_used: 2 }
                    }
                })
            })
            .mockResolvedValueOnce({
                json: async () => ({ status: 'success', data: [{ name: 'X', used: 2 }] })
            });

        await manager.renderTrends(2024);
        await manager.renderTypes(2024);
        await manager.renderTop10(2024, []);
    });

    it('skips trend fetch when year is missing and ignores invalid months', async () => {
        document.body.innerHTML = '<div id="chart-trends"></div>';
        const manager = new ChartManager(state, '/api');

        global.fetch.mockResolvedValueOnce({
            json: async () => ({
                data: [
                    { month: 0, total_days: 2 },
                    { month: 5, total_days: 3 }
                ]
            })
        });

        await manager.renderTrends(2024);
        const callsBefore = global.fetch.mock.calls.length;
        await manager.renderTrends(null);
        expect(global.fetch.mock.calls.length).toBe(callsBefore);
    });

    it('handles top10 non-success responses', async () => {
        document.body.innerHTML = '<canvas id="chart-top10"></canvas>';
        const manager = new ChartManager(state, '/api');

        global.fetch.mockResolvedValueOnce({
            json: async () => ({ status: 'error' })
        });

        await manager.renderTop10(2024, []);
        expect(state.charts.top10).toBeTruthy();
    });

    it('handles type fetch errors', async () => {
        const manager = new ChartManager(state, '/api');
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

        global.fetch.mockRejectedValueOnce(new Error('type error'));
        await manager.renderTypes(2024);

        expect(errorSpy).toHaveBeenCalled();
        errorSpy.mockRestore();
    });
});

describe('Visualizations', () => {
    let originalRAF;

    beforeEach(() => {
        document.body.innerHTML = `
            <svg><circle id="ring"></circle></svg>
            <span id="value"></span>
            <svg><path id="gauge-compliance"></path></svg>
            <span id="gauge-value"></span>
            <span class="gauge-label"></span>
            <span id="compliance-count"></span>
            <span id="compliance-total"></span>
            <div id="countdown-container"></div>
            <div id="no-expiring"></div>
            <span id="expiring-days"></span>
            <span id="expiring-detail"></span>
            <span id="critical-count"></span>
            <span id="warning-count"></span>
            <span id="healthy-count"></span>
            <span id="quick-haken"></span>
            <span id="quick-ukeoi"></span>
            <span id="quick-staff"></span>
        `;

        originalRAF = global.requestAnimationFrame;
        global.requestAnimationFrame = (cb) => cb(performance.now() + 10000);
    });

    afterEach(() => {
        global.requestAnimationFrame = originalRAF;
    });

    it('updates UI animations and counters', () => {
        jest.useFakeTimers();
        const viz = new Visualizations();

        viz.animateRing('ring', 'value', 5, 10, 50);
        viz.updateGauge(85, 8, 10);
        viz.updateExpiringDays([
            { balance: 0 },
            { balance: 1.5 },
            { balance: 4 },
            { balance: 6 }
        ]);
        viz.updateQuickStats(3, 2, 5);

        jest.runAllTimers();

        expect(document.getElementById('ring').style.strokeDasharray).not.toBe('');
        expect(document.getElementById('value').textContent).not.toBe('');
        expect(document.getElementById('gauge-value').textContent).toContain('%');
        expect(document.getElementById('expiring-days').textContent).toContain('days');
        expect(document.getElementById('quick-haken').textContent).not.toBe('');

        viz.showConfetti();
        expect(document.querySelectorAll('.confetti').length).toBe(50);
        jest.runAllTimers();
        expect(document.querySelectorAll('.confetti').length).toBe(0);

        jest.useRealTimers();
    });

    it('covers alternate visualization branches', () => {
        const viz = new Visualizations();
        const valueEl = document.getElementById('value');
        const originalRAF = global.requestAnimationFrame;
        let rafCalls = 0;
        global.requestAnimationFrame = (cb) => {
            rafCalls += 1;
            const time = rafCalls === 1 ? performance.now() : performance.now() + 10000;
            cb(time);
        };

        viz.animateRing('missing-ring', 'missing-value', 1, 1, 100);
        viz.animateNumber(valueEl, 0, 1.5, 100);
        viz.updateGauge(60, 6, 10);
        viz.updateGauge(20, 2, 10);

        viz.updateExpiringDays([]);

        expect(document.getElementById('no-expiring').style.display).toBe('block');
        expect(rafCalls).toBeGreaterThan(1);
        global.requestAnimationFrame = originalRAF;
    });

    it('handles missing visualization elements safely', () => {
        const viz = new Visualizations();

        document.body.innerHTML = '';
        viz.updateGauge(50, 1, 2);

        document.body.innerHTML = '<svg><path id="gauge-compliance"></path></svg>';
        viz.updateGauge(60, 1, 2);

        document.body.innerHTML = '<div></div>';
        viz.updateExpiringDays([{ balance: 2 }]);
        viz.updateQuickStats(1, 2, 3);

        document.body.innerHTML = '<svg><circle id="ring"></circle></svg>';
        viz.animateRing('ring', 'missing-value', 1, 1, 50);
    });
});
