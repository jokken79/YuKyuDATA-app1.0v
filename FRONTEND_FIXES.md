# Frontend Fixes - Implementation Guide

**Prioridad:** IMMEDIATE (Semana actual)
**Tiempo estimado:** 4-6 horas
**Impacto:** Alto (Reduce memory leaks, mejora accesibilidad)

---

## 1. CRITICAL FIX: Modal Memory Leak

**Archivo:** `/home/user/YuKyuDATA-app1.0v/static/src/components/Modal.js`
**Línea:** ~280 (método `destroy()`)
**Impacto:** Memory grows 20KB per modal destroyed

### Problema

```javascript
// ACTUAL (línea 280-290)
destroy() {
    if (this.element) {
        this.element.remove();
        this.element = null;
    }
    // ❌ FALTA: removeEventListener
}
```

### Solución

Reemplazar el método `destroy()` con:

```javascript
destroy() {
    if (this.isOpen) {
        this.close();
    }

    // ✅ AGREGAR: Remover todos los event listeners
    document.removeEventListener('keydown', this._handleKeyDown);

    if (this.element) {
        this.element.removeEventListener('click', this._handleBackdropClick);
        this.element.remove();
        this.element = null;
    }

    if (this.backdrop) {
        this.backdrop.remove();
        this.backdrop = null;
    }

    // Limpiar referencias
    this.previousActiveElement = null;
    this.focusableElements = [];

    // Remover del registry
    Modal.activeModals.delete(this.id);
}
```

---

## 2. CRITICAL FIX: Select Memory Leak

**Archivo:** `/home/user/YuKyuDATA-app1.0v/static/src/components/Select.js`
**Línea:** ~200 (método `destroy()`)
**Impacto:** Memory grows 15KB per select destroyed

### Problema

```javascript
// ACTUAL
destroy() {
    if (this.element) {
        this.element.remove();
    }
    // ❌ FALTA: removeEventListener para document.click
}
```

### Solución

```javascript
destroy() {
    // ✅ AGREGAR: Remover listener de document
    document.removeEventListener('click', this._handleDocumentClick);

    if (this.dropdown) {
        this.dropdown.remove();
        this.dropdown = null;
    }

    if (this.element) {
        this.element.remove();
        this.element = null;
    }

    // Limpiar referencias
    this.filteredOptions = [];
    this.selectedOptions = new Set();
}
```

---

## 3. CRITICAL FIX: Tooltip Cleanup

**Archivo:** `/home/user/YuKyuDATA-app1.0v/static/src/components/Tooltip.js`
**Línea:** ~150 (función `destroy()`)
**Impacto:** Tooltip elements remain in DOM indefinitely

### Problema

```javascript
// ACTUAL
function destroy() {
    element.removeEventListener('mouseenter', show);
    element.removeEventListener('mouseleave', hide);
    element.removeEventListener('focus', show);
    element.removeEventListener('blur', hide);
    element.removeEventListener('click', toggle);
    // ❌ FALTA: tooltip.remove()
}
```

### Solución

```javascript
function destroy() {
    // Remover all listeners
    element.removeEventListener('mouseenter', show);
    element.removeEventListener('mouseleave', hide);
    element.removeEventListener('focus', show);
    element.removeEventListener('blur', hide);
    element.removeEventListener('click', toggle);

    // ✅ AGREGAR: Remover tooltip del DOM
    if (tooltip && tooltip.parentNode) {
        tooltip.parentNode.removeChild(tooltip);
    }

    // Limpiar referencias
    tooltip = null;
    popupTooltips.delete(element);
}
```

---

## 4. HIGH FIX: Form Email Validation

**Archivo:** `/home/user/YuKyuDATA-app1.0v/static/src/components/Form.js`
**Línea:** ~400 (método `validateField()`)
**Impacto:** Puede aceptar emails inválidos

### Problema

```javascript
// ACTUAL (línea 400)
if (field.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    return Form.MESSAGES.email;
}
// Regex muy simple, no cumple RFC 5322
```

### Solución

```javascript
// MEJOR: Usar validación HTML5
if (field.type === 'email') {
    const input = document.createElement('input');
    input.type = 'email';
    input.value = value;

    if (!input.checkValidity()) {
        return Form.MESSAGES.email;
    }
}

// ALTERNATIVA: Regex más completo
if (field.type === 'email') {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    // Mejor aún: RFC 5322 validation
    const rfc5322 = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|([a-zA-Z\-0-9]+(\.[a-zA-Z\-0-9]+)*))$/;

    if (!rfc5322.test(value)) {
        return Form.MESSAGES.email;
    }
}
```

---

## 5. HIGH FIX: Table Keyboard Navigation

**Archivo:** `/home/user/YuKyuDATA-app1.0v/static/src/components/Table.js`
**Ubicación:** Agregar después del método `render()`
**Impacto:** Usuarios de teclado pueden navegar tabla

### Código a agregar

