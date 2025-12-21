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
 * Objeto Utils para compatibilidad con código legacy
 */
export const Utils = {
    escapeHtml,
    escapeAttr,
    safeNumber,
    isValidYear,
    isValidString,
    formatNumber
};

export default Utils;
