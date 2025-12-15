"""
Compliance Agent - Agente de Cumplimiento Legal
================================================

Monitorea y asegura cumplimiento con leyes laborales japonesas:
- 5日取得義務 (Obligación de usar 5 días mínimo)
- 繰越ルール (Reglas de carry-over, max 2 años)
- 年次有給休暇管理簿 (Libro de gestión obligatorio)
- Alertas de expiración
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Niveles de alerta."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ComplianceStatus(Enum):
    """Estados de cumplimiento."""
    COMPLIANT = "compliant"
    AT_RISK = "at_risk"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


@dataclass
class ComplianceAlert:
    """Alerta de cumplimiento."""
    alert_id: str
    level: AlertLevel
    type: str
    employee_num: str
    employee_name: str
    message: str
    message_ja: str  # Mensaje en japonés
    details: Dict = field(default_factory=dict)
    action_required: str = ""
    due_date: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class FiveDayCheck:
    """Resultado de verificación de 5日取得義務."""
    employee_num: str
    employee_name: str
    year: int
    days_used: float
    days_required: float = 5.0
    is_compliant: bool = False
    days_remaining: float = 0.0
    status: ComplianceStatus = ComplianceStatus.UNKNOWN

    def __post_init__(self):
        self.is_compliant = self.days_used >= self.days_required
        self.days_remaining = max(0, self.days_required - self.days_used)

        if self.is_compliant:
            self.status = ComplianceStatus.COMPLIANT
        elif self.days_used >= 3:
            self.status = ComplianceStatus.AT_RISK
        else:
            self.status = ComplianceStatus.NON_COMPLIANT


@dataclass
class ExpirationCheck:
    """Resultado de verificación de expiración."""
    employee_num: str
    employee_name: str
    expiring_days: float
    expiry_date: str
    days_until_expiry: int
    alert_level: AlertLevel


@dataclass
class AnnualLedgerEntry:
    """Entrada en el 年次有給休暇管理簿."""
    employee_num: str
    employee_name: str
    grant_date: str  # 基準日
    granted_days: float  # 付与日数
    used_dates: List[str]  # 取得日
    used_days: float  # 取得日数
    remaining_days: float  # 残日数
    year: int


class ComplianceAgent:
    """
    Agente de Compliance - Cumplimiento con Ley Laboral Japonesa

    Funciones principales:
    - Verificar 5日取得義務 (5-day minimum rule)
    - Detectar días próximos a expirar
    - Generar alertas de cumplimiento
    - Crear 年次有給休暇管理簿 (Annual leave ledger)

    Reglas implementadas:

    1. 5日取得義務 (desde abril 2019):
       - Empleados con 10+ días deben usar mínimo 5 días/año
       - Empresa puede designar fechas si empleado no las usa

    2. 繰越 (Carry-over):
       - Máximo 2 años de validez
       - Uso FIFO (días más antiguos primero)
       - Max acumulación ~40 días

    3. 年次有給休暇管理簿:
       - Obligatorio mantener 3 años
       - Debe incluir: 基準日, 日数, 時季

    Ejemplo de uso:
    ```python
    compliance = ComplianceAgent()

    # Verificar 5日 para un empleado
    check = compliance.check_5_day_compliance("12345", 2025)

    # Verificar todos los empleados
    results = compliance.check_all_5_day_compliance(2025)

    # Obtener alertas activas
    alerts = compliance.get_active_alerts()
    ```
    """

    # Constantes de ley laboral japonesa
    JAPAN_LABOR_RULES = {
        'minimum_annual_use': 5,          # 5日取得義務
        'minimum_days_for_rule': 10,      # Aplica si tiene 10+ días
        'carry_over_years': 2,            # 2年繰越
        'max_accumulation': 40,           # Máximo ~40 días
        'ledger_retention_years': 3,      # Mantener registro 3 años
    }

    # Tabla de días otorgados por antigüedad
    GRANT_TABLE = {
        0.5: 10,   # 6 meses
        1.5: 11,   # 1 año 6 meses
        2.5: 12,   # 2 años 6 meses
        3.5: 14,   # 3 años 6 meses
        4.5: 16,   # 4 años 6 meses
        5.5: 18,   # 5 años 6 meses
        6.5: 20,   # 6+ años
    }

    def __init__(self, db_path: str = "yukyu.db"):
        """
        Inicializa el agente de compliance.

        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = db_path
        self._alerts: List[ComplianceAlert] = []

    # ========================================
    # VERIFICACIÓN DE 5日取得義務
    # ========================================

    def check_5_day_compliance(
        self,
        employee_num: str,
        year: int
    ) -> FiveDayCheck:
        """
        Verifica cumplimiento de 5日取得義務 para un empleado.

        Args:
            employee_num: Número de empleado
            year: Año a verificar

        Returns:
            FiveDayCheck con resultado de verificación
        """
        import sqlite3

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            row = conn.execute('''
                SELECT employee_num, name, granted, used, year
                FROM employees
                WHERE employee_num = ? AND year = ?
            ''', (employee_num, year)).fetchone()

            conn.close()

            if not row:
                return FiveDayCheck(
                    employee_num=employee_num,
                    employee_name="Unknown",
                    year=year,
                    days_used=0,
                    status=ComplianceStatus.UNKNOWN
                )

            # Solo aplica si tiene 10+ días
            if row['granted'] < self.JAPAN_LABOR_RULES['minimum_days_for_rule']:
                return FiveDayCheck(
                    employee_num=employee_num,
                    employee_name=row['name'],
                    year=year,
                    days_used=row['used'],
                    days_required=0,  # No aplica
                    is_compliant=True,
                    status=ComplianceStatus.COMPLIANT
                )

            return FiveDayCheck(
                employee_num=employee_num,
                employee_name=row['name'],
                year=year,
                days_used=row['used']
            )

        except Exception as e:
            logger.error(f"Error verificando compliance: {e}")
            return FiveDayCheck(
                employee_num=employee_num,
                employee_name="Error",
                year=year,
                days_used=0,
                status=ComplianceStatus.UNKNOWN
            )

    def check_all_5_day_compliance(self, year: int) -> Dict:
        """
        Verifica 5日取得義務 para todos los empleados.

        Args:
            year: Año a verificar

        Returns:
            Dict con resumen y lista de verificaciones
        """
        import sqlite3

        results = {
            'year': year,
            'total_checked': 0,
            'compliant': 0,
            'at_risk': 0,
            'non_compliant': 0,
            'not_applicable': 0,
            'checks': []
        }

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            rows = conn.execute('''
                SELECT employee_num, name, granted, used
                FROM employees
                WHERE year = ?
            ''', (year,)).fetchall()

            conn.close()

            for row in rows:
                # Skip si no tiene suficientes días
                if row['granted'] < self.JAPAN_LABOR_RULES['minimum_days_for_rule']:
                    results['not_applicable'] += 1
                    continue

                check = FiveDayCheck(
                    employee_num=row['employee_num'],
                    employee_name=row['name'],
                    year=year,
                    days_used=row['used']
                )

                results['total_checked'] += 1
                results['checks'].append(check)

                if check.status == ComplianceStatus.COMPLIANT:
                    results['compliant'] += 1
                elif check.status == ComplianceStatus.AT_RISK:
                    results['at_risk'] += 1
                else:
                    results['non_compliant'] += 1

                    # Crear alerta si no cumple
                    self._create_5day_alert(check)

            # Calcular porcentaje de cumplimiento
            if results['total_checked'] > 0:
                results['compliance_rate'] = round(
                    (results['compliant'] / results['total_checked']) * 100, 1
                )
            else:
                results['compliance_rate'] = 100.0

            return results

        except Exception as e:
            logger.error(f"Error en verificación masiva: {e}")
            return results

    def _create_5day_alert(self, check: FiveDayCheck):
        """Crea una alerta por incumplimiento de 5日."""
        if check.status == ComplianceStatus.NON_COMPLIANT:
            alert = ComplianceAlert(
                alert_id=f"5day_{check.employee_num}_{check.year}",
                level=AlertLevel.CRITICAL,
                type="5_DAY_VIOLATION",
                employee_num=check.employee_num,
                employee_name=check.employee_name,
                message=f"Employee has only used {check.days_used} of required 5 days",
                message_ja=f"5日取得義務未達成: 現在{check.days_used}日のみ取得 (残り{check.days_remaining}日必要)",
                details={
                    'days_used': check.days_used,
                    'days_remaining': check.days_remaining,
                    'year': check.year
                },
                action_required="従業員に取得を促すか、会社が時季指定を行う必要があります"
            )
            self._alerts.append(alert)

    # ========================================
    # VERIFICACIÓN DE EXPIRACIÓN
    # ========================================

    def check_expiring_balances(
        self,
        year: int,
        warning_days: int = 30
    ) -> List[ExpirationCheck]:
        """
        Detecta balances próximos a expirar.

        Args:
            year: Año fiscal actual
            warning_days: Días de anticipación para alertar

        Returns:
            Lista de ExpirationCheck para empleados con días por expirar
        """
        import sqlite3

        results = []

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Obtener registros del año anterior (los que expiran pronto)
            rows = conn.execute('''
                SELECT employee_num, name, balance, year
                FROM employees
                WHERE year = ? AND balance > 0
            ''', (year - 1,)).fetchall()

            conn.close()

            # Fecha de expiración típica (fin de año fiscal = 31 marzo)
            # Asumiendo año fiscal japonés
            expiry_date = date(year + 1, 3, 31)
            today = date.today()
            days_until = (expiry_date - today).days

            for row in rows:
                if days_until <= warning_days:
                    level = AlertLevel.CRITICAL if days_until <= 7 else AlertLevel.WARNING

                    check = ExpirationCheck(
                        employee_num=row['employee_num'],
                        employee_name=row['name'],
                        expiring_days=row['balance'],
                        expiry_date=expiry_date.isoformat(),
                        days_until_expiry=days_until,
                        alert_level=level
                    )
                    results.append(check)

                    # Crear alerta
                    self._create_expiry_alert(check)

            return results

        except Exception as e:
            logger.error(f"Error verificando expiraciones: {e}")
            return results

    def _create_expiry_alert(self, check: ExpirationCheck):
        """Crea una alerta por expiración próxima."""
        alert = ComplianceAlert(
            alert_id=f"expiry_{check.employee_num}_{check.expiry_date}",
            level=check.alert_level,
            type="EXPIRATION_WARNING",
            employee_num=check.employee_num,
            employee_name=check.employee_name,
            message=f"{check.expiring_days} days expiring in {check.days_until_expiry} days",
            message_ja=f"有給休暇期限切れ警告: {check.expiring_days}日が{check.days_until_expiry}日後に失効します",
            details={
                'expiring_days': check.expiring_days,
                'expiry_date': check.expiry_date,
                'days_until': check.days_until_expiry
            },
            action_required="期限前に取得を促してください",
            due_date=check.expiry_date
        )
        self._alerts.append(alert)

    # ========================================
    # 年次有給休暇管理簿 (ANNUAL LEDGER)
    # ========================================

    def generate_annual_ledger(self, year: int) -> List[AnnualLedgerEntry]:
        """
        Genera el 年次有給休暇管理簿 oficial.

        Este documento es requerido por ley desde 2019.
        Debe mantenerse por 3 años.

        Args:
            year: Año del registro

        Returns:
            Lista de entradas del libro de gestión
        """
        import sqlite3

        entries = []

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Obtener datos de empleados
            employees = conn.execute('''
                SELECT employee_num, name, granted, used, balance, year
                FROM employees
                WHERE year = ?
                ORDER BY name
            ''', (year,)).fetchall()

            # Obtener fechas de uso individuales
            for emp in employees:
                usage_dates = conn.execute('''
                    SELECT use_date FROM yukyu_usage_details
                    WHERE employee_num = ? AND year = ?
                    ORDER BY use_date
                ''', (emp['employee_num'], year)).fetchall()

                dates = [row['use_date'] for row in usage_dates]

                entry = AnnualLedgerEntry(
                    employee_num=emp['employee_num'],
                    employee_name=emp['name'],
                    grant_date=f"{year}-04-01",  # Fecha típica de otorgamiento
                    granted_days=emp['granted'],
                    used_dates=dates,
                    used_days=emp['used'],
                    remaining_days=emp['balance'],
                    year=year
                )
                entries.append(entry)

            conn.close()

            logger.info(f"📋 年次有給休暇管理簿 generado: {len(entries)} empleados")
            return entries

        except Exception as e:
            logger.error(f"Error generando ledger: {e}")
            return entries

    def export_annual_ledger(
        self,
        year: int,
        output_path: str,
        format: str = "csv"
    ) -> bool:
        """
        Exporta el 年次有給休暇管理簿 a archivo.

        Args:
            year: Año del registro
            output_path: Ruta del archivo de salida
            format: Formato (csv, json)

        Returns:
            True si exitoso
        """
        try:
            entries = self.generate_annual_ledger(year)

            if format == "csv":
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)

                    # Header en japonés (requerido por ley)
                    writer.writerow([
                        '社員番号', '氏名', '基準日', '付与日数',
                        '取得日', '取得日数', '残日数', '年度'
                    ])

                    for e in entries:
                        writer.writerow([
                            e.employee_num,
                            e.employee_name,
                            e.grant_date,
                            e.granted_days,
                            ', '.join(e.used_dates),
                            e.used_days,
                            e.remaining_days,
                            e.year
                        ])

            elif format == "json":
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    data = [{
                        'employee_num': e.employee_num,
                        'employee_name': e.employee_name,
                        'grant_date': e.grant_date,
                        'granted_days': e.granted_days,
                        'used_dates': e.used_dates,
                        'used_days': e.used_days,
                        'remaining_days': e.remaining_days,
                        'year': e.year
                    } for e in entries]
                    json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 年次有給休暇管理簿 exportado a {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exportando ledger: {e}")
            return False

    # ========================================
    # ALERTAS
    # ========================================

    def get_active_alerts(
        self,
        level: AlertLevel = None,
        type: str = None
    ) -> List[ComplianceAlert]:
        """
        Obtiene alertas activas.

        Args:
            level: Filtrar por nivel (WARNING, CRITICAL)
            type: Filtrar por tipo (5_DAY_VIOLATION, EXPIRATION_WARNING)

        Returns:
            Lista de alertas
        """
        alerts = self._alerts

        if level:
            alerts = [a for a in alerts if a.level == level]

        if type:
            alerts = [a for a in alerts if a.type == type]

        return alerts

    def get_alerts_summary(self) -> Dict:
        """Obtiene resumen de alertas."""
        return {
            'total': len(self._alerts),
            'critical': sum(1 for a in self._alerts if a.level == AlertLevel.CRITICAL),
            'warning': sum(1 for a in self._alerts if a.level == AlertLevel.WARNING),
            'info': sum(1 for a in self._alerts if a.level == AlertLevel.INFO),
            'by_type': {
                '5_DAY_VIOLATION': sum(1 for a in self._alerts if a.type == '5_DAY_VIOLATION'),
                'EXPIRATION_WARNING': sum(1 for a in self._alerts if a.type == 'EXPIRATION_WARNING')
            }
        }

    def clear_alerts(self):
        """Limpia todas las alertas."""
        self._alerts = []

    # ========================================
    # UTILIDADES
    # ========================================

    def calculate_grant_for_tenure(self, years_of_service: float) -> int:
        """
        Calcula días a otorgar según antigüedad.

        Args:
            years_of_service: Años de servicio

        Returns:
            Días a otorgar según tabla legal
        """
        for tenure, days in sorted(self.GRANT_TABLE.items(), reverse=True):
            if years_of_service >= tenure:
                return days
        return 0

    def get_compliance_report(self, year: int) -> Dict:
        """
        Genera un reporte completo de compliance.

        Args:
            year: Año del reporte

        Returns:
            Dict con métricas de compliance
        """
        five_day_results = self.check_all_5_day_compliance(year)
        expiring = self.check_expiring_balances(year)
        alerts = self.get_alerts_summary()

        return {
            'year': year,
            'generated_at': datetime.now().isoformat(),
            'five_day_compliance': {
                'total_employees': five_day_results['total_checked'],
                'compliant': five_day_results['compliant'],
                'at_risk': five_day_results['at_risk'],
                'non_compliant': five_day_results['non_compliant'],
                'compliance_rate': five_day_results.get('compliance_rate', 0)
            },
            'expiration': {
                'employees_with_expiring_days': len(expiring),
                'total_expiring_days': sum(e.expiring_days for e in expiring)
            },
            'alerts': alerts,
            'overall_status': self._calculate_overall_status(five_day_results, expiring)
        }

    def _calculate_overall_status(self, five_day: Dict, expiring: List) -> str:
        """Calcula estado general de compliance."""
        if five_day['non_compliant'] > 0:
            return "NON_COMPLIANT"
        elif five_day['at_risk'] > 0 or len(expiring) > 0:
            return "AT_RISK"
        else:
            return "COMPLIANT"


# Instancia global
_compliance_instance: Optional[ComplianceAgent] = None


def get_compliance() -> ComplianceAgent:
    """Obtiene la instancia global del agente de compliance."""
    global _compliance_instance
    if _compliance_instance is None:
        _compliance_instance = ComplianceAgent()
    return _compliance_instance
