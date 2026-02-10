# Legacy Bridge: Sistema de Migración Strangler Fig

Puente completo entre el frontend legacy (app.js - 3,701 líneas) y el sistema moderno (static/src/) usando el patrón **Strangler Fig** para migración gradual.

## 📁 Archivos del Directorio

| Archivo | Propósito |
|---------|-----------|
| **unified-bridge.js** | Core del bridge (9 KB). API principal: renderización, estado, tracking |
| **unified-state-bridge.js** | Sincronización de estado App.state ↔ UnifiedState |
| **MIGRATION_GUIDE.md** | Guía completa con patrones y ejemplos |
| **examples.js** | 10 ejemplos prácticos de integración |
| **README.md** | Este archivo |

## 🚀 Quick Start

### 1. Inicializar Bridge

```html
<!-- En templates/index.html, ANTES que app.js -->
<script type="module">
    import { initBridge } from '/static/src/legacy-bridge/unified-bridge.js';
    window.bridge = initBridge();
</script>

<script src="/static/js/app.js"></script>
```

### 2. Registrar Componente Moderno

```javascript
import { getUnifiedBridge } from '/static/src/legacy-bridge/unified-bridge.js';
import { Alert } from '/static/src/components/index.js';

const bridge = getUnifiedBridge();
bridge.registerModernComponent('Alert', Alert, {
    category: 'core',
    props: ['type', 'message'],
    description: 'Alert notification'
});
```

### 3. Usar en Legacy Code

```javascript
// En app.js (legacy)
async function showSuccessAlert() {
    await window.bridge.renderInLegacy('Alert', 'alert-container', {
        type: 'success',
        message: 'Guardado correctamente'
    });
}
```

### 4. Sincronizar Estado

```javascript
// Legacy: cambiar año
window.bridge.syncState('selectedYear', 2025);

// Modern: escuchar cambios
const unsub = bridge.onStateChange('selectedYear', (newYear) => {
    console.log('Year:', newYear);
});
```

## 📊 Arquitectura

```
┌─────────────────────────────────────────┐
│         Legacy (app.js)                 │
├─────────────────────────────────────────┤
│                                         │
│  • Renderización de tabla               │
│  • Lógica de navegación                 │
│  • State (App.state)                    │
│                                         │
└────────────────┬────────────────────────┘
                 │
         ┌───────▼────────┐
         │   Bridge API   │
         ├────────────────┤
         │ • Registry     │
         │ • Rendering    │
         │ • StateSync    │
         │ • Tracking     │
         └───────┬────────┘
                 │
┌────────────────▼────────────────────────┐
│         Modern (static/src/)            │
├─────────────────────────────────────────┤
│                                         │
│  • Componentes funcionales              │
│  • State management avanzado            │
│  • Accesibilidad WCAG AA                │
│                                         │
└─────────────────────────────────────────┘
```

## 🔄 Patrón Strangler Fig

Migración en 3 fases:

```
FASE 1: Legacy
┌──────────────────────┐
│  100% app.js         │
└──────────────────────┘

FASE 2: Bridge + Hybrid
┌──────────────────────┐
│  Modern Components   │ ◄──────┐
│       ▼              │        │
│   [Bridge]           │  Nuevas
│       ▼              │  Features
│  app.js (Legacy)     │        │
└──────────────────────┘ ◄──────┘

FASE 3: Modern
┌──────────────────────┐
│  100% Modern App     │
└──────────────────────┘
```

## 🎯 API Principal

### Componentes

```javascript
// Registrar componente moderno
bridge.registerModernComponent(name, Component, metadata)

// Obtener lista de componentes registrados
const components = bridge.getRegisteredComponents()
```

### Renderización

```javascript
// Renderizar en contenedor legacy
await bridge.renderInLegacy(componentName, containerId, props, options)

// Opciones:
{
    async: true,          // Procesar en queue
    clearContainer: true  // Limpiar antes de renderizar
}
```

