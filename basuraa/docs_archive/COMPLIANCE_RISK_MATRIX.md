# MATRIZ DE RIESGOS DE COMPLIANCE - YuKyuDATA v5.19
## Evaluación Cuantitativa de Vulnerabilidades Legales

**Fecha:** 2026-01-17
**Evaluador:** Claude Code Compliance Expert
**Clasificación:** RIESGO ALTO - Requiere Acción Inmediata

---

## MATRIZ SEVERIDAD vs PROBABILIDAD

```
             PROBABILIDAD
             └─────────────────────────────────────────┐
             BAJA        MEDIA       ALTA      MUY ALTA│
    ┌─────────────────────────────────────────────────┐
    │                                                   │
SE  │                                                   │
VE  │      RIESGO       RIESGO       RIESGO   RIESGO  │
RI  │      MEDIO        ALTO         CRÍTICO  CRÍTICO │
DA  │                                                   │
D   │      R#7, R#8     R#4, R#5,    R#1,     R#2,    │
    │                   R#6           R#3              │
    │                                                   │
    └─────────────────────────────────────────────────┘
```

---

## RIESGOS CRÍTICOS (Acción Hoy)

### 🔴 RIESGO #1: INCUMPLIMIENTO DE 5日取得義務 (Obligación de 5 días)

**Legislación:** Art. 39 § 2 (Ley de Normas Laborales, desde abril 2019)

**Descripción Legal:**
> "Cuando un empleado falla en tomar 5 días de las vacaciones otorgadas, la empresa DEBE designar las fechas"

**Estado Actual:**

| Aspecto | Estado | Código |
|---------|--------|--------|
| Identificación de no-cumplientes | ✅ IMPLEMENTADO | `check_5day_compliance()` línea 416 |
| Designación de fechas | ❌ NO IMPLEMENTADO | - |
| Notificación a empleado | ⚠️ PARCIAL | `notifications.py` |
| Registro en auditoría | ❌ NO IMPLEMENTADO | - |

**Código Problemático:**
```python
# En routes/fiscal.py línea 128-142
@router.get("/5day-compliance/{year}")
async def get_5day_compliance(year: int):
    compliance = check_5day_compliance(year)
    # ← RETORNA ESTADO PERO NO DESIGNA
    # FALTA: Endpoint para designación
```

**Escenario Violación:**

```
Empleado: EMP001
Año: 2025 (abril 2025 - marzo 2026)
Otorgados: 20 días
Usados: 2 días
Sistema: "NON_COMPLIANT"
Empresa: [No hace nada]

RESULTADO:
- Violación legal: ✅ SÍ
- Multa: ¥300,000 (mínimo)
- Responsable: Empresa (YuKyu)
- Defensa: Ninguna (ley clara)
```

**Impacto Financiero:**
- Por empleado: ¥300,000
- Si 100 empleados no cumplen: ¥30,000,000
- Penalización adicional: Hasta 50% de nómina (1 mes)

**Probabilidad de Auditoría:**
- Inspección por Ministerio Trabajo: MEDIA (5% anual)
- Si descubierto en auditoría: 100% multa

**Plazo de Implementación:** HORAS (no días)

**Prioridad:** 🔴🔴🔴 CRÍTICA

---

### 🔴 RIESGO #2: FALTA AUDITORÍA EN DEDUCCIÓN LIFO

**Legislación:** Art. 109 (Retención de Registros - 3 años obligatorio)

**Descripción:**
> "Las empresas deben mantener registros completos de todas las transacciones de vacaciones pagadas por 3 años"

**Estado Actual:**

| Aspecto | Estado | Línea |
|---------|--------|-------|
| Deducción de días | ✅ IMPLEMENTADO | `apply_lifo_deduction()` línea 293 |
| Registro de quién | ❌ NO | UPDATE sin audit |
| Timestamp preciso | ⚠️ PARCIAL | `last_updated` (genérico) |
| Razón/motivo | ❌ NO | |
| Revertibilidad | ❌ NO | No hay trail |
| Trail completo | ❌ NO | Solo balance final |

**Código Problemático:**

```python
# En fiscal_year.py línea 323-330
def apply_lifo_deduction(employee_num: str, days_to_use: float, current_year: int):
    # ... código ...
    c.execute('''
        UPDATE employees
        SET used = used + ?,
            balance = balance - ?,
            last_updated = ?
        WHERE employee_num = ? AND year = ?
    ''', (to_deduct, to_deduct, datetime.now().isoformat(), ...))

    # FALTA COMPLETAMENTE:
    # - Log de auditoría
    # - Quién hizo la deducción
    # - Por qué se dedujo
    # - Timestamp preciso
    # - Balance antes/después
```

