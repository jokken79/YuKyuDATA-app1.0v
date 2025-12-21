/**
 * EJEMPLO DE USO - Optimizaciones de Performance
 * YuKyuDATA v1.0
 *
 * Este archivo muestra cómo implementar todas las optimizaciones
 * en la aplicación real.
 */

// ============================================================================
// 1. IMPORTAR MÓDULOS
// ============================================================================

import { VirtualTable } from '/static/js/modules/virtual-table.js';
import {
    debounce,
    throttle,
    rafThrottle,
    prefersReducedMotion
} from '/static/js/modules/utils.js';
import {
    LazyChartLoader,
    lazyModuleLoader
} from '/static/js/modules/lazy-loader.js';


// ============================================================================
// 2. VIRTUALIZACIÓN DE TABLA PRINCIPAL
// ============================================================================

// Estado global
let employeesData = [];
let virtualTableInstance = null;

// Función para inicializar tabla virtual
async function initVirtualTable() {
    const container = document.querySelector('#employee-table-wrapper');

    // Crear instancia de VirtualTable
    virtualTableInstance = new VirtualTable(container, {
        rowHeight: 60,              // Altura de cada fila
        visibleRows: 20,            // Filas visibles simultáneamente
        bufferRows: 10,             // Buffer superior/inferior
        threshold: 0.5,
        onRowClick: handleRowClick  // Click en fila
    });

    // Función para renderizar columnas
    const renderEmployeeRow = (employee, index) => {
        const balanceBadge = employee.balance < 5
            ? 'badge-danger'
            : employee.balance < 10
                ? 'badge-warning'
                : 'badge-success';

        return `
            <td>${Utils.escapeHtml(employee.employee_num)}</td>
            <td>${Utils.escapeHtml(employee.name)}</td>
            <td>${Utils.escapeHtml(employee.haken)}</td>
            <td>${employee.granted.toFixed(1)}</td>
            <td>${employee.used.toFixed(1)}</td>
            <td><span class="badge ${balanceBadge}">${employee.balance.toFixed(1)}</span></td>
            <td>${(employee.usage_rate * 100).toFixed(1)}%</td>
        `;
    };

    // Cargar datos
    try {
        const response = await fetch('/api/employees');
        employeesData = await response.json();

        virtualTableInstance.setData(employeesData, renderEmployeeRow);

        console.log(`✅ Tabla virtual cargada con ${employeesData.length} empleados`);
    } catch (error) {
        console.error('Error cargando empleados:', error);
        showToast('Error cargando datos', 'error');
    }
}

// Handler para click en fila
function handleRowClick(employee, index, row) {
    showEmployeeModal(employee);
}


// ============================================================================
// 3. BÚSQUEDA CON DEBOUNCING
// ============================================================================

// Función de búsqueda
function performSearch(searchTerm) {
    if (!virtualTableInstance) return;

    const lowerSearch = searchTerm.toLowerCase().trim();

    if (!lowerSearch) {
        // Mostrar todos si búsqueda vacía
        virtualTableInstance.filter(() => true);
        updateSearchResults(employeesData.length);
        return;
    }

    // Filtrar empleados
    const filtered = employeesData.filter(emp =>
        emp.name.toLowerCase().includes(lowerSearch) ||
        emp.employee_num.includes(lowerSearch) ||
        emp.haken.toLowerCase().includes(lowerSearch)
    );

    // Aplicar filtro a tabla virtual
    virtualTableInstance.filter(emp => filtered.includes(emp));

    updateSearchResults(filtered.length);
}

// Crear versión debounced de la búsqueda
const debouncedSearch = debounce(performSearch, 300);

// Configurar input de búsqueda
function setupSearchInput() {
    const searchInput = document.querySelector('#employee-search');

    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        debouncedSearch(e.target.value);
    });

    // Feedback visual mientras se escribe
    searchInput.addEventListener('input', () => {
        searchInput.classList.add('searching');
    });

    // Remover feedback después de debounce
    const removeSearchingClass = debounce(() => {
        searchInput.classList.remove('searching');
    }, 350);

    searchInput.addEventListener('input', () => {
        removeSearchingClass();
    });
}

function updateSearchResults(count) {
    const resultsElement = document.querySelector('#search-results-count');
    if (resultsElement) {
        resultsElement.textContent = `${count} resultado${count !== 1 ? 's' : ''}`;
    }
}


// ============================================================================
// 4. FILTROS CON THROTTLING
// ============================================================================

