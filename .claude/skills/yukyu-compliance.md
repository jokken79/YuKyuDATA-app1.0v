---
name: yukyu-compliance
description: Verifica el cumplimiento de la ley laboral japonesa de vacaciones (5 días obligatorios)
version: 1.0.0
---

# /yukyu-compliance - Verificar Cumplimiento Legal

Verifica el estado de cumplimiento de la obligación de 5 días de vacaciones según la ley laboral japonesa (労働基準法第39条).

## Verificaciones

### 1. Obligación de 5 Días

```bash
curl http://localhost:8000/api/compliance/5day?year=2025
```

**Respuesta esperada:**
```json
{
  "compliant": [...],      // Empleados que cumplen
  "non_compliant": [...],  // Empleados que NO cumplen (RIESGO)
  "warning": [...]         // Empleados cerca del límite
}
```

### 2. Vacaciones por Expirar

```bash
curl http://localhost:8000/api/expiring-soon?year=2025&threshold_months=3
```

### 3. Estado General

```bash
curl http://localhost:8000/api/employees?year=2025
```

## Criterios de Cumplimiento

| Estado | Criterio |
|--------|----------|
| ✅ Cumple | Usó ≥5 días |
| ⚠️ Warning | Usó 3-4 días, quedan ≥3 meses |
| ❌ No cumple | Usó <3 días O quedan <3 meses |

## Consecuencias de No Cumplimiento

- **Multa:** Hasta ¥300,000 por empleado
- **Inspección laboral:** Posible auditoría
- **Reputación:** Impacto en la empresa

## Acciones Recomendadas

1. Identificar empleados en riesgo
2. Planificar fechas de vacaciones
3. Notificar a supervisores
4. Documentar acciones tomadas
