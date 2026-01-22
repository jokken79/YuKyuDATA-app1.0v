# Unified Bridge: Guía de Migración Strangler Fig

## Visión General

El **Unified Bridge** implementa el patrón **Strangler Fig** para permitir una migración gradual del frontend legacy (app.js - 3,701 líneas) al sistema moderno (static/src/).

### ¿Por qué Strangler Fig?

```
Fase 1 (Actual):  100% Legacy
                  [Legacy App]

Fase 2 (Ahora):   Hybrid con Bridge
                  [Modern Components]
                       ↓
                  [Bridge]
                       ↓
                  [Legacy App]

Fase 3 (Futuro):  100% Modern
                  [Modern App]
```

El bridge actúa como intermediario, permitiendo que componentes modernos coexistan y gradualmente reemplacen el código legacy.

---

## Inicialización

### Paso 1: Importar en index.html

```html
<!-- En templates/index.html, antes de app.js -->
<script type="module">
    import { initBridge } from '/static/src/legacy-bridge/unified-bridge.js';

    // Inicializar bridge
    window.bridge = initBridge();

    // Habilitar debug si necesario
    // window.bridge.enableDebugMode();

    console.log('Bridge initialized:', window.bridge);
</script>

<!-- Después, app.js se carga normalmente -->
<script src="/static/js/app.js"></script>
```

### Paso 2: Registrar Componentes Modernos

```javascript
// En static/src/bootstrap.js o setup:
import { getUnifiedBridge } from '/static/src/legacy-bridge/unified-bridge.js';
import { Alert, Modal, Button, Card } from '/static/src/components/index.js';

const bridge = getUnifiedBridge();

// Registrar componentes
bridge.registerModernComponent('Alert', Alert, {
    category: 'core',
    props: ['type', 'message', 'onClose'],
    description: 'Notificación de alerta'
});

bridge.registerModernComponent('Modal', Modal, {
    category: 'layout',
    props: ['title', 'isOpen', 'onClose', 'children'],
    description: 'Modal de diálogo'
});
```

---

## Patrones de Uso

### Patrón 1: Renderizar Componente Moderno en Contenedor Legacy

**Escenario:** Legacy app.js necesita mostrar un Alert moderno.

```javascript
// En legacy code (app.js):
async function showSuccessAlert() {
    try {
        // 1. Asegurar que bridge esté disponible
        const bridge = window.UnifiedBridge;

        // 2. Renderizar componente moderno en contenedor legacy
        await bridge.renderInLegacy('Alert', 'alert-container', {
            type: 'success',
            message: 'Empleado guardado correctamente',
            onClose: () => {
                // Callback cuando usuario cierre alert
                console.log('Alert cerrado');
            }
        });
    } catch (error) {
        console.error('Error rendering alert:', error);
    }
}

// En HTML legacy:
// <div id="alert-container"></div>
```

### Patrón 2: Sincronizar Estado entre Sistemas

**Escenario:** Año fiscal seleccionado en legacy debe estar disponible en moderno.

```javascript
// Legacy code (app.js) - cuando cambia el año:
function onYearChange(newYear) {
    // Guardar en App.state (legacy)
    App.state.selectedYear = newYear;

    // Sincronizar con moderno
    window.UnifiedBridge.syncState('selectedYear', newYear);
}

// Modern code - acceder al estado sincronizado:
import { getUnifiedBridge } from '/static/src/legacy-bridge/unified-bridge.js';

const bridge = getUnifiedBridge();

// Obtener valor actual
const year = bridge.getState('selectedYear');
console.log('Current year from bridge:', year);

// Escuchar cambios
const unsubscribe = bridge.onStateChange('selectedYear', (newYear, oldYear) => {
    console.log(`Year changed: ${oldYear} → ${newYear}`);
    // Recargar datos si es necesario
    loadEmployeesForYear(newYear);
});

// Más tarde, desuscribirse:
unsubscribe();
```

### Patrón 3: Feature Hybrid (Ambos Sistemas)

**Escenario:** Panel de empleados usa tabla legacy pero botones de acción modernos.

```javascript
// Registrar como hybrid:
window.bridge.registerFeature('employees_list', 'hybrid', {
    note: 'Tabla en legacy, botones de acción en moderno',
    migratedComponents: ['ActionButtons'],
    remainingLegacy: ['DataTable']
});

// En el HTML:
// <div id="employees-table"></div>
// <div id="action-buttons-container"></div>

// Renderizar componentes modernos en contenedor legacy:
async function initializeEmployeesPage() {
    const bridge = window.bridge;

    // Tabla (legacy) - renderizada normalmente
    renderLegacyTable('employees-table', employeeData);

    // Botones (moderno)
    await bridge.renderInLegacy('ActionButtons', 'action-buttons-container', {
        actions: [
            { label: 'Editar', icon: 'edit', onClick: editEmployee },
            { label: 'Eliminar', icon: 'trash', onClick: deleteEmployee },
        ]
    });
}
```

### Patrón 4: Migraciones Graduales

**Escenario:** Migrar Leave Requests de legacy a moderno en fases.

