# CLAUDE_MEMORY.md - Sistema de Memoria Persistente

Este archivo sirve como memoria persistente entre sesiones de Claude Code.
Claude debe leer este archivo al inicio de cada sesión para recordar contexto importante.

---

## Última Actualización
- **Fecha**: 2026-01-10
- **Sesión**: Mega-mejora v2.2 - Memory, Docker, CI/CD, Parser, Dashboard
- **Commits**: 3 (edición Excel + memoria + mega-mejora)

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
- **Causa**: Versión de starlette
- **Workaround**: Comentado en main.py
- **Estado**: ⚠️ Pendiente

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

1. [ ] **Fix GZIPMiddleware** - Resolver import error
2. [ ] **Tests E2E** - Playwright para tests de UI
3. [ ] **Notificaciones** - Email/Slack para leave requests
4. [ ] **Multi-idioma** - i18n para interfaz
5. [ ] **Modo offline** - PWA con service worker
6. [ ] **Reportes PDF** - Generación automática

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
