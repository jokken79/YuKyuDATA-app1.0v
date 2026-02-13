/**
 * YuKyu Authentication Module
 * Handles login, logout, and token management.
 */
import { Utils } from './utils.js';

export const Auth = {
    token: null,
    user: null,
    config: {
        apiBase: '/api/v1',
        tokenKey: 'access_token'
    },
    uiCallback: null, // Callback to update UI state

    init(uiCallback) {
        this.uiCallback = uiCallback;
        // Check for saved token
        const token = localStorage.getItem(this.config.tokenKey);
        if (token) {
            this.token = token;
            this.updateState(true);
        } else {
            this.updateState(false);
        }
        this.bindEvents();
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

    async handleLogin(e) {
        e.preventDefault();
        const form = e.target;
        const username = form.username.value;
        const password = form.password.value;
        const btn = form.querySelector('button[type="submit"]');
        const errorEl = document.getElementById('login-error');

        // Simple loading state
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span> Logging in...';
        }
        if (errorEl) errorEl.style.display = 'none';

        try {
            const res = await fetch(`${this.config.apiBase}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (!res.ok) throw new Error('Invalid credentials');

            const data = await res.json();
            this.token = data.access_token;
            localStorage.setItem(this.config.tokenKey, this.token);

            this.updateState(true);

            // Close modal safely
            const modal = document.getElementById('login-modal');
            if (modal) modal.classList.remove('active');

            form.reset();

            // Dispatch event for other modules
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

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem(this.config.tokenKey);
        this.updateState(false);
        window.dispatchEvent(new CustomEvent('auth:logout'));
    },

    showLogin() {
        const modal = document.getElementById('login-modal');
        const input = document.getElementById('login-username');
        if (modal) modal.classList.add('active');
        if (input) input.focus();
    },

    // Wrapper for authenticated fetch
    async fetchWithAuth(url, options = {}) {
        if (!this.token) {
            this.showLogin();
            throw new Error('Authentication required');
        }

        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${this.token}`
        };

        try {
            const res = await fetch(url, { ...options, headers });

            if (res.status === 401) {
                this.logout();
                this.showLogin();
                throw new Error('Session expired');
            }

            return res;
        } catch (error) {
            throw error;
        }
    }
};
