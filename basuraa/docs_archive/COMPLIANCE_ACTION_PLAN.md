# PLAN DE ACCIÓN DE COMPLIANCE
## YuKyuDATA v5.19 - Remediación de Vulnerabilidades Legales

**Fecha Creación:** 2026-01-17
**Auditor:** Claude Code - Compliance Expert Agent
**Vigencia:** Hasta 2026-04-17 (fin año fiscal japonés)

---

## TABLA DE CONTENIDOS

1. Checklist Inmediato (Hoy - 1 semana)
2. Checklist Fase 1 (1-2 semanas)
3. Checklist Fase 2 (3-4 semanas)
4. Checklist Fase 3 (5-8 semanas)
5. Responsabilidades por Rol
6. Herramientas y Recursos
7. Métricas de Éxito

---

## CHECKLIST INMEDIATO (HOY - 24 HORAS)

### Comunicación y Documentación

- [ ] **Notificar a Gerencia**
  - Enviar resumen ejecutivo (COMPLIANCE_SUMMARY.txt)
  - Explicar multa potencial (¥30,900,000+)
  - Solicitar aprobación de plan de remediación
  - Tiempo estimado: 1 hora

- [ ] **Notificar a Legal/HR**
  - Explicar riesgos críticos
  - Compartir documentos de auditoría
  - Solicitar revisión legal
  - Tiempo estimado: 2 horas

- [ ] **Documentación en Repositorio**
  - ✅ COMPLIANCE_AUDIT_2026-01-17.md (ya hecho)
  - ✅ COMPLIANCE_RISK_MATRIX.md (ya hecho)
  - ✅ COMPLIANCE_SUMMARY.txt (ya hecho)
  - [ ] Crear README.md en /docs/compliance/
  - [ ] Agregar links en CLAUDE.md
  - Tiempo estimado: 1 hora

- [ ] **Crear Jira/Tickets**
  - CRÍTICO-001: Auditoría en LIFO deduction
  - CRÍTICO-002: Endpoint 5日 designación
  - CRÍTICO-003: Carry-over auditoría
  - ALTO-004: Validación apply_lifo
  - ALTO-005: Idempotencia carry-over
  - ALTO-006: Validar hire_date
  - Asignar a desarrolladores
  - Tiempo estimado: 1 hora

---

## CHECKLIST FASE 1 - CRÍTICO (1-2 SEMANAS)

### R#2: Auditoría en apply_lifo_deduction()

**Responsable:** Backend Lead
**Esfuerzo:** 4 horas
**Deadline:** 24 Enero 2026

#### Subtareas:

- [ ] Crear tabla en database.py

```sql
CREATE TABLE fiscal_year_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,  -- DEDUCTION, GRANT, CARRYOVER, EXPIRATION, DESIGNATE
    employee_num TEXT NOT NULL,
    year INTEGER NOT NULL,
    days_affected REAL,
    balance_before REAL,
    balance_after REAL,
    performed_by TEXT,  -- Username
    reason TEXT,
    timestamp TEXT NOT NULL,
    UNIQUE(employee_num, year, action, timestamp)
);
```

- [ ] Crear índices para performance

```sql
CREATE INDEX idx_audit_emp_year ON fiscal_year_audit_log(employee_num, year);
CREATE INDEX idx_audit_action ON fiscal_year_audit_log(action);
CREATE INDEX idx_audit_timestamp ON fiscal_year_audit_log(timestamp);
```

- [ ] Modificar apply_lifo_deduction() en fiscal_year.py

```python
# Agregar al final de la deducción exitosa:
c.execute('''
    INSERT INTO fiscal_year_audit_log
    (action, employee_num, year, days_affected, balance_before, balance_after,
     performed_by, reason, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('DEDUCTION', employee_num, current_year, days_to_use,
      breakdown['total_available'], breakdown['total_available'] - days_to_use,
      current_user.username, 'Leave request deduction', datetime.now().isoformat()))
```

- [ ] Crear 5 tests en test_fiscal_year.py

