/**
 * Data Service Module
 * Gestiona la obtención y sincronización de datos desde el API
 * @module data-service
 */

/**
 * Clase para gestionar datos de empleados
 */
export class DataService {
    /**
     * Crea una nueva instancia de DataService
     * @param {string} apiBase - URL base del API
     */
    constructor(apiBase = '/api') {
        /** @type {string} URL base del API */
        this.apiBase = apiBase;

        /** @type {number} Contador de requests para prevenir race conditions */
        this._fetchRequestId = 0;

        /** @type {number} Timeout por defecto en milisegundos (30 segundos) */
        this.defaultTimeout = 30000;

        /** @type {string|null} Token CSRF cacheado */
        this._csrfToken = null;

        /** @type {number} Timestamp de cuando se obtuvo el token CSRF */
        this._csrfTokenTimestamp = 0;

        /** @type {number} Tiempo de vida del token CSRF en ms (50 minutos) */
        this._csrfTokenTTL = 50 * 60 * 1000;

        /** @type {Set} Metodos HTTP que requieren CSRF token */
        this._mutatingMethods = new Set(['POST', 'PUT', 'DELETE', 'PATCH']);
    }

    /**
     * Obtiene un token CSRF desde el servidor
     * @returns {Promise<string>} Token CSRF
     * @private
     */
    async _fetchCsrfToken() {
        try {
            const response = await fetch(`${this.apiBase}/csrf-token`);
            if (!response.ok) {
                throw new Error(`Failed to fetch CSRF token: ${response.status}`);
            }
            const data = await response.json();
            this._csrfToken = data.csrf_token;
            this._csrfTokenTimestamp = Date.now();
            return this._csrfToken;
        } catch (error) {
            console.warn('Could not fetch CSRF token:', error.message);
            return null;
        }
    }

    /**
     * Obtiene el token CSRF, refrescando si es necesario
     * @returns {Promise<string|null>} Token CSRF o null si no se puede obtener
     */
    async getCsrfToken() {
        const now = Date.now();
        const tokenAge = now - this._csrfTokenTimestamp;

        // Si el token no existe o ha expirado, obtener uno nuevo
        if (!this._csrfToken || tokenAge > this._csrfTokenTTL) {
            return await this._fetchCsrfToken();
        }

        return this._csrfToken;
    }

    /**
     * Invalida el token CSRF cacheado
     */
    invalidateCsrfToken() {
        this._csrfToken = null;
        this._csrfTokenTimestamp = 0;
    }

    /**
     * Obtiene los headers necesarios para una peticion, incluyendo CSRF si es necesario
     * @param {string} method - Metodo HTTP
     * @param {Object} existingHeaders - Headers existentes
     * @returns {Promise<Object>} Headers con CSRF token si es necesario
     * @private
     */
    async _getRequestHeaders(method, existingHeaders = {}) {
        const headers = { ...existingHeaders };

        // Solo agregar CSRF para metodos mutantes si no hay Authorization header
        if (this._mutatingMethods.has(method.toUpperCase()) && !headers['Authorization']) {
            const csrfToken = await this.getCsrfToken();
            if (csrfToken) {
                headers['X-CSRF-Token'] = csrfToken;
            }
        }

        return headers;
    }

    /**
     * Realiza una petición fetch con timeout usando AbortController
     * Incluye automáticamente el token CSRF para métodos POST/PUT/DELETE/PATCH
     * @param {string} url - URL de la petición
     * @param {Object} options - Opciones de fetch (method, headers, body, etc.)
     * @param {number} timeout - Timeout en milisegundos (default: 30000)
     * @returns {Promise<Response>} - Respuesta del fetch
     * @throws {Error} - Error de timeout o de red
     * @private
     */
    async _fetchWithTimeout(url, options = {}, timeout = this.defaultTimeout) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        // Obtener el metodo HTTP (default GET)
        const method = (options.method || 'GET').toUpperCase();

        // Agregar headers CSRF para metodos mutantes
        const headers = await this._getRequestHeaders(method, options.headers || {});

