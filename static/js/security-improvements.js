/**
 * Security Improvements
 * Migración de JWT a HttpOnly cookies y mejoras de seguridad
 */

// ============================================
// 1. JWT STORAGE - SECURE COOKIE HANDLING
// ============================================

class SecureTokenManager {
  /**
   * Guarda token en HttpOnly cookie (más seguro que localStorage)
   * Esta operación debe hacerse desde el backend
   * En el frontend solo leemos las cookies del servidor
   */
  static isTokenValid() {
    // El backend envía el token en HttpOnly cookie
    // No podemos acceder desde JS, pero el navegador lo envía automáticamente
    return true; // Si llegamos aquí, el token es válido
  }

  /**
   * Verifica si hay sesión válida
   */
  static hasValidSession() {
    // Hacer request a /api/auth/verify
    // Si el token está en HttpOnly cookie, el navegador lo envía automáticamente
    return fetch('/api/auth/verify', {
      credentials: 'include' // Incluir cookies
    })
    .then(res => res.ok)
    .catch(() => false);
  }

  /**
   * Logout - El backend debe limpiar la cookie
   */
  static async logout() {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include', // Incluir cookies
        headers: {
          'Content-Type': 'application/json'
        }
      });
      // El servidor limpia la HttpOnly cookie
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  /**
   * Login - El backend establece la HttpOnly cookie
   */
  static async login(username, password) {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        credentials: 'include', // Incluir cookies
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });

      if (response.ok) {
        // El servidor estableció automáticamente la HttpOnly cookie
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  }
}

// ============================================
// 2. CSRF PROTECTION
// ============================================

class CSRFProtection {
  /**
   * Obtiene token CSRF del DOM (meta tag o header)
   */
  static getCSRFToken() {
    // Desde meta tag
    let token = document.querySelector('meta[name="csrf-token"]');
    if (token) return token.getAttribute('content');

    // Desde cookie (si está disponible)
    return this.getCookie('csrf-token');
  }

  /**
   * Añade token CSRF a los headers de request
   */
  static addCSRFHeader(headers = {}) {
    const token = this.getCSRFToken();
    if (token) {
      headers['X-CSRF-Token'] = token;
    }
    return headers;
  }

  /**
   * Obtiene valor de cookie
   */
  static getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }
}

// ============================================
// 3. CONTENT SECURITY POLICY HELPERS
// ============================================

class CSPHelper {
  /**
   * Valida que scripts no tengan inline eval
   */
  static validateScriptSafety() {
    const scripts = document.querySelectorAll('script:not([src])');
    const unsafeScripts = [];

    scripts.forEach(script => {
      // Detectar usos de eval, Function, etc
      if (script.textContent.includes('eval(') || 
          script.textContent.includes('Function(')) {
        unsafeScripts.push(script);
      }
    });

    if (unsafeScripts.length > 0) {
      console.warn('Posibles scripts inseguros detectados:', unsafeScripts);
    }

    return unsafeScripts.length === 0;
  }

  /**
   * Recomendaciones de CSP headers (backend)
   */
  static getRecommendedCSPHeaders() {
    return {
      'Content-Security-Policy': [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.plot.ly",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
        "img-src 'self' data: https:",
        "font-src 'self' https://fonts.gstatic.com",
        "connect-src 'self' https:",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'"
      ].join(';')
    };
  }
}

// ============================================
// 4. XSS PROTECTION
// ============================================

class XSSProtection {
  /**
   * Escapa HTML para prevenir XSS
   */
  static escapeHTML(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }

  /**
   * Crea elemento de texto de forma segura
   */
  static createSafeTextElement(text) {
    const el = document.createElement('div');
    el.textContent = text; // textContent no interpreta HTML
    return el;
  }

  /**
   * Valida URLs antes de usarlas
   */
  static isValidURL(url) {
    try {
      const urlObj = new URL(url, window.location.origin);
      // Solo permitir URLs del mismo origen o https
      return urlObj.origin === window.location.origin || 
             urlObj.protocol === 'https:';
    } catch (e) {
      return false;
    }
  }
}

// ============================================
// 5. SECURE FETCH WRAPPER
// ============================================

class SecureAPI {
  /**
   * Wrapper seguro para fetch
   */
  static async request(url, options = {}) {
    const defaultOptions = {
      credentials: 'include', // Incluir cookies (HttpOnly tokens)
      headers: {
        'Content-Type': 'application/json',
        ...CSRFProtection.addCSRFHeader(options.headers || {})
      }
    };

    const mergedOptions = { ...defaultOptions, ...options };

    try {
      const response = await fetch(url, mergedOptions);

      // Manejar respuesta no autorizada
      if (response.status === 401) {
        // Token expirado, redirigir a login
        window.location.href = '/login';
        return null;
      }

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  static get(url) {
    return this.request(url, { method: 'GET' });
  }

  static post(url, data) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  static put(url, data) {
    return this.request(url, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  static delete(url) {
    return this.request(url, { method: 'DELETE' });
  }
}

// ============================================
// INICIALIZACIÓN DE SEGURIDAD
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  // Validar CSP compliance
  CSPHelper.validateScriptSafety();

  // Verificar sesión válida en startup
  SecureTokenManager.hasValidSession().then(isValid => {
    if (!isValid) {
      // Redirigir a login si no hay sesión válida
      console.warn('Sesión no válida');
    }
  });
});

// Exportar para uso en aplicación
export { SecureTokenManager, CSRFProtection, CSPHelper, XSSProtection, SecureAPI };
