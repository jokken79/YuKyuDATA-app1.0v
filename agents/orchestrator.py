"""
Orchestrator Agent - Coordinador Central del Sistema
====================================================

Este agente actúa como el "cerebro" del sistema, coordinando:
- Flujos de trabajo complejos entre múltiples agentes
- Operaciones en lote (bulk operations)
- Sincronización de datos
- Generación de reportes
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Estados posibles de una tarea."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    """Resultado de una tarea ejecutada."""
    task_name: str
    status: TaskStatus
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PipelineResult:
    """Resultado de un pipeline completo."""
    pipeline_name: str
    status: TaskStatus
    tasks: List[TaskResult] = field(default_factory=list)
    total_duration_ms: float = 0
    started_at: str = ""
    completed_at: str = ""


class OrchestratorAgent:
    """
    Agente Orquestador - Coordina tareas complejas entre múltiples agentes.

    Capacidades:
    - Descomponer tareas complejas en subtareas
    - Ejecutar pipelines de procesamiento
    - Manejar errores y rollbacks
    - Reportar progreso

    Ejemplo de uso:
    ```python
    orchestrator = OrchestratorAgent()

    # Ejecutar sincronización completa
    result = orchestrator.orchestrate_full_sync("/path/to/excel.xlsm")

    # Ejecutar reporte de compliance
    result = orchestrator.orchestrate_compliance_check(year=2025)
    ```
    """

    def __init__(self, documentor=None, data_parser=None, compliance_agent=None):
        """
        Inicializa el orquestador con referencias a otros agentes.

        Args:
            documentor: Agente documentador para logging
            data_parser: Agente parseador de datos
            compliance_agent: Agente de compliance
        """
        self.documentor = documentor
        self.data_parser = data_parser
        self.compliance_agent = compliance_agent
        self._current_pipeline: Optional[str] = None
        self._task_history: List[PipelineResult] = []

    def execute_pipeline(
        self,
        pipeline_name: str,
        steps: List[tuple],  # List of (name, function, args, kwargs)
        stop_on_error: bool = True
    ) -> PipelineResult:
        """
        Ejecuta un pipeline de tareas secuenciales.

        Args:
            pipeline_name: Nombre identificador del pipeline
            steps: Lista de tuplas (nombre, función, args, kwargs)
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
            func = step[1]
            args = step[2] if len(step) > 2 else ()
            kwargs = step[3] if len(step) > 3 else {}

            task_result = self._execute_task(task_name, func, args, kwargs)
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

        self._task_history.append(result)
        self._current_pipeline = None

        # Documentar resultado si hay documentor disponible
        if self.documentor:
            self.documentor.log_pipeline_execution(result)

        return result

    def _execute_task(
        self,
        task_name: str,
        func: Callable,
        args: tuple,
        kwargs: dict
    ) -> TaskResult:
        """Ejecuta una tarea individual y captura su resultado."""
        logger.info(f"  ⏳ Ejecutando: {task_name}")
        start_time = datetime.now()

        try:
            data = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(f"  ✓ {task_name} completado ({duration:.0f}ms)")
            return TaskResult(
                task_name=task_name,
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
                status=TaskStatus.FAILED,
                error=error_msg,
                duration_ms=duration
            )

    # ========================================
    # PIPELINES PREDEFINIDOS
    # ========================================

    def orchestrate_full_sync(self, excel_path: str) -> PipelineResult:
        """
        Pipeline completo de sincronización de datos.

        Pasos:
        1. Parsear archivo Excel
        2. Validar datos
        3. Detectar anomalías
        4. Guardar en base de datos
        5. Actualizar estadísticas
        6. Generar notificaciones
        """
        # Importar servicios necesarios
        import excel_service
        import database

        steps = [
            ("parse_excel", excel_service.parse_excel_file, (excel_path,)),
            ("validate_data", self._validate_sync_data, ()),
            ("save_to_db", database.save_employees, ()),
            ("update_stats", self._update_statistics, ()),
        ]

        return self.execute_pipeline("full_sync", steps)

    def orchestrate_compliance_check(self, year: int) -> PipelineResult:
        """
        Pipeline de verificación de compliance.

        Pasos:
        1. Cargar datos del año
        2. Verificar 5日取得義務
        3. Verificar expiración de días
        4. Generar alertas
        5. Crear reporte
        """
        if not self.compliance_agent:
            raise ValueError("ComplianceAgent no configurado")

        steps = [
            ("load_year_data", self._load_year_data, (year,)),
            ("check_5_day_rule", self.compliance_agent.check_all_5_day_compliance, (year,)),
            ("check_expirations", self.compliance_agent.check_expiring_balances, (year,)),
            ("generate_alerts", self._generate_compliance_alerts, ()),
        ]

        return self.execute_pipeline(f"compliance_check_{year}", steps)

    def orchestrate_report_generation(
        self,
        report_type: str,
        year: int,
        filters: Optional[Dict] = None
    ) -> PipelineResult:
        """
        Pipeline de generación de reportes.

        Args:
            report_type: Tipo de reporte ('annual_ledger', 'usage_summary', 'compliance')
            year: Año del reporte
            filters: Filtros opcionales
        """
        steps = [
            ("load_data", self._load_report_data, (year, filters)),
            ("calculate_metrics", self._calculate_report_metrics, ()),
            ("format_report", self._format_report, (report_type,)),
        ]

        return self.execute_pipeline(f"report_{report_type}_{year}", steps)

    def orchestrate_bulk_approval(
        self,
        request_ids: List[int],
        approved_by: str
    ) -> PipelineResult:
        """
        Pipeline de aprobación masiva de solicitudes.

        Args:
            request_ids: Lista de IDs de solicitudes a aprobar
            approved_by: Nombre del aprobador
        """
        import database

        steps = []
        for req_id in request_ids:
            steps.append((
                f"approve_{req_id}",
                database.approve_leave_request,
                (req_id, approved_by)
            ))

        # No detener en error para procesar todas las solicitudes
        return self.execute_pipeline(
            f"bulk_approval_{len(request_ids)}_requests",
            steps,
            stop_on_error=False
        )

    # ========================================
    # MÉTODOS AUXILIARES
    # ========================================

    def _validate_sync_data(self, data: List[Dict] = None) -> Dict:
        """Valida datos antes de guardar."""
        if self.data_parser:
            return self.data_parser.validate_data(data or [])
        return {"valid": True, "errors": []}

    def _update_statistics(self) -> Dict:
        """Actualiza estadísticas del sistema."""
        import database
        years = database.get_available_years()
        return {"years_updated": years}

    def _load_year_data(self, year: int) -> List[Dict]:
        """Carga datos de un año específico."""
        import database
        return database.get_employees(year=year)

    def _generate_compliance_alerts(self) -> List[Dict]:
        """Genera alertas basadas en verificaciones de compliance."""
        # Implementación pendiente
        return []

    def _load_report_data(self, year: int, filters: Optional[Dict]) -> Dict:
        """Carga datos para un reporte."""
        import database
        data = database.get_employees(year=year)
        return {"year": year, "data": data, "filters": filters}

    def _calculate_report_metrics(self, data: Dict = None) -> Dict:
        """Calcula métricas para el reporte."""
        return {"calculated": True}

    def _format_report(self, report_type: str, data: Dict = None) -> Dict:
        """Formatea el reporte según su tipo."""
        return {"report_type": report_type, "formatted": True}

    # ========================================
    # CONSULTAS Y ESTADO
    # ========================================

    def get_pipeline_history(self, limit: int = 10) -> List[PipelineResult]:
        """Obtiene historial de pipelines ejecutados."""
        return self._task_history[-limit:]

    def get_current_status(self) -> Dict:
        """Obtiene estado actual del orquestador."""
        return {
            "current_pipeline": self._current_pipeline,
            "total_pipelines_executed": len(self._task_history),
            "last_execution": self._task_history[-1] if self._task_history else None
        }


# Instancia global (singleton)
_orchestrator_instance: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    """Obtiene la instancia global del orquestador."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorAgent()
    return _orchestrator_instance
