"""
YUKYU PREMIUM - Sistema de Agentes Inteligentes
================================================

Sistema completo de 12 agentes especializados para análisis y gestión.

Agentes Disponibles:
--------------------

1. OrchestratorAgent (Coordinador Central)
   - Coordina todos los agentes especializados
   - Ejecuta pipelines de tareas
   - Análisis completo del proyecto
   - Ejecución paralela de análisis

2. NerdAgent (Análisis Técnico Profundo)
   - Análisis de código y arquitectura
   - Detección de code smells
   - Métricas de complejidad ciclomática
   - Análisis de seguridad en código

3. UIDesignerAgent (Diseño Visual)
   - Análisis de CSS/SCSS
   - Auditoría de Design System
   - Generación de paletas de colores
   - Exportación de tokens para Figma

4. UXAnalystAgent (Experiencia de Usuario)
   - Evaluación heurística (Nielsen)
   - Análisis de flujos de usuario
   - Detección de puntos de fricción
   - Análisis de formularios

5. SecurityAgent (Seguridad y Hardening)
   - Escaneo OWASP Top 10
   - Detección de secretos expuestos
   - Análisis de SQL Injection/XSS
   - Verificación de configuración

6. PerformanceAgent (Optimización)
   - Detección de queries N+1
   - Análisis de complejidad algorítmica
   - Análisis de bundle size
   - Optimización de assets

7. TestingAgent (QA Automatizado)
   - Análisis de cobertura de tests
   - Detección de tests frágiles
   - Sugerencias de tests
   - Análisis de testabilidad

8. DataParserAgent (Parsing de Datos)
   - Parsing flexible de Excel/CSV
   - Detección automática de headers
   - Validación de datos
   - Detección de anomalías

9. ComplianceAgent (Cumplimiento Legal)
   - Verificación de ley laboral japonesa
   - 5日取得義務 (5-day minimum rule)
   - Alertas de expiración
   - 年次有給休暇管理簿 (Annual ledger)

10. DocumentorAgent (Documentación)
    - Logging estructurado
    - Audit trail
    - Snapshots del sistema
    - Reportes de actividad

11. FigmaAgent (Integración Figma)
    - Exportación de Design Tokens
    - Generación de Figma Variables
    - Sincronización de Design System
    - Formato Tokens Studio

12. CanvasAgent (Canvas/SVG)
    - Análisis de archivos SVG
    - Optimización de SVG
    - Generación de gráficos (Chart.js/ApexCharts)
    - Análisis de código Canvas

Uso Básico:
-----------

```python
from agents import get_orchestrator, AgentType

# Obtener el orquestador
orchestrator = get_orchestrator()

# Análisis completo del proyecto
report = orchestrator.run_full_analysis()
print(f"Salud general: {report.overall_health}%")

# Pipeline de seguridad
security_result = orchestrator.orchestrate_security_audit()

# Usar un agente específico
from agents import NerdAgent
nerd = NerdAgent()
issues = nerd.analyze_file("main.py")

# Pipeline personalizado
result = orchestrator.execute_pipeline("custom", [
    ("security", AgentType.SECURITY, "audit_security", {}),
    ("performance", AgentType.PERFORMANCE, "analyze_performance", {}),
])
```

Pipelines Predefinidos:
-----------------------

- orchestrate_full_sync(excel_path): Sincronización completa de datos
- orchestrate_compliance_check(year): Verificación de cumplimiento
- orchestrate_security_audit(): Auditoría de seguridad
- orchestrate_code_review(): Revisión de código
- orchestrate_ui_ux_audit(): Auditoría UI/UX
"""

# Orquestador Central
from .orchestrator import (
    OrchestratorAgent,
    get_orchestrator,
    TaskStatus,
    TaskResult,
    PipelineResult,
    FullAnalysisReport,
    AgentType
)

# Agentes Originales
from .data_parser import DataParserAgent
from .documentor import DocumentorAgent
from .compliance import ComplianceAgent

# Nuevos Agentes Especializados
from .nerd import NerdAgent, get_nerd_agent
from .ui_designer import UIDesignerAgent, get_ui_designer_agent
from .ux_analyst import UXAnalystAgent, get_ux_analyst_agent
from .security import SecurityAgent, get_security_agent
from .performance import PerformanceAgent, get_performance_agent
from .testing import TestingAgent, get_testing_agent
from .figma import FigmaAgent, get_figma_agent
from .canvas import CanvasAgent, get_canvas_agent

__all__ = [
    # Orquestador
    'OrchestratorAgent',
    'get_orchestrator',
    'TaskStatus',
    'TaskResult',
    'PipelineResult',
    'FullAnalysisReport',
    'AgentType',

    # Agentes Originales
    'DataParserAgent',
    'DocumentorAgent',
    'ComplianceAgent',

    # Nuevos Agentes
    'NerdAgent',
    'get_nerd_agent',
    'UIDesignerAgent',
    'get_ui_designer_agent',
    'UXAnalystAgent',
    'get_ux_analyst_agent',
    'SecurityAgent',
    'get_security_agent',
    'PerformanceAgent',
    'get_performance_agent',
    'TestingAgent',
    'get_testing_agent',
    'FigmaAgent',
    'get_figma_agent',
    'CanvasAgent',
    'get_canvas_agent',
]

# Versión del sistema de agentes
__version__ = "2.1.0"

# Metadata
__author__ = "YuKyuDATA Team"
__description__ = "Sistema de Agentes Inteligentes para Análisis de Proyectos"
