/**
 * DataTable Component - YuKyuDATA Design System
 * Accessible data table with sorting, pagination, and virtual scrolling
 *
 * @module components/Table
 * @version 1.0.0
 */

import { escapeHtml } from '../../js/modules/utils.js';

/**
 * Column definition
 * @typedef {Object} ColumnDef
 * @property {string} key - Data key
 * @property {string} label - Column header label (Japanese)
 * @property {boolean} [sortable=true] - Enable sorting
 * @property {string} [align='left'] - Text alignment: 'left' | 'center' | 'right'
 * @property {string} [width] - Column width (CSS value)
 * @property {Function} [render] - Custom render function (value, row, index) => string|HTMLElement
 * @property {Function} [compare] - Custom compare function for sorting
 * @property {boolean} [hidden=false] - Hide column
 */

/**
 * Table options
 * @typedef {Object} TableOptions
 * @property {ColumnDef[]} columns - Column definitions
 * @property {Array} [data=[]] - Table data
 * @property {boolean} [sortable=true] - Enable column sorting
 * @property {boolean} [paginated=true] - Enable pagination
 * @property {number} [pageSize=20] - Rows per page
 * @property {number[]} [pageSizeOptions=[10, 20, 50, 100]] - Page size options
 * @property {boolean} [selectable=false] - Enable row selection
 * @property {boolean} [striped=true] - Striped rows
 * @property {boolean} [hoverable=true] - Hover effect on rows
 * @property {boolean} [bordered=false] - Bordered table
 * @property {boolean} [loading=false] - Show loading state
 * @property {string} [emptyMessage='データがありません'] - Empty state message
 * @property {Function} [onRowClick] - Row click callback (row, index, event)
 * @property {Function} [onSort] - Sort callback (column, direction)
 * @property {Function} [onPageChange] - Page change callback (page)
 * @property {Function} [onSelectionChange] - Selection change callback (selectedRows)
 * @property {string} [ariaLabel='データテーブル'] - Table ARIA label
 */

/**
 * DataTable component class
 * @class
 */
export class DataTable {
  /**
   * Create a DataTable instance
   * @param {HTMLElement|string} container - Container element or selector
   * @param {TableOptions} options - Table configuration
   */
  constructor(container, options = {}) {
    this.container = typeof container === 'string'
      ? document.querySelector(container)
      : container;

    if (!this.container) {
      throw new Error('DataTable: Container element not found');
    }

    // Configuration
    this.columns = options.columns || [];
    this.originalData = options.data || [];
    this.data = [...this.originalData];
    this.sortable = options.sortable !== false;
    this.paginated = options.paginated !== false;
    this.pageSize = options.pageSize || 20;
    this.pageSizeOptions = options.pageSizeOptions || [10, 20, 50, 100];
    this.selectable = options.selectable || false;
    this.striped = options.striped !== false;
    this.hoverable = options.hoverable !== false;
    this.bordered = options.bordered || false;
    this.loading = options.loading || false;
    this.emptyMessage = options.emptyMessage || 'データがありません';
    this.ariaLabel = options.ariaLabel || 'データテーブル';

    // Callbacks
    this.onRowClick = options.onRowClick || null;
    this.onSort = options.onSort || null;
    this.onPageChange = options.onPageChange || null;
    this.onSelectionChange = options.onSelectionChange || null;

    // State
    this.currentPage = 1;
    this.sortColumn = null;
    this.sortDirection = null; // 'asc' | 'desc' | null
    this.selectedRows = new Set();

    // Element references
    this.tableElement = null;
    this.headerElement = null;
    this.bodyElement = null;
    this.paginationElement = null;

    // Initialize
    this._injectStyles();
    this.render();
  }

