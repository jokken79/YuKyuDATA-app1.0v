# SISTEMA DE SKILLS Y SUBAGENTES - YuKyuDATA-app

**Versión:** 1.0
**Fecha:** 2026-01-09
**Autor:** Claude Opus 4.5

---

## VISIÓN GENERAL

Este documento describe el sistema completo de skills y subagentes diseñado para asistir en el desarrollo, mantenimiento y mejora continua de YuKyuDATA-app.

---

## ARQUITECTURA DEL SISTEMA

### Diagrama de Skills y Agentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORQUESTADOR PRINCIPAL                                │
│                    (agents/orchestrator.py - 721 LOC)                        │
│                                                                              │
│   Coordina todos los agentes y pipelines de análisis                        │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────────┐
          │                             │                                 │
          ▼                             ▼                                 ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   SKILLS CLAUDE     │   │   AGENTES PYTHON    │   │   SKILLS NUEVOS     │
│   (.claude/skills/) │   │   (agents/)         │   │   (CREADOS HOY)     │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
          │                             │                                 │
    ┌─────┴─────┐               ┌───────┴───────┐               ┌────────┴────────┐
    │           │               │               │               │                 │
    ▼           ▼               ▼               ▼               ▼                 ▼
┌───────┐  ┌────────┐     ┌────────┐     ┌────────┐     ┌──────────┐     ┌──────────┐
│Yukyu  │  │Frontend│     │Security│     │Testing │     │   App    │     │Intelli-  │
│Comply.│  │Design  │     │Agent   │     │Agent   │     │Optimizer │     │Testing   │
└───────┘  └────────┘     └────────┘     └────────┘     └──────────┘     └──────────┘
                                                               │
                                                   ┌───────────┼───────────┐
                                                   │           │           │
                                                   ▼           ▼           ▼
                                             ┌─────────┐ ┌─────────┐ ┌─────────┐
                                             │Code     │ │Full-    │ │Documenta│
                                             │Quality  │ │Stack    │ │tion Gen │
                                             │Master   │ │Architect│ │         │
                                             └─────────┘ └─────────┘ └─────────┘
```

---

## CATÁLOGO DE SKILLS

### Skills Existentes (Pre-existentes)

| Skill | Ubicación | Propósito |
|-------|-----------|-----------|
| **yukyu-compliance** | `.claude/skills/yukyu-compliance/` | Normativa japonesa 有給休暇 |
| **frontend-design** | `.claude/skills/frontend-design/` | Diseño de interfaces premium |
| **playwright** | `.claude/skills/playwright/` | Testing E2E automatizado |
| **excel-japanese-parser** | `.claude/skills/` | Parsing de Excel japonés |
| **japanese-labor-compliance** | `.claude/skills/` | Ley laboral japonesa |

### Skills Nuevos (Creados en esta sesión)

| Skill | Ubicación | Propósito |
|-------|-----------|-----------|
| **app-optimizer** | `.claude/skills/app-optimizer/` | Performance + seguridad integral |
| **intelligent-testing** | `.claude/skills/intelligent-testing/` | Testing avanzado con generación |
| **code-quality-master** | `.claude/skills/code-quality-master/` | Refactoring y code smells |
| **full-stack-architect** | `.claude/skills/full-stack-architect/` | Decisiones de arquitectura |
| **documentation-generator** | `.claude/skills/documentation-generator/` | Documentación automática |

---

## CATÁLOGO DE AGENTES

### Agentes Python Existentes

| Agente | Archivo | LOC | Especialización |
|--------|---------|-----|-----------------|
| **Orchestrator** | `orchestrator.py` | 721 | Coordinación de pipelines |
| **Nerd** | `nerd.py` | 946 | Análisis técnico profundo |
| **Security** | `security.py` | 885 | OWASP Top 10, secretos |
| **Performance** | `performance.py` | 789 | N+1, bundle size |
| **Testing** | `testing.py` | 899 | Cobertura, tests frágiles |
| **UI Designer** | `ui_designer.py` | 1,023 | WCAG, Design System |
| **UX Analyst** | `ux_analyst.py` | 943 | Nielsen heuristics |
| **Compliance** | `compliance.py` | 665 | Ley laboral japonesa |
| **Data Parser** | `data_parser.py` | 551 | Excel/CSV parsing |
| **Documentor** | `documentor.py` | 560 | Audit trail |
| **Canvas** | `canvas.py` | 817 | SVG/Canvas analysis |
| **Figma** | `figma.py` | 735 | Tokens para Figma |

---

## CÓMO USAR LOS SKILLS

### Invocación por Nombre

```bash
# En Claude Code CLI
/yukyu-compliance       # Verificación de cumplimiento japonés
/frontend-design        # Diseño de interfaces
/app-optimizer          # Optimización integral
/intelligent-testing    # Testing avanzado
/code-quality-master    # Calidad de código
/full-stack-architect   # Decisiones de arquitectura
/documentation-generator # Generación de docs
/playwright             # Testing E2E
```

### Ejemplo de Uso: app-optimizer

**Input:**
```
Analiza la performance y seguridad de main.py
```

**Output esperado:**
```json
{
    "performance": {
        "score": 75,
        "issues": [
            {"type": "N+1", "line": 234, "severity": "HIGH"},
            {"type": "MISSING_INDEX", "table": "employees", "column": "year"}
        ]
    },
    "security": {
        "score": 65,
        "vulnerabilities": [
            {"type": "MISSING_AUTH", "endpoint": "/api/employees", "severity": "CRITICAL"}
        ]
    }
}
```

### Ejemplo de Uso: intelligent-testing

**Input:**
```
Genera tests para calculate_granted_days en fiscal_year.py
```

**Output esperado:**
```python
import pytest
from fiscal_year import calculate_granted_days