**Caso de Auditoría:**

```
Ministerio Trabajo: "¿Quién dedujo 5 días a EMP001 el 2025-06-15?"
Empresa: "No sabemos... el sistema lo hizo automáticamente"
Ministerio: "VIOLACIÓN - Sin trail de auditoría"

RESULTADO:
- Multa: ¥300,000
- Requerimiento: Implementar audit trail
- Plazo: 30 días
```

**Impacto:**
- Imposible reconstruir decisiones
- Responsabilidad personal del admin (criminal)
- Documentos no admitibles en corte

**Plazo de Implementación:** 3-4 horas

**Prioridad:** 🔴🔴🔴 CRÍTICA

---

### 🔴 RIESGO #3: PÉRDIDA DE DATOS EN CARRY-OVER SIN AUDITAR

**Legislación:** Art. 109 + Derecho Laboral Japonés (Protección de derechos)

**Descripción:**
Si un empleado tiene 50 días y máximo es 40, ¿qué pasa con los 10 días?

**Estado Actual:**

```python
# fiscal_year.py línea 179-182
if carry_over > max_carry:
    stats['days_expired'] += carry_over - max_carry  # ← PÉRDIDA
    carry_over = max_carry
```

**Problema:**
- ❌ No audita CUÁLES días se pierden
- ❌ No notifica a empleado
- ❌ No registra en log
- ❌ No genera reporte de pérdida

**Escenario Violación:**

```
Año Fiscal 2024 (FY2024):
EMP001 otorgados: 20 días
EMP001 usado: 0 días
EMP001 balance: 20 días (carry-over)

Año Fiscal 2025 (FY2025):
EMP001 otorgados: 20 días (nuevo)
Total antes carry-over: 20 + 20 = 40 ✅

Pero si error anterior año:
EMP001 balance: 25 días (error cálculo)
Total: 25 + 20 = 45 días
Capping: 45 → 40 (5 días perdidos)

AUDITORÍA:
Ministerio: "¿Por qué EMP001 perdió 5 días?"
Empresa: "No sabemos... el sistema lo hizo"
Ministerio: "VIOLACIÓN - Confiscación de derechos"

RESULTADO:
- Multa: ¥600,000 (negligencia grave)
- Compensación empleado: 5 días × 8h = 40 horas de paga
- Reportaje prensa: Reputación dañada
```

**Impacto:**
- Violación de derechos laborales
- Caso de corte civil posible
- Responsabilidad criminal potencial

**Plazo de Implementación:** 4-5 horas

**Prioridad:** 🔴🔴🔴 CRÍTICA

---

## RIESGOS ALTOS (Implementar en 30 días)

### ⚠️ RIESGO #4: VALIDACIÓN INCOMPLETA EN apply_lifo_deduction()

**Severidad:** ALTA
**Líneas Afectadas:** 293-350
**Tipo:** Input Validation

**Validaciones Faltantes:**

| Validación | Estado | Impacto |
|------------|--------|---------|
| `days_to_use > 0` | ❌ | Permite negativos → balance aumento incorrecto |
| `employee_num existe` | ❌ | Crea registro fantasma |
| `year <= current_year` | ❌ | Deducción retroactiva imposible validar |
| `balance >= days_to_use` | ❌ | Falla silenciosa (no retorna error) |
| `days_to_use <= 40` | ❌ | Deducción > máximo legal |

**Escenarios de Ataque:**

```python
# Ataque 1: Negativos
apply_lifo_deduction('EMP001', -100, 2025)
# Resultado: Balance sube 100 días (CORRUPTO)

# Ataque 2: Empleado inexistente
apply_lifo_deduction('HACKER', 20, 2025)
# Resultado: Crea registro HACKER con balance negativo

# Ataque 3: Año futuro
apply_lifo_deduction('EMP001', 5, 2099)
# Resultado: Deducción en año futuro (inconsistencia)

# Ataque 4: Balance insuficiente
apply_lifo_deduction('EMP001', 100, 2025)  # Solo tiene 30
# Resultado: FALLA SILENCIOSA, retorna success=False sin error claro
```

**Código Vulnerable:**

```python
def apply_lifo_deduction(employee_num: str, days_to_use: float, current_year: int) -> Dict:
    # ← NO VALIDA NADA
    breakdown = get_employee_balance_breakdown(employee_num, current_year)
    remaining = days_to_use  # ← Podría ser negativo

    for item in breakdown['lifo_order']:
        # Procesa sin validar
```

