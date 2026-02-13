# 📊 Yukyu Excel Master

**Maestro de Excel - Importación, Validación y Debugging de Archivos Excel**

## 📋 Descripción

Skill especializado para gestionar la importación y exportación de archivos Excel en Yukyu Pro. Maneja dos tipos de archivos:

1. **社員台帳 (DAICHO)** - Registro de empleados
2. **有給休暇管理 (YUKYU)** - Gestión de vacaciones pagadas

---

## ⚡ Comandos Disponibles

### `/excel-analyze`
Analiza la estructura de un archivo Excel antes de importar.

**Uso:**
```bash
/excel-analyze <filepath> [--type=daicho|yukyu|auto]
```

**Análisis realizado:**
- Hojas encontradas vs esperadas
- Columnas detectadas vs requeridas
- Formato de fechas detectado
- Encoding de caracteres
- Filas válidas vs inválidas

**Salida:**
```
📊 ANÁLISIS DE ARCHIVO EXCEL
═══════════════════════════════════════════════════

Archivo: 社員台帳_2024.xlsx
Tipo detectado: DAICHO (社員台帳)
Tamaño: 2.3 MB

📑 HOJAS ENCONTRADAS:
  ✅ DBGenzaiX (派遣社員) - 45 filas
  ✅ DBUkeoiX (請負社員) - 23 filas
  ✅ DBStaffX (スタッフ) - 12 filas
  ⚠️ DBOtherX (不明) - NO ESPERADA, será ignorada

📋 COLUMNAS DETECTADAS (DBGenzaiX):
  ✅ 社員№ (A) - 45/45 válidos
  ✅ 氏名 (B) - 45/45 válidos
  ✅ カナ (C) - 43/45 válidos (2 vacíos)
  ✅ 派遣先 (D) - 45/45 válidos
  ✅ 在職中 (E) - 45/45 válidos
  ✅ 入社日 (F) - 45/45 válidos
  ⚠️ 退社日 (G) - 8/45 válidos (37 vacíos - OK)

📅 FORMATO DE FECHAS:
  Detectado: Excel serial number
  Conversión: (date - 25569) × 86400 × 1000

✅ LISTO PARA IMPORTAR
```

---

### `/excel-validate`
Valida datos de Excel contra el schema esperado con reglas de negocio.

**Uso:**
```bash
/excel-validate <filepath> [--strict] [--output=console|csv]
```

**Validaciones realizadas:**

**Para DAICHO:**
- 社員№ único y no vacío
- 氏名 presente
- 派遣先 existente
- 入社日 formato válido
- 在職中 valor válido (在職中/退社)

**Para YUKYU:**
- 社員№ coincide con DAICHO
- 経過月 en valores válidos (6,18,30,42,54,66,78+)
- 付与数 ≤ 20 (máximo legal)
- 消化日数 ≤ 付与数
- Columnas 1-40 son fechas válidas
- 時効数 ≥ 0

**Salida:**
```
🔍 VALIDACIÓN DE DATOS EXCEL
═══════════════════════════════════════════════════

Archivo: 有給休暇管理_2024.xlsx
Tipo: YUKYU (有給休暇管理)

📊 RESUMEN DE VALIDACIÓN:
  Total filas procesadas: 156
  ✅ Válidas: 148 (94.9%)
  ⚠️ Con warnings: 6 (3.8%)
  ❌ Con errores: 2 (1.3%)

❌ ERRORES (bloquean importación):
1. Fila 45 (社員№: HM0099)
   Error: 消化日数 (25) > 付与数 (20)
   Acción: Corregir en Excel antes de importar

2. Fila 89 (社員№: ---)
   Error: 社員№ vacío
   Acción: Completar o eliminar fila

⚠️ WARNINGS (no bloquean, pero revisar):
1. Fila 23 (社員№: AB0012)
   Warning: 経過月 = 24 (no es valor estándar)
   Sugerencia: Debería ser 18 o 30

2. Fila 67 (社員№: CD0034)
   Warning: Fecha en columna 15 es futura (2025-12-25)
   Sugerencia: Verificar si es correcto

💡 RECOMENDACIÓN:
   Corregir 2 errores antes de importar.
   Los warnings serán importados con valores actuales.
```

---

### `/excel-preview`
Preview de datos que serán importados y merge resultante.

**Uso:**
```bash
/excel-preview <filepath> [--employee=ID] [--limit=10]
```

**Muestra:**
- Datos a importar (nuevo)
- Datos existentes (actual)
- Resultado del merge (final)
- Diferencias detectadas

**Salida:**
```
👁️ PREVIEW DE IMPORTACIÓN
═══════════════════════════════════════════════════

Empleado: 諸岡 貴士 (HM0006)
Cliente: 名護農業組合

┌────────────────────────────────────────────────────────┐
│ CAMPO              │ ACTUAL     │ EXCEL      │ FINAL  │
├────────────────────┼────────────┼────────────┼────────┤
│ 付与合計           │ 14日       │ 16日       │ 16日 ↑ │
│ 消化合計           │ 8日        │ 8日        │ 8日    │
│ 残高               │ 6日        │ 8日        │ 8日 ↑  │
│ yukyuDates.length  │ 8          │ 8          │ 8      │
└────────────────────────────────────────────────────────┘

🔄 PERÍODOS (periodHistory):

ACTUAL:
  1. 初回(6ヶ月): 10日付与, 6日消化, 4日残 [EXPIRADO]
  2. 1年6ヶ月: 11日付与, 2日消化, 9日残 [VIGENTE]

NUEVO (Excel):
  1. 初回(6ヶ月): 10日付与, 6日消化, 4日残 [EXPIRADO]
  2. 1年6ヶ月: 11日付与, 2日消化, 9日残 [VIGENTE]
  3. 2年6ヶ月: 12日付与, 0日消化, 12日残 [NUEVO] ✨

📊 IMPACTO:
  - Se agregará nuevo período (2年6ヶ月)
  - Balance aumentará de 6日 a 8日
  - Sin conflictos de fechas detectados
```

