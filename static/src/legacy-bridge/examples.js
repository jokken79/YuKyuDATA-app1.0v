/**
 * Unified Bridge: Ejemplos Prácticos
 *
 * Ejemplos reales de cómo usar el bridge para migrar features
 * del sistema legacy (app.js) al moderno (static/src/)
 */

/**
 * ============================================================================
 * EJEMPLO 1: Migrar Alert Notifications
 * ============================================================================
 *
 * Antes: Modales de Bootstrap/HTML manual
 * Después: Componentes modernos mediante bridge
 */

// --- SETUP (una sola vez) ---
export function setupAlertNotifications() {
    const bridge = window.UnifiedBridge;

    // Importar componente moderno (en real, sería import)
    // import { Alert } from '/static/src/components/Alert.js';
    // bridge.registerModernComponent('Alert', Alert, {...});

    // En la práctica, si los componentes ya están importados:
    console.log('Alert notifications bridge setup');
}

// --- USAGE (legacy code calls) ---
export async function showLegacyAlert(type, message) {
    const bridge = window.UnifiedBridge;

    try {
        // Asegurar contenedor existe
        let container = document.getElementById('bridge-alerts-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'bridge-alerts-container';
            container.style.position = 'fixed';
            container.style.top = '20px';
            container.style.right = '20px';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        // Renderizar alert moderno en contenedor legacy
        await bridge.renderInLegacy('Alert', 'bridge-alerts-container', {
            type, // 'success', 'error', 'warning', 'info'
            message,
            onClose: () => {
                container.innerHTML = '';
            }
        });

        // Registrar para tracking
        bridge.trackPageView('alert_shown', 'modern');

    } catch (error) {
        console.error('Failed to show modern alert:', error);
        // Fallback a alert nativo
        alert(message);
    }
}

/**
 * ============================================================================
 * EJEMPLO 2: Sincronizar Filtro de Año entre Sistemas
 * ============================================================================
 *
 * Legacy: Desplegable en HTML controla App.state.year
 * Modern: Componentes en static/src/ leen bridge.getState('year')
 */

// --- LEGACY CODE (app.js) ---
export function setupYearFilterSync() {
    const bridge = window.UnifiedBridge;

    // Cuando el usuario cambia el año en legacy
    document.addEventListener('change', (e) => {
        if (e.target.id === 'year-filter') {
            const newYear = parseInt(e.target.value);

            // 1. Guardar en App.state (legacy)
            if (window.App?.state) {
                window.App.state.year = newYear;
            }

            // 2. Sincronizar con bridge
            bridge.syncState('selectedYear', newYear);

            // 3. Notificar que datos necesitan recargarse
            bridge.syncState('refreshData', true);

            console.log(`Year changed to ${newYear}, synced with bridge`);
        }
    });
}

// --- MODERN CODE (static/src/managers/EmployeesManager.js) ---
export function setupModernEmployeesWithBridgeSync() {
    const bridge = window.UnifiedBridge;

    // Escuchar cambios de año desde legacy
    const unsubscribe = bridge.onStateChange('selectedYear', async (newYear, oldYear) => {
        console.log(`Modern: Year changed from ${oldYear} to ${newYear}`);

        // Recargar datos
        const employees = await fetchEmployees(newYear);

        // Actualizar vista
        renderEmployeeTable(employees);
    });

    // Escuchar cambios en refreshData
    const unsubRefresh = bridge.onStateChange('refreshData', async (shouldRefresh) => {
        if (shouldRefresh) {
            const year = bridge.getState('selectedYear');
            const employees = await fetchEmployees(year);
            renderEmployeeTable(employees);

            // Resetear flag
            bridge.syncState('refreshData', false);
        }
    });

    // Retornar cleanup function
    return () => {
        unsubscribe();
        unsubRefresh();
    };
}

/**
 * ============================================================================
 * EJEMPLO 3: Feature Híbrida - Tabla Legacy + Botones Modernos
 * ============================================================================
 *
 * Escenario: Migración gradual de tabla de empleados
 * - Tabla: Mantener legacy (código complejo)
 * - Botones: Mover a moderno (componentes reutilizables)
 */

export async function initializeHybridEmployeesPage() {
    const bridge = window.UnifiedBridge;

    // Registrar como feature híbrida
    bridge.registerFeature('employees_page', 'hybrid', {
        legacy: ['DataTable', 'Filters', 'Pagination'],
        modern: ['ActionButtons', 'ContextMenu'],
        nextMigration: 'Move DataTable to modern',
        targetDate: '2026-06-30'
    });

    // Paso 1: Renderizar tabla legacy (como siempre)
    const employees = await fetchEmployees();
    renderLegacyEmployeeTable('employees-table', employees);

    // Paso 2: Renderizar botones modernos en contenedor legacy
    try {
        await bridge.renderInLegacy('ActionButtons', 'employees-actions-container', {
            actions: [
                {
                    id: 'edit',
                    label: '編集',
                    icon: 'pencil',
                    onClick: (rowData) => {
                        openEditModal(rowData);
                    }
                },
                {
                    id: 'delete',
                    label: '削除',
                    icon: 'trash',
                    onClick: (rowData) => {
                        confirmDelete(rowData);
                    }
                },
                {
                    id: 'view',
                    label: '詳細',
                    icon: 'eye',
                    onClick: (rowData) => {
                        showDetails(rowData);
                    }
                }
            ]
        });

        console.log('[Employees Page] Hybrid setup complete');
    } catch (error) {
        console.error('Failed to render modern action buttons:', error);
    }

    // Registrar page view
    bridge.trackPageView('employees', 'hybrid');
}

// HTML necesario:
// <div id="employees-table"></div>
// <div id="employees-actions-container"></div>

/**
 * ============================================================================
 * EJEMPLO 4: Migración Completa - Leave Requests
 * ============================================================================
 *
 * Estrategia: Mover componente completo de legacy a moderno
 * Fases:
 * 1. Crear componentes modernos
 * 2. Usar bridge durante transición
 * 3. Remover código legacy cuando esté listo
 */

// --- FASE 1: Feature aún está en legacy ---
export function registerLeaveRequestsPhase1() {
    const bridge = window.UnifiedBridge;

    bridge.registerFeature('leave_requests', 'legacy', {
        status: 'Legacy',
        nextPhase: 'Hybrid rendering',
        targetDate: '2026-04-01'
    });
}

// --- FASE 2: Empezar a usar bridge para nuevos features ---
export async function addLeaveRequestModern() {
    const bridge = window.UnifiedBridge;

    // Registrar nuevo componente moderno
    // bridge.registerModernComponent('LeaveRequestForm', LeaveRequestForm, {...});

    // Usar bridge para renderizar
    await bridge.renderInLegacy('LeaveRequestForm', 'leave-request-form-container', {
        onSubmit: async (formData) => {
            // Enviar al servidor
            const result = await createLeaveRequest(formData);

            // Sincronizar estado
            bridge.syncState('lastLeaveRequest', result);

            // Mostrar confirmación
            await showLegacyAlert('success', '申請しました');
        },
        onCancel: () => {
            bridge.syncState('showLeaveForm', false);
        }
    });

    // Registrar progreso
    bridge.registerFeature('leave_requests_form', 'modern', {
        parent: 'leave_requests',
        status: 'Partial migration'
    });
}

// --- FASE 3: Feature completamente moderno ---
export function registerLeaveRequestsPhase3() {
    const bridge = window.UnifiedBridge;

    bridge.registerFeature('leave_requests', 'modern', {
        status: 'Fully migrated',
        migratedDate: new Date().toISOString(),
        removeLegacyCode: true
    });
}

/**
 * ============================================================================
 * EJEMPLO 5: Monitoreo de Migración
 * ============================================================================
 *
 * Cómo rastrear el progreso de migración en tiempo real
 */

export function setupMigrationMonitoring() {
    const bridge = window.UnifiedBridge;

    // Crear dashboard simple de migración
    setInterval(() => {
        const stats = bridge.getMigrationStats();
        const progress = bridge.getMigrationProgress();

        console.log(`
┌─ MIGRATION PROGRESS ─────────────────┐
│ Overall: ${progress}%
│ Legacy:  ${stats.systems.legacy} features
│ Modern:  ${stats.systems.modern} features
│ Hybrid:  ${stats.systems.hybrid} features
│ Uptime:  ${Math.floor(stats.uptime.minutes)}m ${stats.uptime.seconds % 60}s
└──────────────────────────────────────┘
        `);
    }, 60000); // Cada minuto

    // Registrar cuando se renderiza un componente
    bridge.on('component-rendered', (data) => {
        console.log(`✓ Rendered: ${data.componentName} (${data.duration}ms)`);

        // Podría enviar al servidor para analytics
        // fetch('/api/analytics/bridge', {
        //     method: 'POST',
        //     body: JSON.stringify({ event: 'component_rendered', ...data })
        // });
    });

    // Registrar errores
    bridge.on('component-error', (data) => {
        console.error(`✗ Error: ${data.componentName} - ${data.error}`);

        // Alertar al equipo si hay muchos errores
        // if (errorCount > threshold) notifyTeam();
    });
}

/**
 * ============================================================================
 * EJEMPLO 6: Manejo de Errores y Fallbacks
 * ============================================================================
 *
 * Patrones para manejo robusto de errores
 */

export async function renderWithFallback(componentName, containerId, props) {
    const bridge = window.UnifiedBridge;

    try {
        // Intentar renderizar componente moderno
        await bridge.renderInLegacy(componentName, containerId, props);
        console.log(`Successfully rendered ${componentName}`);

    } catch (error) {
        console.error(`Failed to render ${componentName}:`, error);

        // Fallback 1: Si componente no existe, mostrar fallback simple
        if (error.message.includes('not registered')) {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = `
                    <div class="alert alert-warning">
                        <strong>⚠️ Componente no disponible</strong>
                        <p>El componente ${componentName} no está registrado.</p>
                        <p>Por favor, contacta al equipo de desarrollo.</p>
                    </div>
                `;
            }
            return;
        }

        // Fallback 2: Si contenedor no existe
        if (error.message.includes('not found')) {
            console.error(`Container #${containerId} not found in DOM`);
            return;
        }

        // Fallback 3: Error genérico
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <strong>❌ Error de renderización</strong>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }
}

