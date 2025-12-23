# Repository Guidelines

## Estructura del Proyecto y Organizacion de Modulos
- `main.py` define la API FastAPI y rutas; `database.py`, `excel_service.py`, `fiscal_year.py`, `excel_export.py` concentran la logica principal.
- `templates/index.html` es el entry de la SPA; JS modular en `static/js/modules/`, assets en `static/js/` y `static/css/`.
- `tests/` contiene pruebas backend y frontend; `tests/unit/` y `tests/integration/` son pruebas HTML; `script/` tiene utilidades de arranque.
- Artefactos locales en `uploads/`, `exports/`, `backups/`, `logs/`; la base local es `yukyu.db`.

## Comandos de Build, Test y Desarrollo
Usa estos comandos desde la raiz del repo:
```bash
# API + SPA (modo desarrollo)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
script\start_app_dynamic.bat
script\start_quick_8000.bat

# Backend tests
python -m pytest tests/ -v

# Tests HTML (servidor estatico)
python -m http.server 8080

# Jest unit tests
npx jest --config jest.config.js

# Build/minificacion (salida en build/)
python build.py
```

## Estilo de Codigo y Convenciones de Nombres
- Indentacion: 4 espacios en Python y JavaScript.
- Python: `snake_case` para funciones/variables, `PascalCase` para clases y modelos Pydantic; usa type hints cuando agregues funciones nuevas.
- JavaScript: `camelCase` para funciones/variables y `PascalCase` para clases; manten los modulos en `static/js/modules/`.
- No hay formatter obligatorio; mantiene el estilo del archivo que toques.

## Guia de Testing
- Pytest recoge `test_*.py` y `*_test.py` en `tests/`.
- Pruebas HTML viven en `tests/unit/*.html` y `tests/integration/*.html`; abre via `http://localhost:8080/tests/...` o con el servidor de la app.
- Jest apunta a `tests/**/*.test.js` y mantiene umbrales globales de cobertura (80%). Ajusta mocks/restauraciones cuando uses `fetch` o `localStorage`.

## Commits y Pull Requests
- Convencion observada: Conventional Commits con resumen en espanol (`feat: agregar ...`, `fix: corregir ...`, `docs: ...`, `refactor: ...`).
- PRs: descripcion clara, comandos ejecutados y resultados, issue vinculada si existe, y capturas cuando se toca UI. Si hay cambios en DB o datos, describe impacto y backups.

## Seguridad y Configuracion
- Define `JWT_SECRET_KEY` para cualquier uso fuera de local; el usuario `admin`/`admin123` es solo para desarrollo.
- No subas datos reales ni archivos Excel de produccion; trata `yukyu.db` como dato local.
- Manten fuera de control de versiones `uploads/`, `exports/`, `backups/`, `logs/`.

## Agentes Internos
- El sistema de agentes vive en `agents/`; consulta `AGENTS_SYSTEM.md` para APIs y flujos.
- Si cambias agentes o endpoints de analisis, actualiza la documentacion asociada.
