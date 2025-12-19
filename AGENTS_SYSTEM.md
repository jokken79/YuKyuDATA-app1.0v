# Sistema de Agentes Inteligentes - YuKyuDATA v2.0

## Visión General

El sistema de agentes de YuKyuDATA es una arquitectura modular de **10 agentes especializados** coordinados por un **Orquestador Central** que permite análisis completos y automatizados del proyecto.

```
                    ┌─────────────────────────────────────┐
                    │     🎯 ORCHESTRATOR AGENT          │
                    │   (Coordinador Central)             │
                    │                                     │
                    │  • Pipelines secuenciales           │
                    │  • Ejecución paralela               │
                    │  • Análisis completo                │
                    │  • Reportes consolidados            │
                    └───────────────┬─────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  🤓 NERD      │          │  🎨 UI        │          │  🎯 UX        │
│  Agent        │          │  Designer     │          │  Analyst      │
├───────────────┤          ├───────────────┤          ├───────────────┤
│ • AST parsing │          │ • CSS análisis│          │ • Heurísticas │
│ • Code smells │          │ • Paletas     │          │ • User flows  │
│ • Complejidad │          │ • Figma export│          │ • Formularios │
│ • Seguridad   │          │ • A11y audit  │          │ • Fricción    │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  🔒 SECURITY  │          │  ⚡ PERFORMANCE│         │  🧪 TESTING   │
│  Agent        │          │  Agent        │          │  Agent        │
├───────────────┤          ├───────────────┤          ├───────────────┤
│ • OWASP Top10 │          │ • N+1 queries │          │ • Coverage    │
│ • Secretos    │          │ • Bundle size │          │ • Test quality│
│ • SQL/XSS     │          │ • Assets      │          │ • Suggestions │
│ • Config      │          │ • Algoritmos  │          │ • Testability │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  📊 DATA      │          │  ⚖️ COMPLIANCE │         │  📝 DOCUMENTOR│
│  Parser       │          │  Agent        │          │  Agent        │
├───────────────┤          ├───────────────┤          ├───────────────┤
│ • Excel parse │          │ • 5日義務     │          │ • Audit log   │
│ • Validación  │          │ • Expiración  │          │ • Snapshots   │
│ • Anomalías   │          │ • Alertas     │          │ • Reportes    │
│ • Headers     │          │ • 管理簿      │          │ • Memoria     │
└───────────────┘          └───────────────┘          └───────────────┘
```

---

## Agentes Disponibles

### 1. OrchestratorAgent (Coordinador Central)

El "cerebro" del sistema que coordina todos los demás agentes.

**Ubicación:** `agents/orchestrator.py`

**Capacidades:**
- Ejecutar pipelines de tareas secuenciales
- Ejecutar análisis en paralelo (ThreadPoolExecutor)
- Coordinar análisis completo del proyecto
- Generar reportes consolidados
- Gestionar historial de ejecuciones

**Uso:**
```python
from agents import get_orchestrator, AgentType

orchestrator = get_orchestrator()

# Análisis completo (todos los agentes en paralelo)
report = orchestrator.run_full_analysis()
print(f"Salud general: {report.overall_health}%")

# Pipeline personalizado
result = orchestrator.execute_pipeline("mi_pipeline", [
    ("tarea1", AgentType.SECURITY, "audit_security", {}),
    ("tarea2", AgentType.PERFORMANCE, "analyze_performance", {}),
])

# Pipelines predefinidos
orchestrator.orchestrate_security_audit()
orchestrator.orchestrate_code_review()
orchestrator.orchestrate_ui_ux_audit()
orchestrator.orchestrate_compliance_check(2025)
```

---

### 2. NerdAgent (Análisis Técnico Profundo)

El "cerebro analítico" que examina el código en detalle.

**Ubicación:** `agents/nerd.py`

**Capacidades:**
- Análisis de código Python con AST parsing
- Detección de code smells (funciones largas, God Class, etc.)
- Métricas de complejidad ciclomática
- Análisis de seguridad (eval/exec, SQL injection patterns)
- Cálculo de deuda técnica

**Uso:**
```python
from agents import NerdAgent

nerd = NerdAgent()

# Analizar un archivo
issues = nerd.analyze_file("main.py")

# Analizar proyecto completo
report = nerd.analyze_project()
print(f"Salud: {report.overall_health}%")
print(f"Issues: {report.total_issues}")

# Métricas de un archivo
metrics = nerd.get_code_metrics("main.py")
print(f"Complejidad: {metrics.cyclomatic_complexity}")

# Estimación de deuda técnica
debt = nerd.get_tech_debt_estimate()
print(f"Horas para resolver: {debt['total_hours']}")
```

