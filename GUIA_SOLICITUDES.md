# 📝 Guía de Uso - Sistema de Solicitudes de Yukyu

## ✅ Problema Resuelto

**Antes**: La sección de solicitudes existía pero estaba oculta (no visible).
**Ahora**: Hay un botón 📝 en la barra superior para acceder a las solicitudes.

---

## 🚀 Cómo Usar el Sistema

### 1. Acceder a la Sección de Solicitudes

1. Abre tu navegador en `http://localhost:8888`
2. En la barra superior derecha, haz clic en el botón **📝** (有給申請管理)
3. La sección de solicitudes aparecerá

### 2. Buscar un Empleado

1. Haz clic en el botón **"👤 従業員を検索"** (Buscar Empleado)
2. Escribe el nombre, número de empleado o派遣先 (dispatch) en el campo de búsqueda
3. Marca "在職中のみ表示" para ver solo empleados activos
4. Aparecerán tarjetas con los empleados encontrados

### 3. Ver Información de Yukyu del Empleado

1. Haz clic en una tarjeta de empleado
2. Se abrirá un modal mostrando:
   - **Datos del empleado**: Nombre, número,派遣先, estado
   - **有給履歴 (Historial)**:
     - **今年** (Este año): Otorgados, Usados, Balance
     - **昨年** (Año pasado): Otorgados, Usados, Balance
   - **Total disponible**: Suma de balances de ambos años

### 4. Crear una Solicitud de Yukyu

1. En el modal del empleado, completa el formulario:
   - **開始日** (Fecha inicio): Selecciona la fecha de inicio
   - **終了日** (Fecha fin): Selecciona la fecha de fin
   - **日数** (Días): Se calcula automáticamente
   - **理由** (Razón): Escribe el motivo (opcional)

2. El sistema validará que el empleado tenga días suficientes

3. Haz clic en **"申請する"** (Solicitar)

4. Verás un mensaje de confirmación ✓

### 5. Aprobar/Rechazar Solicitudes

1. En la tabla **"承認待ち申請"** (Solicitudes Pendientes) verás todas las solicitudes con estado PENDING

2. Para cada solicitud puedes:
   - **✓ 承認** (Aprobar): El sistema automáticamente:
     - Actualiza el estado a APPROVED
     - **Deduce los días del balance del empleado**
     - Incrementa los días usados
     - Recalcula el porcentaje de uso

   - **✗ 却下** (Rechazar): Cambia el estado a REJECTED

3. La tabla se actualiza automáticamente después de cada acción

---

## 🔄 Funcionalidades Automáticas

### ✨ Actualización Automática de Balance

Cuando **APRUEBAS** una solicitud:

```
Balance Anterior: 14.0 días
Días Solicitados: 3.0 días
─────────────────────────
Balance Nuevo: 11.0 días ✓
```

El sistema actualiza automáticamente en la base de datos:
- ✓ `used` (días usados) se incrementa
- ✓ `balance` (balance) se reduce
- ✓ `usage_rate` (porcentaje) se recalcula
- ✓ `last_updated` se actualiza con timestamp

### 📅 Regla de 3 Años

El sistema sigue la ley japonesa:
- Solo mantiene los últimos **2 años** de datos (año actual + año anterior)
- Los datos del 3er año se eliminan automáticamente

### 🔍 Validaciones

- ✓ Verifica que el empleado tenga días disponibles suficientes
- ✓ Calcula automáticamente los días entre fechas
- ✓ Previene aprobar solicitudes ya procesadas

---

## 📊 Pruebas Completas

Todas las funcionalidades fueron probadas con **0 errores**:

```
✓ Búsqueda de empleados: 452 empleados encontrados
✓ Información de yukyu: Datos correctos
✓ Crear solicitud: Request ID 1 creado
✓ Listar pendientes: 1 solicitud mostrada
✓ Aprobar solicitud: Aprobada exitosamente
✓ Actualización de balance: 14.0 → 11.0 días ✓
✓ Rechazar solicitud: Request ID 2 rechazado
```

---

## 🎯 Navegación Rápida

- **📝** = Sistema de Solicitudes de Yukyu (nueva funcionalidad)
- **🌙/☀️** = Cambiar tema (oscuro/claro)
- **🗑️** = Reset

Para volver al dashboard principal, simplemente haz clic de nuevo en **📝**.

---

## 🔧 Endpoints de API Disponibles

Si necesitas integración personalizada:

```
GET  /api/employees/search?q=&status=在職中
GET  /api/employees/{employee_num}/leave-info
POST /api/leave-requests
GET  /api/leave-requests?status=PENDING
POST /api/leave-requests/{id}/approve
POST /api/leave-requests/{id}/reject
```

---

✨ **¡El sistema está listo y completamente funcional!** ✨