/**
 * ============================================================================
 * EJEMPLO 7: Integration con Auth y Permisos
 * ============================================================================
 *
 * Síncronizar estado de autenticación entre sistemas
 */

export function setupAuthSync() {
    const bridge = window.UnifiedBridge;

    // Cuando usuario hace login
    window.App = window.App || {};
    const originalLogin = window.App.login || (() => {});

    window.App.login = async function(credentials) {
        // Ejecutar login original
        const result = await originalLogin.call(this, credentials);

        if (result.success) {
            // Sincronizar datos de usuario
            const userData = {
                id: result.user.id,
                name: result.user.name,
                role: result.user.role,
                permissions: result.user.permissions
            };

            bridge.syncState('currentUser', userData);
            bridge.syncState('isAuthenticated', true);
            bridge.syncState('userRole', result.user.role);

            console.log('Auth state synchronized');
        } else {
            bridge.syncState('isAuthenticated', false);
        }

        return result;
    };

    // Escuchar cambios en rol desde modern
    bridge.onStateChange('userRole', (newRole) => {
        console.log(`[Auth] User role changed to ${newRole}`);
        // Recargar permisos, actualizar UI, etc.
    });
}

/**
 * ============================================================================
 * EJEMPLO 8: Setup Completo en index.html
 * ============================================================================
 *
 * Orden correcto de inicialización
 */

