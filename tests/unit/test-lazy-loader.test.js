import {
    LazyChartLoader,
    LazyComponentLoader,
    LazyModuleLoader,
    createLazyChartLoader,
    createLazyModuleLoader,
    lazyLoadImages
} from '../../static/js/modules/lazy-loader.js';
import path from 'path';
import { pathToFileURL } from 'url';

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0));

class MockIntersectionObserver {
    constructor(callback) {
        this.callback = callback;
        this.elements = new Set();
    }

    observe(element) {
        this.elements.add(element);
    }

    unobserve(element) {
        this.elements.delete(element);
    }

    disconnect() {
        this.elements.clear();
    }

    trigger(isIntersecting = true, target = null) {
        const entries = target
            ? [{ isIntersecting, target }]
            : Array.from(this.elements).map(el => ({ isIntersecting, target: el }));
        this.callback(entries, this);
    }
}

describe('lazyLoadImages', () => {
    let originalObserver;
    let originalImage;

    beforeEach(() => {
        originalObserver = global.IntersectionObserver;
        originalImage = global.Image;
        global.IntersectionObserver = MockIntersectionObserver;
    });

    afterEach(() => {
        global.IntersectionObserver = originalObserver;
        global.Image = originalImage;
    });

    it('loads images when visible', () => {
        document.body.innerHTML = '<img id="img" data-src="image.png">';
        global.Image = class {
            set src(value) {
                this._src = value;
                if (this.onload) this.onload();
            }
        };
        const observer = lazyLoadImages('img[data-src]');
        observer.trigger(true, document.getElementById('img'));

        const img = document.getElementById('img');
        expect(img.src).toContain('image.png');
        expect(img.dataset.src).toBeUndefined();
        expect(img.classList.contains('lazy-loaded')).toBe(true);
    });

    it('handles image load errors', () => {
        document.body.innerHTML = '<img id="img" data-src="bad.png">';
        global.Image = class {
            set src(value) {
                this._src = value;
                if (this.onerror) this.onerror();
            }
        };
        const observer = lazyLoadImages('img[data-src]');
        observer.trigger(true, document.getElementById('img'));

        const img = document.getElementById('img');
        expect(img.classList.contains('lazy-error')).toBe(true);
    });

    it('skips images without src', () => {
        document.body.innerHTML = '<img id="img" data-src="">';
        global.Image = class {
            set src(value) {
                this._src = value;
                if (this.onload) this.onload();
            }
        };
        const observer = lazyLoadImages('img[data-src]');
        observer.trigger(true, document.getElementById('img'));
        expect(document.getElementById('img').classList.contains('lazy-loaded')).toBe(false);
    });
});

describe('LazyChartLoader', () => {
    let originalObserver;

    beforeEach(() => {
        originalObserver = global.IntersectionObserver;
        global.IntersectionObserver = MockIntersectionObserver;
        document.body.innerHTML = '<div id="chart"></div>';
        window.ApexCharts = undefined;
        window.Chart = undefined;
    });

    afterEach(() => {
        global.IntersectionObserver = originalObserver;
    });

    it('registers and renders charts', async () => {
        const loader = new LazyChartLoader({ chartLibrary: 'apexcharts' });
        const renderFn = jest.fn().mockResolvedValue({ destroy: jest.fn() });
        const container = document.getElementById('chart');
        window.ApexCharts = function MockApex() {};

        loader.registerChart('chart-1', container, renderFn);
        loader.observer.trigger(true, container);
        await flushPromises();

        expect(container.classList.contains('lazy-chart-loaded')).toBe(true);
        expect(loader.getChart('chart-1')).toBeTruthy();
    });

    it('handles chart render errors', async () => {
        const loader = new LazyChartLoader({ chartLibrary: 'chartjs' });
        const renderFn = jest.fn().mockRejectedValue(new Error('fail'));
        const container = document.getElementById('chart');
        window.Chart = function MockChart() {};

        loader.registerChart('chart-err', container, renderFn);
        loader.observer.trigger(true, container);
        await flushPromises();

        expect(container.classList.contains('lazy-chart-error')).toBe(true);
    });

    it('handles missing containers and force renders', async () => {
        const loader = new LazyChartLoader({ chartLibrary: 'apexcharts' });
        const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
        loader.registerChart('missing', '#does-not-exist', jest.fn());
        expect(warnSpy).toHaveBeenCalled();

        const container = document.getElementById('chart');
        window.ApexCharts = function MockApex() {};
        const renderFn = jest.fn().mockResolvedValue({ destroy: jest.fn() });

        loader.registerChart('force', container, renderFn);
        loader.forceRender('force');
        await flushPromises();

        expect(container.classList.contains('lazy-chart-loaded')).toBe(true);
        expect(loader.getChart('missing')).toBeNull();
    });

    it('destroys rendered charts', async () => {
        const loader = new LazyChartLoader({ chartLibrary: 'apexcharts' });
        const container = document.getElementById('chart');
        window.ApexCharts = function MockApex() {};
        const destroy = jest.fn();

        loader.registerChart('chart-destroy', container, jest.fn().mockResolvedValue({ destroy }));
        loader.observer.trigger(true, container);
        await flushPromises();

        loader.destroy();
        expect(destroy).toHaveBeenCalled();
    });

    it('loads missing libraries during render', async () => {
        const apexLoader = new LazyChartLoader({ chartLibrary: 'apexcharts' });
        const apexContainer = document.getElementById('chart');
        const apexLoad = jest.spyOn(apexLoader, '_loadApexCharts').mockResolvedValue(undefined);
        apexLoader.registerChart('chart-load-apex', apexContainer, jest.fn().mockResolvedValue({}));
        apexLoader.observer.trigger(true, apexContainer);
        await flushPromises();
        expect(apexLoad).toHaveBeenCalled();

        const chartLoader = new LazyChartLoader({ chartLibrary: 'chartjs' });
        const chartContainer = document.getElementById('chart');
        const chartLoad = jest.spyOn(chartLoader, '_loadChartJS').mockResolvedValue(undefined);
        chartLoader.registerChart('chart-load-js', chartContainer, jest.fn().mockResolvedValue({}));
        chartLoader.observer.trigger(true, chartContainer);
        await flushPromises();
        expect(chartLoad).toHaveBeenCalled();
    });

    it('skips rendering when already rendered', async () => {
        const loader = new LazyChartLoader({ chartLibrary: 'apexcharts' });
        const container = document.getElementById('chart');
        loader.charts.set('chart-skip', {
            element: container,
            renderFn: jest.fn(),
            rendered: true,
            instance: null
        });

        await loader._renderChart('chart-skip', container);
        expect(container.classList.contains('lazy-chart-loading')).toBe(false);
    });

    it('loads chart libraries dynamically', async () => {
        const loader = createLazyChartLoader({ chartLibrary: 'apexcharts' });
        const originalAppend = document.head.appendChild;
        document.head.appendChild = (node) => {
            if (node.onload) node.onload();
            return node;
        };

        await loader._loadApexCharts();
        await loader._loadChartJS();

        window.ApexCharts = function MockApex() {};
        window.Chart = function MockChart() {};
        await loader._loadApexCharts();
        await loader._loadChartJS();

        document.head.appendChild = originalAppend;
    });
});