```javascript
// Fase 1: Feature registrada como legacy
bridge.registerFeature('leave_requests', 'legacy', {
    status: 'En uso',
    targetDate: '2026-06-30'
});

// Fase 2: Empezar migración - usar bridge para nuevas features
bridge.registerFeature('leave_requests_approval', 'modern', {
    status: 'En migración',
    parent: 'leave_requests'
});

// Fase 3: Ya completamente moderno
bridge.registerFeature('leave_requests', 'modern', {
    status: 'Migrado',
    migratedDate: new Date().toISOString()
});
```

### Patrón 5: Event Listeners para Bridge

```javascript
const bridge = window.bridge;

// Escuchar cuando se renderiza un componente
bridge.on('component-rendered', (data) => {
    console.log(`Component ${data.componentName} rendered in ${data.duration}ms`);
    // Trigger post-render logic
});

// Escuchar errores de renderización
bridge.on('component-error', (data) => {
    console.error(`Failed to render ${data.componentName}: ${data.error}`);
    // Fallback o mostrar error
});

// Escuchar cambios de estado
bridge.onStateChange('currentPage', (newPage, oldPage) => {
    console.log(`Navigated from ${oldPage} to ${newPage}`);
});
```

---

## Ejemplos Completos

### Ejemplo 1: Convertir Modal Legacy a Moderno

**Antes (Legacy):**
```javascript
function showApprovalModal(leaveRequest) {
    // Renderizar HTML manualmente
    const html = `
        <div class="modal active" id="approval-modal">
            <div class="modal-content">
                <h2>${leaveRequest.employeeName}</h2>
                <p>${leaveRequest.reason}</p>
                <button onclick="approveLeave()">Aprobar</button>
                <button onclick="rejectLeave()">Rechazar</button>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
}
```

**Después (Con Bridge):**
```javascript
import { getUnifiedBridge } from '/static/src/legacy-bridge/unified-bridge.js';
import { LeaveApprovalModal } from '/static/src/components/LeaveApprovalModal.js';

async function showApprovalModal(leaveRequest) {
    const bridge = getUnifiedBridge();

    // Registrar componente (una sola vez)
    if (!bridge.componentRegistry.has('LeaveApprovalModal')) {
        bridge.registerModernComponent('LeaveApprovalModal', LeaveApprovalModal, {
            category: 'form',
            props: ['leaveRequest', 'onApprove', 'onReject'],
            description: 'Modal para aprobar/rechazar solicitudes de vacaciones'
        });
    }

    // Renderizar
    await bridge.renderInLegacy('LeaveApprovalModal', 'modal-container', {
        leaveRequest,
        onApprove: async () => {
            await approveLeave(leaveRequest.id);
            bridge.syncState('refreshLeaveRequests', true);
        },
        onReject: async () => {
            await rejectLeave(leaveRequest.id);
            bridge.syncState('refreshLeaveRequests', true);
        }
    });
}

// En HTML:
// <div id="modal-container"></div>
```

### Ejemplo 2: Dashboard Híbrido

```javascript
// Registrar estructura del dashboard
window.bridge.registerFeature('dashboard', 'hybrid', {
    legacy: ['LeftSidebar', 'TopNav', 'EmployeeTable'],
    modern: ['StatCards', 'ChartWidget', 'NotificationCenter'],
    note: 'Migración gradual: charts primero, después tablas'
});

async function initializeDashboard() {
    const bridge = window.bridge;

    // Legacy: Renderizar tabla (app.js)
    renderEmployeeTable('#employees-table', employeeData);

    // Modern: Renderizar cards de estadísticas
    await bridge.renderInLegacy('StatCards', 'stat-cards-container', {
        stats: [
            { label: 'Total Employees', value: 245 },
            { label: 'On Leave Today', value: 12 },
            { label: 'Expiring Soon', value: 8 }
        ]
    });

    // Modern: Renderizar widget de notificaciones
    await bridge.renderInLegacy('NotificationCenter', 'notifications-container', {
        onClose: () => console.log('Notifications closed')
    });

    // Registrar page view
    bridge.trackPageView('dashboard', 'hybrid');
}
```

---

## Monitoreo y Estadísticas

### Obtener Progreso de Migración

```javascript
const bridge = window.bridge;

// Porcentaje de features migradas (0-100)
const progress = bridge.getMigrationProgress();
console.log(`Migration progress: ${progress}%`);

// Estadísticas detalladas
const stats = bridge.getMigrationStats();
console.log('Features by system:', stats.systems);
console.log('Component usage:', stats.componentUsage);
console.log('Page views:', stats.pageViews);

// Generar reporte
console.log(bridge.getMigrationReport());

/* Output:
╔════════════════════════════════════════════════════╗
║         MIGRATION STATUS REPORT                    ║
╚════════════════════════════════════════════════════╝

📊 Overall Progress: 35%

🏢 Features by System:
  • Legacy:  8
  • Modern:  4
  • Hybrid:  2

📱 Page Views: 127

⏱️  Uptime: 2h 45m 32s
*/
```

### Exportar Datos de Migración

```javascript
// Para análisis o reportes
const migrationData = bridge.exportMigrationData();