---

### 3. UIDesignerAgent (Diseño Visual)

Especialista en diseño de interfaces y sistemas visuales.

**Ubicación:** `agents/ui_designer.py`

**Capacidades:**
- Análisis de archivos CSS/SCSS
- Auditoría de Design System
- Generación de paletas de colores armónicas
- Verificación de contraste WCAG (AA/AAA)
- Exportación de tokens para Figma
- Análisis de accesibilidad visual

**Uso:**
```python
from agents import UIDesignerAgent

ui = UIDesignerAgent()

# Auditoría completa de UI
report = ui.audit_ui()
print(f"A11Y Score: {report.accessibility_score}%")

# Extraer Design System
ds = ui.extract_design_system()
print(f"Colores: {len(ds.colors)}")
print(f"Fuentes: {len(ds.fonts)}")

# Exportar tokens para Figma
ui.export_figma_tokens("design-tokens.json")

# Verificar contraste
ratio, compliance = ui.check_color_contrast("#333333", "#ffffff")
print(f"Ratio: {ratio}:1, WCAG AA: {compliance['AA_normal']}")

# Generar paleta de colores
palette = ui.generate_color_palette("#3498db", scheme="triadic")
```

---

### 4. UXAnalystAgent (Experiencia de Usuario)

Experto en UX que analiza y mejora la experiencia del usuario.

**Ubicación:** `agents/ux_analyst.py`

**Capacidades:**
- Evaluación heurística (10 heurísticas de Nielsen)
- Análisis de flujos de usuario
- Detección de puntos de fricción
- Análisis de formularios
- Análisis de microinteracciones
- Carga cognitiva

**Uso:**
```python
from agents import UXAnalystAgent

ux = UXAnalystAgent()

# Auditoría completa de UX
report = ux.audit_ux()
print(f"Usability Score: {report.usability_score}%")

# Evaluación heurística
issues = ux.heuristic_evaluation()
for issue in issues:
    print(f"[{issue.heuristic.value}] {issue.title}")

# Análisis de formularios
forms = ux.analyze_forms()
for form in forms:
    print(f"{form.name}: {form.score}%")

# Análisis de flujos de usuario
flows = ux.analyze_user_flows()
for flow in flows:
    print(f"{flow.name}: {flow.cognitive_load} carga")
```

---

### 5. SecurityAgent (Seguridad y Hardening)

Experto en seguridad de aplicaciones web.

**Ubicación:** `agents/security.py`

**Capacidades:**
- Escaneo OWASP Top 10 (2021)
- Detección de secretos expuestos (API keys, passwords)
- Análisis de SQL Injection
- Análisis de XSS
- Verificación de configuración de seguridad
- Cálculo de entropía para secretos

**Uso:**
```python
from agents import SecurityAgent

security = SecurityAgent()

# Auditoría completa de seguridad
report = security.audit_security()
print(f"Security Score: {report.security_score}%")
print(f"Críticos: {report.critical_count}")

# Buscar secretos expuestos
secrets = security.scan_for_secrets()
for secret in secrets:
    print(f"[{secret.secret_type}] {secret.file_path}:{secret.line_number}")

# Escanear OWASP Top 10
vulns = security.scan_owasp_top_10()
for vuln in vulns:
    print(f"[{vuln.severity.value}] {vuln.title}")

# Analizar configuración
config = security.analyze_security_config()
print(f"HTTPS: {config.has_https}")
print(f"Rate Limiting: {config.has_rate_limiting}")
```

---

### 6. PerformanceAgent (Optimización)

Experto en análisis y optimización de rendimiento.

**Ubicación:** `agents/performance.py`

**Capacidades:**
- Detección de queries N+1
- Análisis de complejidad algorítmica
- Análisis de bundle size (JS/CSS)
- Optimización de assets/imágenes
- Detección de memory leaks potenciales

**Uso:**
```python
from agents import PerformanceAgent

perf = PerformanceAgent()

# Análisis completo de rendimiento
report = perf.analyze_performance()
print(f"Performance Score: {report.performance_score}%")

# Análisis de base de datos
db_issues, db_metrics = perf.analyze_database_performance()
print(f"N+1 potenciales: {len(db_metrics.potential_n_plus_1)}")

# Análisis de código
code_issues = perf.analyze_code_performance()

# Análisis de bundle
bundle_issues, bundle_metrics = perf.analyze_bundle_size()
print(f"JS total: {bundle_metrics.total_js_size_kb:.0f}KB")

# Análisis de assets
asset_issues, asset_metrics = perf.analyze_assets()
print(f"Imágenes: {asset_metrics.total_images_size_mb:.1f}MB")
```

