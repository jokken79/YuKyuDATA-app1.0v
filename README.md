# YuKyuDATA-app 1.0v

## Sistema de Gestión de Vacaciones Pagadas (有給休暇管理システム)

Sistema completo para la gestión de vacaciones pagadas de empleados, desarrollado con FastAPI + SQLite + JavaScript vanilla.

---

## Estado del Proyecto

| Categoría | Estado | Puntuación |
|-----------|--------|------------|
| **Tests** | 63 pasando | ~98% |
| **Backend** | Funcional | 8.0/10 |
| **Frontend** | Mejorado | 8.5/10 |
| **Seguridad** | JWT + Rate Limiting | 8.5/10 |
| **UI/UX** | Sistema Unificado | 8.0/10 |
| **Documentación** | Completa | 9/10 |

---

## Características Principales

- **Dashboard Premium**: Visualizaciones interactivas con Chart.js y ApexCharts
- **Gestión de Vacaciones**: Seguimiento de días otorgados, usados y balance
- **Tres Tipos de Empleados**:
  - `employees` - Datos de vacaciones
  - `genzai` - Empleados de despacho (派遣社員)
  - `ukeoi` - Empleados contratistas (請負社員)
- **Sistema de Solicitudes**: CRUD completo para solicitudes de vacaciones
- **Cumplimiento Normativo**: Verificación de la regla de 5 días mínimos
- **Reportes Mensuales**: Período 21日〜20日 (sistema japonés)
- **Exportación Excel**: Generación de reportes en formato Excel
- **PWA**: Funcionalidad offline con Service Worker
- **Tema Claro/Oscuro**: Soporte completo de temas
- **Autenticación JWT**: Sistema completo con refresh tokens y sesiones
- **Rate Limiting**: Protección contra abuso con límites dinámicos
- **Paginación**: Respuestas paginadas para endpoints de lista

---

## Requisitos

```bash
Python 3.8+
pip install fastapi uvicorn openpyxl
```

---

## Inicio Rápido

```bash
# Iniciar servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# O usar scripts de inicio (Windows)
start_quick_8000.bat
```

Accede a: http://localhost:8000

---

## Estructura del Proyecto

```
YuKyuDATA-app1.0v/
├── main.py              # Backend FastAPI (2,751 líneas)
├── database.py          # Operaciones SQLite (1,103 líneas)
├── excel_service.py     # Parser de Excel (475 líneas)
├── fiscal_year.py       # Cálculos de año fiscal (512 líneas)
├── templates/
│   └── index.html       # Dashboard SPA (1,833 líneas)
├── static/
│   ├── js/app.js        # Frontend JS (3,701 líneas)
│   └── css/             # Estilos (125 KB)
├── tests/
│   ├── test_api.py      # Tests de API (27 tests)
│   └── test_comprehensive.py # Tests completos (35 tests)
├── agents/              # Módulos de agentes inteligentes
└── docs/                # Documentación técnica
```

**Total**: ~12,600 líneas de código

---

## 🔐 Autenticación y Seguridad

### Sistema de Autenticación

La aplicación utiliza **JWT (JSON Web Tokens)** para autenticación con las siguientes características:

- **Access Tokens**: Expiración de 15 minutos
- **Refresh Tokens**: Expiración de 7 días con rotación automática
- **Sesiones Múltiples**: Soporte para múltiples dispositivos
- **Revocación**: Logout individual o de todas las sesiones

### Credenciales de Desarrollo

⚠️ **Solo para entorno de desarrollo** (cuando `DEBUG=true`):

En modo DEBUG, el sistema genera automáticamente credenciales temporales seguras.
Las credenciales se muestran en la **consola del servidor** al iniciar.

```bash
# Las credenciales temporales aparecerán así en la consola:
[WARNING] Credenciales de desarrollo generadas:
  admin: <contraseña-aleatoria-16-chars>
  demo: <contraseña-aleatoria-16-chars>
```

### Configurar Usuarios en Producción

```bash
# Opción 1: Variable de entorno JSON
USERS_JSON='{"admin":{"password":"$2b$12$hash...","role":"admin"}}'

# Opción 2: Archivo externo
USERS_FILE=/etc/yukyu/users.json
```

> **IMPORTANTE**: En producción (`DEBUG=false`), debes configurar `JWT_SECRET_KEY` y usuarios.

### Endpoints de Autenticación

| Endpoint | Método | Descripción | Auth Requerida |
|----------|--------|-------------|----------------|
| `/api/auth/login` | POST | Iniciar sesión | No |
| `/api/auth/logout` | POST | Cerrar sesión actual | Sí |
| `/api/auth/logout-all` | POST | Cerrar todas las sesiones | Sí |
| `/api/auth/refresh` | POST | Renovar access token | No (requiere refresh token) |
| `/api/auth/verify` | GET | Verificar validez del token | Sí |
| `/api/auth/me` | GET | Obtener información del usuario | Sí |
| `/api/auth/sessions` | GET | Listar sesiones activas | Sí |
| `/api/auth/register` | POST | Registrar nuevo usuario | No |
| `/api/auth/change-password` | POST | Cambiar contraseña | Sí |

### Ejemplo de Uso

```javascript
// 1. Login (usar credenciales de la consola del servidor en desarrollo)
const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'admin',
        password: 'tu-contraseña'  // Ver consola del servidor
    })
});
const data = await response.json();
const { access_token, refresh_token } = data;

// 2. Usar el token en requests
const protectedResponse = await fetch('/api/employees', {
    headers: {
        'Authorization': `Bearer ${access_token}`
    }
});

// 3. Renovar token cuando expire
const refreshResponse = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
});
```

### Rate Limiting

Protección automática contra abuso con límites por endpoint:

