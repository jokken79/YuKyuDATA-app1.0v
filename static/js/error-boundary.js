/**
 * Error Boundary Module
 * Implementa error boundaries para mejor manejo de errores
 * @module error-boundary
 */

/**
 * Clase para manejar errores de la aplicación
 */
export class ErrorBoundary {
    constructor(options = {}) {
        /** @type {Function} Callback para errores */
        this.onError = options.onError || this.defaultErrorHandler;
        
        /** @type {Function} Callback para errores asíncronos */
        this.onAsyncError = options.onAsyncError || this.defaultAsyncErrorHandler;
        
        /** @type {Function} Callback para rechazos de promesas no manejados */
        this.onUnhandledRejection = options.onUnhandledRejection || this.defaultUnhandledRejectionHandler;
        
        /** @type {Array} Array de errores registrados */
        this.errors = [];
        
        /** @type {boolean} Flag para controlar si está activo */
        this.isActive = true;
        
        this.setupGlobalHandlers();
    }

    /**
     * Configura los manejadores globales de errores
     */
    setupGlobalHandlers() {
        // Error síncrono
        window.addEventListener('error', (event) => {
            if (!this.isActive) return;
            
            const error = {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error,
                timestamp: new Date().toISOString(),
                type: 'sync'
            };
            
            this.handleError(error);
        });

        // Error asíncrono
        window.addEventListener('unhandledrejection', (event) => {
            if (!this.isActive) return;
            
            const error = {
                message: event.reason?.message || 'Unhandled Promise Rejection',
                reason: event.reason,
                timestamp: new Date().toISOString(),
                type: 'promise'
            };
            
            this.handleUnhandledRejection(error);
        });
    }

    /**
     * Maneja un error y lo registra
     * @param {Object} errorInfo - Información del error
     */
    handleError(errorInfo) {
        this.errors.push(errorInfo);
        
        // Limitar a 100 errores para evitar memory leaks
        if (this.errors.length > 100) {
            this.errors = this.errors.slice(-50);
        }
        
        this.onError(errorInfo);
    }

    /**
     * Maneja rechazos de promesas no manejados
     * @param {Object} errorInfo - Información del error
     */
    handleUnhandledRejection(errorInfo) {
        this.errors.push(errorInfo);
        
        // Limitar a 100 errores
        if (this.errors.length > 100) {
            this.errors = this.errors.slice(-50);
        }
        
        this.onUnhandledRejection(errorInfo);
    }

    /**
     * Manejador por defecto para errores
     * @param {Object} errorInfo - Información del error
     */
    defaultErrorHandler(errorInfo) {
        console.error('Error Boundary caught an error:', errorInfo);
        
        // Mostrar notificación de error al usuario
        this.showErrorNotification(errorInfo);
        
        // Enviar error al servidor si está configurado
        this.reportError(errorInfo);
    }

    /**
     * Manejador por defecto para errores asíncronos
     * @param {Object} errorInfo - Información del error
     */
    defaultAsyncErrorHandler(errorInfo) {
        console.error('Error Boundary caught an async error:', errorInfo);
        this.showErrorNotification(errorInfo);
        this.reportError(errorInfo);
    }

    /**
     * Manejador por defecto para rechazos de promesas
     * @param {Object} errorInfo - Información del error
     */
    defaultUnhandledRejectionHandler(errorInfo) {
        console.error('Error Boundary caught unhandled rejection:', errorInfo);
        this.showErrorNotification(errorInfo);
        this.reportError(errorInfo);
    }

