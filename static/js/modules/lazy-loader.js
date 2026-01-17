/**
 * Lazy Loader Module - Carga diferida de recursos y módulos
 * Optimiza la carga inicial y mejora Time to Interactive
 * @module lazy-loader
 */

/**
 * Lazy Image Loader - Carga imágenes cuando son visibles
 * @param {string} selector - Selector CSS para imágenes lazy
 * @param {Object} options - Opciones del observer
 */
export function lazyLoadImages(selector = 'img[data-src]', options = {}) {
    const defaultOptions = {
        root: null,
        rootMargin: '50px',
        threshold: 0.01
    };

    const config = { ...defaultOptions, ...options };

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                const src = img.dataset.src;

                if (src) {
                    // Preload de la imagen
                    const tempImage = new Image();
                    tempImage.onload = () => {
                        img.src = src;
                        img.classList.add('lazy-loaded');
                        img.removeAttribute('data-src');
                    };
                    tempImage.onerror = () => {
                        img.classList.add('lazy-error');
                    };
                    tempImage.src = src;
                }

                observer.unobserve(img);
            }
        });
    }, config);

    // Observar todas las imágenes
    document.querySelectorAll(selector).forEach(img => {
        imageObserver.observe(img);
    });

    return imageObserver;
}

/**
 * Lazy Chart Loader - Carga gráficos cuando son visibles
 * Compatible con Chart.js y ApexCharts
 */
export class LazyChartLoader {
    constructor(options = {}) {
        this.options = {
            rootMargin: '100px',
            threshold: 0.1,
            chartLibrary: 'apexcharts', // 'chartjs' o 'apexcharts'
            ...options
        };

        this.charts = new Map();
        this.observer = null;
        this._init();
    }

    /**
     * Inicializa el IntersectionObserver
     * @private
     */
    _init() {
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const container = entry.target;
                    const chartId = container.dataset.chartId;

                    if (chartId && this.charts.has(chartId)) {
                        this._renderChart(chartId, container);
                        this.observer.unobserve(container);
                    }
                }
            });
        }, {
            root: null,
            rootMargin: this.options.rootMargin,
            threshold: this.options.threshold
        });
    }

    /**
     * Registra un gráfico para carga lazy
     * @param {string} chartId - ID único del gráfico
     * @param {string|HTMLElement} container - Contenedor del gráfico
     * @param {Function} renderFn - Función que renderiza el gráfico
     */
    registerChart(chartId, container, renderFn) {
        const element = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!element) {
            console.warn(`[LazyChartLoader] Container not found: ${container}`);
            return;
        }

        // Guardar configuración del gráfico
        element.dataset.chartId = chartId;
        this.charts.set(chartId, {
            element,
            renderFn,
            rendered: false,
            instance: null
        });

        // Observar el contenedor
        this.observer.observe(element);

        // Agregar clase para indicar que está pendiente
        element.classList.add('lazy-chart-pending');
    }

    /**
     * Renderiza un gráfico específico
     * @param {string} chartId - ID del gráfico
     * @param {HTMLElement} container - Contenedor
     * @private
     */
    async _renderChart(chartId, container) {
        const chartConfig = this.charts.get(chartId);

        if (!chartConfig || chartConfig.rendered) {
            return;
        }

        try {
            // Mostrar skeleton loader
            container.classList.add('lazy-chart-loading');
            container.classList.remove('lazy-chart-pending');

            // Cargar biblioteca si no está disponible
            if (this.options.chartLibrary === 'apexcharts' && !window.ApexCharts) {
                await this._loadApexCharts();
            } else if (this.options.chartLibrary === 'chartjs' && !window.Chart) {
                await this._loadChartJS();
            }

            // Ejecutar función de renderizado
            const chartInstance = await chartConfig.renderFn(container);

            // Actualizar estado
            chartConfig.rendered = true;
            chartConfig.instance = chartInstance;

            container.classList.remove('lazy-chart-loading');
            container.classList.add('lazy-chart-loaded');

            // Chart rendered successfully
        } catch (error) {
            console.error(`[LazyChartLoader] Error rendering chart ${chartId}:`, error);
            container.classList.remove('lazy-chart-loading');
            container.classList.add('lazy-chart-error');
        }
    }

    /**
     * Carga ApexCharts dinámicamente
     * @private
     */
    async _loadApexCharts() {
        return new Promise((resolve, reject) => {
            if (window.ApexCharts) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/apexcharts@3.44.0/dist/apexcharts.min.js';
            script.onload = () => {
                // ApexCharts loaded
                resolve();
            };
            script.onerror = () => reject(new Error('Failed to load ApexCharts'));
            document.head.appendChild(script);
        });
    }

    /**
     * Carga Chart.js dinámicamente
     * @private
     */
    async _loadChartJS() {
        return new Promise((resolve, reject) => {
            if (window.Chart) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
            script.onload = () => {
                // Chart.js loaded
                resolve();
            };
            script.onerror = () => reject(new Error('Failed to load Chart.js'));
            document.head.appendChild(script);
        });
    }

    /**
     * Fuerza el renderizado de un gráfico sin esperar a que sea visible
     * @param {string} chartId - ID del gráfico
     */
    forceRender(chartId) {
        const chartConfig = this.charts.get(chartId);
        if (chartConfig && !chartConfig.rendered) {
            this._renderChart(chartId, chartConfig.element);
        }
    }

    /**
     * Obtiene la instancia de un gráfico renderizado
     * @param {string} chartId - ID del gráfico
     * @returns {Object|null} - Instancia del gráfico o null
     */
    getChart(chartId) {
        const chartConfig = this.charts.get(chartId);
        return chartConfig?.instance || null;
    }

    /**
     * Destruye todos los gráficos y limpia recursos
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }

        this.charts.forEach((config, chartId) => {
            if (config.instance && typeof config.instance.destroy === 'function') {
                config.instance.destroy();
            }
        });

        this.charts.clear();
    }
}

/**
 * Lazy Module Loader - Carga módulos ES6 dinámicamente
 */
