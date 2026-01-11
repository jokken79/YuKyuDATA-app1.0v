/**
 * Internationalization (i18n) Module
 * Sistema de internacionalizacion para YuKyuDATA-app
 * @module i18n
 */

/**
 * Clase Singleton para gestionar traducciones
 */
class I18n {
    /**
     * Crea una nueva instancia de I18n
     */
    constructor() {
        if (I18n.instance) {
            return I18n.instance;
        }

        /** @type {string} Idioma actual */
        this.currentLocale = 'ja';

        /** @type {Object} Cache de traducciones cargadas */
        this.translations = {};

        /** @type {string[]} Idiomas soportados */
        this.supportedLocales = ['ja', 'es', 'en'];

        /** @type {string} Clave de localStorage */
        this.storageKey = 'yukyu-locale';

        /** @type {string} Ruta base para archivos de traduccion */
        this.localesPath = '/static/locales';

        /** @type {boolean} Flag de inicializacion */
        this.isInitialized = false;

        /** @type {Function[]} Callbacks para cambios de idioma */
        this.changeListeners = [];

        I18n.instance = this;
    }

    /**
     * Inicializa el sistema de i18n
     * @returns {Promise<void>}
     */
    async init() {
        if (this.isInitialized) {
            return;
        }

        // Cargar idioma guardado o detectar del navegador
        const savedLocale = localStorage.getItem(this.storageKey);
        const browserLocale = this.detectBrowserLocale();

        this.currentLocale = savedLocale || browserLocale || 'ja';

        // Cargar traducciones del idioma actual
        await this.loadTranslations(this.currentLocale);

        this.isInitialized = true;
        console.log(`i18n initialized with locale: ${this.currentLocale}`);
    }

    /**
     * Detecta el idioma preferido del navegador
     * @returns {string} Codigo de idioma detectado
     */
    detectBrowserLocale() {
        const browserLang = navigator.language || navigator.userLanguage || '';
        const langCode = browserLang.split('-')[0].toLowerCase();

        // Mapear codigos de idioma a nuestros soportados
        if (langCode === 'ja') return 'ja';
        if (langCode === 'es') return 'es';
        if (langCode === 'en') return 'en';

        // Default a japones (idioma principal de la app)
        return 'ja';
    }

