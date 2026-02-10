/**
 * YuKyu Dashboard v5.3 - Advanced Analytics & Security Enhanced
 */

const App = {
    state: {
        data: [],
        year: null,
        availableYears: [],
        charts: {},
        currentView: 'dashboard',
        typeFilter: 'all',
        fallbackWarnedYear: null
    },

    config: {
        apiBase: '/api/v1'  // MIGRATION: Updated from /api to /api/v1
    },

    // ========================================
    // INTERNATIONALIZATION (i18n) MODULE
    // ========================================
    i18n: {
        currentLocale: 'ja',
        translations: {},
        supportedLocales: ['ja', 'es', 'en'],
        storageKey: 'yukyu-locale',
        localesPath: '/static/locales',
        isInitialized: false,
        changeListeners: [],

        localeInfo: {
            ja: { name: 'Japanese', nativeName: 'Japanese', flag: 'JP', code: 'JA' },
            es: { name: 'Spanish', nativeName: 'Castellano', flag: 'ES', code: 'ES' },
            en: { name: 'English', nativeName: 'English', flag: 'EN', code: 'EN' }
        },

        async init() {
            if (this.isInitialized) return;

            // Load saved locale or detect from browser
            const savedLocale = localStorage.getItem(this.storageKey);
            const browserLocale = this.detectBrowserLocale();
            this.currentLocale = savedLocale || browserLocale || 'ja';

            // Load translations
            await this.loadTranslations(this.currentLocale);

            // Update document lang attribute
            document.documentElement.lang = this.currentLocale;

            // Update UI selector
            this.updateLanguageSelector();

            // Setup event listeners
            this.setupLanguageSelector();

            this.isInitialized = true;
            // i18n initialized with selected locale
        },

        detectBrowserLocale() {
            const browserLang = navigator.language || navigator.userLanguage || '';
            const langCode = browserLang.split('-')[0].toLowerCase();

            if (langCode === 'ja') return 'ja';
            if (langCode === 'es') return 'es';
            if (langCode === 'en') return 'en';

            return 'ja';
        },

        async loadTranslations(locale) {
            if (!this.supportedLocales.includes(locale)) {
                console.warn(`Locale "${locale}" not supported. Using "ja".`);
                locale = 'ja';
            }

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

                // Translations loaded for locale
                return translations;

            } catch (error) {
                console.error(`Failed to load translations for ${locale}:`, error);

                if (locale !== 'ja') {
                    return this.loadTranslations('ja');
                }

                this.translations[locale] = {};
                return {};
            }
        },

        async setLocale(locale) {
            if (!this.supportedLocales.includes(locale)) {
                console.warn(`Locale "${locale}" not supported.`);
                return;
            }

            if (locale === this.currentLocale) {
                return;
            }

            // Load translations if not cached
            await this.loadTranslations(locale);

            this.currentLocale = locale;
            localStorage.setItem(this.storageKey, locale);

            // Update document lang attribute
            document.documentElement.lang = locale;

            // Update UI selector
            this.updateLanguageSelector();

            // Update all translated elements
            this.updateDOM();

            // Notify listeners
            this.notifyListeners();

            // Locale changed

            // Show toast notification
            const info = this.localeInfo[locale];
            App.ui.showToast('info', `Language: ${info.nativeName}`);
        },

        getLocale() {
            return this.currentLocale;
        },

        t(key, params = {}) {
            const translations = this.translations[this.currentLocale] || {};
            let value = this.getNestedValue(translations, key);

            // Fallback to Japanese
            if (value === undefined && this.currentLocale !== 'ja') {
                const jaTranslations = this.translations['ja'] || {};
                value = this.getNestedValue(jaTranslations, key);
            }

            // Return key if not found
            if (value === undefined) {
                return key;
            }

            // Interpolate parameters
            return this.interpolate(value, params);
        },

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
        },

        interpolate(template, params) {
            if (!params || typeof template !== 'string') {
                return template;
            }

            return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
                return params.hasOwnProperty(key) ? params[key] : match;
            });
        },

        onLocaleChange(callback) {
            if (typeof callback === 'function') {
                this.changeListeners.push(callback);
            }

            return () => {
                const index = this.changeListeners.indexOf(callback);
                if (index > -1) {
                    this.changeListeners.splice(index, 1);
                }
            };
        },

        notifyListeners() {
            const locale = this.currentLocale;
            this.changeListeners.forEach(callback => {
                try {
                    callback(locale);
                } catch (error) {
                    console.error('Error in locale change listener:', error);
                }
            });
        },

        updateDOM() {
            // Update elements with data-i18n
            document.querySelectorAll('[data-i18n]').forEach(element => {
                const key = element.getAttribute('data-i18n');
                const translation = this.t(key);
                if (translation !== key) {
                    element.textContent = translation;
                }
            });

            // Update placeholders with data-i18n-placeholder
            document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
                const key = element.getAttribute('data-i18n-placeholder');
                const translation = this.t(key);
                if (translation !== key) {
                    element.placeholder = translation;
                }
            });

            // Update titles with data-i18n-title
            document.querySelectorAll('[data-i18n-title]').forEach(element => {
                const key = element.getAttribute('data-i18n-title');
                const translation = this.t(key);
                if (translation !== key) {
                    element.title = translation;
                }
            });

            // Update aria-labels with data-i18n-aria
            document.querySelectorAll('[data-i18n-aria]').forEach(element => {
                const key = element.getAttribute('data-i18n-aria');
                const translation = this.t(key);
                if (translation !== key) {
                    element.setAttribute('aria-label', translation);
                }
            });
        },

        setupLanguageSelector() {
            const selectorBtn = document.getElementById('language-selector-btn');
            const selector = document.getElementById('language-selector');
            const dropdown = document.getElementById('language-dropdown');

            if (!selectorBtn || !selector) return;

            // Toggle dropdown on button click
            selectorBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                selector.classList.toggle('open');
                selectorBtn.setAttribute('aria-expanded',
                    selector.classList.contains('open') ? 'true' : 'false'
                );
            });

            // Handle language option clicks
            if (dropdown) {
                dropdown.querySelectorAll('.language-option').forEach(option => {
                    option.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        const locale = option.dataset.locale;
                        if (locale) {
                            await this.setLocale(locale);
                            selector.classList.remove('open');
                            selectorBtn.setAttribute('aria-expanded', 'false');
                        }
                    });
                });
            }

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!selector.contains(e.target)) {
                    selector.classList.remove('open');
                    selectorBtn.setAttribute('aria-expanded', 'false');
                }
            });

            // Keyboard navigation
            selectorBtn.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    selector.classList.remove('open');
                    selectorBtn.setAttribute('aria-expanded', 'false');
                }
            });
        },

        updateLanguageSelector() {
            const flagEl = document.getElementById('current-lang-flag');
            const codeEl = document.getElementById('current-lang-code');
            const dropdown = document.getElementById('language-dropdown');

            const info = this.localeInfo[this.currentLocale];

            if (flagEl) flagEl.textContent = info.flag;
            if (codeEl) codeEl.textContent = info.code;

            // Update active state in dropdown
            if (dropdown) {
                dropdown.querySelectorAll('.language-option').forEach(option => {
                    const isActive = option.dataset.locale === this.currentLocale;
                    option.classList.toggle('active', isActive);
                    option.setAttribute('aria-selected', isActive ? 'true' : 'false');
                });
            }
        },

        getLocaleInfo() {
            return this.localeInfo[this.currentLocale];
        },

        getAllLocalesInfo() {
            return this.supportedLocales.map(code => ({
                code,
                ...this.localeInfo[code]
            }));
        }
    },

    // ========================================
    // AUTH MODUlE (JWT Handling)
    // ========================================
    auth: {
        token: null,
        user: null,

        init() {
            // Check for saved token
            const token = localStorage.getItem('access_token');
            if (token) {
                this.token = token;
                this.updateUI(true);
            } else {
                this.updateUI(false);
            }

            // Bind login form
            const loginForm = document.getElementById('login-form');
            if (loginForm) {
                loginForm.addEventListener('submit', (e) => this.handleLogin(e));
            }
        },

        async handleLogin(e) {
            e.preventDefault();
            const form = e.target;
            const username = form.username.value;
            const password = form.password.value;
            const btn = form.querySelector('button[type="submit"]');
            const errorEl = document.getElementById('login-error');

            App.ui.setBtnLoading(btn, true);
            errorEl.style.display = 'none';

            try {
                const res = await fetch(`${App.config.apiBase}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                if (!res.ok) throw new Error('Invalid credentials');

                const data = await res.json();
                this.token = data.access_token;
                localStorage.setItem('access_token', this.token);

                this.updateUI(true);
                document.getElementById('login-modal').classList.remove('active');
                form.reset();
                App.ui.showToast('success', 'Logged in successfully');

            } catch (err) {
                console.error(err);
                errorEl.style.display = 'block';
                errorEl.textContent = 'Invalid username or password';
            } finally {
                App.ui.setBtnLoading(btn, false);
            }
        },

        logout() {
            this.token = null;
            this.user = null;
            localStorage.removeItem('access_token');
            this.updateUI(false);
            App.ui.showToast('info', 'Logged out');
            // Optionally call API logout endpoint
        },

        showLogin() {
            document.getElementById('login-modal').classList.add('active');
            document.getElementById('login-username').focus();
        },

        updateUI(isLoggedIn) {
            const loginBtn = document.getElementById('btn-login');
            const logoutBtn = document.getElementById('btn-logout');

            if (loginBtn) loginBtn.classList.toggle('d-none', isLoggedIn);
            if (logoutBtn) logoutBtn.classList.toggle('d-none', !isLoggedIn);
        },

        // Wrapper for fetch calls requiring auth
        async fetchWithAuth(url, options = {}) {
            if (!this.token) {
                this.showLogin();
                throw new Error('Authentication required');
            }

            const headers = {
                ...options.headers,
                'Authorization': `Bearer ${this.token}`
            };

            const res = await fetch(url, { ...options, headers });

            if (res.status === 401) {
                this.logout();
                this.showLogin();
                throw new Error('Session expired');
            }

            return res;
        }
    },

    // ========================================
    // SECURITY UTILITIES (XSS Prevention)
    // ========================================
    utils: {
        /**
         * Escapes HTML to prevent XSS attacks
         */
        escapeHtml(str) {
            if (str === null || str === undefined) return '';
            const div = document.createElement('div');
            div.textContent = String(str);
            return div.innerHTML;
        },

        /**
         * Escapes attribute values
         */
        escapeAttr(str) {
            if (str === null || str === undefined) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/'/g, '&#39;')
                .replace(/"/g, '&quot;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        },

        /**
         * Safely creates a number from input
         */
        safeNumber(val, defaultVal = 0) {
            const num = parseFloat(val);
            return Number.isFinite(num) ? num : defaultVal;
        },

        /**
         * Validates year is within acceptable range
         */
        isValidYear(year) {
            const num = parseInt(year);
            return Number.isInteger(num) && num >= 2000 && num <= 2100;
        }
    },

    // ========================================
    // VISUALIZATIONS MODULE (Advanced Animations)
    // ========================================
    visualizations: {
        // Animate SVG progress ring
        animateRing(elementId, valueId, value, maxValue, duration = 1000) {
            const ring = document.getElementById(elementId);
            const valueEl = document.getElementById(valueId);
            if (!ring || !valueEl) return;

            const radius = 34;
            const circumference = 2 * Math.PI * radius; // 213.6
            const safeMaxValue = maxValue > 0 ? maxValue : 1; // Prevent division by zero
            const percent = Math.min(value / safeMaxValue, 1);
            const offset = circumference - (percent * circumference);

            // Animate the ring
            ring.style.strokeDasharray = circumference;
            ring.style.strokeDashoffset = circumference;

            // Trigger animation after a small delay
            setTimeout(() => {
                ring.style.strokeDashoffset = offset;
            }, 100);

            // Animate the number
            this.animateNumber(valueEl, 0, value, duration);
        },

        // Animate number counting up
        animateNumber(element, start, end, duration) {
            const startTime = performance.now();
            const isFloat = !Number.isInteger(end);

            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);

                // Ease out cubic
                const easeOut = 1 - Math.pow(1 - progress, 3);
                const current = start + (end - start) * easeOut;

                if (isFloat) {
                    element.textContent = current.toFixed(1);
                } else {
                    element.textContent = Math.round(current).toLocaleString();
                }

                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };

            requestAnimationFrame(animate);
        },

        // Update compliance gauge (semi-circle)
        updateGauge(complianceRate, compliant = 0, total = 0) {
            const gauge = document.getElementById('gauge-compliance');
            const valueEl = document.getElementById('gauge-value');
            const labelEl = document.querySelector('.gauge-label');
            const countEl = document.getElementById('compliance-count');
            const totalEl = document.getElementById('compliance-total');
            if (!gauge) return;

            // Semi-circle arc length is ~251.2 (π * 80)
            const arcLength = Math.PI * 80;
            const safeRate = isNaN(complianceRate) ? 0 : complianceRate;
            const percent = Math.min(safeRate / 100, 1);
            const offset = arcLength - (percent * arcLength);

            // Set color based on compliance
            let color = 'var(--danger)';
            if (complianceRate >= 80) color = 'var(--success)';
            else if (complianceRate >= 50) color = 'var(--warning)';

            gauge.style.stroke = color;
            gauge.style.strokeDasharray = arcLength;
            gauge.style.strokeDashoffset = arcLength;

            setTimeout(() => {
                gauge.style.strokeDashoffset = offset;
            }, 200);

            if (valueEl) {
                this.animateNumber(valueEl, 0, complianceRate, 1500);
                setTimeout(() => {
                    valueEl.textContent = Math.round(complianceRate) + '%';
                }, 1600);
            }

            if (countEl) countEl.textContent = compliant;
            if (totalEl) totalEl.textContent = total;

            if (labelEl) {
                if (complianceRate >= 80) {
                    labelEl.textContent = '優秀 - Excelente';
                    labelEl.style.color = 'var(--success)';
                } else if (complianceRate >= 50) {
                    labelEl.textContent = '注意 - Atención';
                    labelEl.style.color = 'var(--warning)';
                } else {
                    labelEl.textContent = '要改善 - Mejorar';
                    labelEl.style.color = 'var(--danger)';
                }
            }
        },

        // Update expiring days countdown
        updateExpiringDays(data) {
            const countdownContainer = document.getElementById('countdown-container');
            const noExpiring = document.getElementById('no-expiring');
            const expiringDays = document.getElementById('expiring-days');
            const expiringDetail = document.getElementById('expiring-detail');
            const criticalCount = document.getElementById('critical-count');
            const warningCount = document.getElementById('warning-count');
            const healthyCount = document.getElementById('healthy-count');

            // Calculate categories
            const critical = data.filter(e => e.balance <= 0).length;
            const warning = data.filter(e => e.balance > 0 && e.balance < 3).length;
            const healthy = data.filter(e => e.balance >= 5).length;

            // Update counts with animation
            if (criticalCount) this.animateNumber(criticalCount, 0, critical, 800);
            if (warningCount) this.animateNumber(warningCount, 0, warning, 800);
            if (healthyCount) this.animateNumber(healthyCount, 0, healthy, 800);

            // Filter employees with low balance
            const expiring = data
                .filter(e => e.balance < 5 && e.balance > 0)
                .sort((a, b) => a.balance - b.balance);

            const totalExpiringDays = expiring.reduce((sum, e) => sum + e.balance, 0);

            if (expiring.length === 0) {
                if (countdownContainer) countdownContainer.style.display = 'none';
                if (noExpiring) noExpiring.style.display = 'block';
            } else {
                if (countdownContainer) countdownContainer.style.display = 'flex';
                if (noExpiring) noExpiring.style.display = 'none';
                if (expiringDays) expiringDays.textContent = totalExpiringDays.toFixed(1) + ' days';
                if (expiringDetail) expiringDetail.textContent = `from ${expiring.length} employees`;
            }
        },

        // Show confetti celebration
        showConfetti() {
            const colors = ['#00d4ff', '#ff6b6b', '#ffd93d', '#6bcb77', '#c56cf0'];
            const confettiCount = 50;

            for (let i = 0; i < confettiCount; i++) {
                const confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.left = Math.random() * 100 + 'vw';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.animationDelay = Math.random() * 0.5 + 's';
                confetti.style.transform = `rotate(${Math.random() * 360}deg)`;
                document.body.appendChild(confetti);

                // Remove after animation
                setTimeout(() => confetti.remove(), 3500);
            }
        },

        // Quick stats for employee types
        updateQuickStats(hakenCount, ukeoiCount, staffCount) {
            const hakenEl = document.getElementById('quick-haken');
            const ukeoiEl = document.getElementById('quick-ukeoi');
            const staffEl = document.getElementById('quick-staff');

            if (hakenEl) this.animateNumber(hakenEl, 0, hakenCount, 800);
            if (ukeoiEl) this.animateNumber(ukeoiEl, 0, ukeoiCount, 800);
            if (staffEl) this.animateNumber(staffEl, 0, staffCount, 800);
        }
    },

    async init() {
        // Initializing YuKyu Premium Dashboard
        this.ui.showLoading();

        // Initialize theme
        this.theme.init();

        // Initialize auth
        this.auth.init();

        // Initialize internationalization (i18n)
        this.i18n.init();

        // Initialize Router (Hash-based)
        this.router.init();

        // Initialize Calendar
        if (this.calendar) {
            this.calendar.init();
        }

        // Fetch initial data
        this.data.fetchEmployees();

        this.ui.hideLoading();
        this.events.setupListeners();
    },

    // ========================================
    // ROUTER MODULE (Hash-based)
    // ========================================
    router: {
        init() {
            window.addEventListener('hashchange', () => this.handleRouting());
            // Initial routing
            if (window.location.hash) {
                this.handleRouting();
            } else {
                // Default to dashboard
                window.location.hash = 'dashboard';
            }
        },

        handleRouting() {
            const hash = window.location.hash.substring(1);
            if (hash) {
                App.ui.switchView(hash);
            }
        }
    },

    // ========================================
    // THEME MODULE
    // ========================================
    theme: {
        current: 'light',

        init() {
            // Load saved theme or default to light
            const saved = localStorage.getItem('yukyu-theme');
            this.current = saved || 'light';
            this.apply();

            // Setup keyboard shortcut (Ctrl+Shift+T)
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                    e.preventDefault();
                    this.toggle();
                }
            });
        },

        toggle() {
            this.current = this.current === 'dark' ? 'light' : 'dark';
            this.apply();
            localStorage.setItem('yukyu-theme', this.current);
            App.ui.showToast('info', this.current === 'dark' ? '🌙 ダークモード' : '☀️ ライトモード');
        },

        apply() {
            document.documentElement.setAttribute('data-theme', this.current);

            // Update theme toggle button
            const icon = document.getElementById('theme-icon');
            const label = document.getElementById('theme-label');
            const btn = document.querySelector('.theme-toggle-premium');

            if (icon) icon.textContent = this.current === 'dark' ? '🌙' : '☀️';
            if (label) label.textContent = this.current === 'dark' ? 'Dark' : 'Light';

            // Update accessibility attributes
            if (btn) {
                const isDark = this.current === 'dark';
                btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
                btn.setAttribute('aria-label', isDark
                    ? 'Switch to light mode. Current theme: dark (Ctrl+Shift+T)'
                    : 'Switch to dark mode. Current theme: light (Ctrl+Shift+T)'
                );
                btn.title = isDark
                    ? 'テーマ切替 - Switch to Light (Ctrl+Shift+T)'
                    : 'テーマ切替 - Switch to Dark (Ctrl+Shift+T)';
            }

            // ============================================
            // ACTUALIZAR FLATPICKR DINÁMICAMENTE
            // ============================================
            // Buscar todas las instancias de Flatpickr y actualizar su tema
            const flatpickrInstances = [
                window.startDatePicker,
                window.endDatePicker,
                window.reportStartPicker,
                window.reportEndPicker
            ];

            flatpickrInstances.forEach(picker => {
                if (picker && picker.config) {
                    // Actualizar el tema del Flatpickr
                    picker.set('theme', this.current);

                    // Forzar re-render del calendario si está abierto
                    if (picker.isOpen) {
                        picker.close();
                        setTimeout(() => picker.open(), 50);
                    }
                }
            });

            // ============================================
            // ACTUALIZAR SELECTORES (<select>)
            // ============================================
            // Los selectores ya se actualizarán automáticamente con CSS
            // pero podemos forzar un refresh si es necesario
            const selects = document.querySelectorAll('select.input-glass');
            selects.forEach(select => {
                // Trigger reflow para aplicar nuevos estilos
                select.offsetHeight;
            });
        }
    },

    data: {
        // Request counter to prevent race conditions when changing years rapidly
        _fetchRequestId: 0,

        async fetchEmployees(year = null, activeOnly = true, allowRetry = true) {
            // Increment request ID to track this specific request
            const requestId = ++this._fetchRequestId;

            // Update state year if provided
            if (year !== null && year !== undefined) {
                App.state.year = parseInt(year);
            }

            try {
                // Use enhanced endpoint with employee type and active status
                let url = `${App.config.apiBase}/employees?enhanced=true&active_only=${activeOnly}`;
                if (App.state.year) url += `&year=${App.state.year}`;

                const res = await fetch(url);

                if (!res.ok) {
                    const errorText = await res.text().catch(() => '');
                    throw new Error(errorText || `Server error: ${res.status}`);
                }

                // Check if this request is still the most recent one
                if (requestId !== this._fetchRequestId) {
                    // Ignoring stale response for year
                    return; // Ignore stale responses
                }

                const json = await res.json();

                const rawEmployees = Array.isArray(json)
                    ? json
                    : (Array.isArray(json?.data) ? json.data : (Array.isArray(json?.employees) ? json.employees : []));

                const derivedYears = [...new Set(
                    rawEmployees
                        .map(e => parseInt(e?.year))
                        .filter(Number.isFinite)
                )].sort((a, b) => b - a);

                App.state.data = rawEmployees.map(emp => ({
                    ...emp,
                    employeeNum: emp.employee_num,
                    usageRate: emp.granted > 0 ? Math.round((emp.used / emp.granted) * 100) : 0,
                    // Enhanced fields
                    employeeType: emp.employee_type || 'staff',
                    employmentStatus: emp.employment_status || '在職中',
                    isActive: emp.is_active === 1 || emp.is_active === true
                }));

                const apiYears = Array.isArray(json?.available_years)
                    ? json.available_years
                    : (Array.isArray(json?.years) ? json.years : null);

                App.state.availableYears = Array.isArray(apiYears)
                    ? apiYears.map(y => parseInt(y)).filter(Number.isFinite).sort((a, b) => b - a)
                    : derivedYears;

                // Smart Year Selection
                if (App.state.availableYears.length > 0 && !App.state.year) {
                    const currentYear = new Date().getFullYear();
                    // Prefer current year if available, otherwise first available
                    if (App.state.availableYears.includes(currentYear)) {
                        App.state.year = currentYear;
                    } else if (App.state.availableYears.includes(currentYear - 1)) {
                        // Or previous year if current not available
                        App.state.year = currentYear - 1;
                    } else {
                        // Fallback to first available
                        App.state.year = App.state.availableYears[0];
                    }

                    // If year wasn't passed, we need to refetch with the selected year to filter correctly
                    if (!year) {
                        return this.fetchEmployees(App.state.year);
                    }
                }

                // Retry once without active filter if nothing returned
                if (App.state.data.length === 0 && activeOnly && allowRetry) {
                    console.warn('⚠️ Sin resultados con active_only=true, reintentando con active_only=false');
                    return this.fetchEmployees(App.state.year, false, false);
                }

                // Final check before updating UI
                if (requestId !== this._fetchRequestId) {
                    return;
                }

                // Data loaded successfully for the year

                await App.ui.updateAll();

            } catch (err) {
                // Only show error if this is still the current request
                if (requestId === this._fetchRequestId) {
                    console.error(err);
                    const msg = (err && err.message) ? err.message : String(err);
                    App.ui.showToast('error', `Failed to load data: ${msg}`);
                }
            }
        },

        async sync() {
            if (!App.auth.token) {
                App.auth.showLogin();
                return;
            }
            const btn = document.getElementById('btn-sync-main');
            App.ui.setBtnLoading(btn, true);
            try {
                const res = await App.auth.fetchWithAuth(`${App.config.apiBase}/sync`, { method: 'POST' });
                if (!res.ok) {
                    const errorText = await res.text();
                    throw new Error(errorText || `Server error: ${res.status}`);
                }
                const json = await res.json();

                // Mostrar toast rápido
                App.ui.showToast('success', `✅ ${json.count}件の有給データを同期しました`, 3000);

                // Obtener datos actualizados para el reporte de importación
                await this.fetchEmployees(App.state.year);

                // Preparar datos para el modal de resultado de importación
                const importData = {
                    count: json.count || 0,
                    skipped: json.skipped || 0,
                    duplicates: json.duplicates || 0,
                    validation: json.validation || null,
                    employees: App.state.data || []
                };

                // Mostrar modal de resultado de importación
                if (App.importReport && typeof App.importReport.showImportResult === 'function') {
                    App.importReport.showImportResult(importData);
                }

            } catch (err) {
                console.error('Sync error:', err);
                if (err.message.includes('Authentication') || err.message === 'Session expired') {
                    // Handled by fetchWithAuth
                } else if (err.message.includes('fetch') || err.name === 'TypeError') {
                    App.ui.showToast('error', '🌐 ネットワークエラー: サーバーに接続できません', 6000);
                } else {
                    App.ui.showToast('error', `❌ 同期失敗: ${err.message}`, 6000);
                }
            } finally {
                App.ui.setBtnLoading(btn, false);
            }
        },

        async syncGenzai() {
            if (!App.auth.token) {
                App.auth.showLogin();
                return;
            }
            const btn = document.getElementById('btn-sync-genzai');
            App.ui.setBtnLoading(btn, true);
            try {
                const res = await App.auth.fetchWithAuth(`${App.config.apiBase}/sync-genzai`, { method: 'POST' });
                if (!res.ok) throw new Error(`Server error: ${res.status}`);
                const json = await res.json();
                App.ui.showToast('success', `✅ 派遣社員データを同期しました (${json.count || 0}件)`, 5000);
            } catch (err) {
                console.error('Genzai sync error:', err);
                if (err.message !== 'Authentication required' && err.message !== 'Session expired') {
                    App.ui.showToast('error', '❌ 派遣社員の同期に失敗しました', 6000);
                }
            } finally {
                App.ui.setBtnLoading(btn, false);
            }
        },

        async syncUkeoi() {
            if (!App.auth.token) {
                App.auth.showLogin();
                return;
            }
            const btn = document.getElementById('btn-sync-ukeoi');
            App.ui.setBtnLoading(btn, true);
            try {
                const res = await App.auth.fetchWithAuth(`${App.config.apiBase}/sync-ukeoi`, { method: 'POST' });
                if (!res.ok) throw new Error(`Server error: ${res.status}`);
                const json = await res.json();
                App.ui.showToast('success', `✅ 請負社員データを同期しました (${json.count || 0}件)`, 5000);
            } catch (err) {
                console.error('Ukeoi sync error:', err);
                if (err.message !== 'Authentication required' && err.message !== 'Session expired') {
                    App.ui.showToast('error', '❌ 請負社員の同期に失敗しました', 6000);
                }
            } finally {
                App.ui.setBtnLoading(btn, false);
            }
        },

        getFiltered() {
            if (!App.state.year) return App.state.data;

            // Use loose equality to handle string/number differences and check if year exists
            const filtered = App.state.data.filter(e => !e.year || e.year == App.state.year);

            // Fallback: if the selected year returns no data but we do have data, show all
            if (filtered.length === 0 && App.state.data.length > 0) {
                console.warn(`⚠️ Sin datos para el año ${App.state.year}, mostrando todos los registros`);
                if (App.state.fallbackWarnedYear !== App.state.year) {
                    App.state.fallbackWarnedYear = App.state.year;
                    App.ui.showToast('warning', `⚠️ No hay registros para ${App.state.year}. Mostrando todos los datos disponibles.`);
                }
                return App.state.data;
            }

            return filtered;
        },

        getFactoryStats() {
            const stats = {};
            const data = this.getFiltered();
            data.forEach(e => {
                const f = e.haken;
                // Filtrar fábricas sin nombre válido
                if (!f || f === '0' || f === 'Unknown' || f.trim() === '' || f === 'null') return;
                if (!stats[f]) stats[f] = 0;
                stats[f] += e.used;
            });
            return Object.entries(stats).sort((a, b) => b[1] - a[1]);
        }
    },

    ui: {
        async updateAll() {
            const data = App.data.getFiltered();
            // Updating UI with employee data for year

            await this.renderKPIs();
            this.renderTable('', App.state.typeFilter);
            await this.renderCharts();
            this.updateYearFilter();
            this.updateTypeCounts();

            const badge = document.getElementById('emp-count-badge');
            if (badge) badge.innerText = `${data.length} Employees`;
        },

        switchView(viewName) {
            if (!viewName) return;

            // Update Hash if different (for deep linking)
            if (window.location.hash !== `#${viewName}`) {
                window.location.hash = viewName;
                return; // Router will trigger switchView again
            }

            // Hide all views
            document.querySelectorAll('.view-section').forEach(el => {
                el.classList.remove('active');
                el.classList.remove('d-block');
                el.classList.add('d-none');
                el.style.display = 'none';
            });

            // Show target view
            const target = document.getElementById(`view-${viewName}`);
            if (target) {
                target.classList.remove('d-none');
                target.classList.add('d-block');
                target.style.display = 'block';
                setTimeout(() => {
                    target.classList.add('active');
                    // Animate view transition with GSAP
                    if (App.animations && App.animations.transitionView) {
                        App.animations.transitionView(target);
                    }
                }, 10);
            }

            // Update Sidebar
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            const activeNav = document.querySelector(`.nav-item[data-view="${viewName}"]`);
            if (activeNav) activeNav.classList.add('active');

            // Update Header
            const titleMap = {
                'dashboard': 'ダッシュボード',
                'employees': '従業員一覧',
                'factories': '工場別分析',
                'requests': '有給休暇申請',
                'calendar': '休暇カレンダー',
                'compliance': 'コンプライアンス',
                'analytics': '詳細分析',
                'reports': '月次レポート (21日〜20日)',
                'settings': 'システム設定'
            };
            document.getElementById('page-title').innerText = titleMap[viewName] || 'Dashboard';

            App.state.currentView = viewName;

            // Re-render charts if switching to factory view to ensure size correctness
            if (viewName === 'factories') {
                setTimeout(() => {
                    App.ui.ensureChartsVisible();
                    App.charts.renderFactoryChart();
                }, 100);
            }

            // Re-render charts for dashboard view
            if (viewName === 'dashboard') {
                setTimeout(() => {
                    App.ui.ensureChartsVisible();
                    App.charts.renderDistribution();
                    App.charts.renderTrends();
                }, 100);
            }

            // Re-render charts for analytics view
            if (viewName === 'analytics') {
                setTimeout(() => {
                    App.ui.ensureChartsVisible();
                    App.charts.renderTypes();
                }, 100);
            }

            // Load data for specific views
            if (viewName === 'requests') {
                App.requests.loadFactories();
                App.requests.loadPending();
                App.requests.loadHistory();
            }

            if (viewName === 'calendar') {
                App.calendar.loadEvents();
            }

            if (viewName === 'compliance') {
                App.compliance.loadAlerts();
            }

            if (viewName === 'analytics') {
                App.analytics.loadDashboard();
            }

            if (viewName === 'reports') {
                App.reports.init();
            }

            if (viewName === 'settings') {
                App.settings.loadSnapshot();
            }

            if (viewName === 'employees') {
                App.employeeTypes.loadData();
            }
        },

        async renderKPIs() {
            const data = App.data.getFiltered();
            const total = data.length;
            const granted = data.reduce((s, e) => s + App.utils.safeNumber(e.granted), 0);

            // Fetch TRUE usage from individual dates (R-BE columns)
            // This returns the correct value (~3318) instead of column N sum (~4466)
            let used = 0;
            let balance = 0;
            let rate = 0;

            try {
                if (App.state.year) {
                    const res = await fetch(`${App.config.apiBase}/yukyu/kpi-stats/${App.state.year}`);
                    const kpi_res = await res.json();
                    if (kpi_res.status === 'success' && kpi_res.kpi) {
                        used = App.utils.safeNumber(kpi_res.kpi.total_used);
                        balance = App.utils.safeNumber(kpi_res.kpi.total_balance);
                        rate = App.utils.safeNumber(kpi_res.kpi.usage_rate);
                    }
                }
            } catch (e) {
                console.warn('KPI API failed, using local calculation:', e);
                // Fallback to old calculation if endpoint fails
                used = data.reduce((s, e) => s + App.utils.safeNumber(e.used), 0);
                balance = granted - used;
                rate = granted > 0 ? Math.round((used / granted) * 100) : 0;
            }

            // Update KPI displays (guard missing DOM nodes)
            const elements = {
                'kpi-used': used,
                'kpi-used-detail': used,
                'kpi-balance': balance,
                'kpi-balance-detail': balance,
                'kpi-rate': rate,
                'kpi-rate-detail': rate,
                'kpi-total': total,
                'kpi-granted': granted
            };

            Object.entries(elements).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) {
                    if (id.includes('rate')) {
                        el.innerText = (val || 0) + '%';
                    } else if (id.includes('detail')) {
                        el.innerText = Math.round(val || 0).toLocaleString() + (id.includes('used') ? ' days' : ' days left');
                    } else {
                        el.innerText = Math.round(val || 0).toLocaleString();
                    }
                }
            });

            // Calculate max values for rings
            const maxUsage = granted > 0 ? granted : 10000;
            const maxBalance = granted > 0 ? granted : 10000;

            // Animate progress rings
            App.visualizations.animateRing('ring-usage', 'ring-usage-value', used, maxUsage, 1200);
            App.visualizations.animateRing('ring-balance', 'ring-balance-value', balance, maxBalance, 1200);
            App.visualizations.animateRing('ring-rate', 'ring-rate-value', rate, 100, 1200);

            // Calculate compliance (% of employees with >= 5 days used - Japanese law)
            const compliant = data.filter(e => e.used >= 5).length;
            const complianceRate = total > 0 ? Math.round((compliant / total) * 100) : 0;
            App.visualizations.updateGauge(complianceRate, compliant, total);

            // Update expiring days countdown
            App.visualizations.updateExpiringDays(data);
        },

        renderTable(filterText = '', typeFilter = 'all') {
            const tbody = document.getElementById('table-body');
            let data = App.data.getFiltered();

            // Filter by text search
            if (filterText) {
                const q = filterText.toLowerCase();
                data = data.filter(e =>
                    e.name.toLowerCase().includes(q) ||
                    String(e.employeeNum).includes(q) ||
                    (e.haken && e.haken.toLowerCase().includes(q))
                );
            }

            // Filter by employee type (genzai, ukeoi, staff)
            if (typeFilter && typeFilter !== 'all') {
                data = data.filter(e => e.employeeType === typeFilter);
            }

            if (data.length === 0) {
                tbody.textContent = '';
                const tr = document.createElement('tr');
                const td = document.createElement('td');
                td.colSpan = 9;  // Updated for bulk edit checkbox column
                td.style.textAlign = 'center';
                td.style.padding = '2rem';
                td.textContent = 'No matching records found';
                tr.appendChild(td);
                tbody.appendChild(tr);
                return;
            }

            // Using data attributes instead of inline onclick (XSS prevention)
            tbody.innerHTML = data.map(e => {
                const empNum = App.utils.escapeAttr(e.employeeNum);

                // Name display logic: Show name with Kana below when available
                const displayName = App.utils.escapeHtml(e.name);
                let subName = '';

                // Show Kana (katakana) below the name when available
                if (e.kana && e.kana.trim()) {
                    subName = `<div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">${App.utils.escapeHtml(e.kana)}</div>`;
                }

                const haken = App.utils.escapeHtml(e.haken || '-');
                const granted = App.utils.safeNumber(e.granted).toFixed(1);
                const used = App.utils.safeNumber(e.used).toFixed(1);
                const balance = App.utils.safeNumber(e.balance);
                const usageRate = App.utils.safeNumber(e.usageRate);
                const balanceClass = balance < 0 ? 'badge-critical' : balance < 5 ? 'badge-danger' : 'badge-success';

                // Employee type badge
                const typeLabels = { genzai: '派遣', ukeoi: '請負', staff: '社員' };
                const typeClasses = { genzai: 'type-genzai', ukeoi: 'type-ukeoi', staff: 'type-staff' };
                const empType = e.employeeType || 'staff';
                const typeLabel = typeLabels[empType] || '社員';
                const typeClass = typeClasses[empType] || 'type-staff';

                // Determine color based on usage rate
                const rateColor = usageRate >= 80 ? 'var(--success)' : usageRate >= 50 ? 'var(--warning)' : 'var(--danger)';
                const rateGlow = usageRate >= 80 ? '0 0 8px var(--success)' : usageRate >= 50 ? '0 0 8px var(--warning)' : '0 0 8px var(--danger)';

                // Check if employee is selected
                const isSelected = App.bulkEdit && App.bulkEdit.selectedEmployees.has(e.employeeNum);

                return `
                <tr class="employee-row" data-employee-num="${empNum}" style="cursor: pointer;">
                    <td class="table-checkbox" onclick="event.stopPropagation();">
                        <input type="checkbox"
                            class="employee-select-checkbox"
                            data-employee-num="${empNum}"
                            ${isSelected ? 'checked' : ''}
                            onchange="App.bulkEdit.toggleEmployee('${empNum}', this.checked)"
                            title="選択">
                    </td>
                    <td><div class="font-bold">${empNum}</div></td>
                    <td>
                        <div class="employee-name-cell">
                            <div>
                                <span class="font-bold text-white">${displayName}</span>
                                ${subName}
                            </div>
                            <span class="badge-type ${typeClass}" style="margin-left: 8px;">${typeLabel}</span>
                        </div>
                    </td>
                    <td><div class="text-sm text-gray-400">${haken}</div></td>
                    <td>${granted}</td>
                    <td><span class="text-gradient">${used}</span></td>
                    <td><span class="badge ${balanceClass}">${balance.toFixed(1)}</span></td>
                    <td>
                        <div class="mini-progress" style="width: 100px; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; position: relative;">
                            <div class="mini-progress-fill" style="width: ${Math.min(usageRate, 100)}%; height: 100%; background: linear-gradient(90deg, ${rateColor}, ${rateColor}88); border-radius: 4px; box-shadow: ${rateGlow}; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);"></div>
                        </div>
                        <div class="text-xs mt-1 text-right" style="color: ${rateColor}; font-weight: 500;">${usageRate}%</div>
                    </td>
                </tr>
            `}).join('');
        },

        handleSearch(val) {
            // Use employeeTypes module if data is loaded, otherwise use main table
            if (App.employeeTypes && App.employeeTypes.data && App.employeeTypes.data.all.length > 0) {
                App.employeeTypes.renderTable(val);
            } else {
                this.renderTable(val, App.state.typeFilter);
            }
        },

        filterByType(type) {
            App.state.typeFilter = type;

            // Update active tab
            document.querySelectorAll('.type-tab').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.type === type);
            });

            // Re-render table with current search and type filter
            const searchVal = document.getElementById('search-input')?.value || '';
            this.renderTable(searchVal, type);
        },

        updateTypeCounts() {
            const data = App.data.getFiltered();
            const counts = {
                all: data.length,
                genzai: data.filter(e => e.employeeType === 'genzai').length,
                ukeoi: data.filter(e => e.employeeType === 'ukeoi').length,
                staff: data.filter(e => e.employeeType === 'staff').length
            };

            // Update count badges (Sidebar + dashboard quick stats)
            const countSidebar = document.getElementById('emp-count-badge-sidebar');
            const qsHaken = document.getElementById('qs-haken');
            const qsUkeoi = document.getElementById('qs-ukeoi');
            const qsStaff = document.getElementById('qs-staff');
            const kpiTotal = document.getElementById('kpi-total');

            if (countSidebar) countSidebar.textContent = counts.all;
            if (qsHaken) qsHaken.textContent = counts.genzai;
            if (qsUkeoi) qsUkeoi.textContent = counts.ukeoi;
            if (qsStaff) qsStaff.textContent = counts.staff;
            if (kpiTotal) kpiTotal.textContent = counts.all;
        },

        updateYearFilter() {
            const selector = document.getElementById('year-selector');
            if (!selector) return;

            // Ensure availableYears is an array
            const apiYears = Array.isArray(App.state.availableYears) ? App.state.availableYears : [];

            // Proactive: Always include Current Year and Next Year for future-proofing
            const currentYear = new Date().getFullYear();
            const nextYear = currentYear + 1;

            // Combine API years with current/next year and sort unique
            let years = [...new Set([...apiYears, currentYear, nextYear])];
            years.sort((a, b) => b - a);

            // Build options
            selector.innerHTML = years.map(y => {
                const safeYear = parseInt(y) || 0;
                return `<option value="${safeYear}" ${Number(App.state.year) === Number(safeYear) ? 'selected' : ''}>${safeYear}年</option>`;
            }).join('');

            // Handle change event (remove old listeners by replacing element or just adding once)
            // Since we rebuild HTML, we need to reattach or use delegation
            if (!selector.dataset.listener) {
                selector.addEventListener('change', (e) => {
                    const year = parseInt(e.target.value);
                    if (year) {
                        App.state.year = year;
                        App.data.fetchEmployees(year);
                    }
                });
                selector.dataset.listener = "true";
            }

            // Update year labels elsewhere in UI
            const yearLabels = document.querySelectorAll('.dynamic-year-label');
            yearLabels.forEach(el => el.textContent = `(${App.state.year})`);
        },

        async renderCharts() {
            // Ensure charts are visible before rendering
            this.ensureChartsVisible();

            try { App.charts.renderDistribution(); } catch (e) { console.error('renderDistribution failed', e); }
            try { await App.charts.renderTrends(); } catch (e) { console.error('renderTrends failed', e); }
            try { App.charts.renderFactoryChart(); } catch (e) { console.error('renderFactoryChart failed', e); }
            try { await App.charts.renderTypes(); } catch (e) { console.error('renderTypes failed', e); }
            try { await App.charts.renderTop10(); } catch (e) { console.error('renderTop10 failed', e); }
        },

        // Ensure charts are visible and properly sized
        _isEnsureChartsRunning: false,
        ensureChartsVisible() {
            // Prevent infinite loop - this function triggers resize which calls this function again
            if (this._isEnsureChartsRunning) return;
            this._isEnsureChartsRunning = true;

            const chartContainers = document.querySelectorAll('.chart-container, .chart-container-sm, .chart-container-lg');

            chartContainers.forEach(container => {
                // Force container to be visible and have proper layout
                container.style.display = 'block';
                container.style.visibility = 'visible';
                container.style.opacity = '1';
                container.style.overflow = 'visible';

                // Ensure a minimum height is set if not already present
                if (!container.style.minHeight) {
                    container.style.minHeight = '300px';
                }

                // Force reflow to ensure proper sizing
                container.offsetHeight;
            });

            // Trigger a global resize event to notify charting libraries (ApexCharts, Chart.js)
            // to recalculate their dimensions based on the now-visible containers
            // This ensures charts are "synchronized" with their container sizes
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
                // Reset flag after resize event is processed
                setTimeout(() => { this._isEnsureChartsRunning = false; }, 300);
            }, 100);
        },

        showLoading() { document.getElementById('loader').classList.add('active'); },
        hideLoading() { document.getElementById('loader').classList.remove('active'); },

        // Button loading state helper
        setBtnLoading(btn, isLoading) {
            if (!btn) return;
            if (isLoading) {
                btn.classList.add('is-loading');
                btn.disabled = true;
            } else {
                btn.classList.remove('is-loading');
                btn.disabled = false;
            }
        },

        // Mobile menu toggle functions
        toggleMobileMenu() {
            const toggle = document.getElementById('mobile-menu-toggle');
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebar-overlay');

            if (sidebar && toggle) {
                const isOpen = sidebar.classList.contains('is-open');
                if (isOpen) {
                    this.closeMobileMenu();
                } else {
                    sidebar.classList.add('is-open');
                    toggle.classList.add('is-active');
                    toggle.setAttribute('aria-expanded', 'true');
                    if (overlay) {
                        overlay.classList.add('is-active');
                        overlay.setAttribute('aria-hidden', 'false');
                    }
                    // Prevent body scroll when menu is open
                    document.body.style.overflow = 'hidden';
                }
            }
        },

        closeMobileMenu() {
            const toggle = document.getElementById('mobile-menu-toggle');
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebar-overlay');

            if (sidebar) {
                sidebar.classList.remove('is-open');
            }
            if (toggle) {
                toggle.classList.remove('is-active');
                toggle.setAttribute('aria-expanded', 'false');
            }
            if (overlay) {
                overlay.classList.remove('is-active');
                overlay.setAttribute('aria-hidden', 'true');
            }
            // Restore body scroll
            document.body.style.overflow = '';
        },

        showToast(type, msg, duration = 4000) {
            // Use modern toast system if available
            if (typeof ModernUI !== 'undefined' && ModernUI.Toast) {
                // Parse message for title (emoji prefix) and content
                const hasEmoji = /^[\u{1F300}-\u{1F9FF}]/u.test(msg);
                let title = '';
                let message = msg;

                // Extract title from emoji-prefixed messages
                if (hasEmoji) {
                    const parts = msg.split(' ');
                    if (parts.length > 1) {
                        title = parts[0];
                        message = parts.slice(1).join(' ');
                    }
                } else {
                    // Default titles
                    const titles = {
                        success: 'Success',
                        error: 'Error',
                        warning: 'Warning',
                        info: 'Info'
                    };
                    title = titles[type] || 'Notification';
                }

                ModernUI.Toast.show({
                    type,
                    title,
                    message,
                    duration
                });
                return;
            }

            // Fallback to original toast system
            const container = document.getElementById('toast-container');
            if (!container) return;

            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;

            const styles = {
                success: { border: 'var(--success)', bg: 'rgba(34, 197, 94, 0.1)' },
                error: { border: 'var(--danger)', bg: 'rgba(239, 68, 68, 0.1)' },
                warning: { border: 'var(--warning)', bg: 'rgba(251, 191, 36, 0.1)' },
                info: { border: 'var(--primary)', bg: 'rgba(56, 189, 248, 0.1)' }
            };
            const style = styles[type] || styles.info;

            toast.style.cssText = `
                border-left: 4px solid ${style.border};
                background: ${style.bg};
                backdrop-filter: blur(10px);
            `;
            // Use textContent to prevent XSS - safer than innerHTML
            toast.textContent = msg;

            const closeBtn = document.createElement('button');
            closeBtn.textContent = '×';
            closeBtn.className = 'toast-close';
            closeBtn.onclick = () => toast.remove();
            toast.appendChild(closeBtn);

            container.appendChild(toast);

            setTimeout(() => {
                toast.style.animation = 'slideOutRight 0.3s forwards';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        },

        async openModal(id) {
            const emp = App.state.data.find(e => e.employeeNum == id);
            if (!emp) return;

            // Mostrar modal con loading
            document.getElementById('modal-title').innerText = emp.name;
            document.getElementById('modal-content').innerHTML = `
                <div style="text-align: center; padding: 2rem;">
                    <div class="spinner" style="margin: 0 auto;"></div>
                    <p style="margin-top: 1rem; color: #94a3b8;">Loading data...</p>
                </div>
            `;
            document.getElementById('detail-modal').classList.add('active');

            // FIX: Ensure modal content is visible (reset GSAP opacity)
            const modalContent = document.querySelector('#detail-modal .modal-content-container');
            if (modalContent) {
                if (typeof gsap !== 'undefined') {
                    gsap.set(modalContent, { opacity: 1, scale: 1, clearProps: 'opacity,transform' });
                } else {
                    modalContent.style.opacity = '1';
                    modalContent.style.transform = 'scale(1)';
                }
            }

            // Obtener datos completos del empleado
            try {
                const res = await fetch(`${App.config.apiBase}/employees/${id}/leave-info`);
                const json = await res.json();

                if (json.status !== 'success') {
                    throw new Error('No se pudieron cargar los datos');
                }

                const employee = json.employee || {};
                const yukyuHistory = json.yukyu_history || [];
                const usageHistory = json.usage_history || [];
                const totalAvailable = json.total_available || 0;

                // Calcular fecha de renovación (基準日 + 1 año)
                let renewalDate = 'No disponible';
                if (yukyuHistory.length > 0) {
                    const latestYear = Math.max(...yukyuHistory.map(h => h.year));
                    // Renovación típica en noviembre del siguiente año
                    renewalDate = `${latestYear + 1}年11月頃`;
                }

                // Generar HTML del historial de 2 años
                let historyHtml = '';
                yukyuHistory.sort((a, b) => b.year - a.year).forEach(h => {
                    historyHtml += `
                        <div class="glass-panel" style="padding: 1rem; margin-bottom: 0.5rem; background: rgba(56, 189, 248, 0.1);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <strong style="color: #38bdf8;">📅 ${h.year}年度</strong>
                                <span class="badge" style="background: ${h.usage_rate > 75 ? '#22c55e' : h.usage_rate > 50 ? '#eab308' : '#ef4444'};">
                                    ${h.usage_rate?.toFixed(1) || 0}%
                                </span>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem; font-size: 0.9rem;">
                                <div><span style="color: #94a3b8;">付与:</span> ${h.granted || 0}日</div>
                                <div><span style="color: #94a3b8;">使用:</span> ${h.used || 0}日</div>
                                <div><span style="color: #38bdf8; font-weight: bold;">残:</span> ${h.balance || 0}日</div>
                            </div>
                        </div>
                    `;
                });

                // Generar HTML de fechas de uso recientes CON indicador de año fiscal
                let usageDatesHtml = '';
                if (usageHistory.length > 0) {
                    const recentUsage = usageHistory.slice(0, 10);

                    // Determinar el año fiscal al que pertenece cada fecha de uso
                    // Regla: El año fiscal comienza en abril (mes 4)
                    // Ejemplo: 2024-02-03 pertenece al año fiscal 2023 (porque aún no llegó abril 2024)
                    const getFiscalYear = (dateStr) => {
                        const date = new Date(dateStr);
                        const year = date.getFullYear();
                        const month = date.getMonth() + 1; // 0-indexed to 1-indexed
                        // Si estamos antes de abril, el año fiscal es el año anterior
                        return month < 4 ? year - 1 : year;
                    };

                    // Colores para diferenciar años fiscales
                    const fiscalYearColors = {
                        [new Date().getFullYear()]: '#10b981',                      // Current FY - Emerald
                        [new Date().getFullYear() - 1]: 'var(--color-primary-500)', // Last FY - Trust Blue
                        [new Date().getFullYear() - 2]: '#64748b',                 // 2 years ago - Slate
                    };
                    const defaultColor = '#94a3b8'; // Older years - Gray

                    usageDatesHtml = `
                        <div style="margin-top: 1rem;">
                            <h4 style="color: #94a3b8; margin-bottom: 0.5rem;">📋 使用履歴 (最近10件)</h4>
                            <div style="max-height: 200px; overflow-y: auto; background: rgba(0,0,0,0.2); border-radius: 8px; padding: 0.5rem;">
                                ${recentUsage.map(u => {
                        const fiscalYear = getFiscalYear(u.date);
                        const fyColor = fiscalYearColors[fiscalYear] || defaultColor;
                        return `
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                                            <span style="background: ${fyColor}; color: #fff; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">${fiscalYear}年度</span>
                                            <span style="color: #e2e8f0;">${u.date}</span>
                                        </div>
                                        <span style="color: var(--color-primary-500); font-weight: bold;">${u.days}日</span>
                                    </div>
                                `}).join('')}
                            </div>
                            <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap; font-size: 0.7rem;">
                                <span style="color: #94a3b8;">凡例:</span>
                                <span style="color: #10b981;">● 今年度</span>
                                <span style="color: var(--color-primary-500);">● 昨年度</span>
                                <span style="color: #64748b;">● 2年前</span>
                            </div>
                        </div>
                    `;
                } else {
                    // Fallback logic
                    const totalUsed = yukyuHistory.reduce((acc, h) => acc + (h.used || 0), 0);
                    if (totalUsed > 0) {
                        usageDatesHtml = `
                             <div style="margin-top: 1rem;">
                                <h4 style="color: #94a3b8; margin-bottom: 0.5rem;">📋 使用履歴</h4>
                                <div style="padding: 1rem; text-align: center; border: 1px dashed rgba(255,255,255,0.2); border-radius: 8px;">
                                    <p style="color: #eab308; font-size: 0.9rem;">⚠️ 詳細な使用履歴が見つかりません</p>
                                    <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.3rem;">合計 ${totalUsed.toFixed(1)}日 使用されていますが、日付データがありません。</p>
                                </div>
                            </div>
                        `;
                    } else {
                        usageDatesHtml = `
                             <div style="margin-top: 1rem;">
                                <h4 style="color: #94a3b8; margin-bottom: 0.5rem;">📋 使用履歴</h4>
                                <div style="padding: 0.5rem; text-align: center; color: #64748b; font-size: 0.9rem;">
                                    使用履歴はありません
                                </div>
                            </div>
                        `;
                    }
                }

                // XSS prevention: escape all user data
                const safeEmpNum = App.utils.escapeHtml(emp.employeeNum);
                const safeEmpNumAttr = App.utils.escapeAttr(emp.employeeNum);
                const safeName = App.utils.escapeHtml(emp.name);

                // Name display logic
                const isRomaji = /^[A-Za-z0-9\s.,]+$/.test(emp.name);
                let displayName = safeName;
                if (isRomaji && emp.kana) {
                    displayName = `${App.utils.escapeHtml(emp.kana)} <span style="font-size: 0.7em; opacity: 0.7;">(${safeName})</span>`;
                }

                // Update title with Katakana if applicable
                const modalTitle = document.getElementById('modal-title');
                if (modalTitle) modalTitle.innerHTML = displayName;

                const safeHaken = App.utils.escapeHtml(emp.haken || employee.factory || '-');
                const safeType = App.utils.escapeHtml(employee.type || (emp.type === 'haken' ? '派遣' : emp.type === 'ukeoi' ? '請負' : 'スタッフ'));
                const safeStatus = App.utils.escapeHtml(employee.status || '在職中');
                const safeTotalAvailable = App.utils.safeNumber(totalAvailable);
                const safeRenewalDate = App.utils.escapeHtml(renewalDate);

                document.getElementById('modal-content').innerHTML = `
                    <!-- Información básica -->
                    <div class="bento-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 1.5rem; gap: 0.8rem;">
                        <div class="glass-panel" style="padding: 0.8rem; text-align: center;">
                            <div style="color: #94a3b8; font-size: 0.8rem;">社員番号</div>
                            <div style="font-size: 1.2rem; font-weight: bold;">${safeEmpNum}</div>
                        </div>
                        <div class="glass-panel" style="padding: 0.8rem; text-align: center;">
                            <div style="color: #94a3b8; font-size: 0.8rem;">派遣先</div>
                            <div style="font-size: 0.9rem; font-weight: bold;">${safeHaken}</div>
                        </div>
                        <div class="glass-panel" style="padding: 0.8rem; text-align: center;">
                            <div style="color: #94a3b8; font-size: 0.8rem;">タイプ</div>
                            <div style="font-size: 1rem;">${safeType}</div>
                        </div>
                        <div class="glass-panel" style="padding: 0.8rem; text-align: center;">
                            <div style="color: #94a3b8; font-size: 0.8rem;">ステータス</div>
                            <div style="font-size: 1rem; color: ${employee.status === '在職中' ? '#22c55e' : '#ef4444'};">${safeStatus}</div>
                        </div>
                    </div>

                    <!-- Balance total actual -->
                    <div class="glass-panel" style="padding: 1rem; margin-bottom: 1rem; background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(56, 189, 248, 0.2)); text-align: center;">
                        <div style="color: #94a3b8; font-size: 0.9rem;">💰 有給残日数 (合計)</div>
                        <div style="font-size: 2rem; font-weight: bold; color: #22c55e;">${safeTotalAvailable}日</div>
                        <div style="color: #94a3b8; font-size: 0.8rem;">次回付与: ${safeRenewalDate}</div>
                    </div>

                    <!-- Historial de 2 años -->
                    <h4 style="color: #94a3b8; margin-bottom: 0.5rem;">📊 年度別履歴 (過去2年)</h4>
                    ${historyHtml || '<p style="color: #64748b;">履歴データがありません</p>'}

                    <!-- Fechas de uso recientes -->
                    ${usageDatesHtml}

                    <!-- Botón de edición (v2.1 NEW) -->
                    <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
                        <button class="btn btn-primary" style="width: 100%;" data-action="edit-yukyu" data-employee-num="${safeEmpNumAttr}">
                            ✏️ 有給使用データを編集
                        </button>
                        <p style="text-align: center; color: #94a3b8; font-size: 0.75rem; margin-top: 0.5rem;">
                            日付の追加・修正・削除ができます
                        </p>
                    </div>

                    <!-- Botón de PDF (v2.4 NEW) -->
                    <div style="margin-top: 1rem;">
                        <button class="btn btn-secondary" style="width: 100%;" data-action="download-pdf" data-employee-num="${safeEmpNumAttr}">
                            📄 PDFレポートをダウンロード
                        </button>
                    </div>
                `;

                // Add event listeners safely (prevent XSS via onclick)
                document.querySelector('[data-action="edit-yukyu"]')?.addEventListener('click', () => {
                    App.ui.closeModal();
                    App.editYukyu.openModal(emp.employeeNum);
                });
                document.querySelector('[data-action="download-pdf"]')?.addEventListener('click', () => {
                    App.reports.downloadEmployeePDF(emp.employeeNum, App.state.year || null);
                });

            } catch (error) {
                console.error('Error loading employee details:', error);
                // Fallback a datos básicos si el API falla - XSS prevention: escape all user data
                const safeEmpNum = App.utils.escapeHtml(emp.employeeNum);
                const safeHaken = App.utils.escapeHtml(emp.haken);
                const safeGranted = App.utils.safeNumber(emp.granted);
                const safeUsed = App.utils.safeNumber(emp.used);
                const safeBalance = App.utils.safeNumber(emp.balance);
                const safeUsageRate = App.utils.safeNumber(emp.usageRate);

                document.getElementById('modal-content').innerHTML = `
                    <div class="bento-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 2rem;">
                        <div><span class="text-gray-400">ID:</span> ${safeEmpNum}</div>
                        <div><span class="text-gray-400">Factory:</span> ${safeHaken}</div>
                        <div><span class="text-gray-400">Granted:</span> ${safeGranted}</div>
                        <div><span class="text-gray-400">Used:</span> ${safeUsed}</div>
                        <div><span class="text-gray-400">Balance:</span> ${safeBalance}</div>
                        <div><span class="text-gray-400">Rate:</span> ${safeUsageRate}%</div>
                    </div>
                    <div style="text-align: center; color: #ef4444;">
                        <p style="font-weight: bold; margin-bottom: 0.5rem;">⚠️ 詳細データの取得に失敗しました</p>
                        <p style="font-family: monospace; font-size: 0.8rem; background: rgba(0,0,0,0.3); padding: 0.5rem; border-radius: 4px;">${error.message}</p>
                    </div>
                `;
            }
        },

        closeModal() {
            document.getElementById('detail-modal').classList.remove('active');
        }
    },

    charts: {
        destroy(id) {
            if (App.state.charts[id]) {
                App.state.charts[id].destroy();
            }
        },

        renderDistribution() {
            const container = document.getElementById('chart-distribution');
            if (!container) return;

            if (typeof ApexCharts === 'undefined') {
                container.textContent = 'Charts unavailable (ApexCharts not loaded)';
                return;
            }

            this.destroy('distribution');

            const data = App.data.getFiltered();
            const ranges = [0, 0, 0, 0]; // 0-25, 26-50, 51-75, 76-100

            data.forEach(e => {
                if (e.usageRate <= 25) ranges[0]++;
                else if (e.usageRate <= 50) ranges[1]++;
                else if (e.usageRate <= 75) ranges[2]++;
                else ranges[3]++;
            });

            const options = {
                series: ranges,
                chart: {
                    type: 'donut',
                    height: 320,
                    background: 'transparent',
                    animations: {
                        enabled: true,
                        easing: 'easeinout',
                        speed: 800,
                        animateGradually: {
                            enabled: true,
                            delay: 150
                        },
                        dynamicAnimation: {
                            enabled: true,
                            speed: 350
                        }
                    },
                    dropShadow: {
                        enabled: true,
                        top: 3,
                        left: 0,
                        blur: 10,
                        opacity: 0.3,
                        color: '#000'
                    }
                },
                labels: ['0-25%', '26-50%', '51-75%', '76-100%'],
                colors: ['var(--gray-300)', 'var(--color-info-light)', 'var(--color-primary-500)', 'var(--color-primary-700)'],
                legend: {
                    position: 'right',
                    labels: {
                        colors: '#64748b'
                    },
                    markers: {
                        width: 12,
                        height: 12,
                        radius: 3
                    }
                },
                plotOptions: {
                    pie: {
                        donut: {
                            size: '70%',
                            labels: {
                                show: true,
                                total: {
                                    show: true,
                                    label: 'Total',
                                    color: '#64748b',
                                    formatter: () => data.length
                                },
                                value: {
                                    color: '#0f172a',
                                    fontSize: '22px',
                                    fontWeight: 600
                                }
                            }
                        }
                    }
                },
                dataLabels: {
                    enabled: true,
                    style: {
                        fontSize: '14px',
                        fontWeight: 'bold'
                    },
                    dropShadow: {
                        enabled: true,
                        blur: 3,
                        opacity: 0.8
                    }
                },
                stroke: {
                    width: 0
                },
                tooltip: {
                    theme: 'dark',
                    y: {
                        formatter: function (value) {
                            return value + ' employees'
                        }
                    }
                }
            };

            App.state.charts['distribution'] = new ApexCharts(container, options);
            App.state.charts['distribution'].render();
        },

        async renderTrends() {
            const container = document.getElementById('chart-trends');
            if (!container) return;
            this.destroy('trends');

            if (typeof ApexCharts === 'undefined') {
                container.textContent = 'Charts unavailable (ApexCharts not loaded)';
                return;
            }

            let trendsData = Array(12).fill(0);
            try {
                if (App.state.year) {
                    const res = await fetch(`${App.config.apiBase}/yukyu/monthly-summary/${App.state.year}`);
                    const json = await res.json();
                    if (json.data) {
                        json.data.forEach(m => {
                            if (m.month >= 1 && m.month <= 12) {
                                trendsData[m.month - 1] = m.total_days;
                            }
                        });
                    }
                }
            } catch (e) { console.error("Trend fetch error", e); }

            const options = {
                series: [{
                    name: 'Days Used',
                    data: trendsData
                }],
                chart: {
                    type: 'area',
                    height: 320,
                    background: 'transparent',
                    toolbar: {
                        show: true,
                        tools: {
                            download: true,
                            zoom: true,
                            zoomin: true,
                            zoomout: true,
                            pan: false
                        }
                    },
                    animations: {
                        enabled: true,
                        easing: 'easeinout',
                        speed: 800,
                        animateGradually: {
                            enabled: true,
                            delay: 150
                        },
                        dynamicAnimation: {
                            enabled: true,
                            speed: 350
                        }
                    },
                    dropShadow: {
                        enabled: true,
                        top: 3,
                        left: 0,
                        blur: 15,
                        opacity: 0.2,
                        color: 'var(--color-primary-500)'
                    }
                },
                colors: ['var(--color-primary-500)'],
                fill: {
                    type: 'gradient',
                    gradient: {
                        shade: 'dark',
                        type: 'vertical',
                        shadeIntensity: 0.5,
                        gradientToColors: ['var(--color-primary-700)'],
                        opacityFrom: 0.7,
                        opacityTo: 0.2,
                        stops: [0, 100]
                    }
                },
                stroke: {
                    curve: 'smooth',
                    width: 3,
                    colors: ['var(--color-primary-500)']
                },
                dataLabels: {
                    enabled: false
                },
                markers: {
                    size: 5,
                    colors: ['var(--color-primary-500)'],
                    strokeColors: '#fff',
                    strokeWidth: 2,
                    hover: {
                        size: 7
                    }
                },
                xaxis: {
                    categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    labels: {
                        style: {
                            colors: '#94a3b8'
                        }
                    },
                    axisBorder: {
                        show: false
                    },
                    axisTicks: {
                        show: false
                    }
                },
                yaxis: {
                    labels: {
                        style: {
                            colors: '#94a3b8'
                        },
                        formatter: function (value) {
                            return Math.round(value)
                        }
                    }
                },
                grid: {
                    borderColor: 'rgba(255,255,255,0.05)',
                    strokeDashArray: 4,
                    xaxis: {
                        lines: {
                            show: false
                        }
                    }
                },
                tooltip: {
                    theme: 'dark',
                    y: {
                        formatter: function (value) {
                            return value.toFixed(1) + ' days'
                        }
                    }
                }
            };

            App.state.charts['trends'] = new ApexCharts(container, options);
            App.state.charts['trends'].render();
        },

        async renderTypes() {
            const ctx = document.getElementById('chart-types');
            if (!ctx) return;
            this.destroy('types');

            if (typeof Chart === 'undefined') {
                // Canvas exists but Chart.js is missing (CDN blocked/offline)
                return;
            }

            let typeData = { labels: ['Haken', 'Ukeoi', 'Staff'], data: [0, 0, 0] };
            try {
                if (App.state.year) {
                    const res = await fetch(`${App.config.apiBase}/yukyu/by-employee-type/${App.state.year}`);
                    // API returns generic format, check if json is correct
                    const json = await res.json();

                    // The endpoint structure might be slightly different depending on implementation
                    // Assuming structure based on previous context: { status: 'success', breakdown: { ... } }
                    if (json.data) {
                        typeData.data = [
                            json.data.hakenshain?.total_used || 0,
                            json.data.ukeoi?.total_used || 0,
                            json.data.staff?.total_used || 0
                        ];
                    } else if (json.breakdown) { // Adapting to likely structure
                        typeData.data = [
                            json.breakdown.hakenshain?.total_used || 0,
                            json.breakdown.ukeoi?.total_used || 0,
                            json.breakdown.staff?.total_used || 0
                        ];
                    }
                }
            } catch (e) { console.error("Type fetch error", e); }

            App.state.charts['types'] = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['Haken (Dispatch)', 'Ukeoi (Contract)', 'Staff'],
                    datasets: [{
                        data: typeData.data,
                        backgroundColor: ['var(--color-primary-500)', 'var(--color-primary-400)', 'var(--color-primary-700)'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: '#64748b' } }
                    }
                }
            });
        },

        async renderTop10() {
            const ctx = document.getElementById('chart-top10');
            if (!ctx) return;
            this.destroy('top10');

            if (typeof Chart === 'undefined') {
                return;
            }

            // Fetch Top 10 from API - only ACTIVE employees (在職中)
            let sorted = [];
            try {
                const year = App.state.year || new Date().getFullYear();
                const res = await fetch(`${App.config.apiBase}/analytics/top10-active/${year}`);
                const json = await res.json();
                if (json.status === 'success' && json.data) {
                    sorted = json.data;
                }
            } catch (e) {
                // Fallback to client-side calculation
                console.warn('Top10 API failed, using local data', e);
                sorted = [...App.data.getFiltered()].sort((a, b) => b.used - a.used).slice(0, 10);
            }

            App.state.charts['top10'] = new Chart(ctx, {
                type: 'bar',
                indexAxis: 'y',
                data: {
                    labels: sorted.map(e => e.name),
                    datasets: [{
                        label: 'Days Used (在職中のみ)',
                        data: sorted.map(e => e.used),
                        backgroundColor: 'rgba(251, 191, 36, 0.7)',
                        borderColor: '#fbbf24',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            ticks: { color: '#94a3b8', autoSkip: false },
                            grid: { display: false }
                        },
                        x: {
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#94a3b8' }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        },

        renderFactoryChart() {
            const container = document.getElementById('chart-factories');
            if (!container) return;

            if (typeof ApexCharts === 'undefined') {
                container.textContent = 'Charts unavailable (ApexCharts not loaded)';
                return;
            }

            this.destroy('factories');
            const stats = App.data.getFactoryStats().slice(0, 10); // Top 10

            const options = {
                series: [{
                    name: 'Days Used',
                    data: stats.map(s => s[1])
                }],
                chart: {
                    type: 'bar',
                    height: 500,
                    background: 'transparent',
                    toolbar: {
                        show: true
                    },
                    animations: {
                        enabled: true,
                        easing: 'easeinout',
                        speed: 800,
                        animateGradually: {
                            enabled: true,
                            delay: 150
                        },
                        dynamicAnimation: {
                            enabled: true,
                            speed: 350
                        }
                    }
                },
                plotOptions: {
                    bar: {
                        horizontal: true,
                        borderRadius: 8,
                        dataLabels: {
                            position: 'top'
                        },
                        distributed: true
                    }
                },
                colors: ['var(--color-primary-500)', 'var(--color-primary-400)', 'var(--color-primary-700)', 'var(--color-primary-800)', 'var(--color-primary-900)',
                    '#3b82f6', '#10b981', '#f59e0b', '#64748b', '#475569'],
                dataLabels: {
                    enabled: true,
                    style: {
                        fontSize: '12px',
                        colors: ['#fff']
                    },
                    formatter: function (value) {
                        return value.toFixed(1)
                    },
                    offsetX: 30
                },
                xaxis: {
                    categories: stats.map(s => s[0]),
                    labels: {
                        style: {
                            colors: '#94a3b8'
                        }
                    },
                    axisBorder: {
                        show: false
                    }
                },
                yaxis: {
                    labels: {
                        style: {
                            colors: '#94a3b8'
                        }
                    }
                },
                grid: {
                    borderColor: 'rgba(255,255,255,0.05)',
                    xaxis: {
                        lines: {
                            show: true
                        }
                    },
                    yaxis: {
                        lines: {
                            show: false
                        }
                    }
                },
                tooltip: {
                    theme: 'dark',
                    y: {
                        formatter: function (value) {
                            return value.toFixed(1) + ' days'
                        }
                    }
                },
                legend: {
                    show: false
                }
            };

            App.state.charts['factories'] = new ApexCharts(container, options);
            App.state.charts['factories'].render();
        }
    },

    events: {
        setupListeners() {
            // Modern event delegation for data-action attributes (WCAG compliant)
            document.addEventListener('click', (e) => {
                const target = e.target.closest('[data-action]');
                if (!target) return;

                const action = target.dataset.action;
                const args = [];

                // Special actions
                if (action === 'window.reload') {
                    window.location.reload();
                    return;
                }

                // Extract arguments from data attributes
                if (target.dataset.view) args.push(target.dataset.view);
                if (target.dataset.type) args.push(target.dataset.type);
                if (target.dataset.tab) args.push(target.dataset.tab);
                if (target.dataset.mode) args.push(target.dataset.mode);
                if (target.dataset.format) args.push(target.dataset.format);
                if (target.dataset.entity) args.push(target.dataset.entity);
                if (target.dataset.employeeNum) args.push(target.dataset.employeeNum);
                if (target.dataset.year) args.push(target.dataset.year);
                if (target.dataset.id) args.push(target.dataset.id);

                // Navigate to method and execute
                const parts = action.split('.');
                let context = App;
                for (let i = 0; i < parts.length - 1; i++) {
                    context = context[parts[i]];
                    if (!context) return;
                }
                const method = context[parts[parts.length - 1]];
                if (typeof method === 'function') {
                    e.preventDefault();
                    method.apply(context, args);
                }
            });

            // Close modal when clicking outside (backdrop click)
            document.getElementById('detail-modal').addEventListener('click', (e) => {
                if (e.target.id === 'detail-modal') App.ui.closeModal();
            });

            // Modal backdrop handlers for all modals
            const modalBackdropHandlers = [
                { id: 'confirm-modal', close: () => App.requests?.hideConfirmation?.() },
                { id: 'edit-yukyu-modal', close: () => App.editYukyu?.closeModal?.() },
                { id: 'audit-history-modal', close: () => App.auditHistory?.closeModal?.() },
                { id: 'import-report-modal', close: () => App.importReport?.closeModal?.() },
                { id: 'bulk-edit-modal', close: () => App.bulkEdit?.closeModal?.() }
            ];

            modalBackdropHandlers.forEach(({ id, close }) => {
                const modal = document.getElementById(id);
                if (modal) {
                    modal.addEventListener('click', (e) => {
                        if (e.target === modal) close();
                    });
                }
            });

            // Event delegation for employee rows (XSS-safe)
            const tableBody = document.getElementById('table-body');
            if (tableBody) {
                tableBody.addEventListener('click', (e) => {
                    const row = e.target.closest('.employee-row');
                    if (row && row.dataset.employeeNum) {
                        App.ui.openModal(row.dataset.employeeNum);
                    }
                });
            }

            // Event delegation for search results
            const searchResults = document.getElementById('emp-search-results');
            if (searchResults) {
                searchResults.addEventListener('click', (e) => {
                    const item = e.target.closest('.search-result-item');
                    if (item && item.dataset.employeeNum) {
                        App.requests.selectEmployee(item.dataset.employeeNum);
                    }
                });
            }

            // Event delegation for leave request actions
            const pendingList = document.getElementById('pending-requests');
            if (pendingList) {
                pendingList.addEventListener('click', (e) => {
                    const approveBtn = e.target.closest('.btn-approve');
                    const rejectBtn = e.target.closest('.btn-reject');
                    const cancelBtn = e.target.closest('.btn-cancel');
                    if (approveBtn && approveBtn.dataset.requestId) {
                        App.requests.approve(parseInt(approveBtn.dataset.requestId));
                    }
                    if (rejectBtn && rejectBtn.dataset.requestId) {
                        App.requests.reject(parseInt(rejectBtn.dataset.requestId));
                    }
                    if (cancelBtn && cancelBtn.dataset.requestId) {
                        App.requests.cancel(parseInt(cancelBtn.dataset.requestId));
                    }
                });
            }

            // Event delegation for history table actions (revert)
            const historyTable = document.getElementById('requests-history');
            if (historyTable) {
                historyTable.addEventListener('click', (e) => {
                    const revertBtn = e.target.closest('.btn-revert');
                    if (revertBtn && revertBtn.dataset.requestId) {
                        App.requests.revert(parseInt(revertBtn.dataset.requestId));
                    }
                });
            }

            // Keyboard navigation
            document.addEventListener('keydown', (e) => {
                // ESC to close modal
                if (e.key === 'Escape') {
                    const modal = document.getElementById('detail-modal');
                    if (modal && modal.classList.contains('active')) {
                        App.ui.closeModal();
                    }
                    // Also close mobile menu on ESC
                    App.ui.closeMobileMenu();
                }
            });

            // Mobile hamburger menu toggle
            const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
            const sidebarOverlay = document.getElementById('sidebar-overlay');

            if (mobileMenuToggle) {
                mobileMenuToggle.addEventListener('click', () => {
                    App.ui.toggleMobileMenu();
                });
            }

            if (sidebarOverlay) {
                sidebarOverlay.addEventListener('click', () => {
                    App.ui.closeMobileMenu();
                });
            }

            // Close mobile menu when nav item is clicked
            document.querySelectorAll('.nav-item').forEach(item => {
                item.addEventListener('click', () => {
                    App.ui.closeMobileMenu();
                });
            });

            // Handle window resize to keep charts synchronized with layout
            let resizeTimer;
            window.addEventListener('resize', () => {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(() => {
                    // Only trigger if we are in a view that has charts
                    const viewsWithCharts = ['dashboard', 'factories', 'analytics'];
                    if (viewsWithCharts.includes(App.state.currentView)) {
                        // Resynchronizing charts after resize
                        App.ui.ensureChartsVisible();
                    }
                }, 250);
            });
        }
    },

    // ========================================
    // REQUESTS MODULE (申請)
    // ========================================
    requests: {
        selectedEmployee: null,
        searchTimeout: null,
        factories: [],

        async loadFactories() {
            try {
                const res = await fetch(`${App.config.apiBase}/factories?status=在職中`);
                const json = await res.json();

                // API returns { factories: [...] } not { data: [...] }
                if (json.factories) {
                    this.factories = json.factories;
                    const select = document.getElementById('factory-filter');
                    if (select) {
                        // Keep first option (All Factories)
                        select.innerHTML = '<option value="">すべての工場 (All Factories)</option>';
                        this.factories.forEach(factory => {
                            const opt = document.createElement('option');
                            opt.value = factory;
                            opt.textContent = factory;
                            select.appendChild(opt);
                        });
                    }
                }
            } catch (e) {
                console.error('Failed to load factories:', e);
            }
        },

        filterByFactory() {
            const factory = document.getElementById('factory-filter').value;
            const searchInput = document.getElementById('emp-search');
            const query = searchInput.value;

            // If factory is selected, show employees from that factory
            if (factory) {
                this.searchWithFactory(query, factory);
            } else {
                // If no factory selected and no query, clear results
                if (!query || query.length < 2) {
                    document.getElementById('emp-search-results').innerHTML = '';
                } else {
                    this.searchEmployee(query);
                }
            }
        },

        async searchWithFactory(query, factory) {
            try {
                let url = `${App.config.apiBase}/employees/search?status=在職中`;
                if (query) url += `&q=${encodeURIComponent(query)}`;
                if (factory) url += `&factory=${encodeURIComponent(factory)}`;

                const res = await fetch(url);
                const json = await res.json();

                const container = document.getElementById('emp-search-results');
                if (json.data && json.data.length > 0) {
                    container.innerHTML = json.data.slice(0, 15).map(emp => {
                        const empNum = App.utils.escapeAttr(emp.employee_num);
                        const name = App.utils.escapeHtml(emp.name);
                        const kana = emp.kana ? App.utils.escapeHtml(emp.kana) : '';
                        const empFactory = App.utils.escapeHtml(emp.factory || '-');
                        const type = App.utils.escapeHtml(emp.type);
                        const kanaDisplay = kana ? `<div style="font-size: 0.75rem; color: #94a3b8;">${kana}</div>` : '';
                        return `
                        <div class="search-result-item" data-employee-num="${empNum}"
                             style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; cursor: pointer; transition: all 0.2s;">
                            <div style="font-weight: 600;">${name}</div>
                            ${kanaDisplay}
                            <div style="font-size: 0.85rem; color: var(--muted);">${empNum} | ${empFactory} | ${type}</div>
                        </div>
                    `}).join('');
                } else {
                    container.innerHTML = '<div style="padding: 1rem; color: var(--muted); text-align: center;">No results found</div>';
                }
            } catch (e) {
                console.error(e);
            }
        },

        async searchEmployee(query) {
            if (this.searchTimeout) clearTimeout(this.searchTimeout);

            const factory = document.getElementById('factory-filter')?.value || '';

            // If factory is selected, allow search with shorter query
            if (!factory && (!query || query.length < 2)) {
                document.getElementById('emp-search-results').innerHTML = '';
                return;
            }

            this.searchTimeout = setTimeout(async () => {
                try {
                    let url = `${App.config.apiBase}/employees/search?status=在職中`;
                    if (query) url += `&q=${encodeURIComponent(query)}`;
                    if (factory) url += `&factory=${encodeURIComponent(factory)}`;

                    const res = await fetch(url);
                    const json = await res.json();

                    const container = document.getElementById('emp-search-results');
                    if (json.data && json.data.length > 0) {
                        // Using data attributes instead of inline onclick (XSS prevention)
                        container.innerHTML = json.data.slice(0, 15).map(emp => {
                            const empNum = App.utils.escapeAttr(emp.employee_num);
                            const name = App.utils.escapeHtml(emp.name);
                            const kana = emp.kana ? App.utils.escapeHtml(emp.kana) : '';
                            const empFactory = App.utils.escapeHtml(emp.factory || '-');
                            const type = App.utils.escapeHtml(emp.type);
                            const kanaDisplay = kana ? `<div style="font-size: 0.75rem; color: #94a3b8;">${kana}</div>` : '';
                            return `
                            <div class="search-result-item" data-employee-num="${empNum}"
                                 style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; cursor: pointer; transition: all 0.2s;">
                                <div style="font-weight: 600;">${name}</div>
                                ${kanaDisplay}
                                <div style="font-size: 0.85rem; color: var(--muted);">${empNum} | ${empFactory} | ${type}</div>
                            </div>
                        `}).join('');
                    } else {
                        container.innerHTML = '<div style="padding: 1rem; color: var(--muted); text-align: center;">No results found</div>';
                    }
                } catch (e) {
                    console.error(e);
                }
            }, 300);
        },

        async selectEmployee(empNum) {
            try {
                const res = await fetch(`${App.config.apiBase}/employees/${empNum}/leave-info`);
                const json = await res.json();

                if (json.employee) {
                    this.selectedEmployee = json;

                    // Update UI
                    document.getElementById('selected-emp-info').style.display = 'block';
                    document.getElementById('selected-emp-name').innerText = json.employee.name;
                    document.getElementById('selected-emp-details').innerText =
                        `${json.employee.employee_num} | ${json.employee.factory || '-'} | ${json.employee.type}`;
                    document.getElementById('selected-emp-balance').innerText = json.total_available.toFixed(1) + '日';

                    // Show hourly wage info if available
                    const hourlyWageInfo = document.getElementById('hourly-wage-info');
                    if (json.hourly_wage && json.hourly_wage > 0) {
                        hourlyWageInfo.style.display = 'block';
                        document.getElementById('selected-emp-wage').innerText = `¥${json.hourly_wage.toLocaleString()}`;
                        const totalHours = json.total_hours_available || (json.total_available * 8);
                        document.getElementById('selected-emp-hours').innerText = `${totalHours.toFixed(0)}時間`;
                    } else {
                        hourlyWageInfo.style.display = 'none';
                    }

                    // Render yukyu history table (2 years)
                    this.renderYukyuHistoryTable(json.yukyu_history || []);

                    // Show usage history
                    this.renderUsageHistory(json);

                    // Clear search and mark as valid
                    document.getElementById('emp-search').value = json.employee.name;
                    document.getElementById('emp-search').classList.add('is-valid');
                    document.getElementById('emp-search-results').innerHTML = '';

                    // Update progress steps
                    this.updateProgressSteps(2);

                    // Update cost estimate if hourly is selected
                    this.updateCostEstimate();
                }
            } catch (e) {
                App.ui.showToast('error', 'Failed to load employee info');
            }
        },

        renderYukyuHistoryTable(yukyuHistory) {
            const tbody = document.getElementById('yukyu-history-tbody');
            if (!tbody) return;

            if (!yukyuHistory || yukyuHistory.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="padding: 1rem; text-align: center; color: var(--muted);">
                            履歴データがありません
                        </td>
                    </tr>
                `;
                return;
            }

            // Sort by year descending (newest first)
            const sortedHistory = [...yukyuHistory].sort((a, b) => b.year - a.year);

            // Calculate totals
            const totals = {
                granted: 0,
                used: 0,
                balance: 0
            };

            let rows = sortedHistory.map(h => {
                const granted = h.granted || 0;
                const used = h.used || 0;
                const balance = h.balance || 0;
                const rate = h.usage_rate || 0;

                totals.granted += granted;
                totals.used += used;
                totals.balance += balance;

                // Color based on usage rate
                const rateColor = rate >= 75 ? 'var(--success)' : rate >= 50 ? 'var(--warning)' : 'var(--error)';
                const balanceColor = balance > 5 ? 'var(--success)' : balance > 0 ? 'var(--warning)' : 'var(--error)';

                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <td style="padding: 0.5rem; font-weight: 600;">${h.year}年度</td>
                        <td style="padding: 0.5rem; text-align: center;">${granted.toFixed(1)}</td>
                        <td style="padding: 0.5rem; text-align: center;">${used.toFixed(1)}</td>
                        <td style="padding: 0.5rem; text-align: center; color: ${balanceColor}; font-weight: 600;">${balance.toFixed(1)}</td>
                        <td style="padding: 0.5rem; text-align: center;">
                            <span style="display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; background: ${rateColor}20; color: ${rateColor}; font-weight: 600;">
                                ${rate.toFixed(1)}%
                            </span>
                        </td>
                    </tr>
                `;
            }).join('');

            // Add totals row
            const avgRate = totals.granted > 0 ? (totals.used / totals.granted * 100) : 0;
            rows += `
                <tr style="background: rgba(56, 189, 248, 0.1); font-weight: 600;">
                    <td style="padding: 0.5rem; border-radius: 0 0 0 8px;">合計</td>
                    <td style="padding: 0.5rem; text-align: center;">${totals.granted.toFixed(1)}</td>
                    <td style="padding: 0.5rem; text-align: center;">${totals.used.toFixed(1)}</td>
                    <td style="padding: 0.5rem; text-align: center; color: var(--success);">${totals.balance.toFixed(1)}</td>
                    <td style="padding: 0.5rem; text-align: center; border-radius: 0 0 8px 0;">${avgRate.toFixed(1)}%</td>
                </tr>
            `;

            tbody.innerHTML = rows;
        },

        toggleLeaveType() {
            const leaveType = document.getElementById('leave-type').value;
            const daysContainer = document.getElementById('days-input-container');
            const hoursContainer = document.getElementById('hours-input-container');
            const costContainer = document.getElementById('cost-estimate-container');

            if (leaveType === 'hourly') {
                daysContainer.style.display = 'none';
                hoursContainer.style.display = 'block';
                costContainer.style.display = 'block';
                this.updateCostEstimate();
            } else {
                daysContainer.style.display = 'block';
                hoursContainer.style.display = 'none';
                costContainer.style.display = 'none';

                // Set default days based on type
                const daysInput = document.getElementById('days-requested');
                if (leaveType === 'half_am' || leaveType === 'half_pm') {
                    daysInput.value = '0.5';
                } else {
                    daysInput.value = '1';
                }
            }
        },

        updateCostEstimate() {
            if (!this.selectedEmployee || !this.selectedEmployee.hourly_wage) {
                document.getElementById('cost-estimate').innerText = '-';
                return;
            }

            const hours = parseFloat(document.getElementById('hours-requested').value) || 0;
            const wage = this.selectedEmployee.hourly_wage;
            const cost = hours * wage;

            document.getElementById('cost-estimate').innerText = `¥${cost.toLocaleString()}`;
        },

        renderUsageHistory(json) {
            const container = document.getElementById('usage-history-container');
            const summaryEl = document.getElementById('usage-history-summary');
            const detailEl = document.getElementById('usage-history-detail');

            // Check if we have history data
            const history = json.history || [];
            const usageHistory = json.usage_history || [];

            if (history.length === 0 && usageHistory.length === 0) {
                container.style.display = 'none';
                return;
            }

            container.style.display = 'block';

            // Build summary by year (from history data)
            let summaryHtml = '<div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;">';
            history.forEach(h => {
                const year = h.year;
                const used = h.used || 0;
                const granted = h.granted || 0;
                summaryHtml += `
                    <div style="padding: 0.5rem 0.75rem; background: rgba(255,255,255,0.05); border-radius: 6px; font-size: 0.8rem;">
                        <span style="color: var(--primary); font-weight: 600;">${year}年</span>
                        <span style="margin-left: 0.5rem;">使用: ${used}日</span>
                        <span style="margin-left: 0.5rem; color: var(--muted);">/ ${granted}日</span>
                    </div>
                `;
            });
            summaryHtml += '</div>';
            summaryEl.innerHTML = summaryHtml;

            // Build detail list (individual usage dates)
            if (usageHistory.length > 0) {
                let detailHtml = '<table style="width: 100%; font-size: 0.8rem; border-collapse: collapse;">';
                detailHtml += '<thead><tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">';
                detailHtml += '<th style="text-align: left; padding: 0.5rem;">日付</th>';
                detailHtml += '<th style="text-align: right; padding: 0.5rem;">日数</th>';
                detailHtml += '<th style="text-align: right; padding: 0.5rem;">年度</th>';
                detailHtml += '</tr></thead><tbody>';

                usageHistory.forEach(u => {
                    const date = u.date || '-';
                    const days = u.days || 0;
                    const year = u.year || '-';
                    detailHtml += `
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 0.5rem;">${App.utils.escapeHtml(date)}</td>
                            <td style="text-align: right; padding: 0.5rem;">${days}日</td>
                            <td style="text-align: right; padding: 0.5rem; color: var(--muted);">${year}</td>
                        </tr>
                    `;
                });

                detailHtml += '</tbody></table>';
                detailEl.innerHTML = detailHtml;
            } else {
                detailEl.innerHTML = '<div style="color: var(--muted); font-size: 0.8rem; padding: 0.5rem;">使用履歴の詳細はありません</div>';
            }
        },

        toggleUsageHistory() {
            const detailEl = document.getElementById('usage-history-detail');
            const btn = event.target;
            if (detailEl.style.display === 'none') {
                detailEl.style.display = 'block';
                btn.innerText = '詳細を隠す';
            } else {
                detailEl.style.display = 'none';
                btn.innerText = '詳細を表示';
            }
        },

        // ===== UX IMPROVEMENTS =====

        // Update progress steps
        updateProgressSteps(step) {
            for (let i = 1; i <= 3; i++) {
                const el = document.getElementById(`step-${i}`);
                el.classList.remove('active', 'completed');
                if (i < step) el.classList.add('completed');
                if (i === step) el.classList.add('active');
            }
        },

        // Validate dates inline
        validateDates() {
            const startDate = document.getElementById('start-date');
            const endDate = document.getElementById('end-date');
            const startValidation = document.getElementById('start-date-validation');
            const endValidation = document.getElementById('end-date-validation');
            let isValid = true;

            // Reset
            startDate.classList.remove('is-valid', 'is-invalid');
            endDate.classList.remove('is-valid', 'is-invalid');
            startValidation.classList.remove('show', 'error', 'success');
            endValidation.classList.remove('show', 'error', 'success');

            const today = new Date().toISOString().split('T')[0];

            if (startDate.value) {
                if (startDate.value < today) {
                    startDate.classList.add('is-invalid');
                    startValidation.textContent = '⚠️ 過去の日付は選択できません';
                    startValidation.classList.add('show', 'error');
                    isValid = false;
                } else {
                    startDate.classList.add('is-valid');
                }
            }

            if (endDate.value && startDate.value) {
                if (endDate.value < startDate.value) {
                    endDate.classList.add('is-invalid');
                    endValidation.textContent = '⚠️ 終了日は開始日以降にしてください';
                    endValidation.classList.add('show', 'error');
                    isValid = false;
                } else {
                    endDate.classList.add('is-valid');
                }
            }

            // Update progress if employee selected and dates valid
            if (this.selectedEmployee && startDate.value && endDate.value && isValid) {
                this.updateProgressSteps(2);
            }

            return isValid;
        },

        // Validate days inline
        validateDays() {
            const daysInput = document.getElementById('days-requested');
            const validation = document.getElementById('days-validation');
            const days = parseFloat(daysInput.value) || 0;

            daysInput.classList.remove('is-valid', 'is-invalid');
            validation.classList.remove('show', 'error', 'warning', 'success');

            if (!this.selectedEmployee) return;

            const available = this.selectedEmployee.total_available || 0;

            if (days <= 0) {
                daysInput.classList.add('is-invalid');
                validation.textContent = '⚠️ 日数を入力してください';
                validation.classList.add('show', 'error');
                return false;
            }

            if (days > available) {
                daysInput.classList.add('is-invalid');
                // Escape numeric value to prevent XSS
                validation.textContent = `⚠️ 残り${App.utils.escapeHtml(String(available))}日を超えています`;
                validation.classList.add('show', 'error');
                return false;
            }

            if (days > available * 0.8) {
                daysInput.classList.add('is-valid');
                validation.textContent = `ℹ️ 残り${App.utils.escapeHtml((available - days).toFixed(1))}日になります`;
                validation.classList.add('show', 'warning');
                return true;
            }

            daysInput.classList.add('is-valid');
            return true;
        },

        // Validate hours inline
        validateHours() {
            const hoursInput = document.getElementById('hours-requested');
            const validation = document.getElementById('hours-validation');
            const hours = parseFloat(hoursInput.value) || 0;

            hoursInput.classList.remove('is-valid', 'is-invalid');
            validation.classList.remove('show', 'error', 'warning', 'success');

            if (!this.selectedEmployee) return;

            const totalHours = this.selectedEmployee.total_hours_available || (this.selectedEmployee.total_available * 8);

            if (hours <= 0 || hours > 7) {
                hoursInput.classList.add('is-invalid');
                validation.textContent = '⚠️ 1〜7時間の範囲で入力してください';
                validation.classList.add('show', 'error');
                return false;
            }

            if (hours > totalHours) {
                hoursInput.classList.add('is-invalid');
                validation.textContent = `⚠️ 残り${App.utils.escapeHtml(totalHours.toFixed(0))}時間を超えています`;
                validation.classList.add('show', 'error');
                return false;
            }

            hoursInput.classList.add('is-valid');
            return true;
        },

        // Update character counter
        updateCharCounter() {
            const textarea = document.getElementById('leave-reason');
            const counter = document.getElementById('reason-char-counter');
            const length = textarea.value.length;
            const max = 200;

            counter.textContent = `${length} / ${max}`;
            counter.classList.remove('warning', 'danger');

            if (length > max * 0.9) {
                counter.classList.add('danger');
            } else if (length > max * 0.7) {
                counter.classList.add('warning');
            }
        },

        // Show confirmation modal
        showConfirmation() {
            // Validate all fields first
            if (!this.selectedEmployee) {
                App.ui.showToast('error', '従業員を選択してください');
                document.getElementById('emp-search').focus();
                return;
            }

            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;

            if (!startDate || !endDate) {
                App.ui.showToast('error', '日付を入力してください');
                return;
            }

            if (!this.validateDates()) {
                App.ui.showToast('error', '日付を確認してください');
                return;
            }

            const leaveType = document.getElementById('leave-type').value;
            const isHourly = leaveType === 'hourly';

            if (isHourly && !this.validateHours()) {
                return;
            } else if (!isHourly && !this.validateDays()) {
                return;
            }

            // Update progress to step 3
            this.updateProgressSteps(3);

            // Populate confirmation modal
            document.getElementById('confirm-employee').textContent = this.selectedEmployee.employee.name;
            document.getElementById('confirm-factory').textContent = this.selectedEmployee.employee.factory || '-';
            document.getElementById('confirm-dates').textContent = `${startDate} 〜 ${endDate}`;

            const typeLabels = {
                'full': '全日休暇',
                'half_am': '午前半休',
                'half_pm': '午後半休',
                'hourly': '時間休'
            };
            document.getElementById('confirm-type').textContent = typeLabels[leaveType] || leaveType;

            if (isHourly) {
                const hours = parseFloat(document.getElementById('hours-requested').value) || 0;
                document.getElementById('confirm-amount').textContent = `${hours}時間`;

                const wage = this.selectedEmployee.hourly_wage || 0;
                const cost = hours * wage;
                document.getElementById('confirm-cost').textContent = `¥${cost.toLocaleString()}`;
                document.getElementById('confirm-cost-row').style.display = 'flex';
            } else {
                const days = parseFloat(document.getElementById('days-requested').value) || 0;
                document.getElementById('confirm-amount').textContent = `${days}日`;
                document.getElementById('confirm-cost-row').style.display = 'none';
            }

            const available = this.selectedEmployee.total_available || 0;
            const requested = isHourly
                ? (parseFloat(document.getElementById('hours-requested').value) || 0) / 8
                : (parseFloat(document.getElementById('days-requested').value) || 0);
            const remaining = (available - requested).toFixed(1);
            document.getElementById('confirm-balance').textContent = `${available}日 → ${remaining}日`;

            const reason = document.getElementById('leave-reason').value || '(なし)';
            document.getElementById('confirm-reason').textContent = reason;

            // Show modal
            document.getElementById('confirm-modal').classList.add('active');
        },

        hideConfirmation() {
            document.getElementById('confirm-modal').classList.remove('active');
            this.updateProgressSteps(2);
        },

        async submitConfirmed() {
            // Add loading state to button
            const submitBtn = document.getElementById('confirm-submit-btn');
            submitBtn.classList.add('is-loading');

            try {
                await this.submit();
                this.hideConfirmation();
            } finally {
                submitBtn.classList.remove('is-loading');
            }
        },

        async submit() {
            if (!this.selectedEmployee) {
                App.ui.showToast('error', '従業員を選択してください');
                return;
            }

            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            const leaveType = document.getElementById('leave-type').value;
            const reason = document.getElementById('leave-reason').value;

            // Determine days and hours based on leave type
            let daysRequested = 0;
            let hoursRequested = 0;

            if (leaveType === 'hourly') {
                hoursRequested = parseFloat(document.getElementById('hours-requested').value) || 0;
                daysRequested = hoursRequested / 8; // Convert hours to days for balance check
            } else {
                daysRequested = parseFloat(document.getElementById('days-requested').value) || 0;
            }

            if (!startDate || !endDate) {
                App.ui.showToast('error', '日付を入力してください');
                return;
            }

            // Validate based on leave type
            if (leaveType === 'hourly') {
                if (hoursRequested <= 0 || hoursRequested > 7) {
                    App.ui.showToast('error', '時間数は1〜7時間の範囲で入力してください');
                    return;
                }
                const totalHoursAvailable = this.selectedEmployee.total_hours_available || (this.selectedEmployee.total_available * 8);
                if (hoursRequested > totalHoursAvailable) {
                    App.ui.showToast('error', `残時間が不足しています (残り: ${totalHoursAvailable.toFixed(0)}時間)`);
                    return;
                }
            } else {
                if (daysRequested > this.selectedEmployee.total_available) {
                    App.ui.showToast('error', `残日数が不足しています (残り: ${this.selectedEmployee.total_available}日)`);
                    return;
                }
            }

            // Calculate cost estimate for hourly leave
            const hourlyWage = this.selectedEmployee.hourly_wage || 0;
            const costEstimate = leaveType === 'hourly' ? hoursRequested * hourlyWage : 0;

            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        employee_num: this.selectedEmployee.employee.employee_num,
                        employee_name: this.selectedEmployee.employee.name,
                        start_date: startDate,
                        end_date: endDate,
                        days_requested: daysRequested,
                        hours_requested: hoursRequested,
                        leave_type: leaveType,
                        reason: reason,
                        hourly_wage: hourlyWage,
                        cost_estimate: costEstimate
                    })
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Request failed');
                }

                const typeLabel = leaveType === 'hourly' ? `${hoursRequested}時間` : `${daysRequested}日`;
                App.ui.showToast('success', `申請が送信されました (${typeLabel})`);
                this.resetForm();
                this.loadPending();
                this.loadHistory();

            } catch (e) {
                App.ui.showToast('error', e.message);
            } finally {
                App.ui.hideLoading();
            }
        },

        resetForm() {
            this.selectedEmployee = null;
            document.getElementById('factory-filter').value = '';
            document.getElementById('emp-search').value = '';
            document.getElementById('emp-search-results').innerHTML = '';
            document.getElementById('selected-emp-info').style.display = 'none';
            document.getElementById('hourly-wage-info').style.display = 'none';
            document.getElementById('usage-history-container').style.display = 'none';
            document.getElementById('start-date').value = '';
            document.getElementById('end-date').value = '';
            document.getElementById('days-requested').value = '1';
            document.getElementById('hours-requested').value = '1';
            document.getElementById('leave-type').value = 'full';
            document.getElementById('leave-reason').value = '';

            // Reset to days mode
            document.getElementById('days-input-container').style.display = 'block';
            document.getElementById('hours-input-container').style.display = 'none';
            document.getElementById('cost-estimate-container').style.display = 'none';

            // Reset validation states
            ['emp-search', 'start-date', 'end-date', 'days-requested', 'hours-requested'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.classList.remove('is-valid', 'is-invalid');
            });

            // Reset validation messages
            ['emp-search-validation', 'start-date-validation', 'end-date-validation', 'days-validation', 'hours-validation'].forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    el.classList.remove('show', 'error', 'success', 'warning');
                    el.innerHTML = '';
                }
            });

            // Reset progress steps
            this.updateProgressSteps(1);

            // Reset char counter
            const charCounter = document.getElementById('reason-char-counter');
            if (charCounter) charCounter.textContent = '0 / 200';
        },

        async loadPending() {
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests?status=PENDING`);
                const json = await res.json();

                const container = document.getElementById('pending-requests');
                if (json.data && json.data.length > 0) {
                    container.innerHTML = json.data.map(req => {
                        // Display hours or days based on leave type
                        const isHourly = req.leave_type === 'hourly';
                        const duration = isHourly
                            ? `${App.utils.safeNumber(req.hours_requested)}時間`
                            : `${App.utils.safeNumber(req.days_requested)}日`;
                        const typeLabel = {
                            'full': '全日',
                            'half_am': '午前半休',
                            'half_pm': '午後半休',
                            'hourly': '時間休'
                        }[req.leave_type] || '';
                        const costInfo = isHourly && req.cost_estimate > 0
                            ? `<div style="font-size: 0.8rem; color: var(--warning); margin-top: 0.25rem;">💰 見積: ¥${App.utils.safeNumber(req.cost_estimate).toLocaleString()}</div>`
                            : '';

                        // XSS prevention: escape all user data and use data attributes
                        const empName = App.utils.escapeHtml(req.employee_name);
                        const startDate = App.utils.escapeHtml(req.start_date);
                        const endDate = App.utils.escapeHtml(req.end_date);
                        const reason = App.utils.escapeHtml(req.reason || '-');
                        const reqId = parseInt(req.id) || 0;

                        return `
                            <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.75rem;">
                                <div class="flex-between">
                                    <div>
                                        <div style="font-weight: 600;">${empName}</div>
                                        <div style="font-size: 0.85rem; color: var(--muted);">
                                            ${startDate} 〜 ${endDate}
                                            <span class="badge badge-info" style="margin-left: 0.5rem; padding: 0.15rem 0.5rem; font-size: 0.7rem;">${typeLabel}</span>
                                            (${duration})
                                        </div>
                                        <div style="font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem;">${reason}</div>
                                        ${costInfo}
                                    </div>
                                    <div style="display: flex; gap: 0.5rem;">
                                        <button class="btn btn-glass btn-approve" data-request-id="${reqId}"
                                            style="background: rgba(52, 211, 153, 0.2); padding: 0.5rem 1rem;">✓ 承認</button>
                                        <button class="btn btn-glass btn-reject" data-request-id="${reqId}"
                                            style="background: rgba(248, 113, 113, 0.2); padding: 0.5rem 1rem;">✗ 却下</button>
                                        <button class="btn btn-glass btn-cancel" data-request-id="${reqId}"
                                            style="background: rgba(148, 163, 184, 0.2); padding: 0.5rem 0.75rem;" title="キャンセル">🗑</button>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 2rem;">承認待ちの申請はありません</div>';
                }
            } catch (e) {
                console.error(e);
            }
        },

        async loadHistory() {
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests`);
                const json = await res.json();

                const tbody = document.getElementById('requests-history');
                if (json.data && json.data.length > 0) {
                    tbody.innerHTML = json.data.map(req => {
                        const statusBadge = req.status === 'APPROVED' ? 'badge-success' :
                            req.status === 'REJECTED' ? 'badge-danger' :
                                req.status === 'CANCELLED' ? 'badge-info' : 'badge-warning';
                        const statusText = req.status === 'APPROVED' ? '承認済' :
                            req.status === 'REJECTED' ? '却下' :
                                req.status === 'CANCELLED' ? '取消済' : '審査中';

                        // Display hours or days based on leave type
                        const isHourly = req.leave_type === 'hourly';
                        const duration = isHourly
                            ? `${App.utils.safeNumber(req.hours_requested)}時間`
                            : `${App.utils.safeNumber(req.days_requested)}日`;
                        const typeLabel = {
                            'full': '全日',
                            'half_am': '午前半休',
                            'half_pm': '午後半休',
                            'hourly': '時間休'
                        }[req.leave_type] || '全日';

                        // XSS prevention: escape all user data
                        const safeId = parseInt(req.id) || 0;
                        const safeName = App.utils.escapeHtml(req.employee_name);
                        const safeStartDate = App.utils.escapeHtml(req.start_date);
                        const safeEndDate = App.utils.escapeHtml(req.end_date);
                        const safeReason = App.utils.escapeHtml(req.reason || '-');
                        const safeRequestedAt = App.utils.escapeHtml(req.requested_at?.slice(0, 10) || '-');

                        // Show revert button only for approved requests
                        const actionBtn = req.status === 'APPROVED'
                            ? `<button class="btn btn-glass btn-revert" data-request-id="${safeId}"
                                style="padding: 0.25rem 0.5rem; font-size: 0.7rem; background: rgba(251, 191, 36, 0.2);"
                                title="承認を取り消す">↩ 取消</button>`
                            : '-';

                        return `
                            <tr>
                                <td>${safeId}</td>
                                <td>${safeName}</td>
                                <td>${safeStartDate} 〜 ${safeEndDate}</td>
                                <td>
                                    <span class="badge badge-info" style="margin-right: 0.25rem; padding: 0.1rem 0.4rem; font-size: 0.65rem;">${typeLabel}</span>
                                    ${duration}
                                </td>
                                <td>${safeReason}</td>
                                <td><span class="badge ${statusBadge}">${statusText}</span></td>
                                <td>${safeRequestedAt}</td>
                                <td>${actionBtn}</td>
                            </tr>
                        `;
                    }).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem;">申請履歴がありません</td></tr>';
                }
            } catch (e) {
                console.error(e);
            }
        },

        async approve(requestId) {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests/${requestId}/approve`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ approved_by: 'Manager' })
                });

                if (!res.ok) throw new Error('Approval failed');

                App.ui.showToast('success', '申請を承認しました');
                App.visualizations.showConfetti(); // Celebrate approval!
                this.loadPending();
                this.loadHistory();
                App.data.fetchEmployees(App.state.year); // Refresh balance

            } catch (e) {
                App.ui.showToast('error', e.message);
            } finally {
                App.ui.hideLoading();
            }
        },

        async reject(requestId) {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests/${requestId}/reject`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rejected_by: 'Manager' })
                });

                if (!res.ok) throw new Error('Rejection failed');

                App.ui.showToast('success', '申請を却下しました');
                this.loadPending();
                this.loadHistory();

            } catch (e) {
                App.ui.showToast('error', e.message);
            } finally {
                App.ui.hideLoading();
            }
        },

        async cancel(requestId) {
            // Use modern dialog if available
            let confirmed = false;
            if (typeof ModernUI !== 'undefined' && ModernUI.Dialog) {
                const result = await ModernUI.Dialog.show({
                    type: 'danger',
                    title: '申請キャンセル',
                    message: `申請 #${requestId} をキャンセルしますか？この操作は取り消せません。`,
                    confirmText: 'キャンセルする',
                    cancelText: '戻る',
                    danger: true
                });
                confirmed = result.confirmed;
            } else {
                confirmed = confirm(`申請 #${requestId} をキャンセルしますか？\n\nこの操作は取り消せません。`);
            }

            if (!confirmed) return;

            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests/${requestId}`, {
                    method: 'DELETE'
                });

                if (!res.ok) {
                    const errorData = await res.json();
                    throw new Error(errorData.detail || 'Cancel failed');
                }

                App.ui.showToast('success', '申請をキャンセルしました');
                this.loadPending();
                this.loadHistory();

            } catch (e) {
                App.ui.showToast('error', e.message);
            } finally {
                App.ui.hideLoading();
            }
        },

        async revert(requestId) {
            // Use modern dialog if available
            let confirmed = false;
            if (typeof ModernUI !== 'undefined' && ModernUI.Dialog) {
                const result = await ModernUI.Dialog.show({
                    type: 'warning',
                    title: '承認取り消し',
                    message: `申請 #${requestId} を取り消しますか？承認済みの休暇が取り消され、日数が返却されます。`,
                    confirmText: '取り消す',
                    cancelText: 'キャンセル'
                });
                confirmed = result.confirmed;
            } else {
                confirmed = confirm(`申請 #${requestId} を取り消しますか？\n\n承認済みの休暇が取り消され、日数が返却されます。`);
            }

            if (!confirmed) return;

            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests/${requestId}/revert`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reverted_by: 'Manager' })
                });

                if (!res.ok) {
                    const errorData = await res.json();
                    throw new Error(errorData.detail || 'Revert failed');
                }

                const json = await res.json();
                App.ui.showToast('success', json.message || '申請を取り消しました');
                this.loadPending();
                this.loadHistory();
                App.data.fetchEmployees(App.state.year); // Refresh balance

            } catch (e) {
                App.ui.showToast('error', e.message);
            } finally {
                App.ui.hideLoading();
            }
        }
    },

    // ========================================
    // BACKUP MODULE
    // ========================================
    backup: {
        async create() {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/backup`, { method: 'POST' });
                const json = await res.json();

                if (!res.ok) throw new Error(json.detail || 'Backup failed');

                App.ui.showToast('success', `バックアップ作成: ${json.backup.filename}`);
                return json.backup;

            } catch (e) {
                App.ui.showToast('error', e.message);
            } finally {
                App.ui.hideLoading();
            }
        },

        async list() {
            try {
                const res = await fetch(`${App.config.apiBase}/backups`);
                const json = await res.json();
                return json.backups || [];
            } catch (e) {
                console.error(e);
                return [];
            }
        },

        async restore(filename) {
            // Use modern dialog if available
            let confirmed = false;
            if (typeof ModernUI !== 'undefined' && ModernUI.Dialog) {
                const result = await ModernUI.Dialog.show({
                    type: 'warning',
                    title: 'バックアップ復元',
                    message: `"${filename}" から復元しますか？現在のデータは上書きされます。復元前に自動バックアップが作成されます。`,
                    confirmText: '復元する',
                    cancelText: 'キャンセル'
                });
                confirmed = result.confirmed;
            } else {
                confirmed = confirm(`バックアップ "${filename}" から復元しますか？\n\n⚠️ 現在のデータは上書きされます。\n（復元前に自動バックアップが作成されます）`);
            }

            if (!confirmed) return;

            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/backup/restore`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename })
                });

                const json = await res.json();
                if (!res.ok) throw new Error(json.detail || 'Restore failed');

                App.ui.showToast('success', `復元完了: ${filename}`);
                App.data.fetchEmployees(App.state.year); // Reload data

            } catch (e) {
                App.ui.showToast('error', e.message);
            } finally {
                App.ui.hideLoading();
            }
        },

        async showBackupList() {
            const backups = await this.list();

            if (backups.length === 0) {
                App.ui.showToast('info', 'バックアップがありません');
                return;
            }

            // Escape HTML to prevent XSS
            const escapeHtml = (str) => {
                const div = document.createElement('div');
                div.textContent = str;
                return div.innerHTML;
            };

            const listHtml = backups.map((b, index) => `
                <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem;">
                    <div class="flex-between">
                        <div>
                            <div style="font-weight: 600; font-size: 0.9rem;">${escapeHtml(b.filename)}</div>
                            <div style="font-size: 0.75rem; color: var(--muted);">${escapeHtml(String(b.size_mb))} MB | ${escapeHtml(b.created_at.slice(0, 19).replace('T', ' '))}</div>
                        </div>
                        <button class="btn btn-glass backup-restore-btn" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" data-backup-index="${index}">
                            復元
                        </button>
                    </div>
                </div>
            `).join('');

            document.getElementById('modal-title').innerText = '📦 バックアップ一覧';
            document.getElementById('modal-content').innerHTML = `
                <div style="max-height: 400px; overflow-y: auto;">
                    ${listHtml}
                </div>
                <div style="margin-top: 1rem;">
                    <button class="btn btn-primary backup-create-btn" style="width: 100%;">
                        📦 新規バックアップ作成
                    </button>
                </div>
            `;

            // Add event listeners safely (prevent XSS via onclick)
            document.querySelectorAll('.backup-restore-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const idx = parseInt(btn.dataset.backupIndex, 10);
                    if (backups[idx]) {
                        App.backup.restore(backups[idx].filename);
                    }
                });
            });

            document.querySelector('.backup-create-btn')?.addEventListener('click', () => {
                App.backup.create();
                App.ui.closeModal();
            });

            document.getElementById('detail-modal').style.display = 'flex';
        }
    },

    // ========================================
    // COMPLIANCE MODULE
    // ========================================
    compliance: {
        async check5Day() {
            const year = App.state.year || new Date().getFullYear();
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/compliance/5day-check/${year}`);
                const json = await res.json();

                // Update summary cards
                document.getElementById('comp-total').innerText = json.summary.total_checked;
                document.getElementById('comp-compliant').innerText = json.summary.compliant;
                document.getElementById('comp-atrisk').innerText = json.summary.at_risk;
                document.getElementById('comp-noncompliant').innerText = json.summary.non_compliant;

                // Show non-compliant list
                const container = document.getElementById('compliance-list');
                if (json.non_compliant_employees && json.non_compliant_employees.length > 0) {
                    container.innerHTML = json.non_compliant_employees.map(emp => {
                        const statusColor = emp.status === 'non_compliant' ? 'var(--danger)' : 'var(--warning)';
                        // XSS prevention: escape all user data
                        const safeName = App.utils.escapeHtml(emp.name);
                        const safeEmpNum = App.utils.escapeHtml(emp.employee_num);
                        const safeDaysUsed = App.utils.safeNumber(emp.days_used).toFixed(1);
                        const safeDaysRemaining = App.utils.safeNumber(emp.days_remaining).toFixed(1);
                        return `
                            <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid ${statusColor};">
                                <div class="flex-between">
                                    <div>
                                        <div style="font-weight: 600;">${safeName}</div>
                                        <div style="font-size: 0.85rem; color: var(--muted);">${safeEmpNum}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 1.1rem; font-weight: 700; color: ${statusColor};">${safeDaysUsed}日</div>
                                        <div style="font-size: 0.8rem; color: var(--muted);">残り ${safeDaysRemaining}日必要</div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--success);">✅ 全員が5日取得義務を達成しています</div>';
                }

                App.ui.showToast('success', `Compliance check completed for ${year}`);

            } catch (e) {
                App.ui.showToast('error', 'Compliance check failed');
            } finally {
                App.ui.hideLoading();
            }
        },

        async loadAlerts() {
            try {
                const res = await fetch(`${App.config.apiBase}/compliance/alerts`);
                const json = await res.json();

                const container = document.getElementById('alerts-container');
                if (json.alerts && json.alerts.length > 0) {
                    container.innerHTML = json.alerts.map(alert => {
                        const levelIcon = alert.level === 'critical' ? '🔴' : alert.level === 'warning' ? '🟡' : '🔵';
                        // XSS prevention: escape all user data
                        const safeName = App.utils.escapeHtml(alert.employee_name);
                        const safeMessage = App.utils.escapeHtml(alert.message_ja);
                        const safeAction = App.utils.escapeHtml(alert.action_required || '-');
                        return `
                            <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem;">
                                <div style="font-weight: 600;">${levelIcon} ${safeName}</div>
                                <div style="font-size: 0.9rem; margin-top: 0.25rem;">${safeMessage}</div>
                                <div style="font-size: 0.8rem; color: var(--muted); margin-top: 0.5rem;">
                                    対応: ${safeAction}
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--success);">✅ アラートはありません</div>';
                }

            } catch (e) {
                console.error(e);
            }
        },

        async loadLedger() {
            const year = App.state.year || new Date().getFullYear();
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/compliance/annual-ledger/${year}`);
                const json = await res.json();

                const container = document.getElementById('ledger-container');
                if (json.entries && json.entries.length > 0) {
                    container.innerHTML = `
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>社員番号</th>
                                    <th>氏名</th>
                                    <th>基準日</th>
                                    <th>付与日数</th>
                                    <th>取得日数</th>
                                    <th>残日数</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${json.entries.map(e => {
                        // XSS prevention: escape all user data
                        const safeEmpNum = App.utils.escapeHtml(e.employee_num);
                        const safeName = App.utils.escapeHtml(e.employee_name);
                        const safeGrantDate = App.utils.escapeHtml(e.grant_date);
                        const safeGranted = App.utils.safeNumber(e.granted_days);
                        const safeUsed = App.utils.safeNumber(e.used_days);
                        const safeRemaining = App.utils.safeNumber(e.remaining_days);
                        return `
                                    <tr>
                                        <td>${safeEmpNum}</td>
                                        <td>${safeName}</td>
                                        <td>${safeGrantDate}</td>
                                        <td>${safeGranted}</td>
                                        <td>${safeUsed}</td>
                                        <td>${safeRemaining}</td>
                                    </tr>
                                `}).join('')}
                            </tbody>
                        </table>
                    `;
                } else {
                    container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--muted);">データがありません</div>';
                }

            } catch (e) {
                App.ui.showToast('error', 'Failed to load ledger');
            } finally {
                App.ui.hideLoading();
            }
        },

        async exportLedger(format = 'csv') {
            const year = App.state.year || new Date().getFullYear();
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/compliance/export-ledger/${year}?format=${format}`, {
                    method: 'POST'
                });
                const json = await res.json();

                if (json.status === 'success') {
                    App.ui.showToast('success', `年次有給休暇管理簿を出力しました: ${json.filename}`);
                }

            } catch (e) {
                App.ui.showToast('error', 'Export failed');
            } finally {
                App.ui.hideLoading();
            }
        }
    },

    // ========================================
    // SETTINGS MODULE
    // ========================================
    settings: {
        async loadSnapshot() {
            try {
                const res = await fetch(`${App.config.apiBase}/system/snapshot`);
                const json = await res.json();

                if (json.snapshot) {
                    const s = json.snapshot;
                    document.getElementById('sys-db-size').innerText = s.database_size_kb.toFixed(1) + ' KB';
                    document.getElementById('sys-emp-count').innerText = s.employees_count;
                    document.getElementById('sys-health').innerText = s.health_status;
                    document.getElementById('sys-health').style.color =
                        s.health_status === 'HEALTHY' ? 'var(--success)' : 'var(--danger)';
                }

                App.ui.showToast('success', 'System snapshot updated');

            } catch (e) {
                App.ui.showToast('error', 'Failed to load snapshot');
            }
        },

        async viewAuditLog() {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/system/audit-log?limit=50`);
                const json = await res.json();

                let content = '<div style="max-height: 400px; overflow-y: auto;">';
                if (json.entries && json.entries.length > 0) {
                    content += json.entries.map(e => {
                        // XSS prevention: escape all user data
                        const safeAction = App.utils.escapeHtml(e.action);
                        const safeEntityType = App.utils.escapeHtml(e.entity_type);
                        const safeEntityId = App.utils.escapeHtml(e.entity_id || '-');
                        const safeTimestamp = App.utils.escapeHtml(e.timestamp?.slice(0, 19) || '');
                        return `
                        <div style="padding: 0.5rem; background: rgba(255,255,255,0.03); margin-bottom: 0.25rem; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
                            <span style="color: var(--primary);">[${safeAction}]</span>
                            <span style="color: var(--muted);">${safeEntityType}/${safeEntityId}</span>
                            <span style="color: #64748b; float: right;">${safeTimestamp}</span>
                        </div>
                    `}).join('');
                } else {
                    content += '<div style="text-align: center; padding: 2rem; color: var(--muted);">No audit log entries</div>';
                }
                content += '</div>';

                document.getElementById('modal-title').innerText = '📜 Audit Log';
                document.getElementById('modal-content').innerHTML = content;
                document.getElementById('detail-modal').classList.add('active');

            } catch (e) {
                App.ui.showToast('error', 'Failed to load audit log');
            } finally {
                App.ui.hideLoading();
            }
        }
    },

    // ========================================
    // CALENDAR MODULE
    // ========================================
    calendar: {
        currentYear: new Date().getFullYear(),
        currentMonth: new Date().getMonth() + 1,
        events: [],
        selectedDate: null,

        async loadEvents() {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/calendar/events?year=${this.currentYear}&month=${this.currentMonth}`);
                const json = await res.json();
                this.events = json.events || [];
                this.renderCalendar();
                this.updateMonthlySummary();
                App.ui.showToast('success', 'カレンダーを更新しました');
            } catch (e) {
                App.ui.showToast('error', 'カレンダーの読み込みに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        // Static header HTML to prevent losing headers on re-render
        _headerHtml: `
            <div class="calendar-header">日</div>
            <div class="calendar-header">月</div>
            <div class="calendar-header">火</div>
            <div class="calendar-header">水</div>
            <div class="calendar-header">木</div>
            <div class="calendar-header">金</div>
            <div class="calendar-header">土</div>
        `,

        renderCalendar() {
            const grid = document.getElementById('calendar-grid');
            const title = document.getElementById('calendar-month-title');

            // Update title
            const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
            title.innerText = `${this.currentYear}年 ${monthNames[this.currentMonth - 1]}`;

            // Clear grid and re-add headers (fixed: headers were being lost)
            grid.innerHTML = this._headerHtml;

            // Get first day and days in month
            const firstDay = new Date(this.currentYear, this.currentMonth - 1, 1).getDay();
            const daysInMonth = new Date(this.currentYear, this.currentMonth, 0).getDate();
            const daysInPrevMonth = new Date(this.currentYear, this.currentMonth - 1, 0).getDate();

            const today = new Date();
            const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

            // Previous month days
            for (let i = firstDay - 1; i >= 0; i--) {
                const day = daysInPrevMonth - i;
                grid.appendChild(this.createDayCell(day, true));
            }

            // Current month days
            for (let day = 1; day <= daysInMonth; day++) {
                const dateStr = `${this.currentYear}-${String(this.currentMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                const isToday = dateStr === todayStr;
                const dayEvents = this.events.filter(e => e.start <= dateStr && e.end >= dateStr);
                grid.appendChild(this.createDayCell(day, false, isToday, dateStr, dayEvents));
            }

            // Next month days
            const totalCells = firstDay + daysInMonth;
            const remainingCells = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
            for (let day = 1; day <= remainingCells; day++) {
                grid.appendChild(this.createDayCell(day, true));
            }
        },

        createDayCell(day, isOtherMonth, isToday = false, dateStr = '', events = []) {
            const cell = document.createElement('div');
            cell.className = `calendar-day ${isOtherMonth ? 'other-month' : ''} ${isToday ? 'today' : ''} ${this.selectedDate === dateStr ? 'selected' : ''}`;

            if (!isOtherMonth && dateStr) {
                cell.onclick = () => this.selectDate(dateStr, events);
            }

            let html = `<div class="calendar-day-number">${day}</div>`;

            if (!isOtherMonth && events.length > 0) {
                const displayEvents = events.slice(0, 2);
                displayEvents.forEach(e => {
                    // XSS prevention: escape title before display
                    const safeTitle = App.utils.escapeHtml(e.title?.split('(')[0]?.trim() || '');
                    html += `<div class="calendar-event" style="background: ${e.color};">${safeTitle}</div>`;
                });
                if (events.length > 2) {
                    html += `<div class="calendar-event-count">+${events.length - 2}</div>`;
                }
            }

            cell.innerHTML = html;
            return cell;
        },

        selectDate(dateStr, events) {
            this.selectedDate = dateStr;
            this.renderCalendar();

            document.getElementById('selected-date-display').innerText = dateStr;

            const container = document.getElementById('day-detail-container');
            if (events.length > 0) {
                container.innerHTML = events.map(e => {
                    const typeLabels = { 'full': '全日', 'half_am': '午前半休', 'half_pm': '午後半休', 'hourly': '時間休', 'usage': '使用日' };
                    const typeLabel = typeLabels[e.leave_type] || typeLabels[e.type] || '休暇';
                    // XSS prevention: escape all user data
                    const safeName = App.utils.escapeHtml(e.employee_name);
                    const safeDays = App.utils.safeNumber(e.days);
                    const safeHours = App.utils.safeNumber(e.hours);
                    return `
                        <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid ${e.color};">
                            <div style="font-weight: 600;">${safeName}</div>
                            <div style="font-size: 0.85rem; color: var(--muted);">
                                ${typeLabel} ${safeDays ? `(${safeDays}日)` : ''} ${safeHours ? `(${safeHours}時間)` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 2rem;">この日の休暇取得者はいません</div>';
            }
        },

        updateMonthlySummary() {
            const uniqueEmployees = new Set(this.events.map(e => e.employee_num));
            const totalDays = this.events.reduce((sum, e) => sum + (e.days || 0), 0);

            document.getElementById('cal-month-employees').innerText = uniqueEmployees.size;
            document.getElementById('cal-month-days').innerText = totalDays.toFixed(1);
        },

        prevMonth() {
            this.currentMonth--;
            if (this.currentMonth < 1) {
                this.currentMonth = 12;
                this.currentYear--;
            }
            this.loadEvents();
        },

        nextMonth() {
            this.currentMonth++;
            if (this.currentMonth > 12) {
                this.currentMonth = 1;
                this.currentYear++;
            }
            this.loadEvents();
        },

        goToToday() {
            this.currentYear = new Date().getFullYear();
            this.currentMonth = new Date().getMonth() + 1;
            this.loadEvents();
        }
    },

    // ========================================
    // ANALYTICS MODULE
    // ========================================
    analytics: {
        async loadDashboard() {
            const year = App.state.year || new Date().getFullYear();
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/analytics/dashboard/${year}`);
                const json = await res.json();

                // Update summary cards
                // Update summary cards with safety checks
                document.getElementById('ana-total-emp').innerText = App.utils.safeNumber(json.summary.total_employees);
                document.getElementById('ana-total-granted').innerText = App.utils.safeNumber(json.summary.total_granted).toLocaleString();
                document.getElementById('ana-total-used').innerText = App.utils.safeNumber(json.summary.total_used).toLocaleString();
                document.getElementById('ana-avg-rate').innerText = App.utils.safeNumber(json.summary.average_rate) + '%';

                // Render department chart
                this.renderDepartmentChart(json.department_stats);

                // Render employee type chart
                this.renderTypeChart(json.type_stats);

                // Render top users
                this.renderTopUsers(json.top_users);

                // Render high balance
                this.renderHighBalance(json.high_balance);

                // Load predictions
                this.loadPredictions();

            } catch (e) {
                App.ui.showToast('error', '分析データの読み込みに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        renderDepartmentChart(deptStats) {
            const ctx = document.getElementById('chart-department');
            if (!ctx) return;

            if (App.state.charts['department']) {
                App.state.charts['department'].destroy();
            }

            // Guard: If stats are empty or null, don't attempt chart creation
            if (!deptStats || !Array.isArray(deptStats) || deptStats.length === 0) return;

            const data = deptStats.slice(0, 10);
            App.state.charts['department'] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.name.length > 15 ? d.name.substring(0, 15) + '...' : d.name),
                    datasets: [{
                        label: '使用日数',
                        data: data.map(d => d.total_used),
                        backgroundColor: 'rgba(6, 182, 212, 0.5)',
                        borderColor: 'var(--color-primary-500)',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#64748b' } },
                        y: { grid: { display: false }, ticks: { color: '#64748b' } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        },

        renderTypeChart(typeStats) {
            const ctx = document.getElementById('chart-emp-type');
            if (!ctx) return;

            if (App.state.charts['empType']) {
                App.state.charts['empType'].destroy();
            }

            App.state.charts['empType'] = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(typeStats),
                    datasets: [{
                        data: Object.values(typeStats).map(v => v.used),
                        backgroundColor: ['var(--color-primary-500)', 'var(--color-primary-400)', 'var(--color-primary-700)'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: '#64748b' } }
                    }
                }
            });
        },

        renderTopUsers(topUsers) {
            const container = document.getElementById('top-users-list');
            container.innerHTML = topUsers.map((u, i) => {
                // XSS prevention: escape all user data
                const safeName = App.utils.escapeHtml(u.name);
                const safeEmpNum = App.utils.escapeHtml(u.employee_num);
                const safeUsed = App.utils.safeNumber(u.used);
                return `
                <div style="display: flex; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 0.5rem;">
                    <div style="width: 30px; height: 30px; background: ${i < 3 ? 'var(--warning)' : 'rgba(255,255,255,0.1)'}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 0.75rem; font-weight: 700; font-size: 0.8rem;">
                        ${i + 1}
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600;">${safeName}</div>
                        <div style="font-size: 0.8rem; color: var(--muted);">${safeEmpNum}</div>
                    </div>
                    <div style="font-weight: 700; color: var(--success);">${safeUsed}日</div>
                </div>
            `}).join('');
        },

        renderHighBalance(highBalance) {
            const container = document.getElementById('high-balance-list');
            container.innerHTML = highBalance.map(u => {
                // XSS prevention: escape all user data
                const safeName = App.utils.escapeHtml(u.name);
                const safeEmpNum = App.utils.escapeHtml(u.employee_num);
                const safeBalance = App.utils.safeNumber(u.balance);
                return `
                <div style="display: flex; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 0.5rem;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600;">${safeName}</div>
                        <div style="font-size: 0.8rem; color: var(--muted);">${safeEmpNum}</div>
                    </div>
                    <div style="font-weight: 700; color: var(--warning);">${safeBalance}日</div>
                </div>
            `}).join('');
        },

        async loadPredictions() {
            const year = App.state.year || new Date().getFullYear();

            try {
                const res = await fetch(`${App.config.apiBase}/analytics/predictions/${year}`);
                const json = await res.json();

                document.getElementById('pred-current-month').innerText = json.current_month + '月';
                document.getElementById('pred-remaining-months').innerText = json.remaining_months + 'ヶ月';
                document.getElementById('pred-avg-monthly').innerText = json.avg_monthly_usage + '日';
                document.getElementById('pred-at-risk').innerText = json.at_risk_count + '人';

                const container = document.getElementById('at-risk-employees');
                if (json.at_risk_employees && json.at_risk_employees.length > 0) {
                    container.innerHTML = json.at_risk_employees.map(e => {
                        // XSS prevention: escape all user data
                        const safeName = App.utils.escapeHtml(e.name);
                        const safeEmpNum = App.utils.escapeHtml(e.employee_num);
                        const safeCurrentUsed = App.utils.safeNumber(e.current_used);
                        const safeDaysNeeded = App.utils.safeNumber(e.days_needed);
                        return `
                        <div style="display: flex; align-items: center; padding: 0.5rem; background: rgba(248, 113, 113, 0.1); border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid var(--danger);">
                            <div style="flex: 1;">
                                <div style="font-weight: 600;">${safeName}</div>
                                <div style="font-size: 0.8rem; color: var(--muted);">${safeEmpNum}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 0.8rem; color: var(--muted);">現在 ${safeCurrentUsed}日</div>
                                <div style="font-weight: 700; color: var(--danger);">あと ${safeDaysNeeded}日必要</div>
                            </div>
                        </div>
                    `}).join('');
                } else {
                    container.innerHTML = '<div style="text-align: center; color: var(--success); padding: 1rem;">✅ 5日義務達成リスク者はいません</div>';
                }

            } catch (e) {
                console.error('Predictions error', e);
            }
        },

        async exportExcel(type) {
            const year = App.state.year || new Date().getFullYear();
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/export/excel?export_type=${type}&year=${year}`, {
                    method: 'POST'
                });
                const json = await res.json();

                if (json.status === 'success') {
                    App.ui.showToast('success', `${json.filename} をエクスポートしました`);
                }
            } catch (e) {
                App.ui.showToast('error', 'エクスポートに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        // ========================================
        // ADVANCED ANALYTICS - Year Comparison
        // ========================================
        async loadYearComparison() {
            const currentYear = App.state.year || new Date().getFullYear();
            const previousYear = currentYear - 1;

            try {
                const [currentRes, previousRes] = await Promise.all([
                    fetch(`${App.config.apiBase}/analytics/dashboard/${currentYear}`),
                    fetch(`${App.config.apiBase}/analytics/dashboard/${previousYear}`)
                ]);

                const currentData = await currentRes.json();
                const previousData = await previousRes.json();

                this.renderYearComparison(currentData, previousData, currentYear, previousYear);
            } catch (e) {
                console.error('Year comparison error:', e);
            }
        },

        renderYearComparison(current, previous, currentYear, previousYear) {
            const ctx = document.getElementById('chart-year-comparison');
            if (!ctx) return;

            if (App.state.charts['yearComparison']) {
                App.state.charts['yearComparison'].destroy();
            }

            const labels = ['付与日数', '使用日数', '平均使用率'];
            const currentValues = [
                current.summary?.total_granted || 0,
                current.summary?.total_used || 0,
                current.summary?.average_rate || 0
            ];
            const previousValues = [
                previous.summary?.total_granted || 0,
                previous.summary?.total_used || 0,
                previous.summary?.average_rate || 0
            ];

            App.state.charts['yearComparison'] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: `${previousYear}年`,
                            data: previousValues,
                            backgroundColor: 'rgba(156, 163, 175, 0.5)',
                            borderColor: '#9ca3af',
                            borderWidth: 1,
                            borderRadius: 4
                        },
                        {
                            label: `${currentYear}年`,
                            data: currentValues,
                            backgroundColor: 'rgba(6, 182, 212, 0.5)',
                            borderColor: 'var(--color-primary-500)',
                            borderWidth: 1,
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#64748b' } },
                        y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#64748b' } }
                    },
                    plugins: {
                        legend: { position: 'top', labels: { color: '#64748b' } },
                        title: { display: true, text: '年度比較', color: '#64748b' }
                    }
                }
            });

            // Update comparison stats
            const usedDiff = currentValues[1] - previousValues[1];
            const rateDiff = currentValues[2] - previousValues[2];
            const statsContainer = document.getElementById('year-comparison-stats');
            if (statsContainer) {
                statsContainer.innerHTML = `
                    <div class="stat-card">
                        <span class="stat-label">使用日数変化</span>
                        <span class="stat-value ${usedDiff >= 0 ? 'text-success' : 'text-danger'}">
                            ${usedDiff >= 0 ? '+' : ''}${usedDiff.toFixed(1)}日
                        </span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">使用率変化</span>
                        <span class="stat-value ${rateDiff >= 0 ? 'text-success' : 'text-danger'}">
                            ${rateDiff >= 0 ? '+' : ''}${rateDiff.toFixed(1)}%
                        </span>
                    </div>
                `;
            }
        },

        // ========================================
        // ADVANCED ANALYTICS - Monthly Trend
        // ========================================
        async loadMonthlyTrend() {
            const year = App.state.year || new Date().getFullYear();

            try {
                const res = await fetch(`${App.config.apiBase}/analytics/monthly-trend/${year}`);
                const data = await res.json();
                this.renderMonthlyTrend(data);
            } catch (e) {
                console.error('Monthly trend error:', e);
            }
        },

        renderMonthlyTrend(data) {
            const ctx = document.getElementById('chart-monthly-trend');
            if (!ctx) return;

            if (App.state.charts['monthlyTrend']) {
                App.state.charts['monthlyTrend'].destroy();
            }

            const months = ['4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月', '1月', '2月', '3月'];
            const usageData = data.monthly_usage || Array(12).fill(0);
            const cumulativeData = data.cumulative_usage || [];

            App.state.charts['monthlyTrend'] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: months,
                    datasets: [
                        {
                            label: '月次使用',
                            data: usageData,
                            borderColor: 'var(--color-primary-500)',
                            backgroundColor: 'rgba(6, 182, 212, 0.1)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        },
                        {
                            label: '累積使用',
                            data: cumulativeData,
                            borderColor: 'var(--color-primary-400)',
                            backgroundColor: 'transparent',
                            borderDash: [5, 5],
                            tension: 0.4,
                            pointRadius: 3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#64748b' } },
                        y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#64748b' } }
                    },
                    plugins: {
                        legend: { position: 'top', labels: { color: '#64748b' } },
                        title: { display: true, text: '月次使用トレンド', color: '#64748b' }
                    }
                }
            });
        },

        // ========================================
        // ADVANCED ANALYTICS - Compliance Gauge
        // ========================================
        renderComplianceGauge(complianceRate) {
            const ctx = document.getElementById('chart-compliance-gauge');
            if (!ctx) return;

            if (App.state.charts['complianceGauge']) {
                App.state.charts['complianceGauge'].destroy();
            }

            const rate = complianceRate || 0;
            const color = rate >= 90 ? '#34d399' : rate >= 70 ? '#fbbf24' : '#f87171';

            App.state.charts['complianceGauge'] = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [rate, 100 - rate],
                        backgroundColor: [color, 'rgba(255,255,255,0.1)'],
                        borderWidth: 0,
                        circumference: 180,
                        rotation: 270
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '75%',
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: false }
                    }
                }
            });

            // Update gauge value display
            const gaugeValue = document.getElementById('gauge-value');
            if (gaugeValue) {
                gaugeValue.textContent = `${rate.toFixed(1)}%`;
                gaugeValue.style.color = color;
            }
        },

        // ========================================
        // ADVANCED ANALYTICS - Load All
        // ========================================
        async loadAdvancedAnalytics() {
            await Promise.all([
                this.loadYearComparison(),
                this.loadMonthlyTrend()
            ]);
        }
    },

    // ========================================
    // MONTHLY REPORTS MODULE
    // ========================================
    reports: {
        currentYear: new Date().getFullYear(),
        currentMonth: new Date().getMonth() + 1,
        mode: 'monthly',

        init() {
            // Initialize year selector
            const yearSelect = document.getElementById('report-year');
            const years = App.state.availableYears.length > 0 ? App.state.availableYears : [new Date().getFullYear()];
            yearSelect.innerHTML = years.map(y => `<option value="${y}" ${y === this.currentYear ? 'selected' : ''}>${y}年</option>`).join('');

            // Set current month
            document.getElementById('report-month').value = this.currentMonth;

            // Initialize custom date pickers with default range (last 30 days)
            const today = new Date();
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            document.getElementById('report-start-date').value = thirtyDaysAgo.toISOString().split('T')[0];
            document.getElementById('report-end-date').value = today.toISOString().split('T')[0];

            // Load data
            this.loadMonthList();
            this.loadReport();
        },

        setMode(mode) {
            this.mode = mode;
            const monthlySelector = document.getElementById('monthly-selector');
            const customSelector = document.getElementById('custom-selector');
            const tabMonthly = document.getElementById('tab-monthly');
            const tabCustom = document.getElementById('tab-custom');

            // Update tab active states
            if (this.mode === 'monthly') {
                tabMonthly.classList.add('active');
                tabCustom.classList.remove('active');
                monthlySelector.style.display = 'flex';
                customSelector.style.display = 'none';
                this.loadReport();
            } else {
                tabMonthly.classList.remove('active');
                tabCustom.classList.add('active');
                monthlySelector.style.display = 'none';
                customSelector.style.display = 'block';
            }
        },

        async exportReport() {
            const data = this.mode === 'monthly'
                ? { year: this.currentYear, month: this.currentMonth }
                : {
                    startDate: document.getElementById('report-start-date').value,
                    endDate: document.getElementById('report-end-date').value
                };

            App.ui.showLoading();
            try {
                const params = this.mode === 'monthly'
                    ? `export_type=monthly_report&year=${data.year}&month=${data.month}`
                    : `export_type=custom_report&start_date=${data.startDate}&end_date=${data.endDate}`;

                const res = await fetch(`${App.config.apiBase}/export/excel?${params}`, { method: 'POST' });
                const json = await res.json();

                if (json.status === 'success') {
                    App.ui.showToast('success', `レポートをエクスポートしました: ${json.filename}`);
                    if (json.download_url) {
                        window.open(json.download_url, '_blank');
                    }
                } else {
                    throw new Error(json.detail || 'エクスポートに失敗しました');
                }
            } catch (e) {
                App.ui.showToast('error', e.message || 'エクスポートに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        async loadCustomReport() {
            const startDate = document.getElementById('report-start-date').value;
            const endDate = document.getElementById('report-end-date').value;

            if (!startDate || !endDate) {
                App.ui.showToast('error', '開始日と終了日を選択してください');
                return;
            }

            if (endDate < startDate) {
                App.ui.showToast('error', '終了日は開始日より後を選択してください');
                return;
            }

            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/reports/custom?start_date=${startDate}&end_date=${endDate}`);
                const json = await res.json();

                if (json.status !== 'success') {
                    throw new Error(json.detail || 'レポート取得に失敗しました');
                }

                // Update period display
                document.getElementById('report-period-label').innerText = json.report_period.label;

                // Update summary cards
                document.getElementById('rpt-emp-count').innerText = json.summary.total_employees + '人';
                document.getElementById('rpt-total-days').innerText = json.summary.total_days + '日';
                document.getElementById('rpt-total-hours').innerText = json.summary.total_hours + '時間';
                const avgDays = json.summary.total_employees > 0
                    ? (json.summary.total_days / json.summary.total_employees).toFixed(1)
                    : '0';
                document.getElementById('rpt-avg-days').innerText = avgDays + '日';

                // Render lists
                this.renderEmployeeList(json.employees);
                this.renderFactoryList(json.by_factory);
                this.renderDailyGrid(json.by_date);

                App.ui.showToast('success', `カスタムレポートを読み込みました (${json.report_period.days_in_period}日間)`);

            } catch (e) {
                App.ui.showToast('error', e.message || 'レポートの読み込みに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        async loadMonthList() {
            this.currentYear = parseInt(document.getElementById('report-year').value);
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/reports/monthly-list/${this.currentYear}`);
                const json = await res.json();

                const tbody = document.getElementById('report-year-summary');
                if (json.reports && json.reports.length > 0) {
                    tbody.innerHTML = json.reports.map(r => {
                        // XSS prevention: escape all user data
                        const safeMonth = parseInt(r.month) || 0;
                        const safeLabel = App.utils.escapeHtml(r.label);
                        const safePeriod = App.utils.escapeHtml(r.period);
                        const safeEmpCount = App.utils.safeNumber(r.employee_count);
                        const safeTotalDays = App.utils.safeNumber(r.total_days);
                        return `
                        <tr style="cursor: pointer;" data-month="${safeMonth}">
                            <td style="font-weight: 600;">${safeLabel}</td>
                            <td style="font-size: 0.85rem; color: var(--muted);">${safePeriod}</td>
                            <td>${safeEmpCount}人</td>
                            <td style="color: var(--primary); font-weight: 600;">${safeTotalDays}日</td>
                            <td><button class="btn btn-glass" style="padding: 0.25rem 0.75rem; font-size: 0.8rem;">詳細</button></td>
                        </tr>
                    `}).join('');

                    // Add event listeners safely (prevent XSS via onclick)
                    tbody.querySelectorAll('tr[data-month]').forEach(row => {
                        row.addEventListener('click', () => {
                            App.reports.selectMonth(parseInt(row.dataset.month));
                        });
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem;">データがありません</td></tr>';
                }

            } catch (e) {
                App.ui.showToast('error', '月次一覧の読み込みに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        selectMonth(month) {
            document.getElementById('report-month').value = month;
            this.loadReport();
        },

        async loadReport() {
            this.currentYear = parseInt(document.getElementById('report-year').value);
            this.currentMonth = parseInt(document.getElementById('report-month').value);

            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/reports/monthly/${this.currentYear}/${this.currentMonth}`);
                const json = await res.json();

                // Update period display
                document.getElementById('report-period-label').innerText = json.report_period.label;

                // Update summary cards
                document.getElementById('rpt-emp-count').innerText = json.summary.total_employees + '人';
                document.getElementById('rpt-total-days').innerText = json.summary.total_days + '日';
                document.getElementById('rpt-total-hours').innerText = json.summary.total_hours + '時間';
                const avgDays = json.summary.total_employees > 0
                    ? (json.summary.total_days / json.summary.total_employees).toFixed(1)
                    : '0';
                document.getElementById('rpt-avg-days').innerText = avgDays + '日';

                // Render employee list
                this.renderEmployeeList(json.employees);

                // Render factory list
                this.renderFactoryList(json.by_factory);

                // Render daily grid
                this.renderDailyGrid(json.by_date);

                App.ui.showToast('success', `${this.currentYear}年${this.currentMonth}月度レポートを読み込みました`);

            } catch (e) {
                App.ui.showToast('error', 'レポートの読み込みに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        renderEmployeeList(employees) {
            const container = document.getElementById('report-employee-list');
            if (employees && employees.length > 0) {
                container.innerHTML = employees.map(emp => {
                    // XSS prevention: escape all user data
                    const safeName = App.utils.escapeHtml(emp.name);
                    const safeEmpNum = App.utils.escapeHtml(emp.employee_num);
                    const safeFactory = App.utils.escapeHtml(emp.factory || '-');
                    const safeTotalDays = App.utils.safeNumber(emp.total_days);
                    const safeTotalHours = App.utils.safeNumber(emp.total_hours);

                    const datesHtml = emp.dates.map(d => {
                        const typeLabel = { 'full': '全', 'half_am': '午前', 'half_pm': '午後', 'hourly': '時' }[d.type] || '';
                        const safeDate = App.utils.escapeHtml(d.date?.slice(5) || '');
                        return `<span class="badge badge-info" style="margin: 0.1rem; padding: 0.15rem 0.4rem; font-size: 0.65rem;">${safeDate} ${typeLabel}</span>`;
                    }).join('');

                    return `
                        <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem;">
                            <div class="flex-between" style="margin-bottom: 0.5rem;">
                                <div>
                                    <div style="font-weight: 600;">${safeName}</div>
                                    <div style="font-size: 0.8rem; color: var(--muted);">${safeEmpNum} | ${safeFactory}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 1.25rem; font-weight: 700; color: var(--primary);">${safeTotalDays}日</div>
                                    ${safeTotalHours > 0 ? `<div style="font-size: 0.8rem; color: var(--warning);">+${safeTotalHours}時間</div>` : ''}
                                </div>
                            </div>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.25rem;">
                                ${datesHtml}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 2rem;">この期間の取得者はいません</div>';
            }
        },

        renderFactoryList(factories) {
            const container = document.getElementById('report-factory-list');
            if (factories && factories.length > 0) {
                container.innerHTML = factories.map(f => {
                    // XSS prevention: escape all user data
                    const safeFactory = App.utils.escapeHtml(f.factory);
                    const safeEmpCount = App.utils.safeNumber(f.employee_count);
                    const safeTotalDays = App.utils.safeNumber(f.total_days);
                    const safeNames = f.employees.map(e => App.utils.escapeHtml(e.name)).join(', ');
                    return `
                    <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem;">
                        <div class="flex-between" style="margin-bottom: 0.5rem;">
                            <div style="font-weight: 600;">${safeFactory}</div>
                            <div>
                                <span style="font-size: 0.9rem; color: var(--muted);">${safeEmpCount}人</span>
                                <span style="font-size: 1.1rem; font-weight: 700; color: var(--primary); margin-left: 0.5rem;">${safeTotalDays}日</span>
                            </div>
                        </div>
                        <div style="font-size: 0.8rem; color: var(--muted);">
                            ${safeNames}
                        </div>
                    </div>
                `}).join('');
            } else {
                container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 2rem;">データがありません</div>';
            }
        },

        renderDailyGrid(dailyData) {
            const container = document.getElementById('report-daily-grid');
            if (dailyData && dailyData.length > 0) {
                container.innerHTML = dailyData.map(d => {
                    const bgColor = d.count >= 5 ? 'rgba(248, 113, 113, 0.3)' :
                        d.count >= 3 ? 'rgba(251, 191, 36, 0.3)' :
                            'rgba(56, 189, 248, 0.15)';
                    // XSS prevention: escape all user data
                    const safeDate = App.utils.escapeHtml(d.date?.slice(5) || '');
                    const safeCount = App.utils.safeNumber(d.count);
                    const safeEmployees = d.employees.map(e => App.utils.escapeHtml(e)).join(', ');
                    return `
                        <div style="padding: 0.5rem; background: ${bgColor}; border-radius: 8px; text-align: center;" title="${safeEmployees}">
                            <div style="font-weight: 600; font-size: 0.9rem;">${safeDate}</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${safeCount}</div>
                            <div style="font-size: 0.7rem; color: var(--muted);">人</div>
                        </div>
                    `;
                }).join('');
            } else {
                container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 2rem; grid-column: 1 / -1;">この期間のデータはありません</div>';
            }
        }
    },

    // ========================================
    // GSAP ANIMATIONS MODULE (Lazy Loading)
    // ========================================
    animations: {
        // CDN URLs for lazy loading
        _cdnUrls: {
            gsapCore: 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js',
            scrollTrigger: 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js',
            scrollToPlugin: 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollToPlugin.min.js',
            animateCss: 'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css'
        },

        // Loading state
        _loading: false,
        _loaded: false,

        /**
         * Load a script dynamically
         * @param {string} url - Script URL
         * @returns {Promise}
         */
        _loadScript(url) {
            return new Promise((resolve, reject) => {
                const existing = document.querySelector(`script[src="${url}"]`);
                if (existing) {
                    resolve();
                    return;
                }
                const script = document.createElement('script');
                script.src = url;
                script.async = true;
                script.onload = resolve;
                script.onerror = () => reject(new Error(`Failed to load: ${url}`));
                document.head.appendChild(script);
            });
        },

        /**
         * Load a stylesheet dynamically
         * @param {string} url - Stylesheet URL
         * @returns {Promise}
         */
        _loadStylesheet(url) {
            return new Promise((resolve, reject) => {
                const existing = document.querySelector(`link[href="${url}"]`);
                if (existing) {
                    resolve();
                    return;
                }
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = url;
                link.onload = resolve;
                link.onerror = () => reject(new Error(`Failed to load: ${url}`));
                document.head.appendChild(link);
            });
        },

        /**
         * Load GSAP and plugins on demand
         * @returns {Promise<gsap>}
         */
        async loadGSAP() {
            if (typeof window.gsap !== 'undefined' && this._loaded) {
                return window.gsap;
            }

            if (this._loading) {
                // Wait for existing load to complete
                return new Promise((resolve) => {
                    const check = setInterval(() => {
                        if (this._loaded && typeof window.gsap !== 'undefined') {
                            clearInterval(check);
                            resolve(window.gsap);
                        }
                    }, 50);
                });
            }

            this._loading = true;

            try {
                // Load GSAP core first
                await this._loadScript(this._cdnUrls.gsapCore);

                // Load plugins in parallel
                await Promise.all([
                    this._loadScript(this._cdnUrls.scrollTrigger),
                    this._loadScript(this._cdnUrls.scrollToPlugin)
                ]);

                // Register plugins
                if (window.gsap && window.ScrollTrigger && window.ScrollToPlugin) {
                    window.gsap.registerPlugin(window.ScrollTrigger, window.ScrollToPlugin);
                }

                this._loaded = true;
                this._loading = false;
                return window.gsap;
            } catch (error) {
                this._loading = false;
                console.warn('[Animations] Failed to load GSAP:', error);
                return null;
            }
        },

        /**
         * Load Animate.css on demand
         * @returns {Promise}
         */
        async loadAnimateCSS() {
            if (document.querySelector(`link[href*="animate.css"]`)) {
                return;
            }
            await this._loadStylesheet(this._cdnUrls.animateCss);
        },

        /**
         * Initialize animations - loads GSAP on demand
         */
        async init() {
            // Respect prefers-reduced-motion (WCAG 2.3.3)
            const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            if (prefersReducedMotion) {
                this._applyReducedMotionFallback();
                return;
            }

            // Load GSAP on demand
            const gsap = await this.loadGSAP();
            if (!gsap) {
                this._applyReducedMotionFallback();
                return;
            }

            // Run animations
            this._runInitialAnimations(gsap);
        },

        /**
         * Apply fallback for reduced motion or when GSAP fails to load
         */
        _applyReducedMotionFallback() {
            // Show all elements immediately without animation
            document.querySelectorAll('.stat-card, .nav-item, .logo, .glass-panel').forEach(el => {
                el.style.opacity = '1';
                el.style.transform = 'none';
            });
        },

        /**
         * Run initial page animations
         * @param {gsap} gsap - GSAP instance
         */
        _runInitialAnimations(gsap) {
            // Animate stat cards on load
            gsap.from('.stat-card', {
                duration: 0.8,
                y: 30,
                opacity: 0,
                stagger: 0.1,
                ease: 'power3.out',
                delay: 0.2
            });

            // Animate glass panels on scroll
            if (typeof ScrollTrigger !== 'undefined') {
                gsap.utils.toArray('.glass-panel').forEach((panel, index) => {
                    if (index > 3) {
                        gsap.from(panel, {
                            scrollTrigger: {
                                trigger: panel,
                                start: 'top 90%',
                                end: 'top 70%',
                                toggleActions: 'play none none reverse'
                            },
                            duration: 0.6,
                            y: 40,
                            opacity: 0,
                            ease: 'power2.out'
                        });
                    }
                });

                // Parallax effect for background orbs
                gsap.to('body::before', {
                    scrollTrigger: { scrub: true },
                    y: (i, target) => -ScrollTrigger.maxScroll(window) * 0.3
                });
            }

            // Smooth scroll for anchor links
            if (typeof ScrollToPlugin !== 'undefined') {
                document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                    anchor.addEventListener('click', function (e) {
                        e.preventDefault();
                        const target = document.querySelector(this.getAttribute('href'));
                        if (target) {
                            gsap.to(window, {
                                duration: 1,
                                scrollTo: { y: target, offsetY: 20 },
                                ease: 'power3.inOut'
                            });
                        }
                    });
                });
            }

            // Animate sidebar navigation items
            gsap.from('.nav-item', {
                duration: 0.6,
                x: -30,
                opacity: 0,
                stagger: 0.08,
                ease: 'power2.out',
                delay: 0.3,
                clearProps: 'all'
            });

            // Animate logo
            gsap.from('.logo', {
                duration: 1,
                scale: 0.8,
                opacity: 0,
                ease: 'elastic.out(1, 0.5)'
            });

            // Button hover animations
            document.querySelectorAll('.btn').forEach(btn => {
                btn.addEventListener('mouseenter', () => {
                    gsap.to(btn, { duration: 0.3, scale: 1.05, ease: 'power2.out' });
                });
                btn.addEventListener('mouseleave', () => {
                    gsap.to(btn, { duration: 0.3, scale: 1, ease: 'power2.out' });
                });
            });

            // Number counter animation for KPIs
            this.animateCounters(gsap);
        },

        /**
         * Animate KPI counters
         * @param {gsap} gsap - GSAP instance (optional, will use window.gsap if not provided)
         */
        animateCounters(gsap) {
            const g = gsap || window.gsap;
            if (!g) {
                // Fallback: just show values without animation
                return;
            }

            const counters = [
                { id: 'kpi-used', suffix: '' },
                { id: 'kpi-balance', suffix: '' },
                { id: 'kpi-rate', suffix: '%' },
                { id: 'kpi-total', suffix: '' }
            ];

            counters.forEach(({ id, suffix }) => {
                const element = document.getElementById(id);
                if (element && element.textContent !== '-') {
                    const value = parseFloat(element.textContent.replace(/[^\d.-]/g, ''));
                    if (!isNaN(value)) {
                        const obj = { val: 0 };
                        g.to(obj, {
                            val: value,
                            duration: 2,
                            ease: 'power2.out',
                            onUpdate: function () {
                                element.textContent = Math.round(obj.val).toLocaleString() + suffix;
                            }
                        });
                    }
                }
            });
        },

        /**
         * Animate view transitions - loads GSAP if needed
         * @param {HTMLElement} viewElement - Element to animate
         */
        async transitionView(viewElement) {
            // Check reduced motion preference
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                viewElement.style.opacity = '1';
                return;
            }

            // Try to use existing GSAP or load it
            let gsap = window.gsap;
            if (!gsap) {
                gsap = await this.loadGSAP();
            }

            if (!gsap) {
                viewElement.style.opacity = '1';
                return;
            }

            // Ensure the element is visible
            gsap.set(viewElement, { opacity: 1, y: 0 });

            // Animate children with stagger
            const children = viewElement.querySelectorAll('.glass-panel, .stat-card');
            if (children.length > 0) {
                gsap.fromTo(children,
                    { y: 15, opacity: 0.8 },
                    {
                        duration: 0.4,
                        y: 0,
                        opacity: 1,
                        stagger: 0.05,
                        ease: 'power2.out',
                        clearProps: 'all'
                    }
                );
            }
        },

        /**
         * Preload GSAP in background during idle time
         * Call this early to have GSAP ready when needed
         */
        preloadInBackground() {
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                return;
            }

            const preload = () => {
                this.loadGSAP().catch(() => {
                    // Silently fail preload
                });
            };

            if ('requestIdleCallback' in window) {
                requestIdleCallback(preload, { timeout: 3000 });
            } else {
                setTimeout(preload, 1500);
            }
        }
    },

    // ========================================
    // EMPLOYEE TYPES MODULE (Haken/Ukeoi/Staff)
    // ========================================
    employeeTypes: {
        currentTab: 'all',
        activeOnly: true,
        data: {
            haken: [],
            ukeoi: [],
            staff: [],
            all: []
        },

        async loadData() {
            try {
                const year = App.state.year || new Date().getFullYear();
                // filter_by_year=true filtra empleados activos durante ese año (入社日 <= año AND (退社日 IS NULL OR 退社日 >= año))
                const res = await fetch(`${App.config.apiBase}/employees/by-type?year=${year}&active_only=${this.activeOnly}&filter_by_year=true`);
                const json = await res.json();

                if (json.status === 'success') {
                    this.data.haken = json.haken.employees || [];
                    this.data.ukeoi = json.ukeoi.employees || [];
                    this.data.staff = json.staff.employees || [];
                    this.data.all = [...this.data.haken, ...this.data.ukeoi, ...this.data.staff];

                    // Update counts (employee type tabs)
                    document.getElementById('count-type-all').innerText = this.data.all.length;
                    document.getElementById('count-type-haken').innerText = this.data.haken.length;
                    document.getElementById('count-type-ukeoi').innerText = this.data.ukeoi.length;
                    document.getElementById('count-type-staff').innerText = this.data.staff.length;

                    // Update summary cards
                    document.getElementById('haken-used').innerText = Math.round(json.haken.total_used);
                    document.getElementById('ukeoi-used').innerText = Math.round(json.ukeoi.total_used);
                    document.getElementById('staff-used').innerText = Math.round(json.staff.total_used);
                    document.getElementById('total-type-used').innerText = Math.round(
                        json.haken.total_used + json.ukeoi.total_used + json.staff.total_used
                    );

                    // Render table with current tab
                    this.renderTable();
                }
            } catch (e) {
                console.error('Failed to load employee types:', e);
                App.ui.showToast('error', '従業員データの読み込みに失敗しました');
            }
        },

        switchTab(tab) {
            this.currentTab = tab;

            // Update tab buttons
            document.querySelectorAll('.employee-tabs .btn').forEach(btn => btn.classList.remove('active', 'btn-primary'));
            document.getElementById(`tab-${tab}`).classList.add('active', 'btn-primary');

            this.renderTable();
        },

        toggleActiveFilter() {
            this.activeOnly = document.getElementById('active-only-toggle').checked;
            this.loadData();
        },

        renderTable(filterText = '') {
            const tbody = document.getElementById('table-body');
            let data = this.data[this.currentTab] || [];

            // Apply search filter
            if (filterText) {
                const q = filterText.toLowerCase();
                data = data.filter(e =>
                    (e.name && e.name.toLowerCase().includes(q)) ||
                    (e.employee_num && String(e.employee_num).includes(q)) ||
                    (e.haken && e.haken.toLowerCase().includes(q)) ||
                    (e.dispatch_name && e.dispatch_name.toLowerCase().includes(q)) ||
                    (e.contract_business && e.contract_business.toLowerCase().includes(q))
                );
            }

            document.getElementById('emp-count-badge').innerText = `${data.length} Employees`;

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 2rem;">データがありません</td></tr>';
                return;
            }

            tbody.innerHTML = data.map(e => {
                const empNum = App.utils.escapeAttr(e.employee_num || '');
                const name = App.utils.escapeHtml(e.name || '');
                const type = e.type || '';
                const typeLabel = type === 'haken' ? '🏭 派遣' : type === 'ukeoi' ? '📋 請負' : '👔 スタッフ';
                const typeBadge = type === 'haken' ? 'badge-info' : type === 'ukeoi' ? 'badge-success' : 'badge-warning';
                const factory = App.utils.escapeHtml(e.dispatch_name || e.contract_business || e.haken || '-');
                const granted = App.utils.safeNumber(e.granted).toFixed(1);
                const used = App.utils.safeNumber(e.used).toFixed(1);
                const balance = App.utils.safeNumber(e.balance);
                const usageRate = e.granted > 0 ? Math.round((e.used / e.granted) * 100) : 0;
                const balanceClass = balance < 0 ? 'badge-critical' : balance < 5 ? 'badge-danger' : 'badge-success';

                // Check if employee is selected
                const isSelected = App.bulkEdit && App.bulkEdit.selectedEmployees.has(e.employee_num);

                return `
                <tr class="employee-row" data-employee-num="${empNum}" style="cursor: pointer;" onclick="App.ui.openModal('${empNum}')">
                    <td class="table-checkbox" onclick="event.stopPropagation();">
                        <input type="checkbox"
                            class="employee-select-checkbox"
                            data-employee-num="${empNum}"
                            ${isSelected ? 'checked' : ''}
                            onchange="App.bulkEdit.toggleEmployee('${empNum}', this.checked)"
                            title="選択">
                    </td>
                    <td><div class="font-bold">${empNum}</div></td>
                    <td><div class="font-bold text-white">${name}</div></td>
                    <td><span class="badge ${typeBadge}">${typeLabel}</span></td>
                    <td><div class="text-sm text-gray-400">${factory}</div></td>
                    <td>${granted}</td>
                    <td><span class="text-gradient">${used}</span></td>
                    <td><span class="badge ${balanceClass}">${balance.toFixed(1)}</span></td>
                    <td>
                        <div style="width: 100px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                            <div style="width: ${Math.min(usageRate, 100)}%; height: 100%; background: var(--primary);"></div>
                        </div>
                        <div class="text-xs mt-1 text-right">${usageRate}%</div>
                    </td>
                </tr>
            `}).join('');
        }
    }
};

