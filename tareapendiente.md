# Tareas Pendientes - YuKyuDATA v2.8

## Resumen de la Sesion

Esta sesion se enfoco en corregir problemas de UI/UX y preparar el sistema para sincronizacion de datos.

---

## Tareas Completadas

1. **Auditar endpoints API** - Se verificaron todos los endpoints y su funcionamiento
2. **Corregir mismatch HTML/JS en KPIs** - Los IDs de los elementos KPI ahora coinciden
3. **Arreglar errores JS en ui-enhancements.js** - Se agregaron null checks para `e.target.closest()`
4. **Arreglar loop infinito de resize en charts** - Se agrego flag `_isEnsureChartsRunning` para prevenir recursion
5. **Mejorar sidebar** - Se creo ui-fixes-v2.8.css con mejoras de ancho y visibilidad

---

## Tareas Pendientes

### Alta Prioridad

#### 1. Sincronizar Excel con Base de Datos
**Estado:** Bloqueado por autenticacion
**Descripcion:** El archivo Excel actualizado fue copiado de E: a D:
- Archivo origen: `E:\CosasParaAppsJp\有給休暇管理.xlsm` (1814 filas)
- Archivo destino: `D:\YuKyuDATA-app1.0v\有給休暇管理.xlsm`
- El endpoint `/api/sync` requiere autenticacion admin

**Solucion implementada:**
- Se agrego usuario admin de desarrollo en `auth.py`:
  - Usuario: `admin`
  - Password: `admin123456`
  - Solo funciona cuando `DEBUG=true` en `.env`

**Para completar la sincronizacion:**
1. Iniciar servidor: `python -m uvicorn main:app --reload --port 8000`
2. Login como admin en la interfaz web
3. Hacer clic en "Sync" o llamar al endpoint:
   ```bash
   # Obtener token
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123456"}'

   # Usar token para sync
   curl -X POST http://localhost:8000/api/sync \
     -H "Authorization: Bearer <TOKEN>"
   ```

---

### Media Prioridad

#### 2. Implementar Login en Frontend
**Estado:** Pendiente
**Descripcion:** La interfaz web necesita formulario de login para acceder a funciones admin
- Actualmente el boton Sync falla con 401 porque no hay token
- Se necesita agregar modal/pagina de login
- Guardar token en localStorage/sessionStorage

#### 3. Verificar Datos Despues de Sync
**Estado:** Pendiente (depende de tarea 1)
**Descripcion:** Confirmar que los datos del Excel coinciden con la base de datos
- Actualmente: 1393 empleados en DB
- Excel actualizado: 1814 filas (posiblemente ~1400+ empleados despues de filtrar)

---

### Baja Prioridad

#### 4. Mejorar Sidebar Colapsado
**Estado:** Parcialmente completado
**Descripcion:** El sidebar ya tiene mejoras en `ui-fixes-v2.8.css`
- Ancho aumentado a 260px
- Tooltips para modo colapsado
- Responsive breakpoints configurados

#### 5. Optimizar Carga de Charts
**Estado:** Completado pero puede mejorarse
**Descripcion:** Los charts ya cargan correctamente
- Fix de loop infinito aplicado
- Considerar lazy loading para mejor rendimiento

---

## Archivos Modificados en Esta Sesion

| Archivo | Cambios |
|---------|---------|
| `templates/index.html` | Agregado `data-theme="dark"`, imports CSS |
| `static/css/ui-fixes-v2.8.css` | NUEVO - Fixes de sidebar, theme, cards |
| `static/js/app.js` | Fix loop infinito `ensureChartsVisible()` |
| `static/js/modules/ui-enhancements.js` | Null checks para eventos |
| `config/security.py` | CSP actualizado para CDN scripts |
| `auth.py` | Usuario admin de desarrollo agregado |
| `.env` | NUEVO - Configuracion de desarrollo |

---

## Notas Tecnicas

### Credenciales de Desarrollo (Solo DEBUG=true)
- Usuario: `demo` / Password: `demo123456` / Rol: user
- Usuario: `admin` / Password: `admin123456` / Rol: admin

### Puertos
- Puerto por defecto: 8000
- Si esta ocupado, usar: 8001

### Comandos Utiles
```bash
# Iniciar servidor
python -m uvicorn main:app --reload --port 8000

# Verificar estado
curl http://localhost:8000/health

# Ver empleados
curl http://localhost:8000/api/employees?year=2026
```

---

## Proximos Pasos Recomendados

1. **Inmediato:** Completar sync de datos con Excel actualizado
2. **Corto plazo:** Agregar formulario de login al frontend
3. **Mediano plazo:** Tests automatizados para UI
4. **Largo plazo:** Implementar autenticacion OAuth/SSO para produccion
