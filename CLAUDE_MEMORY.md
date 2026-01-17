# CLAUDE_MEMORY.md - Sistema de Memoria Persistente

Este archivo sirve como memoria persistente entre sesiones de Claude Code.
Claude debe leer este archivo al inicio de cada sesión para recordar contexto importante.

---

## Última Actualización
- **Fecha**: 2026-01-17
- **Sesión**: UI/UX Deep Audit & WCAG Fixes v5.4
- **Commits**: 10 (v2.1 + v2.2 + v2.3 + v2.4 + v2.5 + v2.6 + v2.7 + v5.4)

---

## Decisiones de Arquitectura Importantes

### 1. Diseño de Base de Datos
- **Patrón ID compuesto**: `{employee_num}_{year}` para tabla employees
- **LIFO para deducciones**: Días más nuevos se consumen primero
- **Período fiscal**: 21日〜20日 (día 21 al 20 del siguiente mes)

### 2. Stack Tecnológico
- Backend: FastAPI + SQLite (con soporte PostgreSQL opcional)
- Frontend: Vanilla JS con ES6 modules (NO frameworks)
- Estilos: Glassmorphism design system
- Containerización: Docker con docker-compose

### 3. Patrones de Código
- Usar `INSERT OR REPLACE` para sincronización idempotente
- Usar `with get_db() as conn:` para conexiones seguras
- Frontend usa patrón singleton `App.{module}`
- Agentes usan patrón `get_{agent}_agent()` para singleton

---

## Features Implementadas (Historial)

### v5.4 (2026-01-17) - UI/UX Deep Audit & WCAG AA Compliance
**Análisis exhaustivo del agente elite-ui-architect + implementación de mejoras críticas:**

| Categoría | Feature | Archivos | Descripción |
|-----------|---------|----------|-------------|
| Colores | Purple Elimination | `sidebar-premium.css`, `components.css`, `utilities.css`, `accessibility.css`, `arari-glow.css` | Eliminados 65 usos de purple/violet, reemplazados con Amber/Cyan/Teal (paleta corporativa) |
| Accesibilidad | ARIA Labels Dinámicos | `ui-manager.js` | KPIs, tablas, contadores con aria-label en japonés |
| Accesibilidad | Focus Trap | `ui-manager.js` | FocusTrap integrado en sidebar mobile y modales, cierre con Escape |
| Accesibilidad | WCAG AA Badges | `components.css` | Contraste corregido (4.5:1+) para badges success/warning/danger/info |
| Accesibilidad | Reduced Motion | `app.js`, `components.css` | GSAP animations respetan prefers-reduced-motion |
| UX | Skeleton Loaders | `components.css` | Nuevos skeletons específicos: stat-value, table-row, kpi-ring, chart |

**Puntuación UI/UX mejorada**: 7.2/10 → 8.5/10 (estimado)

**Cambios de paleta corporativa:**
- ❌ `#a855f7` (purple) → ✅ `#f59e0b` (amber) para badges Ukeoi
- ❌ `#8b5cf6` (violet) → ✅ `#14b8a6` (teal) para glows
- ❌ `#7c3aed` (purple) → ✅ `#0891b2` (cyan) para visited links

---

### v2.7 (2026-01-14) - UI/UX Enhancements (Sprint 1, 2 & 3)
**Implementación completa de mejoras UI/UX recomendadas por el agente experto:**

| Sprint | Feature | Archivos | Descripción |
|--------|---------|----------|-------------|
| 1 | Form Validation | `ui-enhancements.js` | Sistema de validación con feedback real-time, mensajes localizados |
| 1 | Loading States | `ui-enhancements.js` | Spinners, aria-busy, estados de éxito/error |
| 1 | Confirm Dialogs | `ui-enhancements.js` | Confirmación para acciones destructivas (delete/reset) |
| 2 | Focus Trap | `ui-enhancements.js` | Trap de foco en modales para accesibilidad |
| 2 | Tablet Responsive | `ui-enhancements.css` | Fixes para breakpoint 768px, sidebar toggle |
| 2 | CSS Tokens | `ui-enhancements.css` | Variables consolidadas para transiciones, sombras, radios |
| 3 | Progress Indicators | `ui-enhancements.js` | Indicadores de progreso con estados indeterminate/complete/error |
| 3 | Tooltip System | `ui-enhancements.js` | Tooltips accesibles con posicionamiento dinámico |
| 3 | Light Theme Contrast | `ui-enhancements.css` | Mejoras de contraste para modo claro (WCAG AA) |

