# Análisis de pendientes en archivos Markdown

Fecha: 2026-02-19

## Alcance
Se revisaron todos los archivos `*.md` del repositorio para detectar señales de trabajo pendiente:

- checkboxes sin marcar (`- [ ]`, `1. [ ]`, `[ ]`)
- palabras clave: `pendiente`, `pending`, `por hacer`, `faltante`

> Nota: aparecen muchos `.md` en `node_modules/`, `.agent/` y `.claude/`; estos se consideran documentación de terceros o tooling y no backlog del producto.

## Hallazgos clave (código/documentación del proyecto activo)

Los documentos con más pendientes explícitos son:

1. `docs/MIGRATION_PLAN.md` → **96** ítems pendientes.
2. `docs/IMPLEMENTATION_PLAN.md` → **77** ítems pendientes.
3. `docs/PRODUCTION_CHECKLIST.md` → **56** ítems pendientes.
4. `static/src/legacy-bridge/MIGRATION_GUIDE.md` → **25** ítems pendientes.
5. `docs/UNIFIED_BRIDGE_SUMMARY.md` → **24** ítems pendientes.
6. `FRONTEND-MIGRATION-GUIDE.md` → **21** ítems pendientes.
7. `docs/RUNBOOKS.md` → **15** ítems pendientes.
8. `tests/README.md` → **12** checks de validación pendientes.

## Archivos con pendientes pero de contexto histórico/archivo

La carpeta `basuraa/` concentra muchos checklists antiguos (auditorías, fases, planes y reportes históricos). Estos documentos contienen múltiples tareas no marcadas, pero parecen material de archivo y no necesariamente backlog vigente.

## Conclusión

Sí, **falta trabajo por hacer** según la documentación Markdown: hay múltiples planes/checklists aún sin completar, especialmente en migración, implementación y preparación de producción.

## Recomendación operativa (prioridad)

1. Consolidar un único backlog activo usando como fuente principal:
   - `docs/MIGRATION_PLAN.md`
   - `docs/IMPLEMENTATION_PLAN.md`
   - `docs/PRODUCTION_CHECKLIST.md`
2. Marcar explícitamente documentos archivados (`basuraa/`) como **solo histórico** para evitar ruido.
3. Definir dueño + fecha por cada checkbox crítico de producción/migración.
4. Programar una limpieza de docs duplicados (`tarea-pendiente.md` vs `tareapendiente.md`, etc.) para reducir ambigüedad.