### Estado

```javascript
// Sincronizar valor
bridge.syncState(key, value)

// Obtener valor
const value = bridge.getState(key)

// Escuchar cambios (retorna unsubscribe)
const unsub = bridge.onStateChange(key, (newVal, oldVal) => {
    console.log(`${key}: ${oldVal} → ${newVal}`);
})

// Snapshot de estado actual
const snapshot = bridge.getStateSnapshot()
```

### Migración

```javascript
// Registrar feature como legacy/modern/hybrid
bridge.registerFeature(name, system, details)

// Rastrear page view
bridge.trackPageView(pageName, system)

// Obtener estadísticas
const stats = bridge.getMigrationStats()

// Progreso 0-100
const progress = bridge.getMigrationProgress()

// Reporte formateado
console.log(bridge.getMigrationReport())

// Exportar datos
const data = bridge.exportMigrationData()
```

### Eventos

```javascript
// Escuchar eventos del bridge
bridge.on('component-rendered', (data) => {
    console.log(`${data.componentName} rendered in ${data.duration}ms`);
})

bridge.on('component-error', (data) => {
    console.error(`${data.componentName} error: ${data.error}`);
})

// Remover listener
bridge.off(eventType, listener)
```

### Debug

```javascript
// Habilitar logging detallado
bridge.enableDebugMode()

// Obtener info de debug
const info = bridge.getDebugInfo()

// Imprimir en consola
bridge.printDebugInfo()
```

## 📝 Ejemplos

### Ejemplo 1: Alert Moderno en Legacy

```javascript
// Legacy code (app.js)
async function onSaveComplete() {
    await window.bridge.renderInLegacy('Alert', 'alert-container', {
        type: 'success',
        message: 'Guardado',
        onClose: () => console.log('Closed')
    });
}

// HTML:
// <div id="alert-container"></div>
```

### Ejemplo 2: Tabla Hybrid (Legacy + Botones Modernos)

```javascript
async function initializeEmployees() {
    const bridge = window.bridge;

    // Registrar como hybrid
    bridge.registerFeature('employees', 'hybrid', {
        legacy: ['Table', 'Pagination'],
        modern: ['ActionButtons']
    });

    // Tabla legacy (como siempre)
    renderLegacyTable('#employees-table', data);

    // Botones modernos
    await bridge.renderInLegacy('ActionButtons', 'actions-container', {
        actions: [
            { label: 'Edit', onClick: editEmployee },
            { label: 'Delete', onClick: deleteEmployee }
        ]
    });
}
```

### Ejemplo 3: Sincronizar Año

```javascript
// Legacy: cuando cambia año
document.getElementById('year-select').addEventListener('change', (e) => {
    const year = parseInt(e.target.value);
    window.bridge.syncState('selectedYear', year);
});

// Modern: escuchar cambio
bridge.onStateChange('selectedYear', (newYear) => {
    console.log('Reload data for year:', newYear);
    loadData(newYear);
});
```

Ver **examples.js** para 10 ejemplos completos.

## 📚 Documentación Completa

Ver **MIGRATION_GUIDE.md** para:
- Patrones de migración detallados
- Mejores prácticas
- Troubleshooting
- Checklist de implementación
- Hoja de ruta de migración

## ✅ Checklist de Implementación

Para migrar una feature:

- [ ] Crear componente moderno en `/static/src/components/`
- [ ] Registrar con `bridge.registerModernComponent()`
- [ ] Registrar feature con `bridge.registerFeature()`
- [ ] Reemplazar calls legacy con `bridge.renderInLegacy()`
- [ ] Sincronizar estado si es necesario
- [ ] Testear en ambos modos (dark/light)
- [ ] Verificar accesibilidad (WCAG AA)
- [ ] Medir performance
- [ ] Documentar cambios

## 🔍 Monitoreo

