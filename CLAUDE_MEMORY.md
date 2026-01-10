# CLAUDE_MEMORY.md - Sistema de Memoria Persistente

Este archivo sirve como memoria persistente entre sesiones de Claude Code.
Claude debe leer este archivo al inicio de cada sesión para recordar contexto importante.

---

## Última Actualización
- **Fecha**: 2026-01-10
- **Sesión**: Implementación de edición de Excel v2.1

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

### 3. Patrones de Código
- Usar `INSERT OR REPLACE` para sincronización idempotente
- Usar `with get_db() as conn:` para conexiones seguras
- Frontend usa patrón singleton `App.{module}`

---

## Features Implementadas (Historial)

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

## Errores Conocidos y Soluciones

### Error: Medio día no se detecta en Excel
- **Causa**: `days_used = 1.0` hardcodeado en parser
- **Solución temporal**: Editar manualmente con nuevo sistema v2.1
- **TODO**: Mejorar parser para detectar valores en celdas

### Error: Comentarios en celdas ignoran fechas
- **Causa**: `data_only=True` en openpyxl
- **Solución**: Sistema de edición manual v2.1

---

## Próximas Mejoras Sugeridas

1. [ ] **Parser mejorado**: Detectar medio día automáticamente
2. [ ] **Validación en importación**: Alertar sobre celdas problemáticas
3. [ ] **Historial de ediciones**: Audit log para cambios manuales
4. [ ] **Bulk edit**: Editar múltiples empleados a la vez

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
3. Revisar TODOs pendientes si existen

### Antes de implementar:
1. Verificar si ya existe funcionalidad similar
2. Revisar sección "Errores Conocidos"
3. Seguir patrones establecidos en "Decisiones de Arquitectura"

### Al terminar sesión:
1. Actualizar este archivo con nuevos aprendizajes
2. Documentar errores encontrados y soluciones
3. Agregar features implementadas al historial

---

## Contacto con Usuario

### Preferencias conocidas:
- Comunicación en castellano
- Le gustan las explicaciones visuales (tablas, diagramas)
- Prefiere soluciones completas end-to-end
- Usa Windows (scripts .bat)
