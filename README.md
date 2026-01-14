# YuKyuDATA-app 1.0v

## Sistema de Gestión de Vacaciones Pagadas (有給休暇管理システム)

Sistema completo para la gestión de vacaciones pagadas de empleados, desarrollado con FastAPI + SQLite + JavaScript vanilla.

---

## Estado del Proyecto

| Categoría | Estado | Puntuación |
|-----------|--------|------------|
| **Tests** | 61/62 pasando | 98.4% |
| **Backend** | Funcional | 6.5/10 |
| **Frontend** | Funcional | 7.1/10 |
| **Seguridad** | Necesita mejoras | 4.5/10 |
| **Documentación** | Completa | 8/10 |

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

---

## Requisitos

```bash
Python 3.8+
pip install fastapi uvicorn openpyxl
```

### Configuración de autenticación segura

Estas variables **son obligatorias** para iniciar la API y evitar credenciales por defecto:

- `JWT_SECRET_KEY`: clave secreta para firmar los tokens JWT.
- `ADMIN_USERNAME`: usuario administrador.
- `ADMIN_PASSWORD_SALT`: sal utilizada para derivar el hash.
- `ADMIN_PASSWORD_HASH`: hash PBKDF2-HMAC-SHA256 de la contraseña administradora (100k iteraciones).
- `ADMIN_NAME` (opcional): nombre visible del administrador.
- `UPLOAD_MAX_BYTES` (opcional): límite de tamaño de subida (por defecto 5 MB).

Genera el hash de la contraseña con Python (ejemplo para `admin123`):

```bash
python - <<'PY'
import hashlib
password = "admin123"
salt = "elige-una-sal-segura"
dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
print(f"ADMIN_PASSWORD_SALT={salt}")
print(f"ADMIN_PASSWORD_HASH={dk.hex()}")
PY
```

Carga las variables en tu entorno (por ejemplo con `.env`) antes de ejecutar el servidor.

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

### Áreas de Mejora

1. **Seguridad** (CRÍTICO)
   - Sin autenticación en endpoints
   - File upload sin validación de MIME type
   - Datos sensibles expuestos sin filtrado

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

### Prioridad Alta (Inmediato)

```python
# 1. Agregar autenticación
from fastapi import Depends
from fastapi.security import HTTPBearer

# 2. Validar uploads
if mime not in ALLOWED_MIMES:
    raise HTTPException(400, "Invalid file type")

# 3. Filtrar datos sensibles por rol
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

## Archivos de Datos

Los archivos Excel fuente deben estar en:
- Vacaciones: `D:\YuKyuDATA-app\有給休暇管理.xlsm`
- Registro: `D:\YuKyuDATA-app\【新】社員台帳(UNS)T　2022.04.05～.xlsm`

---

## Licencia

Proyecto interno - Todos los derechos reservados

---

## Última Actualización

- **Fecha**: 2025-12-17
- **Versión**: 1.0v
- **Análisis**: Completo con 62 tests, 4 agentes de análisis
