/**
 * Cache Manager Module
 * Implementa caching para endpoints frecuentemente accedidos
 * @module cache-manager
 */

/**
 * Clase para gestionar caché de respuestas API
 */
export class CacheManager {
    constructor(options = {}) {
        /** @type {Map} Cache principal */
        this.cache = new Map();
        
        /** @type {Map} Metadatos del cache */
        this.metadata = new Map();
        
        /** @type {number} Tiempo por defecto (5 minutos) */
        this.defaultTTL = options.defaultTTL || 5 * 60 * 1000;
        
        /** @type {number} Máximo tamaño del cache (100 items) */
        this.maxSize = options.maxSize || 100;
        
        /** @type {string} Prefijo para claves */
        this.keyPrefix = options.keyPrefix || 'yukyu_cache_';
        
        /** @type {boolean} Usar localStorage */
        this.useLocalStorage = options.useLocalStorage !== false;
        
        this._loadFromStorage();
    }

    /**
     * Genera una clave de cache
     * @param {string} url - URL del request
     * @param {Object} options - Opciones adicionales
     * @returns {string} - Clave de cache
     * @private
     */
    _generateKey(url, options = {}) {
        const params = new URLSearchParams(options.params || {}).toString();
        const key = params ? `${url}?${params}` : url;
        return this.keyPrefix + btoa(key);
    }

    /**
     * Verifica si un item está en cache y es válido
     * @param {string} key - Clave del cache
     * @returns {boolean} - True si es válido
     * @private
     */
    _isValid(key) {
        const meta = this.metadata.get(key);
        if (!meta) return false;
        
        // Verificar TTL
        if (Date.now() > meta.expires) {
            this.delete(key);
            return false;
        }
        
        return true;
    }

    /**
     * Limpia cache expirado
     * @private
     */
    _cleanupExpired() {
        const now = Date.now();
        for (const [key, meta] of this.metadata.entries()) {
            if (now > meta.expires) {
                this.delete(key);
            }
        }
    }

    /**
     * Maneja el tamaño máximo del cache
     * @private
     */
    _manageSize() {
        if (this.cache.size >= this.maxSize) {
            // Eliminar el item más antiguo (LRU)
            let oldestKey = null;
            let oldestTime = Date.now();
            
            for (const [key, meta] of this.metadata.entries()) {
                if (meta.created < oldestTime) {
                    oldestTime = meta.created;
                    oldestKey = key;
                }
            }
            
            if (oldestKey) {
                this.delete(oldestKey);
            }
        }
    }

    /**
     * Guarda en localStorage
     * @private
     */
    _saveToStorage() {
        if (!this.useLocalStorage) return;
        
        try {
            const cacheData = {
                cache: Array.from(this.cache.entries()),
                metadata: Array.from(this.metadata.entries()),
                timestamp: Date.now()
            };
            
            localStorage.setItem(this.keyPrefix + 'data', JSON.stringify(cacheData));
        } catch (error) {
            console.warn('Failed to save cache to localStorage:', error);
        }
    }

    /**
     * Carga desde localStorage
     * @private
     */
    _loadFromStorage() {
        if (!this.useLocalStorage) return;
        
        try {
            const data = localStorage.getItem(this.keyPrefix + 'data');
            if (!data) return;
            
            const cacheData = JSON.parse(data);
            
            // Restaurar cache
            this.cache = new Map(cacheData.cache || []);
            this.metadata = new Map(cacheData.metadata || []);
            
            // Limpiar expirados
            this._cleanupExpired();
        } catch (error) {
            console.warn('Failed to load cache from localStorage:', error);
        }
    }

    /**
     * Obtiene un item del cache
     * @param {string} url - URL del request
     * @param {Object} options - Opciones adicionales
     * @returns {any|null} - Datos cacheados o null
     */
    get(url, options = {}) {
        const key = this._generateKey(url, options);
        
        if (!this._isValid(key)) {
            return null;
        }
        
        // Actualizar metadatos de acceso
        const meta = this.metadata.get(key);
        meta.lastAccessed = Date.now();
        meta.accessCount++;
        
        const data = this.cache.get(key);
        
        // Actualizar localStorage
        this._saveToStorage();
        
        return data;
    }

    /**
     * Guarda un item en el cache
     * @param {string} url - URL del request
     * @param {any} data - Datos a cachear
     * @param {Object} options - Opciones
     * @returns {boolean} - True si se guardó correctamente
     */
    set(url, data, options = {}) {
        const key = this._generateKey(url, options);
        const ttl = options.ttl || this.defaultTTL;
        
        // Manejar tamaño del cache
        this._manageSize();
        
        const now = Date.now();
        const meta = {
            created: now,
            lastAccessed: now,
            accessCount: 0,
            expires: now + ttl,
            url: url,
            ttl: ttl
        };
        
        // Guardar en cache
        this.cache.set(key, data);
        this.metadata.set(key, meta);
        
        // Guardar en localStorage
        this._saveToStorage();
        
        return true;
    }

    /**
     * Elimina un item del cache
     * @param {string} key - Clave del item
     * @returns {boolean} - True si se eliminó
     */
    delete(key) {
        const deleted = this.cache.delete(key) || this.metadata.delete(key);
        
        if (deleted) {
            this._saveToStorage();
        }
        
        return deleted;
    }