// ============================================
// EDIT YUKYU DATA MODULE (v2.1 - NEW)
// Permite editar datos importados desde Excel
// ============================================
App.editYukyu = {
    currentEmployee: null,
    currentYear: null,
    originalDetails: [],
    pendingChanges: {
        updates: [],   // {id, days_used}
        deletes: [],   // [id, id, ...]
        adds: []       // {use_date, days_used}
    },

    /**
     * Abre el modal de edición para un empleado
     */
    async openModal(employeeNum, year = null) {
        this.currentEmployee = null;
        this.currentYear = year || App.state.year;
        this.pendingChanges = { updates: [], deletes: [], adds: [] };

        // Mostrar modal con loading
        document.getElementById('edit-emp-name').textContent = 'Cargando...';
        document.getElementById('edit-emp-num').textContent = `社員番号: ${employeeNum}`;
        document.getElementById('edit-emp-balance').textContent = '-';
        document.getElementById('edit-usage-list').innerHTML = `
            <div class="text-center text-muted p-lg">
                <div class="spinner" style="margin: 0 auto;"></div>
                <p style="margin-top: 1rem;">データを読み込み中...</p>
            </div>
        `;
        document.getElementById('edit-yukyu-modal').classList.add('active');

        try {
            // Cargar datos del empleado
            const res = await fetch(`${App.config.apiBase}/yukyu/employee-summary/${employeeNum}/${this.currentYear}`);

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to load data');
            }

            const data = await res.json();
            this.currentEmployee = data.employee;
            this.originalDetails = data.usage_details || [];

            // Actualizar UI
            this.renderEmployeeInfo();
            this.renderUsageList();
            this.updateSummary();

        } catch (error) {
            console.error('Error loading employee data:', error);
            App.ui.showToast('error', `データ読み込みエラー: ${error.message}`);
            this.closeModal();
        }
    },

    /**
     * Renderiza la información del empleado
     */
    renderEmployeeInfo() {
        if (!this.currentEmployee) return;

        document.getElementById('edit-emp-name').textContent = this.currentEmployee.name;
        document.getElementById('edit-emp-num').textContent = `社員番号: ${this.currentEmployee.employee_num}`;
        document.getElementById('edit-emp-balance').textContent = `${this.currentEmployee.balance.toFixed(1)}日`;
    },

    /**
     * Renderiza la lista de días de uso
     */
    renderUsageList() {
        const container = document.getElementById('edit-usage-list');

        if (this.originalDetails.length === 0 && this.pendingChanges.adds.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted p-lg">
                    使用記録がありません。下のフォームから追加できます。
                </div>
            `;
            return;
        }

        let html = '';

        // Renderizar detalles existentes
        this.originalDetails.forEach(detail => {
            const isDeleted = this.pendingChanges.deletes.includes(detail.id);
            const update = this.pendingChanges.updates.find(u => u.id === detail.id);
            const currentDays = update ? update.days_used : detail.days_used;

            let itemClass = 'usage-item';
            if (isDeleted) itemClass += ' pending-delete';
            else if (update) itemClass += ' pending-update';

            html += `
                <div class="${itemClass}" data-id="${detail.id}">
                    <div class="usage-item-date">
                        📅 ${detail.use_date}
                    </div>
                    <div class="usage-item-days">
                        <select class="input-glass" onchange="App.editYukyu.updateDays(${detail.id}, this.value)" ${isDeleted ? 'disabled' : ''}>
                            <option value="1.0" ${currentDays == 1.0 ? 'selected' : ''}>1日 (全日)</option>
                            <option value="0.5" ${currentDays == 0.5 ? 'selected' : ''}>0.5日 (半日)</option>
                            <option value="0.25" ${currentDays == 0.25 ? 'selected' : ''}>0.25日 (2時間)</option>
                        </select>
                        ${isDeleted ?
                    `<button class="btn btn-glass btn-sm" onclick="App.editYukyu.undoDelete(${detail.id})">↩ 戻す</button>` :
                    `<button class="usage-item-delete" onclick="App.editYukyu.markDelete(${detail.id})">🗑 削除</button>`
                }
                    </div>
                </div>
            `;
        });

        // Renderizar nuevos items pendientes
        this.pendingChanges.adds.forEach((add, index) => {
            html += `
                <div class="usage-item pending-add" data-add-index="${index}">
                    <div class="usage-item-date">
                        📅 ${add.use_date} <span class="badge badge-success">新規</span>
                    </div>
                    <div class="usage-item-days">
                        <select class="input-glass" onchange="App.editYukyu.updatePendingAdd(${index}, this.value)">
                            <option value="1.0" ${add.days_used == 1.0 ? 'selected' : ''}>1日 (全日)</option>
                            <option value="0.5" ${add.days_used == 0.5 ? 'selected' : ''}>0.5日 (半日)</option>
                            <option value="0.25" ${add.days_used == 0.25 ? 'selected' : ''}>0.25日 (2時間)</option>
                        </select>
                        <button class="usage-item-delete" onclick="App.editYukyu.removePendingAdd(${index})">🗑 削除</button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    },

    /**
     * Actualiza días de un registro existente
     */
    updateDays(id, newDays) {
        const days = parseFloat(newDays);
        const original = this.originalDetails.find(d => d.id === id);

        if (!original) return;

        // Si volvió al valor original, quitar de updates
        if (original.days_used === days) {
            this.pendingChanges.updates = this.pendingChanges.updates.filter(u => u.id !== id);
        } else {
            // Actualizar o agregar
            const existing = this.pendingChanges.updates.find(u => u.id === id);
            if (existing) {
                existing.days_used = days;
            } else {
                this.pendingChanges.updates.push({ id, days_used: days });
            }
        }

        this.renderUsageList();
        this.updateSummary();
    },

    /**
     * Marca un registro para eliminar
     */
    markDelete(id) {
        if (!this.pendingChanges.deletes.includes(id)) {
            this.pendingChanges.deletes.push(id);
        }
        this.renderUsageList();
        this.updateSummary();
    },

    /**
     * Deshace la eliminación de un registro
     */
    undoDelete(id) {
        this.pendingChanges.deletes = this.pendingChanges.deletes.filter(d => d !== id);
        this.renderUsageList();
        this.updateSummary();
    },

    /**
     * Agrega un nuevo registro de uso
     */
    addUsage() {
        const dateInput = document.getElementById('add-use-date');
        const daysSelect = document.getElementById('add-days-used');

        const useDate = dateInput.value;
        const daysUsed = parseFloat(daysSelect.value);

        if (!useDate) {
            App.ui.showToast('error', '日付を選択してください');
            return;
        }

        // Verificar que la fecha no exista ya
        const existsInOriginal = this.originalDetails.some(d => d.use_date === useDate);
        const existsInPending = this.pendingChanges.adds.some(a => a.use_date === useDate);

        if (existsInOriginal || existsInPending) {
            App.ui.showToast('error', 'この日付は既に登録されています');
            return;
        }

        this.pendingChanges.adds.push({
            use_date: useDate,
            days_used: daysUsed
        });

        // Limpiar input
        dateInput.value = '';

        this.renderUsageList();
        this.updateSummary();
        App.ui.showToast('success', '使用日を追加しました（未保存）');
    },

    /**
     * Actualiza un registro pendiente de agregar
     */
    updatePendingAdd(index, newDays) {
        if (this.pendingChanges.adds[index]) {
            this.pendingChanges.adds[index].days_used = parseFloat(newDays);
            this.updateSummary();
        }
    },

    /**
     * Elimina un registro pendiente de agregar
     */
    removePendingAdd(index) {
        this.pendingChanges.adds.splice(index, 1);
        this.renderUsageList();
        this.updateSummary();
    },

    /**
     * Actualiza el resumen de cambios
     */
    updateSummary() {
        if (!this.currentEmployee) return;

        // Calcular total de días usados después de cambios
        let totalUsed = 0;

        // Sumar días originales (excepto los eliminados, con updates aplicados)
        this.originalDetails.forEach(detail => {
            if (this.pendingChanges.deletes.includes(detail.id)) return;

            const update = this.pendingChanges.updates.find(u => u.id === detail.id);
            totalUsed += update ? update.days_used : detail.days_used;
        });

        // Sumar días nuevos
        this.pendingChanges.adds.forEach(add => {
            totalUsed += add.days_used;
        });

        const granted = this.currentEmployee.granted || 0;
        const newBalance = granted - totalUsed;

        document.getElementById('edit-total-used').textContent = `${totalUsed.toFixed(1)}日`;
        document.getElementById('edit-new-balance').textContent = `${newBalance.toFixed(1)}日`;

        // Cambiar color si el balance es negativo
        const balanceEl = document.getElementById('edit-new-balance');
        balanceEl.className = newBalance < 0 ? 'font-bold text-danger' :
            newBalance < 5 ? 'font-bold text-warning' :
                'font-bold text-success';
    },

    /**
     * Guarda todos los cambios
     */
    async saveChanges() {
        const hasChanges = this.pendingChanges.updates.length > 0 ||
            this.pendingChanges.deletes.length > 0 ||
            this.pendingChanges.adds.length > 0;

        if (!hasChanges) {
            App.ui.showToast('warning', '変更がありません');
            return;
        }

        const saveBtn = document.getElementById('edit-save-btn');
        saveBtn.disabled = true;
        saveBtn.textContent = '保存中...';

        try {
            // 1. Procesar eliminaciones
            for (const id of this.pendingChanges.deletes) {
                const res = await fetch(`${App.config.apiBase}/yukyu/usage-details/${id}`, {
                    method: 'DELETE'
                });
                if (!res.ok) throw new Error(`Failed to delete record ${id}`);
            }

            // 2. Procesar actualizaciones
            for (const update of this.pendingChanges.updates) {
                const res = await fetch(`${App.config.apiBase}/yukyu/usage-details/${update.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ days_used: update.days_used })
                });
                if (!res.ok) throw new Error(`Failed to update record ${update.id}`);
            }

            // 3. Procesar nuevos registros
            for (const add of this.pendingChanges.adds) {
                const res = await fetch(`${App.config.apiBase}/yukyu/usage-details`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        employee_num: this.currentEmployee.employee_num,
                        name: this.currentEmployee.name,
                        use_date: add.use_date,
                        days_used: add.days_used
                    })
                });
                if (!res.ok) throw new Error(`Failed to add record for ${add.use_date}`);
            }

            // 4. Recalcular balance del empleado
            const recalcRes = await fetch(
                `${App.config.apiBase}/yukyu/recalculate/${this.currentEmployee.employee_num}/${this.currentYear}`,
                { method: 'POST' }
            );

            if (!recalcRes.ok) throw new Error('Failed to recalculate balance');

            App.ui.showToast('success', '✅ 変更が保存されました');
            this.closeModal();

            // Refrescar datos de la app
            await App.data.fetchData();
            App.ui.updateAll();

        } catch (error) {
            console.error('Error saving changes:', error);
            App.ui.showToast('error', `保存エラー: ${error.message}`);
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = '💾 変更を保存';
        }
    },

    /**
     * Cierra el modal
     */
    closeModal() {
        document.getElementById('edit-yukyu-modal').classList.remove('active');
        this.currentEmployee = null;
        this.originalDetails = [];
        this.pendingChanges = { updates: [], deletes: [], adds: [] };
    }
};

// ============================================
// IMPORT REPORT MODULE (v2.2 - NEW)
// Sistema de validación visual para importación de Excel
// ============================================
App.importReport = {
    // Estado del último reporte de importación
    lastReport: null,
    warningsExpanded: false,
    errorsExpanded: false,

    /**
     * Muestra el modal con el resultado de importación
     * @param {Object} data - Datos de la respuesta de sync
     */
    showImportResult(data) {
        this.lastReport = this.processImportData(data);

        const modal = document.getElementById('import-result-modal');
        if (!modal) {
            console.error('Import result modal not found');
            return;
        }

        // Actualizar estadísticas
        this.updateStatistics();

        // Actualizar banner de estado
        this.updateStatusBanner();

        // Actualizar breakdown
        this.updateBreakdown();

        // Actualizar warnings
        this.updateWarnings();

        // Actualizar errores
        this.updateErrors();

        // Actualizar empleados problemáticos
        this.updateProblematicEmployees();

        // Mostrar modal
        modal.classList.add('active');

        // Reset expansion states
        this.warningsExpanded = false;
        this.errorsExpanded = false;
    },

    /**
     * Procesa los datos de importación para generar el reporte
     */
    processImportData(data) {
        const report = {
            timestamp: new Date().toISOString(),
            total: data.count || 0,
            success: 0,
            warnings: [],
            errors: [],
            problematicEmployees: [],
            breakdown: {
                fullDays: 0,
                halfDays: 0,
                hourlyLeave: 0,
                noUsage: 0,
                highUsage: 0,
                lowBalance: 0,
                expiringSoon: 0
            }
        };

        // Si hay datos de validación en la respuesta
        if (data.validation) {
            report.warnings = data.validation.warnings || [];
            report.errors = data.validation.errors || [];
        }

        // Analizar datos de empleados para generar breakdown
        if (data.employees && Array.isArray(data.employees)) {
            data.employees.forEach(emp => {
                // Clasificar por tipo de uso
                if (emp.used >= 1) {
                    report.breakdown.fullDays++;
                } else if (emp.used >= 0.5) {
                    report.breakdown.halfDays++;
                } else if (emp.used > 0 && emp.used < 0.5) {
                    report.breakdown.hourlyLeave++;
                } else if (emp.used === 0) {
                    report.breakdown.noUsage++;
                }

                // Detectar problemas
                const usageRate = emp.granted > 0 ? (emp.used / emp.granted) * 100 : 0;

                if (usageRate >= 80) {
                    report.breakdown.highUsage++;
                    report.warnings.push({
                        type: 'high_usage',
                        employee: emp.name,
                        employeeNum: emp.employee_num,
                        message: `使用率が高い (${usageRate.toFixed(1)}%)`,
                        value: usageRate
                    });
                }

                if (emp.balance <= 5 && emp.balance > 0) {
                    report.breakdown.lowBalance++;
                    report.warnings.push({
                        type: 'low_balance',
                        employee: emp.name,
                        employeeNum: emp.employee_num,
                        message: `残日数が少ない (${emp.balance}日)`,
                        value: emp.balance
                    });
                }

                // Validar datos inválidos
                if (!emp.name || emp.name.trim() === '') {
                    report.errors.push({
                        type: 'invalid_name',
                        employee: emp.employee_num,
                        message: '氏名が空です',
                        row: emp.row || '不明'
                    });
                }

                if (emp.granted < 0 || emp.used < 0) {
                    report.errors.push({
                        type: 'negative_value',
                        employee: emp.name || emp.employee_num,
                        message: '負の値が検出されました',
                        row: emp.row || '不明'
                    });
                }

                if (emp.used > emp.granted) {
                    report.warnings.push({
                        type: 'over_usage',
                        employee: emp.name,
                        employeeNum: emp.employee_num,
                        message: `使用日数が付与日数を超えています (${emp.used}/${emp.granted})`,
                        value: emp.used - emp.granted
                    });
                    report.problematicEmployees.push({
                        name: emp.name,
                        employeeNum: emp.employee_num,
                        issue: '使用超過',
                        detail: `${emp.used}日/${emp.granted}日`
                    });
                }
            });
        }

        // Calcular éxitos (total - errores)
        report.success = report.total - report.errors.length;

        // Agregar warnings basados en datos de respuesta directa
        if (data.skipped && data.skipped > 0) {
            report.warnings.push({
                type: 'skipped_rows',
                message: `${data.skipped}行がスキップされました`,
                value: data.skipped
            });
        }

        if (data.duplicates && data.duplicates > 0) {
            report.warnings.push({
                type: 'duplicates',
                message: `${data.duplicates}件の重複データが検出されました`,
                value: data.duplicates
            });
        }

        return report;
    },

    /**
     * Actualiza las estadísticas en el modal
     */
    updateStatistics() {
        const report = this.lastReport;
        if (!report) return;

        document.getElementById('import-stat-total').textContent = report.total;
        document.getElementById('import-stat-success').textContent = report.success;
        document.getElementById('import-stat-warnings').textContent = report.warnings.length;
        document.getElementById('import-stat-errors').textContent = report.errors.length;
    },

    /**
     * Actualiza el banner de estado según el resultado
     */
    updateStatusBanner() {
        const report = this.lastReport;
        if (!report) return;

        const banner = document.getElementById('import-status-banner');
        const icon = banner.querySelector('.import-status-icon');
        const title = document.getElementById('import-status-title');
        const subtitle = document.getElementById('import-status-subtitle');
        const modalIcon = document.getElementById('import-result-icon');

        // Remover clases anteriores
        banner.classList.remove('import-status-success', 'import-status-warning', 'import-status-error');

        if (report.errors.length > 0) {
            // Estado: Error
            banner.classList.add('import-status-error');
            icon.textContent = '❌';
            title.textContent = 'インポートに問題があります';
            subtitle.textContent = `${report.errors.length}件のエラーと${report.warnings.length}件の警告があります`;
            modalIcon.textContent = '⚠️';
        } else if (report.warnings.length > 0) {
            // Estado: Warning
            banner.classList.add('import-status-warning');
            icon.textContent = '⚠️';
            title.textContent = 'インポート完了（警告あり）';
            subtitle.textContent = `${report.success}件を処理しました。${report.warnings.length}件の警告があります`;
            modalIcon.textContent = '📊';
        } else {
            // Estado: Success
            banner.classList.add('import-status-success');
            icon.textContent = '✅';
            title.textContent = 'インポート完了';
            subtitle.textContent = `${report.success}件のデータが正常に処理されました`;
            modalIcon.textContent = '✅';
        }
    },

    /**
     * Actualiza la sección de breakdown
     */
    updateBreakdown() {
        const report = this.lastReport;
        if (!report) return;

        const grid = document.getElementById('import-breakdown-grid');
        const breakdown = report.breakdown;

        grid.innerHTML = `
            <div class="import-breakdown-item">
                <span class="import-breakdown-label">全日使用</span>
                <span class="import-breakdown-value">${breakdown.fullDays}件</span>
            </div>
            <div class="import-breakdown-item">
                <span class="import-breakdown-label">半日使用</span>
                <span class="import-breakdown-value">${breakdown.halfDays}件</span>
            </div>
            <div class="import-breakdown-item">
                <span class="import-breakdown-label">時間単位使用</span>
                <span class="import-breakdown-value">${breakdown.hourlyLeave}件</span>
            </div>
            <div class="import-breakdown-item">
                <span class="import-breakdown-label">未使用</span>
                <span class="import-breakdown-value">${breakdown.noUsage}件</span>
            </div>
            <div class="import-breakdown-item">
                <span class="import-breakdown-label">高使用率 (80%+)</span>
                <span class="import-breakdown-value" style="color: var(--warning);">${breakdown.highUsage}件</span>
            </div>
            <div class="import-breakdown-item">
                <span class="import-breakdown-label">残日数少 (5日以下)</span>
                <span class="import-breakdown-value" style="color: var(--danger);">${breakdown.lowBalance}件</span>
            </div>
        `;
    },

    /**
     * Actualiza la lista de warnings
     */
    updateWarnings() {
        const report = this.lastReport;
        if (!report) return;

        const section = document.getElementById('import-warnings-section');
        const list = document.getElementById('import-warnings-list');

        if (report.warnings.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';

        // Agrupar warnings por tipo
        const groupedWarnings = {};
        report.warnings.forEach(warning => {
            const type = warning.type || 'other';
            if (!groupedWarnings[type]) {
                groupedWarnings[type] = [];
            }
            groupedWarnings[type].push(warning);
        });

        let html = '';
        for (const [type, warnings] of Object.entries(groupedWarnings)) {
            warnings.slice(0, 10).forEach(warning => {
                html += `
                    <div class="import-warning-item">
                        <span class="item-icon">⚠️</span>
                        <span class="item-text">
                            ${warning.employee ? `<strong>${warning.employee}</strong>: ` : ''}
                            ${this.escapeHtml(warning.message)}
                        </span>
                        ${warning.employeeNum ? `<span class="item-row">${warning.employeeNum}</span>` : ''}
                    </div>
                `;
            });
            if (warnings.length > 10) {
                html += `
                    <div class="import-warning-item" style="font-style: italic; opacity: 0.7;">
                        <span class="item-icon">...</span>
                        <span class="item-text">他 ${warnings.length - 10}件</span>
                    </div>
                `;
            }
        }

        list.innerHTML = html;
    },

    /**
     * Actualiza la lista de errores
     */
    updateErrors() {
        const report = this.lastReport;
        if (!report) return;

        const section = document.getElementById('import-errors-section');
        const list = document.getElementById('import-errors-list');

        if (report.errors.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';

        let html = '';
        report.errors.slice(0, 20).forEach(error => {
            html += `
                <div class="import-error-item">
                    <span class="item-icon">❌</span>
                    <span class="item-text">
                        ${error.employee ? `<strong>${error.employee}</strong>: ` : ''}
                        ${this.escapeHtml(error.message)}
                    </span>
                    ${error.row ? `<span class="item-row">行 ${error.row}</span>` : ''}
                </div>
            `;
        });

        if (report.errors.length > 20) {
            html += `
                <div class="import-error-item" style="font-style: italic; opacity: 0.7;">
                    <span class="item-icon">...</span>
                    <span class="item-text">他 ${report.errors.length - 20}件のエラー</span>
                </div>
            `;
        }

        list.innerHTML = html;
    },

    /**
     * Actualiza la sección de empleados problemáticos
     */
    updateProblematicEmployees() {
        const report = this.lastReport;
        if (!report) return;

        const section = document.getElementById('import-problems-section');
        const list = document.getElementById('import-problems-list');

        if (report.problematicEmployees.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';

        let html = '';
        report.problematicEmployees.slice(0, 10).forEach((emp, idx) => {
            // XSS prevention: escape all user data
            const safeEmpNum = this.escapeHtml(emp.employeeNum);
            const safeDetail = this.escapeHtml(emp.detail);
            html += `
                <div class="import-problem-item">
                    <div class="import-problem-employee">
                        <span class="import-problem-name">${this.escapeHtml(emp.name)}</span>
                        <span class="import-problem-num">(${safeEmpNum})</span>
                    </div>
                    <span class="import-problem-issue">${this.escapeHtml(emp.issue)}: ${safeDetail}</span>
                    <button class="import-problem-action" data-emp-index="${idx}">
                        詳細
                    </button>
                </div>
            `;
        });

        list.innerHTML = html;

        // Add event listeners safely (prevent XSS via onclick)
        list.querySelectorAll('.import-problem-action').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.empIndex);
                const emp = report.problematicEmployees[idx];
                if (emp) App.importReport.viewEmployee(emp.employeeNum);
            });
        });
    },

    /**
     * Alterna la expansión de warnings
     */
    toggleWarnings() {
        this.warningsExpanded = !this.warningsExpanded;
        const list = document.getElementById('import-warnings-list');
        const toggle = document.getElementById('import-warnings-toggle');

        list.style.display = this.warningsExpanded ? 'block' : 'none';
        toggle.classList.toggle('expanded', this.warningsExpanded);
    },

    /**
     * Alterna la expansión de errores
     */
    toggleErrors() {
        this.errorsExpanded = !this.errorsExpanded;
        const list = document.getElementById('import-errors-list');
        const toggle = document.getElementById('import-errors-toggle');

        list.style.display = this.errorsExpanded ? 'block' : 'none';
        toggle.classList.toggle('expanded', this.errorsExpanded);
    },

    /**
     * Ver detalles de un empleado problemático
     */
    viewEmployee(employeeNum) {
        this.closeModal();
        // Buscar en la tabla y resaltar, o abrir modal de detalles
        if (App.ui && App.ui.openModal) {
            App.ui.openModal(employeeNum);
        }
    },

    /**
     * Resalta empleados problemáticos en la tabla principal
     */
    highlightProblematicEmployees() {
        if (!this.lastReport || !this.lastReport.problematicEmployees) return;

        const problemEmployeeNums = this.lastReport.problematicEmployees.map(e => e.employeeNum);
        const tableRows = document.querySelectorAll('#employee-table tbody tr');

        tableRows.forEach(row => {
            const empNumCell = row.querySelector('td:first-child');
            if (empNumCell) {
                const empNum = empNumCell.textContent.trim();
                if (problemEmployeeNums.includes(empNum)) {
                    row.classList.add('row-problematic');
                    row.style.animation = 'pulse-highlight 2s ease-in-out 3';
                } else {
                    row.classList.remove('row-problematic');
                    row.style.animation = '';
                }
            }
        });
    },

    /**
     * Descarga el reporte en formato JSON o CSV
     */
    downloadReport(format = 'json') {
        if (!this.lastReport) {
            App.ui.showToast('error', 'レポートデータがありません');
            return;
        }

        const report = this.lastReport;
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');

        if (format === 'json') {
            const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `import_report_${timestamp}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else {
            // CSV format
            const lines = [
                'Type,Employee,EmployeeNum,Message,Value',
                ...report.warnings.map(w =>
                    `Warning,"${w.employee || ''}","${w.employeeNum || ''}","${w.message}","${w.value || ''}"`
                ),
                ...report.errors.map(e =>
                    `Error,"${e.employee || ''}","${e.row || ''}","${e.message}",""`
                )
            ];
            const csv = lines.join('\n');
            const bom = '\uFEFF'; // BOM for Excel UTF-8
            const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `import_report_${timestamp}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        App.ui.showToast('success', 'レポートをダウンロードしました');
    },

    /**
     * Cierra el modal
     */
    closeModal() {
        const modal = document.getElementById('import-result-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    },

    /**
     * Utilidad para escapar HTML
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// ============================================
// AUDIT HISTORY MODULE (v2.3 - NEW)
// Sistema de visualizacion de historial de cambios
// ============================================
App.auditHistory = {
    // Estado del modulo
    currentEntityType: null,
    currentEntityId: null,
    allHistory: [],
    filteredHistory: [],

    /**
     * Muestra el historial de una entidad especifica
     * @param {string} entityType - Tipo de entidad (employee, leave_request, yukyu_usage)
     * @param {string} entityId - ID de la entidad
     */
    async showEntityHistory(entityType, entityId) {
        if (!entityId) {
            App.ui.showToast('warning', 'エンティティIDが必要です');
            return;
        }

        this.currentEntityType = entityType;
        this.currentEntityId = entityId;
        this.allHistory = [];
        this.filteredHistory = [];

        // Mostrar modal con loading
        document.getElementById('audit-entity-info').textContent = `${this.getEntityTypeLabel(entityType)}: ${entityId}`;
        document.getElementById('audit-history-list').innerHTML = `
            <div class="text-center text-muted p-lg">
                <div class="spinner" style="margin: 0 auto;"></div>
                <p style="margin-top: 1rem;">履歴を読み込み中...</p>
            </div>
        `;
        document.getElementById('audit-action-filter').value = '';
        document.getElementById('audit-history-modal').classList.add('active');

        try {
            const res = await fetch(`${App.config.apiBase}/audit-log/${entityType}/${entityId}`);

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to load history');
            }

            const data = await res.json();
            this.allHistory = data.history || [];
            this.filteredHistory = [...this.allHistory];

            this.renderHistory();

        } catch (error) {
            console.error('Error loading audit history:', error);
            document.getElementById('audit-history-list').innerHTML = `
                <div class="text-center text-danger p-lg">
                    <p>履歴の読み込みに失敗しました: ${this.escapeHtml(error.message)}</p>
                </div>
            `;
        }
    },

    /**
     * Aplica el filtro de accion
     */
    applyFilter() {
        const filterValue = document.getElementById('audit-action-filter').value;

        if (filterValue) {
            this.filteredHistory = this.allHistory.filter(h => h.action === filterValue);
        } else {
            this.filteredHistory = [...this.allHistory];
        }

        this.renderHistory();
    },

    /**
     * Renderiza la lista de historial
     */
    renderHistory() {
        const container = document.getElementById('audit-history-list');

        if (this.filteredHistory.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted p-lg">
                    履歴がありません
                </div>
            `;
            return;
        }

        let html = '';

        this.filteredHistory.forEach(record => {
            const timestamp = new Date(record.timestamp).toLocaleString('ja-JP');
            const actionBadge = this.getActionBadge(record.action);
            const changes = this.formatChanges(record.old_value, record.new_value);

            html += `
                <div class="audit-history-item" style="border-bottom: 1px solid var(--border-color); padding: 1rem 0;">
                    <div class="flex-between mb-sm">
                        <div>
                            ${actionBadge}
                            <span class="text-muted text-sm ml-sm">by ${this.escapeHtml(record.user_id || 'system')}</span>
                        </div>
                        <div class="text-muted text-sm">
                            ${timestamp}
                        </div>
                    </div>
                    ${changes ? `<div class="audit-changes mt-sm">${changes}</div>` : ''}
                    ${record.ip_address ? `<div class="text-muted text-xs mt-sm">IP: ${this.escapeHtml(record.ip_address)}</div>` : ''}
                </div>
            `;
        });

        container.innerHTML = html;
    },

    /**
     * Obtiene el badge de accion
     */
    getActionBadge(action) {
        const badges = {
            'CREATE': '<span class="badge badge-success">CREATE</span>',
            'UPDATE': '<span class="badge badge-warning">UPDATE</span>',
            'DELETE': '<span class="badge badge-danger">DELETE</span>',
            'APPROVE': '<span class="badge badge-info">APPROVE</span>',
            'REJECT': '<span class="badge badge-secondary">REJECT</span>',
            'REVERT': '<span class="badge badge-warning">REVERT</span>',
            'CLEANUP': '<span class="badge badge-secondary">CLEANUP</span>'
        };
        return badges[action] || `<span class="badge">${this.escapeHtml(action)}</span>`;
    },

    /**
     * Formatea los cambios para mostrar
     */
    formatChanges(oldValue, newValue) {
        if (!oldValue && !newValue) return '';

        let html = '<div class="text-sm" style="background: var(--bg-secondary); padding: 0.5rem; border-radius: 4px;">';

        if (oldValue && typeof oldValue === 'object') {
            const fields = Object.keys(newValue || oldValue);
            fields.forEach(field => {
                if (field === 'last_updated' || field === 'id') return; // Skip metadata fields

                const oldVal = oldValue?.[field];
                const newVal = newValue?.[field];

                if (oldVal !== newVal) {
                    html += `
                        <div class="flex-between py-xs">
                            <span class="font-medium">${this.escapeHtml(field)}:</span>
                            <span>
                                ${oldVal !== undefined ? `<span class="text-danger line-through">${this.formatValue(oldVal)}</span>` : ''}
                                ${oldVal !== undefined && newVal !== undefined ? ' → ' : ''}
                                ${newVal !== undefined ? `<span class="text-success">${this.formatValue(newVal)}</span>` : ''}
                            </span>
                        </div>
                    `;
                }
            });
        } else {
            if (oldValue) {
                html += `<div class="text-danger">旧: ${this.formatValue(oldValue)}</div>`;
            }
            if (newValue) {
                html += `<div class="text-success">新: ${this.formatValue(newValue)}</div>`;
            }
        }

        html += '</div>';
        return html;
    },

    /**
     * Formatea un valor para mostrar
     */
    formatValue(value) {
        if (value === null || value === undefined) return '-';
        if (typeof value === 'object') return JSON.stringify(value);
        return this.escapeHtml(String(value));
    },

    /**
     * Obtiene la etiqueta del tipo de entidad
     */
    getEntityTypeLabel(entityType) {
        const labels = {
            'employee': '従業員',
            'leave_request': '有給申請',
            'yukyu_usage': '有給使用',
            'genzai': '派遣社員',
            'ukeoi': '請負社員',
            'staff': 'スタッフ'
        };
        return labels[entityType] || entityType;
    },

    /**
     * Cierra el modal
     */
    closeModal() {
        document.getElementById('audit-history-modal').classList.remove('active');
        this.currentEntityType = null;
        this.currentEntityId = null;
        this.allHistory = [];
        this.filteredHistory = [];
    },

    /**
     * Utilidad para escapar HTML
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// ========================================
// BULK EDIT MODULE (v2.3 - NEW)
// ========================================
App.bulkEdit = {
    // State
    selectedEmployees: new Map(), // Map<employeeNum, employeeData>
    previewData: null,
    warnings: [],

    /**
     * Toggle selection for a single employee
     */
    toggleEmployee(employeeNum, checked) {
        if (checked) {
            const emp = App.state.data.find(e => e.employeeNum === employeeNum);
            if (emp) {
                this.selectedEmployees.set(employeeNum, emp);
            }
        } else {
            this.selectedEmployees.delete(employeeNum);
        }
        this.updateToolbar();
    },

    /**
     * Toggle select all visible employees
     */
    toggleSelectAll(checked) {
        const checkboxes = document.querySelectorAll('.employee-select-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = checked;
            const empNum = cb.dataset.employeeNum;
            if (checked) {
                const emp = App.state.data.find(e => e.employeeNum === empNum);
                if (emp) this.selectedEmployees.set(empNum, emp);
            } else {
                this.selectedEmployees.delete(empNum);
            }
        });
        this.updateToolbar();
    },

    /**
     * Clear all selections
     */
    clearSelection() {
        this.selectedEmployees.clear();
        document.querySelectorAll('.employee-select-checkbox').forEach(cb => cb.checked = false);
        document.getElementById('select-all-checkbox').checked = false;
        this.updateToolbar();
        this.closeModal();
    },

    /**
     * Update toolbar visibility and count
     */
    updateToolbar() {
        const toolbar = document.getElementById('bulk-edit-toolbar');
        const countEl = document.getElementById('bulk-selected-count');
        const count = this.selectedEmployees.size;

        if (countEl) countEl.textContent = count;
        if (toolbar) {
            if (count > 0) {
                toolbar.classList.add('active');
            } else {
                toolbar.classList.remove('active');
            }
        }
    },

    /**
     * Open the bulk edit modal
     */
    openModal() {
        if (this.selectedEmployees.size === 0) {
            App.ui.showToast('warning', 'No hay empleados seleccionados');
            return;
        }
        if (this.selectedEmployees.size > 50) {
            App.ui.showToast('error', 'Maximo 50 empleados por operacion');
            return;
        }

        // Update modal content
        document.getElementById('bulk-edit-count').textContent = this.selectedEmployees.size;

        // Populate employee list - XSS prevention: use data attributes instead of inline onclick
        const listEl = document.getElementById('bulk-edit-employees-list');
        const employeesArray = Array.from(this.selectedEmployees.values());
        listEl.innerHTML = employeesArray.map((emp, idx) => `
            <div class="bulk-edit-employee-chip">
                <span>${App.utils.escapeHtml(emp.name)}</span>
                <span class="remove" data-emp-index="${idx}">&times;</span>
            </div>
        `).join('');

        // Add event listeners safely (prevent XSS via onclick)
        listEl.querySelectorAll('.remove').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.empIndex);
                const emp = employeesArray[idx];
                if (emp) App.bulkEdit.removeFromSelection(emp.employeeNum);
            });
        });

        // Populate haken dropdown
        const hakenSelect = document.getElementById('bulk-edit-set-haken');
        const factories = [...new Set(App.state.data.map(e => e.haken).filter(Boolean))];
        hakenSelect.innerHTML = '<option value="">派遣先を選択...</option>' +
            factories.map(f => `<option value="${App.utils.escapeAttr(f)}">${App.utils.escapeHtml(f)}</option>`).join('');

        // Reset fields
        this.resetFields();

        // Show modal
        document.getElementById('bulk-edit-modal').classList.add('active');
    },

    /**
     * Close the modal
     */
    closeModal() {
        document.getElementById('bulk-edit-modal').classList.remove('active');
        this.previewData = null;
        this.warnings = [];
    },

    /**
     * Remove employee from selection
     */
    removeFromSelection(employeeNum) {
        this.selectedEmployees.delete(employeeNum);
        const cb = document.querySelector(`.employee-select-checkbox[data-employee-num="${employeeNum}"]`);
        if (cb) cb.checked = false;
        this.updateToolbar();

        if (this.selectedEmployees.size === 0) {
            this.closeModal();
        } else {
            document.getElementById('bulk-edit-count').textContent = this.selectedEmployees.size;
            const chip = document.querySelector(`.bulk-edit-employee-chip:has([onclick*="${employeeNum}"])`);
            if (chip) chip.remove();
        }
    },

    /**
     * Toggle employee list visibility
     */
    toggleEmployeeList() {
        const list = document.getElementById('bulk-edit-employees-list');
        const toggle = document.getElementById('bulk-edit-employees-toggle');
        if (list.style.display === 'none') {
            list.style.display = 'flex';
            toggle.textContent = '▲';
        } else {
            list.style.display = 'none';
            toggle.textContent = '▼';
        }
    },

    /**
     * Toggle a field's input visibility
     */
    toggleField(fieldName) {
        const group = document.getElementById(`bulk-edit-${fieldName.replace('_', '-')}-group`);
        const checkbox = document.getElementById(`bulk-edit-${fieldName.replace('_', '-')}-check`);
        if (group && checkbox) {
            group.style.display = checkbox.checked ? 'flex' : 'none';
        }
        // Reset preview when field changes
        document.getElementById('bulk-edit-preview-section').style.display = 'none';
        document.getElementById('bulk-edit-apply-btn').disabled = true;
    },

    /**
     * Reset all fields
     */
    resetFields() {
        ['add-granted', 'add-used', 'set-haken'].forEach(field => {
            const check = document.getElementById(`bulk-edit-${field}-check`);
            const group = document.getElementById(`bulk-edit-${field}-group`);
            const input = document.getElementById(`bulk-edit-${field}`);
            if (check) check.checked = false;
            if (group) group.style.display = 'none';
            if (input) input.value = '';
        });
        document.getElementById('bulk-edit-preview-section').style.display = 'none';
        document.getElementById('bulk-edit-warnings-section').style.display = 'none';
        document.getElementById('bulk-edit-apply-btn').disabled = true;
    },

    /**
     * Get current updates from form
     */
    getUpdates() {
        const updates = {};

        if (document.getElementById('bulk-edit-add-granted-check').checked) {
            const val = parseFloat(document.getElementById('bulk-edit-add-granted').value);
            if (!isNaN(val) && val > 0) updates.add_granted = val;
        }
        if (document.getElementById('bulk-edit-add-used-check').checked) {
            const val = parseFloat(document.getElementById('bulk-edit-add-used').value);
            if (!isNaN(val) && val > 0) updates.add_used = val;
        }
        if (document.getElementById('bulk-edit-set-haken-check').checked) {
            const val = document.getElementById('bulk-edit-set-haken').value;
            if (val) updates.set_haken = val;
        }

        return updates;
    },

    /**
     * Preview changes before applying
     */
    async preview() {
        const updates = this.getUpdates();
        if (Object.keys(updates).length === 0) {
            App.ui.showToast('warning', '変更する項目を選択してください');
            return;
        }

        const employeeNums = Array.from(this.selectedEmployees.keys());
        const year = App.state.year;

        try {
            App.ui.showLoading();
            const response = await fetch(`${App.config.apiBase}/employees/bulk-update/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ employee_nums: employeeNums, year, updates })
            });

            const result = await response.json();
            App.ui.hideLoading();

            if (!response.ok) {
                throw new Error(result.detail || 'Preview failed');
            }

            this.previewData = result;
            this.warnings = result.warnings || [];

            // Render preview
            this.renderPreview(result.preview);

            // Show warnings if any
            if (this.warnings.length > 0) {
                this.renderWarnings(this.warnings);
                document.getElementById('bulk-edit-warnings-section').style.display = 'block';
            } else {
                document.getElementById('bulk-edit-warnings-section').style.display = 'none';
            }

            // Enable apply button
            document.getElementById('bulk-edit-apply-btn').disabled = false;
            document.getElementById('bulk-edit-preview-section').style.display = 'block';

        } catch (error) {
            App.ui.hideLoading();
            App.ui.showToast('error', `プレビューエラー: ${error.message}`);
        }
    },

    /**
     * Render preview table
     */
    renderPreview(previewItems) {
        const listEl = document.getElementById('bulk-edit-preview-list');

        let html = `
            <div class="bulk-edit-preview-item bulk-edit-preview-header">
                <div>従業員</div>
                <div>付与</div>
                <div>使用</div>
                <div>残日数</div>
            </div>
        `;

        previewItems.forEach(item => {
            const changes = item.changes || {};
            const grantedChange = changes.granted ? `${item.current.granted} → ${item.proposed.granted}` : item.current.granted;
            const usedChange = changes.used ? `${item.current.used} → ${item.proposed.used}` : item.current.used;
            const balanceChange = changes.balance ? `${item.current.balance} → ${item.proposed.balance}` : item.current.balance;

            const balanceClass = item.proposed.balance < 0 ? 'text-danger' : item.proposed.balance < 5 ? 'text-warning' : '';

            html += `
                <div class="bulk-edit-preview-item">
                    <div>${App.utils.escapeHtml(item.name)}</div>
                    <div>${changes.granted ? `<span class="text-muted">${item.current.granted}</span> <span class="bulk-edit-change-arrow">→</span> <strong>${item.proposed.granted}</strong>` : item.current.granted}</div>
                    <div>${changes.used ? `<span class="text-muted">${item.current.used}</span> <span class="bulk-edit-change-arrow">→</span> <strong>${item.proposed.used}</strong>` : item.current.used}</div>
                    <div class="${balanceClass}">${changes.balance ? `<span class="text-muted">${item.current.balance}</span> <span class="bulk-edit-change-arrow">→</span> <strong>${item.proposed.balance}</strong>` : item.current.balance}</div>
                </div>
            `;
        });

        listEl.innerHTML = html;
    },

    /**
     * Render warnings
     */
    renderWarnings(warnings) {
        const listEl = document.getElementById('bulk-edit-warnings-list');
        listEl.innerHTML = warnings.map(w => `
            <div class="bulk-edit-warning-item">
                <span>⚠️</span>
                <span>${App.utils.escapeHtml(w.name || w.employee_num)}: ${App.utils.escapeHtml(w.message)}</span>
            </div>
        `).join('');
    },

    /**
     * Apply the bulk update
     */
    async apply() {
        const updates = this.getUpdates();
        if (Object.keys(updates).length === 0) {
            App.ui.showToast('warning', '変更する項目を選択してください');
            return;
        }

        // Confirm if there are warnings
        if (this.warnings.length > 0) {
            if (!confirm(`${this.warnings.length}件の警告があります。続行しますか？`)) {
                return;
            }
        }

        const employeeNums = Array.from(this.selectedEmployees.keys());
        const year = App.state.year;

        try {
            App.ui.showLoading();
            const response = await fetch(`${App.config.apiBase}/employees/bulk-update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ employee_nums: employeeNums, year, updates })
            });

            const result = await response.json();
            App.ui.hideLoading();

            if (!response.ok) {
                throw new Error(result.detail || 'Update failed');
            }

            // Show success message
            App.ui.showToast('success', `${result.updated_count}名のデータを更新しました (ID: ${result.operation_id})`);

            // Close modal and clear selection
            this.closeModal();
            this.clearSelection();

            // Refresh data
            await App.data.fetchEmployees(App.state.year);

        } catch (error) {
            App.ui.hideLoading();
            App.ui.showToast('error', `更新エラー: ${error.message}`);
        }
    }
};

