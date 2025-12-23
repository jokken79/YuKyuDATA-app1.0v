/**
 * Enhanced App Integration
 * Integra todas las mejoras implementadas
 * @module enhanced-app
 */

import { lazyLoader, loadCriticalModules, preloadAllModules } from './lazy-loader.js';
import { globalErrorBoundary, ComponentErrorBoundary } from './error-boundary.js';
import { cacheManager, cachedFetch } from '../cache-manager.js';
import { imageOptimizer, lazyLoader as imageLazyLoader, optimizeImages } from './image-optimizer.js';
import { prefersReducedMotion, getAnimationDelay } from './modules/utils.js';

/**
 * Clase principal de la aplicación mejorada
 */
export class EnhancedApp {
    constructor() {
        /** @type {boolean} Flag de inicialización */
        this.isInitialized = false;
        
        /** @type {Object} Configuración de la aplicación */
        this.config = {
            enableCache: true,
            enableLazyLoading: true,
            enableImageOptimization: true,
            enableErrorBoundary: true,
            enableServiceWorker: true,
            enablePerformanceMonitoring: true
        };
        
        /** @type {Object} Métricas de rendimiento */
        this.performanceMetrics = {
            loadTime: 0,
            renderTime: 0,
            cacheHitRate: 0,
            imageOptimizationCount: 0,
            errorCount: 0
        };
    }

    /**
     * Inicializa la aplicación mejorada
     * @param {Object} options - Opciones de configuración
     */
    async initialize(options = {}) {
        try {
            console.log('Enhanced App: Initializing...');
            
            // Medir tiempo de inicio
            const startTime = performance.now();
            
            // Combinar configuración
            this.config = { ...this.config, ...options };
            
            // Inicializar componentes en orden
            await this._initializeErrorBoundary();
            await this._initializeServiceWorker();
            await this._initializeCaching();
            await this._initializeModules();
            await this._initializeImageOptimization();
            await this._initializePerformanceMonitoring();
            
            // Calcular métricas
            this.performanceMetrics.loadTime = performance.now() - startTime;
            
            this.isInitialized = true;
            console.log('Enhanced App: Initialized successfully', this.performanceMetrics);
            
            // Disparar evento de inicialización
            this._dispatchEvent('app:initialized', {
                metrics: this.performanceMetrics,
                config: this.config
            });
            
        } catch (error) {
            console.error('Enhanced App: Initialization failed', error);
            this._handleCriticalError(error);
        }
    }

    /**
     * Inicializa el sistema de manejo de errores
     * @private
     */
    async _initializeErrorBoundary() {
        if (!this.config.enableErrorBoundary) return;
        
        // Configurar error boundary global
        globalErrorBoundary.activate();
        
        // Envolver funciones críticas
        this._wrapCriticalFunctions();
        
        console.log('Enhanced App: Error boundary initialized');
    }

    /**
     * Inicializa el Service Worker
     * @private
     */
    async _initializeServiceWorker() {
        if (!this.config.enableServiceWorker || !('serviceWorker' in navigator)) {
            return;
        }
        
        try {
            const registration = await navigator.serviceWorker.register('/static/sw-enhanced.js', {
                scope: '/'
            });
            
            console.log('Enhanced App: Service Worker registered', registration);
            
            // Esperar a que el SW esté activo
            if (registration.active) {
                this._onServiceWorkerReady(registration);
            } else {
                registration.addEventListener('controllerchange', () => {
                    this._onServiceWorkerReady(registration);
                });
            }
            
        } catch (error) {
            console.warn('Enhanced App: Service Worker registration failed', error);
        }
    }

    /**
     * Maneja cuando el Service Worker está listo
     * @param {ServiceWorkerRegistration} registration - Registro del SW
     * @private
     */
    _onServiceWorkerReady(registration) {
        // Enviar mensaje para saltar waiting
        if (registration.waiting) {
            registration.waiting.postMessage({ type: 'SKIP_WAITING' });
        }
        
        // Precacher endpoints críticos
        if (registration.active) {
            registration.active.postMessage({
                type: 'CACHE_API',
                urls: [
                    '/api/employees?enhanced=true&active_only=true',
                    '/api/yukyu/kpi-stats/2024'
                ]
            });
        }
        
        console.log('Enhanced App: Service Worker ready');
    }