---

### 7. TestingAgent (QA Automatizado)

Experto en calidad y testing.

**Ubicación:** `agents/testing.py`

**Capacidades:**
- Análisis de cobertura de tests (estático)
- Detección de código sin tests
- Análisis de calidad de tests existentes
- Detección de tests frágiles
- Generación de sugerencias de tests

**Uso:**
```python
from agents import TestingAgent

qa = TestingAgent()

# Análisis completo de testing
report = qa.analyze_testing()
print(f"Testing Score: {report.testing_score}%")
print(f"Cobertura: {report.coverage.coverage_percentage:.1f}%")

# Análisis de cobertura
coverage = qa.analyze_coverage()
print(f"Funciones sin test: {len(coverage.untested_functions)}")

# Calidad de tests
quality_issues, test_files = qa.analyze_test_quality()
for issue in quality_issues:
    print(f"[{issue.category.value}] {issue.title}")

# Generar sugerencias de tests
suggestions = qa.generate_test_suggestions()
for sug in suggestions:
    print(f"[{sug.priority}] Test para {sug.target_function}")

# Análisis de testabilidad
testability_issues = qa.analyze_testability()
```

---

### 8. DataParserAgent (Parsing de Datos)

Especializado en parsing y validación de datos Excel/CSV.

**Ubicación:** `agents/data_parser.py`

**Capacidades:**
- Detección automática de headers en Excel
- Mapeo flexible de columnas (japonés/inglés)
- Validación exhaustiva de datos
- Detección de anomalías
- Transformación de formatos

**Uso:**
```python
from agents import DataParserAgent

parser = DataParserAgent()

# Encontrar fila de headers
header_row, headers = parser.find_header_row(sheet)

# Parsear Excel
result = parser.parse_excel("archivo.xlsx")
print(f"Registros: {len(result.data)}")
print(f"Issues: {len(result.issues)}")

# Validar datos
validation = parser.validate_data(data)
print(f"Válido: {validation.is_valid}")
print(f"Errores: {validation.error_count}")
```

---

### 9. ComplianceAgent (Cumplimiento Legal)

Monitorea el cumplimiento con leyes laborales japonesas.

**Ubicación:** `agents/compliance.py`

**Capacidades:**
- Verificar 5日取得義務 (5-day minimum rule)
- Verificar reglas de carry-over (máx 2 años)
- Monitorear expiración de días
- Generar alertas de cumplimiento
- Crear 年次有給休暇管理簿 (libro de gestión)

**Uso:**
```python
from agents import ComplianceAgent

compliance = ComplianceAgent()

# Verificar 5-day rule para todos
results = compliance.check_all_5_day_compliance(2025)
for result in results:
    if not result.is_compliant:
        print(f"{result.employee_name}: {result.days_used}/5 días")

# Verificar expiración
expirations = compliance.check_expiring_balances(2025)

# Generar alertas
alerts = compliance.get_active_alerts()
for alert in alerts:
    print(f"[{alert.level.value}] {alert.message}")

# Generar libro anual
ledger = compliance.generate_annual_ledger(2025)
```

---

### 10. DocumentorAgent (Documentación y Memoria)

Mantiene la "memoria" del sistema.

**Ubicación:** `agents/documentor.py`

**Capacidades:**
- Logging estructurado de operaciones
- Historial de cambios (audit trail)
- Generación de snapshots del sistema
- Búsqueda en historial

**Uso:**
```python
from agents import DocumentorAgent

doc = DocumentorAgent()

# Registrar una operación
doc.log_operation('SYNC', 'employees', {'count': 100})

# Obtener snapshot del sistema
snapshot = doc.get_system_snapshot()
print(f"Empleados: {snapshot.employees_count}")

# Buscar en historial
results = doc.search_history('APPROVE', entity_type='leave_request')

# Reporte de actividad
activity = doc.get_activity_report(days=7)
```

---

## Pipelines Predefinidos

El Orquestador incluye pipelines listos para usar:

### 1. Análisis Completo
```python
report = orchestrator.run_full_analysis()
```
Ejecuta todos los agentes en paralelo y genera un reporte consolidado.

