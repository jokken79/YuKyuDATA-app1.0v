/**
 * Auth Manager - JWT Token Management
 * Handles authentication state, token storage, and API request authentication
 */

class AuthManager {
    constructor() {
        this.tokenKey = 'yukyu_auth_token';
        this.userKey = 'yukyu_user_data';
        this.token = this.getStoredToken();
        this.user = this.getStoredUser();
        this.listeners = [];
    }

    /**
     * Get stored token from localStorage
     */
    getStoredToken() {
        return localStorage.getItem(this.tokenKey);
    }

    /**
     * Get stored user data from localStorage
     */
    getStoredUser() {
        const userData = localStorage.getItem(this.userKey);
        return userData ? JSON.parse(userData) : null;
    }

    /**
     * Store token in localStorage
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem(this.tokenKey, token);
        this.notifyListeners();
    }

    /**
     * Store user data in localStorage
     */
    setUser(user) {
        this.user = user;
        localStorage.setItem(this.userKey, JSON.stringify(user));
        this.notifyListeners();
    }

    /**
     * Clear authentication data
     */
    clearAuth() {
        this.token = null;
        this.user = null;
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
        this.notifyListeners();
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Check if user has admin role
     */
    isAdmin() {
        return this.user && this.user.role === 'admin';
    }

    /**
     * Get current user info
     */
    getCurrentUser() {
        return this.user;
    }

    /**
     * Login with credentials
     */
    async login(username, password) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();

            // Store token and user data
            this.setToken(data.access_token);
            this.setUser({
                username: data.username,
                role: data.role,
                user_id: data.user_id
            });

            return { success: true, data };
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            // Optional: Call backend logout endpoint
            if (this.isAuthenticated()) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: this.getAuthHeaders(),
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.clearAuth();
        }
    }

    /**
     * Get authentication headers for API requests
     */
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    /**
     * Make authenticated API request
     */
    async authFetch(url, options = {}) {
        const config = {
            ...options,
            headers: {
                ...this.getAuthHeaders(),
                ...(options.headers || {}),
            },
        };

        try {
            const response = await fetch(url, config);

            // Handle 401 Unauthorized - token expired or invalid
            if (response.status === 401) {
                this.clearAuth();
                this.showLoginRequired();
                throw new Error('Authentication required');
            }

            return response;
        } catch (error) {
            console.error('Auth fetch error:', error);
            throw error;
        }
    }

    /**
     * Show login required notification
     */
    showLoginRequired() {
        // Trigger login modal if available
        const event = new CustomEvent('auth:loginRequired');
        window.dispatchEvent(event);
    }

    /**
     * Subscribe to auth state changes
     */
    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(cb => cb !== callback);
        };
    }

    /**
     * Notify all listeners of auth state change
     */
    notifyListeners() {
        this.listeners.forEach(callback => {
            callback({
                isAuthenticated: this.isAuthenticated(),
                user: this.user,
                token: this.token,
            });
        });
    }

    /**
     * Verify token validity with backend
     */
    async verifyToken() {
        if (!this.token) {
            return false;
        }

        try {
            const response = await this.authFetch('/api/auth/verify');
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Create singleton instance
const authManager = new AuthManager();

// Export for use in other modules
window.AuthManager = authManager;

export default authManager;