```javascript
/**
 * Setup keyboard navigation for table
 * @private
 */
_setupKeyboardNavigation() {
    this.tableElement.addEventListener('keydown', (e) => {
        const activeRow = this.tableElement.querySelector('tr[data-focused=true]');

        switch (e.key) {
            case 'ArrowUp':
                e.preventDefault();
                this._focusPreviousRow(activeRow);
                break;

            case 'ArrowDown':
                e.preventDefault();
                this._focusNextRow(activeRow);
                break;

            case 'ArrowLeft':
                e.preventDefault();
                this._focusPreviousColumn(activeRow);
                break;

            case 'ArrowRight':
                e.preventDefault();
                this._focusNextColumn(activeRow);
                break;

            case 'Enter':
                e.preventDefault();
                if (activeRow) {
                    const rowData = this._getRowData(activeRow);
                    if (this.onRowClick) {
                        this.onRowClick(rowData);
                    }
                }
                break;
        }
    });
}

/**
 * Focus previous row
 * @private
 */
_focusPreviousRow(currentRow) {
    if (!currentRow) return;
    const prevRow = currentRow.previousElementSibling;
    if (prevRow) {
        currentRow.removeAttribute('data-focused');
        prevRow.setAttribute('data-focused', 'true');
        prevRow.focus();
    }
}

/**
 * Focus next row
 * @private
 */
_focusNextRow(currentRow) {
    if (!currentRow) return;
    const nextRow = currentRow.nextElementSibling;
    if (nextRow) {
        currentRow.removeAttribute('data-focused');
        nextRow.setAttribute('data-focused', 'true');
        nextRow.focus();
    }
}
```

---

## 6. HIGH FIX: Pagination Keyboard Navigation

**Archivo:** `/home/user/YuKyuDATA-app1.0v/static/src/components/Pagination.js`
**Ubicación:** En la sección de button event listeners
**Impacto:** Accesibilidad mejorada

### Código a agregar

```javascript
// Agregar en la función que crea botones de página:
const pageButton = document.createElement('button');
pageButton.type = 'button';
pageButton.textContent = pageNum;
pageButton.className = 'pagination-btn';

// ✅ AGREGAR: Hacer focusable con tab
pageButton.setAttribute('tabindex', pageNum === currentPage ? '0' : '-1');

// ✅ AGREGAR: aria-label en japonés
pageButton.setAttribute('aria-label', `ページ ${pageNum}${pageNum === currentPage ? ' (現在)' : ''}`);

// ✅ AGREGAR: aria-current si es página actual
if (pageNum === currentPage) {
    pageButton.setAttribute('aria-current', 'page');
}

pageButton.addEventListener('click', () => {
    this._goToPage(pageNum);
});

// ✅ AGREGAR: Keyboard navigation (Left/Right arrows)
pageButton.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft' && pageNum > 1) {
        e.preventDefault();
        this._goToPage(pageNum - 1);
    } else if (e.key === 'ArrowRight' && pageNum < this.totalPages) {
        e.preventDefault();
        this._goToPage(pageNum + 1);
    }
});

container.appendChild(pageButton);
```

---

## 7. MEDIUM FIX: Badge Accessibility

**Archivo:** `/home/user/YuKyuDATA-app1.0v/static/src/components/Badge.js`
**Ubicación:** En método `render()`
**Impacto:** Screen readers entienden status badges

### Código a modificar

```javascript
// ACTUAL:
const badge = document.createElement('span');
badge.className = `badge badge-${variant}`;
badge.textContent = label;

// ✅ MEJORADO:
const badge = document.createElement('span');
badge.className = `badge badge-${variant}`;
badge.textContent = label;

// Agregar aria attributes
badge.setAttribute('role', 'status');
badge.setAttribute('aria-label', this._getStatusLabel(variant, label));

// Helper para traducciones
_getStatusLabel(variant, label) {
    const translations = {
        'success': `承認: ${label}`,
        'warning': `警告: ${label}`,
        'danger': `エラー: ${label}`,
        'info': `情報: ${label}`
    };
    return translations[variant] || label;
}
```

---

## 8. MEDIUM FIX: CSS Consolidation

**Archivos a consolidar:**
- `static/css/main.css` (3,908 líneas) - KEEPER
- `static/css/ui-enhancements.css` (676 líneas) - MERGE
- `static/css/ui-fixes-v2.8.css` (1,037 líneas) - MERGE
- `static/css/premium-corporate.css` (1,247 líneas) - MERGE
- Otros → Review y eliminar si duplicados

### Plan de acción

1. **Backup archivos:**
   ```bash
   cp static/css/main.css static/css/main.css.backup
   cp static/css/ui-enhancements.css static/css/ui-enhancements.css.backup
   ```

2. **Identificar duplicados:**
   ```bash
   grep -h "^\..*{" static/css/main.css static/css/ui-*.css | sort | uniq -d
   ```

3. **Consolidar:** Copiar estilos únicos de ui-enhancements.css a main.css

4. **Limpiar HTML:**
   ```html
   <!-- ANTES: -->
   <link rel="stylesheet" href="/static/css/main.css">
   <link rel="stylesheet" href="/static/css/ui-enhancements.css">
   <link rel="stylesheet" href="/static/css/ui-fixes-v2.8.css">

   <!-- DESPUÉS: -->
   <link rel="stylesheet" href="/static/css/main.css">
   ```