describe('LazyModuleLoader', () => {
    it('loads and caches modules', async () => {
        const loader = new LazyModuleLoader();
        const modulePath = pathToFileURL(path.join(process.cwd(), 'tests/fixtures/dummy-module.cjs')).href;

        const mod = await loader.loadModule('dummy', modulePath);
        expect(mod.default.value).toBe(123);
        expect(loader.isLoaded('dummy')).toBe(true);

        const cached = await loader.loadModule('dummy', modulePath);
        expect(cached).toBe(mod);
        expect(loader.getModule('missing')).toBeNull();
    });

    it('waits for in-flight modules and preloads', async () => {
        const loader = new LazyModuleLoader();
        const modulePath = pathToFileURL(path.join(process.cwd(), 'tests/fixtures/dummy-module.cjs')).href;

        const first = loader.loadModule('dummy', modulePath);
        const second = loader.loadModule('dummy', modulePath);
        const results = await Promise.all([first, second]);

        expect(results[0]).toBe(results[1]);

        await loader.preloadModules([
            { id: 'dummy', path: modulePath },
            { id: 'bad', path: 'file:///bad/module.js' }
        ]);
    });
});

describe('LazyComponentLoader', () => {
    let originalObserver;

    beforeEach(() => {
        originalObserver = global.IntersectionObserver;
        global.IntersectionObserver = MockIntersectionObserver;
        document.body.innerHTML = '<div id="component"></div>';
    });

    afterEach(() => {
        global.IntersectionObserver = originalObserver;
    });

    it('loads components on intersection', async () => {
        const loader = new LazyComponentLoader();
        const container = document.getElementById('component');
        const loaderFn = jest.fn().mockResolvedValue(undefined);

        loader.registerComponent('comp-1', container, loaderFn);
        loader.observer.trigger(true, container);
        await Promise.resolve();

        expect(container.classList.contains('lazy-component-loaded')).toBe(true);
        loader.destroy();
    });

    it('handles missing and failing components', async () => {
        const loader = new LazyComponentLoader();
        const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
        loader.registerComponent('missing', '#none', jest.fn());
        expect(warnSpy).toHaveBeenCalled();

        const container = document.getElementById('component');
        const failing = jest.fn().mockRejectedValue(new Error('fail'));
        await loader._loadComponent('missing', container);
        await loader._loadComponent('missing', container);

        loader.registerComponent('bad', container, failing);
        await loader._loadComponent('bad', container);
        expect(container.classList.contains('lazy-component-error')).toBe(true);
    });
});

describe('factory helpers', () => {
    it('creates lazy loaders', () => {
        const chartLoader = createLazyChartLoader();
        const moduleLoader = createLazyModuleLoader();
        expect(chartLoader).toBeTruthy();
        expect(moduleLoader).toBeTruthy();
    });
});
