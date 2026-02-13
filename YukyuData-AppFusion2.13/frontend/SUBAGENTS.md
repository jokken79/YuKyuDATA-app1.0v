# 🤖 Subagentes Especializados para Yukyu Pro

Este documento describe los subagentes especializados disponibles para el desarrollo y mantenimiento de Yukyu Pro.

---

## 📋 Índice de Subagentes

| Subagente | Propósito | Cuándo Usar |
|-----------|-----------|-------------|
| **yukyu-analyzer** | Análisis profundo de código y datos | Debugging complejo, auditorías |
| **yukyu-refactor** | Refactorización segura de código | Mejoras de arquitectura |
| **yukyu-migrator** | Migraciones de datos y schema | Upgrades de versión |
| **yukyu-documenter** | Generación de documentación | Docs técnicos y de usuario |
| **yukyu-debugger** | Debugging especializado | Problemas específicos |
| **yukyu-security** | Auditoría de seguridad | Revisiones de seguridad |

---

## 🔍 yukyu-analyzer

**Propósito:** Análisis profundo de código, datos y flujos de la aplicación.

### Capacidades
- Análisis de dependencias entre módulos
- Detección de código muerto
- Análisis de complejidad ciclomática
- Profiling de uso de memoria
- Análisis de patrones de datos

### Cuándo Usar
```
Usar cuando necesites:
- Entender cómo fluyen los datos
- Encontrar dependencias ocultas
- Identificar código que puede eliminarse
- Analizar patrones de uso en localStorage
```

### Ejemplo de Invocación
```
Lanza el subagente yukyu-analyzer para:
1. Analizar el flujo de datos desde ExcelSync hasta Dashboard
2. Identificar todas las dependencias de balanceCalculator
3. Encontrar funciones no utilizadas en services/
```

### Outputs Típicos
- Diagramas de flujo de datos
- Reportes de dependencias
- Lista de código muerto
- Métricas de complejidad

---

## 🔧 yukyu-refactor

**Propósito:** Refactorización segura con preservación de funcionalidad.

### Capacidades
- Extracción de funciones/componentes
- Renombrado seguro (cross-references)
- Modernización de patrones
- Consolidación de código duplicado
- Migración a nuevos APIs

### Cuándo Usar
```
Usar cuando necesites:
- Extraer lógica compartida a un nuevo servicio
- Renombrar una función usada en múltiples lugares
- Convertir class components a functional
- Consolidar código repetido
```

### Ejemplo de Invocación
```
Lanza el subagente yukyu-refactor para:
1. Extraer la lógica de cálculo de períodos a un nuevo servicio
2. Renombrar 'getEmployeeBalance' a 'calculateBalance' en todo el codebase
3. Consolidar los patrones de validación duplicados
```

### Principios de Refactoring
- ✅ Cambios pequeños e incrementales
- ✅ Tests antes de refactorizar
- ✅ Commits atómicos
- ❌ No cambiar comportamiento
- ❌ No agregar features durante refactor

---

## 🔄 yukyu-migrator

**Propósito:** Migraciones seguras de datos y schema.

### Capacidades
- Creación de scripts de migración
- Backup automático pre-migración
- Validación post-migración
- Rollback en caso de error
- Migración de tipos TypeScript

### Cuándo Usar
```
Usar cuando necesites:
- Agregar nuevos campos a Employee
- Cambiar estructura de periodHistory
- Migrar de localStorage a IndexedDB
- Actualizar formato de fechas
```

### Ejemplo de Invocación
```
Lanza el subagente yukyu-migrator para:
1. Agregar campo 'department' a Employee
2. Migrar yukyuDates de string[] a {date, duration}[]
3. Crear migración reversible con rollback
```

### Flujo de Migración
```
1. Crear backup
2. Validar schema actual
3. Aplicar transformaciones
4. Validar schema nuevo
5. Guardar datos migrados
6. Log de cambios
```

---

## 📝 yukyu-documenter

**Propósito:** Generación automática de documentación.

### Capacidades
- Generación de JSDoc/TSDoc
- Documentación de APIs
- Guías de usuario
- Diagramas de arquitectura
- Changelogs automáticos

### Cuándo Usar
```
Usar cuando necesites:
- Documentar una nueva feature
- Generar docs de API para servicios
- Crear guía de usuario para un componente
- Actualizar README con cambios recientes
```

### Ejemplo de Invocación
```
Lanza el subagente yukyu-documenter para:
1. Generar JSDoc para todos los métodos de db.ts
2. Crear guía de usuario para ExcelSync
3. Documentar el flujo de aprobación con diagrama
```

### Formatos de Output
- Markdown (README, guías)
- TSDoc (código fuente)
- Mermaid (diagramas)
- HTML (documentación web)