    /**
     * Carga las traducciones de un idioma
     * @param {string} locale - Codigo de idioma (ja, es, en)
     * @returns {Promise<Object>} Traducciones cargadas
     */
    async loadTranslations(locale) {
        // Validar locale
        if (!this.supportedLocales.includes(locale)) {
            console.warn(`Locale "${locale}" not supported. Using "ja".`);
            locale = 'ja';
        }

        // Usar cache si ya esta cargado
        if (this.translations[locale]) {
            return this.translations[locale];
        }

        try {
            const response = await fetch(`${this.localesPath}/${locale}.json`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const translations = await response.json();
            this.translations[locale] = translations;

            console.log(`Loaded translations for: ${locale}`);
            return translations;

        } catch (error) {
            console.error(`Failed to load translations for ${locale}:`, error);

            // Fallback a traducciones por defecto
            if (locale !== 'ja') {
                return this.loadTranslations('ja');
            }

            // Si falla japones, usar objeto vacio
            this.translations[locale] = {};
            return {};
        }
    }

    /**
     * Cambia el idioma actual
     * @param {string} locale - Codigo de idioma (ja, es, en)
     * @returns {Promise<void>}
     */
    async setLocale(locale) {
        if (!this.supportedLocales.includes(locale)) {
            console.warn(`Locale "${locale}" not supported.`);
            return;
        }

        if (locale === this.currentLocale) {
            return;
        }

        // Cargar traducciones si no estan en cache
        await this.loadTranslations(locale);

        this.currentLocale = locale;
        localStorage.setItem(this.storageKey, locale);

        // Actualizar atributo lang del documento
        document.documentElement.lang = locale;

        // Notificar a todos los listeners
        this.notifyListeners();

        console.log(`Locale changed to: ${locale}`);
    }

    /**
     * Obtiene el idioma actual
     * @returns {string} Codigo de idioma actual
     */
    getLocale() {
        return this.currentLocale;
    }

    /**
     * Obtiene los idiomas soportados
     * @returns {string[]} Array de codigos de idioma
     */
    getSupportedLocales() {
        return this.supportedLocales;
    }

    /**
     * Traduce una clave con interpolacion de parametros
     * @param {string} key - Clave de traduccion (ej: "nav.dashboard")
     * @param {Object} params - Parametros para interpolacion
     * @returns {string} Texto traducido
     */
    t(key, params = {}) {
        const translations = this.translations[this.currentLocale] || {};

        // Navegar por la clave con notacion de punto
        let value = this.getNestedValue(translations, key);

        // Si no existe, intentar con fallback a japones
        if (value === undefined && this.currentLocale !== 'ja') {
            const jaTranslations = this.translations['ja'] || {};
            value = this.getNestedValue(jaTranslations, key);
        }

        // Si aun no existe, retornar la clave
        if (value === undefined) {
            console.warn(`Translation key not found: ${key}`);
            return key;
        }

        // Interpolar parametros
        return this.interpolate(value, params);
    }

    /**
     * Obtiene un valor anidado de un objeto usando notacion de punto
     * @param {Object} obj - Objeto fuente
     * @param {string} key - Clave con notacion de punto (ej: "nav.dashboard")
     * @returns {*} Valor encontrado o undefined
     */
    getNestedValue(obj, key) {
        const keys = key.split('.');
        let current = obj;

        for (const k of keys) {
            if (current === null || current === undefined) {
                return undefined;
            }
            current = current[k];
        }

        return current;
    }

    /**
     * Interpola parametros en un string
     * @param {string} template - String con placeholders {{param}}
     * @param {Object} params - Objeto con valores para reemplazar
     * @returns {string} String interpolado
     */
    interpolate(template, params) {
        if (!params || typeof template !== 'string') {
            return template;
        }

        return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return params.hasOwnProperty(key) ? params[key] : match;
        });
    }

    /**
     * Registra un callback para cambios de idioma
     * @param {Function} callback - Funcion a ejecutar cuando cambia el idioma
     * @returns {Function} Funcion para eliminar el listener
     */
    onLocaleChange(callback) {
        if (typeof callback === 'function') {
            this.changeListeners.push(callback);
        }

        // Retornar funcion para eliminar el listener
        return () => {
            const index = this.changeListeners.indexOf(callback);
            if (index > -1) {
                this.changeListeners.splice(index, 1);
            }
        };
    }

    /**
     * Notifica a todos los listeners de cambio de idioma
     */
    notifyListeners() {
        const locale = this.currentLocale;
        this.changeListeners.forEach(callback => {
            try {
                callback(locale);
            } catch (error) {
                console.error('Error in locale change listener:', error);
            }
        });
    }

    /**
     * Actualiza todos los elementos del DOM con atributo data-i18n
     */
    updateDOM() {
        // Actualizar elementos con data-i18n
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);

            if (translation !== key) {
                element.textContent = translation;
            }
        });

        // Actualizar placeholders con data-i18n-placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            const translation = this.t(key);

            if (translation !== key) {
                element.placeholder = translation;
            }
        });

        // Actualizar titles con data-i18n-title
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            const translation = this.t(key);

            if (translation !== key) {
                element.title = translation;
            }
        });

        // Actualizar aria-labels con data-i18n-aria
        document.querySelectorAll('[data-i18n-aria]').forEach(element => {
            const key = element.getAttribute('data-i18n-aria');
            const translation = this.t(key);

            if (translation !== key) {
                element.setAttribute('aria-label', translation);
            }
        });
    }

    /**
     * Obtiene informacion del idioma actual
     * @returns {Object} Informacion del idioma
     */
    getLocaleInfo() {
        const localeInfo = {
            ja: { name: 'Japanese', nativeName: 'Japanese', flag: 'JP', icon: 'JP' },
            es: { name: 'Spanish', nativeName: 'Castellano', flag: 'ES', icon: 'ES' },
            en: { name: 'English', nativeName: 'English', flag: 'US', icon: 'EN' }
        };

        return localeInfo[this.currentLocale] || localeInfo.ja;
    }

    /**
     * Obtiene informacion de todos los idiomas soportados
     * @returns {Object[]} Array de informacion de idiomas
     */
    getAllLocalesInfo() {
        return [
            { code: 'ja', name: 'Japanese', nativeName: 'Japanese', flag: 'JP', icon: 'JP' },
            { code: 'es', name: 'Spanish', nativeName: 'Castellano', flag: 'ES', icon: 'ES' },
            { code: 'en', name: 'English', nativeName: 'English', flag: 'US', icon: 'EN' }
        ];
    }
}

/**
 * Instancia singleton de I18n
 */
const i18n = new I18n();

/**
 * Funcion de atajo para traducir
 * @param {string} key - Clave de traduccion
 * @param {Object} params - Parametros para interpolacion
 * @returns {string} Texto traducido
 */
export const t = (key, params = {}) => i18n.t(key, params);

export { I18n };
export default i18n;
