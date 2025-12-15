# Guía de Prueba Completa del Sistema

## ✅ PASO 1: Iniciar el Servidor

### Opción A: Con selección de puerto
```bash
start_app.bat
```
Cuando te pregunte, ingresa el puerto (por ejemplo: 8000)

### Opción B: Puerto rápido
```bash
start_quick_8000.bat
```

**Verifica**: Deberías ver en la consola:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

---

## ✅ PASO 2: Verificar la Interfaz Web

1. Abre tu navegador en: **http://localhost:8000**

2. Deberías ver:
   - ✅ Título: "有給休暇管理ダッシュボード"
   - ✅ Panel de sincronización con botón "自動同期"
   - ✅ Nueva sección "社員台帳同期" con dos botones:
     - 🏢 派遣社員 (Genzai)
     - 📋 請負社員 (Ukeoi)

---

## ✅ PASO 3: Probar Sincronización de Vacaciones

1. Haz clic en el botón **"自動同期"** (Sincronización automática)

2. Deberías ver:
   - ✅ Spinner de carga con mensaje "自動同期中..."
   - ✅ Notificación verde: "同期成功: XXXX件"
   - ✅ Dashboard se muestra con gráficos
   - ✅ Tabla de datos al final con empleados

3. **Importante**: Verifica que el conteo incluya TODOS los registros (sin filtro de 高雄工業 本社)
   - El número debe ser aproximadamente **1691 registros** o más

---

## ✅ PASO 4: Probar Filtro de Años

1. En la sección "年度フィルター" verás botones de años disponibles

2. Haz clic en **"2025年度"**

3. Verifica:
   - ✅ El botón se marca como activo (fondo degradado)
   - ✅ Dashboard actualiza con datos del año seleccionado
   - ✅ Tabla filtra solo datos de 2025

4. Haz clic en **"全表示"** (Mostrar todos)
   - ✅ Se muestran todos los años nuevamente

---

## ✅ PASO 5: Probar Sincronización de Genzai (Dispatch)

1. Haz clic en el botón **"🏢 派遣社員 (Genzai)"**

2. Deberías ver:
   - ✅ Spinner: "派遣社員データ同期中..."
   - ✅ Notificación: "派遣社員同期成功: 1067名"
   - ✅ Contador actualizado: "派遣社員数: 1067"

---

## ✅ PASO 6: Probar Sincronización de Ukeoi (Contratados)

1. Haz clic en el botón **"📋 請負社員 (Ukeoi)"**

2. Deberías ver:
   - ✅ Spinner: "請負社員データ同期中..."
   - ✅ Notificación: "請負社員同期成功: 141名"
   - ✅ Contador actualizado: "請負社員数: 141"

---

## ✅ PASO 7: Verificar la Base de Datos

Ejecuta este script para ver el contenido de la base de datos:

```python
python -c "
import sqlite3
conn = sqlite3.connect('yukyu.db')
c = conn.cursor()

# Contar registros
tables = ['employees', 'genzai', 'ukeoi']
for table in tables:
    count = c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {count} registros')

conn.close()
"
```

Deberías ver algo como:
```
employees: 1691 registros  (o más, sin filtro)
genzai: 1067 registros
ukeoi: 141 registros
```

---

## ✅ PASO 8: Verificar API Endpoints (Swagger)

1. Abre: **http://localhost:8000/docs**

2. Verifica que aparezcan estos endpoints:

**Vacaciones:**
- ✅ GET `/api/employees`
- ✅ POST `/api/sync`
- ✅ POST `/api/upload`
- ✅ DELETE `/api/reset`

**Genzai:**
- ✅ GET `/api/genzai`
- ✅ POST `/api/sync-genzai`
- ✅ DELETE `/api/reset-genzai`

**Ukeoi:**
- ✅ GET `/api/ukeoi`
- ✅ POST `/api/sync-ukeoi`
- ✅ DELETE `/api/reset-ukeoi`

3. Prueba un endpoint:
   - Haz clic en `GET /api/genzai`
   - Click "Try it out"
   - Click "Execute"
   - Deberías ver 1067 registros en la respuesta

---

## ✅ PASO 9: Verificar que el Filtro fue Eliminado

Ejecuta:
```python
python -c "
import sqlite3
conn = sqlite3.connect('yukyu.db')
c = conn.cursor()

honsha = c.execute(
    'SELECT COUNT(*) FROM employees WHERE haken = ?',
    ('高雄工業 本社',)
).fetchone()[0]

print(f'Empleados de 高雄工業 本社: {honsha}')
conn.close()
"
```

Si muestra un número > 0, significa que el filtro fue eliminado correctamente ✅

---

## ✅ PASO 10: Prueba de Cambio de Puerto

1. Detén el servidor actual (Ctrl+C)

2. Inicia con otro puerto:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

3. Abre: **http://localhost:5000**

4. Verifica que todo funciona igual ✅

---

## 📊 Resumen de Conteos Esperados

| Base de Datos | Registros Esperados |
|---------------|---------------------|
| Employees (Vacaciones) | ~1691 (SIN filtro de 本社) |
| Genzai (Dispatch) | ~1067 |
| Ukeoi (Contratados) | ~141 |

---

## ❌ Problemas Comunes y Soluciones

### Problema: "404 Not Found" al sincronizar Genzai/Ukeoi
**Causa**: Servidor corriendo con código viejo
**Solución**:
1. Detén el servidor (Ctrl+C)
2. Reinicia: `start_app.bat`

### Problema: No aparecen los botones nuevos en el frontend
**Causa**: Caché del navegador
**Solución**:
1. Presiona Ctrl+F5 (refrescar forzado)
2. O abre en modo incógnito

### Problema: "File not found" al sincronizar
**Causa**: Archivos Excel no están en las rutas esperadas
**Solución**: Verifica que existan:
- `D:\YuKyuDATA-app\有給休暇管理.xlsm`
- `D:\YuKyuDATA-app\【新】社員台帳(UNS)T　2022.04.05～.xlsm`

### Problema: El contador muestra 0 después de sincronizar
**Causa**: Error en la sincronización
**Solución**:
1. Abre la consola del navegador (F12)
2. Revisa errores en la pestaña "Console"
3. Verifica que el servidor esté corriendo

---

## ✅ Checklist Final

- [ ] Servidor inicia correctamente
- [ ] Puerto se puede cambiar
- [ ] Frontend carga sin errores
- [ ] Sincronización de vacaciones funciona
- [ ] Filtro de años funciona
- [ ] Sincronización de Genzai funciona
- [ ] Sincronización de Ukeoi funciona
- [ ] Base de datos tiene 3 tablas con datos
- [ ] Filtro de 高雄工業 本社 fue eliminado
- [ ] API endpoints funcionan en Swagger
- [ ] Cambio de puerto funciona

---

## 🎉 Si todo está ✅, el sistema está funcionando perfectamente!

### Próximos pasos sugeridos:

1. **Crear páginas para ver Genzai/Ukeoi**: Actualmente solo se pueden ver via API
2. **Agregar búsqueda y filtros** para empleados
3. **Dashboard combinado** que muestre datos de las 3 bases
4. **Exportar a Excel** los datos sincronizados

¿Quieres que implemente alguna de estas funcionalidades?