**Archivos creados:**
- `static/js/modules/ui-enhancements.js` (600+ líneas)
- `static/css/ui-enhancements.css` (400+ líneas)

**Integración:**
- Module ES6 exportado con clases: `FormValidator`, `LoadingState`, `ConfirmDialog`, `FocusTrap`, `Tooltip`, `ProgressIndicator`
- Auto-inicialización de tooltips en botones principales
- Atributos data-tooltip añadidos a botones sync
- Accesible globalmente via `window.UIEnhancements`

### v2.6 (2026-01-14) - Notification Read Status
**Implementación de estado de lectura para notificaciones:**

| Feature | Archivos | Descripción |
|---------|----------|-------------|
| Notification Reads Table | `database.py` | Nueva tabla `notification_reads` para trackear estado de lectura por usuario |
| Read Status Tracking | `database.py` | Funciones: `mark_notification_read()`, `mark_all_notifications_read()`, `get_read_notification_ids()`, `get_unread_count()` |
| GET /api/notifications | `main.py` | Actualizado para incluir `is_read` por usuario y filtro `unread_only` |
| POST /api/notifications/{id}/mark-read | `main.py` | Nuevo endpoint para marcar notificación como leída |
| POST /api/notifications/mark-all-read | `main.py` | Nuevo endpoint para marcar múltiples notificaciones como leídas |
| GET /api/notifications/unread-count | `main.py` | Nuevo endpoint para obtener conteo de no leídas |

**Detalles técnicos:**
- Estado de lectura es per-usuario (multi-usuario ready)
- Usa UNIQUE constraint para evitar duplicados
- Índices para búsquedas rápidas por user_id y notification_id

### v2.5 (2026-01-14) - TODO Review & Test Improvements
**5 TODOs corregidos + Análisis completo de testing y CI/CD:**

| Feature | Archivos | Descripción |
|---------|----------|-------------|
| CSP Hardening | `config.security.py` | `unsafe-inline` removido, usa `strict-dynamic` |
| Backup Notifications | `monitoring/backup_scheduler.py` | Email/Slack notifications implementadas |
| Smart Test Assertions | `agents/testing.py` | Assertions específicas por tipo de función |
| New Employees Count | `agents/documentor.py` | Conteo de empleados nuevos en reportes |
| Leave Requests Module | `static/js/modules/leave-requests-manager.js` | Módulo completo de solicitudes |

**Análisis de Testing realizado:**
- 30+ endpoints sin tests documentados
- Módulos críticos sin cobertura: LIFO Deduction, Sanitizer, Excel parsing
- Recomendación: Aumentar coverage de 50% a 80%

**Mejoras CI/CD recomendadas:**
- E2E tests con Playwright
- Performance benchmarks
- Dependabot auto-merge
- Release automation

### v2.4 (2026-01-11) - Security & Testing
**8 mejoras de seguridad y testing implementadas:**

| Feature | Archivos | Descripción |
|---------|----------|-------------|
| XSS Fix | `app.js` | 13 vulnerabilidades XSS corregidas |
| CSRF Protection | `csrf_middleware.py`, `main.py` | Middleware CSRF para POST/PUT/DELETE |
| SQL Indexes | `database.py` | 4 índices nuevos (hire_date, leave_date, visa_expiry) |
| Fetch Timeout | `data-service.js` | AbortController con timeout 30s |
| Fiscal Tests | `tests/test_fiscal_year.py` | Tests unitarios para 12 funciones críticas |
| 40-Day Limit | `fiscal_year.py` | Validación de límite máximo acumulable |
| AT_RISK Fix | `fiscal_year.py` | Bug corregido en check_5day_compliance() |
| Async Parsing | `main.py` | asyncio.to_thread() para Excel no bloqueante |

### v2.3 (2026-01-10) - Notifications, i18n, PWA, PDF, E2E
**8 mejoras principales implementadas:**

| Feature | Archivos | Descripción |
|---------|----------|-------------|
| Notifications | `notifications.py` | Sistema Email/Slack para alertas |
| i18n | `static/js/modules/i18n.js`, `static/locales/*.json` | Multi-idioma (ja/es/en) |
| PWA Offline | `static/sw.js`, `offline-storage.js` | Service Worker + IndexedDB |
| PDF Reports | `reports.py` | Generación de reportes PDF |
| E2E Tests | `tests/e2e/*.spec.js` | 6 test suites con Playwright |
| Bulk Edit | `App.bulkEdit` | Edición masiva de empleados |
| Audit Log | `database.py`, `main.py` | Trail completo de cambios |
| Email Templates | `templates/emails/*.html` | Plantillas HTML para emails |