```javascript
// Progreso de migración
const progress = bridge.getMigrationProgress();
console.log(`${progress}% features migrated`);

// Reporte completo
console.log(bridge.getMigrationReport());

// Output:
// ╔════════════════════════════════════════════════════╗
// ║         MIGRATION STATUS REPORT                    ║
// ╚════════════════════════════════════════════════════╝
// 📊 Overall Progress: 35%
// 🏢 Features by System:
//   • Legacy:  8
//   • Modern:  4
//   • Hybrid:  2
```

## 🚨 Troubleshooting

### Component not registered
```
Error: Component "Alert" not registered
```
**Solución:** Registrar primero con `bridge.registerModernComponent()`

### Container not found
```
Error: Container "#alert-container" not found
```
**Solución:** Asegurar que el HTML existe: `<div id="alert-container"></div>`

### State no sincroniza
```javascript
// ❌ Incorrecto
App.state.year = 2025;

// ✅ Correcto
bridge.syncState('year', 2025);
```

### Memory leaks
```javascript
// Siempre unsubscribirse
const unsub = bridge.onStateChange('key', callback);
// Después: unsub();
```

## 📊 Estadísticas de Uso

```javascript
const stats = bridge.getMigrationStats();

console.log(stats);
// {
//   features: {...},
//   componentUsage: {...},
//   pageViews: [...],
//   systems: {
//     legacy: 8,
//     modern: 4,
//     hybrid: 2
//   },
//   uptime: {
//     milliseconds: ...,
//     seconds: ...,
//     minutes: ...
//   }
// }
```

## 🧪 Testing

```javascript
// Test: Registrar componente
const bridge = window.UnifiedBridge;
bridge.registerModernComponent('Test', () => '<div>Test</div>');
console.assert(bridge.componentRegistry.has('Test'), 'Component registered');

// Test: Sincronizar estado
bridge.syncState('key', 'value');
console.assert(bridge.getState('key') === 'value', 'State synced');

// Test: Renderizar
const container = document.createElement('div');
container.id = 'test';
document.body.appendChild(container);
await bridge.renderInLegacy('Test', 'test', {});
console.assert(container.innerHTML.includes('Test'), 'Component rendered');
```

## 🎨 Design System Integration

El bridge respeta el design system YuKyu v5.4:

- **Paleta:** Amber (#f59e0b), Cyan (#1d4ed8), Teal (#14b8a6)
- **Tipografía:** Noto Sans JP + system fonts
- **Espaciado:** Sistema 4px
- **Accesibilidad:** WCAG AA compliance
- **Temas:** Dark/Light mode support

Ver `/static/css/main.css` y `/static/css/design-system/` para estilos.

## 🔐 Seguridad

- **XSS Prevention:** Bridge sanitiza props automáticamente
- **State Isolation:** Legacy y modern tienen state separado pero sincronizado
- **Error Boundaries:** Errores en componentes no afectan la app
- **Type Safety:** Validación de componentes registrados

## 📈 Hoja de Ruta

**Q1 2026:** Dashboard + Employees (Hybrid)
**Q2 2026:** Leave Requests (Modern)
**Q3 2026:** Analytics + Reports (Modern)
**Q4 2026:** Cleanup + Optimization

## 🤝 Contributing

Para agregar nuevos features al bridge:

1. Crear test en `tests/legacy-bridge.test.js`
2. Implementar feature en `unified-bridge.js`
3. Agregar ejemplo en `examples.js`
4. Documentar en `MIGRATION_GUIDE.md`
5. Actualizar este README

## 📞 Soporte

Para preguntas o issues:
1. Ver `MIGRATION_GUIDE.md` sección Troubleshooting
2. Revisar ejemplos en `examples.js`
3. Habilitar debug mode: `bridge.enableDebugMode()`
4. Contactar al equipo de desarrollo

---

**Última actualización:** 2026-01-22
**Patrón:** Strangler Fig
**Objetivo:** Migración gradual legacy → moderno sin downtime
