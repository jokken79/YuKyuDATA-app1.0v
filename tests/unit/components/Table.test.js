/**
 * Tests for DataTable Component
 * YuKyuDATA Design System
 */

const { JSDOM } = require('jsdom');

// Setup DOM environment before imports
const dom = new JSDOM('<!DOCTYPE html><html><head></head><body><div id="table-container"></div></body></html>', {
  url: 'http://localhost'
});
global.document = dom.window.document;
global.window = dom.window;
global.HTMLElement = dom.window.HTMLElement;

// Mock escapeHtml
jest.mock('../../../static/js/modules/utils.js', () => ({
  escapeHtml: (str) => {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
}));

// Import after mocks
const { DataTable } = require('../../../static/src/components/Table.js');

describe('DataTable Component', () => {
  let container;
  let testColumns;
  let testData;

  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = '<div id="table-container"></div>';
    container = document.getElementById('table-container');

    // Reset test data
    testColumns = [
      { key: 'id', label: 'ID', sortable: true },
      { key: 'name', label: '名前', sortable: true },
      { key: 'email', label: 'メール', sortable: false },
      { key: 'balance', label: '残高', sortable: true, align: 'right' }
    ];

    testData = [
      { id: 1, name: '田中太郎', email: 'tanaka@example.com', balance: 10.5 },
      { id: 2, name: '山田花子', email: 'yamada@example.com', balance: 5.0 },
      { id: 3, name: '佐藤次郎', email: 'sato@example.com', balance: 15.0 },
      { id: 4, name: '鈴木三郎', email: 'suzuki@example.com', balance: 20.0 },
      { id: 5, name: '高橋四郎', email: 'takahashi@example.com', balance: 0 }
    ];
  });

  describe('Constructor', () => {
    test('creates table with default options', () => {
      const table = new DataTable(container, { columns: testColumns });

      expect(table.sortable).toBe(true);
      expect(table.paginated).toBe(true);
      expect(table.pageSize).toBe(20);
      expect(table.striped).toBe(true);
      expect(table.hoverable).toBe(true);
      expect(table.selectable).toBe(false);
    });

    test('creates table with custom options', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        sortable: false,
        paginated: false,
        pageSize: 10,
        selectable: true,
        striped: false
      });

      expect(table.sortable).toBe(false);
      expect(table.paginated).toBe(false);
      expect(table.pageSize).toBe(10);
      expect(table.selectable).toBe(true);
      expect(table.striped).toBe(false);
    });

    test('accepts string selector for container', () => {
      const table = new DataTable('#table-container', { columns: testColumns });

      expect(table.container).toBe(container);
    });

    test('throws error when container not found', () => {
      expect(() => {
        new DataTable('#nonexistent', { columns: testColumns });
      }).toThrow('DataTable: Container element not found');
    });

    test('renders table immediately', () => {
      new DataTable(container, { columns: testColumns, data: testData });

      expect(container.querySelector('table')).toBeTruthy();
    });
  });

  describe('Rendering', () => {
    test('renders table header with columns', () => {
      new DataTable(container, { columns: testColumns });

      const headers = container.querySelectorAll('th');
      expect(headers.length).toBe(testColumns.length);
      expect(headers[1].textContent).toContain('名前');
    });

    test('renders table body with data', () => {
      new DataTable(container, { columns: testColumns, data: testData });

      const rows = container.querySelectorAll('tbody tr');
      expect(rows.length).toBe(testData.length);
    });

    test('renders empty state when no data', () => {
      new DataTable(container, { columns: testColumns, data: [] });

      const emptyState = container.querySelector('.data-table-empty');
      expect(emptyState).toBeTruthy();
      expect(emptyState.textContent).toContain('データがありません');
    });

    test('renders custom empty message', () => {
      new DataTable(container, {
        columns: testColumns,
        data: [],
        emptyMessage: 'カスタム空メッセージ'
      });

      const emptyState = container.querySelector('.data-table-empty');
      expect(emptyState.textContent).toContain('カスタム空メッセージ');
    });

    test('applies striped class when striped option is true', () => {
      new DataTable(container, {
        columns: testColumns,
        data: testData,
        striped: true
      });

      const table = container.querySelector('table');
      expect(table.classList.contains('striped')).toBe(true);
    });

    test('applies hoverable class when hoverable option is true', () => {
      new DataTable(container, {
        columns: testColumns,
        data: testData,
        hoverable: true
      });

      const table = container.querySelector('table');
      expect(table.classList.contains('hoverable')).toBe(true);
    });

    test('applies bordered class when bordered option is true', () => {
      new DataTable(container, {
        columns: testColumns,
        data: testData,
        bordered: true
      });

      const table = container.querySelector('table');
      expect(table.classList.contains('bordered')).toBe(true);
    });

    test('hides columns with hidden: true', () => {
      const columns = [
        { key: 'id', label: 'ID', hidden: true },
        { key: 'name', label: '名前' }
      ];

      new DataTable(container, { columns, data: testData });

      const headers = container.querySelectorAll('th');
      expect(headers.length).toBe(1);
      expect(headers[0].textContent).toContain('名前');
    });

    test('applies custom column width', () => {
      const columns = [
        { key: 'id', label: 'ID', width: '100px' },
        { key: 'name', label: '名前' }
      ];

      new DataTable(container, { columns, data: testData });

      const firstHeader = container.querySelector('th');
      expect(firstHeader.getAttribute('style')).toContain('width: 100px');
    });

    test('applies column alignment', () => {
      new DataTable(container, { columns: testColumns, data: testData });

      const balanceCells = container.querySelectorAll('td.text-right');
      expect(balanceCells.length).toBeGreaterThan(0);
    });

    test('uses custom render function', () => {
      const columns = [
        { key: 'name', label: '名前' },
        {
          key: 'balance',
          label: '残高',
          render: (value) => `${value.toFixed(2)} days`
        }
      ];

      new DataTable(container, { columns, data: testData });

      const cells = container.querySelectorAll('tbody td');
      const balanceCell = cells[1];
      expect(balanceCell.textContent).toContain('10.50 days');
    });
  });

  describe('ARIA Accessibility', () => {
    test('table has role="grid"', () => {
      new DataTable(container, { columns: testColumns });

      const table = container.querySelector('table');
      expect(table.getAttribute('role')).toBe('grid');
    });

    test('table has aria-label', () => {
      new DataTable(container, {
        columns: testColumns,
        ariaLabel: 'Employee data table'
      });

      const table = container.querySelector('table');
      expect(table.getAttribute('aria-label')).toBe('Employee data table');
    });

    test('header cells have scope="col"', () => {
      new DataTable(container, { columns: testColumns });

      const headers = container.querySelectorAll('th');
      headers.forEach(th => {
        expect(th.getAttribute('scope')).toBe('col');
      });
    });

    test('header cells have role="columnheader"', () => {
      new DataTable(container, { columns: testColumns });

      const headers = container.querySelectorAll('th');
      headers.forEach(th => {
        expect(th.getAttribute('role')).toBe('columnheader');
      });
    });

    test('sortable headers have aria-sort attribute', () => {
      const table = new DataTable(container, { columns: testColumns, data: testData });

      // Sort by name
      table.sort('name', 'asc');

      const nameHeader = container.querySelector('th[data-column="name"]');
      expect(nameHeader.getAttribute('aria-sort')).toBe('ascending');
    });

    test('sortable headers have tabindex for keyboard access', () => {
      new DataTable(container, { columns: testColumns });

      const sortableHeader = container.querySelector('th.sortable');
      expect(sortableHeader.getAttribute('tabindex')).toBe('0');
    });

    test('rows have role="row"', () => {
      new DataTable(container, { columns: testColumns, data: testData });

      const rows = container.querySelectorAll('tr');
      rows.forEach(row => {
        expect(row.getAttribute('role')).toBe('row');
      });
    });
  });

  describe('Sorting', () => {
    test('sorts data ascending', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData
      });

      table.sort('name', 'asc');

      const firstRow = container.querySelector('tbody tr:first-child');
      expect(firstRow.textContent).toContain('高橋四郎'); // First in Japanese alphabetical order
    });

    test('sorts data descending', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData
      });

      table.sort('balance', 'desc');

      const firstRow = container.querySelector('tbody tr:first-child');
      expect(firstRow.textContent).toContain('鈴木三郎'); // 20.0 balance
    });

    test('toggles sort direction on click', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData
      });

      const nameHeader = container.querySelector('th[data-column="name"]');

      // First click - ascending
      nameHeader.click();
      expect(table.sortDirection).toBe('asc');

      // Second click - descending
      nameHeader.click();
      expect(table.sortDirection).toBe('desc');
    });

    test('calls onSort callback', () => {
      const onSort = jest.fn();
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData,
        onSort
      });

      table.sort('name', 'asc');

      expect(onSort).toHaveBeenCalledWith('name', 'asc');
    });

    test('handles numeric sorting correctly', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData
      });

      table.sort('balance', 'asc');

      const rows = container.querySelectorAll('tbody tr');
      const firstBalance = rows[0].textContent;
      const lastBalance = rows[rows.length - 1].textContent;

      expect(firstBalance).toContain('0');
      expect(lastBalance).toContain('20');
    });

    test('uses custom compare function', () => {
      const columns = [
        {
          key: 'name',
          label: '名前',
          compare: (a, b) => a.length - b.length
        }
      ];

      const table = new DataTable(container, { columns, data: testData });
      table.sort('name', 'asc');

      // Should sort by name length
      expect(table.sortColumn).toBe('name');
    });

    test('handles null values in sorting', () => {
      const dataWithNulls = [
        { id: 1, name: null },
        { id: 2, name: '田中' },
        { id: 3, name: '山田' }
      ];

      const columns = [{ key: 'name', label: '名前' }];
      const table = new DataTable(container, { columns, data: dataWithNulls });

      // Should not throw
      expect(() => table.sort('name', 'asc')).not.toThrow();
    });
  });

  describe('Pagination', () => {
    test('paginates data', () => {
      const largeData = Array.from({ length: 50 }, (_, i) => ({
        id: i + 1,
        name: `User ${i + 1}`
      }));

      const columns = [{ key: 'id', label: 'ID' }, { key: 'name', label: 'Name' }];

      new DataTable(container, {
        columns,
        data: largeData,
        pageSize: 10
      });

      const rows = container.querySelectorAll('tbody tr');
      expect(rows.length).toBe(10);
    });

    test('shows pagination controls', () => {
      const largeData = Array.from({ length: 50 }, (_, i) => ({
        id: i + 1,
        name: `User ${i + 1}`
      }));

      const columns = [{ key: 'id', label: 'ID' }];

      new DataTable(container, {
        columns,
        data: largeData,
        pageSize: 10,
        paginated: true
      });

      const pagination = container.querySelector('.data-table-pagination');
      expect(pagination).toBeTruthy();
    });

    test('navigates to specific page', () => {
      const largeData = Array.from({ length: 50 }, (_, i) => ({
        id: i + 1,
        name: `User ${i + 1}`
      }));

      const columns = [{ key: 'id', label: 'ID' }];

      const table = new DataTable(container, {
        columns,
        data: largeData,
        pageSize: 10
      });

      table.goToPage(3);

      expect(table.currentPage).toBe(3);
      const firstRow = container.querySelector('tbody tr');
      expect(firstRow.textContent).toContain('21'); // Third page starts at 21
    });

    test('calls onPageChange callback', () => {
      const onPageChange = jest.fn();
      const largeData = Array.from({ length: 50 }, (_, i) => ({ id: i + 1 }));
      const columns = [{ key: 'id', label: 'ID' }];

      const table = new DataTable(container, {
        columns,
        data: largeData,
        pageSize: 10,
        onPageChange
      });

      table.goToPage(2);

      expect(onPageChange).toHaveBeenCalledWith(2);
    });

    test('displays pagination info', () => {
      const largeData = Array.from({ length: 50 }, (_, i) => ({ id: i + 1 }));
      const columns = [{ key: 'id', label: 'ID' }];

      new DataTable(container, {
        columns,
        data: largeData,
        pageSize: 10
      });

      const info = container.querySelector('.pagination-info');
      expect(info.textContent).toContain('50');
      expect(info.textContent).toContain('1-10');
    });

    test('hides pagination when paginated is false', () => {
      new DataTable(container, {
        columns: testColumns,
        data: testData,
        paginated: false
      });

      const pagination = container.querySelector('.data-table-pagination');
      expect(pagination).toBeFalsy();
    });

    test('clamps page number to valid range', () => {
      const largeData = Array.from({ length: 50 }, (_, i) => ({ id: i + 1 }));
      const columns = [{ key: 'id', label: 'ID' }];

      const table = new DataTable(container, {
        columns,
        data: largeData,
        pageSize: 10
      });

      table.goToPage(100); // Way beyond total pages
      expect(table.currentPage).toBe(5); // Should clamp to last page

      table.goToPage(-1);
      expect(table.currentPage).toBe(1); // Should clamp to first page
    });
  });

  describe('Selection', () => {
    test('renders selection checkboxes when selectable', () => {
      new DataTable(container, {
        columns: testColumns,
        data: testData,
        selectable: true
      });

      const checkboxes = container.querySelectorAll('.row-checkbox');
      expect(checkboxes.length).toBe(testData.length + 1); // Data rows + header
    });

    test('selects row on checkbox click', () => {
      const onSelectionChange = jest.fn();
      new DataTable(container, {
        columns: testColumns,
        data: testData,
        selectable: true,
        onSelectionChange
      });

      const checkbox = container.querySelector('.row-select');
      checkbox.checked = true;
      checkbox.dispatchEvent(new dom.window.Event('change'));

      expect(onSelectionChange).toHaveBeenCalled();
    });

    test('select all checkbox selects all rows', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData,
        selectable: true
      });

      const selectAll = container.querySelector('.select-all');
      selectAll.checked = true;
      selectAll.dispatchEvent(new dom.window.Event('change'));

      expect(table.getSelectedRows().length).toBe(testData.length);
    });

    test('getSelectedRows returns selected data', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData,
        selectable: true
      });

      const selectAll = container.querySelector('.select-all');
      selectAll.checked = true;
      selectAll.dispatchEvent(new dom.window.Event('change'));

      const selectedRows = table.getSelectedRows();
      expect(selectedRows.length).toBe(testData.length);
      expect(selectedRows[0].name).toBe('田中太郎');
    });

    test('clearSelection clears all selections', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData,
        selectable: true
      });

      const selectAll = container.querySelector('.select-all');
      selectAll.checked = true;
      selectAll.dispatchEvent(new dom.window.Event('change'));

      table.clearSelection();

      expect(table.getSelectedRows().length).toBe(0);
    });
  });

  describe('Row Click', () => {
    test('calls onRowClick callback', () => {
      const onRowClick = jest.fn();
      new DataTable(container, {
        columns: testColumns,
        data: testData,
        onRowClick
      });

      const row = container.querySelector('tbody tr');
      row.click();

      expect(onRowClick).toHaveBeenCalledWith(
        testData[0],
        0,
        expect.any(Object)
      );
    });

    test('adds clickable class to rows when onRowClick set', () => {
      new DataTable(container, {
        columns: testColumns,
        data: testData,
        onRowClick: jest.fn()
      });

      const row = container.querySelector('tbody tr');
      expect(row.classList.contains('clickable')).toBe(true);
    });
  });

  describe('Data Management', () => {
    test('setData updates table data', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData
      });

      const newData = [{ id: 100, name: 'New User', email: 'new@example.com', balance: 99 }];
      table.setData(newData);

      const rows = container.querySelectorAll('tbody tr');
      expect(rows.length).toBe(1);
      expect(rows[0].textContent).toContain('New User');
    });

    test('filter filters data by predicate', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData
      });

      table.filter(row => row.balance >= 10);

      const rows = container.querySelectorAll('tbody tr');
      expect(rows.length).toBe(3); // 10.5, 15, 20
    });

    test('resetFilter restores original data', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData
      });

      table.filter(row => row.balance >= 10);
      table.resetFilter();

      const rows = container.querySelectorAll('tbody tr');
      expect(rows.length).toBe(testData.length);
    });

    test('setData resets to page 1', () => {
      const largeData = Array.from({ length: 50 }, (_, i) => ({ id: i + 1 }));
      const columns = [{ key: 'id', label: 'ID' }];

      const table = new DataTable(container, {
        columns,
        data: largeData,
        pageSize: 10
      });

      table.goToPage(3);
      table.setData([{ id: 999 }]);

      expect(table.currentPage).toBe(1);
    });
  });

  describe('Loading State', () => {
    test('setLoading shows loading indicator', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData
      });

      table.setLoading(true);

      const loadingContainer = container.querySelector('.data-table-loading');
      expect(loadingContainer).toBeTruthy();
    });

    test('setLoading false hides loading indicator', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData,
        loading: true
      });

      table.setLoading(false);

      const loadingContainer = container.querySelector('.data-table-loading');
      expect(loadingContainer).toBeFalsy();
    });
  });

  describe('destroy()', () => {
    test('clears container content', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData
      });

      table.destroy();

      expect(container.innerHTML).toBe('');
    });
  });

  describe('refresh()', () => {
    test('re-renders table', () => {
      const table = new DataTable(container, {
        columns: testColumns,
        data: testData
      });

      // Modify data directly
      table.data[0].name = 'Modified Name';
      table.refresh();

      const firstRow = container.querySelector('tbody tr');
      expect(firstRow.textContent).toContain('Modified Name');
    });
  });
});
