---
description: "Dashboard y UI de YuKyuDATA - usar cuando se modifique el frontend, estilos CSS, gráficos o interactividad JavaScript"
---

# Skill: Frontend Dashboard YuKyuDATA

## Arquitectura del Frontend

**Tipo**: Single Page Application (SPA) vanilla
**Archivos principales**:
- `templates/index.html` - Estructura HTML
- `static/css/main.css` - Estilos (1,500+ líneas)
- `static/js/app.js` - Lógica (2,900+ líneas)

## Estructura del Estado Global

```javascript
const App = {
    state: {
        employees: [],
        genzai: [],
        ukeoi: [],
        selectedYear: null,
        availableYears: [],
        theme: 'light',
        currentView: 'dashboard'
    },
    config: {
        apiBase: '/api',
        chartColors: ['#38bdf8', '#f472b6', '#a3e635']
    },
    utils: { escapeHtml, escapeAttr, safeNumber, isValidYear },
    theme: { toggle, apply },
    data: { fetch, sync },
    ui: { render, showToast, showModal },
    charts: { usage, distribution, monthly },
    init()
}
```

## Vistas Disponibles

| Vista | Selector | Descripción |
|-------|----------|-------------|
| Dashboard | `#view-dashboard` | KPIs y gráficos principales |
| Employees | `#view-employees` | Lista con búsqueda |
| Factories | `#view-factories` | Estadísticas por派遣先 |
| Requests | `#view-requests` | Solicitudes de vacaciones |
| Calendar | `#view-calendar` | Vista de fechas |
| Compliance | `#view-compliance` | Verificación 5日取得義務 |
| Analytics | `#view-analytics` | Gráficos avanzados |
| Reports | `#view-reports` | Reportes mensuales |

## Sistema de Temas

```css
:root {
    /* Light theme */
    --bg-primary: #f8fafc;
    --text-primary: #0f172a;
    --accent: #38bdf8;
}

[data-theme="dark"] {
    --bg-primary: #0f172a;
    --text-primary: #f8fafc;
    --accent: #38bdf8;
}
```

## Librerías Externas

- **ApexCharts**: Gráficos interactivos
- **GSAP**: Animaciones suaves
- **Animate.css**: Transiciones CSS

## Seguridad XSS

```javascript
// SIEMPRE usar estas funciones para datos dinámicos
App.utils.escapeHtml(userInput)    // Para contenido HTML
App.utils.escapeAttr(userInput)    // Para atributos
App.utils.safeNumber(value)        // Para números
```

## Patrones de UI

### Toast Notifications
```javascript
App.ui.showToast('Mensaje', 'success');  // success, error, warning, info
```

### Modal
```javascript
App.ui.showModal({
    title: 'Detalle Empleado',
    content: htmlContent,
    onClose: () => {}
});
```

### Navegación entre vistas
```javascript
App.ui.showView('employees');  // Cambia vista activa
```

## Endpoints del Frontend

```javascript
// Datos
GET  /api/employees?year={year}
GET  /api/genzai
GET  /api/ukeoi

// Sincronización
POST /api/sync
POST /api/sync-genzai
POST /api/sync-ukeoi

// Solicitudes
GET  /api/leave-requests
POST /api/leave-requests
PUT  /api/leave-requests/{id}/approve
```

## PWA Support

```html
<link rel="manifest" href="/static/manifest.json">
<meta name="apple-mobile-web-app-capable" content="yes">
```

## Responsive Breakpoints

```css
/* Mobile first */
@media (min-width: 768px) { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1280px) { /* Large */ }
```
