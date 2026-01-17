/**
 * Animation Loader Module - Lazy loading para GSAP y Animate.css
 * Optimiza Time to Interactive cargando animaciones bajo demanda
 * @module animation-loader
 */

/**
 * URLs de las bibliotecas de animacion
 */
const GSAP_CDN = {
    core: 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js',
    scrollTrigger: 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js',
    scrollToPlugin: 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollToPlugin.min.js'
};

const ANIMATE_CSS_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css';

/**
 * Estado de carga de las bibliotecas
 */
const loadState = {
    gsapCore: false,
    gsapScrollTrigger: false,
    gsapScrollToPlugin: false,
    animateCss: false,
    loading: {
        gsap: false,
        animateCss: false
    }
};

/**
 * Promesas de carga para evitar cargas duplicadas
 */
let gsapLoadPromise = null;
let animateCssLoadPromise = null;

/**
 * Carga un script dinamicamente
 * @param {string} url - URL del script
 * @returns {Promise} - Resuelve cuando el script esta cargado
 */
function loadScript(url) {
    return new Promise((resolve, reject) => {
        // Verificar si ya existe
        const existing = document.querySelector(`script[src="${url}"]`);
        if (existing) {
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = url;
        script.async = true;
        script.onload = resolve;
        script.onerror = () => reject(new Error(`Failed to load script: ${url}`));
        document.head.appendChild(script);
    });
}

/**
 * Carga un stylesheet dinamicamente
 * @param {string} url - URL del stylesheet
 * @returns {Promise} - Resuelve cuando el stylesheet esta cargado
 */
function loadStylesheet(url) {
    return new Promise((resolve, reject) => {
        // Verificar si ya existe
        const existing = document.querySelector(`link[href="${url}"]`);
        if (existing) {
            resolve();
            return;
        }

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        link.onload = resolve;
        link.onerror = () => reject(new Error(`Failed to load stylesheet: ${url}`));
        document.head.appendChild(link);
    });
}

/**
 * AnimationLoader - Gestor de carga diferida para bibliotecas de animacion
 */
export const AnimationLoader = {
    /**
     * Verifica si GSAP esta cargado
     * @returns {boolean}
     */
    get gsapLoaded() {
        return typeof window.gsap !== 'undefined';
    },

    /**
     * Verifica si ScrollTrigger esta cargado
     * @returns {boolean}
     */
    get scrollTriggerLoaded() {
        return typeof window.ScrollTrigger !== 'undefined';
    },

    /**
     * Verifica si ScrollToPlugin esta cargado
     * @returns {boolean}
     */
    get scrollToPluginLoaded() {
        return typeof window.ScrollToPlugin !== 'undefined';
    },

    /**
     * Verifica si Animate.css esta cargado
     * @returns {boolean}
     */
    get animateCssLoaded() {
        return loadState.animateCss || document.querySelector(`link[href*="animate.css"]`) !== null;
    },

    /**
     * Carga GSAP core
     * @returns {Promise<gsap>} - Objeto gsap
     */
    async loadGSAPCore() {
        if (this.gsapLoaded) {
            return window.gsap;
        }

        await loadScript(GSAP_CDN.core);
        loadState.gsapCore = true;
        return window.gsap;
    },

    /**
     * Carga GSAP con todos los plugins necesarios
     * @param {Object} options - Opciones de carga
     * @param {boolean} options.scrollTrigger - Cargar ScrollTrigger
     * @param {boolean} options.scrollToPlugin - Cargar ScrollToPlugin
     * @returns {Promise<gsap>} - Objeto gsap con plugins registrados
     */
    async loadGSAP(options = { scrollTrigger: true, scrollToPlugin: true }) {
        // Reutilizar promesa existente si ya esta cargando
        if (gsapLoadPromise && loadState.loading.gsap) {
            return gsapLoadPromise;
        }

        // Ya cargado
        if (this.gsapLoaded &&
            (!options.scrollTrigger || this.scrollTriggerLoaded) &&
            (!options.scrollToPlugin || this.scrollToPluginLoaded)) {
            return window.gsap;
        }

        loadState.loading.gsap = true;

        gsapLoadPromise = (async () => {
            try {
                // Cargar GSAP core primero
                await this.loadGSAPCore();

                // Cargar plugins en paralelo
                const pluginPromises = [];

                if (options.scrollTrigger && !this.scrollTriggerLoaded) {
                    pluginPromises.push(
                        loadScript(GSAP_CDN.scrollTrigger).then(() => {
                            loadState.gsapScrollTrigger = true;
                        })
                    );
                }

                if (options.scrollToPlugin && !this.scrollToPluginLoaded) {
                    pluginPromises.push(
                        loadScript(GSAP_CDN.scrollToPlugin).then(() => {
                            loadState.gsapScrollToPlugin = true;
                        })
                    );
                }

                await Promise.all(pluginPromises);

                // Registrar plugins
                if (window.gsap) {
                    const plugins = [];
                    if (window.ScrollTrigger) plugins.push(window.ScrollTrigger);
                    if (window.ScrollToPlugin) plugins.push(window.ScrollToPlugin);
                    if (plugins.length > 0) {
                        window.gsap.registerPlugin(...plugins);
                    }
                }

                loadState.loading.gsap = false;
                return window.gsap;
            } catch (error) {
                loadState.loading.gsap = false;
                console.error('[AnimationLoader] Error loading GSAP:', error);
                throw error;
            }
        })();

        return gsapLoadPromise;
    },

    /**
     * Carga Animate.css
     * @returns {Promise<void>}
     */
    async loadAnimateCSS() {
        if (this.animateCssLoaded) {
            return;
        }

        // Reutilizar promesa existente
        if (animateCssLoadPromise && loadState.loading.animateCss) {
            return animateCssLoadPromise;
        }

        loadState.loading.animateCss = true;

        animateCssLoadPromise = (async () => {
            try {
                await loadStylesheet(ANIMATE_CSS_CDN);
                loadState.animateCss = true;
                loadState.loading.animateCss = false;
            } catch (error) {
                loadState.loading.animateCss = false;
                console.error('[AnimationLoader] Error loading Animate.css:', error);
                throw error;
            }
        })();

        return animateCssLoadPromise;
    },

    /**
     * Carga todas las bibliotecas de animacion
     * @returns {Promise<{gsap: gsap, animateCss: boolean}>}
     */
    async loadAll() {
        const [gsap] = await Promise.all([
            this.loadGSAP(),
            this.loadAnimateCSS()
        ]);

        return { gsap, animateCss: true };
    },

    /**
     * Ejecuta una animacion GSAP de forma segura
     * Carga la biblioteca si es necesario
     * @param {Function} animationFn - Funcion que usa gsap
     * @param {Object} fallbackFn - Funcion fallback si falla la carga
     * @returns {Promise}
     */
    async withGSAP(animationFn, fallbackFn = null) {
        // Verificar preferencia de reduccion de movimiento
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            if (fallbackFn) fallbackFn();
            return;
        }

        try {
            const gsap = await this.loadGSAP();
            await animationFn(gsap);
        } catch (error) {
            console.warn('[AnimationLoader] GSAP not available, using fallback');
            if (fallbackFn) fallbackFn();
        }
    },

    /**
     * Aplica una clase de Animate.css a un elemento
     * Carga la biblioteca si es necesario
     * @param {HTMLElement} element - Elemento a animar
     * @param {string} animationName - Nombre de la animacion (sin prefijo animate__)
     * @param {Object} options - Opciones adicionales
     * @returns {Promise<void>}
     */
    async animateElement(element, animationName, options = {}) {
        const {
            duration = null,
            delay = null,
            onComplete = null
        } = options;

        // Verificar preferencia de reduccion de movimiento
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            if (onComplete) onComplete();
            return;
        }

        try {
            await this.loadAnimateCSS();

            // Configurar duracion y delay si se especifican
            if (duration) {
                element.style.setProperty('--animate-duration', duration);
            }
            if (delay) {
                element.style.setProperty('--animate-delay', delay);
            }

            // Agregar clases de animacion
            element.classList.add('animate__animated', `animate__${animationName}`);

            // Manejar fin de animacion
            const handleAnimationEnd = () => {
                element.classList.remove('animate__animated', `animate__${animationName}`);
                element.removeEventListener('animationend', handleAnimationEnd);
                if (onComplete) onComplete();
            };

            element.addEventListener('animationend', handleAnimationEnd, { once: true });
        } catch (error) {
            console.warn('[AnimationLoader] Animate.css not available');
            if (onComplete) onComplete();
        }
    },

    /**
     * Precarga las bibliotecas en segundo plano usando requestIdleCallback
     * Util para cargar durante tiempo idle del navegador
     */
    preloadInBackground() {
        const preload = () => {
            // Solo precargar si no hay preferencia de reduccion de movimiento
            if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                // Precargar GSAP con baja prioridad
                this.loadGSAP().catch(() => {
                    // Silenciar error de precarga
                });
                // Precargar Animate.css
                this.loadAnimateCSS().catch(() => {
                    // Silenciar error de precarga
                });
            }
        };

        if ('requestIdleCallback' in window) {
            requestIdleCallback(preload, { timeout: 5000 });
        } else {
            // Fallback para navegadores sin requestIdleCallback
            setTimeout(preload, 2000);
        }
    },

    /**
     * Configura un IntersectionObserver para cargar animaciones cuando
     * un elemento es visible
     * @param {string} selector - Selector CSS de elementos a observar
     * @param {Function} animationFn - Funcion que ejecuta la animacion
     * @returns {IntersectionObserver}
     */
    observeForAnimation(selector, animationFn) {
        const elements = document.querySelectorAll(selector);

        if (elements.length === 0) {
            return null;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.withGSAP(
                            (gsap) => animationFn(entry.target, gsap),
                            () => {
                                // Fallback: mostrar elemento sin animacion
                                entry.target.style.opacity = '1';
                                entry.target.style.transform = 'none';
                            }
                        );
                        observer.unobserve(entry.target);
                    }
                });
            },
            {
                rootMargin: '50px',
                threshold: 0.1
            }
        );

        elements.forEach(el => observer.observe(el));
        return observer;
    },

    /**
     * Obtiene el estado de carga actual
     * @returns {Object}
     */
    getLoadState() {
        return {
            gsapCore: this.gsapLoaded,
            scrollTrigger: this.scrollTriggerLoaded,
            scrollToPlugin: this.scrollToPluginLoaded,
            animateCss: this.animateCssLoaded
        };
    }
};

