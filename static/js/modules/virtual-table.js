/**
 * Virtual Table Module - Optimización de performance para tablas grandes
 * Implementa scroll virtual para renderizar solo filas visibles
 * @module virtual-table
 */

/**
 * Clase VirtualTable - Maneja virtualización de tablas grandes
 */
export class VirtualTable {
    /**
     * @param {HTMLElement} container - Contenedor de la tabla
     * @param {Object} options - Opciones de configuración
     */
    constructor(container, options = {}) {
        this.container = container;
        this.tbody = container.querySelector('tbody');
        this.thead = container.querySelector('thead');

        // Configuración
        this.options = {
            rowHeight: options.rowHeight || 60,           // Altura de cada fila en px
            visibleRows: options.visibleRows || 20,       // Filas visibles simultáneamente
            bufferRows: options.bufferRows || 10,         // Filas adicionales como buffer
            threshold: options.threshold || 0.5,          // Threshold para IntersectionObserver
            onRowClick: options.onRowClick || null,       // Callback al hacer click en fila
            ...options
        };

        // Estado
        this.data = [];
        this.filteredData = [];
        this.startIndex = 0;
        this.endIndex = 0;
        this.scrollTop = 0;
        this.isScrolling = false;
        this.scrollTimeout = null;
        this.renderColumns = null;

        // Elementos virtuales
        this.scrollContainer = null;
        this.viewportContainer = null;
        this.topSpacer = null;
        this.bottomSpacer = null;

        // Inicializar
        this._init();
    }

    /**
     * Inicializa la estructura de la tabla virtual
     * @private
     */
    _init() {
        // Guardar tabla original como referencia
        this.originalTable = this.container.querySelector('table').cloneNode(true);

        // Crear estructura de scroll virtual
        this._createVirtualStructure();

        // Configurar event listeners
        this._setupEventListeners();
    }

    /**
     * Crea la estructura HTML para el scroll virtual
     * @private
     */
    _createVirtualStructure() {
        const table = this.container.querySelector('table');

        // Crear contenedor de scroll
        this.scrollContainer = document.createElement('div');
        this.scrollContainer.className = 'virtual-scroll-container';
        this.scrollContainer.style.cssText = `
            position: relative;
            overflow-y: auto;
            overflow-x: hidden;
            max-height: ${this.options.visibleRows * this.options.rowHeight}px;
            -webkit-overflow-scrolling: touch;
        `;

        // Crear spacers para simular altura total
        this.topSpacer = document.createElement('div');
        this.topSpacer.style.cssText = 'height: 0px; pointer-events: none;';

        this.bottomSpacer = document.createElement('div');
        this.bottomSpacer.style.cssText = 'height: 0px; pointer-events: none;';

        // Crear viewport para filas visibles
        this.viewportContainer = document.createElement('div');
        this.viewportContainer.className = 'virtual-viewport';

        // Reorganizar estructura
        const parent = this.container;
        parent.innerHTML = '';

        // Agregar header fijo si existe
        if (this.thead) {
            const headerWrapper = document.createElement('div');
            headerWrapper.className = 'virtual-header-wrapper';
            headerWrapper.style.cssText = `
                position: sticky;
                top: 0;
                z-index: 10;
                background: var(--bg-card);
            `;
            const headerTable = document.createElement('table');
            headerTable.className = table.className;
            headerTable.appendChild(this.thead.cloneNode(true));
            headerWrapper.appendChild(headerTable);
            parent.appendChild(headerWrapper);
        }

        // Agregar contenedor de scroll
        this.scrollContainer.appendChild(this.topSpacer);
        this.scrollContainer.appendChild(this.viewportContainer);
        this.scrollContainer.appendChild(this.bottomSpacer);
        parent.appendChild(this.scrollContainer);

        // Crear tabla dentro del viewport
        this.virtualTable = document.createElement('table');
        this.virtualTable.className = table.className;
        this.virtualTbody = document.createElement('tbody');
        this.virtualTbody.id = this.tbody?.id || '';
        this.virtualTable.appendChild(this.virtualTbody);
        this.viewportContainer.appendChild(this.virtualTable);
    }

    /**
     * Configura event listeners
     * @private
     */
    _setupEventListeners() {
        // Scroll con debounce para mejor performance
        this.scrollContainer.addEventListener('scroll', () => {
            this.scrollTop = this.scrollContainer.scrollTop;

            if (!this.isScrolling) {
                this.isScrolling = true;
                this.scrollContainer.classList.add('is-scrolling');
            }

            // Cancelar timeout previo
            if (this.scrollTimeout) {
                clearTimeout(this.scrollTimeout);
            }

            // Render inmediato para scroll suave
            this._renderVisibleRows();

            // Marcar fin de scroll después de 150ms
            this.scrollTimeout = setTimeout(() => {
                this.isScrolling = false;
                this.scrollContainer.classList.remove('is-scrolling');
            }, 150);
        }, { passive: true });

        // Resize observer para ajustar altura de filas
        if (window.ResizeObserver) {
            this.resizeObserver = new ResizeObserver(() => {
                this._updateRowHeight();
            });
            this.resizeObserver.observe(this.virtualTable);
        }
    }

    /**
     * Actualiza la altura real de las filas
     * @private
     */
    _updateRowHeight() {
        if (this.virtualTbody.children.length > 0) {
            const firstRow = this.virtualTbody.children[0];
            const actualHeight = firstRow.getBoundingClientRect().height;
            if (actualHeight > 0 && Math.abs(actualHeight - this.options.rowHeight) > 5) {
                this.options.rowHeight = actualHeight;
                this._updateSpacers();
            }
        }
    }