function applyFilters() {
    const yearFilter = document.querySelector('#year-filter').value;
    const departmentFilter = document.querySelector('#department-filter').value;
    const balanceFilter = document.querySelector('#balance-filter').value;

    let filtered = [...employeesData];

    // Filtro por año
    if (yearFilter && yearFilter !== 'all') {
        filtered = filtered.filter(emp => emp.year === parseInt(yearFilter));
    }

    // Filtro por departamento
    if (departmentFilter && departmentFilter !== 'all') {
        filtered = filtered.filter(emp => emp.haken === departmentFilter);
    }

    // Filtro por balance
    if (balanceFilter && balanceFilter !== 'all') {
        switch (balanceFilter) {
            case 'low':
                filtered = filtered.filter(emp => emp.balance < 5);
                break;
            case 'medium':
                filtered = filtered.filter(emp => emp.balance >= 5 && emp.balance < 10);
                break;
            case 'high':
                filtered = filtered.filter(emp => emp.balance >= 10);
                break;
        }
    }

    virtualTableInstance.filter(emp => filtered.includes(emp));
    updateFilterResults(filtered.length);
}

// Throttled version para filtros rápidos
const throttledFilter = throttle(applyFilters, 150);

function setupFilters() {
    const filterElements = document.querySelectorAll(
        '#year-filter, #department-filter, #balance-filter'
    );

    filterElements.forEach(filter => {
        filter.addEventListener('change', throttledFilter);
    });
}


// ============================================================================
// 5. LAZY LOADING DE GRÁFICOS
// ============================================================================

const chartLoader = new LazyChartLoader({
    rootMargin: '100px',
    threshold: 0.1,
    chartLibrary: 'apexcharts'
});

// Registrar gráfico de distribución de uso
function registerUsageDistributionChart() {
    chartLoader.registerChart(
        'usage-distribution',
        '#usage-distribution-chart',
        async (container) => {
            // Preparar datos
            const ranges = {
                '0-25%': 0,
                '26-50%': 0,
                '51-75%': 0,
                '76-100%': 0
            };

            employeesData.forEach(emp => {
                const rate = emp.usage_rate * 100;
                if (rate <= 25) ranges['0-25%']++;
                else if (rate <= 50) ranges['26-50%']++;
                else if (rate <= 75) ranges['51-75%']++;
                else ranges['76-100%']++;
            });

            const options = {
                series: [{
                    name: 'Empleados',
                    data: Object.values(ranges)
                }],
                chart: {
                    type: 'bar',
                    height: 350,
                    background: 'transparent',
                    foreColor: '#e2e8f0'
                },
                xaxis: {
                    categories: Object.keys(ranges)
                },
                colors: ['#06b6d4'],
                theme: {
                    mode: document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'
                }
            };

            const chart = new ApexCharts(container, options);
            await chart.render();
            return chart;
        }
    );
}

// Registrar gráfico de top 10 usuarios
function registerTop10Chart() {
    chartLoader.registerChart(
        'top-10-users',
        '#top-10-chart',
        async (container) => {
            // Top 10 por uso
            const sorted = [...employeesData]
                .sort((a, b) => b.used - a.used)
                .slice(0, 10);

            const options = {
                series: [{
                    name: 'Días usados',
                    data: sorted.map(emp => emp.used)
                }],
                chart: {
                    type: 'bar',
                    height: 350,
                    background: 'transparent',
                    foreColor: '#e2e8f0'
                },
                xaxis: {
                    categories: sorted.map(emp => emp.name)
                },
                colors: ['#22d3ee'],
                plotOptions: {
                    bar: {
                        horizontal: true
                    }
                }
            };

            const chart = new ApexCharts(container, options);
            await chart.render();
            return chart;
        }
    );
}


// ============================================================================
// 6. LAZY LOADING DE MÓDULOS
// ============================================================================

// Exportar a Excel - solo cargar cuando se necesite
async function exportToExcel() {
    try {
        showToast('Preparando exportación...', 'info');

        // Cargar módulo de exportación bajo demanda
        const exportModule = await lazyModuleLoader.loadModule(
            'export-service',
            '/static/js/modules/export-service.js'
        );

        // Usar el módulo
        await exportModule.exportToExcel(employeesData);

        showToast('Exportación completada', 'success');
    } catch (error) {
        console.error('Error en exportación:', error);
        showToast('Error al exportar', 'error');
    }
}

