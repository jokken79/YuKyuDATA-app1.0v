# Verificación Completa del Sistema

## ❗ IMPORTANTE: DEBES REINICIAR EL SERVIDOR

Los cambios que hice requieren que **reinicies el servidor** para que se carguen.

### Paso 1: Detener el servidor actual
- Si está corriendo con `start_app.bat`, cierra la ventana
- O presiona `Ctrl+C` en la terminal donde corre

### Paso 2: Iniciar el servidor nuevamente
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

O simplemente ejecuta:
```bash
start_app.bat
```

---

## ✅ Cambios Realizados

### 1. Filtro Eliminado ✓
**Archivo:** `excel_service.py`
**Cambio:** Eliminé las líneas 64-66 que filtraban `haken == "高雄工業 本社"`
**Resultado:** Ahora TODOS los empleados se importan (excepto los que no tienen nombre)

### 2. Nuevas Tablas en Base de Datos ✓
**Archivo:** `database.py`
**Tablas creadas:**
- `genzai` - Empleados en dispatch (DBGenzaiX)
- `ukeoi` - Empleados contratados (DBUkeoiX)

**Funciones agregadas:**
- `save_genzai(data)` - Guarda empleados dispatch
- `get_genzai()` - Obtiene empleados dispatch
- `clear_genzai()` - Limpia tabla genzai
- `save_ukeoi(data)` - Guarda empleados contratados
- `get_ukeoi()` - Obtiene empleados contratados
- `clear_ukeoi()` - Limpia tabla ukeoi

### 3. Nuevos Parsers de Excel ✓
**Archivo:** `excel_service.py`
**Funciones agregadas:**
- `parse_genzai_sheet(file_path)` - Lee hoja DBGenzaiX
- `parse_ukeoi_sheet(file_path)` - Lee hoja DBUkeoiX

### 4. Nuevos Endpoints API ✓
**Archivo:** `main.py`

**Endpoints Genzai:**
- `GET /api/genzai` - Obtener empleados dispatch
- `POST /api/sync-genzai` - Sincronizar desde Excel
- `DELETE /api/reset-genzai` - Limpiar tabla

**Endpoints Ukeoi:**
- `GET /api/ukeoi` - Obtener empleados contratados
- `POST /api/sync-ukeoi` - Sincronizar desde Excel
- `DELETE /api/reset-ukeoi` - Limpiar tabla

---

## 🧪 Cómo Verificar (DESPUÉS de reiniciar el servidor)

### Opción 1: Usar el script de prueba
```bash
python test_new_features.py
```

Este script prueba:
- Parsing de DBGenzaiX (debe mostrar ~1067 empleados)
- Parsing de DBUkeoiX (debe mostrar ~141 empleados)
- Guardado en base de datos
- Recuperación de datos

### Opción 2: Probar con curl

**1. Sincronizar datos de vacaciones:**
```bash
curl -X POST http://localhost:8000/api/sync
```

**2. Sincronizar Genzai (dispatch):**
```bash
curl -X POST http://localhost:8000/api/sync-genzai
```

**3. Sincronizar Ukeoi (contratados):**
```bash
curl -X POST http://localhost:8000/api/sync-ukeoi
```

**4. Ver datos:**
```bash
# Vacaciones
curl http://localhost:8000/api/employees

# Genzai
curl http://localhost:8000/api/genzai

# Ukeoi
curl http://localhost:8000/api/ukeoi
```

### Opción 3: Usar Swagger UI
Abre en tu navegador:
```
http://localhost:8000/docs
```

Deberías ver los nuevos endpoints:
- `/api/genzai` (GET)
- `/api/sync-genzai` (POST)
- `/api/reset-genzai` (DELETE)
- `/api/ukeoi` (GET)
- `/api/sync-ukeoi` (POST)
- `/api/reset-ukeoi` (DELETE)

---

## 📊 Resultados Esperados