  /**
   * Inject table styles
   * @private
   */
  _injectStyles() {
    if (document.getElementById('datatable-component-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'datatable-component-styles';
    styles.textContent = `
      .data-table-container {
        background: var(--card-bg, rgba(15, 15, 15, 0.85));
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--radius-lg, 16px);
        overflow: hidden;
      }

      .data-table-wrapper {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
      }

      .data-table {
        width: 100%;
        border-collapse: collapse;
        font-size: var(--font-size-sm, 0.875rem);
      }

      .data-table th,
      .data-table td {
        padding: var(--table-cell-padding-y, 1rem) var(--table-cell-padding-x, 1rem);
        text-align: left;
        border-bottom: var(--table-border, 1px solid rgba(255, 255, 255, 0.05));
      }

      .data-table th {
        background: var(--table-header-bg, rgba(255, 255, 255, 0.02));
        font-weight: var(--font-weight-semibold, 600);
        color: var(--color-text-secondary, #94a3b8);
        font-size: var(--font-size-xs, 0.75rem);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        white-space: nowrap;
        user-select: none;
      }

      .data-table th.sortable {
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .data-table th.sortable:hover {
        background: rgba(255, 255, 255, 0.05);
        color: var(--color-text-primary, #f8fafc);
      }

      .data-table th.sortable:focus {
        outline: var(--focus-outline, 3px solid var(--color-primary));
        outline-offset: -3px;
      }

      .th-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .sort-icon {
        width: 16px;
        height: 16px;
        opacity: 0.3;
        transition: all 0.2s ease;
      }

      .data-table th.sorted .sort-icon {
        opacity: 1;
        color: var(--color-primary, #06b6d4);
      }

      .data-table th.sorted.desc .sort-icon {
        transform: rotate(180deg);
      }

      .data-table td {
        color: var(--color-text-primary, #f8fafc);
        vertical-align: middle;
      }

      .data-table.striped tbody tr:nth-child(even) {
        background: rgba(255, 255, 255, 0.02);
      }

      .data-table.hoverable tbody tr {
        transition: background 0.2s ease;
      }

      .data-table.hoverable tbody tr:hover {
        background: rgba(6, 182, 212, 0.05);
      }

      .data-table.bordered td,
      .data-table.bordered th {
        border: 1px solid rgba(255, 255, 255, 0.1);
      }

      .data-table tbody tr.selected {
        background: rgba(6, 182, 212, 0.1);
      }

      .data-table tbody tr.clickable {
        cursor: pointer;
      }

      .data-table .text-left { text-align: left; }
      .data-table .text-center { text-align: center; }
      .data-table .text-right { text-align: right; }

      /* Selection checkbox */
      .row-checkbox {
        width: 18px;
        height: 18px;
        cursor: pointer;
        accent-color: var(--color-primary, #06b6d4);
      }

      /* Empty state */
      .data-table-empty {
        padding: 3rem 2rem;
        text-align: center;
        color: var(--color-text-muted, #64748b);
      }

      .data-table-empty-icon {
        width: 48px;
        height: 48px;
        margin: 0 auto 1rem;
        opacity: 0.5;
      }

      /* Loading state */
      .data-table-loading {
        position: relative;
        pointer-events: none;
      }

      .data-table-loading::after {
        content: '';
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
      }

      .loading-spinner {
        width: 32px;
        height: 32px;
        border: 3px solid rgba(255, 255, 255, 0.1);
        border-top-color: var(--color-primary, #06b6d4);
        border-radius: 50%;
        animation: table-spin 0.8s linear infinite;
      }

      @keyframes table-spin {
        to { transform: rotate(360deg); }
      }

      /* Pagination */
      .data-table-pagination {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 1.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        gap: 1rem;
        flex-wrap: wrap;
      }

      .pagination-info {
        font-size: var(--font-size-sm, 0.875rem);
        color: var(--color-text-muted, #64748b);
      }

      .pagination-controls {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .pagination-btn {
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: var(--color-text-secondary, #94a3b8);
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .pagination-btn:hover:not(:disabled) {
        background: rgba(255, 255, 255, 0.1);
        color: var(--color-text-primary, #f8fafc);
      }

      .pagination-btn:disabled {
        opacity: 0.3;
        cursor: not-allowed;
      }

      .pagination-btn:focus {
        outline: var(--focus-outline, 3px solid var(--color-primary));
        outline-offset: 2px;
      }

      .pagination-pages {
        display: flex;
        align-items: center;
        gap: 0.25rem;
      }

      .pagination-page {
        min-width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        color: var(--color-text-secondary, #94a3b8);
        font-size: var(--font-size-sm, 0.875rem);
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .pagination-page:hover {
        background: rgba(255, 255, 255, 0.05);
        color: var(--color-text-primary, #f8fafc);
      }

      .pagination-page.active {
        background: var(--color-primary, #06b6d4);
        color: #000;
        font-weight: 600;
      }

      .pagination-page:focus {
        outline: var(--focus-outline, 3px solid var(--color-primary));
        outline-offset: 2px;
      }

      .page-size-select {
        padding: 0.5rem 2rem 0.5rem 0.75rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: var(--color-text-secondary, #94a3b8);
        font-size: var(--font-size-sm, 0.875rem);
        cursor: pointer;
        appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2306b6d4' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 0.75rem center;
      }

      .page-size-select:focus {
        outline: var(--focus-outline, 3px solid var(--color-primary));
        outline-offset: 2px;
        border-color: var(--color-primary, #06b6d4);
      }

      /* Light theme */
      [data-theme="light"] .data-table-container {
        background: rgba(255, 255, 255, 0.95);
        border-color: rgba(0, 0, 0, 0.1);
      }

      [data-theme="light"] .data-table th {
        background: rgba(0, 0, 0, 0.02);
        color: #64748b;
      }

      [data-theme="light"] .data-table td {
        color: #1e293b;
        border-color: rgba(0, 0, 0, 0.05);
      }

      [data-theme="light"] .data-table.striped tbody tr:nth-child(even) {
        background: rgba(0, 0, 0, 0.02);
      }

      [data-theme="light"] .data-table.hoverable tbody tr:hover {
        background: rgba(6, 182, 212, 0.05);
      }

      [data-theme="light"] .pagination-btn,
      [data-theme="light"] .page-size-select {
        background: rgba(0, 0, 0, 0.05);
        border-color: rgba(0, 0, 0, 0.1);
      }

      /* Responsive */
      @media (max-width: 768px) {
        .data-table th,
        .data-table td {
          padding: 0.75rem 0.5rem;
        }

        .data-table-pagination {
          flex-direction: column;
          gap: 0.75rem;
        }
      }
    `;
    document.head.appendChild(styles);
  }

  /**
   * Get sorted and paginated data
   * @private
   * @returns {Array} Processed data
   */
  _getProcessedData() {
    let result = [...this.data];

    // Sort
    if (this.sortColumn && this.sortDirection) {
      const column = this.columns.find(c => c.key === this.sortColumn);

      result.sort((a, b) => {
        let valA = a[this.sortColumn];
        let valB = b[this.sortColumn];

        // Custom compare function
        if (column && column.compare) {
          return this.sortDirection === 'asc'
            ? column.compare(valA, valB)
            : column.compare(valB, valA);
        }

        // Default comparison
        if (valA === null || valA === undefined) valA = '';
        if (valB === null || valB === undefined) valB = '';

        if (typeof valA === 'number' && typeof valB === 'number') {
          return this.sortDirection === 'asc' ? valA - valB : valB - valA;
        }

        const strA = String(valA).toLowerCase();
        const strB = String(valB).toLowerCase();
        const compared = strA.localeCompare(strB, 'ja');

        return this.sortDirection === 'asc' ? compared : -compared;
      });
    }

    // Paginate
    if (this.paginated) {
      const start = (this.currentPage - 1) * this.pageSize;
      result = result.slice(start, start + this.pageSize);
    }

    return result;
  }

  /**
   * Get total pages
   * @private
   * @returns {number} Total pages
   */
  _getTotalPages() {
    return Math.ceil(this.data.length / this.pageSize);
  }

  /**
   * Render table header
   * @private
   * @returns {string} Header HTML
   */
  _renderHeader() {
    const visibleColumns = this.columns.filter(c => !c.hidden);

    let headerHtml = '<tr role="row">';

    // Selection column
    if (this.selectable) {
      headerHtml += `
        <th scope="col" style="width: 50px;">
          <input type="checkbox" class="row-checkbox select-all"
                 aria-label="全て選択"
                 ${this.selectedRows.size === this.data.length && this.data.length > 0 ? 'checked' : ''}>
        </th>
      `;
    }

    visibleColumns.forEach(col => {
      const sortable = this.sortable && col.sortable !== false;
      const isSorted = this.sortColumn === col.key;
      const classes = [
        sortable ? 'sortable' : '',
        isSorted ? 'sorted' : '',
        isSorted && this.sortDirection === 'desc' ? 'desc' : '',
        col.align ? `text-${col.align}` : ''
      ].filter(Boolean).join(' ');

      const width = col.width ? `style="width: ${col.width}"` : '';
      const sortIcon = sortable ? `
        <svg class="sort-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12l7-7 7 7"/>
        </svg>
      ` : '';

      headerHtml += `
        <th scope="col"
            role="columnheader"
            class="${classes}"
            ${width}
            ${sortable ? `tabindex="0" aria-sort="${isSorted ? (this.sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}"` : ''}
            data-column="${col.key}">
          <div class="th-content">
            <span>${escapeHtml(col.label)}</span>
            ${sortIcon}
          </div>
        </th>
      `;
    });

    headerHtml += '</tr>';
    return headerHtml;
  }

  /**
   * Render table body
   * @private
   * @returns {string} Body HTML
   */
  _renderBody() {
    const processedData = this._getProcessedData();
    const visibleColumns = this.columns.filter(c => !c.hidden);

    if (processedData.length === 0) {
      const colSpan = visibleColumns.length + (this.selectable ? 1 : 0);
      return `
        <tr>
          <td colspan="${colSpan}">
            <div class="data-table-empty">
              <svg class="data-table-empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
              </svg>
              <p>${escapeHtml(this.emptyMessage)}</p>
            </div>
          </td>
        </tr>
      `;
    }

    return processedData.map((row, index) => {
      const actualIndex = (this.currentPage - 1) * this.pageSize + index;
      const isSelected = this.selectedRows.has(actualIndex);
      const rowClasses = [
        isSelected ? 'selected' : '',
        this.onRowClick ? 'clickable' : ''
      ].filter(Boolean).join(' ');

      let rowHtml = `<tr role="row" class="${rowClasses}" data-index="${actualIndex}">`;

      // Selection checkbox
      if (this.selectable) {
        rowHtml += `
          <td>
            <input type="checkbox" class="row-checkbox row-select"
                   data-index="${actualIndex}"
                   aria-label="行を選択"
                   ${isSelected ? 'checked' : ''}>
          </td>
        `;
      }

      visibleColumns.forEach(col => {
        const value = row[col.key];
        const align = col.align ? `text-${col.align}` : '';

        let cellContent;
        if (col.render) {
          const rendered = col.render(value, row, actualIndex);
          cellContent = typeof rendered === 'string' ? rendered : '';
          if (rendered instanceof HTMLElement) {
            cellContent = rendered.outerHTML;
          }
        } else {
          cellContent = value !== null && value !== undefined ? escapeHtml(String(value)) : '';
        }

        rowHtml += `<td class="${align}">${cellContent}</td>`;
      });

      rowHtml += '</tr>';
      return rowHtml;
    }).join('');
  }

  /**
   * Render pagination
   * @private
   * @returns {string} Pagination HTML
   */
  _renderPagination() {
    if (!this.paginated) return '';

    const totalPages = this._getTotalPages();
    const totalItems = this.data.length;
    const start = Math.min((this.currentPage - 1) * this.pageSize + 1, totalItems);
    const end = Math.min(this.currentPage * this.pageSize, totalItems);

    // Page buttons
    let pagesHtml = '';
    const maxVisiblePages = 5;
    let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    if (startPage > 1) {
      pagesHtml += `<button class="pagination-page" data-page="1">1</button>`;
      if (startPage > 2) {
        pagesHtml += `<span style="padding: 0 0.5rem; color: var(--color-text-muted);">...</span>`;
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      pagesHtml += `
        <button class="pagination-page ${i === this.currentPage ? 'active' : ''}"
                data-page="${i}"
                ${i === this.currentPage ? 'aria-current="page"' : ''}>
          ${i}
        </button>
      `;
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        pagesHtml += `<span style="padding: 0 0.5rem; color: var(--color-text-muted);">...</span>`;
      }
      pagesHtml += `<button class="pagination-page" data-page="${totalPages}">${totalPages}</button>`;
    }

    // Page size options
    const pageSizeOptionsHtml = this.pageSizeOptions.map(size =>
      `<option value="${size}" ${size === this.pageSize ? 'selected' : ''}>${size}件</option>`
    ).join('');

    return `
      <div class="data-table-pagination">
        <div class="pagination-info">
          ${totalItems}件中 ${start}-${end}件を表示
        </div>
        <div class="pagination-controls">
          <select class="page-size-select" aria-label="表示件数">
            ${pageSizeOptionsHtml}
          </select>
          <button class="pagination-btn" data-action="first" aria-label="最初のページ" ${this.currentPage === 1 ? 'disabled' : ''}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 17l-5-5 5-5M18 17l-5-5 5-5"/>
            </svg>
          </button>
          <button class="pagination-btn" data-action="prev" aria-label="前のページ" ${this.currentPage === 1 ? 'disabled' : ''}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 18l-6-6 6-6"/>
            </svg>
          </button>
          <div class="pagination-pages">
            ${pagesHtml}
          </div>
          <button class="pagination-btn" data-action="next" aria-label="次のページ" ${this.currentPage === totalPages || totalPages === 0 ? 'disabled' : ''}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </button>
          <button class="pagination-btn" data-action="last" aria-label="最後のページ" ${this.currentPage === totalPages || totalPages === 0 ? 'disabled' : ''}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 17l5-5-5-5M6 17l5-5-5-5"/>
            </svg>
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Render the complete table
   */
  render() {
    const tableClasses = [
      'data-table',
      this.striped ? 'striped' : '',
      this.hoverable ? 'hoverable' : '',
      this.bordered ? 'bordered' : ''
    ].filter(Boolean).join(' ');

    this.container.innerHTML = `
      <div class="data-table-container ${this.loading ? 'data-table-loading' : ''}">
        ${this.loading ? '<div class="loading-spinner"></div>' : ''}
        <div class="data-table-wrapper">
          <table class="${tableClasses}" role="grid" aria-label="${escapeHtml(this.ariaLabel)}">
            <thead>
              ${this._renderHeader()}
            </thead>
            <tbody>
              ${this._renderBody()}
            </tbody>
          </table>
        </div>
        ${this._renderPagination()}
      </div>
    `;

    // Bind events
    this._bindEvents();
  }

  /**
   * Bind event listeners
   * @private
   */
  _bindEvents() {
    // Sort headers
    const sortableHeaders = this.container.querySelectorAll('th.sortable');
    sortableHeaders.forEach(th => {
      th.addEventListener('click', () => this._handleSort(th.dataset.column));
      th.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this._handleSort(th.dataset.column);
        }
      });
    });

    // Row clicks
    if (this.onRowClick) {
      const rows = this.container.querySelectorAll('tbody tr[data-index]');
      rows.forEach(row => {
        row.addEventListener('click', (e) => {
          if (e.target.closest('.row-checkbox')) return;
          const index = parseInt(row.dataset.index, 10);
          this.onRowClick(this.data[index], index, e);
        });
      });
    }

    // Selection
    if (this.selectable) {
      const selectAll = this.container.querySelector('.select-all');
      if (selectAll) {
        selectAll.addEventListener('change', (e) => this._handleSelectAll(e.target.checked));
      }

      const rowCheckboxes = this.container.querySelectorAll('.row-select');
      rowCheckboxes.forEach(cb => {
        cb.addEventListener('change', (e) => {
          this._handleRowSelect(parseInt(cb.dataset.index, 10), e.target.checked);
        });
      });
    }

    // Pagination
    const paginationBtns = this.container.querySelectorAll('.pagination-btn');
    paginationBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        const totalPages = this._getTotalPages();

        switch (action) {
          case 'first': this.goToPage(1); break;
          case 'prev': this.goToPage(this.currentPage - 1); break;
          case 'next': this.goToPage(this.currentPage + 1); break;
          case 'last': this.goToPage(totalPages); break;
        }
      });
    });

    const pageButtons = this.container.querySelectorAll('.pagination-page');
    pageButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        this.goToPage(parseInt(btn.dataset.page, 10));
      });
    });

    const pageSizeSelect = this.container.querySelector('.page-size-select');
    if (pageSizeSelect) {
      pageSizeSelect.addEventListener('change', (e) => {
        this.pageSize = parseInt(e.target.value, 10);
        this.currentPage = 1;
        this.render();
      });
    }
  }

  /**
   * Handle column sort
   * @private
   * @param {string} column - Column key
   */
  _handleSort(column) {
    if (this.sortColumn === column) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = column;
      this.sortDirection = 'asc';
    }

    if (this.onSort) {
      this.onSort(column, this.sortDirection);
    }

    this.render();
  }

  /**
   * Handle select all
   * @private
   * @param {boolean} checked - Checked state
   */
  _handleSelectAll(checked) {
    if (checked) {
      this.data.forEach((_, index) => this.selectedRows.add(index));
    } else {
      this.selectedRows.clear();
    }

    if (this.onSelectionChange) {
      this.onSelectionChange(this.getSelectedRows());
    }

    this.render();
  }

  /**
   * Handle row selection
   * @private
   * @param {number} index - Row index
   * @param {boolean} checked - Checked state
   */
  _handleRowSelect(index, checked) {
    if (checked) {
      this.selectedRows.add(index);
    } else {
      this.selectedRows.delete(index);
    }

    if (this.onSelectionChange) {
      this.onSelectionChange(this.getSelectedRows());
    }

    this.render();
  }

  // Public API

  /**
   * Set table data
   * @param {Array} data - New data array
   * @returns {DataTable} Instance for chaining
   */
  setData(data) {
    this.originalData = data;
    this.data = [...data];
    this.currentPage = 1;
    this.selectedRows.clear();
    this.render();
    return this;
  }

  /**
   * Filter data
   * @param {Function} predicate - Filter function (row) => boolean
   * @returns {DataTable} Instance for chaining
   */
  filter(predicate) {
    this.data = this.originalData.filter(predicate);
    this.currentPage = 1;
    this.render();
    return this;
  }

  /**
   * Reset filters
   * @returns {DataTable} Instance for chaining
   */
  resetFilter() {
    this.data = [...this.originalData];
    this.currentPage = 1;
    this.render();
    return this;
  }

  /**
   * Sort by column
   * @param {string} column - Column key
   * @param {string} [direction='asc'] - Sort direction
   * @returns {DataTable} Instance for chaining
   */
  sort(column, direction = 'asc') {
    this.sortColumn = column;
    this.sortDirection = direction;
    this.render();
    return this;
  }

  /**
   * Go to specific page
   * @param {number} page - Page number
   * @returns {DataTable} Instance for chaining
   */
  goToPage(page) {
    const totalPages = this._getTotalPages();
    this.currentPage = Math.max(1, Math.min(page, totalPages));

    if (this.onPageChange) {
      this.onPageChange(this.currentPage);
    }

    this.render();
    return this;
  }

  /**
   * Set loading state
   * @param {boolean} loading - Loading state
   * @returns {DataTable} Instance for chaining
   */
  setLoading(loading) {
    this.loading = loading;
    this.render();
    return this;
  }

  /**
   * Get selected rows data
   * @returns {Array} Selected rows
   */
  getSelectedRows() {
    return Array.from(this.selectedRows).map(index => this.data[index]);
  }

  /**
   * Clear selection
   * @returns {DataTable} Instance for chaining
   */
  clearSelection() {
    this.selectedRows.clear();
    this.render();
    return this;
  }

  /**
   * Refresh table (re-render)
   * @returns {DataTable} Instance for chaining
   */
  refresh() {
    this.render();
    return this;
  }

  /**
   * Destroy table instance
   */
  destroy() {
    this.container.innerHTML = '';
  }
}

export default DataTable;
