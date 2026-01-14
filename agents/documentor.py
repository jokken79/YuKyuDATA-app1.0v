"""
Documentor Agent - Agente de Documentación y Memoria
====================================================

Mantiene la "memoria" del sistema:
- Logging estructurado de todas las operaciones
- Historial de cambios (audit trail)
- Generación de documentación automática
- Snapshot del estado del sistema
- Búsqueda en historial
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Entrada en el audit log."""
    timestamp: str
    action: str
    entity_type: str
    entity_id: str
    user_id: Optional[str] = None
    old_values: Optional[Dict] = None
    new_values: Optional[Dict] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class SystemSnapshot:
    """Snapshot del estado del sistema."""
    timestamp: str
    employees_count: int
    genzai_count: int
    ukeoi_count: int
    pending_requests: int
    available_years: List[int]
    last_sync: Optional[str]
    database_size_kb: float
    health_status: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ActivityReport:
    """Reporte de actividad del sistema."""
    period_start: str
    period_end: str
    total_syncs: int
    total_requests: int
    approved_requests: int
    rejected_requests: int
    new_employees: int
    top_actions: List[Dict]

    def to_dict(self) -> Dict:
        return asdict(self)


class DocumentorAgent:
    """
    Agente Documentador - Memoria del Sistema

    Responsabilidades:
    - Logging estructurado de operaciones
    - Audit trail completo
    - Snapshots del estado del sistema
    - Generación de reportes de actividad
    - Búsqueda en historial

    Ejemplo de uso:
    ```python
    doc = DocumentorAgent()

    # Registrar una operación
    doc.log_operation('SYNC', 'employees', {'count': 100})

    # Obtener snapshot del sistema
    snapshot = doc.get_system_snapshot()

    # Buscar en historial
    results = doc.search_history('APPROVE', entity_type='leave_request')
    ```
    """

    def __init__(self, db_path: str = "yukyu.db", log_dir: str = "logs"):
        """
        Inicializa el agente documentador.

        Args:
            db_path: Ruta a la base de datos SQLite
            log_dir: Directorio para logs en archivo
        """
        self.db_path = db_path
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self._memory_log: List[AuditEntry] = []
        self._snapshots: List[SystemSnapshot] = []

        # Inicializar tabla de audit si no existe
        self._init_audit_table()

    def _init_audit_table(self):
        """Crea la tabla de audit log si no existe."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    user_id TEXT,
                    old_values TEXT,
                    new_values TEXT,
                    metadata TEXT
                )
            ''')

            # Índices para búsquedas rápidas
            conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id)')

            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"No se pudo crear tabla audit_log: {e}")

    # ========================================
    # LOGGING DE OPERACIONES
    # ========================================

    def log_operation(
        self,
        action: str,
        entity_type: str,
        entity_id: str = "",
        old_values: Dict = None,
        new_values: Dict = None,
        user_id: str = None,
        metadata: Dict = None
    ) -> AuditEntry:
        """
        Registra una operación en el sistema.

        Args:
            action: Tipo de acción (CREATE, UPDATE, DELETE, SYNC, APPROVE, etc.)
            entity_type: Tipo de entidad (employees, leave_request, etc.)
            entity_id: ID de la entidad afectada
            old_values: Valores anteriores (para UPDATE/DELETE)
            new_values: Valores nuevos (para CREATE/UPDATE)
            user_id: ID del usuario que realizó la acción
            metadata: Información adicional

        Returns:
            AuditEntry creada
        """
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata or {}
        )

        # Guardar en memoria
        self._memory_log.append(entry)

        # Guardar en BD
        self._persist_audit_entry(entry)

        # Log a consola
        logger.info(f"📝 [{action}] {entity_type}/{entity_id}")

        return entry

    def log_sync(self, source: str, records_count: int, details: Dict = None):
        """Registra una sincronización de datos."""
        return self.log_operation(
            action="SYNC",
            entity_type=source,
            entity_id=f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            new_values={"count": records_count, **(details or {})}
        )

    def log_leave_request(
        self,
        action: str,
        request_id: int,
        employee_num: str,
        details: Dict = None,
        user_id: str = None
    ):
        """Registra acción sobre solicitud de vacaciones."""
        return self.log_operation(
            action=action,  # CREATE, APPROVE, REJECT
            entity_type="leave_request",
            entity_id=str(request_id),
            new_values={"employee_num": employee_num, **(details or {})},
            user_id=user_id
        )

    def log_pipeline_execution(self, result):
        """Registra la ejecución de un pipeline."""
        return self.log_operation(
            action="PIPELINE_EXECUTION",
            entity_type="pipeline",
            entity_id=result.pipeline_name,
            new_values={
                "status": result.status.value,
                "tasks_count": len(result.tasks),
                "duration_ms": result.total_duration_ms
            }
        )

    def _persist_audit_entry(self, entry: AuditEntry):
        """Persiste entrada de audit en la BD."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO audit_log
                (timestamp, action, entity_type, entity_id, user_id, old_values, new_values, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.timestamp,
                entry.action,
                entry.entity_type,
                entry.entity_id,
                entry.user_id,
                json.dumps(entry.old_values) if entry.old_values else None,
                json.dumps(entry.new_values) if entry.new_values else None,
                json.dumps(entry.metadata) if entry.metadata else None
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Error persistiendo audit entry: {e}")

    # ========================================
    # SNAPSHOTS DEL SISTEMA
    # ========================================

    def get_system_snapshot(self) -> SystemSnapshot:
        """
        Captura el estado actual del sistema.

        Returns:
            SystemSnapshot con métricas actuales
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Contar registros
            employees_count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
            genzai_count = conn.execute("SELECT COUNT(*) FROM genzai").fetchone()[0]
            ukeoi_count = conn.execute("SELECT COUNT(*) FROM ukeoi").fetchone()[0]

            # Solicitudes pendientes
            pending = conn.execute(
                "SELECT COUNT(*) FROM leave_requests WHERE status = 'PENDING'"
            ).fetchone()[0]

            # Años disponibles
            years_rows = conn.execute(
                "SELECT DISTINCT year FROM employees ORDER BY year DESC"
            ).fetchall()
            years = [r[0] for r in years_rows]

            # Última sincronización
            last_sync_row = conn.execute(
                "SELECT timestamp FROM audit_log WHERE action = 'SYNC' ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            last_sync = last_sync_row[0] if last_sync_row else None

            conn.close()

            # Tamaño de BD
            db_size = Path(self.db_path).stat().st_size / 1024 if Path(self.db_path).exists() else 0

            snapshot = SystemSnapshot(
                timestamp=datetime.now().isoformat(),
                employees_count=employees_count,
                genzai_count=genzai_count,
                ukeoi_count=ukeoi_count,
                pending_requests=pending,
                available_years=years,
                last_sync=last_sync,
                database_size_kb=round(db_size, 2),
                health_status=self._check_health_status()
            )

            self._snapshots.append(snapshot)
            return snapshot

        except Exception as e:
            logger.error(f"Error obteniendo snapshot: {e}")
            return SystemSnapshot(
                timestamp=datetime.now().isoformat(),
                employees_count=0,
                genzai_count=0,
                ukeoi_count=0,
                pending_requests=0,
                available_years=[],
                last_sync=None,
                database_size_kb=0,
                health_status="ERROR"
            )

    def _check_health_status(self) -> str:
        """Verifica el estado de salud del sistema."""
        try:
            # Verificar conexión a BD
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT 1")
            conn.close()
            return "HEALTHY"
        except Exception:
            return "UNHEALTHY"

    # ========================================
    # BÚSQUEDA EN HISTORIAL
    # ========================================

    def search_history(
        self,
        action: str = None,
        entity_type: str = None,
        entity_id: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Busca en el historial de audit.

        Args:
            action: Filtrar por tipo de acción
            entity_type: Filtrar por tipo de entidad
            entity_id: Filtrar por ID de entidad
            start_date: Fecha inicio (ISO format)
            end_date: Fecha fin (ISO format)
            limit: Máximo de resultados

        Returns:
            Lista de entradas que coinciden
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []

            if action:
                query += " AND action = ?"
                params.append(action)

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            if entity_id:
                query += " AND entity_id = ?"
                params.append(entity_id)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += f" ORDER BY timestamp DESC LIMIT {limit}"

            rows = conn.execute(query, params).fetchall()
            conn.close()

            results = []
            for row in rows:
                entry = dict(row)
                # Parsear JSON fields
                if entry.get('old_values'):
                    entry['old_values'] = json.loads(entry['old_values'])
                if entry.get('new_values'):
                    entry['new_values'] = json.loads(entry['new_values'])
                if entry.get('metadata'):
                    entry['metadata'] = json.loads(entry['metadata'])
                results.append(entry)

            return results

        except Exception as e:
            logger.error(f"Error buscando en historial: {e}")
            return []

    def get_recent_activity(self, hours: int = 24) -> List[Dict]:
        """Obtiene actividad reciente."""
        start = (datetime.now() - timedelta(hours=hours)).isoformat()
        return self.search_history(start_date=start)

    def _count_new_employees(self, conn: sqlite3.Connection, start_date: str, end_date: str) -> int:
        """
        Count employees hired within a given period.

        Args:
            conn: SQLite connection
            start_date: Period start (ISO format)
            end_date: Period end (ISO format)

        Returns:
            Number of new employees hired in the period
        """
        try:
            # Check if hire_date column exists in genzai and ukeoi tables
            # Count from both tables (dispatch and contract employees)
            total = 0

            # Count from genzai (dispatch employees)
            try:
                genzai_count = conn.execute('''
                    SELECT COUNT(*) FROM genzai
                    WHERE hire_date IS NOT NULL
                    AND hire_date >= ?
                    AND hire_date <= ?
                    AND (leave_date IS NULL OR leave_date > ?)
                ''', (start_date, end_date, start_date)).fetchone()[0]
                total += genzai_count
            except sqlite3.OperationalError:
                # Table may not exist or have hire_date column
                pass

            # Count from ukeoi (contract employees)
            try:
                ukeoi_count = conn.execute('''
                    SELECT COUNT(*) FROM ukeoi
                    WHERE hire_date IS NOT NULL
                    AND hire_date >= ?
                    AND hire_date <= ?
                    AND (leave_date IS NULL OR leave_date > ?)
                ''', (start_date, end_date, start_date)).fetchone()[0]
                total += ukeoi_count
            except sqlite3.OperationalError:
                # Table may not exist or have hire_date column
                pass

            # Count from staff (office employees)
            try:
                staff_count = conn.execute('''
                    SELECT COUNT(*) FROM staff
                    WHERE hire_date IS NOT NULL
                    AND hire_date >= ?
                    AND hire_date <= ?
                    AND (leave_date IS NULL OR leave_date > ?)
                ''', (start_date, end_date, start_date)).fetchone()[0]
                total += staff_count
            except sqlite3.OperationalError:
                # Table may not exist or have hire_date column
                pass

            return total

        except Exception as e:
            logger.warning(f"Error counting new employees: {e}")
            return 0

    # ========================================
    # REPORTES DE ACTIVIDAD
    # ========================================

    def generate_activity_report(
        self,
        start_date: str,
        end_date: str
    ) -> ActivityReport:
        """
        Genera un reporte de actividad para un período.

        Args:
            start_date: Fecha inicio (ISO format)
            end_date: Fecha fin (ISO format)

        Returns:
            ActivityReport con métricas del período
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Contar syncs
            syncs = conn.execute('''
                SELECT COUNT(*) FROM audit_log
                WHERE action = 'SYNC' AND timestamp BETWEEN ? AND ?
            ''', (start_date, end_date)).fetchone()[0]

            # Contar requests
            total_requests = conn.execute('''
                SELECT COUNT(*) FROM audit_log
                WHERE action = 'CREATE' AND entity_type = 'leave_request'
                AND timestamp BETWEEN ? AND ?
            ''', (start_date, end_date)).fetchone()[0]

            approved = conn.execute('''
                SELECT COUNT(*) FROM audit_log
                WHERE action = 'APPROVE' AND entity_type = 'leave_request'
                AND timestamp BETWEEN ? AND ?
            ''', (start_date, end_date)).fetchone()[0]

            rejected = conn.execute('''
                SELECT COUNT(*) FROM audit_log
                WHERE action = 'REJECT' AND entity_type = 'leave_request'
                AND timestamp BETWEEN ? AND ?
            ''', (start_date, end_date)).fetchone()[0]

            # Top acciones
            top_actions_rows = conn.execute('''
                SELECT action, COUNT(*) as count FROM audit_log
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY action
                ORDER BY count DESC
                LIMIT 5
            ''', (start_date, end_date)).fetchall()

            top_actions = [{"action": r[0], "count": r[1]} for r in top_actions_rows]

            # Count new employees hired in this period
            new_employees = self._count_new_employees(conn, start_date, end_date)

            conn.close()

            return ActivityReport(
                period_start=start_date,
                period_end=end_date,
                total_syncs=syncs,
                total_requests=total_requests,
                approved_requests=approved,
                rejected_requests=rejected,
                new_employees=new_employees,
                top_actions=top_actions
            )

        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return ActivityReport(
                period_start=start_date,
                period_end=end_date,
                total_syncs=0,
                total_requests=0,
                approved_requests=0,
                rejected_requests=0,
                new_employees=0,
                top_actions=[]
            )

    # ========================================
    # EXPORTACIÓN
    # ========================================

    def export_audit_log(self, output_path: str, format: str = "json") -> bool:
        """
        Exporta el audit log a archivo.

        Args:
            output_path: Ruta del archivo de salida
            format: Formato (json, csv)

        Returns:
            True si exitoso
        """
        try:
            entries = self.search_history(limit=10000)

            if format == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(entries, f, ensure_ascii=False, indent=2)
            elif format == "csv":
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if entries:
                        writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                        writer.writeheader()
                        writer.writerows(entries)

            logger.info(f"✅ Audit log exportado a {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exportando audit log: {e}")
            return False

    def get_memory_log(self, limit: int = 100) -> List[Dict]:
        """Obtiene el log en memoria (sesión actual)."""
        return [e.to_dict() for e in self._memory_log[-limit:]]


# Instancia global
_documentor_instance: Optional[DocumentorAgent] = None


def get_documentor() -> DocumentorAgent:
    """Obtiene la instancia global del documentador."""
    global _documentor_instance
    if _documentor_instance is None:
        _documentor_instance = DocumentorAgent()
    return _documentor_instance