    /**
     * Inicializa el sistema de caché
     * @private
     */
    async _initializeCaching() {
        if (!this.config.enableCache) return;
        
        // Configurar fetch global con cache
        this._originalFetch = window.fetch;
        window.fetch = this._enhancedFetch.bind(this);
        
        // Precargar datos críticos
        const criticalUrls = [
            '/api/employees?enhanced=true&active_only=true',
            '/api/yukyu/kpi-stats/2024',
            '/api/yukyu/monthly-summary/2024'
        ];
        
        await cacheManager.preload(criticalUrls.map(url => ({ url })));
        
        console.log('Enhanced App: Caching initialized');
    }

    /**
     * Fetch mejorado con cache
     * @param {string} url - URL del request
     * @param {Object} options - Opciones del fetch
     * @returns {Promise<Response>} - Promesa con la respuesta
     * @private
     */
    async _enhancedFetch(url, options = {}) {
        // Usar cachedFetch para endpoints de API
        if (url.includes('/api/') && this.config.enableCache) {
            return cachedFetch(url, options);
        }
        
        // Fetch normal para otros requests
        return this._originalFetch(url, options);
    }

    /**
     * Inicializa los módulos con lazy loading
     * @private
     */
    async _initializeModules() {
        if (!this.config.enableLazyLoading) return;
        
        // Cargar módulos críticos inmediatamente
        await loadCriticalModules();
        
        // Precargar módulos de UI en segundo plano
        setTimeout(async () => {
            await lazyLoader.preloadModule('/static/js/modules/ui-manager.js');
            await lazyLoader.preloadModule('/static/js/modules/chart-manager.js');
        }, 1000);
        
        // Precargar todos los módulos después de 3 segundos
        setTimeout(preloadAllModules, 3000);
        
        console.log('Enhanced App: Lazy loading initialized');
    }

    /**
     * Inicializa la optimización de imágenes
     * @private
     */
    async _initializeImageOptimization() {
        if (!this.config.enableImageOptimization) return;
        
        // Configurar lazy loading para imágenes
        this._setupImageLazyLoading();
        
        // Optimizar imágenes existentes
        this._optimizeExistingImages();
        
        // Observer para nuevas imágenes
        this._setupImageObserver();
        
        console.log('Enhanced App: Image optimization initialized');
    }

    /**
     * Configura lazy loading para imágenes existentes
     * @private
     */
    _setupImageLazyLoading() {
        const images = document.querySelectorAll('img[data-lazy="true"]');
        images.forEach(img => lazyLoader.observe(img));
    }

    /**
     * Optimiza imágenes existentes
     * @private
     */
    async _optimizeExistingImages() {
        const images = document.querySelectorAll('img:not([data-optimized])');
        
        if (images.length > 0) {
            await optimizeImages(images, {
                maxWidth: 1920,
                quality: 0.8,
                format: 'auto'
            });
            
            this.performanceMetrics.imageOptimizationCount = images.length;
        }
    }

    /**
     * Configura observer para nuevas imágenes
     * @private
     */
    _setupImageObserver() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const images = node.querySelectorAll ? 
                            node.querySelectorAll('img:not([data-optimized])') : 
                            [];
                        
                        if (images.length > 0) {
                            optimizeImages(images);
                        }
                        
                        // Lazy loading para nuevas imágenes
                        const lazyImages = node.querySelectorAll ? 
                            node.querySelectorAll('img[data-lazy="true"]') : 
                            [];
                        
