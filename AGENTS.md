# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: punto de entrada de la app y registro principal de rutas.
- `routes/v1/`: endpoints versionados (`auth.py`, `employees.py`, `reports.py`, etc.).
- `services/`, `repositories/`, `middleware/`, `utils/`: logica de negocio, acceso a datos y utilidades transversales.
- `database/`, `orm/`, `alembic/`: capa de datos, modelos ORM y migraciones.
- `static/` y `templates/`: frontend (JS/CSS) y plantillas HTML.
- `tests/`: pruebas Python (`test_*.py`), Jest (`*.test.js`) y Playwright E2E (`tests/e2e/*.spec.js`).
- `scripts/`: scripts de calidad, despliegue, migracion y mantenimiento.

## Build, Test, and Development Commands
- `pip install -r requirements.txt`: instala dependencias Python.
- `npm install`: instala dependencias Node.
- `python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`: ejecuta la API en local.
- `npm run dev`: inicia webpack en desarrollo.
- `npm run build`: genera el bundle de produccion.
- `python -m pytest tests/ -v`: ejecuta la suite backend.
- `npm test` y `npm run test:coverage`: ejecuta tests Jest y cobertura.
- `npx playwright test`: ejecuta pruebas E2E.
- `pre-commit run --all-files`: ejecuta validaciones locales antes de commit.

## Coding Style & Naming Conventions
- Python: 4 espacios, `snake_case` para funciones/modulos, `PascalCase` para clases.
- JavaScript: ESLint obliga 2 espacios, comillas simples, punto y coma, `prefer-const`, sin `var`.
- CSS: Stylelint obliga 2 espacios y reglas de sintaxis estandar.
- Nombres de tests: Python `test_*.py`, Jest `*.test.js`, Playwright `*.spec.js`.
- Organiza cambios por dominio: por ejemplo, nueva logica de permisos en `routes/v1/leave_requests.py` y su servicio asociado.

## Testing Guidelines
- Usa marcadores de `pytest` definidos en `pytest.ini` (`unit`, `integration`, `e2e`, `slow`, etc.).
- Mantén cobertura en cambios criticos y agrega tests de regresion para cada bug corregido.
- En frontend, prioriza tests de unidad para modulos en `static/src` y E2E para flujos de usuario en `tests/e2e`.

## Commit & Pull Request Guidelines
- Sigue Conventional Commits: `type(scope): resumen` (ejemplo: `fix(auth): handle refresh token rotation`).
- Haz commits pequenos y atomicos; no mezcles refactor grande con nuevas features.
- Cada PR debe incluir descripcion clara, issue/ticket (si existe), evidencia de pruebas y capturas/video en cambios de UI.

## Security & Configuration Tips
- Copia `.env.example` a `.env` y nunca subas secretos reales.
- Ejecuta `scripts/check-secrets.sh` o `pre-commit` antes de push.
- Si tocas autenticacion o rate limiting, valida rutas protegidas y manejo de errores con tests.