    /**
     * Muestra una notificación de error al usuario
     * @param {Object} errorInfo - Información del error
     */
    showErrorNotification(errorInfo) {
        // Crear toast de error si existe el sistema de toast
        if (window.ModernUI && window.ModernUI.Toast) {
            window.ModernUI.Toast.show({
                type: 'error',
                title: 'Error',
                message: this.getErrorMessage(errorInfo),
                duration: 5000
            });
        } else {
            // Fallback a alerta simple
            const message = this.getErrorMessage(errorInfo);
            if (!document.getElementById('error-toast')) {
                const toast = document.createElement('div');
                toast.id = 'error-toast';
                toast.className = 'error-toast';
                toast.innerHTML = `
                    <div class="error-toast-content">
                        <strong>Error:</strong> ${message}
                        <button onclick="this.parentElement.parentElement.remove()" class="error-toast-close">×</button>
                    </div>
                `;
                toast.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #ef4444;
                    color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    z-index: 10000;
                    max-width: 400px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                `;
                document.body.appendChild(toast);
                
                // Auto-remover después de 5 segundos
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.remove();
                    }
                }, 5000);
            }
        }
    }

    /**
     * Obtiene un mensaje de error legible para el usuario
     * @param {Object} errorInfo - Información del error
     * @returns {string} - Mensaje de error
     */
    getErrorMessage(errorInfo) {
        // Errores comunes con mensajes amigables
        const commonErrors = {
            'NetworkError': 'Error de conexión. Verifica tu internet.',
            'TypeError': 'Error en los datos. Intenta recargar la página.',
            'ReferenceError': 'Error interno. Contacta al soporte.',
            'ChunkLoadError': 'Error cargando la aplicación. Recarga la página.',
            'Failed to fetch': 'Error de conexión con el servidor.',
            'Network request failed': 'Error de red. Intenta más tarde.'
        };

        const message = errorInfo.message || '';
        
        // Buscar error común
        for (const [key, friendlyMessage] of Object.entries(commonErrors)) {
            if (message.includes(key)) {
                return friendlyMessage;
            }
        }
        
        // Mensaje genérico si no se encuentra coincidencia
        return 'Ocurrió un error inesperado. Intenta recargar la página.';
    }

    /**
     * Reporta el error al servidor
     * @param {Object} errorInfo - Información del error
     */
    async reportError(errorInfo) {
        try {
            // Solo reportar en producción
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                return;
            }
            
            const reportData = {
                ...errorInfo,
                userAgent: navigator.userAgent,
                url: window.location.href,
                timestamp: new Date().toISOString(),
                sessionId: this.getSessionId()
            };
            
            await fetch('/api/error-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(reportData)
            });
        } catch (reportError) {
            console.warn('Failed to report error:', reportError);
        }
    }

    /**
     * Obtiene o crea un ID de sesión
     * @returns {string} - ID de sesión
     */
    getSessionId() {
        let sessionId = sessionStorage.getItem('error-session-id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('error-session-id', sessionId);
        }
        return sessionId;
    }

    /**
     * Envuelve una función con manejo de errores
     * @param {Function} fn - Función a envolver
     * @param {string} context - Contexto para el error
     * @returns {Function} - Función envuelta
     */
    wrapFunction(fn, context = 'unknown') {
        return (...args) => {
            try {
                const result = fn.apply(this, args);
                
                // Si es una promesa, manejar errores asíncronos
                if (result && typeof result.catch === 'function') {
                    return result.catch(error => {
                        this.handleError({
                            message: error.message,
                            error: error,
                            context,
                            timestamp: new Date().toISOString(),
                            type: 'async'
                        });
                        throw error;
                    });
                }
                
                return result;
            } catch (error) {
                this.handleError({
                    message: error.message,
                    error: error,
                    context,
                    timestamp: new Date().toISOString(),
                    type: 'sync'
                });
                throw error;
            }
        };
    }

    /**
     * Desactiva el error boundary
     */
    deactivate() {
        this.isActive = false;
    }

    /**
     * Activa el error boundary
     */
    activate() {
        this.isActive = true;
    }

    /**
     * Limpia los errores registrados
     */
    clearErrors() {
        this.errors = [];
    }

    /**
     * Obtiene los errores registrados
     * @returns {Array} - Array de errores
     */
    getErrors() {
        return [...this.errors];
    }

    /**
     * Obtiene estadísticas de errores
     * @returns {Object} - Estadísticas
     */
    getErrorStats() {
        const stats = {
            total: this.errors.length,
            byType: {},
            recent: this.errors.slice(-10)
        };
        
        this.errors.forEach(error => {
            stats.byType[error.type] = (stats.byType[error.type] || 0) + 1;
        });
        
        return stats;
    }
}

/**
 * Componente Error Boundary para React-like components
 */
export class ComponentErrorBoundary {
    constructor(container, fallbackComponent) {
        this.container = container;
        this.fallbackComponent = fallbackComponent;
        this.originalContent = container.innerHTML;
        this.hasError = false;
    }

    /**
     * Detecta errores en componentes
     * @param {Function} renderFunction - Función de renderizado
     */
    catchErrors(renderFunction) {
        try {
            if (!this.hasError) {
                renderFunction();
            }
        } catch (error) {
            this.hasError = true;
            this.renderFallback(error);
        }
    }

    /**
     * Renderiza el componente fallback
     * @param {Error} error - Error capturado
     */
    renderFallback(error) {
        if (typeof this.fallbackComponent === 'function') {
            this.container.innerHTML = this.fallbackComponent(error);
        } else {
            this.container.innerHTML = `
                <div class="error-fallback">
                    <h3>Algo salió mal</h3>
                    <p>Por favor, recarga la página e intenta nuevamente.</p>
                    <button onclick="location.reload()" class="btn btn-primary">
                        Recargar Página
                    </button>
                </div>
            `;
        }
    }

    /**
     * Reinicia el error boundary
     */
    reset() {
        this.hasError = false;
        this.container.innerHTML = this.originalContent;
    }
}

/**
 * Instancia global del Error Boundary
 */
export const globalErrorBoundary = new ErrorBoundary({
    onError: (errorInfo) => {
        console.error('Global error:', errorInfo);
    },
    onUnhandledRejection: (errorInfo) => {
        console.error('Unhandled rejection:', errorInfo);
    }
});

export default ErrorBoundary;