---

## 🐛 yukyu-debugger

**Propósito:** Debugging especializado de problemas específicos.

### Capacidades
- Trazado de flujos de ejecución
- Inspección de estado en puntos clave
- Reproducción de bugs
- Análisis de logs
- Generación de casos de test

### Cuándo Usar
```
Usar cuando necesites:
- Debuggear por qué un balance es incorrecto
- Entender por qué un merge no funciona
- Reproducir un bug reportado
- Analizar un crash específico
```

### Ejemplo de Invocación
```
Lanza el subagente yukyu-debugger para:
1. Investigar por qué empleado HM0006 tiene balance negativo
2. Trazar el flujo de aprobación que causa el error DUPLICATE_DATE
3. Reproducir el bug de re-sync que sobrescribe datos
```

### Técnicas de Debugging
- Breakpoints virtuales (logs)
- Estado snapshots
- Diff de antes/después
- Reproducción paso a paso

---

## 🔒 yukyu-security

**Propósito:** Auditoría de seguridad y prevención de vulnerabilidades.

### Capacidades
- Detección de vulnerabilidades OWASP
- Auditoría de dependencias (npm audit)
- Análisis de código inseguro
- Verificación de sanitización
- Revisión de permisos

### Cuándo Usar
```
Usar cuando necesites:
- Revisar código antes de deploy
- Verificar que inputs están sanitizados
- Auditar dependencias npm
- Verificar protección contra XSS/injection
```

### Ejemplo de Invocación
```
Lanza el subagente yukyu-security para:
1. Auditar exportService.ts por vulnerabilidades de injection
2. Verificar sanitización de inputs en LeaveRequest
3. Revisar dependencias npm por vulnerabilidades conocidas
```

### Checklist de Seguridad
- [ ] No hay eval() o innerHTML sin sanitizar
- [ ] Inputs sanitizados (CSV, Excel)
- [ ] No hay secrets en código
- [ ] Dependencias actualizadas
- [ ] LocalStorage no expone datos sensibles

---

## 🚀 Guía de Uso de Subagentes

### Cuándo Lanzar Subagentes

| Situación | Subagente Recomendado |
|-----------|----------------------|
| "No entiendo cómo funciona X" | yukyu-analyzer |
| "Quiero mejorar la estructura de X" | yukyu-refactor |
| "Necesito agregar un campo nuevo" | yukyu-migrator |
| "Falta documentación de X" | yukyu-documenter |
| "Hay un bug en X" | yukyu-debugger |
| "Es seguro este código?" | yukyu-security |

### Formato de Invocación Recomendado

```markdown
Lanza el subagente [NOMBRE] para:

**Contexto:**
[Descripción del problema o necesidad]

**Objetivo:**
[Qué quieres lograr]

**Archivos relevantes:**
- archivo1.ts
- archivo2.tsx

**Restricciones:**
- No modificar X
- Mantener compatibilidad con Y
```

### Combinación de Subagentes

Algunos problemas requieren múltiples subagentes:

```
Refactoring complejo:
1. yukyu-analyzer → Entender impacto
2. yukyu-documenter → Documentar estado actual
3. yukyu-refactor → Hacer cambios
4. yukyu-debugger → Verificar funcionamiento
```

```
Nueva feature con migración:
1. yukyu-migrator → Migrar schema
2. yukyu-refactor → Implementar feature
3. yukyu-security → Verificar seguridad
4. yukyu-documenter → Documentar
```

---

## 📊 Comparativa de Subagentes

```
                    ANÁLISIS    MODIFICACIÓN    DOCUMENTACIÓN
yukyu-analyzer      ████████    ░░░░░░░░        ████░░░░
yukyu-refactor      ████░░░░    ████████        ██░░░░░░
yukyu-migrator      ████░░░░    ████████        ████░░░░
yukyu-documenter    ████░░░░    ██░░░░░░        ████████
yukyu-debugger      ████████    ██░░░░░░        ████░░░░
yukyu-security      ████████    ░░░░░░░░        ████░░░░
```

---

## 🔗 Integración con Skills

Los subagentes pueden complementar los skills existentes:

| Skill | Subagente Complementario |
|-------|-------------------------|
| yukyu-integrity-guardian | yukyu-debugger (para casos complejos) |
| yukyu-compliance-sentinel | yukyu-analyzer (para auditorías) |
| yukyu-excel-master | yukyu-debugger (problemas de import) |
| yukyu-performance-optimizer | yukyu-refactor (aplicar mejoras) |
| yukyu-test-suite | yukyu-debugger (reproducir bugs) |
| yukyu-ui-architect | yukyu-documenter (documentar componentes) |

---

## 📄 Licencia

MIT - Uso libre para empresas
