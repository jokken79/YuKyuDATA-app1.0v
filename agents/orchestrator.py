"""
Orchestrator Agent - Coordinador Central del Sistema de Agentes
================================================================

El "cerebro" del sistema que orquesta todos los agentes especializados:
- NerdAgent: Análisis técnico profundo
- UIDesignerAgent: Diseño visual y Figma
- UXAnalystAgent: Experiencia de usuario
- SecurityAgent: Seguridad y hardening
- PerformanceAgent: Optimización de rendimiento
- TestingAgent: QA y cobertura
- DataParserAgent: Parsing de datos Excel
- ComplianceAgent: Cumplimiento legal japonés
- DocumentorAgent: Documentación y memoria
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Estados posibles de una tarea."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentType(Enum):
    """Tipos de agentes disponibles."""
    NERD = "nerd"
    UI_DESIGNER = "ui_designer"
    UX_ANALYST = "ux_analyst"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DATA_PARSER = "data_parser"
    COMPLIANCE = "compliance"
    DOCUMENTOR = "documentor"


@dataclass
class TaskResult:
    """Resultado de una tarea ejecutada."""
    task_name: str
    agent_type: Optional[AgentType]
    status: TaskStatus
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            'task_name': self.task_name,
            'agent_type': self.agent_type.value if self.agent_type else None,
            'status': self.status.value,
            'duration_ms': self.duration_ms,
            'error': self.error,
            'timestamp': self.timestamp
        }


@dataclass
class PipelineResult:
    """Resultado de un pipeline completo."""
    pipeline_name: str
    status: TaskStatus
    tasks: List[TaskResult] = field(default_factory=list)
    total_duration_ms: float = 0
    started_at: str = ""
    completed_at: str = ""
    summary: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'pipeline_name': self.pipeline_name,
            'status': self.status.value,
            'tasks_count': len(self.tasks),
            'successful': sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED),
            'failed': sum(1 for t in self.tasks if t.status == TaskStatus.FAILED),
            'total_duration_ms': self.total_duration_ms,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'summary': self.summary
        }


@dataclass
class FullAnalysisReport:
    """Reporte completo del análisis de todos los agentes."""
    timestamp: str
    nerd_report: Any
    ui_report: Any
    ux_report: Any
    security_report: Any
    performance_report: Any
    testing_report: Any
    overall_health: float
    critical_issues: List[Dict]
    recommendations: List[str]

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'overall_health': self.overall_health,
            'critical_issues_count': len(self.critical_issues),
            'scores': {
                'code_quality': getattr(self.nerd_report, 'overall_health', 0) if self.nerd_report else 0,
                'ui_accessibility': getattr(self.ui_report, 'accessibility_score', 0) if self.ui_report else 0,
                'ux_usability': getattr(self.ux_report, 'usability_score', 0) if self.ux_report else 0,
                'security': getattr(self.security_report, 'security_score', 0) if self.security_report else 0,
                'performance': getattr(self.performance_report, 'performance_score', 0) if self.performance_report else 0,
                'testing': getattr(self.testing_report, 'testing_score', 0) if self.testing_report else 0
            },
            'recommendations': self.recommendations[:10]
        }


class OrchestratorAgent:
    """
    Agente Orquestador - Coordinador Central del Sistema

    El "cerebro" que coordina todos los agentes especializados:

    Agentes Disponibles:
    - NerdAgent: Análisis técnico profundo del código
    - UIDesignerAgent: Diseño visual, CSS, accesibilidad
    - UXAnalystAgent: Experiencia de usuario, flujos
    - SecurityAgent: Vulnerabilidades, OWASP Top 10
    - PerformanceAgent: Optimización, N+1, bundle
    - TestingAgent: Cobertura, calidad de tests
    - DataParserAgent: Parsing de Excel/CSV
    - ComplianceAgent: Cumplimiento ley laboral japonesa
    - DocumentorAgent: Documentación y auditoría

    Capacidades:
    - Ejecutar pipelines de tareas secuenciales
    - Ejecutar análisis en paralelo
    - Coordinar análisis completo del proyecto
    - Generar reportes consolidados
    - Priorizar issues críticos

    Ejemplo de uso:
    ```python
    orchestrator = OrchestratorAgent()

    # Análisis completo del proyecto
    report = orchestrator.run_full_analysis()

    # Pipeline personalizado
    result = orchestrator.execute_pipeline("custom", [
        ("parse_data", AgentType.DATA_PARSER, "parse_excel", {"path": "file.xlsx"}),
        ("check_security", AgentType.SECURITY, "audit_security", {}),
    ])

    # Análisis rápido
    quick = orchestrator.run_quick_analysis()
    ```
    """

    def __init__(self, project_root: str = "."):
        """
        Inicializa el Orquestador con todos los agentes.

        Args:
            project_root: Ruta raíz del proyecto a analizar
        """
        self.project_root = project_root
        self._agents: Dict[AgentType, Any] = {}
        self._current_pipeline: Optional[str] = None
        self._task_history: List[PipelineResult] = []
        self._lock = threading.Lock()

        # Inicializar agentes lazy
        self._init_agents()

    def _init_agents(self):
        """Inicializa los agentes de forma lazy."""
        # Los agentes se cargan cuando se necesitan
        pass

    def _get_agent(self, agent_type: AgentType) -> Any:
        """Obtiene o crea un agente del tipo especificado."""
        if agent_type not in self._agents:
            self._agents[agent_type] = self._create_agent(agent_type)
        return self._agents[agent_type]

    def _create_agent(self, agent_type: AgentType) -> Any:
        """Crea una instancia del agente especificado."""
        try:
            if agent_type == AgentType.NERD:
                from .nerd import NerdAgent
                return NerdAgent(self.project_root)

            elif agent_type == AgentType.UI_DESIGNER:
                from .ui_designer import UIDesignerAgent
                return UIDesignerAgent(self.project_root)

            elif agent_type == AgentType.UX_ANALYST:
                from .ux_analyst import UXAnalystAgent
                return UXAnalystAgent(self.project_root)

            elif agent_type == AgentType.SECURITY:
                from .security import SecurityAgent
                return SecurityAgent(self.project_root)

            elif agent_type == AgentType.PERFORMANCE:
                from .performance import PerformanceAgent
                return PerformanceAgent(self.project_root)

            elif agent_type == AgentType.TESTING:
                from .testing import TestingAgent
                return TestingAgent(self.project_root)

            elif agent_type == AgentType.DATA_PARSER:
                from .data_parser import DataParserAgent
                return DataParserAgent()

            elif agent_type == AgentType.COMPLIANCE:
                from .compliance import ComplianceAgent
                return ComplianceAgent()

            elif agent_type == AgentType.DOCUMENTOR:
                from .documentor import DocumentorAgent
                return DocumentorAgent()

        except ImportError as e:
            logger.error(f"Error importando agente {agent_type.value}: {e}")
            return None

        return None

    # ========================================
    # EJECUCIÓN DE PIPELINES
    # ========================================

    def execute_pipeline(
        self,
        pipeline_name: str,
        steps: List[tuple],
        stop_on_error: bool = True
    ) -> PipelineResult:
        """
        Ejecuta un pipeline de tareas secuenciales.

        Args:
            pipeline_name: Nombre identificador del pipeline
            steps: Lista de tuplas (nombre, agent_type, method_name, kwargs)
            stop_on_error: Si True, detiene el pipeline ante cualquier error

        Returns:
            PipelineResult con el resultado de todas las tareas
        """
        result = PipelineResult(
            pipeline_name=pipeline_name,
            status=TaskStatus.IN_PROGRESS,
            started_at=datetime.now().isoformat()
        )

        self._current_pipeline = pipeline_name
        logger.info(f"🚀 Iniciando pipeline: {pipeline_name}")

        start_time = datetime.now()

        for step in steps:
            task_name = step[0]
            agent_type = step[1] if len(step) > 1 else None
            method_name = step[2] if len(step) > 2 else None
            kwargs = step[3] if len(step) > 3 else {}

            task_result = self._execute_task(task_name, agent_type, method_name, kwargs)
            result.tasks.append(task_result)

            if task_result.status == TaskStatus.FAILED and stop_on_error:
                result.status = TaskStatus.FAILED
                logger.error(f"❌ Pipeline {pipeline_name} falló en tarea: {task_name}")
                break
        else:
            result.status = TaskStatus.COMPLETED
            logger.info(f"✅ Pipeline {pipeline_name} completado exitosamente")

        end_time = datetime.now()
        result.total_duration_ms = (end_time - start_time).total_seconds() * 1000
        result.completed_at = end_time.isoformat()

        # Generar resumen
        result.summary = {
            'total_tasks': len(result.tasks),
            'successful': sum(1 for t in result.tasks if t.status == TaskStatus.COMPLETED),
            'failed': sum(1 for t in result.tasks if t.status == TaskStatus.FAILED)
        }

        with self._lock:
            self._task_history.append(result)

        self._current_pipeline = None
        return result

    def _execute_task(
        self,
        task_name: str,
        agent_type: Optional[AgentType],
        method_name: Optional[str],
        kwargs: dict
    ) -> TaskResult:
        """Ejecuta una tarea individual."""
        logger.info(f"  ⏳ Ejecutando: {task_name}")
        start_time = datetime.now()

        try:
            if agent_type and method_name:
                agent = self._get_agent(agent_type)
                if agent is None:
                    raise ValueError(f"Agente {agent_type.value} no disponible")

                method = getattr(agent, method_name, None)
                if method is None:
                    raise ValueError(f"Método {method_name} no existe en {agent_type.value}")

                data = method(**kwargs)
            else:
                data = None

            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"  ✓ {task_name} completado ({duration:.0f}ms)")

            return TaskResult(
                task_name=task_name,
                agent_type=agent_type,
                status=TaskStatus.COMPLETED,
                data=data,
                duration_ms=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = str(e)
            logger.error(f"  ✗ {task_name} falló: {error_msg}")

            return TaskResult(
                task_name=task_name,
                agent_type=agent_type,
                status=TaskStatus.FAILED,
                error=error_msg,
                duration_ms=duration
            )

    # ========================================
    # EJECUCIÓN EN PARALELO
    # ========================================

    def execute_parallel(
        self,
        tasks: List[tuple],
        max_workers: int = 4
    ) -> List[TaskResult]:
        """
        Ejecuta múltiples tareas en paralelo.

        Args:
            tasks: Lista de tuplas (nombre, agent_type, method_name, kwargs)
            max_workers: Número máximo de workers

        Returns:
            Lista de TaskResult
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}

            for task in tasks:
                task_name = task[0]
                agent_type = task[1] if len(task) > 1 else None
                method_name = task[2] if len(task) > 2 else None
                kwargs = task[3] if len(task) > 3 else {}

                future = executor.submit(
                    self._execute_task,
                    task_name, agent_type, method_name, kwargs
                )
                futures[future] = task_name

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        return results

    # ========================================
    # ANÁLISIS COMPLETO
    # ========================================

    def run_full_analysis(self, parallel: bool = True) -> FullAnalysisReport:
        """
        Ejecuta un análisis completo del proyecto con todos los agentes.

        Args:
            parallel: Si True, ejecuta agentes en paralelo

        Returns:
            FullAnalysisReport con todos los resultados
        """
        logger.info("🔬 Iniciando análisis completo del proyecto...")
        start_time = datetime.now()

        # Definir tareas de análisis
        analysis_tasks = [
            ("nerd_analysis", AgentType.NERD, "analyze_project", {}),
            ("ui_analysis", AgentType.UI_DESIGNER, "audit_ui", {}),
            ("ux_analysis", AgentType.UX_ANALYST, "audit_ux", {}),
            ("security_analysis", AgentType.SECURITY, "audit_security", {}),
            ("performance_analysis", AgentType.PERFORMANCE, "analyze_performance", {}),
            ("testing_analysis", AgentType.TESTING, "analyze_testing", {}),
        ]

        # Ejecutar análisis
        if parallel:
            results = self.execute_parallel(analysis_tasks)
        else:
            results = [
                self._execute_task(t[0], t[1], t[2], t[3])
                for t in analysis_tasks
            ]

        # Organizar resultados
        reports = {r.task_name: r.data for r in results if r.status == TaskStatus.COMPLETED}

        # Calcular salud general
        scores = []
        if reports.get('nerd_analysis'):
            scores.append(getattr(reports['nerd_analysis'], 'overall_health', 50))
        if reports.get('ui_analysis'):
            scores.append(getattr(reports['ui_analysis'], 'accessibility_score', 50))
        if reports.get('ux_analysis'):
            scores.append(getattr(reports['ux_analysis'], 'usability_score', 50))
        if reports.get('security_analysis'):
            scores.append(getattr(reports['security_analysis'], 'security_score', 50))
        if reports.get('performance_analysis'):
            scores.append(getattr(reports['performance_analysis'], 'performance_score', 50))
        if reports.get('testing_analysis'):
            scores.append(getattr(reports['testing_analysis'], 'testing_score', 50))

        overall_health = sum(scores) / len(scores) if scores else 0

        # Recopilar issues críticos
        critical_issues = []

        # De Nerd
        if reports.get('nerd_analysis'):
            for issue in getattr(reports['nerd_analysis'], 'issues', []):
                if hasattr(issue, 'severity') and issue.severity.value == 'critical':
                    critical_issues.append({
                        'source': 'nerd',
                        'title': issue.title,
                        'file': issue.file_path
                    })

        # De Security
        if reports.get('security_analysis'):
            for vuln in getattr(reports['security_analysis'], 'vulnerabilities', []):
                if hasattr(vuln, 'severity') and vuln.severity.value == 'critical':
                    critical_issues.append({
                        'source': 'security',
                        'title': vuln.title,
                        'file': vuln.file_path
                    })

        # Generar recomendaciones consolidadas
        recommendations = self._generate_consolidated_recommendations(reports)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Análisis completo terminado en {duration:.1f}s")
        logger.info(f"   Salud general: {overall_health:.1f}%")
        logger.info(f"   Issues críticos: {len(critical_issues)}")

        return FullAnalysisReport(
            timestamp=datetime.now().isoformat(),
            nerd_report=reports.get('nerd_analysis'),
            ui_report=reports.get('ui_analysis'),
            ux_report=reports.get('ux_analysis'),
            security_report=reports.get('security_analysis'),
            performance_report=reports.get('performance_analysis'),
            testing_report=reports.get('testing_analysis'),
            overall_health=overall_health,
            critical_issues=critical_issues,
            recommendations=recommendations
        )

    def run_quick_analysis(self) -> Dict[str, Any]:
        """
        Ejecuta un análisis rápido (solo security y performance).

        Returns:
            Dict con resultados resumidos
        """
        logger.info("⚡ Ejecutando análisis rápido...")

        tasks = [
            ("security_quick", AgentType.SECURITY, "scan_for_secrets", {}),
            ("performance_quick", AgentType.PERFORMANCE, "analyze_database_performance", {}),
        ]

        results = self.execute_parallel(tasks, max_workers=2)

        return {
            'timestamp': datetime.now().isoformat(),
            'results': [r.to_dict() for r in results]
        }

    def _generate_consolidated_recommendations(self, reports: Dict) -> List[str]:
        """Genera recomendaciones consolidadas de todos los análisis."""
        recs = []

        # Priorizar seguridad
        if reports.get('security_analysis'):
            sec = reports['security_analysis']
            if hasattr(sec, 'critical_count') and sec.critical_count > 0:
                recs.append(
                    f"🔴 CRÍTICO: {sec.critical_count} vulnerabilidades críticas de seguridad. "
                    "¡Resolver antes de cualquier deploy!"
                )

        # Performance
        if reports.get('performance_analysis'):
            perf = reports['performance_analysis']
            if hasattr(perf, 'database_metrics'):
                n1 = len(getattr(perf.database_metrics, 'potential_n_plus_1', []))
                if n1 > 0:
                    recs.append(
                        f"🐢 Performance: {n1} posibles queries N+1. "
                        "Esto puede causar lentitud severa."
                    )

        # Testing
        if reports.get('testing_analysis'):
            test = reports['testing_analysis']
            if hasattr(test, 'coverage'):
                cov = test.coverage.coverage_percentage
                if cov < 50:
                    recs.append(
                        f"🧪 Testing: Cobertura del {cov:.1f}%. "
                        "Objetivo recomendado: 80%+"
                    )

        # UX
        if reports.get('ux_analysis'):
            ux = reports['ux_analysis']
            if hasattr(ux, 'usability_score') and ux.usability_score < 70:
                recs.append(
                    f"🎯 UX: Score de usabilidad bajo ({ux.usability_score}%). "
                    "Revisa los problemas de experiencia de usuario."
                )

        # UI
        if reports.get('ui_analysis'):
            ui = reports['ui_analysis']
            if hasattr(ui, 'accessibility_score') and ui.accessibility_score < 70:
                recs.append(
                    f"👁️ Accesibilidad: Score bajo ({ui.accessibility_score}%). "
                    "Revisa contraste y estructura HTML."
                )

        # Si todo está bien
        if not recs:
            recs.append(
                "✅ ¡Excelente! El proyecto está en buen estado general. "
                "Continúa aplicando buenas prácticas."
            )

        return recs

    # ========================================
    # PIPELINES PREDEFINIDOS
    # ========================================

    def orchestrate_full_sync(self, excel_path: str) -> PipelineResult:
        """
        Pipeline completo de sincronización de datos.

        Pasos:
        1. Parsear archivo Excel
        2. Validar datos
        3. Guardar en base de datos
        4. Actualizar estadísticas
        """
        steps = [
            ("parse_excel", AgentType.DATA_PARSER, "parse_excel", {"file_path": excel_path}),
            ("validate_data", AgentType.DATA_PARSER, "validate_data", {}),
        ]

        return self.execute_pipeline("full_sync", steps)

    def orchestrate_compliance_check(self, year: int) -> PipelineResult:
        """
        Pipeline de verificación de compliance.

        Pasos:
        1. Verificar 5日取得義務
        2. Verificar expiración de días
        3. Generar alertas
        """
        steps = [
            ("check_5_day_rule", AgentType.COMPLIANCE, "check_all_5_day_compliance", {"year": year}),
            ("check_expirations", AgentType.COMPLIANCE, "check_expiring_balances", {"year": year}),
        ]

        return self.execute_pipeline(f"compliance_check_{year}", steps)

    def orchestrate_security_audit(self) -> PipelineResult:
        """
        Pipeline de auditoría de seguridad.

        Pasos:
        1. Escanear secretos
        2. Verificar OWASP Top 10
        3. Analizar configuración
        """
        steps = [
            ("scan_secrets", AgentType.SECURITY, "scan_for_secrets", {}),
            ("scan_owasp", AgentType.SECURITY, "scan_owasp_top_10", {}),
            ("analyze_config", AgentType.SECURITY, "analyze_security_config", {}),
        ]

        return self.execute_pipeline("security_audit", steps)

    def orchestrate_code_review(self) -> PipelineResult:
        """
        Pipeline de revisión de código.

        Pasos:
        1. Análisis técnico (Nerd)
        2. Análisis de seguridad
        3. Análisis de performance
        """
        steps = [
            ("nerd_analysis", AgentType.NERD, "analyze_project", {}),
            ("security_scan", AgentType.SECURITY, "scan_owasp_top_10", {}),
            ("perf_analysis", AgentType.PERFORMANCE, "analyze_code_performance", {}),
        ]

        return self.execute_pipeline("code_review", steps)

    def orchestrate_ui_ux_audit(self) -> PipelineResult:
        """
        Pipeline de auditoría UI/UX.

        Pasos:
        1. Auditoría de UI
        2. Auditoría de UX
        3. Análisis de accesibilidad
        """
        steps = [
            ("ui_audit", AgentType.UI_DESIGNER, "audit_ui", {}),
            ("ux_audit", AgentType.UX_ANALYST, "audit_ux", {}),
            ("a11y_check", AgentType.UI_DESIGNER, "audit_accessibility", {}),
        ]

        return self.execute_pipeline("ui_ux_audit", steps)

    # ========================================
    # CONSULTAS Y ESTADO
    # ========================================

    def get_pipeline_history(self, limit: int = 10) -> List[Dict]:
        """Obtiene historial de pipelines ejecutados."""
        with self._lock:
            return [p.to_dict() for p in self._task_history[-limit:]]

    def get_current_status(self) -> Dict:
        """Obtiene estado actual del orquestador."""
        return {
            "current_pipeline": self._current_pipeline,
            "total_pipelines_executed": len(self._task_history),
            "loaded_agents": [a.value for a in self._agents.keys()],
            "available_agents": [a.value for a in AgentType]
        }

    def get_agent_status(self) -> Dict[str, bool]:
        """Verifica qué agentes están disponibles."""
        status = {}
        for agent_type in AgentType:
            try:
                agent = self._get_agent(agent_type)
                status[agent_type.value] = agent is not None
            except Exception:
                status[agent_type.value] = False
        return status


# Instancia global (singleton)
_orchestrator_instance: Optional[OrchestratorAgent] = None


def get_orchestrator(project_root: str = ".") -> OrchestratorAgent:
    """Obtiene la instancia global del orquestador."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorAgent(project_root)
    return _orchestrator_instance
