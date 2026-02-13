# Documentación de Lógica de Parseo Excel (YuKyuDATA)

Este documento detalla la lógica técnica utilizada por `services/excel_service.py` para extraer, limpiar y estructurar los datos desde los archivos Excel de gestión de vacaciones (`YukyuKanri`).

## 1. Visión General
El sistema utiliza un enfoque híbrido para el procesamiento de Excel:
- **`openpyxl`**: Para la extracción de datos de resumen y metadatos, permitiendo una lectura celda por celda y detección dinámica de cabeceras.
- **`pandas`**: Para el procesamiento masivo de los detalles de uso (calendario), aprovechando su velocidad y capacidad de manipulación de datos matriciales.

## 2. Hojas Procesadas (Mapper v2.0)

| Hoja Objetivo | Nombre Real en Excel | Estrategia de Parseo |
| :--- | :--- | :--- |
| **Resumen** | `作業者データ　有給` | Header en Fila 5. Datos empiezan Fila 6 (se filtra fila anómala 6 si contiene texto en columnas numéricas). |
| **Genzai (Dispatch)** | `Sheet1` | Header en Fila 3. Datos empiezan Fila 4. |
| **Ukeoi (Contract)** | `請負` | Header en Fila 4. Datos empiezan Fila 5. |
| **Staff** | `Sheet1` (Compartido) o `DBStaffX` | *Actualmente se busca DBStaffX por compatibilidad, pero staff suele estar mezclado en Genzai en la práctica.* |

---

## 3. Lógica de Parseo: Detalle de Uso (Reglas Estrictas)

La extracción de fechas individuales (Cols R a BE) aplica las siguientes reglas de negocio jerárquicas:

| Prioridad | Patrón (Regex/Match) | Acción | Días | Tipo |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `"*"` o `"＊"` | **IGNORAR**. Padding visual. | 0 | - |
| 2 | `/^\d+日間$/` (ej: "7日間") | **IGNORAR**. Marcador de rango. | 0 | - |
| 3 | Contiene `"消滅"` | Extraer fecha, marcar como expirado. | **0.0** | `expired` |
| 4 | Contiene `"半"`, `"0.5"`, `"AM"`, `"PM"` | Extraer fecha (limpiar texto), marcar medio día. | **0.5** | `half` |
| 5 | Contiene `"2h"`, `"2時間"` | Extraer fecha, marcar por horas. | **0.25** | `hourly` |
| 6 | Contiene `"支給"` (Pago) | Extraer fecha antes del paréntesis `(X/X支給)`. | **1.0** | `full` |
| 7 | Fecha Válida | Parseo estándar de fecha. | **1.0** | `full` |

### Notas sobre Fechas
- **Limpieza**: Se eliminan textos entre paréntesis `(...)` y `（...）` antes de parsear si contienen "支給".
- **Año 1900**: Las fechas que Excel parsea como año 1900 se descartan (ruido serial).


---

## 5. Lógica de Parseo: Hojas Maestras (Genzai / Ukeoi / Staff)

Para estas hojas, el sistema es más estricto y espera una estructura de columnas posicional específica, ya que suelen ser exportaciones de sistema.

### DBGenzaiX (Dispatch)
- **Fila de inicio de datos**: Fila 2.
- **Columnas Clave**:
    - Col 1: `社員№`
    - Col 3: `派遣先` (Empresa destino)
    - Col 7: `氏名` (Nombre)
    - Col 13: `時給` (Salario por hora)

### DBUkeoiX (Contract)
- **Fila de inicio de datos**: Fila 2.
- **Columnas Clave**:
    - Col 1: `社員№`
    - Col 2: `請負業務` (Tarea/Proyecto)
    - Col 3: `氏名` (Nombre)

### DBStaffX (Internal Staff)
- **Fila de inicio de datos**: Fila 2.
- **Columnas Clave**:
    - Col 1: `社員№`
    - Col 3: `氏名` (Nombre)
    - Col 15: `入社日` (Fecha de Contratación)
    - Col 16: `退社日` (Fecha de Salida)

---

## 6. Limitaciones Conocidas

1.  **Dependencia Posicional en Detalles**: La extracción de fechas individuales asume que las columnas de calendario comienzan después de la información del empleado (aprox. columna 17). Si se insertan columnas nuevas al principio de la hoja `作業者データ`, este rango podría necesitar ajuste.
2.  **Año por Defecto**: Si una fila no tiene fecha de concesión explícita ni columna de año, el sistema asigna el **año actual** del servidor. Esto podría ser inexacto para cargas masivas de datos históricos muy antiguos si no tienen la columna `年度`.
