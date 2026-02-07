/**
 * Login Modal Component - YuKyuDATA Design System v4
 * Premium authentication interface with validation and error handling
 * Uses SVG icons (no FontAwesome dependency)
 */

import authManager from '../utils/auth-manager.js';

const ICONS = {
    user: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    lock: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    eye: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="eye-icon"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
    eyeOff: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="eye-off-icon" style="display:none"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>',
    check: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    spinner: '<span class="btn-spinner"></span>'
};

class LoginModal {
    constructor() {
        this.modal = null;
        this.isOpen = false;
        this.init();
    }

    init() {
        this.createModal();
        this.attachEventListeners();

        window.addEventListener('auth:loginRequired', () => {
            this.show();
        });
    }

    createModal() {
        const modalHTML = `
            <div id="login-modal-component" class="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="login-modal-component-title">
                <div class="modal-container">
                    <div class="login-branding">
                        <div class="login-logo" aria-hidden="true">有</div>
                        <h2 id="login-modal-component-title" class="login-title">YuKyuDATA</h2>
                        <p class="login-subtitle">有給休暇管理システム</p>
                    </div>

                    <form id="login-form-component" class="login-form" autocomplete="off">
                        <div class="form-group">
                            <label for="login-username-component" class="form-label">
                                ${ICONS.user}
                                Username
                            </label>
                            <input
                                type="text"
                                id="login-username-component"
                                name="username"
                                class="form-control"
                                placeholder="Enter your username"
                                required
                                autocomplete="username"
                            />
                        </div>

                        <div class="form-group">
                            <label for="login-password-component" class="form-label">
                                ${ICONS.lock}
                                Password
                            </label>
                            <div class="password-input-wrapper">
                                <input
                                    type="password"
                                    id="login-password-component"
                                    name="password"
                                    class="form-control"
                                    placeholder="Enter your password"
                                    required
                                    autocomplete="current-password"
                                />
                                <button
                                    type="button"
                                    class="toggle-password"
                                    aria-label="Toggle password visibility"
                                    tabindex="-1"
                                >
                                    ${ICONS.eye}
                                    ${ICONS.eyeOff}
                                </button>
                            </div>
                        </div>

                        <div id="login-error-component" class="alert alert-error" style="display: none;">
                            <span class="error-message"></span>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn-login" id="login-submit-component">
                                <span class="btn-text">Log In</span>
                                <span class="btn-spinner d-none"></span>
                            </button>
                        </div>

                        <div class="dev-credentials" style="display: none;">
                            <strong>Development Mode</strong><br>
                            <code>Check server console for credentials</code>
                        </div>
                    </form>
                </div>
            </div>
        `;

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = modalHTML;
        document.body.appendChild(tempDiv.firstElementChild);

        this.modal = document.getElementById('login-modal-component');

        if (localStorage.getItem('yukyu_debug') === 'true') {
            const devCreds = this.modal.querySelector('.dev-credentials');
            if (devCreds) devCreds.style.display = 'block';
        }
    }

    attachEventListeners() {
        // Click outside to close
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hide();
            }
        });

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.hide();
            }
        });

        // Password toggle
        const togglePassword = this.modal.querySelector('.toggle-password');
        const passwordInput = this.modal.querySelector('[id$="-password-component"]');

        if (togglePassword && passwordInput) {
            togglePassword.addEventListener('click', () => {
                const isPassword = passwordInput.type === 'password';
                passwordInput.type = isPassword ? 'text' : 'password';
                togglePassword.querySelector('.eye-icon').style.display = isPassword ? 'none' : '';
                togglePassword.querySelector('.eye-off-icon').style.display = isPassword ? '' : 'none';
            });
        }

        // Form submission
        const form = this.modal.querySelector('form');
        form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    async handleSubmit(e) {
        e.preventDefault();

        const username = this.modal.querySelector('[name="username"]').value.trim();
        const password = this.modal.querySelector('[name="password"]').value;
        const submitBtn = this.modal.querySelector('.btn-login');
        const btnText = submitBtn.querySelector('.btn-text');
        const btnSpinner = submitBtn.querySelector('.btn-spinner');

        if (!username || !password) {
            this.showError('Please fill in all fields');
            return;
        }

        // Show loading state
        submitBtn.disabled = true;
        btnText.textContent = 'Signing in...';
        btnSpinner.classList.remove('d-none');
        this.hideError();

        try {
            const result = await authManager.login(username, password);

            if (result.success) {
                this.showSuccess();
                setTimeout(() => {
                    this.hide();
                    this.resetForm();

                    window.dispatchEvent(new CustomEvent('auth:loginSuccess', {
                        detail: { user: authManager.getCurrentUser() }
                    }));

                    window.location.reload();
                }, 1000);
            } else {
                this.showError(result.error || 'Invalid credentials');
            }
        } catch (error) {
            this.showError('Connection error. Please try again.');
        } finally {
            submitBtn.disabled = false;
            btnText.textContent = 'Log In';
            btnSpinner.classList.add('d-none');
        }
    }

    showError(message) {
        const errorDiv = this.modal.querySelector('.alert-error');
        const errorMessage = errorDiv.querySelector('.error-message');

        errorMessage.textContent = message;
        errorDiv.style.display = 'flex';

        errorDiv.classList.add('shake');
        setTimeout(() => errorDiv.classList.remove('shake'), 500);
    }

    hideError() {
        const errorDiv = this.modal.querySelector('.alert-error');
        if (errorDiv) errorDiv.style.display = 'none';
    }

    showSuccess() {
        const form = this.modal.querySelector('form');
        form.innerHTML = `
            <div class="login-success">
                <div class="login-success-icon">${ICONS.check}</div>
                <h3>Welcome!</h3>
                <p>Login successful</p>
            </div>
        `;
    }

    resetForm() {
        const form = this.modal.querySelector('form');
        if (form && form.reset) {
            form.reset();
            this.hideError();
        }
    }

    show() {
        this.modal.classList.add('active');
        this.isOpen = true;

        setTimeout(() => {
            const usernameInput = this.modal.querySelector('[name="username"]');
            if (usernameInput) usernameInput.focus();
        }, 150);

        document.body.style.overflow = 'hidden';
    }

    hide() {
        this.modal.classList.remove('active');
        this.isOpen = false;
        this.resetForm();
        document.body.style.overflow = '';
    }
}

// Initialize login modal when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.loginModal = new LoginModal();
    });
} else {
    window.loginModal = new LoginModal();
}

export default LoginModal;
