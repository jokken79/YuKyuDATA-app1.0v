# YuKyuDATA - Memoria del Proyecto

## Project Overview

| Campo | Valor |
|-------|-------|
| **Nombre** | YuKyuDATA |
| **Descripción** | Sistema de gestión de vacaciones pagadas (有給休暇) |
| **Stack** | FastAPI + SQLite/PostgreSQL + Vanilla JS |
| **Estado** | Producción v1.0 |
| **Idioma UI** | Japonés |
| **Idioma Código** | Inglés |
| **Idioma Docs** | Castellano |

---

## Decisions Log

### 2024 - ID Compuesto para Employees
**Contexto:** Necesitábamos trackear vacaciones por empleado Y año fiscal.

**Decisión:** Usar `{employee_num}_{year}` como Primary Key en tabla `employees`.

**Alternativas descartadas:**
1. Autoincrement ID - No permite identificar registros por año fácilmente
2. Composite key sin concatenar - Más complejo para queries

**Consecuencias:**
- Todo código debe formar el ID correctamente: `f"{emp_num}_{year}"`
- Queries eficientes por año
- Evita duplicados automáticamente

**Estado:** ✅ Implementado

---

### 2024 - Período Fiscal 21日〜20日
**Contexto:** El período fiscal japonés para vacaciones no coincide con mes calendario.

**Decisión:** Implementar lógica específica de período fiscal en `services/fiscal_year.py`.

**Razón:** Cumplimiento de 労働基準法 第39条 (Ley de Normas Laborales).

**Consecuencias:**
- No usar funciones de mes estándar para cálculos fiscales
- El día 21 de cada mes inicia nuevo período
- Abril-21 al Marzo-20 del siguiente año = 1 año fiscal

**Estado:** ✅ Implementado

---

### 2024 - LIFO para Deducciones de Vacaciones
**Contexto:** Cuando un empleado usa vacaciones, ¿de qué año se deducen primero?

**Decisión:** LIFO (Last In, First Out) - Deducir los días más nuevos primero.

**Razón:**
- Maximiza el uso de días que expiran más tarde
- Los días más viejos (con fecha de expiración más cercana) se preservan
- Beneficia al empleado

**Implementación:**
```python
# services/fiscal_year.py
def apply_lifo_deduction(emp_num, days, year):
    # Ordenar por fecha de otorgamiento DESCENDENTE
    grants = sorted(grants, key=lambda g: g.grant_date, reverse=True)
    # Deducir de los más nuevos primero
```

**Estado:** ✅ Implementado

---

### 2025-01 - ALLOWED_TABLES Whitelist (Security Fix P0)
**Contexto:** Vulnerabilidad crítica de SQL Injection en SearchService.

**Decisión:** Implementar whitelist `ALLOWED_TABLES` para todas las búsquedas.

**Código:**
```python
ALLOWED_TABLES = {'employees', 'genzai', 'ukeoi', 'staff'}
if table not in ALLOWED_TABLES:
    raise ValueError(f"Invalid table: {table}")
```

**Consecuencias:**
- Cualquier nueva tabla debe agregarse a la whitelist
- Búsquedas solo funcionan en tablas permitidas

**Estado:** ✅ Implementado

---

### 2025-01 - Paleta Cyan Unificada (#06b6d4)
**Contexto:** Inconsistencias visuales entre componentes.