// Enviar al servidor
fetch('/api/migration-stats', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(migrationData)
});
```

### Debug Mode

```javascript
const bridge = window.bridge;

// Habilitar logging detallado
bridge.enableDebugMode();

// Obtener información de debug
const debugInfo = bridge.getDebugInfo();
console.log(debugInfo);

// Imprimir en consola formateado
bridge.printDebugInfo();
```

---

## Checklist de Implementación

### Para Migrar una Feature

- [ ] Entender la feature actual en legacy (app.js)
- [ ] Crear componente moderno en `/static/src/components/`
- [ ] Exportar desde `index.js`
- [ ] Registrar en bridge: `bridge.registerModernComponent(...)`
- [ ] Registrar feature: `bridge.registerFeature('name', 'modern')`
- [ ] Reemplazar calls en legacy con `bridge.renderInLegacy(...)`
- [ ] Sincronizar estado si es necesario
- [ ] Testear en ambos sistemas (dark/light mode)
- [ ] Verificar accesibilidad (WCAG AA)
- [ ] Medir performance
- [ ] Actualizar documentación

### Para Feature Hybrid

- [ ] Usar `registerFeature(..., 'hybrid')`
- [ ] Documentar qué parte es legacy vs modern
- [ ] Testear interacción entre sistemas
- [ ] Planificar siguiente fase de migración
- [ ] Documentar pasos para completar migración

---

## Mejores Prácticas

### ✅ DO (Hacer)

```javascript
// Sincronizar antes de renderizar
bridge.syncState('currentData', data);
await bridge.renderInLegacy('Component', 'container', { data });

// Registrar features apropiadamente
bridge.registerFeature('feature_name', 'modern', {
    description: 'Descripción clara'
});

// Manejar errores
try {
    await bridge.renderInLegacy('Component', 'id', props);
} catch (error) {
    console.error('Render failed:', error);
    // Fallback o mostrar error al usuario
}

// Unsubscribirse de listeners
const unsub = bridge.onStateChange('key', callback);
// Luego:
unsub();
```

### ❌ DON'T (No hacer)

```javascript
// No renderizar sin registrar
await bridge.renderInLegacy('UnregisteredComponent', 'id', {});

// No mezclar estado sin sincronizar
App.state.data = newData;
// Sin: bridge.syncState('data', newData);

// No dejar listeners "flotando"
for (let i = 0; i < 100; i++) {
    bridge.onStateChange('key', callback); // Memory leak!
}

// No ignorar errores
bridge.renderInLegacy('Component', 'id', props)
    .catch(err => console.error(err)); // OK
    // Pero mejor tener fallback UI
```

---

## Troubleshooting

### Error: Component not registered

```
Error: Component "Alert" not registered
```

**Solución:** Registrar el componente primero:
```javascript
bridge.registerModernComponent('Alert', AlertComponent, {...});
```

### Error: Container not found

```
Error: Container "#alert-container" not found in DOM
```

**Solución:** Asegurar que el HTML existe:
```html
<div id="alert-container"></div>
```

### State no se sincroniza

```javascript
// ❌ Incorrecto
App.state.year = 2025; // Legacy no notifica

// ✅ Correcto
bridge.syncState('year', 2025); // Sincroniza ambos
```

### Memory leaks

```javascript
// ❌ Incorrecto
bridge.on('component-rendered', callback); // Nunca se quita

// ✅ Correcto
const cleanup = () => bridge.off('component-rendered', callback);
// Llamar cleanup cuando el componente se destruya
```

---

## Hoja de Ruta de Migración

**Q1 2026:** Features Críticas (Dashboard, Employees)
- [ ] StatCards moderno
- [ ] EmployeeTable híbrido (legacy + botones modernos)

**Q2 2026:** Workflows Complejos
- [ ] LeaveRequests completamente moderno
- [ ] ApprovalModals modernos

**Q3 2026:** Analytics y Reportes
- [ ] ChartWidget moderno
- [ ] ReportsPage moderno

**Q4 2026:** Cleanup
- [ ] Remover código legacy innecesario
- [ ] Optimizar bundle size
- [ ] Documentación final

---

## API Reference

### Bridge Methods

```javascript
// Componentes
bridge.registerModernComponent(name, Component, metadata)
bridge.getRegisteredComponents()

// Renderización
await bridge.renderInLegacy(name, containerId, props, options)

// Estado
bridge.syncState(key, value)
bridge.getState(key)
bridge.onStateChange(key, callback) // Returns unsubscribe function
bridge.getStateSnapshot()

// Migración
bridge.registerFeature(name, system, details)
bridge.trackPageView(page, system)
bridge.getMigrationStats()
bridge.getMigrationProgress() // 0-100
bridge.getMigrationReport() // Formatted string
bridge.exportMigrationData()

// Eventos
bridge.on(eventType, listener)
bridge.off(eventType, listener)

// Debug
bridge.enableDebugMode()
bridge.getDebugInfo()
bridge.printDebugInfo()
```

---

## Referencias

- **Pattern:** Strangler Fig Pattern
- **Architecture:** Incremental migration
- **State Management:** Dual-system synchronization
- **Testing:** Jest + Playwright