class TestCalculateGrantedDays:
    @pytest.mark.parametrize("years,expected", [
        (0.0, 0),      # Bajo mínimo
        (0.5, 10),     # 6 meses exactos
        (1.5, 11),     # 1.5 años
        (6.5, 20),     # Máximo
    ])
    def test_grant_table_values(self, years, expected):
        assert calculate_granted_days(years) == expected
```

---

## PIPELINES PREDEFINIDOS

### Pipeline: Full Analysis
```python
# Ejecuta 6 agentes en paralelo
orchestrator.run_full_analysis()

# Incluye:
# 1. Nerd Agent → Code quality
# 2. Security Agent → OWASP scan
# 3. Performance Agent → N+1, bundle
# 4. Testing Agent → Coverage
# 5. UI Designer → WCAG
# 6. UX Analyst → Heuristics
```

### Pipeline: Compliance Check
```python
# Verificación de cumplimiento legal
orchestrator.orchestrate_compliance_check(year=2025)

# Incluye:
# 1. Check 5-day obligation
# 2. Expiring balances
# 3. Year-end carryover
# 4. Annual ledger generation
```

### Pipeline: Security Audit
```python
# Auditoría de seguridad completa
orchestrator.orchestrate_security_audit()

# Incluye:
# 1. OWASP Top 10 scan
# 2. Secret scanning
# 3. Dependency vulnerabilities
# 4. Configuration review
```

### Pipeline: Code Review
```python
# Revisión de código integral
orchestrator.orchestrate_code_review()

# Incluye:
# 1. Code smells detection
# 2. Complexity analysis
# 3. Test coverage
# 4. Documentation coverage
```

---

## MATRIZ DE CAPACIDADES

| Capacidad | Skills Involucrados | Agentes Involucrados |
|-----------|---------------------|----------------------|
| **Performance** | app-optimizer | performance.py, nerd.py |
| **Seguridad** | app-optimizer | security.py |
| **Testing** | intelligent-testing, playwright | testing.py |
| **Calidad** | code-quality-master | nerd.py |
| **Arquitectura** | full-stack-architect | orchestrator.py |
| **Documentación** | documentation-generator | documentor.py |
| **UI/UX** | frontend-design | ui_designer.py, ux_analyst.py |
| **Compliance** | yukyu-compliance | compliance.py |
| **Data** | excel-japanese-parser | data_parser.py |
| **Visualización** | - | canvas.py, figma.py |

---

## FLUJO DE TRABAJO RECOMENDADO

### 1. Desarrollo de Nueva Feature

```
┌─────────────────────────────────────────────────────────────┐
│  1. PLANIFICACIÓN                                            │
│     └── /full-stack-architect                                │
│         - Diseño de arquitectura                             │
│         - Trade-offs documentados                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. IMPLEMENTACIÓN                                           │
│     └── /code-quality-master                                 │
│         - Patrones de diseño                                 │
│         - Clean code                                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3. TESTING                                                  │
│     └── /intelligent-testing + /playwright                   │
│         - Unit tests generados                               │
│         - E2E tests                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  4. REVISIÓN                                                 │
│     └── /app-optimizer                                       │
│         - Performance check                                  │
│         - Security audit                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  5. DOCUMENTACIÓN                                            │
│     └── /documentation-generator                             │
│         - API docs                                           │
│         - Changelog                                          │
└─────────────────────────────────────────────────────────────┘
```

### 2. Mantenimiento y Debugging

```
Problema detectado
       │
       ▼