// Botón de exportación
function setupExportButton() {
    const exportBtn = document.querySelector('#export-excel-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToExcel);
    }
}


// ============================================================================
// 7. SCROLL OPTIMIZADO CON RAF THROTTLE
// ============================================================================

let scrollPosition = 0;

function updateScrollIndicator() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercentage = (scrollTop / scrollHeight) * 100;

    // Actualizar indicador visual
    const indicator = document.querySelector('#scroll-indicator');
    if (indicator) {
        indicator.style.width = `${scrollPercentage}%`;
    }

    // Mostrar/ocultar botón "volver arriba"
    const backToTopBtn = document.querySelector('#back-to-top');
    if (backToTopBtn) {
        backToTopBtn.style.display = scrollTop > 300 ? 'flex' : 'none';
    }

    scrollPosition = scrollTop;
}

// RAF throttled para mejor performance
const rafScrollUpdate = rafThrottle(updateScrollIndicator);

function setupScrollOptimization() {
    window.addEventListener('scroll', rafScrollUpdate, { passive: true });
}


// ============================================================================
// 8. ANIMACIONES CON RESPETO A PREFERS-REDUCED-MOTION
// ============================================================================

function initAnimations() {
    if (prefersReducedMotion()) {
        console.log('⚡ Animaciones reducidas (usuario prefiere movimiento reducido)');
        document.body.classList.add('reduced-motion');
        return;
    }

    // Animaciones completas
    const animateOnScroll = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                animateOnScroll.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '50px'
    });

    // Observar elementos animables
    document.querySelectorAll('.stat-card, .glass-panel').forEach(el => {
        animateOnScroll.observe(el);
    });
}


// ============================================================================
// 9. PERFORMANCE MONITORING
// ============================================================================

function measureTablePerformance() {
    performance.mark('table-render-start');

    initVirtualTable().then(() => {
        performance.mark('table-render-end');
        performance.measure('table-render', 'table-render-start', 'table-render-end');

        const measure = performance.getEntriesByName('table-render')[0];
        console.log(`📊 Tabla renderizada en ${measure.duration.toFixed(2)}ms`);

        // Alertar si es muy lento
        if (measure.duration > 200) {
            console.warn('⚠️ Renderizado de tabla lento. Considerar optimizaciones adicionales.');
        }
    });
}


// ============================================================================
// 10. INICIALIZACIÓN DE LA APLICACIÓN
// ============================================================================

async function initApp() {
    console.log('🚀 Iniciando YuKyuDATA con optimizaciones de performance...');

    // 1. Inicializar tabla virtual
    await measureTablePerformance();

    // 2. Configurar búsqueda con debouncing
    setupSearchInput();

    // 3. Configurar filtros con throttling
    setupFilters();

    // 4. Registrar gráficos para lazy loading
    registerUsageDistributionChart();
    registerTop10Chart();

    // 5. Configurar exportación lazy
    setupExportButton();

    // 6. Optimizar scroll
    setupScrollOptimization();

    // 7. Configurar animaciones
    initAnimations();

    console.log('✅ Aplicación iniciada correctamente');
    console.log('📈 Performance optimizations enabled:');
    console.log('  - Virtual scrolling: ON');
    console.log('  - Debounced search: ON (300ms)');
    console.log('  - Throttled filters: ON (150ms)');
    console.log('  - Lazy charts: ON');
    console.log('  - Lazy modules: ON');
    console.log('  - RAF scroll: ON');
    console.log('  - Reduced motion:', prefersReducedMotion() ? 'RESPECTING' : 'OFF');
}

// Ejecutar cuando DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}


// ============================================================================
// UTILIDADES ADICIONALES
// ============================================================================

function showToast(message, type = 'info') {
    // Implementación de toast
    console.log(`[${type.toUpperCase()}] ${message}`);
}

function showEmployeeModal(employee) {
    // Implementación de modal
    console.log('Mostrando detalles de:', employee);
}

function updateFilterResults(count) {
    const resultsElement = document.querySelector('#filter-results-count');
    if (resultsElement) {
        resultsElement.textContent = `${count} resultado${count !== 1 ? 's' : ''}`;
    }
}


// ============================================================================
// EXPORTAR PARA USO EN OTROS MÓDULOS
// ============================================================================

export {
    virtualTableInstance,
    employeesData,
    debouncedSearch,
    throttledFilter,
    chartLoader,
    exportToExcel
};