    /**
     * Elimina un item por URL
     * @param {string} url - URL del request
     * @param {Object} options - Opciones adicionales
     * @returns {boolean} - True si se eliminó
     */
    deleteByUrl(url, options = {}) {
        const key = this._generateKey(url, options);
        return this.delete(key);
    }

    /**
     * Limpia todo el cache
     */
    clear() {
        this.cache.clear();
        this.metadata.clear();
        
        if (this.useLocalStorage) {
            localStorage.removeItem(this.keyPrefix + 'data');
        }
    }

    /**
     * Obtiene estadísticas del cache
     * @returns {Object} - Estadísticas
     */
    getStats() {
        const now = Date.now();
        let totalSize = 0;
        let expiredCount = 0;
        let accessStats = { total: 0, average: 0 };
        
        for (const [key, meta] of this.metadata.entries()) {
            totalSize += JSON.stringify(this.cache.get(key)).length;
            
            if (now > meta.expires) {
                expiredCount++;
            }
            
            accessStats.total += meta.accessCount;
        }
        
        accessStats.average = accessStats.total / this.metadata.size || 0;
        
        return {
            size: this.cache.size,
            maxSize: this.maxSize,
            totalSizeBytes: totalSize,
            expiredCount: expiredCount,
            hitRate: this._calculateHitRate(),
            averageAccess: accessStats.average,
            keys: Array.from(this.metadata.keys())
        };
    }

    /**
     * Calcula el hit rate del cache
     * @returns {number} - Hit rate (0-1)
     * @private
     */
    _calculateHitRate() {
        let totalAccess = 0;
        let hits = 0;
        
        for (const meta of this.metadata.values()) {
            totalAccess += meta.accessCount;
            if (meta.accessCount > 1) {
                hits += meta.accessCount - 1; // Restar el primer acceso (miss)
            }
        }
        
        return totalAccess > 0 ? hits / totalAccess : 0;
    }

    /**
     * Precarga múltiples URLs
     * @param {Array<{url: string, options?: Object}>} urls - URLs a precargar
     * @returns {Promise<Array>} - Promesa con resultados
     */
    async preload(urls) {
        const promises = urls.map(async ({ url, options = {} }) => {
            try {
                // Solo precargar si no está en cache
                if (this.get(url, options) === null) {
                    const response = await fetch(url);
                    if (response.ok) {
                        const data = await response.json();
                        this.set(url, data, { ...options, ttl: 10 * 60 * 1000 }); // 10 minutos
                        return { url, success: true };
                    }
                }
                return { url, success: true, cached: true };
            } catch (error) {
                console.warn(`Failed to preload ${url}:`, error);
                return { url, success: false, error: error.message };
            }
        });
        
        return Promise.all(promises);
    }

    /**
     * Invalida cache por patrón
     * @param {RegExp|string} pattern - Patrón para invalidar
     */
    invalidate(pattern) {
        const keysToDelete = [];
        
        for (const [key, meta] of this.metadata.entries()) {
            const shouldDelete = typeof pattern === 'string' 
                ? meta.url.includes(pattern)
                : pattern.test(meta.url);
                
            if (shouldDelete) {
                keysToDelete.push(key);
            }
        }
        
        keysToDelete.forEach(key => this.delete(key));
        
        return keysToDelete.length;
    }
}

/**
 * Configuración de cache para diferentes endpoints
 */
export const CACHE_CONFIG = {
    // Datos que cambian frecuentemente (1 minuto)
    volatile: {
        ttl: 1 * 60 * 1000,
        endpoints: [
            '/api/employees',
            '/api/yukyu/kpi-stats',
            '/api/sync'
        ]
    },
    
    // Datos que cambian ocasionalmente (5 minutos)
    standard: {
        ttl: 5 * 60 * 1000,
        endpoints: [
            '/api/yukyu/monthly-summary',
            '/api/yukyu/by-employee-type',
            '/api/analytics/top10-active'
        ]
    },
    
    // Datos que cambian raramente (30 minutos)
    stable: {
        ttl: 30 * 60 * 1000,
        endpoints: [
            '/api/factories',
            '/api/departments',
            '/api/employee-types'
        ]
    }
};

/**
 * Instancia global del cache manager
 */
export const cacheManager = new CacheManager({
    defaultTTL: 5 * 60 * 1000, // 5 minutos
    maxSize: 100,
    useLocalStorage: true
});

/**
 * Wrapper para fetch con cache
 * @param {string} url - URL a fetch
 * @param {Object} options - Opciones de fetch y cache
 * @returns {Promise<Response>} - Promesa con la respuesta
 */
export async function cachedFetch(url, options = {}) {
    const cacheOptions = {
        ttl: options.cacheTTL,
        params: options.params
    };
    
    // Intentar obtener del cache primero
    const cachedData = cacheManager.get(url, cacheOptions);
    if (cachedData && !options.skipCache) {
        return new Response(JSON.stringify(cachedData), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });
    }
    
    // Si no está en cache o se salta el cache
    try {
        const response = await fetch(url, {
            ...options,
            cache: options.cache || 'default'
        });
        
        // Cachear respuestas exitosas
        if (response.ok && !options.skipCache) {
            const data = await response.clone().json();
            cacheManager.set(url, data, cacheOptions);
        }
        
        return response;
    } catch (error) {
        // Si falla el fetch y hay datos cacheados, usarlos
        if (cachedData && !options.skipCache) {
            console.warn(`Using cached data for ${url} due to fetch error:`, error);
            return new Response(JSON.stringify(cachedData), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        throw error;
    }
}

export default cacheManager;