        try {
            const response = await fetch(url, {
                ...options,
                headers,
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            // Si recibimos 403 por CSRF, invalidar token y reintentar una vez
            if (response.status === 403) {
                const errorData = await response.clone().json().catch(() => ({}));
                if (errorData.error_code === 'CSRF_TOKEN_MISSING' ||
                    errorData.error_code === 'CSRF_TOKEN_INVALID') {
                    console.warn('CSRF token rejected, refreshing...');
                    this.invalidateCsrfToken();

                    // Reintentar con token fresco
                    const freshHeaders = await this._getRequestHeaders(method, options.headers || {});
                    const retryResponse = await fetch(url, {
                        ...options,
                        headers: freshHeaders,
                        signal: controller.signal
                    });
                    return retryResponse;
                }
            }

            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout: El servidor no responde');
            }
            throw error;
        }
    }

    /**
     * Obtiene empleados desde el API
     * @param {number|null} year - Año para filtrar (opcional)
     * @param {boolean} activeOnly - Solo empleados activos
     * @param {Object} state - Objeto de estado de la aplicación
     * @param {Function} updateUI - Función para actualizar UI
     * @param {Function} showToast - Función para mostrar notificaciones
     * @returns {Promise<void>}
     */
    async fetchEmployees(year = null, activeOnly = true, state = null, updateUI = null, showToast = null) {
        // Incrementar ID de request para trackear este request específico
        const requestId = ++this._fetchRequestId;

        try {
            // Usar endpoint mejorado con tipo de empleado y estado activo
            let url = `${this.apiBase}/employees?enhanced=true&active_only=${activeOnly}`;
            if (year) url += `&year=${year}`;

            const res = await this._fetchWithTimeout(url);

            // Verificar si este request sigue siendo el más reciente
            if (requestId !== this._fetchRequestId) {
                console.log('Ignorando respuesta obsoleta para año:', year);
                return;
            }

            const json = await res.json();

            // Si se proporciona el objeto state, actualizarlo
            if (state) {
                state.data = json.data.map(emp => ({
                    ...emp,
                    employeeNum: emp.employee_num,
                    usageRate: emp.granted > 0 ? Math.round((emp.used / emp.granted) * 100) : 0,
                    employeeType: emp.employee_type || 'staff',
                    employmentStatus: emp.employment_status || '在職中',
                    isActive: emp.is_active === 1 || emp.is_active === true
                }));
                state.availableYears = json.available_years;

                // Selección inteligente de año
                if (state.availableYears.length > 0 && !state.year) {
                    const currentYear = new Date().getFullYear();
                    if (state.availableYears.includes(currentYear)) {
                        state.year = currentYear;
                    } else if (state.availableYears.includes(currentYear - 1)) {
                        state.year = currentYear - 1;
                    } else {
                        state.year = state.availableYears[0];
                    }

                    // Si no se pasó year, refetch con el año seleccionado
                    if (!year) {
                        return this.fetchEmployees(state.year, activeOnly, state, updateUI, showToast);
                    }
                }
            }

            // Verificación final antes de actualizar UI
            if (requestId !== this._fetchRequestId) {
                return;
            }

            // Actualizar UI si se proporciona la función
            if (updateUI && typeof updateUI === 'function') {
                await updateUI();
            }

            // Mostrar notificación si se proporciona
            if (showToast && typeof showToast === 'function') {
                showToast('success', 'Data refresh complete');
            }

        } catch (err) {
            // Solo mostrar error si este sigue siendo el request actual
            if (requestId === this._fetchRequestId) {
                console.error(err);
                if (showToast && typeof showToast === 'function') {
                    if (err.message.includes('timeout')) {
                        showToast('error', '⏱️ タイムアウト: サーバーが応答しません', 6000);
                    } else {
                        showToast('error', 'Failed to load data');
                    }
                }
            }
        }
    }