    /**
     * Establece los datos de la tabla
     * @param {Array} data - Array de objetos con datos
     * @param {Function} renderColumns - Función para renderizar columnas
     */
    setData(data, renderColumns) {
        this.data = data;
        this.filteredData = [...data];
        this.renderColumns = renderColumns;
        this._updateSpacers();
        this._renderVisibleRows();
    }

    /**
     * Filtra los datos
     * @param {Function} filterFn - Función de filtro
     */
    filter(filterFn) {
        this.filteredData = this.data.filter(filterFn);
        this.scrollTop = 0;
        this.scrollContainer.scrollTop = 0;
        this._updateSpacers();
        this._renderVisibleRows();
    }

    /**
     * Actualiza los spacers según los datos
     * @private
     */
    _updateSpacers() {
        const totalHeight = this.filteredData.length * this.options.rowHeight;
        this.scrollContainer.style.height = `${Math.min(
            totalHeight,
            this.options.visibleRows * this.options.rowHeight
        )}px`;
    }

    /**
     * Renderiza solo las filas visibles
     * @private
     */
    _renderVisibleRows() {
        if (!this.renderColumns || this.filteredData.length === 0) {
            this.virtualTbody.innerHTML = '<tr><td colspan="100" class="text-center p-xl">No hay datos disponibles</td></tr>';
            this.topSpacer.style.height = '0px';
            this.bottomSpacer.style.height = '0px';
            return;
        }

        // Calcular índices visibles
        const scrollTop = this.scrollTop;
        const startIndex = Math.max(0, Math.floor(scrollTop / this.options.rowHeight) - this.options.bufferRows);
        const endIndex = Math.min(
            this.filteredData.length,
            Math.ceil((scrollTop + this.scrollContainer.clientHeight) / this.options.rowHeight) + this.options.bufferRows
        );

        // Solo re-renderizar si los índices cambiaron significativamente
        if (startIndex === this.startIndex && endIndex === this.endIndex) {
            return;
        }

        this.startIndex = startIndex;
        this.endIndex = endIndex;

        // Actualizar spacers
        this.topSpacer.style.height = `${startIndex * this.options.rowHeight}px`;
        this.bottomSpacer.style.height = `${(this.filteredData.length - endIndex) * this.options.rowHeight}px`;

        // Renderizar filas visibles
        const fragment = document.createDocumentFragment();
        for (let i = startIndex; i < endIndex; i++) {
            const item = this.filteredData[i];
            const tr = document.createElement('tr');
            tr.style.height = `${this.options.rowHeight}px`;
            tr.dataset.index = i;

            // Aplicar función de renderizado de columnas
            tr.innerHTML = this.renderColumns(item, i);

            // Event listener para click
            if (this.options.onRowClick) {
                tr.style.cursor = 'pointer';
                tr.addEventListener('click', () => {
                    this.options.onRowClick(item, i, tr);
                });
            }

            fragment.appendChild(tr);
        }

        // Limpiar y agregar nuevas filas
        this.virtualTbody.innerHTML = '';
        this.virtualTbody.appendChild(fragment);
    }

    /**
     * Refresca la tabla con los datos actuales
     */
    refresh() {
        this._renderVisibleRows();
    }

    /**
     * Actualiza un item específico
     * @param {number} index - Índice del item
     * @param {Object} newData - Nuevos datos
     */
    updateItem(index, newData) {
        if (index >= 0 && index < this.data.length) {
            this.data[index] = newData;
            // Actualizar también en filteredData si existe
            const filteredIndex = this.filteredData.findIndex((item, i) =>
                this.data.indexOf(item) === index
            );
            if (filteredIndex >= 0) {
                this.filteredData[filteredIndex] = newData;
            }
            this._renderVisibleRows();
        }
    }

    /**
     * Scroll a un índice específico
     * @param {number} index - Índice de la fila
     * @param {boolean} smooth - Si debe hacer scroll suave
     */
    scrollToIndex(index, smooth = true) {
        const targetScroll = index * this.options.rowHeight;
        this.scrollContainer.scrollTo({
            top: targetScroll,
            behavior: smooth ? 'smooth' : 'auto'
        });
    }

    /**
     * Destruye la instancia y limpia recursos
     */
    destroy() {
        if (this.scrollTimeout) {
            clearTimeout(this.scrollTimeout);
        }
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        this.scrollContainer?.removeEventListener('scroll', this._handleScroll);
        this.container.innerHTML = '';
        this.container.appendChild(this.originalTable);
    }

    /**
     * Obtiene el total de items
     * @returns {number}
     */
    get totalItems() {
        return this.filteredData.length;
    }

    /**
     * Obtiene las filas visibles actualmente
     * @returns {Array}
     */
    get visibleItems() {
        return this.filteredData.slice(this.startIndex, this.endIndex);
    }
}

/**
 * Helper function para crear una tabla virtual rápidamente
 * @param {string} selector - Selector CSS del contenedor
 * @param {Object} options - Opciones
 * @returns {VirtualTable}
 */
export function createVirtualTable(selector, options = {}) {
    const container = document.querySelector(selector);
    if (!container) {
        throw new Error(`Container not found: ${selector}`);
    }
    return new VirtualTable(container, options);
}

export default VirtualTable;