                        lazyImages.forEach(img => lazyLoader.observe(img));
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Inicializa el monitoreo de rendimiento
     * @private
     */
    async _initializePerformanceMonitoring() {
        if (!this.config.enablePerformanceMonitoring) return;
        
        // Medir tiempo de renderizado
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.entryType === 'measure') {
                        this.performanceMetrics.renderTime += entry.duration;
                    }
                });
            });
            
            observer.observe({ entryTypes: ['measure'] });
        }
        
        // Medir métricas de cache periódicamente
        setInterval(() => {
            const cacheStats = cacheManager.getStats();
            this.performanceMetrics.cacheHitRate = cacheStats.hitRate;
            
            this._dispatchEvent('app:performance-update', this.performanceMetrics);
        }, 30000); // Cada 30 segundos
        
        console.log('Enhanced App: Performance monitoring initialized');
    }

    /**
     * Envuelve funciones críticas con manejo de errores
     * @private
     */
    _wrapCriticalFunctions() {
        // Envolver fetch global
        if (window.fetch) {
            window.fetch = globalErrorBoundary.wrapFunction(
                window.fetch.bind(window),
                'global-fetch'
            );
        }
        
        // Envolver funciones del DOM
        const domFunctions = ['querySelector', 'querySelectorAll', 'getElementById'];
        domFunctions.forEach(funcName => {
            if (document[funcName]) {
                document[funcName] = globalErrorBoundary.wrapFunction(
                    document[funcName].bind(document),
                    `document-${funcName}`
                );
            }
        });
    }

    /**
     * Maneja errores críticos de inicialización
     * @param {Error} error - Error capturado
     * @private
     */
    _handleCriticalError(error) {
        // Mostrar mensaje de error crítico
        const errorDiv = document.createElement('div');
        errorDiv.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: #dc2626;
                color: white;
                padding: 1rem;
                text-align: center;
                z-index: 99999;
                font-family: system-ui;
            ">
                <h3>Error Crítico de Inicialización</h3>
                <p>La aplicación no pudo iniciarse correctamente.</p>
                <button onclick="location.reload()" style="
                    background: white;
                    color: #dc2626;
                    border: none;
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-top: 0.5rem;
                ">Recargar Página</button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
    }

    /**
     * Dispara un evento personalizado
     * @param {string} eventName - Nombre del evento
     * @param {Object} detail - Detalles del evento
     * @private
     */
    _dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    /**
     * Obtiene métricas de rendimiento
     * @returns {Object} - Métricas actuales
     */
    getPerformanceMetrics() {
        return {
            ...this.performanceMetrics,
            cacheStats: cacheManager.getStats(),
            imageOptimizerStats: imageOptimizer.getStats(),
            errorStats: globalErrorBoundary.getErrorStats()
        };
    }

    /**
     * Limpia recursos y cache
     */
    cleanup() {
        console.log('Enhanced App: Cleaning up...');
        
        // Limpiar lazy loader
        if (lazyLoader) {
            lazyLoader.destroy();
        }
        
        // Limpiar cache de imágenes
        if (imageOptimizer) {
            imageOptimizer.clearCache();
        }
        
        // Limpiar cache principal
        if (cacheManager) {
            cacheManager.clear();
        }
        
        // Restaurar fetch original
        if (this._originalFetch) {
            window.fetch = this._originalFetch;
        }
        
        console.log('Enhanced App: Cleanup completed');
    }

    /**
     * Recarga la aplicación con nuevas opciones
     * @param {Object} newOptions - Nuevas opciones
     */
    async reload(newOptions = {}) {
        console.log('Enhanced App: Reloading with new options...');
        
        // Limpiar primero
        this.cleanup();
        
        // Reinicializar con nuevas opciones
        await this.initialize(newOptions);
    }
}

/**
 * Instancia global de la aplicación mejorada
 */
export const enhancedApp = new EnhancedApp();

/**
 * Función de inicialización automática
 * @param {Object} options - Opciones de configuración
 */
export async function initializeEnhancedApp(options = {}) {
    // Esperar a que el DOM esté listo
    if (document.readyState === 'loading') {
        await new Promise(resolve => {
            document.addEventListener('DOMContentLoaded', resolve);
        });
    }
    
    // Inicializar aplicación
    await enhancedApp.initialize(options);
    
    return enhancedApp;
}

/**
 * Configuración por defecto para diferentes entornos
 */
export const ENV_CONFIG = {
    development: {
        enableCache: false,
        enableErrorBoundary: true,
        enablePerformanceMonitoring: true,
        enableServiceWorker: false
    },
    
    production: {
        enableCache: true,
        enableErrorBoundary: true,
        enablePerformanceMonitoring: true,
        enableServiceWorker: true
    },
    
    testing: {
        enableCache: false,
        enableErrorBoundary: true,
        enablePerformanceMonitoring: false,
        enableServiceWorker: false
    }
};

/**
 * Detecta el entorno actual
 * @returns {string} - Nombre del entorno
 */
export function detectEnvironment() {
    const hostname = window.location.hostname;
    
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'development';
    } else if (hostname.includes('test') || hostname.includes('staging')) {
        return 'testing';
    } else {
        return 'production';
    }
}

/**
 * Inicialización automática con configuración de entorno
export async function autoInitialize() {
    const env = detectEnvironment();
    const config = ENV_CONFIG[env] || ENV_CONFIG.production;
    
    console.log(`Enhanced App: Auto-initializing for ${env} environment`);
    
    return initializeEnhancedApp(config);
}

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.EnhancedApp = EnhancedApp;
    window.enhancedApp = enhancedApp;
    window.initializeEnhancedApp = initializeEnhancedApp;
    window.autoInitialize = autoInitialize;
}

export default enhancedApp;