    /**
     * Sincroniza datos de vacaciones desde Excel
     * @param {Function} setBtnLoading - Función para gestionar estado de loading del botón
     * @param {Function} showToast - Función para mostrar notificaciones
     * @param {Function} refetchData - Función para recargar datos después del sync
     * @returns {Promise<void>}
     */
    async sync(setBtnLoading = null, showToast = null, refetchData = null) {
        const btn = document.getElementById('btn-sync-main');

        if (setBtnLoading && typeof setBtnLoading === 'function') {
            setBtnLoading(btn, true);
        }

        try {
            const res = await this._fetchWithTimeout(`${this.apiBase}/sync`, { method: 'POST' });

            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(errorText || `Server error: ${res.status}`);
            }

            const json = await res.json();

            if (showToast && typeof showToast === 'function') {
                showToast('success', `✅ ${json.count}件の有給データを同期しました`, 5000);
            }

            // Recargar datos si se proporciona la función
            if (refetchData && typeof refetchData === 'function') {
                await refetchData();
            }

        } catch (err) {
            console.error('Sync error:', err);

            if (showToast && typeof showToast === 'function') {
                if (err.message.includes('timeout')) {
                    showToast('error', '⏱️ タイムアウト: サーバーが応答しません', 6000);
                } else if (err.message.includes('fetch') || err.name === 'TypeError') {
                    showToast('error', '🌐 ネットワークエラー: サーバーに接続できません', 6000);
                } else {
                    showToast('error', `❌ 同期失敗: ${err.message}`, 6000);
                }
            }
        } finally {
            if (setBtnLoading && typeof setBtnLoading === 'function') {
                setBtnLoading(btn, false);
            }
        }
    }

    /**
     * Sincroniza datos de empleados Genzai (派遣社員)
     * @param {Function} setBtnLoading - Función para gestionar estado de loading
     * @param {Function} showToast - Función para mostrar notificaciones
     * @returns {Promise<void>}
     */
    async syncGenzai(setBtnLoading = null, showToast = null) {
        const btn = document.getElementById('btn-sync-genzai');

        if (setBtnLoading) setBtnLoading(btn, true);

        try {
            const res = await this._fetchWithTimeout(`${this.apiBase}/sync-genzai`, { method: 'POST' });
            if (!res.ok) throw new Error(`Server error: ${res.status}`);

            const json = await res.json();

            if (showToast) {
                showToast('success', `✅ 派遣社員データを同期しました (${json.count || 0}件)`, 5000);
            }
        } catch (err) {
            console.error('Genzai sync error:', err);
            if (showToast) {
                if (err.message.includes('timeout')) {
                    showToast('error', '⏱️ タイムアウト: サーバーが応答しません', 6000);
                } else {
                    showToast('error', '❌ 派遣社員の同期に失敗しました', 6000);
                }
            }
        } finally {
            if (setBtnLoading) setBtnLoading(btn, false);
        }
    }

    /**
     * Sincroniza datos de empleados Ukeoi (請負社員)
     * @param {Function} setBtnLoading - Función para gestionar estado de loading
     * @param {Function} showToast - Función para mostrar notificaciones
     * @returns {Promise<void>}
     */
    async syncUkeoi(setBtnLoading = null, showToast = null) {
        const btn = document.getElementById('btn-sync-ukeoi');

        if (setBtnLoading) setBtnLoading(btn, true);

        try {
            const res = await this._fetchWithTimeout(`${this.apiBase}/sync-ukeoi`, { method: 'POST' });
            if (!res.ok) throw new Error(`Server error: ${res.status}`);

            const json = await res.json();

            if (showToast) {
                showToast('success', `✅ 請負社員データを同期しました (${json.count || 0}件)`, 5000);
            }
        } catch (err) {
            console.error('Ukeoi sync error:', err);
            if (showToast) {
                if (err.message.includes('timeout')) {
                    showToast('error', '⏱️ タイムアウト: サーバーが応答しません', 6000);
                } else {
                    showToast('error', '❌ 請負社員の同期に失敗しました', 6000);
                }
            }
        } finally {
            if (setBtnLoading) setBtnLoading(btn, false);
        }
    }

    /**
     * Obtiene datos filtrados por año
     * @param {Array} data - Array de datos completos
     * @param {number|null} year - Año para filtrar
     * @returns {Array} - Datos filtrados
     */
    getFiltered(data, year = null) {
        if (!year) return data;
        return data.filter(e => e.year === year);
    }

    /**
     * Obtiene estadísticas por fábrica
     * @param {Array} data - Array de datos de empleados
     * @returns {Array<[string, number]>} - Array de tuplas [factory, daysUsed] ordenado
     */
    getFactoryStats(data) {
        const stats = {};

        data.forEach(e => {
            const f = e.haken;
            // Filtrar fábricas sin nombre válido
            if (!f || f === '0' || f === 'Unknown' || f.trim() === '' || f === 'null') {
                return;
            }
            if (!stats[f]) stats[f] = 0;
            stats[f] += e.used;
        });

        return Object.entries(stats).sort((a, b) => b[1] - a[1]);
    }
}

/**
 * Instancia singleton para compatibilidad con código legacy
 */
export const dataService = new DataService();

export default dataService;