### Después de sincronizar vacaciones:
```json
{
  "status": "success",
  "count": 1691,  // Ahora incluye TODOS los registros (sin filtro)
  "message": "Default file synced successfully"
}
```

### Después de sincronizar Genzai:
```json
{
  "status": "success",
  "count": 1067,  // ~1067 empleados dispatch
  "message": "Genzai synced: 1067 dispatch employees"
}
```

### Después de sincronizar Ukeoi:
```json
{
  "status": "success",
  "count": 141,  // ~141 empleados contratados
  "message": "Ukeoi synced: 141 contract employees"
}
```

---

## ⚠️ Lo que FALTA (Frontend)

El frontend HTML (`templates/index.html`) **todavía NO** tiene botones para:
- Sincronizar Genzai
- Sincronizar Ukeoi
- Ver datos de Genzai
- Ver datos de Ukeoi

Por ahora solo puedes acceder a estas funciones via:
- API directa (curl)
- Swagger UI (http://localhost:8000/docs)
- Scripts de Python

Si quieres que agregue botones al frontend para que puedas sincronizar desde la interfaz web, dime y lo haré.

---

## 🗄️ Estructura de la Base de Datos

Después de sincronizar todo, tu archivo `yukyu.db` tendrá 3 tablas:

1. **employees** (Vacaciones)
   - ~1691 registros con información de vacaciones

2. **genzai** (Dispatch)
   - ~1067 empleados con información de dispatch

3. **ukeoi** (Contratados)
   - ~141 empleados con información de contratos

---

## 🔍 Verificar que el filtro fue eliminado

Para confirmar que el filtro de "高雄工業 本社" fue eliminado:

```bash
# Sincroniza datos
curl -X POST http://localhost:8000/api/sync

# Busca empleados de 高雄工業 本社
curl http://localhost:8000/api/employees | python -c "
import sys, json
data = json.load(sys.stdin)
honsha = [e for e in data['data'] if e.get('haken') == '高雄工業 本社']
print(f'Empleados de 高雄工業 本社: {len(honsha)}')
"
```

Si muestra un número mayor a 0, significa que el filtro fue eliminado correctamente.

---

## 🚨 Problemas Comunes

### "404 Not Found" al llamar /api/sync-genzai
**Causa:** Servidor no reiniciado
**Solución:** Detén y reinicia el servidor

### "File not found" al sincronizar
**Causa:** Ruta del archivo Excel incorrecta
**Solución:** Verifica que el archivo existe en:
- Vacaciones: `D:\YuKyuDATA-app\有給休暇管理.xlsm`
- Empleados: `D:\YuKyuDATA-app\【新】社員台帳(UNS)T　2022.04.05～.xlsm`

### El servidor no inicia
**Causa:** Puerto 8000 ya en uso
**Solución:** Mata el proceso anterior o usa otro puerto

---

## ✅ Checklist de Verificación

- [ ] Servidor reiniciado
- [ ] Endpoints nuevos aparecen en /docs
- [ ] Sincronización de vacaciones funciona (muestra ~1691 registros)
- [ ] Sincronización de Genzai funciona (muestra ~1067 registros)
- [ ] Sincronización de Ukeoi funciona (muestra ~141 registros)
- [ ] Filtro de 高雄工業 本社 eliminado (hay empleados de本社)
- [ ] Cambio de año funciona en vacaciones
- [ ] Base de datos yukyu.db tiene 3 tablas

---

## 📝 Archivos Modificados/Creados

**Modificados:**
- ✅ `database.py` - Tablas y funciones nuevas
- ✅ `excel_service.py` - Parsers nuevos, filtro eliminado
- ✅ `main.py` - Endpoints nuevos
- ✅ `CLAUDE.md` - Documentación actualizada

**Creados:**
- ✅ `test_new_features.py` - Script de prueba
- ✅ `test_complete_system.py` - Prueba completa con curl
- ✅ `VERIFICACION_COMPLETA.md` - Este archivo
