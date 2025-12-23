# YuKyuDATA-app Setup Guide

Guía completa de instalación y configuración del sistema de gestión de vacaciones.

## Requisitos del Sistema

### Software Requerido

- **Python**: 3.10 o superior
- **Node.js**: 18.0 o superior (para tests E2E)
- **pip**: Gestor de paquetes de Python
- **Git**: Control de versiones

### Sistemas Operativos Soportados

- Windows 10/11
- macOS 12+
- Linux (Ubuntu 20.04+, Debian 11+)

## Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/your-org/YuKyuDATA-app.git
cd YuKyuDATA-app
```

### 2. Configurar Entorno Virtual Python

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate

# En macOS/Linux:
source venv/bin/activate
```

### 3. Instalar Dependencias Python

```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Instalar Dependencias de Testing (Opcional)

```bash
# Instalar Node.js dependencies
npm install

# Instalar navegadores Playwright
npx playwright install --with-deps
```

### 5. Configurar Archivos Excel

Coloca los archivos Excel en la raíz del proyecto:

- `有給休暇管理.xlsm` - Datos de vacaciones
- `【新】社員台帳(UNS)T　2022.04.05～.xlsm` - Registro de empleados

**Nota**: Los paths pueden configurarse en `main.py` si necesitas usar ubicaciones diferentes.

### 6. Inicializar Base de Datos

La base de datos SQLite se creará automáticamente en el primer inicio. Opcionalmente, puedes sincronizar datos iniciales:

```bash
# Iniciar el servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# En otro terminal, hacer sync inicial (o usa la UI)
curl -X POST http://localhost:8000/api/sync
```

## Configuración

### Variables de Entorno

Crea un archivo `.env` en la raíz (opcional):

```env
# Puerto del servidor
PORT=8000

# Modo debug
DEBUG=true

# Secret key para JWT (cambiar en producción)
SECRET_KEY=tu-secret-key-super-secreta-aqui

# CORS origins permitidos
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Nivel de logging
LOG_LEVEL=INFO
```

### Configuración de Seguridad

⚠️ **IMPORTANTE para Producción**:

1. **Cambiar SECRET_KEY**: Generar una key aleatoria
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. **Configurar CORS**: Restringir origins permitidos en `main.py`

3. **HTTPS**: Usar certificados SSL/TLS en producción

4. **Firewall**: Configurar firewall para limitar acceso

## Ejecución

### Modo Desarrollo

```bash
# Con auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# O usar el script de Windows
.\script\start_app_dynamic.bat
```

### Modo Producción

```bash
# Con Uvicorn (básico)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Con Gunicorn (recomendado para Linux)
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Acceder a la Aplicación

- **Dashboard**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing

### Tests Unitarios

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=. --cov-report=html

# Ver reporte de coverage
open htmlcov/index.html
```

### Tests E2E (Playwright)

```bash
# Ejecutar tests E2E
npm test

# Con UI interactiva
npm run test:ui

# En modo headed (ver navegador)
npm run test:headed

# Debug de tests
npm run test:debug

# Ver reporte
npm run test:report
```

## Estructura del Proyecto

```
YuKyuDATA-app/
├── main.py                  # FastAPI app principal
├── database.py              # Operaciones de base de datos
├── excel_service.py         # Parser de Excel
├── fiscal_year.py           # Lógica de año fiscal japonés
├── excel_export.py          # Exportación de reportes
├── logger.py                # Sistema de logging
│
├── routes/                  # API routes modulares
│   ├── auth.py             # Autenticación
│   ├── employees.py        # Gestión de empleados
│   ├── leave_requests.py   # Solicitudes de vacaciones
│   ├── compliance.py       # Verificaciones normativas
│   └── ...
│
├── services/                # Lógica de negocio
│   ├── auth_service.py     # Servicio de autenticación
│   └── ...
│
├── middleware/              # Middleware personalizado
│   ├── security.py         # Seguridad y auth
│   └── rate_limiter.py     # Rate limiting
│
├── utils/                   # Utilidades
│   └── file_validator.py   # Validación de archivos
│
├── templates/               # HTML templates
│   └── index.html          # Dashboard SPA
│
├── static/                  # Assets estáticos
│   ├── js/                 # JavaScript modules
│   ├── css/                # Stylesheets
│   └── icons/              # Iconos SVG
│
├── tests/                   # Tests
│   ├── e2e/                # Playwright E2E tests
│   └── *.py                # Tests unitarios
│
├── .claude/                 # Claude Code configuration
│   └── skills/             # Custom skills
│
└── docs/                    # Documentación
```

## Solución de Problemas

### Error: "No module named 'fastapi'"

```bash
# Asegúrate de estar en el venv
source venv/bin/activate  # o venv\Scripts\activate en Windows

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "Excel file not found"

- Verificar que los archivos Excel están en la ruta correcta
- Revisar los paths en `main.py` (líneas 266-267)
- Usar rutas absolutas si es necesario

### Error: "Port already in use"

```bash
# Cambiar puerto
python -m uvicorn main:app --reload --port 8001

# O matar el proceso usando el puerto
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### Playwright tests fallan

```bash
# Reinstalar navegadores
npx playwright install --with-deps

# Verificar que el servidor está corriendo
curl http://localhost:8000/api/info
```

## Desarrollo

### Agregar Nuevo Endpoint

1. Crear archivo en `routes/`
2. Implementar router con FastAPI
3. Agregar al `__init__.py` de routes
4. Importar en `main.py` y registrar router
5. Agregar tests en `tests/`

### Agregar Nueva Skill de Claude

1. Crear carpeta en `.claude/skills/nombre-skill/`
2. Crear archivo `SKILL.md` con frontmatter YAML
3. Claude detectará automáticamente el skill

## Seguridad

### Buenas Prácticas

- ✅ Usar autenticación JWT con refresh tokens
- ✅ Validar todos los inputs (Pydantic models)
- ✅ Validar uploads de archivos (MIME type, tamaño, firma)
- ✅ Usar HTTPS en producción
- ✅ Implementar rate limiting
- ✅ No exponer información sensible en logs
- ✅ Mantener dependencias actualizadas

### Checklist de Seguridad

- [ ] SECRET_KEY cambiada (no usar default)
- [ ] CORS configurado correctamente
- [ ] Rate limiting activado
- [ ] File upload validation habilitada
- [ ] HTTPS configurado (producción)
- [ ] Database backups configurados
- [ ] Logs sin información sensible

## Soporte

Para reportar problemas o solicitar features:

- **Issues**: https://github.com/your-org/YuKyuDATA-app/issues
- **Documentación**: Ver `/docs` en el proyecto
- **API Docs**: http://localhost:8000/docs

## Licencia

Proprietary - Todos los derechos reservados

---

**¿Listo para empezar?**

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visita http://localhost:8000 🚀
