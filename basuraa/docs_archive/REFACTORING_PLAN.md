# Database.py Refactorización - Plan Detallado

## Análisis Actual (database.py - 2,972 líneas)

### Categorías Identificadas

1. **Connection Management** (60 líneas)
   - get_db_path()
   - get_db_connection()
   - get_db() [context manager]
   - _get_param_placeholder()
   - _convert_query_placeholders()

2. **Database Initialization** (344 líneas)
   - init_db() - Crea todas las tablas

3. **Validation Functions** (170 líneas)
   - validate_balance_limit()
   - get_employee_total_balance()

4. **CRUD - Employees** (520 líneas)
   - save_employees()
   - get_employees()
   - get_available_years()
   - get_employees_enhanced()
   - clear_database()

5. **CRUD - Genzai** (450 líneas)
   - save_genzai()
   - get_genzai()
   - clear_genzai()

6. **CRUD - Ukeoi** (330 líneas)
   - save_ukeoi()
   - get_ukeoi()
   - clear_ukeoi()

7. **CRUD - Staff** (320 líneas)
   - save_staff()
   - get_staff()
   - clear_staff()

8. **Statistics** (270 líneas)
   - get_stats_by_factory()

9. **Leave Requests** (350 líneas)
   - create_leave_request()
   - get_leave_requests()
   - approve_leave_request()
   - reject_leave_request()
   - cancel_leave_request()
   - revert_approved_request()

10. **Yukyu Usage Details** (510 líneas)
    - save_yukyu_usage_details()
    - get_yukyu_usage_details()
    - get_monthly_usage_summary()
    - update_yukyu_usage_detail()
    - delete_yukyu_usage_detail()
    - add_single_yukyu_usage()
    - recalculate_employee_used_days()

11. **Employee Updates** (280 líneas)
    - update_employee()
    - get_employee_usage_summary()
    - get_employee_yukyu_history()
    - delete_old_yukyu_records()

12. **Backups** (200 líneas)
    - create_backup()
    - list_backups()
    - restore_backup()

13. **Audit Logging** (800 líneas)
    - log_audit()
    - get_audit_log()
    - get_audit_log_by_user()
    - get_entity_history()
    - get_audit_stats()
    - cleanup_old_audit_logs()

14. **Bulk Operations** (500 líneas)
    - init_bulk_audit_table()
    - bulk_update_employees()
    - get_bulk_update_history()
    - revert_bulk_update()

15. **Notifications** (200 líneas)
    - mark_notification_read()
    - mark_all_notifications_read()
    - is_notification_read()
    - get_read_notification_ids()
    - get_unread_count()

## Plan de Refactorización

### Distribución de Código (Target)

```
database/
├── __init__.py (factory + exports)
├── connection.py (150 líneas) - Already exists
├── crud.py (1,600 líneas) - CRUD operations
├── validation.py (300 líneas) - Validations
├── backups.py (200 líneas) - Backup/restore
├── audit.py (400 líneas) - Audit logging
├── notifications.py (150 líneas) - Notifications
└── migrations.py (300 líneas) - Alembic integration

database.py (300 líneas) - Legacy wrapper + factory
```

### Archivos a Crear

1. `database/crud.py` - CRUD completo (1,600 líneas)
2. `database/validation.py` - Validaciones (300 líneas)
3. `database/backups.py` - Backups (200 líneas)
4. `database/audit.py` - Audit logging (400 líneas)
5. `database/notifications.py` - Notifications (150 líneas)
6. `database/migrations.py` - Alembic (300 líneas)

### Impacto en Otros Archivos

- `main.py` - Actualizar imports
- `routes/*.py` - Actualizar imports (19 archivos)
- `services/*.py` - Algunos servicios usan database
- `tests/*.py` - Actualizar imports

## Fase 2 Roadmap

### Semana 2 (24 horas)
1. Crear estructura de directorios `database/`
2. Mover functions a `crud.py`
3. Mover validations a `validation.py`
4. Crear `database.py` wrapper
5. Tests de equivalencia

### Semana 3 (12 horas)
1. Implementar Repository Pattern
2. Crear `repositories/` directory
3. Tests de repositories

### Semana 3 (12 horas)
1. Expandir Service Layer
2. Crear `services/employee_service.py`
3. Crear `services/leave_service.py`
4. Crear `services/compliance_service.py`

## Testing Strategy

1. Verificar que todas las funciones siguen siendo accesibles desde `database.py`
2. Verificar que no hay breaking changes
3. Tests de equivalencia: mismo comportamiento
4. Tests de performance: no debe haber regresión

## Commits Esperados

1. `refactor: split database.py into modules`
2. `refactor: move CRUD operations to database/crud.py`
3. `refactor: implement repository pattern`
4. `refactor: expand service layer`
5. `test: add equivalence tests for database refactoring`