/**
 * Fallback functions para cuando las animaciones no estan disponibles
 */
export const AnimationFallbacks = {
    /**
     * Muestra un elemento sin animacion
     * @param {HTMLElement|string} element - Elemento o selector
     */
    showElement(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.style.opacity = '1';
            el.style.transform = 'none';
            el.style.visibility = 'visible';
        }
    },

    /**
     * Oculta un elemento sin animacion
     * @param {HTMLElement|string} element - Elemento o selector
     */
    hideElement(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.style.opacity = '0';
            el.style.visibility = 'hidden';
        }
    },

    /**
     * Muestra multiples elementos sin animacion
     * @param {string} selector - Selector CSS
     */
    showElements(selector) {
        document.querySelectorAll(selector).forEach(el => {
            el.style.opacity = '1';
            el.style.transform = 'none';
        });
    },

    /**
     * Simula animacion de contador sin GSAP
     * @param {HTMLElement} element - Elemento del contador
     * @param {number} targetValue - Valor final
     * @param {string} suffix - Sufijo (ej: '%')
     * @param {number} duration - Duracion en ms
     */
    animateCounter(element, targetValue, suffix = '', duration = 1000) {
        const startValue = 0;
        const startTime = performance.now();

        const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out quad
            const easeProgress = 1 - (1 - progress) * (1 - progress);
            const currentValue = Math.round(startValue + (targetValue - startValue) * easeProgress);

            element.textContent = currentValue.toLocaleString() + suffix;

            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            }
        };

        requestAnimationFrame(updateCounter);
    }
};

/**
 * Helper para verificar si las animaciones estan habilitadas
 * @returns {boolean}
 */
export function isAnimationEnabled() {
    return !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Export por defecto
 */
export default AnimationLoader;
