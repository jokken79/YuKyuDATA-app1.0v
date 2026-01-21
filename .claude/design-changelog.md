# YuKyuDATA Design Changelog

## 2026-01-20: Unified Design System (Update 4)

### Problema Resuelto
**Conflicto de tokens de diseño**: `yukyu-tokens.css` usaba violeta (#7c3aed) como primario, mientras `nexus-theme` usaba cyan (#06b6d4). Esto causaba inconsistencias visuales.

### Solución: Sistema de Diseño Unificado
Archivo: `static/css/unified-design-system.css`

**Decisión**: Cyan (#06b6d4) como color primario, violeta (#7c3aed) como acento secundario.

### Tokens Principales
```css
:root {
  /* Primary - Cyan */
  --color-primary-500: #06b6d4;
  --color-primary-600: #0891b2;

  /* Accent - Violet (former primary) */
  --color-accent-600: #7c3aed;

  /* Focus Ring (unificado) */
  --shadow-focus: 0 0 0 3px rgba(6, 182, 212, 0.4);
}
```

### Archivos Creados/Modificados
| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `unified-design-system.css` | **NUEVO** | Single source of truth (~580 líneas) |
| `login-modal.css` | Modificado | Usa `--shadow-focus` unificado |
| `templates/index.html` | Modificado | Carga unified-design-system.css primero |
| `services/asset_service.py` | Modificado | Nueva lista de CSS |
| `scripts/build-assets.js` | Modificado | Incluye nuevos archivos |

### CSS Legacy Eliminado
- **Eliminados ~13,884 líneas** de `static/css/legacy_backup/`
- Archivos removidos: globals.css, theme.css, design-tokens.css duplicados

### Nuevo Componente: UIStates
Archivo: `static/src/components/UIStates.js`

Proporciona estados UI consistentes:
- `createLoadingState()` - Spinner con mensaje
- `createEmptyState()` - Estado vacío con icono y acción opcional
- `createErrorState()` - Error con retry button
- `createSkeleton()` - Placeholders (text, card, table, avatar)

```javascript
import { UIStates, createLoadingState } from './components/index.js';

// Uso directo
container.appendChild(createLoadingState({ message: '読み込み中...' }));

// Uso con manager
const uiStates = new UIStates(container);
uiStates.showLoading();
// ... después
uiStates.restore();
```

### Consolidación de Estado Frontend
`static/src/store/state.js` ahora es compatibility layer que delega a `unified-state.js`:

```javascript
// Antes: 3 sistemas de estado separados
// Después: Singleton pattern con proxy para legacy code
import { getUnifiedState } from './unified-state.js';
const unifiedState = getUnifiedState();
```

### Arquitectura CSS Actualizada
```
unified-design-system.css (Single Source of Truth)
  ├── yukyu-tokens.css (legacy compatibility)
  ├── nexus-theme/main.css (componentes nexus)
  ├── login-modal.css (modal de login)
  └── premium-corporate.css (estilos premium)
```

---

## 2025-12-16: Sidebar Premium + Light Mode Fix (Update 3)

### Sidebar Redesign
1. **Professional SVG Icons** - Replaced emojis with stroke-based SVG icons (22x22px)
2. **Organized Navigation Groups**:
   - MAIN: Dashboard, Employees (badge con contador), Factories
   - REQUESTS: 申請 Request, カレンダー
   - ANALYTICS: Compliance, 分析 Analytics, 月次レポート
   - FOOTER: Settings
3. **Compact Layout** - Reduced padding para que todo quepa sin scroll

### Light Mode Premium
- **Fixed**: arari-glow.css ahora solo aplica en `[data-theme="dark"]`
- **High Contrast**: Textos #1e293b (casi negro) sobre fondo blanco
- **Visible Icons**: stroke: #334155 con stroke-width: 2.5
- **Active State**: Fondo azul claro con borde cyan

### Files Added/Modified
- `static/css/sidebar-premium.css` - Nuevo sistema de sidebar
- `static/css/light-mode-premium.css` - Estilos premium para light mode
- `static/css/arari-glow.css` - Envuelto en `[data-theme="dark"]`
- `templates/index.html` - Sidebar con iconos SVG

### CSS Architecture
```
main.css (base)
  └── sidebar-premium.css (sidebar styles)
  └── arari-glow.css (dark mode glows - only when data-theme="dark")
  └── light-mode-premium.css (light mode overrides)
```

### Light Mode Colors
```css
/* Sidebar Light Mode */
--nav-text: #1e293b;
--nav-icon: #334155;
--nav-hover-bg: #e2e8f0;
--nav-active-bg: linear-gradient(#e0f2fe, #dbeafe);
--nav-active-border: #7dd3fc;
--badge-bg: #0ea5e9;
```

---

## 2025-12-16: Premium Enhancements (Update 2)

### New Features Added
1. **Premium Logo SVG** (`static/icons/logo-premium.svg`)
   - Stylized kanji 有 (yu) with gold gradient
   - Decorative corner elements
   - Hover glow effect

2. **Washi Paper Texture**
   - Subtle noise overlay (3% opacity)
   - Paper fiber lines on cards
   - Creates depth without distraction

3. **Custom Cursors**
   - Default: Elegant gold crosshair
   - Pointer: Gold arrow for interactive elements
   - Text: Gold I-beam for inputs

4. **Staggered Animations**
   - Cards fade-in with delay cascade
   - Navigation slides from left
   - Table rows animate sequentially
   - Header with scale entrance

5. **Enhanced Hover States**
   - Gold corner decorations on stat cards
   - Shimmer effect on gradient text
   - Gold highlight on table rows

6. **Premium Scrollbar**
   - Thin elegant design
   - Gold on hover
   - Firefox compatible

### Files Added
- `static/css/premium-enhancements.css`
- `static/icons/logo-premium.svg`

---

## 2025-12-16: Premium Corporate Redesign

### Design Direction
**Aesthetic**: Premium Corporate Japanese
**Philosophy**: Wabi-sabi meets corporate sophistication - maximum restraint, maximum impact

### Typography System
| Role | Font | Weight | Usage |
|------|------|--------|-------|
| Display | Cormorant Garamond | 400-700 | Headers, titles, large numbers |
| Body | Source Sans 3 | 300-700 | Body text, UI elements |
| Japanese | Noto Serif JP | 400-700 | Japanese content (traditional elegance) |
| Monospace | IBM Plex Mono | 400-500 | Code, data, IDs |

### Color Palette
```css
/* Premium Neutrals */
--ink: #0a0a0a;
--charcoal: #1a1a1a;
--graphite: #2d2d2d;
--slate: #4a4a4a;
--pewter: #6b6b6b;
--silver: #9a9a9a;
--platinum: #c4c4c4;
--pearl: #e8e8e8;
--ivory: #f5f5f3;
--snow: #fafafa;

/* Premium Accents */
--gold: #c9a961;
--gold-light: #d4ba7a;
--gold-dark: #a68b4b;

/* Semantic (Muted & Elegant) */
--success: #5a8f6e;
--warning: #c9a961;
--danger: #a65d5d;
--info: #5d7a8f;
```

### Files Modified
- `static/css/premium-corporate.css` - New design system (created)
- `static/css/main.css` - Original design (preserved for rollback)
- `templates/index.html` - Font imports and CSS reference updated
- `static/js/app.js` - Chart colors updated to match palette

### Design Principles Applied
1. **Restraint over excess** - Subtle animations, no flashy effects
2. **Gold accents** - Premium feel without being gaudy
3. **Serif elegance** - Cormorant Garamond for sophistication
4. **Generous whitespace** - Room to breathe
5. **Muted semantic colors** - Danger/success that don't scream

### Rollback Instructions
```html
<!-- In templates/index.html, change: -->
<link rel="stylesheet" href="/static/css/main.css">

<!-- And restore fonts: -->
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+JP:wght@400;500;700&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
```

---

## Design Guidelines for Future Updates

### Do
- Maintain gold (#c9a961) as primary accent
- Use serif fonts for headers
- Keep animations subtle (150-400ms)
- Preserve generous spacing
- Use muted colors for status indicators

### Don't
- Add flashy gradients or glassmorphism
- Use bright/neon colors
- Add excessive micro-interactions
- Use sans-serif for main headers
- Crowd the interface with elements
