/**
 * Lazy Loader Module - Dynamic Import System
 * Implementa code splitting para optimizar el bundle size
 * @module lazy-loader
 */

/**
 * Clase para gestionar carga dinámica de módulos
 */
export class LazyLoader {
    constructor() {
        /** @type {Map} Cache de módulos cargados */
        this.cache = new Map();
        
        /** @type {Map} Cache de promesas de carga */
        this.loadingPromises = new Map();
    }

    /**
     * Carga un módulo de forma dinámica
     * @param {string} moduleName - Nombre del módulo a cargar
     * @param {string} path - Ruta del módulo
     * @returns {Promise<Object>} - Promesa con el módulo cargado
     */
    async loadModule(moduleName, path) {
        // Verificar si ya está en cache
        if (this.cache.has(moduleName)) {
            return this.cache.get(moduleName);
        }

        // Verificar si ya se está cargando
        if (this.loadingPromises.has(moduleName)) {
            return this.loadingPromises.get(moduleName);
        }

        // Crear promesa de carga
        const loadingPromise = this._importModule(path);
        this.loadingPromises.set(moduleName, loadingPromise);

        try {
            const module = await loadingPromise;
            this.cache.set(moduleName, module);
            this.loadingPromises.delete(moduleName);
            return module;
        } catch (error) {
            this.loadingPromises.delete(moduleName);
            throw new Error(`Failed to load module ${moduleName}: ${error.message}`);
        }
    }

    /**
     * Importa dinámicamente un módulo con fallback
     * @param {string} path - Ruta del módulo
     * @returns {Promise<Object>} - Promesa con el módulo
     * @private
     */
    async _importModule(path) {
        try {
            // Intentar importación dinámica ES6
            const module = await import(path);
            return module.default || module;
        } catch (error) {
            console.warn(`Dynamic import failed for ${path}, trying fallback`, error);
            
            // Fallback para navegadores que no soportan dynamic imports
            return this._fallbackLoad(path);
        }
    }

    /**
     * Fallback para carga de módulos con script tags
     * @param {string} path - Ruta del módulo
     * @returns {Promise<Object>} - Promesa con el módulo
     * @private
     */
    _fallbackLoad(path) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.type = 'module';
            script.src = path;
            
            script.onload = () => {
                document.head.removeChild(script);
                // Intentar obtener el módulo del window object
                const moduleName = path.split('/').pop().replace('.js', '');
                if (window[moduleName]) {
                    resolve(window[moduleName]);
                } else {
                    reject(new Error(`Module ${moduleName} not found in window`));
                }
            };
            
            script.onerror = () => {
                document.head.removeChild(script);
                reject(new Error(`Failed to load script: ${path}`));
            };
            
            document.head.appendChild(script);
        });
    }

    /**
     * Precarga un módulo sin ejecutarlo
     * @param {string} path - Ruta del módulo
     * @returns {Promise<void>} - Promesa de precarga
     */
    async preloadModule(path) {
        try {
            const link = document.createElement('link');
            link.rel = 'modulepreload';
            link.href = path;
            document.head.appendChild(link);
            
            // Esperar un poco para que el navegador procese la precarga
            await new Promise(resolve => setTimeout(resolve, 100));
        } catch (error) {
            console.warn(`Failed to preload module: ${path}`, error);
        }
    }

    /**
     * Carga múltiples módulos en paralelo
     * @param {Array<{name: string, path: string}>} modules - Array de módulos
     * @returns {Promise<Array>} - Array con los módulos cargados
     */
    async loadModules(modules) {
        const promises = modules.map(({ name, path }) => 
            this.loadModule(name, path)
        );
        return Promise.all(promises);
    }

    /**
     * Limpia el cache de un módulo específico
     * @param {string} moduleName - Nombre del módulo
     */
    clearCache(moduleName) {
        this.cache.delete(moduleName);
        this.loadingPromises.delete(moduleName);
    }

    /**
     * Limpia todo el cache
     */
    clearAllCache() {
        this.cache.clear();
        this.loadingPromises.clear();
    }

    /**
     * Verifica si un módulo está cargado
     * @param {string} moduleName - Nombre del módulo
     * @returns {boolean} - True si está cargado
     */
    isLoaded(moduleName) {
        return this.cache.has(moduleName);
    }

    /**
     * Obtiene estadísticas de carga
     * @returns {Object} - Estadísticas del loader
     */
    getStats() {
        return {
            cachedModules: this.cache.size,
            loadingModules: this.loadingPromises.size,
            cachedModuleNames: Array.from(this.cache.keys()),
            loadingModuleNames: Array.from(this.loadingPromises.keys())
        };
    }
}

/**
 * Configuración de módulos para carga diferida
 */
export const MODULE_CONFIG = {
    // Módulos críticos (cargados inmediatamente)
    critical: [
        { name: 'utils', path: '/static/js/modules/utils.js' },
        { name: 'theme-manager', path: '/static/js/modules/theme-manager.js' }
    ],
    
    // Módulos de UI (cargados cuando se necesita la interfaz)
    ui: [
        { name: 'ui-manager', path: '/static/js/modules/ui-manager.js' },
        { name: 'chart-manager', path: '/static/js/modules/chart-manager.js' }
    ],
    
    // Módulos de datos (cargados cuando se manipulan datos)
    data: [
        { name: 'data-service', path: '/static/js/modules/data-service.js' },
        { name: 'export-service', path: '/static/js/modules/export-service.js' }
    ],
    
    // Módulos avanzados (cargados bajo demanda)
    advanced: [
        { name: 'virtual-table', path: '/static/js/modules/virtual-table.js' },
        { name: 'lazy-loader', path: '/static/js/modules/lazy-loader.js' }
    ]
};

/**
 * Instancia singleton del LazyLoader
 */
export const lazyLoader = new LazyLoader();

/**
 * Función de conveniencia para cargar módulos críticos
 * @returns {Promise<void>}
 */
export async function loadCriticalModules() {
    await lazyLoader.loadModules(MODULE_CONFIG.critical);
}

/**
 * Función de conveniencia para cargar módulos de UI
 * @returns {Promise<void>}
 */
export async function loadUIModules() {
    await lazyLoader.loadModules(MODULE_CONFIG.ui);
}

/**
 * Función de conveniencia para cargar módulos de datos
 * @returns {Promise<void>}
 */
export async function loadDataModules() {
    await lazyLoader.loadModules(MODULE_CONFIG.data);
}

/**
 * Función de conveniencia para cargar módulos avanzados
 * @returns {Promise<void>}
 */
export async function loadAdvancedModules() {
    await lazyLoader.loadModules(MODULE_CONFIG.advanced);
}

/**
 * Precarga todos los módulos en segundo plano
 * @returns {Promise<void>}
 */
export async function preloadAllModules() {
    const allModules = [
        ...MODULE_CONFIG.ui,
        ...MODULE_CONFIG.data,
        ...MODULE_CONFIG.advanced
    ];
    
    const preloadPromises = allModules.map(({ path }) => 
        lazyLoader.preloadModule(path)
    );
    
    await Promise.allSettled(preloadPromises);
}

export default lazyLoader;