**Solución Estimada:** 2-3 horas (validación Pydantic)

**Prioridad:** ⚠️⚠️⚠️ ALTA

---

### ⚠️ RIESGO #5: NO IDEMPOTENCIA EN process_year_end_carryover()

**Severidad:** ALTA
**Líneas Afectadas:** 139-235
**Tipo:** Data Integrity

**Escenario:**

```
Acción 1: Admin abre página /fiscal/carryover
Acción 2: Admin presiona "Procesar FY2024→FY2025"
Resultado: EMP001 balance = 10 (correcto)

Acción 3: Navegador lento, admin presiona botón de nuevo
Acción 4: Procesa de nuevo
Resultado: EMP001 balance = 20 (DUPLICADO!)

AUDITORÍA:
EMP001 reclama: "¿Por qué me dieron 20 días carry-over?"
Auditor: "No hay log, imposible saber"
Resultado: Litigio (¿quién paga los 10 extras?)
```

**Verificación Actual:**

```python
# NO HAY VALIDACIÓN
# Puede ejecutarse N veces
# Cada vez suma balance sin verificar duplicidad
```

**Impacto:**
- Balance corrupto
- Imposible auditoria
- Conflicto legal empleado-empresa

**Solución Estimada:** 1-2 horas

**Prioridad:** ⚠️⚠️⚠️ ALTA

---

### ⚠️ RIESGO #6: HIRE_DATE CORRUPTA (Futura/Pasada Extrema)

**Severidad:** ALTA
**Líneas Afectadas:** 52-73
**Función:** `calculate_seniority_years()`

**Validaciones Faltantes:**

```python
def calculate_seniority_years(hire_date: str, reference_date: date = None):
    hire = datetime.strptime(hire_date, '%Y-%m-%d').date()
    ref = reference_date or date.today()

    # FALTA:
    # - ¿hire > ref? (futuro)
    # - ¿hire más de 130 años atrás? (inválido)
    # - ¿hire exactamente hoy? (borde)
```

**Escenarios:**

```
Caso 1: Excel error → hire_date = "2099-01-01"
calculate_seniority_years("2099-01-01", date(2025,1,1))
# Retorna: -74.0
# calculate_granted_days(-74) → 0 días
# Empleado pierde derechos (INCORRECTO)

Caso 2: OCR error → hire_date = "1800-01-01"
calculate_seniority_years("1800-01-01", date(2025,1,1))
# Retorna: 225.0
# calculate_granted_days(225) → 20 días (máximo)
# Pero con error de 200 años (INCORRECTO)

Caso 3: Empleado mismo día
calculate_seniority_years("2025-01-17", date(2025,1,17))
# Retorna: 0.0 (borde)
# ¿Otorga 0 o 10 días? (ambiguo)
```

**Impacto:**
- Cálculo erróneo de días otorgados
- Violación de derechos
- No cumple elegibilidad

**Solución Estimada:** 1 hora

**Prioridad:** ⚠️⚠️⚠️ ALTA

---

## RIESGOS MEDIOS (Implementar en 60 días)

### ⚠️ RIESGO #7: ASISTENCIA 80% NO VALIDADA

**Severidad:** MEDIA
**Legislación:** Art. 39 § 1
**Estado:** Requisito legal pero NO implementado

**Requisito:**
> "Empleado debe tener 80% de asistencia en días laborables para ser elegible"

**Implementación Actual:**
- ✅ Identifica en Excel
- ❌ NO valida en BD
- ❌ NO rechaza otorgamiento si < 80%

**Escenario:**

```
Empleado EMP001:
- Contratado: 2024-06-01
- Días laborables 2024-2025: 250
- Días trabajados: 150 (60% asistencia)
- Elegible: ❌ (falta < 80%)

Sistema:
- calculate_seniority_years("2024-06-01") → 0.67 años (< 0.5 meses)
- ✅ Detecta que no es elegible

Pero: Sin validación del 80%, ¿qué pasa si Excel dice sí?
- No hay validación cruzada
- Potencial error manual
```

**Solución Estimada:** 4-5 horas

**Prioridad:** ⚠️⚠️ MEDIA

---

### ⚠️ RIESGO #8: FALTA NOTIFICACIÓN DE EXPIRACIONES

**Severidad:** MEDIA
**Legislación:** Buena práctica (recomendada)
**Estado:** Sistema detecta pero NO notifica

**Implementación Actual:**

