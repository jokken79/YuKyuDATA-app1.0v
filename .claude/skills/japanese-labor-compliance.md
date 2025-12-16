---
description: "Cumplimiento ley laboral japonesa (労働基準法) - usar cuando se trabaje con obligaciones legales, 5日取得義務, o auditorías"
---

# Skill: Cumplimiento Ley Laboral Japonesa

## Marco Legal

**Ley**: 労働基準法 (Ley de Normas Laborales)
**Artículo principal**: Art. 39 - Vacaciones pagadas anuales

## Obligación 5日取得義務 (Desde 2019)

### Regla
- Empleados con **10+ días otorgados** DEBEN usar **mínimo 5 días/año**
- El empleador es responsable de asegurar el cumplimiento

### Penalización
- **¥300,000** por cada empleado que no cumpla
- Puede resultar en inspección laboral

### Cálculo de Cumplimiento
```python
def check_compliance(employee):
    if employee['granted'] >= 10:
        return employee['used'] >= 5
    return True  # No aplica si tiene menos de 10 días
```

## Endpoints de Compliance

```
GET /api/compliance/check
GET /api/compliance/at-risk
GET /api/compliance/summary
```

## Estados de Cumplimiento

| Estado | Color | Significado |
|--------|-------|-------------|
| `compliant` | Verde | ≥5 días usados |
| `on_track` | Azul | Progreso adecuado |
| `at_risk` | Amarillo | Necesita atención |
| `non_compliant` | Rojo | No cumple obligación |

## Período de Retención de Registros

- **Mínimo 3 años** según Art. 109
- La tabla `employees` mantiene histórico por año
- Función `delete_old_yukyu_records()` respeta este período

## Año Fiscal de Otorgamiento

El período de referencia para los 5 días NO es el año calendario:
- Se cuenta desde la **fecha de otorgamiento** del empleado
- Usualmente coincide con aniversario de contratación

## Ledger Anual (年次有給休暇管理簿)

Documento obligatorio que debe contener:
1. Días otorgados (付与日数)
2. Días usados (使用日数)
3. Fechas de uso (取得日)
4. Balance restante (残日数)

### Exportación
```
POST /api/export/excel
{
    "report_type": "ledger",
    "year": 2024
}
```

## Agente de Compliance

El archivo `agents/compliance.py` implementa:
- Verificación automática de 5日取得義務
- Alertas proactivas para empleados en riesgo
- Generación de reportes de cumplimiento

## Alertas Recomendadas

| Días Restantes del Año | Días Usados | Alerta |
|------------------------|-------------|--------|
| >6 meses | <2 | Aviso temprano |
| 3-6 meses | <3 | Atención requerida |
| <3 meses | <4 | Urgente |
| <1 mes | <5 | Crítico |

## Excepciones Legales

La obligación NO aplica a:
- Empleados con menos de 6 meses de antigüedad
- Empleados a tiempo parcial con <10 días otorgados
- Días tomados por enfermedad certificada (別途)
