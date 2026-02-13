/**
 * API Client - Centralized HTTP client with JWT authentication
 * Handles token storage, auto-refresh, and CSRF tokens
 */

const API_BASE = '/api/v1';

// Token storage keys
const ACCESS_TOKEN_KEY = 'yukyu_access_token';
const REFRESH_TOKEN_KEY = 'yukyu_refresh_token';
const USER_KEY = 'yukyu_user';

interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  username: string;
  role: string;
  user_id: string;
}

interface UserInfo {
  username: string;
  role: string;
}

class ApiClient {
  private refreshPromise: Promise<boolean> | null = null;

  // Token management
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  getUser(): UserInfo | null {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      localStorage.removeItem(USER_KEY);
      return null;
    }
  }

  setTokens(tokens: TokenPair): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify({
      username: tokens.username,
      role: tokens.role,
    }));
  }

  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  // Check if access token is about to expire (within 60 seconds)
  private isTokenExpiringSoon(): boolean {
    const token = this.getAccessToken();
    if (!token) return true;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiresAt = payload.exp * 1000;
      return Date.now() > expiresAt - 60000; // 60 seconds before expiry
    } catch {
      return true;
    }
  }

  // Refresh the access token
  async refreshAccessToken(): Promise<boolean> {
    // Deduplicate concurrent refresh calls
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this._doRefresh();
    try {
      return await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async _doRefresh(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        this.clearTokens();
        return false;
      }

      const tokens: TokenPair = await response.json();
      this.setTokens(tokens);
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }

  // Main fetch method with auth
  async fetch(url: string, options: RequestInit = {}): Promise<Response> {
    // Auto-refresh if token is about to expire
    if (this.isTokenExpiringSoon() && this.getRefreshToken()) {
      await this.refreshAccessToken();
    }

    const token = this.getAccessToken();
    const headers = new Headers(options.headers || {});

    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers,
    });

    // If 401, try to refresh and retry once
    if (response.status === 401 && this.getRefreshToken()) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        const newToken = this.getAccessToken();
        headers.set('Authorization', `Bearer ${newToken}`);
        return fetch(`${API_BASE}${url}`, {
          ...options,
          headers,
        });
      }
    }

    return response;
  }

  // Login
  async login(username: string, password: string): Promise<TokenPair> {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'ログインに失敗しました' }));
      throw new Error(error.detail || 'ログインに失敗しました');
    }

    const tokens: TokenPair = await response.json();
    this.setTokens(tokens);
    return tokens;
  }

  // Logout
  async logout(): Promise<void> {
    try {
      const token = this.getAccessToken();
      if (token) {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch {
      // Ignore logout errors
    } finally {
      this.clearTokens();
    }
  }
}

export const apiClient = new ApiClient();
export type { TokenPair, UserInfo };
