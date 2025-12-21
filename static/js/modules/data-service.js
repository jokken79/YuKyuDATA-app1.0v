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
    constructor(apiBase = 'http://localhost:8000/api') {
        /** @type {string} URL base del API */
        this.apiBase = apiBase;

        /** @type {number} Contador de requests para prevenir race conditions */
        this._fetchRequestId = 0;
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

            const res = await fetch(url);

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
                    showToast('error', 'Failed to load data');
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
            const res = await fetch(`${this.apiBase}/sync`, { method: 'POST' });

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
                if (err.message.includes('fetch') || err.name === 'TypeError') {
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
            const res = await fetch(`${this.apiBase}/sync-genzai`, { method: 'POST' });
            if (!res.ok) throw new Error(`Server error: ${res.status}`);

            const json = await res.json();

            if (showToast) {
                showToast('success', `✅ 派遣社員データを同期しました (${json.count || 0}件)`, 5000);
            }
        } catch (err) {
            console.error('Genzai sync error:', err);
            if (showToast) {
                showToast('error', '❌ 派遣社員の同期に失敗しました', 6000);
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
            const res = await fetch(`${this.apiBase}/sync-ukeoi`, { method: 'POST' });
            if (!res.ok) throw new Error(`Server error: ${res.status}`);

            const json = await res.json();

            if (showToast) {
                showToast('success', `✅ 請負社員データを同期しました (${json.count || 0}件)`, 5000);
            }
        } catch (err) {
            console.error('Ukeoi sync error:', err);
            if (showToast) {
                showToast('error', '❌ 請負社員の同期に失敗しました', 6000);
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
