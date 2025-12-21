# Sistema de Diseño YuKyuDATA 2025

## Descripción General

Este directorio contiene el sistema de diseño consolidado y unificado para YuKyuDATA. Los archivos están organizados para facilitar el mantenimiento y la escalabilidad.

## Estructura de Archivos

### 📦 Archivos Principales (Consolidación 2025)

#### `tokens.css`
**Variables CSS unificadas** - El fundamento del sistema de diseño.

Contiene:
- **Colores**: Paleta completa (primarios, secundarios, estados, neutrales)
- **Tipografía**: Familias, tamaños, pesos, alturas de línea
- **Espaciado**: Sistema de 8px
- **Bordes y Radios**: Valores consistentes
- **Sombras**: Glassmorphism, depth, glows
- **Efectos**: Blur, transiciones, animaciones
- **Layout**: Dimensiones principales
- **Z-Index**: Capas organizadas
- **Tokens de componentes**: Valores específicos para buttons, inputs, cards, etc.

**Uso**:
```css
/* Usar variables en cualquier componente */
.mi-componente {
  color: var(--color-primary);
  padding: var(--space-4);
  border-radius: var(--radius-md);
}
```

#### `themes.css`
**Configuración Dark/Light Mode** - Sistema de temas dinámico.

Contiene:
- **Dark Theme**: Efectos de resplandor ambiental, pure black backgrounds
- **Light Theme**: Override de variables para modo claro
- **Component Theming**: Estilos específicos para cada tema
  - Sidebar
  - Stats & Cards
  - Forms (inputs, selects)
  - Buttons
  - Tables
  - Toasts & Modals
  - Tabs
  - Theme Toggle
  - Skeletons
  - Flatpickr

**Uso**:
Los temas se aplican automáticamente basado en `data-theme` attribute:
```html
<html data-theme="dark">  <!-- o "light" -->
```

#### `components.css`
**Componentes reutilizables** - Building blocks de la UI.

Contiene:
- **Buttons**: `.btn`, `.btn-primary`, `.btn-glass`, `.btn-export`
- **Inputs**: `.input-glass` con estados (valid, invalid, focus, hover)
- **Select**: Selectores mejorados con soporte completo dark/light
- **Badges**: `.badge-success`, `.badge-warning`, `.badge-danger`, `.badge-info`, `.badge-critical`
- **Cards**: `.glass-panel` con shimmer effect
- **Tabs**: `.tab-container`, `.tab-btn`
- **Form Groups**: `.form-group`, `.form-section`
- **Utilities**: Clases de ayuda (flex, text-gradient, sr-only)

**Uso**:
```html
<!-- Button example -->
<button class="btn btn-primary">Guardar</button>

<!-- Input example -->
<input type="text" class="input-glass" placeholder="Nombre...">

<!-- Select example -->
<select class="input-glass">
  <option>Opción 1</option>
</select>
```

### 📦 Archivos Adicionales

#### `accessibility.css`
Mejoras de accesibilidad (creado previamente)

#### `utilities.css`
Clases de utilidad (creado previamente)

## Integración Completa

### 1. Flatpickr Dinámico ✅

**Cambios en `/templates/index.html`**:
- Línea 1616-1619: Agregada función `getCurrentTheme()`
- Línea 1630: Cambiado `theme: 'dark'` → `theme: getCurrentTheme()`
- Ahora Flatpickr se inicializa con el tema correcto basado en `data-theme`

**Cambios en `/static/css/design-system/themes.css`**:
- Sección completa de estilos Flatpickr para dark/light modes

### 2. App.theme.apply() Mejorado ✅

**Cambios en `/static/js/app.js`** (líneas 272-313):

Nueva funcionalidad:
```javascript
apply() {
    // ... código existente ...

    // ACTUALIZAR FLATPICKR DINÁMICAMENTE
    const flatpickrInstances = [
        window.startDatePicker,
        window.endDatePicker,
        window.reportStartPicker,
        window.reportEndPicker
    ];

    flatpickrInstances.forEach(picker => {
        if (picker && picker.config) {
            picker.set('theme', this.current);
            if (picker.isOpen) {
                picker.close();
                setTimeout(() => picker.open(), 50);
            }
        }
    });

    // ACTUALIZAR SELECTORES
    const selects = document.querySelectorAll('select.input-glass');
    selects.forEach(select => {
        select.offsetHeight; // Trigger reflow
    });
}
```

### 3. Selectores Consolidados ✅

**Cambios en `/static/css/main.css`** (líneas 554-631):