---

### `/excel-debug`
Debuggear problemas específicos de importación.

**Uso:**
```bash
/excel-debug <issue-type> [--employee=ID]
```

**Tipos de problemas:**
- `dates` - Problemas con fechas
- `periods` - Problemas con períodos
- `merge` - Problemas de merge
- `encoding` - Problemas de encoding
- `columns` - Columnas faltantes

**Salida (dates):**
```
🔧 DEBUG: PROBLEMAS DE FECHAS
═══════════════════════════════════════════════════

Empleado: HM0006 (諸岡 貴士)

📅 ANÁLISIS DE COLUMNAS DE FECHAS (1-40):

Columna 1: 45321 → 2024-01-15 ✅
Columna 2: 45322 → 2024-01-16 ✅
Columna 3: "2024/01/17" → 2024-01-17 ✅ (string parsed)
Columna 4: "15-Jan" → ERROR ❌
  Problema: Formato no reconocido
  Solución: Usar formato YYYY-MM-DD o número Excel

Columna 15: 45654:half → 2024-12-13 (半日) ✅
Columna 16: (vacío) → ignorado ✅

📊 RESUMEN:
  Fechas válidas: 14
  Fechas con error: 1
  Fechas de medio día: 2
  Columnas vacías: 25

💡 SOLUCIÓN RECOMENDADA:
  Cambiar celda D4 de "15-Jan" a "2024-01-15" o 45307
```

---

### `/excel-export`
Exporta datos actuales a formato Excel con todos los períodos.

**Uso:**
```bash
/excel-export [--type=full|summary|compliance] [--filter=active|all]
```

**Tipos de exportación:**

**full**: Formato idéntico al archivo YUKYU original
```
社員№ | 氏名 | 経過月 | 付与数 | 消化日数 | 残高 | 時効 | 1 | 2 | ... | 40
```

**summary**: Resumen por empleado
```
社員№ | 氏名 | 派遣先 | 入社日 | 現在付与 | 現在消化 | 現在残高 | 履歴付与 | 履歴消化
```

**compliance**: Reporte de cumplimiento 39条
```
社員№ | 氏名 | 派遣先 | 付与数 | 消化日数 | 不足日数 | 期限 | リスク
```

**Salida:**
```
📤 EXPORTACIÓN A EXCEL COMPLETADA
═══════════════════════════════════════════════════

Archivo generado: yukyu_export_2025-01-09.xlsx
Ubicación: /downloads/

📊 CONTENIDO:
  Hojas creadas: 3
  ├─ 派遣社員 (45 empleados)
  ├─ 請負社員 (23 empleados)
  └─ スタッフ (12 empleados)

  Total filas: 156 (períodos individuales)
  Fechas exportadas: 847

✅ Compatible con reimportación
✅ Incluye aprobaciones locales
✅ Formato idéntico a origen
```

---

## 🔧 Integración con ExcelSync

El Excel Master se integra con el componente ExcelSync:

```typescript
// ExcelSync.tsx - Progress tracking
const progressStages = [
  { name: '読込', percent: 25 },   // Lectura
  { name: '解析', percent: 50 },   // Análisis
  { name: '処理', percent: 75 },   // Procesamiento
  { name: '保存', percent: 100 }   // Guardado
];
```

---

## 📋 Estructura de Archivos Esperada

### DAICHO (社員台帳)

| Hoja | Categoría | Columnas Requeridas |
|------|-----------|---------------------|
| DBGenzaiX | 派遣社員 | 社員№, 氏名, カナ, 派遣先, 在職中, 入社日 |
| DBUkeoiX | 請負社員 | (mismo) |
| DBStaffX | スタッフ | (mismo) |

### YUKYU (有給休暇管理)

| Hoja | Categoría | Columnas Requeridas |
|------|-----------|---------------------|
| 作業者データ 有給 | 派遣社員 | 社員№, 氏名, 経過月, 有給発生日, 付与数, 消化日数, 期末残高, 時効数, 1-40 |
| 請負 | 請負社員 | (mismo) |

---

## 🔄 Lógica de Merge

### Primera Sincronización (first_sync)
```
Excel → Local (importar todo)
```

### Re-sincronización (re_sync)
```
Excel + Local Approvals → Merged
- Fechas de Excel son base
- Aprobaciones locales se preservan
- Conflictos se reportan
```

---

## ⚠️ Problemas Comunes

### 1. Encoding de Caracteres
```
Problema: 諸岡 aparece como ????
Solución: Guardar Excel como UTF-8 o usar encoding original
```

### 2. Formato de Fechas
```
Problema: Columnas 1-40 no se parsean
Solución: Usar número Excel (ej: 45321) o YYYY-MM-DD
```

### 3. Columnas con Espacios
```
Problema: Columna "1 " (con espacio) no se detecta
Solución: El sistema busca "1" y "1 " automáticamente
```

### 4. 経過月 Inválido
```
Problema: 経過月 = 15 (no es valor estándar)
Solución: Usar valores válidos: 6, 18, 30, 42, 54, 66, 78+
```

---

## 📄 Licencia

MIT - Uso libre para empresas