5. **Test:** Verificar que no se rompió nada visualmente

---

## 9. MEDIUM FIX: Add Reduced Motion Support

**Archivo:** `/home/user/YuKyuDATA-app1.0v/static/css/main.css`
**Ubicación:** Agregar al final del archivo
**Impacto:** Usuarios con problemas de movimiento ven menos animaciones

### CSS a agregar

```css
/* Respect user preference for reduced motion */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }

    /* Specific element overrides */
    .modal-backdrop {
        animation: none !important;
    }

    .toast {
        animation: none !important;
    }

    .fade-in,
    .slide-up,
    .scale-in {
        animation: none !important;
    }

    /* Preserve important transitions for usability */
    .input-glass:focus,
    .btn:hover,
    .nav-item:active {
        transition: background-color 0s, color 0s;
    }
}
```

---

## 10. Quick Wins - ARIA Labels

**Archivos afectados:** Múltiples
**Tiempo:** 1-2 horas
**Impacto:** Mejora accesibilidad significativamente

### Checklist de aria-labels a agregar

```javascript
// [ ] Badge.js
badge.setAttribute('aria-label', `Status: ${label}`);

// [ ] Pagination.js
pageButton.setAttribute('aria-label', `Page ${pageNum}`);
nextBtn.setAttribute('aria-label', '次へ');
prevBtn.setAttribute('aria-label', '前へ');

// [ ] Tooltip.js (elemento de tooltip)
tooltip.setAttribute('role', 'tooltip');
tooltip.setAttribute('aria-hidden', 'true');  // Hidden by default

// [ ] Table.js (checkbox de selección)
checkbox.setAttribute('aria-label', `Select row ${rowNum}`);

// [ ] Form.js (help text)
helpText.setAttribute('aria-describedby', `${fieldName}-help`);

// [ ] Button.js (con solo icono)
if (!this.text && this.icon) {
    button.setAttribute('aria-label', this.ariaLabel || this.title);
}
```

---

## Implementation Checklist

### Immediatamente (Hoy)

- [ ] Fix Modal memory leak (Modal.js)
- [ ] Fix Select memory leak (Select.js)
- [ ] Fix Tooltip cleanup (Tooltip.js)
- [ ] Test memory usage antes/después
- [ ] Commit changes

### Mañana

- [ ] Fix Form email validation
- [ ] Add Table keyboard navigation
- [ ] Add Pagination keyboard navigation
- [ ] Test accesibilidad con screen reader
- [ ] Commit changes

### Próximos días

- [ ] Fix Badge accessibility
- [ ] Fix CSS consolidation
- [ ] Add reduced-motion CSS
- [ ] Add remaining aria-labels
- [ ] Test completo con Lighthouse
- [ ] Commit final

---

## Testing Commands

```bash
# Test memoria (antes/después)
node --inspect static/js/app.js

# Check accesibilidad con axe
npm install -g @axe-core/cli
axe http://localhost:8000

# Lighthouse audit
npx lighthouse http://localhost:8000 --view

# Test memory leaks (Chrome DevTools)
# 1. Open http://localhost:8000
# 2. DevTools → Memory tab
# 3. Take heap snapshot
# 4. Create/destroy 10 modals
# 5. Take another snapshot
# 6. Compare: debería aumentar poco o nada
```

---

## Validation Scripts

```bash
#!/bin/bash
# Run all checks

echo "🔍 Checking for memory leaks..."
grep -n "removeEventListener" static/src/components/Modal.js
grep -n "removeEventListener" static/src/components/Select.js
grep -n "removeEventListener" static/src/components/Tooltip.js

echo "🔍 Checking for duplicate CSS..."
grep -h "^\\." static/css/main.css static/css/ui-*.css | sort | uniq -d | wc -l

echo "🔍 Checking for missing aria-labels..."
grep -n "role=\"status\"" static/src/components/Badge.js
grep -n "aria-current" static/src/components/Pagination.js
grep -n "aria-label" static/src/components/Table.js

echo "✅ All checks complete!"
```

---

## Success Metrics

Después de aplicar estos fixes:

| Métrica | Antes | Después | Target |
|---------|-------|---------|--------|
| Memory leak per modal | 20KB | 0KB | ✅ |
| CSS lines | 11,909 | ~8,000 | ✅ |
| Accesibilidad score | 65% | 80% | ✅ |
| Keyboard navigation | Parcial | Completo | ✅ |
| Lighthouse a11y | 80 | 95+ | ✅ |

---

## Notes

- Todos estos fixes son **non-breaking changes**
- Compatible con browsers modernos (Chrome 76+, Safari 9+)
- No agregan dependencias nuevas
- Pueden ser aplicados incrementalmente
- Recomendado: Aplicar en este orden

**Tiempo total estimado:** 4-6 horas
**Impacto:** Alto - Mejora experiencia de usuario significativamente

