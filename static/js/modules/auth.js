/**
 * YuKyu Authentication Module
 * Handles login/logout using secure HttpOnly cookie session.
 */
export const Auth = {
    token: null,
    user: null,
    config: {
        apiBase: '/api/v1'
    },
    uiCallback: null,

    init(uiCallback) {
        this.uiCallback = uiCallback;
        this.updateState(false);
        this.checkSession();
        this.bindEvents();
    },

    async checkSession() {
        try {
            const res = await fetch(`${this.config.apiBase}/auth/verify`, {
                method: 'GET',
                credentials: 'include'
            });
            this.updateState(res.ok);
        } catch (error) {
            this.updateState(false);
        }
    },

    bindEvents() {
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
    },

    updateState(isLoggedIn) {
        if (this.uiCallback) {
            this.uiCallback(isLoggedIn);
        }
    },

    getCsrfToken() {
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }

        const cookieValue = `; ${document.cookie}`;
        const parts = cookieValue.split('; csrf-token=');
        if (parts.length === 2) {
            return parts.pop().split(';').shift();
        }

        return null;
    },

    getRequestHeaders(method = 'GET', headers = {}) {
        const mergedHeaders = { ...headers };
        const normalizedMethod = method.toUpperCase();
        const isMutatingMethod = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(normalizedMethod);

        if (isMutatingMethod && !mergedHeaders['X-CSRF-Token']) {
            const csrfToken = this.getCsrfToken();
            if (csrfToken) {
                mergedHeaders['X-CSRF-Token'] = csrfToken;
            }
        }

        return mergedHeaders;
    },

    async handleLogin(e) {
        e.preventDefault();
        const form = e.target;
        const username = form.username.value;
        const password = form.password.value;
        const btn = form.querySelector('button[type="submit"]');
        const errorEl = document.getElementById('login-error');

        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span> Logging in...';
        }
        if (errorEl) errorEl.style.display = 'none';

        try {
            const headers = this.getRequestHeaders('POST', { 'Content-Type': 'application/json' });
            const res = await fetch(`${this.config.apiBase}/auth/login`, {
                method: 'POST',
                credentials: 'include',
                headers,
                body: JSON.stringify({ username, password })
            });

            if (!res.ok) throw new Error('Invalid credentials');

            this.updateState(true);

            const modal = document.getElementById('login-modal');
            if (modal) modal.classList.remove('active');

            form.reset();
            window.dispatchEvent(new CustomEvent('auth:login-success'));
        } catch (err) {
            console.error(err);
            if (errorEl) {
                errorEl.style.display = 'block';
                errorEl.textContent = 'Invalid username or password';
            }
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Login';
            }
        }
    },

    async logout() {
        this.token = null;
        this.user = null;
        try {
            await fetch(`${this.config.apiBase}/auth/logout`, {
                method: 'POST',
                credentials: 'include',
                headers: this.getRequestHeaders('POST')
            });
        } catch (error) {
            console.warn('Logout request failed:', error.message);
        }

        this.updateState(false);
        window.dispatchEvent(new CustomEvent('auth:logout'));
    },

    showLogin() {
        const modal = document.getElementById('login-modal');
        const input = document.getElementById('login-username');
        if (modal) modal.classList.add('active');
        if (input) input.focus();
    },

    async fetchWithAuth(url, options = {}) {
        const method = options.method || 'GET';
        const headers = this.getRequestHeaders(method, options.headers || {});

        const res = await fetch(url, {
            ...options,
            method,
            headers,
            credentials: 'include'
        });

        if (res.status === 401) {
            await this.logout();
            this.showLogin();
            throw new Error('Session expired');
        }

        return res;
    }
};
