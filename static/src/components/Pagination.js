/**
 * Pagination Component - YuKyuDATA Design System
 * Accessible pagination controls
 *
 * @module components/Pagination
 * @version 1.0.0
 */

/**
 * Pagination options
 * @typedef {Object} PaginationOptions
 * @property {number} total - Total items
 * @property {number} [current=1] - Current page
 * @property {number} [pageSize=20] - Items per page
 * @property {number[]} [pageSizeOptions=[10,20,50,100]] - Page size options
 * @property {boolean} [showInfo=true] - Show items info
 * @property {boolean} [showPageSize=true] - Show page size selector
 * @property {boolean} [showJumper=false] - Show page jumper input
 * @property {number} [maxVisible=5] - Maximum visible page buttons
 * @property {Function} [onChange] - Page change callback (page, pageSize)
 * @property {string} [className=''] - Additional CSS classes
 */

/**
 * Create a pagination component
 * @param {HTMLElement|string} container - Container element or selector
 * @param {PaginationOptions} options - Pagination configuration
 * @returns {Object} Pagination controller
 */
export function Pagination(container, options = {}) {
  const element = typeof container === 'string'
    ? document.querySelector(container)
    : container;

  if (!element) {
    throw new Error('Pagination: Container element not found');
  }

  // Configuration
  let total = options.total || 0;
  let current = options.current || 1;
  let pageSize = options.pageSize || 20;
  const pageSizeOptions = options.pageSizeOptions || [10, 20, 50, 100];
  const showInfo = options.showInfo !== false;
  const showPageSize = options.showPageSize !== false;
  const showJumper = options.showJumper || false;
  const maxVisible = options.maxVisible || 5;
  const className = options.className || '';

  // Callbacks
  const onChange = options.onChange || null;

  // Inject styles
  injectPaginationStyles();

  /**
   * Get total pages
   * @returns {number} Total pages
   */
  function getTotalPages() {
    return Math.ceil(total / pageSize);
  }

  /**
   * Generate page numbers to display
   * @returns {Array} Page numbers and ellipsis
   */
  function getPageNumbers() {
    const totalPages = getTotalPages();
    const pages = [];

    if (totalPages <= maxVisible + 2) {
      // Show all pages
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      const halfVisible = Math.floor(maxVisible / 2);
      let start = Math.max(2, current - halfVisible);
      let end = Math.min(totalPages - 1, current + halfVisible);

      // Adjust range
      if (current - halfVisible < 2) {
        end = Math.min(totalPages - 1, maxVisible);
      }
      if (current + halfVisible > totalPages - 1) {
        start = Math.max(2, totalPages - maxVisible + 1);
      }

      // Add ellipsis before
      if (start > 2) {
        pages.push('...');
      }

      // Add visible pages
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      // Add ellipsis after
      if (end < totalPages - 1) {
        pages.push('...');
      }

      // Always show last page
      pages.push(totalPages);
    }

    return pages;
  }

  /**
   * Render pagination
   */
  function render() {
    const totalPages = getTotalPages();
    const start = Math.min((current - 1) * pageSize + 1, total);
    const end = Math.min(current * pageSize, total);

    element.className = `pagination ${className}`.trim();
    element.setAttribute('role', 'navigation');
    element.setAttribute('aria-label', 'ページネーション');

    let html = '';

    // Info
    if (showInfo) {
      html += `
        <div class="pagination-info">
          <span>${total.toLocaleString()}件中 ${start.toLocaleString()}-${end.toLocaleString()}件を表示</span>
        </div>
      `;
    }

    // Controls
    html += '<div class="pagination-controls">';

    // Page size selector
    if (showPageSize) {
      html += `
        <div class="pagination-size">
          <select class="pagination-size-select" aria-label="表示件数">
            ${pageSizeOptions.map(size =>
              `<option value="${size}" ${size === pageSize ? 'selected' : ''}>${size}件</option>`
            ).join('')}
          </select>
        </div>
      `;
    }

    // Navigation buttons
    html += '<div class="pagination-nav">';

    // First button
    html += `
      <button type="button" class="pagination-btn" data-action="first"
              aria-label="最初のページ" ${current === 1 ? 'disabled' : ''}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="11 17 6 12 11 7"/><polyline points="18 17 13 12 18 7"/>
        </svg>
      </button>
    `;

    // Previous button
    html += `
      <button type="button" class="pagination-btn" data-action="prev"
              aria-label="前のページ" ${current === 1 ? 'disabled' : ''}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>
    `;

    // Page numbers
    html += '<div class="pagination-pages">';
    const pageNumbers = getPageNumbers();
    pageNumbers.forEach(page => {
      if (page === '...') {
        html += '<span class="pagination-ellipsis">...</span>';
      } else {
        html += `
          <button type="button" class="pagination-page ${page === current ? 'is-active' : ''}"
                  data-page="${page}" ${page === current ? 'aria-current="page"' : ''}>
            ${page}
          </button>
        `;
      }
    });
    html += '</div>';

    // Next button
    html += `
      <button type="button" class="pagination-btn" data-action="next"
              aria-label="次のページ" ${current === totalPages || totalPages === 0 ? 'disabled' : ''}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    `;

    // Last button
    html += `
      <button type="button" class="pagination-btn" data-action="last"
              aria-label="最後のページ" ${current === totalPages || totalPages === 0 ? 'disabled' : ''}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/>
        </svg>
      </button>
    `;

    html += '</div>';

    // Page jumper
    if (showJumper && totalPages > 1) {
      html += `
        <div class="pagination-jumper">
          <input type="number" class="pagination-jumper-input" min="1" max="${totalPages}"
                 placeholder="ページ" aria-label="ページへ移動">
          <button type="button" class="pagination-jumper-btn">移動</button>
        </div>
      `;
    }

    html += '</div>';

    element.innerHTML = html;
    bindEvents();
  }

  /**
   * Bind event listeners
   */
  function bindEvents() {
    // Navigation buttons
    element.querySelectorAll('.pagination-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        const totalPages = getTotalPages();

        switch (action) {
          case 'first': goToPage(1); break;
          case 'prev': goToPage(current - 1); break;
          case 'next': goToPage(current + 1); break;
          case 'last': goToPage(totalPages); break;
        }
      });
    });

    // Page number buttons
    element.querySelectorAll('.pagination-page').forEach(btn => {
      btn.addEventListener('click', () => {
        goToPage(parseInt(btn.dataset.page, 10));
      });
    });

    // Page size selector
    const sizeSelect = element.querySelector('.pagination-size-select');
    if (sizeSelect) {
      sizeSelect.addEventListener('change', (e) => {
        pageSize = parseInt(e.target.value, 10);
        current = 1;
        render();
        if (onChange) onChange(current, pageSize);
      });
    }

    // Page jumper
    const jumperInput = element.querySelector('.pagination-jumper-input');
    const jumperBtn = element.querySelector('.pagination-jumper-btn');
    if (jumperInput && jumperBtn) {
      const jump = () => {
        const page = parseInt(jumperInput.value, 10);
        if (!isNaN(page)) {
          goToPage(page);
          jumperInput.value = '';
        }
      };

      jumperBtn.addEventListener('click', jump);
      jumperInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') jump();
      });
    }
  }

  /**
   * Go to specific page
   * @param {number} page - Page number
   */
  function goToPage(page) {
    const totalPages = getTotalPages();
    const newPage = Math.max(1, Math.min(page, totalPages));

    if (newPage !== current) {
      current = newPage;
      render();
      if (onChange) onChange(current, pageSize);
    }
  }

  // Initial render
  render();

  // Return controller
  return {
    goToPage,
    getCurrentPage: () => current,
    getPageSize: () => pageSize,
    getTotalPages,
    setTotal: (newTotal) => {
      total = newTotal;
      const totalPages = getTotalPages();
      if (current > totalPages) current = Math.max(1, totalPages);
      render();
    },
    setPageSize: (newPageSize) => {
      pageSize = newPageSize;
      current = 1;
      render();
    },
    refresh: render,
    destroy: () => { element.innerHTML = ''; }
  };
}