┌──────────────────┐    ┌──────────────────┐
│ Performance?     │───▶│ /app-optimizer   │
└──────────────────┘    │ Análisis N+1,    │
                        │ bundle, queries  │
                        └──────────────────┘
       │
       ▼
┌──────────────────┐    ┌──────────────────┐
│ Tests failing?   │───▶│/intelligent-testing│
└──────────────────┘    │ Flaky detection, │
                        │ test healing     │
                        └──────────────────┘
       │
       ▼
┌──────────────────┐    ┌──────────────────┐
│ Security issue?  │───▶│ /app-optimizer   │
└──────────────────┘    │ OWASP scan,      │
                        │ secret detection │
                        └──────────────────┘
       │
       ▼
┌──────────────────┐    ┌──────────────────┐
│ UI/UX problem?   │───▶│ /frontend-design │
└──────────────────┘    │ WCAG, usability  │
                        └──────────────────┘
```

### 3. Cumplimiento Legal (有給休暇)

```
Verificación mensual
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  /yukyu-compliance                                            │
│                                                               │
│  1. check_5day_compliance(year)    → Lista no conformes      │
│  2. check_expiring_balances()      → Alertas expiración      │
│  3. generate_annual_ledger()       → 年次有給休暇管理簿        │
│  4. export_compliance_report()     → Excel/PDF               │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## EXTENSIÓN DEL SISTEMA

### Crear Nuevo Skill

1. Crear directorio: `.claude/skills/nombre-skill/`
2. Crear archivo: `SKILL.md` con formato:

```markdown
---
name: nombre-skill
description: Descripción breve
---

# Nombre del Skill

[Contenido del skill...]
```

### Crear Nuevo Agente

1. Crear archivo: `agents/nuevo_agent.py`
2. Implementar clase con patrón Singleton:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class AgentResult:
    success: bool
    data: dict
    issues: List[dict]

class NuevoAgent:
    def __init__(self, project_root: str):
        self.project_root = project_root

    def analyze(self) -> AgentResult:
        # Implementación
        pass

_instance = None

def get_nuevo_agent(project_root: str) -> NuevoAgent:
    global _instance
    if _instance is None:
        _instance = NuevoAgent(project_root)
    return _instance
```

3. Registrar en `agents/__init__.py`
4. Añadir al orquestador si es necesario

---

## MÉTRICAS DEL SISTEMA

### Estadísticas Actuales

| Métrica | Valor |
|---------|-------|
| **Total Skills** | 10 |
| **Total Agentes Python** | 12 |
| **LOC Agentes** | 9,719 |
| **Skills Nuevos (hoy)** | 5 |
| **Pipelines Disponibles** | 6 |

### Cobertura por Área

| Área | Skills | Agentes | Cobertura |
|------|--------|---------|-----------|
| Performance | 1 | 2 | ⭐⭐⭐⭐⭐ |
| Seguridad | 1 | 1 | ⭐⭐⭐⭐ |
| Testing | 2 | 1 | ⭐⭐⭐⭐⭐ |
| Calidad | 1 | 1 | ⭐⭐⭐⭐ |
| Arquitectura | 1 | 1 | ⭐⭐⭐⭐ |
| Documentación | 1 | 1 | ⭐⭐⭐⭐ |
| UI/UX | 1 | 2 | ⭐⭐⭐⭐⭐ |
| Compliance | 2 | 1 | ⭐⭐⭐⭐⭐ |
| Data Parsing | 1 | 1 | ⭐⭐⭐⭐ |

---

## CONCLUSIÓN

Este sistema de skills y subagentes proporciona una cobertura completa para el desarrollo, mantenimiento y mejora de YuKyuDATA-app:

- **10 Skills** que cubren desde diseño hasta compliance
- **12 Agentes Python** para análisis automatizado
- **6 Pipelines** predefinidos para flujos comunes
- **Extensible** mediante creación de nuevos skills y agentes

El sistema está diseñado para trabajar de forma coordinada a través del Orquestador, permitiendo análisis completos en paralelo y flujos de trabajo automatizados.

---

*Documentación generada por Claude Opus 4.5*
*YuKyuDATA-app v1.0 - 2026-01-09*