```python
def test_lifo_deduction_logged():
    """Verifica que deducción se registra en audit_log"""
    apply_lifo_deduction('EMP001', 2.0, 2025)

    conn = sqlite3.connect(TEST_DB)
    audit = conn.execute(
        'SELECT * FROM fiscal_year_audit_log WHERE employee_num = ?',
        ('EMP001',)
    ).fetchone()

    assert audit is not None
    assert audit['days_affected'] == 2.0
    assert audit['action'] == 'DEDUCTION'
    conn.close()

# Tests adicionales:
# - test_audit_log_balance_before_after
# - test_audit_log_timestamp_recorded
# - test_audit_log_user_recorded
# - test_audit_log_reason_recorded
```

**Verificación:**
- [ ] Tests pasan (5/5)
- [ ] Datos se registran en audit_log
- [ ] No hay errores al insertar
- [ ] Índices creados correctamente

---

### R#1: Endpoint 5日 Designación

**Responsable:** Backend Senior
**Esfuerzo:** 6 horas
**Deadline:** 27 Enero 2026

#### Subtareas:

- [ ] Crear modelo Pydantic en models.py

```python
class DesignateOfficialLeaveRequest(BaseModel):
    employee_num: str
    year: int
    designated_dates: List[date]  # Fechas específicas

    @validator('employee_num')
    def validate_employee(cls, v):
        # Verificar que existe
        pass

    @validator('year')
    def validate_year(cls, v):
        if v < 2000 or v > 2099:
            raise ValueError("Invalid year")
        return v
```

- [ ] Crear función en fiscal_year.py

```python
def designate_official_leave(
    employee_num: str,
    year: int,
    designated_dates: List[date],
    performed_by: str
) -> Dict:
    """
    企業による5日の指定
    La empresa designa 5 días si empleado no los toma

    Returns:
    {
        "success": bool,
        "days_designated": float,
        "dates": List[date],
        "audit_id": int
    }
    """
    # 1. Verificar empleado tiene 10+ días
    emp = get_employee(employee_num, year)
    if emp['granted'] < 10:
        raise ValueError("Exempt: < 10 days granted")

    # 2. Verificar ha usado < 5
    if emp['used'] >= 5:
        raise ValueError("Already compliant")

    # 3. Calcular cuántos faltan
    remaining = 5 - emp['used']

    # 4. Registrar en BD (nueva tabla)
    # INSERT INTO official_leave_designation(...)

    # 5. Registrar en audit_log
    c.execute('''
        INSERT INTO fiscal_year_audit_log
        (action, employee_num, year, days_affected, ..., reason)
        VALUES (?, ?, ?, ?, ..., ?)
    ''', ('DESIGNATE', employee_num, year, remaining, ..., 'Official designation'))

    # 6. Retornar éxito
    return {
        "success": True,
        "days_designated": remaining,
        "dates": designated_dates
    }
```

- [ ] Crear endpoint en routes/fiscal.py

