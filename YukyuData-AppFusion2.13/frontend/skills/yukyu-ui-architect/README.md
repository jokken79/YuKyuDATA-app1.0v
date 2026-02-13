# 🎨 Yukyu UI Architect

**Arquitecto de UI - Diseño, Accesibilidad y Sistema de Componentes**

## 📋 Descripción

Skill especializado para gestionar y mejorar la interfaz de usuario de Yukyu Pro. Incluye:

- Auditoría de UI/UX
- Análisis de accesibilidad WCAG 2.1 AA
- Verificación de responsive design
- Documentación del sistema de diseño
- Sugerencias de mejora

---

## ⚡ Comandos Disponibles

### `/ui-audit`
Auditoría completa de UI/UX de la aplicación.

**Uso:**
```bash
/ui-audit [--component=name] [--export=pdf]
```

**Aspectos auditados:**
- Consistencia visual
- Patrones de interacción
- Flujos de usuario
- Feedback visual
- Estados de carga

**Salida:**
```
🎨 AUDITORÍA DE UI/UX
═══════════════════════════════════════════════════

📊 RESUMEN GENERAL:
  Score UI: 8.2/10
  Score UX: 7.8/10
  Score a11y: 8.0/10

✅ FORTALEZAS:

1. SISTEMA DE TEMA (Dark/Light)
   - Toggle funcional ✅
   - Persistencia en localStorage ✅
   - Respeta system preference ✅
   - Transiciones suaves ✅

2. FEEDBACK VISUAL
   - Toast notifications ✅
   - Loading skeletons ✅
   - Progress bars en ExcelSync ✅
   - Estados de error claros ✅

3. GLASSMORPHISM CONSISTENTE
   - Tarjetas con blur consistente ✅
   - Bordes sutiles ✅
   - Sombras apropiadas ✅

⚠️ ÁREAS DE MEJORA:

1. RESPONSIVE (móvil)
   - Dashboard KPIs: Scroll horizontal en <640px
   - Sidebar: Overlap con contenido en tablet
   - Tablas: Horizontal scroll sin indicador

2. FEEDBACK DE ACCIONES
   - Bulk actions: Sin confirmación visual durante proceso
   - Excel import: Progress poco granular

3. ESTADOS VACÍOS
   - EmployeeList sin datos: Solo texto "No hay empleados"
   - Sin ilustración o CTA

4. MICROINTERACCIONES
   - Botones sin hover state en algunos casos
   - Checkboxes sin transición

📋 COMPONENTES AUDITADOS:

| Componente | UI | UX | a11y | Total |
|------------|----|----|------|-------|
| Dashboard | 9 | 8 | 8 | 8.3 |
| EmployeeList | 8 | 8 | 9 | 8.3 |
| LeaveRequest | 7 | 7 | 7 | 7.0 |
| ApplicationMgmt | 8 | 8 | 8 | 8.0 |
| AccountingReports | 8 | 7 | 7 | 7.3 |
| ExcelSync | 9 | 8 | 6 | 7.7 |
| Sidebar | 9 | 9 | 9 | 9.0 |
```

---

### `/ui-a11y`
Análisis detallado de accesibilidad WCAG 2.1 AA.

**Uso:**
```bash
/ui-a11y [--level=A|AA|AAA] [--fix]
```

**Criterios verificados:**
- Perceptible (contraste, alt text, etc.)
- Operable (teclado, focus, timing)
- Comprensible (labels, errores, consistencia)
- Robusto (parsing, name/role/value)

**Salida:**
```
♿ ANÁLISIS DE ACCESIBILIDAD WCAG 2.1 AA
═══════════════════════════════════════════════════

📊 PUNTUACIÓN: 8/10

✅ IMPLEMENTADO CORRECTAMENTE:

1. NAVEGACIÓN POR TECLADO
   - Sidebar: Tab navigation ✅
   - Modals: Focus trap con FocusTrap ✅
   - Buttons: :focus-visible outline ✅

2. ROLES ARIA
   - Sidebar: role="navigation" ✅
   - Modals: aria-modal="true" ✅
   - Tables: role="grid" ✅
   - Toggle: role="switch" ✅

3. SCREEN READERS
   - .sr-only para texto oculto ✅
   - aria-label en iconos ✅
   - aria-describedby en forms ✅

4. PREFERENCIAS DE USUARIO
   - prefers-reduced-motion: respetado ✅
   - prefers-color-scheme: respetado ✅

⚠️ ISSUES DETECTADOS:

NIVEL A (Críticos):
┌────────────────────────────────────────────────────────┐
│ Ninguno detectado ✅                                    │
└────────────────────────────────────────────────────────┘

NIVEL AA (Requeridos):
┌────────────────────────────────────────────────────────┐
│ 1. CONTRASTE (1.4.3)                                   │
│    Problema: Texto gris en dark mode: #6b7280         │
│    Ratio: 3.8:1 (requiere 4.5:1)                       │
│    Ubicación: Sidebar status text                      │
│    Fix: Cambiar a #9ca3af (ratio 5.2:1)               │
│                                                        │
│ 2. FOCUS VISIBLE (2.4.7)                               │
│    Problema: Algunos botones sin :focus-visible        │
│    Ubicación: Export buttons en Dashboard             │
│    Fix: Agregar outline en :focus-visible              │
│                                                        │
│ 3. IDENTIFICACIÓN DE ERRORES (3.3.1)                   │
│    Problema: Errores de form sin asociación           │
│    Ubicación: LeaveRequest date validation            │
│    Fix: aria-invalid + aria-describedby                │
└────────────────────────────────────────────────────────┘

NIVEL AAA (Recomendados):
┌────────────────────────────────────────────────────────┐
│ 1. Contraste mejorado (7:1) no cumplido               │
│ 2. Sin skip links implementados                        │
│ 3. No hay landmarks secundarios                        │
└────────────────────────────────────────────────────────┘

🔧 FIXES AUTOMÁTICOS DISPONIBLES:

/ui-a11y --fix aplicará:
  - Corregir colores de contraste
  - Agregar :focus-visible faltantes
  - Agregar aria-invalid a inputs
  - Agregar skip link a index.html
```

