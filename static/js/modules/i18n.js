/**
 * YuKyu Internationalization (i18n) Module
 * Handles translations and locale management.
 */

export const I18n = {
    currentLocale: 'ja',
    translations: {},
    supportedLocales: ['ja', 'es', 'en'],
    storageKey: 'yukyu-locale',
    localesPath: '/static/locales',
    isInitialized: false,

    localeInfo: {
        ja: { name: 'Japanese', nativeName: 'Japanese', flag: 'JP', code: 'JA' },
        es: { name: 'Spanish', nativeName: 'Castellano', flag: 'ES', code: 'ES' },
        en: { name: 'English', nativeName: 'English', flag: 'EN', code: 'EN' }
    },

    async init() {
        if (this.isInitialized) return;

        const savedLocale = localStorage.getItem(this.storageKey);
        const browserLocale = this.detectBrowserLocale();
        this.currentLocale = savedLocale || browserLocale || 'ja';

        await this.loadTranslations(this.currentLocale);

        document.documentElement.lang = this.currentLocale;
        this.updateDOM();
        this.bindEvents();

        this.isInitialized = true;
    },

    detectBrowserLocale() {
        const browserLang = navigator.language || navigator.userLanguage || '';
        const langCode = browserLang.split('-')[0].toLowerCase();
        return this.supportedLocales.includes(langCode) ? langCode : 'ja';
    },

    async loadTranslations(locale) {
        if (this.translations[locale]) return this.translations[locale];

        try {
            const response = await fetch(`${this.localesPath}/${locale}.json`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const trans = await response.json();
            this.translations[locale] = trans;
            return trans;
        } catch (error) {
            console.warn(`Failed to load ${locale}`, error);
            if (locale !== 'ja') return this.loadTranslations('ja');
            return {};
        }
    },

    t(key, params = {}) {
        const translations = this.translations[this.currentLocale] || {};
        let value = this.getNestedValue(translations, key);

        if (value === undefined && this.currentLocale !== 'ja') {
            const jaTranslations = this.translations['ja'] || {};
            value = this.getNestedValue(jaTranslations, key);
        }

        if (value === undefined) return key;

        return this.interpolate(value, params);
    },

    getNestedValue(obj, key) {
        return key.split('.').reduce((prev, curr) => {
            return (prev && prev[curr] !== undefined) ? prev[curr] : undefined;
        }, obj);
    },

    interpolate(template, params) {
        if (!params || typeof template !== 'string') return template;
        return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return params.hasOwnProperty(key) ? params[key] : match;
        });
    },

    updateDOM() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = this.t(key);
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.t(key);
        });

        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            el.title = this.t(key);
        });

        // Update selector UI if exists
        const flagEl = document.getElementById('current-lang-flag');
        const codeEl = document.getElementById('current-lang-code');
        if (flagEl) flagEl.textContent = this.localeInfo[this.currentLocale].flag;
        if (codeEl) codeEl.textContent = this.localeInfo[this.currentLocale].code;
    },

    bindEvents() {
        // Event delegation for language options
        document.addEventListener('click', async (e) => {
            const option = e.target.closest('.language-option');
            if (option) {
                const locale = option.dataset.locale;
                if (locale) await this.setLocale(locale);

                // Close dropdown logic here if needed, or handle in central UI handler
                const selector = document.getElementById('language-selector');
                if (selector) selector.classList.remove('open');
            }
        });
    },

    async setLocale(locale) {
        if (!this.supportedLocales.includes(locale)) return;
        if (locale === this.currentLocale) return;

        await this.loadTranslations(locale);
        this.currentLocale = locale;
        localStorage.setItem(this.storageKey, locale);
        document.documentElement.lang = locale;

        this.updateDOM();
        window.dispatchEvent(new CustomEvent('i18n:change', { detail: { locale } }));
    }
};
