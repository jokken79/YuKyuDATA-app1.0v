---
description: "Gestión de vacaciones (有給休暇) - usar cuando se trabaje con datos de vacaciones, balances, solicitudes o cálculos de días"
---

# Skill: Gestión de Vacaciones YuKyuDATA

## Contexto del Dominio

Este proyecto gestiona vacaciones pagadas (有給休暇/yukyu) para empleados en Japón según la Ley de Normas Laborales (労働基準法).

## Reglas de Negocio Críticas

### Año Fiscal Japonés
- Período: Del día 21 del mes anterior al día 20 del mes actual
- Ejemplo: Abril = 21 marzo → 20 abril

### Otorgamiento de Días (Art. 39)
| Antigüedad | Días Otorgados |
|------------|----------------|
| 6 meses    | 10 días        |
| 1.5 años   | 11 días        |
| 2.5 años   | 12 días        |
| 3.5 años   | 14 días        |
| 4.5 años   | 16 días        |
| 5.5 años   | 18 días        |
| 6.5+ años  | 20 días (máx)  |

### Reglas de Carry-Over
- Máximo 2 años de validez
- Algoritmo LIFO: Días nuevos se consumen primero
- Balance máximo posible: 40 días (20 actuales + 20 anteriores)

### Obligación Legal 5日取得義務
- Empleados con 10+ días otorgados DEBEN usar mínimo 5 días/año
- Penalización por incumplimiento: ¥300,000 por empleado

## Archivos Clave

- `database.py`: Operaciones CRUD en tabla `employees`
- `excel_service.py`: Parseo de `有給休暇管理.xlsm`
- `fiscal_year.py`: Cálculos de año fiscal japonés
- `main.py`: Endpoints `/api/employees`, `/api/leave-requests`

## Tipos de Solicitud

```python
leave_types = {
    "full": 1.0,      # Día completo
    "half_am": 0.5,   # Media mañana
    "half_pm": 0.5,   # Media tarde
    "hourly": 0.125   # Por hora (1/8 día)
}
```

## Estados de Solicitud

```
PENDING → APPROVED → (puede revertirse)
        → REJECTED
        → CANCELLED
```

## Cálculos Importantes

```python
# Balance
balance = granted - used - expired

# Tasa de uso
usage_rate = (used / granted) * 100

# Costo estimado de solicitud
cost = days_requested * hourly_wage * 8
```