---

### `/ui-responsive`
Verifica el diseño responsive en todos los breakpoints.

**Uso:**
```bash
/ui-responsive [--breakpoint=sm|md|lg|xl|2xl]
```

**Breakpoints Tailwind:**
- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px
- 2xl: 1536px

**Salida:**
```
📱 ANÁLISIS RESPONSIVE
═══════════════════════════════════════════════════

📊 BREAKPOINTS SOPORTADOS:

┌─────────┬───────────┬─────────────────────────────────┐
│ Break   │ Viewport  │ Estado                          │
├─────────┼───────────┼─────────────────────────────────┤
│ mobile  │ <640px    │ ⚠️ Parcial                       │
│ sm      │ 640px     │ ✅ OK                            │
│ md      │ 768px     │ ✅ OK                            │
│ lg      │ 1024px    │ ✅ OK                            │
│ xl      │ 1280px    │ ✅ OK                            │
│ 2xl     │ 1536px    │ ✅ OK                            │
└─────────┴───────────┴─────────────────────────────────┘

📱 MOBILE (<640px):

Dashboard.tsx:
  ❌ KPI cards: overflow horizontal
     Actual: grid-cols-4
     Sugerido: grid-cols-2 sm:grid-cols-4

  ❌ Charts: muy pequeños
     Actual: height fijo
     Sugerido: aspect-ratio responsive

  ✅ Alert panel: stack vertical OK

EmployeeList.tsx:
  ✅ Cards layout móvil OK
  ⚠️ Search bar: botones overflow
     Fix: flex-wrap o botones icono

ApplicationManagement.tsx:
  ✅ Cards layout OK
  ❌ Bulk action bar: botones apilados
     Fix: sticky footer con scroll

LeaveRequest.tsx:
  ⚠️ Form layout: columns no colapsan bien
     Actual: grid-cols-7
     Sugerido: grid-cols-1 lg:grid-cols-7

ExcelSync.tsx:
  ✅ Dropzones: full width OK
  ✅ Progress bars: OK

📊 TABLET (768px):

Sidebar.tsx:
  ⚠️ Hamburger menu overlap con contenido
     Fix: z-index adjustment

Dashboard.tsx:
  ✅ Charts: 2 columns OK
  ✅ KPIs: OK

🖥️ DESKTOP (1024px+):
  ✅ Todo OK
```

---

### `/ui-components`
Documenta el sistema de componentes.

**Uso:**
```bash
/ui-components [--export=storybook|markdown]
```