Agregada sección completa:
- Dark mode select: Background, hover, focus states
- Dark mode options: Estilos para las opciones del dropdown
- Light mode select: Todos los estados
- Light mode options: Estilos optimizados

**Sin dependencia de !important** - Todos los estilos usan especificidad correcta.

## Cómo Usar el Sistema

### 1. Importar en HTML

```html
<!-- En el <head> de tu HTML -->
<link rel="stylesheet" href="/static/css/design-system/tokens.css">
<link rel="stylesheet" href="/static/css/design-system/themes.css">
<link rel="stylesheet" href="/static/css/design-system/components.css">
```

### 2. Crear Componente Nuevo

```css
/* Usar tokens para consistencia */
.mi-nuevo-componente {
  /* Colores */
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  border: var(--border-glass);

  /* Espaciado */
  padding: var(--space-4);
  margin-bottom: var(--space-6);

  /* Bordes */
  border-radius: var(--radius-md);

  /* Sombras */
  box-shadow: var(--shadow-glass);

  /* Transiciones */
  transition: all var(--transition-smooth);
}

/* Soporte para ambos temas */
[data-theme="light"] .mi-nuevo-componente {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: var(--shadow-md);
}
```

### 3. Cambiar Tema Programáticamente

```javascript
// El tema se maneja automáticamente con App.theme.toggle()
// Esto actualizará:
// - data-theme attribute
// - Todas las instancias de Flatpickr
// - Todos los selectores
// - Todos los componentes CSS
```

## Mejores Prácticas

### ✅ DO (Hacer)

1. **Usar variables CSS siempre**
   ```css
   padding: var(--space-4);  /* ✅ Correcto */
   ```

2. **Definir estilos para ambos temas**
   ```css
   .componente { /* dark theme default */ }
   [data-theme="light"] .componente { /* light override */ }
   ```

3. **Usar tokens semánticos**
   ```css
   color: var(--color-text-primary);  /* ✅ Semántico */
   ```

4. **Mantener especificidad baja**
   ```css
   .btn { }  /* ✅ Simple */
   ```

### ❌ DON'T (Evitar)

1. **Valores hardcodeados**
   ```css
   padding: 16px;  /* ❌ Usar var(--space-4) */
   ```

2. **!important innecesario**
   ```css
   color: red !important;  /* ❌ Usar especificidad correcta */
   ```

3. **Colores directos**
   ```css
   color: #06b6d4;  /* ❌ Usar var(--color-primary) */
   ```

4. **Mezclar unidades**
   ```css
   padding: 1rem 16px;  /* ❌ Inconsistente */
   ```

## Extracción de Arari-Glow

El sistema consolidado extrae los mejores elementos de `arari-glow.css`:

### Efectos Incluidos

✅ **Ambient background glows** (solo dark mode)
✅ **Gradient text** con var(--text-gradient)
✅ **Neon button effects** en btn-primary
✅ **Glass panel border glow** en hover
✅ **Stat card gradient borders**
✅ **Table row glow** en hover
✅ **Navigation active state glow**
✅ **Badge glow effects**
✅ **Input focus glow**
✅ **Super bright text shadows** en dark mode

### Optimizaciones

- Eliminados duplicados
- Consolidados selectores
- Mejorado rendimiento
- Mantenida funcionalidad completa

## Checklist de Consolidación

- [x] Crear `/static/css/design-system/tokens.css`
- [x] Crear `/static/css/design-system/themes.css`
- [x] Crear `/static/css/design-system/components.css`
- [x] Modificar `/templates/index.html` - Flatpickr dinámico
- [x] Modificar `/static/js/app.js` - App.theme.apply()
- [x] Modificar `/static/css/main.css` - Select consolidado
- [x] Documentar sistema (este README)

## Mantenimiento Futuro

### Agregar nuevo color
1. Agregar en `tokens.css` bajo `/* COLORES */`
2. Si es específico del tema, agregar override en `themes.css`
3. Documentar uso

### Agregar nuevo componente
1. Definir en `components.css`
2. Usar tokens existentes
3. Agregar variantes de tema si necesario
4. Documentar en este README

### Modificar tema
1. Editar `themes.css`
2. Probar en ambos modos (dark/light)
3. Verificar contraste WCAG AA (4.5:1)

## Recursos

- **Tokens**: Variables globales reutilizables
- **Themes**: Configuración dark/light
- **Components**: Building blocks UI
- **WCAG AA**: Contraste mínimo 4.5:1
- **Glassmorphism**: Blur + transparencia

---

**Última actualización**: 2025-12-21
**Versión**: 1.0
**Autor**: Claude Code Assistant