| Endpoint | Límite | Ventana |
|----------|--------|--------|
| `/api/auth/login` | 5 requests | 60s |
| `/api/auth/register` | 3 requests | 60s |
| `/api/sync*` | 2 requests | 60s |
| `/api/reports/*` | 10 requests | 60s |
| Autenticados (general) | 200 requests | 60s |
| Anónimos (general) | 100 requests | 60s |

---

## API Endpoints

### Vacaciones
- `GET /api/employees` - Lista de empleados con datos de vacaciones
- `GET /api/employees/search?q=` - Búsqueda de empleados
- `POST /api/sync` - Sincronizar desde Excel
- `POST /api/upload` - Subir archivo Excel

### Genzai/Ukeoi
- `GET /api/genzai` - Empleados de despacho
- `GET /api/ukeoi` - Empleados contratistas
- `POST /api/sync-genzai` - Sincronizar genzai
- `POST /api/sync-ukeoi` - Sincronizar ukeoi

### Solicitudes
- `GET /api/leave-requests` - Lista de solicitudes
- `POST /api/leave-requests` - Crear solicitud
- `PUT /api/leave-requests/{id}` - Actualizar solicitud

### Cumplimiento
- `GET /api/compliance/5day-check/{year}` - Verificación de 5 días
- `GET /api/compliance/alerts` - Alertas de cumplimiento
- `GET /api/compliance/annual-ledger/{year}` - Libro anual

### Reportes
- `GET /api/reports/monthly/{year}/{month}` - Reporte mensual
- `GET /api/reports/custom?start_date=&end_date=` - Reporte personalizado
- `POST /api/export/excel` - Exportar a Excel

### Sistema
- `GET /api/system/snapshot` - Estado del sistema
- `GET /api/db-status` - Estado de la base de datos
- `POST /api/backup` - Crear backup

---

## Tests

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Resultados actuales:
# - test_api.py: 26/27 pasando
# - test_comprehensive.py: 35/35 pasando
# - Total: 61/62 (98.4%)
```

---

## Análisis de Calidad

### Fortalezas

1. **Arquitectura clara**: Separación de capas (API, Service, Database)
2. **Flexibilidad de parseo**: Detección inteligente de headers Excel
3. **UI moderna**: Dashboard premium con animaciones
4. **Documentación**: CLAUDE.md completo para desarrollo
5. **PWA**: Funcionalidad offline
6. **Tests**: Cobertura del 98.4%

### Mejoras Recientes (2026-01-19)

1. **✅ Seguridad Implementada**
   - ✅ Sistema completo de autenticación JWT
   - ✅ Refresh tokens con rotación
   - ✅ Rate limiting avanzado user-aware
   - ✅ Error handling centralizado
   - ✅ Custom exceptions con códigos HTTP apropiados
   - ⚠️ File upload sin validación MIME (uso local solamente)

2. **Arquitectura**
   - `main.py` demasiado grande (2,751 líneas)
   - Código duplicado en parsers
   - Falta de inyección de dependencias

3. **Error Handling**
   - Algunos endpoints devuelven 500 en lugar de 400/422
   - Mensajes de error exponen información del sistema

4. **Performance**
   - N+1 queries en búsqueda de empleados
   - Sin paginación en endpoints de lista

---

## Recomendaciones

### ✅ Completado Recientemente

```python
# ✅ 1. Autenticación JWT implementada
from middleware.auth_middleware import get_current_user, require_admin

@app.get("/protected")
async def protected(user: CurrentUser = Depends(get_current_user)):
    return {"user": user.username}

# ✅ 2. Rate limiting implementado
from middleware.rate_limiter import user_aware_limiter

# ✅ 3. Paginación disponible
from utils.pagination_utils import paginate, PaginationParams
```

### Prioridad Media (1-2 semanas)

- Dividir `main.py` en módulos (routes/, services/)
- Migrar validadores Pydantic V1 a V2
- Implementar paginación
- Agregar rate limiting

### Prioridad Baja (1 mes)

- Migrar a SQLAlchemy ORM
- Implementar caching con Redis
- Agregar CI/CD pipeline
- Implementar logging centralizado

---

## 🚀 Producción

### Configuración de Seguridad

Para deployment en producción, ver **[PRODUCTION.md](PRODUCTION.md)** con:

- ✅ SECRET_KEY segura desde .env
- ✅ Tokens con expiración de 15 minutos
- ✅ Rate limiting configurado
- ⚠️ HTTPS requerido (configurar reverse proxy)
- ⚠️ CORS restrictivo (actualizar dominios permitidos)

### Deployment Rápido

```bash
# 1. Copiar template de producción
cp .env.production .env

# 2. Generar SECRET_KEY segura
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Actualizar .env con la key generada y configuraciones

# 4. Iniciar con uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

Ver [PRODUCTION.md](PRODUCTION.md) para guía completa.

---

## Archivos de Datos

Los archivos Excel fuente deben estar en:
- Vacaciones: `D:\YuKyuDATA-app\有給休暇管理.xlsm`
- Registro: `D:\YuKyuDATA-app\【新】社員台帳(UNS)T　2022.04.05～.xlsm`

---

## Licencia

Proyecto interno - Todos los derechos reservados

---

## Última Actualización

- **Fecha**: 2026-01-20
- **Versión**: 1.2v
- **Mejoras**:
  - Sistema de diseño unificado (`unified-design-system.css`)
  - Componente UIStates (loading/empty/error/skeleton)
  - Consolidación estado frontend (singleton pattern)
  - Limpieza CSS legacy (-13,884 líneas)
  - Mejoras de agentes (timeout, circuit breaker, cleanup)
- **Tests**: 63 pasando (~98%)