```python
@router.post("/designate-official-leave")
async def designate_official_leave_endpoint(
    request: DesignateOfficialLeaveRequest,
    user: CurrentUser = Depends(get_admin_user)
):
    """
    企業による5日の指定
    Designa 5日 si empleado no los toma
    """
    try:
        result = designate_official_leave(
            request.employee_num,
            request.year,
            request.designated_dates,
            user.username
        )

        # Notificar a empleado
        send_notification(
            employee_num=request.employee_num,
            type='official_leave_designation',
            message_ja=f"企業により{request.designated_dates}が指定されました",
            message_es=f"Se le han designado días: {request.designated_dates}"
        )

        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error designating leave: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] Crear tabla en database.py

```sql
CREATE TABLE official_leave_designation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_num TEXT NOT NULL,
    year INTEGER NOT NULL,
    designated_date TEXT NOT NULL,
    days REAL DEFAULT 1.0,
    reason TEXT,
    designated_by TEXT,  -- Admin username
    designated_at TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',  -- PENDING, CONFIRMED, CANCELLED
    UNIQUE(employee_num, year, designated_date)
);
```

- [ ] Crear 5 tests

**Verificación:**
- [ ] Tests pasan (5/5)
- [ ] Endpoint accesible solo para admin
- [ ] Notificación se envía
- [ ] Datos se registran en audit_log

---

### R#3: Carry-Over Auditoría

**Responsable:** Backend Senior
**Esfuerzo:** 2 horas
**Deadline:** 27 Enero 2026

#### Subtareas:

- [ ] Crear tabla carryover_audit

```sql
CREATE TABLE carryover_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_year INTEGER NOT NULL,
    to_year INTEGER NOT NULL,
    employee_num TEXT NOT NULL,
    days_carried_over REAL,
    days_expired REAL,
    days_capped REAL,  -- Si se cap en 40
    executed_at TEXT NOT NULL,
    executed_by TEXT,
    executed_reason TEXT,
    UNIQUE(from_year, to_year, employee_num)
);
```

- [ ] Modificar process_year_end_carryover()

```python
def process_year_end_carryover(from_year: int, to_year: int, performed_by: str = "system"):
    # ... código existente ...

    # Agregar: registrar en carryover_audit
    for emp in employees_with_balance:
        c.execute('''
            INSERT INTO carryover_audit
            (from_year, to_year, employee_num, days_carried_over, days_expired,
             executed_at, executed_by, executed_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (from_year, to_year, emp_num, carry_over, days_expired,
              datetime.now().isoformat(), performed_by, 'Annual carryover process'))

        # Si hay expiración, notificar
        if days_expired > 0:
            send_notification(
                employee_num=emp_num,
                type='days_expired',
                message_ja=f"{days_expired}日が失効しました",
                message_es=f"Se le han vencido {days_expired} días"
            )
```

- [ ] Crear 3 tests

**Verificación:**
- [ ] Tests pasan (3/3)
- [ ] Expiración se registra
- [ ] Notificaciones se envían
- [ ] Datos auditables

---

### Validación y Testing

**Responsable:** QA Lead
**Esfuerzo:** 8 horas
**Deadline:** 29 Enero 2026

- [ ] Escribir 20+ tests nuevos

```python
# Archivo: tests/test_compliance_remediation.py

class TestAuditLogIntegration:
    # 5 tests

class TestOfficialLeaveDesignation:
    # 8 tests

class TestCarryoverAudit:
    # 5 tests

class TestInputValidation:
    # 4 tests
```

- [ ] Ejecutar suite completa

```bash
pytest tests/test_fiscal_year.py -v  # 31 tests existentes
pytest tests/test_lifo_deduction.py -v  # 20 tests existentes
pytest tests/test_compliance_remediation.py -v  # 22 tests nuevos
# Total: 73 tests
```

- [ ] Verificar cobertura

```bash
pytest tests/ --cov=services/fiscal_year --cov-report=html
# Objetivo: > 95% cobertura
```

- [ ] Testing manual

- [ ] Testing en staging

**Verificación Final:**
- [ ] Todos los tests pasan
- [ ] Cobertura > 95%
- [ ] Sin errores en staging
- [ ] Audit logs se registran correctamente

---

## CHECKLIST FASE 2 - ALTO (3-4 SEMANAS)

### R#4: Validación de Entrada

**Responsable:** Backend
**Esfuerzo:** 3 horas
**Deadline:** 10 Febrero 2026

```python
# En routes/dependencies.py o routes/fiscal.py

from pydantic import BaseModel, validator

class LifoDeductionRequest(BaseModel):
    employee_num: str
    days: float
    year: int

    @validator('days')
    def validate_days(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("days must be numeric")
        if v <= 0:
            raise ValueError("days must be positive")
        if v > 40:
            raise ValueError("cannot deduct more than 40 days")
        return v

    @validator('employee_num')
    def validate_employee(cls, v):
        emp = get_employee_by_num(v)
        if not emp:
            raise ValueError(f"Employee {v} not found")
        return v

    @validator('year')
    def validate_year(cls, v):
        if v < 2000 or v > 2099:
            raise ValueError("Invalid year")
        if v > date.today().year:
            raise ValueError("Cannot deduct from future year")
        return v
```

**Tests:**
- [ ] test_negative_days_rejected
- [ ] test_zero_days_rejected
- [ ] test_nonexistent_employee_rejected
- [ ] test_invalid_year_rejected
- [ ] test_future_year_rejected
- [ ] test_valid_request_accepted

---

### R#5: Idempotencia en Carry-Over

**Responsable:** Backend
**Esfuerzo:** 2 horas
**Deadline:** 10 Febrero 2026

```python
def process_year_end_carryover(from_year: int, to_year: int, performed_by: str = "system"):
    """
    Con protección contra duplicados
    """
    # NUEVO: Verificar que no se ejecutó
    c.execute('''
        SELECT COUNT(*) as count FROM carryover_audit
        WHERE from_year = ? AND to_year = ?
    ''', (from_year, to_year))

    if c.fetchone()['count'] > 0:
        raise ValueError(f"Carryover {from_year} → {to_year} already executed")

    # ... resto del código ...
```

**Tests:**
- [ ] test_carryover_idempotent_first_call
- [ ] test_carryover_idempotent_second_call_fails
- [ ] test_carryover_idempotent_records_check

---

### R#6: Validar Hire Date

**Responsable:** Backend
**Esfuerzo:** 2 horas
**Deadline:** 11 Febrero 2026

```python
def calculate_seniority_years(hire_date: str, reference_date: date = None) -> float:
    """
    Con validación de hire_date corrupta
    """
    if not hire_date:
        return 0.0

    try:
        hire = datetime.strptime(hire_date, '%Y-%m-%d').date()
        ref = reference_date or date.today()

        # NUEVO: Validaciones
        if hire > ref:
            logger.warning(f"Hire date {hire_date} is in future, returning 0")
            return 0.0

        days_since = (ref - hire).days

        if days_since < 0:
            logger.warning(f"Negative seniority for {hire_date}, returning 0")
            return 0.0

        if days_since > 130 * 365:  # 130 años
            logger.warning(f"Suspiciously old hire date {hire_date}, returning 0")
            return 0.0

        years = days_since / 365.25
        return round(years, 2)
    except (ValueError, TypeError):
        logger.warning(f"Invalid hire_date format: {hire_date}, returning 0")
        return 0.0
```

**Tests:**
- [ ] test_future_hire_date_returns_zero
- [ ] test_past_130_years_returns_zero
- [ ] test_valid_date_returns_seniority
- [ ] test_invalid_format_returns_zero

---

## CHECKLIST FASE 3 - MEDIO (5-8 SEMANAS)

### R#7 + R#8: Dashboard y Reportes

**Responsable:** Frontend + Backend
**Esfuerzo:** 20 horas
**Deadline:** 17 Abril 2026

- [ ] Dashboard de Compliance
  - % Compliant vs AT_RISK vs NON_COMPLIANT
  - Tendencias mensuales
  - Alertas activas
  - Gráficos de expiración

- [ ] Reportes automáticos
  - Reporte mensual de compliance
  - Exportación 年次有給休暇管理簿
  - Email automático a HR

- [ ] Integración Asistencia 80%
  - Validar asistencia en elegibilidad
  - Alertas si < 80%

---

## RESPONSABILIDADES POR ROL

### Backend Team

**Entrega Fase 1 (30 Enero):**
- ✓ Tabla fiscal_year_audit_log
- ✓ Registro en apply_lifo()
- ✓ Endpoint 5日 designación
- ✓ Tabla carryover_audit
- ✓ Validaciones básicas
- Tiempo: 20 horas

**Entrega Fase 2 (28 Febrero):**
- ✓ Validación Pydantic completa
- ✓ Idempotencia carry-over
- ✓ Validación hire_date
- ✓ Mecanismo reversión
- Tiempo: 13 horas

**Entrega Fase 3 (17 Abril):**
- ✓ API endpoints adicionales
- ✓ Reportes automáticos
- ✓ Integraciones
- Tiempo: 20 horas

**Total:** 53 horas de desarrollo

---

### QA Team

**Entrega Fase 1 (30 Enero):**
- ✓ 22 tests nuevos
- ✓ Testing manual
- ✓ Testing en staging
- Tiempo: 12 horas

**Entrega Fase 2 (28 Febrero):**
- ✓ Tests validación
- ✓ Tests idempotencia
- ✓ Regresión testing
- Tiempo: 8 horas

**Entrega Fase 3 (17 Abril):**
- ✓ E2E testing
- ✓ Testing compliance
- Tiempo: 10 horas

**Total:** 30 horas de testing

---

### Legal/Gestión

**Entrega Fase 1 (30 Enero):**
- ✓ Review auditoría
- ✓ Aprobación plan
- ✓ Comunicación stakeholders
- Tiempo: 4 horas

**Entrega Fase 2 (28 Febrero):**
- ✓ Validación legal
- ✓ Documentación
- Tiempo: 2 horas

**Entrega Fase 3 (17 Abril):**
- ✓ Review final
- ✓ Certificación compliance
- Tiempo: 3 horas

**Total:** 9 horas administrativas

---

## HERRAMIENTAS Y RECURSOS

### Desarrollo

```bash
# Base de datos
sqlite3 yukyu.db  # o PostgreSQL

# Testing
pytest tests/test_compliance_remediation.py -v
pytest tests/ --cov=services/fiscal_year

# Logging
logging.getLogger(__name__)

# Auditoría
fiscal_year_audit_log table
carryover_audit table
```

### Documentación

- COMPLIANCE_AUDIT_2026-01-17.md
- COMPLIANCE_RISK_MATRIX.md
- COMPLIANCE_SUMMARY.txt
- COMPLIANCE_ACTION_PLAN.md (este archivo)

### Comunicación

- Jira tickets (CRÍTICO-001 a ALTO-006)
- Slack channel: #compliance-audit
- Weekly sync: Compliance Remediation

---

## MÉTRICAS DE ÉXITO

### Fase 1 (30 Enero)

- [ ] ✅ 100% tests pasan (73/73)
- [ ] ✅ Cobertura > 95%
- [ ] ✅ Audit log registra deducción LIFO
- [ ] ✅ Endpoint 5日 funciona
- [ ] ✅ Carry-over audita expiración
- [ ] ✅ Documentación actualizada

### Fase 2 (28 Febrero)

- [ ] ✅ Validación Pydantic rechaza entrada inválida
- [ ] ✅ Carry-over no puede ejecutarse 2 veces
- [ ] ✅ Hire date > 130 años rechazada
- [ ] ✅ 100% tests pasan
- [ ] ✅ Reversión de deducción funciona

### Fase 3 (17 Abril)

- [ ] ✅ Dashboard compliance visible
- [ ] ✅ Reportes automáticos se envían
- [ ] ✅ Asistencia 80% validada
- [ ] ✅ 100% tests pasan
- [ ] ✅ Auditoría externa aprueba

---

## CRITERIOS DE ACEPTACIÓN

### Cada Feature

- [ ] Código escrito
- [ ] Tests escritos (80%+ cobertura)
- [ ] Code review aprobado
- [ ] Tests pasan en CI/CD
- [ ] Documentación actualizada
- [ ] Documentación legal completada

### Entire Phase

- [ ] Todos los tickets cerrados
- [ ] 100% test pass rate
- [ ] Cobertura > 95%
- [ ] Legal team revisa y aprueba
- [ ] Deployment a staging
- [ ] Final testing en staging

---

## ESCALATION PLAN

**Si algo va mal:**

1. **Issue técnico:** Reportar a Backend Lead
2. **Issue legal:** Reportar a Legal team
3. **Issue timeline:** Reportar a Gerencia (considerar deadline extension)
4. **Critical blocker:** Activar escalation committee (24h response)

---

## PRÓXIMAS REVISIONES

- **Semana 1:** Daily standup compliance
- **Semana 2:** Mid-phase review
- **Semana 4:** End of Fase 1 review
- **Semana 8:** End of Fase 2 review
- **Semana 12:** Final review (Fase 3)
- **17 Abril:** Final audit + certification

---

**Generado por:** Claude Code - Compliance Expert Agent
**Fecha:** 2026-01-17
**Última actualización:** 2026-01-17

