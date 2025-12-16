# Checklist de Verificación - Mejoras de Brillo

Usa esta lista para verificar que todos los cambios visuales funcionan correctamente.

## Preparación

- [ ] Reinicia el servidor FastAPI
- [ ] Abre el navegador en modo incógnito
- [ ] Fuerza refresh con `Ctrl + F5`
- [ ] Verifica que estés en dark mode

## 1. Fondo y Glows Ambient

### Fondo Base
- [ ] El fondo es azul oscuro profundo (#0a1428) en vez de casi negro
- [ ] Se ven gradientes radiantes visibles en las 4 esquinas
- [ ] El color general es más "azulado" que antes

### Glows Flotantes
- [ ] Ves un glow cyan en la esquina superior izquierda
- [ ] Ves un glow púrpura/azul en la esquina superior derecha
- [ ] Ves un glow azul en la parte inferior
- [ ] Los glows se mueven sutilmente (animación float-glow)

## 2. Sidebar

### Apariencia General
- [ ] La sidebar tiene un fondo más sólido y visible
- [ ] El borde derecho tiene un toque cyan visible
- [ ] Proyecta un shadow cyan muy sutil
- [ ] Los elementos son claramente legibles

### Navigation Items
- [ ] Texto en color gris claro (#cbd5e1)
- [ ] Hover muestra fondo cyan claro
- [ ] Hover muestra un glow interior (inset)
- [ ] Item activo tiene borde izquierdo cyan
- [ ] Item activo tiene glow de fondo visible

## 3. Stat Cards (Tarjetas KPI)

### Panel Base
- [ ] Fondo más sólido que antes (0.90 opacidad)
- [ ] Borde con toque cyan muy sutil
- [ ] Shadow triple: negro + cyan + interior
- [ ] Hover muestra borde gradient (cyan/purple)

### Texto
- [ ] Valores numéricos en blanco brillante (#f8fafc)
- [ ] Valores tienen text-shadow cyan visible
- [ ] Labels en gris claro (#cbd5e1)
- [ ] Todo el texto es claramente legible

## 4. Paneles Glass

### Apariencia
- [ ] Fondo con 85% opacidad (más sólido)
- [ ] Borde cyan sutil pero visible
- [ ] Shadow más profundo que antes
- [ ] Highlight interior en borde superior

### Hover
- [ ] Efecto shimmer se activa
- [ ] Borde cyan se intensifica
- [ ] Shadow se hace más pronunciado
- [ ] Elevación sutil (translateY)

## 5. Inputs y Forms

### Input Fields
- [ ] Fondo oscuro con opacidad 60%
- [ ] Borde cyan visible (0.2 opacidad)
- [ ] Hover incrementa visibilidad
- [ ] Focus muestra glow cyan brillante
- [ ] Texto en blanco claramente legible

### Form Sections
- [ ] Fondo con tinte visible (0.4 opacidad)
- [ ] Borde cyan sutil
- [ ] Separación clara del fondo

## 6. Tablas

### Headers
- [ ] Fondo cyan muy sutil (0.08 opacidad)
- [ ] Texto en gris claro (#cbd5e1)
- [ ] Borde inferior cyan más grueso (2px)
- [ ] Claramente diferenciado del body

### Rows
- [ ] Filas tienen fondo base sutil (0.3 opacidad)
- [ ] Texto en gris casi blanco (#e2e8f0)
- [ ] Hover muestra fondo cyan (0.12)
- [ ] Hover muestra shadow cyan alrededor
- [ ] Hover muestra borde izquierdo cyan
- [ ] Animación de entrada visible en carga

## 7. Badges

### Badge Success (Verde)
- [ ] Fondo verde con 20% opacidad
- [ ] Borde verde con 40% opacidad
- [ ] Texto en verde claro (#6ee7b7)
- [ ] Glow verde visible (15px blur)

### Badge Warning (Amarillo)
- [ ] Fondo amarillo con 20% opacidad
- [ ] Borde amarillo con 40% opacidad
- [ ] Texto en amarillo claro (#fcd34d)
- [ ] Glow amarillo visible

### Badge Danger (Rojo)
- [ ] Fondo rojo con 20% opacidad
- [ ] Borde rojo con 40% opacidad
- [ ] Texto en rojo claro (#fca5a5)
- [ ] Glow rojo visible

## 8. Botones

### Botón Primary
- [ ] Gradient cyan → blue de fondo
- [ ] Triple shadow: cyan + cyan difuso + interior
- [ ] Hover incrementa todos los shadows
- [ ] Hover activa animación pulse-glow
- [ ] Click muestra efecto ripple
- [ ] Elevación en hover (translateY)

### Botón Glass
- [ ] Fondo semi-transparente visible
- [ ] Borde blanco sutil
- [ ] Hover incrementa opacidad
- [ ] Hover muestra shadow

## 9. Tab Buttons

### Container
- [ ] Fondo oscuro con 60% opacidad
- [ ] Borde cyan sutil
- [ ] Padding interno visible

### Tabs
- [ ] Tab activo con fondo cyan sólido
- [ ] Tab activo con shadow + glow cyan
- [ ] Tab hover con feedback visual
- [ ] Transiciones suaves

## 10. Modales y Overlays

### Loader Overlay
- [ ] Fondo más claro que antes (rgba(10,20,40,0.9))
- [ ] Spinner con glows cyan y purple
- [ ] Blur de fondo visible

### Confirm Modal
- [ ] Overlay con fondo visible
- [ ] Modal content con borde cyan
- [ ] Shadow triple pronunciada
- [ ] Fondo más sólido (0.95 opacidad)

## 11. Toasts

- [ ] Fondo muy sólido (0.95 opacidad)
- [ ] Borde cyan visible (0.3 opacidad)
- [ ] Shadow doble: profundo + glow cyan
- [ ] Texto claramente legible

## 12. Calendar (si aplica)

- [ ] Días con fondo base visible (0.4 opacidad)
- [ ] Hover muestra fondo cyan (0.15)
- [ ] Números de días legibles
- [ ] Separación clara entre días

## 13. Efectos Especiales

### Animaciones
- [ ] Float-glow en glows ambient (20-25s)
- [ ] Pulse-glow en botones primary hover (2s)
- [ ] FadeInUp en cards de bento-grid
- [ ] Shimmer en glass-panels hover

### Text Gradients
- [ ] Headers con gradient cyan → blue → purple
- [ ] Gradient animado y suave
- [ ] Claramente visible sobre fondo oscuro

## 14. Responsive (Mobile)

Si reduces el viewport:
- [ ] Sidebar se convierte en barra horizontal
- [ ] Nav items siguen siendo legibles
- [ ] Glows se mantienen visibles
- [ ] Paneles mantienen opacidad
- [ ] Touch targets son accesibles

## 15. Light Mode (Verificación rápida)

Cambia a light mode:
- [ ] Los ajustes de arari-glow NO afectan light mode
- [ ] Light mode sigue funcionando correctamente
- [ ] Cambio de tema es instantáneo

## Problemas Comunes

Si algo no funciona:

### Cache del navegador
```
1. Ctrl + Shift + Delete (Borrar cache)
2. Ctrl + F5 (Force refresh)
3. Modo incógnito
```

### Archivos no cargados
```
Verifica en DevTools > Network:
- arari-glow.css debe cargar (200 OK)
- main.css debe cargar (200 OK)
```

### Estilos no aplicados
```
Verifica en DevTools > Elements > Computed:
- Busca el elemento problemático
- Verifica que los estilos de arari-glow tengan !important
```

## Capturas de Comparación

Toma capturas de:
1. Vista general del dashboard
2. Sidebar con nav items
3. Stat cards en hover
4. Tabla en hover
5. Botón primary en hover
6. Badges de todos los tipos

## Resultado Final Esperado

✅ **Fondo:** Más claro y azulado
✅ **Glows:** Claramente visibles y vibrantes
✅ **Paneles:** Sólidos pero con glassmorphism
✅ **Texto:** Todo claramente legible
✅ **Interacciones:** Feedback visual pronunciado
✅ **Estilo:** Arari vibrante 100% preservado

---

**Si todos los checks pasan:** ¡El rediseño está completo! 🎉
**Si hay problemas:** Verifica archivos CSS cargados y cache del navegador
