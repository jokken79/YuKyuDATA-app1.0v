/**
 * Utils Module - Security & Validation Utilities
 * Funciones para prevención de XSS y validación de datos
 * @module utils
 */

/**
 * Escapa HTML para prevenir ataques XSS
 * @param {*} str - String a escapar
 * @returns {string} - String escapado
 */
export function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

/**
 * Escapa valores de atributos HTML
 * @param {*} str - String a escapar
 * @returns {string} - String escapado para atributos
 */
export function escapeAttr(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/'/g, '&#39;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

/**
 * Convierte de forma segura un valor a número
 * @param {*} val - Valor a convertir
 * @param {number} defaultVal - Valor por defecto si la conversión falla
 * @returns {number} - Número válido o valor por defecto
 */
export function safeNumber(val, defaultVal = 0) {
    const num = parseFloat(val);
    return Number.isFinite(num) ? num : defaultVal;
}

/**
 * Valida que un año esté en un rango aceptable
 * @param {number|string} year - Año a validar
 * @returns {boolean} - true si el año es válido
 */
export function isValidYear(year) {
    const num = parseInt(year);
    return Number.isInteger(num) && num >= 2000 && num <= 2100;
}

/**
 * Valida que un string no esté vacío
 * @param {*} str - String a validar
 * @returns {boolean} - true si el string es válido
 */
export function isValidString(str) {
    return str !== null && str !== undefined && String(str).trim() !== '';
}

/**
 * Formatea un número con separadores de miles
 * @param {number} num - Número a formatear
 * @param {number} decimals - Número de decimales
 * @returns {string} - Número formateado
 */
export function formatNumber(num, decimals = 0) {
    const n = safeNumber(num);
    return decimals > 0 ? n.toFixed(decimals) : n.toLocaleString();
}

/**
 * Debounce - Retrasa la ejecución de una función hasta que pase un tiempo sin llamadas
 * Ideal para: búsquedas, validación en tiempo real, resize events
 * @param {Function} func - Función a ejecutar
 * @param {number} delay - Delay en milisegundos (default: 300ms)
 * @returns {Function} - Función debounced
 */
export function debounce(func, delay = 300) {
    let timeoutId = null;

    return function debounced(...args) {
        const context = this;

        // Limpiar timeout previo
        if (timeoutId) {
            clearTimeout(timeoutId);
        }

        // Configurar nuevo timeout
        timeoutId = setTimeout(() => {
            func.apply(context, args);
            timeoutId = null;
        }, delay);
    };
}

/**
 * Throttle - Limita la frecuencia de ejecución de una función
 * Ideal para: scroll events, mouse move, input rápido
 * @param {Function} func - Función a ejecutar
 * @param {number} limit - Tiempo mínimo entre ejecuciones en ms (default: 150ms)
 * @returns {Function} - Función throttled
 */
export function throttle(func, limit = 150) {
    let inThrottle = false;
    let lastResult;

    return function throttled(...args) {
        const context = this;

        if (!inThrottle) {
            lastResult = func.apply(context, args);
            inThrottle = true;

            setTimeout(() => {
                inThrottle = false;
            }, limit);
        }

        return lastResult;
    };
}

/**
 * RequestAnimationFrame wrapper para throttling de animaciones
 * Más eficiente que throttle para operaciones visuales
 * @param {Function} func - Función a ejecutar
 * @returns {Function} - Función que usa RAF
 */
export function rafThrottle(func) {
    let rafId = null;

    return function rafThrottled(...args) {
        const context = this;

        if (rafId) {
            return;
        }

        rafId = requestAnimationFrame(() => {
            func.apply(context, args);
            rafId = null;
        });
    };
}

/**
 * Debounce con opción de ejecución inmediata (leading edge)
 * @param {Function} func - Función a ejecutar
 * @param {number} delay - Delay en milisegundos
 * @param {boolean} immediate - Si debe ejecutarse inmediatamente
 * @returns {Function} - Función debounced
 */
export function debounceImmediate(func, delay = 300, immediate = false) {
    let timeoutId = null;

    return function debouncedImmediate(...args) {
        const context = this;
        const callNow = immediate && !timeoutId;

        if (timeoutId) {
            clearTimeout(timeoutId);
        }

        timeoutId = setTimeout(() => {
            timeoutId = null;
            if (!immediate) {
                func.apply(context, args);
            }
        }, delay);

        if (callNow) {
            func.apply(context, args);
        }
    };
}

/**
 * Crea un debouncer cancelable
 * @param {Function} func - Función a ejecutar
 * @param {number} delay - Delay en milisegundos
 * @returns {Object} - Objeto con métodos execute y cancel
 */
export function createCancelableDebounce(func, delay = 300) {
    let timeoutId = null;

    return {
        execute(...args) {
            const context = this;

            if (timeoutId) {
                clearTimeout(timeoutId);
            }

            timeoutId = setTimeout(() => {
                func.apply(context, args);
                timeoutId = null;
            }, delay);
        },

        cancel() {
            if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
        },

        isPending() {
            return timeoutId !== null;
        }
    };
}

/**
 * Detecta si el usuario prefiere reducir movimiento (a11y)
 * @returns {boolean} - true si prefiere movimiento reducido
 */
export function prefersReducedMotion() {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    return mediaQuery.matches;
}

/**
 * Obtiene el delay de animación apropiado según preferencias
 * @param {number} normalDelay - Delay normal en ms
 * @returns {number} - Delay ajustado (0 si prefiere movimiento reducido)
 */
export function getAnimationDelay(normalDelay) {
    return prefersReducedMotion() ? 0 : normalDelay;
}

/**
 * Objeto Utils para compatibilidad con código legacy
 */
export const Utils = {
    escapeHtml,
    escapeAttr,
    safeNumber,
    isValidYear,
    isValidString,
    formatNumber,
    debounce,
    throttle,
    rafThrottle,
    debounceImmediate,
    createCancelableDebounce,
    prefersReducedMotion,
    getAnimationDelay
};

export default Utils;