// --- HTML ---
/*
<!DOCTYPE html>
<html>
<head>
    <title>YuKyu DATA</title>
    <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
    <div id="app"></div>

    <!-- 1. Inicializar bridge ANTES que app.js -->
    <script type="module">
        import { initBridge } from '/static/src/legacy-bridge/unified-bridge.js';
        import { setupAlertNotifications, setupYearFilterSync } from '/static/src/legacy-bridge/examples.js';

        window.bridge = initBridge();
        setupAlertNotifications();
        setupYearFilterSync();

        // Habilitar debug en desarrollo
        if (process.env.DEBUG === 'true') {
            window.bridge.enableDebugMode();
        }
    </script>

    <!-- 2. Cargar app.js legacy (después del bridge) -->
    <script src="/static/js/app.js"></script>

    <!-- 3. Inicializar componentes modernos -->
    <script type="module">
        import { initModernApp } from '/static/src/bootstrap.js';
        window.modernApp = await initModernApp(window.bridge);
    </script>
</body>
</html>
*/

/**
 * ============================================================================
 * EJEMPLO 9: Testing con Bridge
 * ============================================================================
 *
 * Cómo testear componentes con el bridge
 */

// tests/bridge.test.js
export const testExamples = {
    // Test: Registrar componente
    testRegisterComponent() {
        const bridge = window.UnifiedBridge;
        const MockComponent = () => '<div>Mock</div>';

        bridge.registerModernComponent('Mock', MockComponent, {
            category: 'test',
            props: []
        });

        if (bridge.componentRegistry.has('Mock')) {
            console.log('✓ Component registration works');
        } else {
            throw new Error('✗ Component registration failed');
        }
    },

    // Test: Sincronizar estado
    testStateSync() {
        const bridge = window.UnifiedBridge;

        bridge.syncState('testKey', 'testValue');
        const value = bridge.getState('testKey');

        if (value === 'testValue') {
            console.log('✓ State sync works');
        } else {
            throw new Error('✗ State sync failed');
        }
    },

    // Test: Renderizar en contenedor
    async testRenderInLegacy() {
        const bridge = window.UnifiedBridge;

        // Crear contenedor
        const container = document.createElement('div');
        container.id = 'test-container';
        document.body.appendChild(container);

        // Registrar mock component
        const TestComponent = () => {
            const div = document.createElement('div');
            div.textContent = 'Test rendered';
            return div;
        };

        bridge.registerModernComponent('TestComponent', TestComponent);

        // Renderizar
        await bridge.renderInLegacy('TestComponent', 'test-container', {});

        if (container.textContent.includes('Test rendered')) {
            console.log('✓ Render in legacy works');
        } else {
            throw new Error('✗ Render in legacy failed');
        }

        // Cleanup
        document.body.removeChild(container);
    }
};