// ========================================
// BATCH IMPORT MODULE (v2.5 - NEW)
// Importar múltiples archivos Excel
// ========================================
App.batchImport = {
    files: [],
    results: [],
    isProcessing: false,

    /**
     * Abrir modal de batch import
     */
    openModal() {
        this.files = [];
        this.results = [];
        this.isProcessing = false;

        const modal = document.getElementById('batch-import-modal');
        if (!modal) {
            this.createModal();
        }
        document.getElementById('batch-import-modal').style.display = 'flex';
        this.updateUI();
    },

    /**
     * Crear modal dinámicamente
     */
    createModal() {
        const modal = document.createElement('div');
        modal.id = 'batch-import-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 700px;">
                <div class="modal-header">
                    <h3>📁 バッチインポート - 複数ファイル</h3>
                    <button class="modal-close" onclick="App.batchImport.closeModal()">×</button>
                </div>
                <div class="modal-body">
                    <!-- Drop Zone -->
                    <div id="batch-drop-zone" class="drop-zone" ondragover="App.batchImport.handleDragOver(event)"
                         ondrop="App.batchImport.handleDrop(event)" ondragleave="App.batchImport.handleDragLeave(event)">
                        <input type="file" id="batch-file-input" multiple accept=".xlsx,.xlsm,.xls"
                               onchange="App.batchImport.handleFileSelect(event)" style="display: none;">
                        <div class="drop-zone-content">
                            <span class="drop-zone-icon">📂</span>
                            <p>ファイルをドラッグ&ドロップ</p>
                            <p class="text-muted">または</p>
                            <button class="btn btn-primary" onclick="document.getElementById('batch-file-input').click()">
                                ファイルを選択
                            </button>
                        </div>
                    </div>

                    <!-- File List -->
                    <div id="batch-file-list" class="batch-file-list" style="margin-top: 1rem;"></div>

                    <!-- Progress -->
                    <div id="batch-progress" style="display: none; margin-top: 1rem;">
                        <div class="progress-bar-container">
                            <div id="batch-progress-bar" class="progress-bar" style="width: 0%;"></div>
                        </div>
                        <p id="batch-progress-text" class="text-center text-muted" style="margin-top: 0.5rem;"></p>
                    </div>

                    <!-- Results -->
                    <div id="batch-results" style="display: none; margin-top: 1rem;"></div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="App.batchImport.closeModal()">閉じる</button>
                    <button id="batch-import-btn" class="btn btn-primary" onclick="App.batchImport.startImport()" disabled>
                        インポート開始
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    },

    /**
     * Cerrar modal
     */
    closeModal() {
        const modal = document.getElementById('batch-import-modal');
        if (modal) modal.style.display = 'none';
    },

    /**
     * Handle drag over
     */
    handleDragOver(event) {
        event.preventDefault();
        event.currentTarget.classList.add('drag-over');
    },

    /**
     * Handle drag leave
     */
    handleDragLeave(event) {
        event.currentTarget.classList.remove('drag-over');
    },

    /**
     * Handle file drop
     */
    handleDrop(event) {
        event.preventDefault();
        event.currentTarget.classList.remove('drag-over');
        const files = Array.from(event.dataTransfer.files).filter(f =>
            f.name.endsWith('.xlsx') || f.name.endsWith('.xlsm') || f.name.endsWith('.xls')
        );
        this.addFiles(files);
    },

    /**
     * Handle file select
     */
    handleFileSelect(event) {
        const files = Array.from(event.target.files);
        this.addFiles(files);
    },

    /**
     * Add files to list
     */
    addFiles(newFiles) {
        newFiles.forEach(file => {
            if (!this.files.find(f => f.name === file.name)) {
                this.files.push(file);
            }
        });
        this.updateUI();
    },

    /**
     * Remove file from list
     */
    removeFile(index) {
        this.files.splice(index, 1);
        this.updateUI();
    },

    /**
     * Update UI
     */
    updateUI() {
        const listEl = document.getElementById('batch-file-list');
        const importBtn = document.getElementById('batch-import-btn');

        if (this.files.length === 0) {
            listEl.innerHTML = '<p class="text-muted text-center">ファイルが選択されていません</p>';
            importBtn.disabled = true;
        } else {
            listEl.innerHTML = this.files.map((file, i) => `
                <div class="batch-file-item">
                    <span class="batch-file-icon">📄</span>
                    <span class="batch-file-name">${App.utils.escapeHtml(file.name)}</span>
                    <span class="batch-file-size">${(file.size / 1024).toFixed(1)} KB</span>
                    <button class="btn btn-sm btn-danger" onclick="App.batchImport.removeFile(${i})">✕</button>
                </div>
            `).join('');
            importBtn.disabled = this.isProcessing;
        }
    },

    /**
     * Start batch import
     */
    async startImport() {
        if (this.files.length === 0 || this.isProcessing) return;

        this.isProcessing = true;
        this.results = [];

        const progressEl = document.getElementById('batch-progress');
        const progressBar = document.getElementById('batch-progress-bar');
        const progressText = document.getElementById('batch-progress-text');
        const resultsEl = document.getElementById('batch-results');
        const importBtn = document.getElementById('batch-import-btn');

        progressEl.style.display = 'block';
        resultsEl.style.display = 'none';
        importBtn.disabled = true;

        for (let i = 0; i < this.files.length; i++) {
            const file = this.files[i];
            const progress = ((i + 1) / this.files.length) * 100;

            progressBar.style.width = `${progress}%`;
            progressText.textContent = `処理中: ${file.name} (${i + 1}/${this.files.length})`;

            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch(`${App.config.apiBase}/upload`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                this.results.push({
                    filename: file.name,
                    success: response.ok,
                    count: result.count || 0,
                    message: result.message || result.detail || 'Unknown error'
                });
            } catch (error) {
                this.results.push({
                    filename: file.name,
                    success: false,
                    count: 0,
                    message: error.message
                });
            }
        }

        this.isProcessing = false;
        progressEl.style.display = 'none';
        this.showResults();
    },

    /**
     * Show import results
     */
    showResults() {
        const resultsEl = document.getElementById('batch-results');
        const successCount = this.results.filter(r => r.success).length;
        const totalImported = this.results.reduce((sum, r) => sum + r.count, 0);

        resultsEl.style.display = 'block';
        resultsEl.innerHTML = `
            <div class="batch-results-summary ${successCount === this.results.length ? 'success' : 'warning'}">
                <h4>${successCount}/${this.results.length} ファイル成功</h4>
                <p>合計 ${totalImported} 件のレコードをインポートしました</p>
            </div>
            <div class="batch-results-list">
                ${this.results.map(r => `
                    <div class="batch-result-item ${r.success ? 'success' : 'error'}">
                        <span class="batch-result-icon">${r.success ? '✅' : '❌'}</span>
                        <span class="batch-result-name">${App.utils.escapeHtml(r.filename)}</span>
                        <span class="batch-result-count">${r.count}件</span>
                        ${!r.success ? `<span class="batch-result-error">${App.utils.escapeHtml(r.message)}</span>` : ''}
                    </div>
                `).join('')}
            </div>
        `;

        // Clear files
        this.files = [];
        this.updateUI();

        // Refresh main data
        App.data.fetchEmployees(App.state.year);
    }
};