### v2.2 (2026-01-10) - Mega-mejora
**8 mejoras principales implementadas:**

| Feature | Archivos | Descripción |
|---------|----------|-------------|
| Memory Agent | `agents/memory.py` | Sistema de memoria persistente JSON |
| Docker Dev | `Dockerfile`, `docker-compose.*.yml` | Entorno de desarrollo containerizado |
| Pre-commit Hooks | `.pre-commit-config.yaml`, `scripts/` | Verificaciones automáticas pre-commit |
| Project Dashboard | `/status`, `scripts/project-status.py` | Dashboard visual + CLI |
| CI/CD Pipeline | `.github/workflows/` | GitHub Actions para CI/CD |
| Parser Mejorado | `excel_service.py` | Detecta medio día, maneja comentarios |
| GitHub Issues | `scripts/github_issues.py` | Integración completa con GitHub |
| Import Validation | `app.js`, `index.html` | Modal con alertas visuales |

### v2.1 (2026-01-10) - Edición de Excel
- **Problema resuelto**: Celdas con comentarios se ignoraban en importación
- **Solución**: CRUD completo para yukyu_usage_details
- **Endpoints nuevos**:
  - PUT/DELETE/POST `/api/yukyu/usage-details`
  - POST `/api/yukyu/recalculate/{emp}/{year}`
  - PUT `/api/employees/{emp}/{year}`
- **Frontend**: Modal de edición con `App.editYukyu`

### v2.0 - Detalles de Uso Individual
- Tabla `yukyu_usage_details` para fechas individuales
- Columnas R-BE del Excel parseadas
- Endpoint `/api/yukyu/usage-details`

### v1.x - Sistema Base
- Sincronización desde Excel
- Leave requests workflow (PENDING → APPROVED/REJECTED)
- Backup/Restore sistema
- JWT Authentication

---

## Nuevos Endpoints (v2.2)

### Dashboard & Status
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/status` | Dashboard HTML visual |
| GET | `/api/project-status` | Estado del proyecto (JSON) |

### GitHub Integration
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/github/issues` | Listar issues |
| POST | `/api/github/issues` | Crear issue |
| POST | `/api/github/sync-todos` | Sincronizar TODOs |

---

## Nuevos Scripts Disponibles

```bash
# Docker
./scripts/docker-dev.sh           # Iniciar desarrollo
./scripts/docker-dev.sh --stop    # Detener

# Pre-commit
./scripts/install-hooks.sh        # Instalar hooks
./scripts/run-checks.sh           # Verificar manualmente

# Status
python scripts/project-status.py  # Estado en CLI

# GitHub
python scripts/sync-issues.py     # Sincronizar TODOs a Issues
```

---

## Errores Conocidos y Soluciones

### Error: Medio día no se detecta en Excel
- **Causa**: Antes `days_used = 1.0` hardcodeado
- **Solución v2.2**: Parser mejorado detecta automáticamente:
  - 半, 0.5, 午前, 午後 → 0.5 días
  - 2h, 2時間, 時間休 → 0.25 días
- **Estado**: ✅ RESUELTO

### Error: Comentarios en celdas ignoran fechas
- **Causa**: `data_only=True` en openpyxl
- **Solución v2.2**: Parser intenta extraer fecha de todas formas
- **Solución v2.1**: Sistema de edición manual
- **Estado**: ✅ RESUELTO

### Error: GZIPMiddleware import
- **Causa**: Nombre de clase era `GZipMiddleware` (no `GZIPMiddleware`)
- **Solución v2.3**: Corregido import a `from starlette.middleware.gzip import GZipMiddleware`
- **Estado**: ✅ RESUELTO

---

## Archivos Importantes por Módulo

### Core Application
| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `main.py` | 5,500+ | FastAPI endpoints |
| `database.py` | 1,400+ | SQLite CRUD |
| `excel_service.py` | 800+ | Parser Excel mejorado |
| `fiscal_year.py` | 513 | Lógica fiscal japonesa |

### Frontend
| Archivo | Propósito |
|---------|-----------|
| `app.js` | 4,800+ líneas, módulos App.* |
| `index.html` | SPA principal + modales |
| `status.html` | Dashboard de estado |

