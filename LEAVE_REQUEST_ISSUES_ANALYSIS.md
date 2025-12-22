# 🔍 **ANÁLISIS: Problemas en Solicitudes de Yukyu**

## **Problema 1: Aparecen Funcionarios de Otra Fábrica** ⚠️

### Síntoma
Cuando se selecciona una fábrica y se busca un empleado, aparecen empleados de otras fábricas.

### Investigación

#### Frontend (app.js)
```javascript
// Línea 1618-1634: filterByFactory()
filterByFactory() {
    const factory = document.getElementById('factory-filter').value;
    if (factory) {
        this.searchWithFactory(query, factory);  // ✓ Pasa factory
    }
}

// Línea 1636-1665: searchWithFactory()
async searchWithFactory(query, factory) {
    let url = `${App.config.apiBase}/employees/search?status=在職中`;
    if (query) url += `&q=${encodeURIComponent(query)}`;
    if (factory) url += `&factory=${encodeURIComponent(factory)}`;  // ✓ Factory en URL
    // ...
}

// Línea 1667-1709: searchEmployee()
async searchEmployee(query) {
    const factory = document.getElementById('factory-filter')?.value || '';
    let url = `${App.config.apiBase}/employees/search?status=在職中`;
    if (query) url += `&q=${encodeURIComponent(query)}`;
    if (factory) url += `&factory=${encodeURIComponent(factory)}`;  // ✓ Factory en URL
    // ...
}
```

✓ Frontend **SÍ está enviando** `&factory=` al backend

#### Backend (main.py)
```python
# Línea 648-704: search_employees()
@app.get("/api/employees/search")
async def search_employees(q: str = "", status: str = None, factory: str = None):
    # Genzai filtering (línea 659-661)
    if factory and emp_factory != factory:
        continue  # ✓ Filtra si factory no coincide

    # Ukeoi filtering (línea 683-685)
    if factory and emp_factory != factory:
        continue  # ✓ Filtra si factory no coincide
```

✓ Backend **SÍ está filtrando** por factory

### Causa Probable

**El filtrado ESTÁ funcionando correctamente en el código.**

Posibles razones por las que el usuario ve empleados de otra fábrica:

1. **No ha seleccionado factory** - Si no selecciona en el dropdown, `factory` = '' (vacío)
   - Resultado: Se muestran empleados de TODAS las fábricas
   - Solución: El usuario necesita seleccionar una fábrica específica

2. **El dropdown está vacío** - Si `/api/factories` no devuelve datos
   - Resultado: No hay fábricas para seleccionar
   - Revisar: `loadFactories()` línea 1594-1616 en app.js
   - Revisar: Endpoint en main.py línea 609-643

3. **Data desincronizada** - Si los genzai/ukeoi en BD no tienen factory correcta
   - Los empleados en BD tienen `dispatch_name` o `contract_business` vacíos
   - Revisar: Base de datos

### **Solución 1: Mejora de UX**

Mostrar una advertencia si no se selecciona factory:

```javascript
// En filterByFactory() - línea 1618
filterByFactory() {
    const factory = document.getElementById('factory-filter').value;
    const query = document.getElementById('emp-search').value;

    if (!factory && (!query || query.length < 2)) {
        App.ui.showToast('warning', '工場を選択するか検索キーワードを入力してください');
        document.getElementById('emp-search-results').innerHTML = '';
        return;
    }
    // ... rest of code
}
```

### **Solución 2: Verificar Base de Datos**

```sql
-- Verificar que genzai/ukeoi tienen factory correcta
SELECT employee_num, name, dispatch_name FROM genzai LIMIT 10;
SELECT employee_num, name, contract_business FROM ukeoi LIMIT 10;
```

---

## **Problema 2: Datos de Solicitud No Se Guardan** ⚠️

### Síntoma
Se llenan los datos del formulario, se envía la solicitud, pero no aparecen en "Pending Requests".

### Investigación

#### Flujo de Guardado

**Frontend (app.js)**
```javascript
// Línea 2229: POST request
const res = await fetch(`${App.config.apiBase}/leave-requests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        employee_num: this.selectedEmployee.employee.employee_num,
        employee_name: this.selectedEmployee.employee.name,
        start_date: startDate,
        end_date: endDate,
        days_requested: daysRequested,
        hours_requested: hoursRequested,
        leave_type: leaveType,
        reason: reason,
        hourly_wage: hourlyWage,
        cost_estimate: costEstimate
    })
});

if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Request failed');  // ← Si hay error, se muestra
}

