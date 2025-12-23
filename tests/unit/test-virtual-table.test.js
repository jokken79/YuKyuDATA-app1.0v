import { VirtualTable, createVirtualTable } from '../../static/js/modules/virtual-table.js';

describe('VirtualTable', () => {
    let container;
    let table;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="table-container">
                <table class="data-table">
                    <thead><tr><th>Name</th></tr></thead>
                    <tbody id="table-body"></tbody>
                </table>
            </div>
        `;
        container = document.getElementById('table-container');
        table = container.querySelector('table');
        table.scrollTo = jest.fn();
    });

    it('creates virtual structure and renders rows', () => {
        const onRowClick = jest.fn();
        const vt = new VirtualTable(container, { rowHeight: 20, visibleRows: 2, bufferRows: 1, onRowClick });

        vt.setData(
            [{ name: 'A' }, { name: 'B' }, { name: 'C' }],
            (item) => `<td>${item.name}</td>`
        );

        expect(vt.totalItems).toBe(3);
        expect(vt.visibleItems.length).toBeGreaterThan(0);

        vt.refresh();
        vt.refresh();

        const firstRow = vt.virtualTbody.querySelector('tr');
        firstRow.dispatchEvent(new Event('click'));
        expect(onRowClick).toHaveBeenCalled();
    });

    it('filters and updates items', () => {
        const vt = new VirtualTable(container, { rowHeight: 20, visibleRows: 2, bufferRows: 1 });
        vt.setData(
            [{ name: 'A' }, { name: 'B' }],
            (item) => `<td>${item.name}</td>`
        );

        vt.filter(item => item.name === 'B');
        expect(vt.totalItems).toBe(1);

        const shared = vt.data[1];
        vt.updateItem(1, shared);
        expect(vt.data[1].name).toBe('B');

        vt.updateItem(99, { name: 'X' });
    });

    it('scrolls and destroys cleanly', () => {
        const vt = new VirtualTable(container, { rowHeight: 20, visibleRows: 2, bufferRows: 1 });
        vt.setData(
            [{ name: 'A' }, { name: 'B' }, { name: 'C' }],
            (item) => `<td>${item.name}</td>`
        );

        vt.scrollContainer.scrollTo = jest.fn();
        vt.scrollToIndex(2, false);
        expect(vt.scrollContainer.scrollTo).toHaveBeenCalled();

        vt.virtualTbody.children[0].getBoundingClientRect = () => ({ height: 80 });
        vt._updateRowHeight();

        vt.scrollTimeout = setTimeout(() => {}, 10);
        vt.destroy();
        expect(container.querySelector('table')).toBeTruthy();
    });

    it('renders empty table state', () => {
        const vt = new VirtualTable(container, { rowHeight: 20, visibleRows: 2, bufferRows: 1 });
        vt.refresh();
        expect(vt.virtualTbody.textContent).toContain('No hay datos');
    });

    it('handles scroll events', () => {
        jest.useFakeTimers();
        const clearSpy = jest.spyOn(global, 'clearTimeout');
        const vt = new VirtualTable(container, { rowHeight: 20, visibleRows: 2, bufferRows: 1 });
        vt.setData(
            [{ name: 'A' }, { name: 'B' }, { name: 'C' }],
            (item) => `<td>${item.name}</td>`
        );
        vt.scrollContainer.scrollTop = 40;
        vt.scrollContainer.dispatchEvent(new Event('scroll'));
        vt.scrollContainer.dispatchEvent(new Event('scroll'));
        expect(clearSpy).toHaveBeenCalled();
        jest.runAllTimers();
        expect(vt.isScrolling).toBe(false);
        clearSpy.mockRestore();
        jest.useRealTimers();
    });

    it('uses ResizeObserver when available', () => {
        const originalResizeObserver = window.ResizeObserver;
        const observe = jest.fn();
        const disconnect = jest.fn();
        let resizeCallback;
        window.ResizeObserver = jest.fn((cb) => {
            resizeCallback = cb;
            return { observe, disconnect };
        });

        const vt = new VirtualTable(container, { rowHeight: 20, visibleRows: 2, bufferRows: 1 });
        const updateSpy = jest.spyOn(vt, '_updateRowHeight');
        expect(observe).toHaveBeenCalled();

        resizeCallback();
        expect(updateSpy).toHaveBeenCalled();

        vt.destroy();
        expect(disconnect).toHaveBeenCalled();
        updateSpy.mockRestore();
        window.ResizeObserver = originalResizeObserver;
    });
});

describe('createVirtualTable', () => {
    it('creates virtual table for selector', () => {
        document.body.innerHTML = `
            <div id="virtual">
                <table><tbody></tbody></table>
            </div>
        `;
        const vt = createVirtualTable('#virtual', { rowHeight: 10 });
        expect(vt).toBeTruthy();
    });

    it('throws on missing container', () => {
        expect(() => createVirtualTable('#missing')).toThrow('Container not found');
    });
});
