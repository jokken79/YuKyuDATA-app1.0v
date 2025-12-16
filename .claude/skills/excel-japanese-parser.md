---
description: "Parseo de Excel japonés - usar cuando se trabaje con archivos Excel, columnas japonesas, o sincronización de datos"
---

# Skill: Parser de Excel Japonés

## Archivos Excel del Sistema

### 1. Vacaciones: `有給休暇管理.xlsm`
- **Ubicación**: `D:\YuKyuDATA-app\有給休暇管理.xlsm`
- **Contenido**: Resumen de vacaciones por empleado y año
- **Columnas de fechas individuales**: R-BE (días específicos de uso)

### 2. Registro de Empleados: `【新】社員台帳(UNS)T　2022.04.05～.xlsm`
- **Ubicación**: `D:\YuKyuDATA-app\【新】社員台帳(UNS)T　2022.04.05～.xlsm`
- **Hojas**:
  - `DBGenzaiX`: Empleados en dispatch (派遣)
  - `DBUkeoiX`: Empleados por contrato (請負)

## Mapeo de Columnas (Fuzzy Matching)

### Campos Comunes
```python
column_mappings = {
    'employee_num': ['社員№', '従業員番号', '社員番号', '番号', 'id', 'no', '№'],
    'name': ['氏名', '名前', 'name'],
    'kana': ['フリガナ', 'ふりがな', 'カナ'],
    'haken': ['派遣先', '所属', '部署', '現場'],
    'granted': ['付与日数', '付与', '総日数', '有給残日数'],
    'used': ['使用日数', '使用', '消化'],
    'year': ['年度', '年', 'year', '対象年度'],
    'status': ['現在状態', '状態', 'ステータス'],
    'birth_date': ['生年月日', '誕生日'],
    'gender': ['性別'],
    'nationality': ['国籍'],
    'hourly_wage': ['時給', '給与']
}
```

## Lógica de Detección de Headers

```python
def find_header_row(sheet, max_rows=10):
    """Busca fila con '氏名' o '名前' en primeras 10 filas"""
    for row_idx in range(1, max_rows + 1):
        for cell in sheet[row_idx]:
            if cell.value and ('氏名' in str(cell.value) or '名前' in str(cell.value)):
                return row_idx
    return None
```

## Reglas de Filtrado

### Empleados Válidos
- DEBE tener nombre (氏名) no vacío
- DEBE tener número de empleado

### Registros a Ignorar
- Filas sin nombre → Probablemente headers duplicados
- `haken == "高雄工業 本社"` → Sede principal (no dispatch)

## Parseo de Fechas Individuales (Columnas R-BE)

Las columnas R a BE contienen fechas específicas de uso de vacaciones:
```python
# Formato esperado: datetime o string "YYYY-MM-DD"
for col_idx in range(17, 57):  # R=17, BE=56
    cell_value = row[col_idx]
    if cell_value and isinstance(cell_value, datetime):
        use_dates.append(cell_value.strftime('%Y-%m-%d'))
```

## Funciones del Servicio

| Función | Propósito |
|---------|-----------|
| `parse_excel_file()` | Datos de vacaciones (resumen) |
| `parse_genzai_sheet()` | Empleados dispatch |
| `parse_ukeoi_sheet()` | Empleados contrato |
| `parse_yukyu_usage_details()` | Fechas individuales |

## Manejo de Errores Comunes

```python
# Valor vacío o None
value = str(row[col]) if col != -1 and row[col] else "Unknown"

# Conversión numérica segura
try:
    granted = float(row[cols['granted']]) if cols['granted'] != -1 else 0.0
except (ValueError, TypeError):
    granted = 0.0

# Fechas
try:
    date = cell.value.strftime('%Y-%m-%d') if hasattr(cell.value, 'strftime') else str(cell.value)
except:
    date = None
```