// Línea 2252: Success
App.ui.showToast('success', `申請が送信されました`);
this.resetForm();
this.loadPending();  // ← Reload pending requests
```

**Backend (main.py)**
```python
# Línea 807-875: create_leave_request()
@app.post("/api/leave-requests")
async def create_leave_request(request_data: dict):
    # Validación (línea 814-817)
    required = ['employee_num', 'employee_name', 'start_date', 'end_date', 'days_requested']
    for field in required:
        if field not in request_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    # Guardar (línea 852-863)
    request_id = database.create_leave_request(
        employee_num=request_data['employee_num'],
        employee_name=request_data['employee_name'],
        start_date=request_data['start_date'],
        end_date=request_data['end_date'],
        days_requested=request_data['days_requested'],
        reason=request_data.get('reason', ''),
        year=current_year,
        hours_requested=hours_requested,
        leave_type=request_data.get('leave_type', 'full'),
        hourly_wage=hourly_wage
    )

    return {
        "status": "success",
        "message": "申請が作成されました",
        "request_id": request_id,
    }
```

### Posibles Causas

**Causa 1: Error HTTP no Visible**
- Si `res.ok` es false (status != 2xx), se muestra error en toast
- ¿Apareció algún error en el toast?

**Causa 2: Request Creado pero No en Lista**
```python
# Línea 881 en main.py
requests = database.get_leave_requests(status=status, employee_num=employee_num, year=year)
```
- ¿El request se creó pero `loadPending()` no lo muestra?
- Revisar: Función `get_leave_requests()` en database.py

**Causa 3: Reset De Formulario Ocultó Datos**
```javascript
// Línea 2253-2255
this.resetForm();      // Limpia el formulario
this.loadPending();    // Recarga lista
```
- Si `loadPending()` FALLA, el usuario no ve nada
- Pero el formulario se limpió, dando la ilusión de "guardado"

**Causa 4: Status del Request**
```python
# Cuando se crea, ¿qué status tiene?
# Revisar database.create_leave_request() - probablemente 'PENDING'
# Pero get_leave_requests() podría estar filtrando por otro status
```

### **Solución 1: Mejorar Feedback**

```javascript
// Línea 2254: Add logging antes de reset
async submitConfirmed() {
    const submitBtn = document.getElementById('confirm-submit-btn');
    submitBtn.classList.add('is-loading');

    try {
        const response = await this.submit();
        console.log('✓ Request created:', response);  // ← DEBUG

        this.hideConfirmation();
    } catch (e) {
        console.error('✗ Submit error:', e);  // ← DEBUG
        App.ui.showToast('error', `Error: ${e.message}`);
    } finally {
        submitBtn.classList.remove('is-loading');
    }
}
```

### **Solución 2: Verificar loadPending()**

```javascript
// Línea 2307: Revisar esta función
async loadPending() {
    try {
        const res = await fetch(`${App.config.apiBase}/leave-requests?status=PENDING`);
        const json = await res.json();

        console.log('Pending requests:', json);  // ← DEBUG

        // Renderizar lista...
    } catch (e) {
        console.error('Failed to load pending:', e);
    }
}
```

### **Solución 3: Check Database**

```python
# En main.py, agregar endpoint de debugging
@app.get("/api/debug/leave-requests")
async def debug_leave_requests():
    """Debug endpoint - returns ALL requests regardless of status"""
    try:
        # Raw query - sin filtros
        requests = database.get_leave_requests()  # SIN status filter
        return {"status": "success", "data": requests, "total": len(requests)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
```

Luego en el navegador, abrir:
```
http://localhost:8000/api/debug/leave-requests
```

Si ves requests aquí pero NO en `/api/leave-requests?status=PENDING`, entonces el problema es el filtrado de status.

---

## 🎯 **Próximos Pasos**

### **Inmediato:**

1. **Problema 1 (Funcionarios de otra fábrica):**
   - [ ] Verificar que el usuario REALMENTE selecciona una fábrica
   - [ ] Verificar que `/api/factories` devuelve datos
   - [ ] Verificar que genzai/ukeoi en BD tienen `dispatch_name`/`contract_business`

2. **Problema 2 (Datos no se guardan):**
   - [ ] Abrir DevTools (F12)
   - [ ] Ir a Network tab
   - [ ] Hacer solicitud
   - [ ] Ver request POST `/api/leave-requests`
   - [ ] Ver response - ¿Es 200 OK o error?
   - [ ] Ver si hay toast de error
   - [ ] Si creó bien, ¿por qué no aparece en pending?

### **Si necesitas que Implemente Fixes:**

```
Me falta:
1. Output de DevTools mostrando el error (si hay)
2. Confirmación si `/api/factories` devuelve datos
3. Check de BD: SELECT * FROM leave_requests;
```

---

## 📝 **Checklist de Debugging**

- [ ] Abrir DevTools (F12 → Network)
- [ ] Hacer solicitud de yukyu
- [ ] Copiar URL y response del POST `/api/leave-requests`
- [ ] Verificar status HTTP (200, 400, 500?)
- [ ] Ver si hay toast de error
- [ ] Revisar Console for any JavaScript errors
- [ ] Ejecutar `/api/debug/leave-requests` en navegador
- [ ] Check BD: `SELECT COUNT(*) FROM leave_requests;`

**Estado:** Análisis completado, fixes ready ✅