**Decisión:** Cyan (#06b6d4) como color primario unificado.

**Archivos afectados:**
- `static/css/unified-design-system.css`
- `static/css/yukyu-tokens.css`

**Estado:** ✅ Implementado

---

## Patterns & Conventions

### Backend (Python/FastAPI)

```python
# Conexión a BD - SIEMPRE context manager
with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE year = ?", (year,))

# SQL - SIEMPRE parametrizado
c.execute("SELECT * FROM table WHERE id = ?", (id,))  # ✅
c.execute(f"SELECT * FROM table WHERE id = {id}")     # ❌ NUNCA

# Endpoint estructura
@app.post("/api/resource")
async def endpoint(
    request: RequestModel,
    csrf_token: str = Header(None, alias="X-CSRF-Token"),
    current_user: dict = Depends(get_current_user_optional)
):
    try:
        result = service.process(request)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend (JavaScript)

```javascript
// Datos dinámicos - SIEMPRE escapar
element.textContent = userData;          // ✅ Seguro
element.innerHTML = escapeHtml(userData); // ✅ Si necesitas HTML

// localStorage - SIEMPRE try-catch
try {
    const data = JSON.parse(localStorage.getItem('key'));
} catch (e) {
    localStorage.removeItem('key');
    return defaultValue;
}

// Eventos - cleanup en unmount
const handler = () => { ... };
element.addEventListener('click', handler);
// En cleanup:
element.removeEventListener('click', handler);
```

### Commits

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
refactor: Code refactoring
test: Add or update tests
chore: Maintenance tasks
```

---

## Bugs & Lessons Learned

### 2025-01 - SQL Injection en SearchService
**Síntoma:** El parámetro `table` se concatenaba directamente en SQL.

**Causa raíz:** Falta de validación de input para nombres de tabla.

**Solución:** Implementar whitelist `ALLOWED_TABLES`.

**Lección:**
> NUNCA confiar en input del usuario, incluso para valores que "parecen" seguros como nombres de tabla.

**Prevención:** Code review obligatorio para cualquier código que construya queries SQL.

---

### 2025-01 - localStorage Corrupto
**Síntoma:** App no cargaba si localStorage contenía JSON inválido.

**Causa raíz:** `JSON.parse()` sin try-catch.

**Solución:** Envolver todas las lecturas de localStorage en try-catch.

**Lección:**
> localStorage puede corromperse por diversas razones. Siempre manejar el error.

**Prevención:** Linter rule para detectar `JSON.parse(localStorage.getItem(...))` sin try-catch.

---

### 2024-XX - LIFO vs FIFO
**Síntoma:** Días de vacaciones se deducían en orden incorrecto.

**Causa raíz:** Implementación inicial usaba FIFO (más viejos primero).

**Solución:** Cambiar a LIFO (más nuevos primero).

**Lección:**
> Las reglas de negocio japonesas pueden ser contra-intuitivas. Verificar con experto en compliance.

---

## User Preferences

### Comunicación
- **Idioma:** Castellano
- **Emojis:** Solo si se piden explícitamente
- **Estilo:** Conciso, directo, técnico
- **Explicaciones:** Incluir el "por qué" cuando sea útil

### Código
- **Type hints:** Recomendados en Python
- **Docstrings:** En inglés para funciones públicas
- **Comentarios:** Solo cuando el código no es auto-explicativo
- **Tests:** Requeridos para funcionalidad nueva

### Git
- **Branch naming:** `claude/feature-name-{sessionId}`
- **Commits:** Conventional commits en inglés
- **PRs:** Descripción clara con test plan

---

## Known Issues

### Excel Sync
| Issue | Workaround |
|-------|------------|
| Archivo debe estar en raíz | Configurar ruta en `.env` si es diferente |
| Falla si Excel está abierto | Cerrar Excel antes de sync |
| Caracteres japoneses en Windows | Usar encoding UTF-8 |

### CSRF Token
| Issue | Workaround |
|-------|------------|
| Token expira | Frontend debe refrescar página |
| Header incorrecto | Usar exactamente `X-CSRF-Token` |

### Theme
| Issue | Workaround |
|-------|------------|
| Algunos componentes legacy sin light mode | Verificar ambos temas al hacer cambios |
| Transición brusca entre temas | CSS transition en `:root` |

---

## External Dependencies

### Python
| Dependencia | Versión | Uso |
|-------------|---------|-----|
| FastAPI | 0.109+ | Framework web |
| SQLAlchemy | 2.0+ | ORM (migración en progreso) |
| PyJWT | 2.8+ | Autenticación JWT |
| openpyxl | - | Lectura de Excel |
| passlib | - | Hashing de passwords |

### JavaScript
| Dependencia | Uso |
|-------------|-----|
| Chart.js | Gráficos |
| ApexCharts | Gráficos avanzados |

### Archivos de Datos
| Archivo | Propósito |
|---------|-----------|
| `有給休暇管理.xlsm` | Master de vacaciones |
| `【新】社員台帳(UNS)T　2022.04.05～.xlsm` | Registro de empleados |

---

## Session History

### 2025-01-22 - Integración de Agentes Elite
**Acciones:**
- Copiados 10 agentes del repositorio claude-agents-elite
- Creado agents-registry.json con workflows
- Establecida estructura de memoria

**Agentes agregados:**
- architect, critic, explorer (Core)
- debugger, reviewer, stuck (Quality)
- database, api-designer, data-sync, memory (Domain)

**Resultado:** Sistema de agentes extendido y documentado.

---

*Última actualización: 2025-01-22*