/**
 * Inject pagination styles
 * @private
 */
function injectPaginationStyles() {
  if (document.getElementById('pagination-component-styles')) return;

  const styles = document.createElement('style');
  styles.id = 'pagination-component-styles';
  styles.textContent = `
    .pagination {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      flex-wrap: wrap;
      padding: 1rem 0;
    }

    .pagination-info {
      font-size: var(--font-size-sm, 0.875rem);
      color: var(--color-text-muted, #64748b);
    }

    .pagination-controls {
      display: flex;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .pagination-nav {
      display: flex;
      align-items: center;
      gap: 0.25rem;
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

    .pagination-btn:focus-visible {
      outline: var(--focus-outline, 3px solid var(--color-primary));
      outline-offset: 2px;
    }

    .pagination-btn:disabled {
      opacity: 0.3;
      cursor: not-allowed;
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
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      padding: 0 0.5rem;
    }

    .pagination-page:hover:not(.is-active) {
      background: rgba(255, 255, 255, 0.05);
      color: var(--color-text-primary, #f8fafc);
    }

    .pagination-page.is-active {
      background: linear-gradient(135deg, var(--color-primary, #06b6d4), var(--color-secondary, #0891b2));
      color: #000;
      font-weight: 600;
    }

    .pagination-page:focus-visible {
      outline: var(--focus-outline, 3px solid var(--color-primary));
      outline-offset: 2px;
    }

    .pagination-ellipsis {
      padding: 0 0.5rem;
      color: var(--color-text-muted, #64748b);
    }

    .pagination-size {
      display: flex;
      align-items: center;
    }

    .pagination-size-select {
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

    .pagination-size-select:focus-visible {
      outline: var(--focus-outline, 3px solid var(--color-primary));
      outline-offset: 2px;
      border-color: var(--color-primary, #06b6d4);
    }

    .pagination-jumper {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .pagination-jumper-input {
      width: 70px;
      padding: 0.5rem 0.75rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      color: var(--color-text-primary, #f8fafc);
      font-size: var(--font-size-sm, 0.875rem);
      text-align: center;
    }

    .pagination-jumper-input:focus-visible {
      outline: none;
      border-color: var(--color-primary, #06b6d4);
    }

    .pagination-jumper-input::-webkit-inner-spin-button,
    .pagination-jumper-input::-webkit-outer-spin-button {
      -webkit-appearance: none;
      margin: 0;
    }

    .pagination-jumper-btn {
      padding: 0.5rem 1rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      color: var(--color-text-secondary, #94a3b8);
      font-size: var(--font-size-sm, 0.875rem);
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .pagination-jumper-btn:hover {
      background: rgba(255, 255, 255, 0.1);
      color: var(--color-text-primary, #f8fafc);
    }

    .pagination-jumper-btn:focus-visible {
      outline: var(--focus-outline, 3px solid var(--color-primary));
      outline-offset: 2px;
    }

    /* Light theme */
    [data-theme="light"] .pagination-btn,
    [data-theme="light"] .pagination-size-select,
    [data-theme="light"] .pagination-jumper-input,
    [data-theme="light"] .pagination-jumper-btn {
      background: rgba(0, 0, 0, 0.05);
      border-color: rgba(0, 0, 0, 0.1);
      color: #64748b;
    }

    [data-theme="light"] .pagination-btn:hover:not(:disabled),
    [data-theme="light"] .pagination-page:hover:not(.is-active),
    [data-theme="light"] .pagination-jumper-btn:hover {
      background: rgba(0, 0, 0, 0.1);
      color: #1e293b;
    }

    [data-theme="light"] .pagination-jumper-input {
      color: #1e293b;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .pagination {
        flex-direction: column;
        gap: 0.75rem;
      }

      .pagination-controls {
        width: 100%;
        justify-content: center;
      }

      .pagination-info {
        width: 100%;
        text-align: center;
      }

      .pagination-jumper {
        display: none;
      }
    }

    @media (max-width: 480px) {
      .pagination-nav {
        gap: 0.125rem;
      }

      .pagination-btn,
      .pagination-page {
        width: 32px;
        height: 32px;
        min-width: 32px;
      }

      .pagination-size {
        display: none;
      }
    }
  `;
  document.head.appendChild(styles);
}

export default Pagination;