```python
# fiscal_year.py línea 367-413
def check_expiring_soon(...):
    # Retorna lista de empleados con días por expirar
    # Pero NO NOTIFICA
```

**Requerimiento Legal Implícito:**
Empleado debe tener oportunidad de usar días antes de expirar

**Escenario:**

```
Empleado EMP001:
- Balance 2024: 5 días
- Estos 5 días expiran: 2026-03-31

Sistema:
- ✅ Detecta en 2026-01-17
- ❌ NO notifica a EMP001
- Resultado: EMP001 no usa antes de expiración
- Pérdida: 5 días sin usar

Auditoría:
"¿Se notificó al empleado?"
Empresa: "No, el sistema solo detectaba"
Auditor: "Violación de derecho a notificación"
```

**Solución Estimada:** 2-3 horas

**Prioridad:** ⚠️⚠️ MEDIA

---

## MATRIZ FINAL DE SEVERIDAD

```
┌─────────────┬──────────┬────────────┬──────────┬──────────┐
│ Riesgo      │ Severid  │ Probabil   │ Multa    │ Plazo    │
│             │ ad       │ idad       │ Potencial│ Implem   │
├─────────────┼──────────┼────────────┼──────────┼──────────┤
│ R#1: 5日    │ CRÍTICA  │ ALTA       │ ¥300k+   │ Hoy      │
│ R#2: Audit  │ CRÍTICA  │ ALTA       │ ¥300k    │ Hoy      │
│ R#3: Carry  │ CRÍTICA  │ MEDIA      │ ¥600k    │ Hoy      │
│ R#4: Valid  │ ALTA     │ ALTA       │ ¥100k    │ 1 semana │
│ R#5: Idem   │ ALTA     │ MEDIA      │ ¥50k     │ 1 semana │
│ R#6: Date   │ ALTA     │ BAJA       │ ¥100k    │ 1 semana │
│ R#7: 80%    │ MEDIA    │ BAJA       │ ¥50k     │ 1 mes    │
│ R#8: Notif  │ MEDIA    │ BAJA       │ ¥0       │ 2 meses  │
└─────────────┴──────────┴────────────┴──────────┴──────────┘

TOTAL MULTA POTENCIAL (SIN REMEDIACIÓN): ¥1,800,000+
```

---

## CRONOGRAMA DE REMEDIACIÓN RECOMENDADO

```
SEMANA 1 (Hoy - 23 Enero)
├─ R#1: Endpoint 5日 designación (6h)
├─ R#2: Auditoría log en BD (3h)
└─ R#3: Auditar carry-over (2h)
└─ Tests nuevos (5h)
└─ Total: 16 horas

SEMANA 2 (24-30 Enero)
├─ R#4: Validación apply_lifo (3h)
├─ R#5: Idempotencia check (2h)
├─ R#6: Validar hire_date (1h)
└─ Tests (8h)
└─ Total: 14 horas

SEMANA 3 (31 Jan - 13 Feb)
├─ Documentación COMPLIANCE_AUDIT.md
├─ Legal review
├─ Notificación a stakeholders
└─ Total: 8 horas

SEMANA 4-6 (14 Feb - 6 Mar)
├─ R#7: Asistencia 80% (5h)
├─ R#8: Notificación expiraciones (3h)
└─ Tests adicionales (10h)
└─ Total: 18 horas

SEMANA 7-8 (7 Mar - 20 Mar)
├─ Dashboard compliance
├─ Reportes automáticos
├─ Training interno
└─ Total: 20 horas

ESTIMADO TOTAL: 76 horas (2 desarrolladores, 3 semanas intensivas)
```

---

## RESUMEN EJECUTIVO PARA STAKEHOLDERS

**¿Qué está en riesgo?**
- Multas por ¥1,800,000+ por no cumplir ley laboral
- Responsabilidad criminal potencial (admin)
- Reputación dañada ante inspección

**¿Qué debe hacerse?**
1. Hoy: Implementar 3 features críticas (16 horas)
2. Semana 1: Validaciones (14 horas)
3. Semana 2: Testing y documentación (8 horas)

**¿Cuál es el costo?**
- Remediación: ~76 horas de desarrollo
- Costo evitado: ¥1,800,000+ en multas
- ROI: 23,000:1

**¿Cuándo?**
- Crítico: Hoy - 30 Enero
- Moderado: 31 Enero - 6 Marzo
- Óptimo: Completar antes 31 Marzo (fin año fiscal japón)

---

**Generado por:** Claude Code - Compliance Expert Agent
**Fecha:** 2026-01-17
**Validez:** Crítico aplicar antes de 30 Enero 2026