**Salida:**
```
📚 SISTEMA DE COMPONENTES
═══════════════════════════════════════════════════

🎨 DESIGN TOKENS:

COLORES (Dark Mode):
  --bg-primary: #050505
  --bg-secondary: #0a0a0a
  --text-primary: #ffffff
  --neon-blue: #00e5ff
  --neon-red: #ff004c
  --accent-yellow: #eab308
  --accent-green: #22c55e

COLORES (Light Mode):
  --bg-primary: #f8fafc
  --bg-secondary: #ffffff
  --text-primary: #0f172a
  --neon-blue: #0077b6
  --neon-red: #dc2626

TIPOGRAFÍA:
  Font Primary: 'Plus Jakarta Sans', sans-serif
  Font Japanese: 'Noto Sans JP', sans-serif
  Font Mono: ui-monospace, monospace

ESPACIADO (Tailwind scale):
  xs: 0.5rem (8px)
  sm: 0.75rem (12px)
  md: 1rem (16px)
  lg: 1.5rem (24px)
  xl: 2rem (32px)

───────────────────────────────────────────────────

📋 COMPONENTES BASE:

1. CYBER-GLASS CARD
   ```html
   <div class="cyber-glass rounded-xl border border-white/10 p-6">
     <!-- Content -->
   </div>
   ```

2. AGGRESSIVE HEADING
   ```html
   <h2 class="aggressive-text text-xl font-bold">
     タイトル
   </h2>
   ```

3. NEON BUTTON (Primary)
   ```html
   <button class="px-4 py-2 bg-cyan-500/20 text-cyan-400
                  border border-cyan-500/30 rounded-lg
                  hover:bg-cyan-500/30 transition-all">
     アクション
   </button>
   ```

4. NEON BUTTON (Danger)
   ```html
   <button class="px-4 py-2 bg-red-500/20 text-red-400
                  border border-red-500/30 rounded-lg
                  hover:bg-red-500/30 transition-all">
     削除
   </button>
   ```

5. INPUT FIELD
   ```html
   <input class="w-full px-4 py-3 rounded-lg
                 bg-black/20 border border-white/10
                 text-white placeholder-gray-500
                 focus:border-cyan-500/50 focus:outline-none"
          placeholder="入力..." />
   ```

6. TABLE ROW
   ```html
   <tr class="border-b border-white/5
              hover:bg-white/5 transition-colors">
     <td class="py-4 px-4">...</td>
   </tr>
   ```

───────────────────────────────────────────────────

📋 COMPONENTES ESPECIALIZADOS:

1. Skeleton (Loading)
2. DigitalHanko (Sello japonés)
3. ThemeToggle (Dark/Light switch)

📋 PATRONES DE LAYOUT:

1. Sidebar + Main Content (desktop)
2. Off-canvas nav (mobile)
3. Cards grid (responsive)
4. Table/Cards adaptive (mobile=cards, desktop=table)
```

---

### `/ui-improve`
Sugiere mejoras concretas de UI/UX.

**Uso:**
```bash
/ui-improve [--priority=high|medium|low|all]
```

**Salida:**
```
💡 MEJORAS SUGERIDAS DE UI/UX
═══════════════════════════════════════════════════

🔴 PRIORIDAD ALTA:

1. EMPTY STATES
   Problema: Listas vacías muestran solo texto
   Mejora: Agregar ilustración + CTA

   ```tsx
   // EmployeeList.tsx
   {employees.length === 0 && (
     <div class="flex flex-col items-center py-12">
       <EmptyIllustration class="w-48 h-48 opacity-50" />
       <p class="text-gray-400 mt-4">従業員がまだいません</p>
       <button class="mt-4 btn-primary">
         Excelからインポート
       </button>
     </div>
   )}
   ```

2. LOADING FEEDBACK EN BULK ACTIONS
   Problema: Sin feedback durante proceso
   Mejora: Progress modal con detalle

   ```tsx
   <Modal open={isProcessing}>
     <ProgressBar value={current} max={total} />
     <p>処理中: {current}/{total}</p>
     <div class="text-sm text-gray-400">
       現在: {currentEmployee}
     </div>
   </Modal>
   ```

3. CONFIRMACIÓN DE ACCIONES DESTRUCTIVAS
   Problema: Delete sin confirmación
   Mejora: Modal de confirmación

🟡 PRIORIDAD MEDIA:

4. SKELETON PERSONALIZADO POR COMPONENTE
   Actual: Skeleton genérico
   Mejora: Skeleton que imita layout real

5. TRANSICIONES ENTRE TABS
   Actual: Corte abrupto
   Mejora: Framer Motion cross-fade

6. TOOLTIPS INFORMATIVOS
   Problema: KPIs sin explicación
   Mejora: Tooltip con descripción

   ```tsx
   <Tooltip content="年間5日以上取得義務のある社員">
     <InfoIcon class="w-4 h-4" />
   </Tooltip>
   ```

7. BREADCRUMBS EN MODALES
   Problema: Contexto perdido en modales anidados
   Mejora: Breadcrumb trail

🟢 PRIORIDAD BAJA:

8. ANIMACIONES DE ENTRADA
   Actual: Aparición instantánea
   Mejora: Stagger fade-in para listas

9. INDICADORES DE SCROLL
   Problema: Usuario no sabe que hay más contenido
   Mejora: Gradient fade en bordes

10. SHORTCUTS KEYBOARD
    Ya existe useKeyboardShortcuts
    Mejora: Mostrar tooltip con shortcut en hover

📊 IMPACTO ESTIMADO:
  UX Score: 7.8 → 8.5 (+9%)
  User satisfaction: +15% estimado
  Task completion time: -20% estimado
```

---

## 🎨 Guía de Estilo Visual

### Glassmorphism
```css
.cyber-glass {
  backdrop-filter: blur(50px) saturate(250%);
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

### Neon Glow
```css
.neon-glow {
  text-shadow: 0 0 10px currentColor,
               0 0 20px currentColor,
               0 0 40px currentColor;
}
```

### Sharp Panels
```css
.sharp-panel {
  clip-path: polygon(
    0 0, calc(100% - 12px) 0,
    100% 12px, 100% 100%,
    12px 100%, 0 calc(100% - 12px)
  );
}
```

---

## 📄 Licencia

MIT - Uso libre para empresas