/**
 * ============================================================================
 * EJEMPLO 10: Performance y Optimización
 * ============================================================================
 *
 * Consejos para optimizar el bridge
 */

export const performanceTips = {
    // Tip 1: Lazy load componentes
    lazyLoadComponents(bridge) {
        // No registrar todos los componentes al inicio
        // Registrar bajo demanda:

        const componentsToLoad = {
            'Modal': () => import('/static/src/components/Modal.js'),
            'Tooltip': () => import('/static/src/components/Tooltip.js'),
            'Dropdown': () => import('/static/src/components/Dropdown.js'),
        };

        return async (name) => {
            if (!bridge.componentRegistry.has(name) && componentsToLoad[name]) {
                const module = await componentsToLoad[name]();
                bridge.registerModernComponent(name, module.default);
            }
        };
    },

    // Tip 2: Batch rendering
    async batchRender(bridge, renders) {
        // En lugar de:
        // await bridge.renderInLegacy(...);
        // await bridge.renderInLegacy(...);
        // await bridge.renderInLegacy(...);

        // Hacer:
        return Promise.all(
            renders.map(([name, id, props]) =>
                bridge.renderInLegacy(name, id, props)
            )
        );
    },

    // Tip 3: Debounce state sync
    debounceSync(bridge, key, value, wait = 300) {
        let timeoutId;
        return () => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                bridge.syncState(key, value);
            }, wait);
        };
    }
};

/**
 * Export all examples
 */
export default {
    showLegacyAlert,
    setupYearFilterSync,
    initializeHybridEmployeesPage,
    setupMigrationMonitoring,
    renderWithFallback,
    setupAuthSync,
    setupAlertNotifications,
    setupModernEmployeesWithBridgeSync,
    registerLeaveRequestsPhase1,
    addLeaveRequestModern,
    registerLeaveRequestsPhase3,
    testExamples,
    performanceTips
};