// ========================================
// PDF REPORTS MODULE (v2.4 - NEW)
// Sistema de generacion de reportes PDF
// ========================================
App.reports = {
    /**
     * Descarga reporte PDF de un empleado
     * @param {string} employeeNum - Numero de empleado
     * @param {number|null} year - Ano fiscal (opcional)
     */
    async downloadEmployeePDF(employeeNum, year = null) {
        try {
            App.ui.showLoading('PDFを生成中...');

            let url = `${App.config.apiBase}/reports/employee/${employeeNum}/pdf`;
            if (year) {
                url += `?year=${year}`;
            }

            const response = await fetch(url);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'PDF生成に失敗しました');
            }

            const blob = await response.blob();
            const filename = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '')
                || `reporte_empleado_${employeeNum}.pdf`;

            this.downloadBlob(blob, filename);
            App.ui.hideLoading();
            App.ui.showToast('success', 'PDFレポートをダウンロードしました');

        } catch (error) {
            App.ui.hideLoading();
            App.ui.showToast('error', `PDF生成エラー: ${error.message}`);
            console.error('PDF download error:', error);
        }
    },

    /**
     * Descarga reporte anual (年次有給休暇管理簿)
     * @param {number} year - Ano fiscal
     */
    async downloadAnnualLedger(year) {
        try {
            App.ui.showLoading('年次管理簿を生成中...');

            const response = await fetch(`${App.config.apiBase}/reports/annual/${year}/pdf`);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'PDF生成に失敗しました');
            }

            const blob = await response.blob();
            const filename = `年次有給休暇管理簿_${year}.pdf`;

            this.downloadBlob(blob, filename);
            App.ui.hideLoading();
            App.ui.showToast('success', '年次管理簿をダウンロードしました');

        } catch (error) {
            App.ui.hideLoading();
            App.ui.showToast('error', `PDF生成エラー: ${error.message}`);
            console.error('Annual ledger download error:', error);
        }
    },

    /**
     * Descarga reporte mensual
     * @param {number} year - Ano
     * @param {number} month - Mes (1-12)
     */
    async downloadMonthlySummary(year, month) {
        try {
            App.ui.showLoading('月次レポートを生成中...');

            const response = await fetch(`${App.config.apiBase}/reports/monthly/${year}/${month}/pdf`);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'PDF生成に失敗しました');
            }

            const blob = await response.blob();
            const filename = `reporte_mensual_${year}_${String(month).padStart(2, '0')}.pdf`;

            this.downloadBlob(blob, filename);
            App.ui.hideLoading();
            App.ui.showToast('success', '月次レポートをダウンロードしました');

        } catch (error) {
            App.ui.hideLoading();
            App.ui.showToast('error', `PDF生成エラー: ${error.message}`);
            console.error('Monthly summary download error:', error);
        }
    },

    /**
     * Descarga reporte de cumplimiento (5日取得義務)
     * @param {number} year - Ano fiscal
     */
    async downloadComplianceReport(year) {
        try {
            App.ui.showLoading('コンプライアンスレポートを生成中...');

            const response = await fetch(`${App.config.apiBase}/reports/compliance/${year}/pdf`);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'PDF生成に失敗しました');
            }

            const blob = await response.blob();
            const filename = `reporte_cumplimiento_5dias_${year}.pdf`;

            this.downloadBlob(blob, filename);
            App.ui.hideLoading();
            App.ui.showToast('success', 'コンプライアンスレポートをダウンロードしました');

        } catch (error) {
            App.ui.hideLoading();
            App.ui.showToast('error', `PDF生成エラー: ${error.message}`);
            console.error('Compliance report download error:', error);
        }
    },

    /**
     * Genera y descarga un reporte personalizado
     * @param {Object} config - Configuracion del reporte
     */
    async downloadCustomReport(config) {
        try {
            App.ui.showLoading('カスタムレポートを生成中...');

            const response = await fetch(`${App.config.apiBase}/reports/custom/pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'PDF生成に失敗しました');
            }

            const blob = await response.blob();
            const filename = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '')
                || `reporte_custom.pdf`;

            this.downloadBlob(blob, filename);
            App.ui.hideLoading();
            App.ui.showToast('success', 'カスタムレポートをダウンロードしました');

        } catch (error) {
            App.ui.hideLoading();
            App.ui.showToast('error', `PDF生成エラー: ${error.message}`);
            console.error('Custom report download error:', error);
        }
    },

    /**
     * Muestra modal de opciones de exportacion PDF
     */
    showExportModal() {
        const year = App.state.year || new Date().getFullYear();
        const currentMonth = new Date().getMonth() + 1;

        const modalHtml = `
            <div id="pdf-export-modal" class="modal active">
                <div class="modal-content" style="max-width: 500px;">
                    <div class="modal-header">
                        <h3>PDFレポートをエクスポート</h3>
                        <button class="modal-close" onclick="App.reports.closeModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="export-options">
                            <!-- Reporte Anual -->
                            <div class="export-option glass-panel" style="padding: 1rem; margin-bottom: 1rem; cursor: pointer;"
                                 onclick="App.reports.downloadAnnualLedger(${year}); App.reports.closeModal();">
                                <div style="display: flex; align-items: center; gap: 1rem;">
                                    <span style="font-size: 2rem;">📊</span>
                                    <div>
                                        <h4 style="margin: 0; color: var(--text-primary);">年次有給休暇管理簿</h4>
                                        <p style="margin: 0; color: var(--text-secondary); font-size: 0.85rem;">
                                            ${year}年度 - 法定必須書類
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <!-- Reporte de Cumplimiento -->
                            <div class="export-option glass-panel" style="padding: 1rem; margin-bottom: 1rem; cursor: pointer;"
                                 onclick="App.reports.downloadComplianceReport(${year}); App.reports.closeModal();">
                                <div style="display: flex; align-items: center; gap: 1rem;">
                                    <span style="font-size: 2rem;">✅</span>
                                    <div>
                                        <h4 style="margin: 0; color: var(--text-primary);">5日取得義務レポート</h4>
                                        <p style="margin: 0; color: var(--text-secondary); font-size: 0.85rem;">
                                            ${year}年度 - コンプライアンス状況
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <!-- Reporte Mensual -->
                            <div class="export-option glass-panel" style="padding: 1rem; margin-bottom: 1rem;">
                                <div style="display: flex; align-items: center; gap: 1rem;">
                                    <span style="font-size: 2rem;">📅</span>
                                    <div style="flex: 1;">
                                        <h4 style="margin: 0; color: var(--text-primary);">月次レポート</h4>
                                        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                                            <select id="pdf-month-select" style="flex: 1; padding: 0.5rem; border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color);">
                                                ${Array.from({ length: 12 }, (_, i) => i + 1).map(m =>
            `<option value="${m}" ${m === currentMonth ? 'selected' : ''}>${m}月</option>`
        ).join('')}
                                            </select>
                                            <button class="btn btn-primary btn-sm" onclick="App.reports.downloadMonthlySummary(${year}, document.getElementById('pdf-month-select').value); App.reports.closeModal();">
                                                ダウンロード
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Reporte Personalizado -->
                            <div class="export-option glass-panel" style="padding: 1rem; cursor: pointer;"
                                 onclick="App.reports.showCustomReportForm();">
                                <div style="display: flex; align-items: center; gap: 1rem;">
                                    <span style="font-size: 2rem;">⚙️</span>
                                    <div>
                                        <h4 style="margin: 0; color: var(--text-primary);">カスタムレポート</h4>
                                        <p style="margin: 0; color: var(--text-secondary); font-size: 0.85rem;">
                                            フィルターと列を選択
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Insertar modal en el DOM
        const existingModal = document.getElementById('pdf-export-modal');
        if (existingModal) {
            existingModal.remove();
        }
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Agregar estilos hover
        document.querySelectorAll('.export-option').forEach(opt => {
            opt.addEventListener('mouseenter', () => {
                opt.style.transform = 'translateX(5px)';
                opt.style.borderColor = 'var(--primary)';
            });
            opt.addEventListener('mouseleave', () => {
                opt.style.transform = '';
                opt.style.borderColor = '';
            });
        });
    },

    /**
     * Muestra formulario de reporte personalizado
     */
    showCustomReportForm() {
        const year = App.state.year || new Date().getFullYear();
        const factories = [...new Set(App.state.data.map(e => e.haken).filter(Boolean))];

        const formHtml = `
            <div id="custom-report-form">
                <h4 style="margin-bottom: 1rem;">カスタムレポート設定</h4>

                <div style="margin-bottom: 1rem;">
                    <label style="display: block; margin-bottom: 0.3rem; color: var(--text-secondary);">タイトル</label>
                    <input type="text" id="custom-report-title" value="カスタム有給レポート"
                           style="width: 100%; padding: 0.5rem; border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color);">
                </div>

                <div style="margin-bottom: 1rem;">
                    <label style="display: block; margin-bottom: 0.3rem; color: var(--text-secondary);">派遣先フィルター</label>
                    <select id="custom-report-dept" style="width: 100%; padding: 0.5rem; border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color);">
                        <option value="">全て</option>
                        ${factories.map(f => `<option value="${App.utils.escapeAttr(f)}">${App.utils.escapeHtml(f)}</option>`).join('')}
                    </select>
                </div>

                <div style="margin-bottom: 1rem;">
                    <label style="display: block; margin-bottom: 0.3rem; color: var(--text-secondary);">残日数フィルター</label>
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="number" id="custom-report-min-balance" placeholder="最小" min="0" max="40"
                               style="flex: 1; padding: 0.5rem; border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color);">
                        <input type="number" id="custom-report-max-balance" placeholder="最大" min="0" max="40"
                               style="flex: 1; padding: 0.5rem; border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color);">
                    </div>
                </div>

                <div style="margin-bottom: 1rem;">
                    <label style="display: block; margin-bottom: 0.3rem; color: var(--text-secondary);">並び替え</label>
                    <select id="custom-report-sort" style="width: 100%; padding: 0.5rem; border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color);">
                        <option value="employee_num">社員番号</option>
                        <option value="name">名前</option>
                        <option value="balance">残日数</option>
                        <option value="used">使用日数</option>
                        <option value="usage_rate">使用率</option>
                    </select>
                </div>

                <div style="display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1.5rem;">
                    <button class="btn btn-secondary" onclick="App.reports.showExportModal();">戻る</button>
                    <button class="btn btn-primary" onclick="App.reports.generateCustomReport();">PDF生成</button>
                </div>
            </div>
        `;

        document.querySelector('#pdf-export-modal .modal-body').innerHTML = formHtml;
    },

    /**
     * Genera reporte personalizado desde el formulario
     */
    async generateCustomReport() {
        const year = App.state.year || new Date().getFullYear();
        const config = {
            title: document.getElementById('custom-report-title').value || 'Custom Report',
            filters: {
                year: year,
                department: document.getElementById('custom-report-dept').value || null,
                min_balance: parseFloat(document.getElementById('custom-report-min-balance').value) || null,
                max_balance: parseFloat(document.getElementById('custom-report-max-balance').value) || null
            },
            columns: ['employee_num', 'name', 'haken', 'granted', 'used', 'balance', 'usage_rate'],
            sort_by: document.getElementById('custom-report-sort').value,
            include_stats: true
        };

        // Limpiar filtros nulos
        Object.keys(config.filters).forEach(key => {
            if (config.filters[key] === null || config.filters[key] === '') {
                delete config.filters[key];
            }
        });

        this.closeModal();
        await this.downloadCustomReport(config);
    },

    /**
     * Cierra el modal de exportacion
     */
    closeModal() {
        const modal = document.getElementById('pdf-export-modal');
        if (modal) {
            modal.remove();
        }
    },

    /**
     * Utilidad para descargar un blob como archivo
     * @param {Blob} blob - Blob del archivo
     * @param {string} filename - Nombre del archivo
     */
    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
};

// ========================================
// CALENDAR MODULE (Grid View)
// ========================================
App.calendar = {
    currentDate: new Date(),
    events: [],

    init() {
        const container = document.getElementById('calendar-grid');
        if (container) {
            this.render();
            // Load events if visible
            if (container.offsetParent !== null) {
                this.loadEvents();
            }
        }

        // Bind button actions globally if not already bound
        document.querySelectorAll('[data-action^="calendar."]').forEach(btn => {
            const action = btn.dataset.action.split('.')[1]; // prevMonth, nextMonth, etc
            if (this[action]) {
                btn.onclick = () => this[action]();
            }
        });
    },

    prevMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        this.render();
        this.loadEvents();
    },

    nextMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        this.render();
        this.loadEvents();
    },

    goToToday() {
        this.currentDate = new Date();
        this.render();
        this.loadEvents();
    },

    /* Render the grid structure (empty) */
    render() {
        const container = document.getElementById('calendar-grid');
        if (!container) return;

        container.className = 'calendar-grid';

        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();

        /* Update Title */
        const titleEl = document.getElementById('calendar-month-label') || document.getElementById('calendar-month-title');
        if (titleEl) {
            const months = ['1月', '2月', '3月', '4月', '5月', '6月',
                '7月', '8月', '9月', '10月', '11月', '12月'];
            titleEl.textContent = `${year}年 ${months[month]}`;
        }

        /* Build Grid HTML */
        let html = '';

        /* Headers */
        const days = ['日', '月', '火', '水', '木', '金', '土'];
        days.forEach(day => {
            html += `<div class="calendar-header-cell">${day}</div>`;
        });

        /* Days calculation */
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const today = new Date();
        const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;

        /* Padding */
        for (let i = 0; i < firstDay; i++) {
            html += `<div class="calendar-day empty"></div>`;
        }

        /* Actual Days */
        for (let i = 1; i <= daysInMonth; i++) {
            const isToday = isCurrentMonth && i === today.getDate();
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;

            html += `
            <div class="calendar-day ${isToday ? 'today' : ''}" id="cal-day-${dateStr}">
                <span class="calendar-date-label">${i}</span>
                <div id="cal-events-${dateStr}" class="calendar-events-list"></div>
            </div>
            `;
        }

        container.innerHTML = html;

        // Re-bind listeners that might have been lost
        this.bindDayClicks();
    },

    bindDayClicks() {
        // Optional: Add click handlers to days for adding new events
    },

    /* Fetch and display events */
    async loadEvents() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth() + 1;

        try {
            App.ui.showLoading();

            // source='all' to get both requests and excel usage
            // The backend endpoint is /api/calendar/events
            const response = await fetch(`${App.config.apiBase}/calendar/events?year=${year}&month=${month}&source=all`);
            const json = await response.json();
            App.ui.hideLoading();

            if (json.status === 'success' && json.events) {
                this.displayEvents(json.events);
            }
        } catch (error) {
            console.error('Failed to load calendar events', error);
            App.ui.hideLoading();
            App.ui.showToast('error', 'カレンダーデータの取得に失敗しました');
        }
    },

    displayEvents(events) {
        // Clear existing events (though render() usually clears them)
        // This is safe because render() is called before loadEvents() typically.

        events.forEach(evt => {
            // Handle multi-day events
            let current = new Date(evt.start);
            const end = new Date(evt.end);

            // Safety break for infinite loops
            let loopCount = 0;

            while (current <= end && loopCount < 31) {
                loopCount++;

                // Format date as YYYY-MM-DD
                const y = current.getFullYear();
                const m = String(current.getMonth() + 1).padStart(2, '0');
                const d = String(current.getDate()).padStart(2, '0');
                const dateStr = `${y}-${m}-${d}`;

                const container = document.getElementById(`cal-events-${dateStr}`);
                if (container) {
                    const el = document.createElement('div');

                    // Determine class based on leave_type
                    let typeClass = 'event-full'; // default
                    if (evt.leave_type === 'half_am') typeClass = 'event-am';
                    else if (evt.leave_type === 'half_pm') typeClass = 'event-pm';
                    else if (evt.leave_type === 'hourly') typeClass = 'event-hourly';
                    else if (evt.type === 'usage_detail') typeClass = 'event-full'; // usage from excel

                    el.className = `calendar-event ${typeClass}`;
                    el.title = evt.title; // Tooltip
                    // Simplify text for small view: "Name (Type)"
                    el.textContent = evt.title.split('(')[0];

                    container.appendChild(el);
                }

                // Next day
                current.setDate(current.getDate() + 1);
            }
        });
    }
};

window.App = App;

document.addEventListener('DOMContentLoaded', () => {
    App.init();

    // Start preloading GSAP in background immediately
    // This uses requestIdleCallback to avoid blocking initial render
    if (App.animations && App.animations.preloadInBackground) {
        App.animations.preloadInBackground();
    }

    // ========================================
    // CALENDAR MODULE (Grid View)
    // ========================================


    // Initialize GSAP animations after a short delay
    // GSAP will be loaded on-demand if not already preloaded
    setTimeout(() => {
        if (App.animations) {
            App.animations.init();
        }
    }, 300);
});