### 2. Auditoría de Seguridad
```python
result = orchestrator.orchestrate_security_audit()
```
Pasos: Escanear secretos → OWASP Top 10 → Verificar configuración

### 3. Revisión de Código
```python
result = orchestrator.orchestrate_code_review()
```
Pasos: Análisis Nerd → Seguridad → Performance

### 4. Auditoría UI/UX
```python
result = orchestrator.orchestrate_ui_ux_audit()
```
Pasos: UI Audit → UX Audit → Accesibilidad

### 5. Verificación de Compliance
```python
result = orchestrator.orchestrate_compliance_check(2025)
```
Pasos: 5-day rule → Expiración → Alertas

---

## Scores y Métricas

Cada agente produce un score de 0-100:

| Agente | Score | Significado |
|--------|-------|-------------|
| Nerd | `overall_health` | Salud del código |
| UI | `accessibility_score` | Accesibilidad WCAG |
| UX | `usability_score` | Usabilidad (Nielsen) |
| Security | `security_score` | Seguridad (OWASP) |
| Performance | `performance_score` | Rendimiento |
| Testing | `testing_score` | Calidad de tests |

**Cálculo de Salud General:**
```
overall_health = promedio(todos los scores)
```

---

## API Endpoints

El sistema expone endpoints en la API:

```
GET  /api/orchestrator/status        # Estado del orquestador
GET  /api/orchestrator/history       # Historial de pipelines
POST /api/orchestrator/run-full      # Ejecutar análisis completo
POST /api/orchestrator/run-security  # Auditoría de seguridad
POST /api/orchestrator/run-review    # Revisión de código
```

---

## Integración con la App

### Desde main.py

```python
from agents import get_orchestrator, AgentType

@app.get("/api/analysis/full")
async def run_full_analysis():
    orchestrator = get_orchestrator()
    report = orchestrator.run_full_analysis()
    return report.to_dict()

@app.get("/api/analysis/security")
async def run_security_analysis():
    orchestrator = get_orchestrator()
    result = orchestrator.orchestrate_security_audit()
    return result.to_dict()
```

### Desde Scripts

```python
#!/usr/bin/env python
from agents import get_orchestrator

if __name__ == "__main__":
    orchestrator = get_orchestrator("/path/to/project")
    report = orchestrator.run_full_analysis()

    print(f"Salud General: {report.overall_health}%")
    print(f"Issues Críticos: {len(report.critical_issues)}")

    for rec in report.recommendations:
        print(f"  - {rec}")
```

---

## Extensión del Sistema

### Crear un Nuevo Agente

1. Crear archivo `agents/mi_agente.py`:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class MiReporte:
    score: float
    issues: List[dict]

class MiAgente:
    def __init__(self, project_root: str = "."):
        self.project_root = project_root

    def analyze(self) -> MiReporte:
        # Tu lógica aquí
        return MiReporte(score=85.0, issues=[])
```

2. Agregar al `__init__.py`:

```python
from .mi_agente import MiAgente
__all__.append('MiAgente')
```

3. Registrar en el Orquestador:

```python
class AgentType(Enum):
    # ... existing
    MI_AGENTE = "mi_agente"

def _create_agent(self, agent_type: AgentType):
    # ... existing
    elif agent_type == AgentType.MI_AGENTE:
        from .mi_agente import MiAgente
        return MiAgente(self.project_root)
```

---

## Buenas Prácticas

1. **Usa el Orquestador** para análisis completos
2. **Agentes individuales** para tareas específicas
3. **Cachea resultados** si los usas frecuentemente
4. **Ejecuta en paralelo** cuando sea posible
5. **Prioriza issues críticos** antes de los menores

---

## Changelog

### v2.0.0 (2025-12-19)
- ✨ Nuevo: NerdAgent para análisis técnico profundo
- ✨ Nuevo: UIDesignerAgent para diseño visual
- ✨ Nuevo: UXAnalystAgent para experiencia de usuario
- ✨ Nuevo: SecurityAgent para seguridad OWASP
- ✨ Nuevo: PerformanceAgent para optimización
- ✨ Nuevo: TestingAgent para QA
- 🔄 Mejorado: OrchestratorAgent con ejecución paralela
- 🔄 Mejorado: Pipelines predefinidos
- 📊 Nuevo: FullAnalysisReport consolidado

### v1.0.0
- OrchestratorAgent básico
- DataParserAgent
- ComplianceAgent
- DocumentorAgent