export class LazyModuleLoader {
    constructor() {
        this.modules = new Map();
        this.loading = new Set();
    }

    /**
     * Carga un módulo dinámicamente
     * @param {string} moduleId - ID único del módulo
     * @param {string} modulePath - Path al módulo
     * @returns {Promise} - Módulo cargado
     */
    async loadModule(moduleId, modulePath) {
        // Si ya está cargado, retornar desde cache
        if (this.modules.has(moduleId)) {
            return this.modules.get(moduleId);
        }

        // Si está cargando, esperar a que termine
        if (this.loading.has(moduleId)) {
            return this._waitForModule(moduleId);
        }

        try {
            this.loading.add(moduleId);
            // Loading module

            const module = await import(modulePath);

            this.modules.set(moduleId, module);
            this.loading.delete(moduleId);

            // Module loaded
            return module;
        } catch (error) {
            this.loading.delete(moduleId);
            console.error(`[LazyModuleLoader] Error loading module ${moduleId}:`, error);
            throw error;
        }
    }

    /**
     * Espera a que un módulo termine de cargar
     * @param {string} moduleId - ID del módulo
     * @private
     */
    async _waitForModule(moduleId) {
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                if (!this.loading.has(moduleId)) {
                    clearInterval(checkInterval);
                    resolve(this.modules.get(moduleId));
                }
            }, 50);
        });
    }

    /**
     * Precarga módulos en segundo plano
     * @param {Array} moduleConfigs - Array de {id, path}
     */
    async preloadModules(moduleConfigs) {
        const promises = moduleConfigs.map(({ id, path }) =>
            this.loadModule(id, path).catch(err => {
                console.warn(`[LazyModuleLoader] Failed to preload ${id}:`, err);
            })
        );

        return Promise.allSettled(promises);
    }

    /**
     * Verifica si un módulo está cargado
     * @param {string} moduleId - ID del módulo
     * @returns {boolean}
     */
    isLoaded(moduleId) {
        return this.modules.has(moduleId);
    }

    /**
     * Obtiene un módulo cargado
     * @param {string} moduleId - ID del módulo
     * @returns {Object|null}
     */
    getModule(moduleId) {
        return this.modules.get(moduleId) || null;
    }
}

/**
 * Lazy Component Loader - Carga componentes cuando son necesarios
 */
export class LazyComponentLoader {
    constructor() {
        this.components = new Map();
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const componentId = element.dataset.lazyComponent;

                    if (componentId) {
                        this._loadComponent(componentId, element);
                        this.observer.unobserve(element);
                    }
                }
            });
        }, {
            rootMargin: '200px',
            threshold: 0.01
        });
    }

    /**
     * Registra un componente para carga lazy
     * @param {string} componentId - ID del componente
     * @param {string|HTMLElement} container - Contenedor
     * @param {Function} loaderFn - Función que carga y renderiza el componente
     */
    registerComponent(componentId, container, loaderFn) {
        const element = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!element) {
            console.warn(`[LazyComponentLoader] Container not found: ${container}`);
            return;
        }

        element.dataset.lazyComponent = componentId;
        this.components.set(componentId, {
            element,
            loaderFn,
            loaded: false
        });

        this.observer.observe(element);
    }

    /**
     * Carga un componente
     * @param {string} componentId - ID del componente
     * @param {HTMLElement} element - Elemento contenedor
     * @private
     */
    async _loadComponent(componentId, element) {
        const config = this.components.get(componentId);

        if (!config || config.loaded) {
            return;
        }

        try {
            element.classList.add('lazy-component-loading');
            await config.loaderFn(element);
            config.loaded = true;
            element.classList.remove('lazy-component-loading');
            element.classList.add('lazy-component-loaded');
            // Component loaded
        } catch (error) {
            console.error(`[LazyComponentLoader] Error loading component ${componentId}:`, error);
            element.classList.add('lazy-component-error');
        }
    }

    /**
     * Destruye el loader y limpia recursos
     */
    destroy() {
        this.observer.disconnect();
        this.components.clear();
    }
}

/**
 * Helper function para crear un loader de gráficos rápidamente
 * @param {Object} options - Opciones
 * @returns {LazyChartLoader}
 */
export function createLazyChartLoader(options = {}) {
    return new LazyChartLoader(options);
}

/**
 * Helper function para crear un loader de módulos
 * @returns {LazyModuleLoader}
 */
export function createLazyModuleLoader() {
    return new LazyModuleLoader();
}

/**
 * Exportar instancias globales para uso conveniente
 */
export const lazyChartLoader = new LazyChartLoader();
export const lazyModuleLoader = new LazyModuleLoader();
export const lazyComponentLoader = new LazyComponentLoader();

export default {
    LazyChartLoader,
    LazyModuleLoader,
    LazyComponentLoader,
    lazyLoadImages,
    createLazyChartLoader,
    createLazyModuleLoader,
    lazyChartLoader,
    lazyModuleLoader,
    lazyComponentLoader
};