### Agentes
| Archivo | Propósito |
|---------|-----------|
| `agents/memory.py` | Sistema de memoria |
| `agents/compliance.py` | Verificación 5-días |
| `agents/orchestrator.py` | Coordinación |

### DevOps
| Archivo | Propósito |
|---------|-----------|
| `Dockerfile` | Build de imagen |
| `docker-compose.dev.yml` | Desarrollo |
| `.github/workflows/ci.yml` | CI pipeline |

---

## Próximas Mejoras Sugeridas

1. [x] **Fix GZIPMiddleware** - Resolver import error (v2.3)
2. [x] **Tests E2E** - Playwright para tests de UI (v2.3)
3. [x] **Notificaciones** - Email/Slack para leave requests (v2.3)
4. [x] **Multi-idioma** - i18n para interfaz (v2.3)
5. [x] **Modo offline** - PWA con service worker (v2.3)
6. [x] **Reportes PDF** - Generación automática (v2.3)

### Nuevas sugerencias (v2.5):
7. [x] **LIFO Deduction Tests** - Tests críticos para deducción de días (COMPLETADO: `tests/test_lifo_deduction.py`)
8. [x] **Sanitizer Tests** - Tests de prevención XSS para seguridad (COMPLETADO: `tests/unit/test-sanitizer.test.js`)
9. [x] **E2E Tests Playwright** - Flujos críticos automatizados (COMPLETADO: `tests/e2e/*.spec.js`)
10. [x] **GitHub Actions E2E** - Workflow para e2e-tests.yml (COMPLETADO: `.github/workflows/e2e-tests.yml`)
11. [x] **Coverage 80%** - Aumentar threshold en ci.yml (COMPLETADO: `--cov-fail-under=80`)
12. [x] **Dockerfile.secure** - Crear imagen segura para producción (COMPLETADO: `Dockerfile.secure`)
13. [ ] **Mobile-first refactor** - Mejor experiencia móvil
14. [x] **API Documentation** - Swagger/OpenAPI docs (COMPLETADO: `/docs`, `/redoc`)

---

## Convenciones del Proyecto

### Idiomas
- **Código**: Inglés (variables, funciones)
- **UI**: Japonés (labels, mensajes)
- **Documentación**: Castellano/Español (para el usuario)
- **Comentarios**: Inglés o Castellano según contexto

### Nombres de Branches
- Features: `claude/feature-name-{sessionId}`
- Fixes: `claude/fix-description-{sessionId}`

### Commits
- Usar conventional commits: `feat:`, `fix:`, `docs:`, etc.
- Mensajes en inglés
- Descripción detallada en body

---

## Notas para Claude

### Al iniciar sesión:
1. Leer este archivo primero
2. Verificar estado de git (`git status`, `git log -3`)
3. Revisar TODOs pendientes en `agents/memory_store.json`
4. Ejecutar `python scripts/project-status.py` para estado rápido

### Antes de implementar:
1. Verificar si ya existe funcionalidad similar
2. Revisar sección "Errores Conocidos"
3. Seguir patrones establecidos en "Decisiones de Arquitectura"
4. Usar `App.editYukyu` como referencia para modales

### Al terminar sesión:
1. Actualizar este archivo con nuevos aprendizajes
2. Ejecutar `python scripts/sync-issues.py` si hay TODOs nuevos
3. Documentar errores encontrados y soluciones
4. Agregar features implementadas al historial

---

## Contacto con Usuario

### Preferencias conocidas:
- Comunicación en castellano
- Le gustan las explicaciones visuales (tablas, diagramas)
- Prefiere soluciones completas end-to-end
- Usa Windows (scripts .bat disponibles)
- Valora la proactividad ("Haz todo lo necesario")

## Recent Commits

| Date | Hash | Message |
|------|------|---------|
| 2026-01-14 | TBD | feat: Fix 5 TODOs, improve testing & CI/CD analysis (v2.5) |
| 2026-01-11 | 8023305 | feat: Security, performance & testing improvements (v2.4) |
| 2026-01-10 | c07a85e | chore: Mark audit log and bulk edit TODOs as completed |
| 2026-01-10 | 3167930 | docs: Update CLAUDE_MEMORY.md with v2.3 session summary |
| 2026-01-10 | 7fb8bfe | feat: Add notifications, i18n, PWA offline, PDF reports, E2E tests |
