/**
 * Login Modal Component
 * Premium login interface with validation and error handling
 */

import authManager from '../utils/auth-manager.js';

class LoginModal {
    constructor() {
        this.modal = null;
        this.isOpen = false;
        this.init();
    }

    /**
     * Initialize the modal
     */
    init() {
        this.createModal();
        this.attachEventListeners();

        // Listen for login required events
        window.addEventListener('auth:loginRequired', () => {
            this.show();
        });
    }

    /**
     * Create modal HTML structure
     */
    createModal() {
        const modalHTML = `
            <div id="login-modal" class="modal-overlay" style="display: none;">
                <div class="modal-container">
                    <div class="modal-header">
                        <h2>
                            <i class="fas fa-lock"></i>
                            Iniciar Sesión
                        </h2>
                        <button class="modal-close" aria-label="Cerrar">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-body">
                        <form id="login-form" autocomplete="off">
                            <div class="form-group">
                                <label for="login-username">
                                    <i class="fas fa-user"></i>
                                    Usuario
                                </label>
                                <input 
                                    type="text" 
                                    id="login-username" 
                                    name="username"
                                    class="form-control"
                                    placeholder="Ingrese su usuario"
                                    required
                                    autocomplete="username"
                                />
                            </div>

                            <div class="form-group">
                                <label for="login-password">
                                    <i class="fas fa-key"></i>
                                    Contraseña
                                </label>
                                <div class="password-input-wrapper">
                                    <input 
                                        type="password" 
                                        id="login-password" 
                                        name="password"
                                        class="form-control"
                                        placeholder="Ingrese su contraseña"
                                        required
                                        autocomplete="current-password"
                                    />
                                    <button 
                                        type="button" 
                                        class="toggle-password"
                                        aria-label="Mostrar/Ocultar contraseña"
                                    >
                                        <i class="fas fa-eye"></i>
                                    </button>
                                </div>
                            </div>

                            <div id="login-error" class="alert alert-error" style="display: none;">
                                <i class="fas fa-exclamation-circle"></i>
                                <span class="error-message"></span>
                            </div>

                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary btn-block" id="login-submit">
                                    <i class="fas fa-sign-in-alt"></i>
                                    Iniciar Sesión
                                </button>
                            </div>

                            <div class="dev-credentials" style="display: none;">
                                <small class="text-muted">
                                    <strong>Credenciales de desarrollo:</strong><br>
                                    Admin: <code>admin</code> / <code>admin123456</code><br>
                                    Usuario: <code>demo</code> / <code>demo123456</code>
                                </small>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;

        // Insert modal into DOM
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = modalHTML;
        document.body.appendChild(tempDiv.firstElementChild);

        this.modal = document.getElementById('login-modal');

        // Show dev credentials if in debug mode
        if (localStorage.getItem('yukyu_debug') === 'true') {
            this.modal.querySelector('.dev-credentials').style.display = 'block';
        }
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Close button
        const closeBtn = this.modal.querySelector('.modal-close');
        closeBtn.addEventListener('click', () => this.hide());

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
        const passwordInput = this.modal.querySelector('#login-password');

        togglePassword.addEventListener('click', () => {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;

            const icon = togglePassword.querySelector('i');
            icon.classList.toggle('fa-eye');
            icon.classList.toggle('fa-eye-slash');
        });

        // Form submission
        const form = this.modal.querySelector('#login-form');
        form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    /**
     * Handle form submission
     */
    async handleSubmit(e) {
        e.preventDefault();

        const username = this.modal.querySelector('#login-username').value.trim();
        const password = this.modal.querySelector('#login-password').value;
        const submitBtn = this.modal.querySelector('#login-submit');
        const errorDiv = this.modal.querySelector('#login-error');

        // Validate inputs
        if (!username || !password) {
            this.showError('Por favor complete todos los campos');
            return;
        }

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Iniciando sesión...';
        this.hideError();

        try {
            // Attempt login
            const result = await authManager.login(username, password);

            if (result.success) {
                // Success
                this.showSuccess();
                setTimeout(() => {
                    this.hide();
                    this.resetForm();

                    // Trigger login success event
                    window.dispatchEvent(new CustomEvent('auth:loginSuccess', {
                        detail: { user: authManager.getCurrentUser() }
                    }));

                    // Reload page to update UI
                    window.location.reload();
                }, 1000);
            } else {
                // Error
                this.showError(result.error || 'Credenciales inválidas');
            }
        } catch (error) {
            this.showError('Error de conexión. Intente nuevamente.');
            console.error('Login error:', error);
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Iniciar Sesión';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const errorDiv = this.modal.querySelector('#login-error');
        const errorMessage = errorDiv.querySelector('.error-message');

        errorMessage.textContent = message;
        errorDiv.style.display = 'flex';

        // Shake animation
        errorDiv.classList.add('shake');
        setTimeout(() => errorDiv.classList.remove('shake'), 500);
    }

    /**
     * Hide error message
     */
    hideError() {
        const errorDiv = this.modal.querySelector('#login-error');
        errorDiv.style.display = 'none';
    }

    /**
     * Show success message
     */
    showSuccess() {
        const form = this.modal.querySelector('#login-form');
        form.innerHTML = `
            <div class="alert alert-success text-center">
                <i class="fas fa-check-circle fa-3x mb-3"></i>
                <h3>¡Bienvenido!</h3>
                <p>Inicio de sesión exitoso</p>
            </div>
        `;
    }

    /**
     * Reset form to initial state
     */
    resetForm() {
        const form = this.modal.querySelector('#login-form');
        if (form) {
            form.reset();
            this.hideError();
        }
    }

    /**
     * Show modal
     */
    show() {
        this.modal.style.display = 'flex';
        this.isOpen = true;

        // Focus on username input
        setTimeout(() => {
            this.modal.querySelector('#login-username').focus();
        }, 100);

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    /**
     * Hide modal
     */
    hide() {
        this.modal.style.display = 'none';
        this.isOpen = false;
        this.resetForm();

        // Restore body scroll
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
