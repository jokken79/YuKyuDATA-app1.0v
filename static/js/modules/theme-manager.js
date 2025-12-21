/**
 * Theme Manager Module
 * Gestiona el tema (dark/light) de la aplicación
 * @module theme-manager
 */

/**
 * Clase para gestionar temas de la aplicación
 */
export class ThemeManager {
    /**
     * Crea una nueva instancia de ThemeManager
     */
    constructor() {
        /** @type {string} Tema actual (dark o light) */
        this.current = 'dark';

        /** @type {string} Clave de localStorage */
        this.storageKey = 'yukyu-theme';
    }

    /**
     * Inicializa el tema desde localStorage o usa el tema por defecto
     */
    init() {
        const saved = localStorage.getItem(this.storageKey);
        this.current = saved || 'dark';
        this.apply();
    }

    /**
     * Alterna entre modo oscuro y claro
     * @param {Function} showToast - Función opcional para mostrar notificación
     */
    toggle(showToast = null) {
        this.current = this.current === 'dark' ? 'light' : 'dark';
        this.apply();
        localStorage.setItem(this.storageKey, this.current);

        // Notificar cambio si se proporciona función de toast
        if (showToast && typeof showToast === 'function') {
            showToast('info', this.current === 'dark' ? '🌙 ダークモード' : '☀️ ライトモード');
        }
    }

    /**
     * Aplica el tema actual al documento
     */
    apply() {
        document.documentElement.setAttribute('data-theme', this.current);
        this.updateThemeButton();
        this.updateFlatpickr();
    }

    /**
     * Actualiza el botón de tema en el UI
     */
    updateThemeButton() {
        const icon = document.getElementById('theme-icon');
        const label = document.getElementById('theme-label');

        if (icon) {
            icon.textContent = this.current === 'dark' ? '🌙' : '☀️';
        }
        if (label) {
            label.textContent = this.current === 'dark' ? 'Dark' : 'Light';
        }
    }

    /**
     * Actualiza el tema de Flatpickr si está disponible
     */
    updateFlatpickr() {
        // Si existe Flatpickr, actualizar su tema
        if (window.flatpickr) {
            const flatpickrInstances = document.querySelectorAll('.flatpickr-input');
            flatpickrInstances.forEach(input => {
                if (input._flatpickr) {
                    // Recrear instancia con nuevo tema si es necesario
                    const config = input._flatpickr.config;
                    input._flatpickr.destroy();
                    window.flatpickr(input, config);
                }
            });
        }
    }

    /**
     * Obtiene el tema actual
     * @returns {string} - 'dark' o 'light'
     */
    getCurrent() {
        return this.current;
    }

    /**
     * Establece un tema específico
     * @param {string} theme - 'dark' o 'light'
     */
    setTheme(theme) {
        if (theme === 'dark' || theme === 'light') {
            this.current = theme;
            this.apply();
            localStorage.setItem(this.storageKey, this.current);
        }
    }

    /**
     * Verifica si está en modo oscuro
     * @returns {boolean} - true si está en modo oscuro
     */
    isDark() {
        return this.current === 'dark';
    }
}

/**
 * Instancia singleton del ThemeManager para compatibilidad con código legacy
 */
export const themeManager = new ThemeManager();

export default themeManager;
