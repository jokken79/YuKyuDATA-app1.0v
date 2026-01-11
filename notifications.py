"""
Notification Service for YuKyuDATA-app
======================================
Sistema de notificaciones por Email y Slack para eventos de yukyu.

Características:
- Email SMTP con soporte HTML y texto plano
- Slack Webhooks con bloques formateados
- Templates HTML para diferentes eventos
- Gestión de configuración persistente
- Registro de notificaciones enviadas
- Modo de prueba para desarrollo

Uso:
    from notifications import notification_service

    # Enviar email
    notification_service.send_email(
        to="employee@company.com",
        subject="Solicitud Aprobada",
        body="Tu solicitud de vacaciones ha sido aprobada."
    )

    # Enviar a Slack
    notification_service.send_slack(
        channel="#yukyu-notifications",
        message="Nueva solicitud de vacaciones"
    )
"""

import os
import smtplib
import json
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import logging
import urllib.request
import urllib.error

# Setup logging
logger = logging.getLogger("notifications")
logger.setLevel(logging.INFO)

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates" / "emails"

# Database path for notification settings
DB_PATH = Path(__file__).parent / "yukyu.db"


@dataclass
class NotificationSettings:
    """Configuración de notificaciones almacenada en la base de datos."""
    # Email settings
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@yukyu.app"
    smtp_from_name: str = "YuKyuDATA システム"
    email_enabled: bool = False

    # Slack settings
    slack_webhook_url: str = ""
    slack_channel: str = "#yukyu-notifications"
    slack_enabled: bool = False

    # Notification preferences
    notify_on_leave_created: bool = True
    notify_on_leave_approved: bool = True
    notify_on_leave_rejected: bool = True
    notify_on_expiring_days: bool = True
    notify_on_compliance_warning: bool = True

    # Manager notification emails (comma-separated)
    manager_emails: str = ""

    def to_dict(self) -> Dict:
        return {
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "smtp_user": self.smtp_user,
            "smtp_password": "***" if self.smtp_password else "",  # Mask password
            "smtp_from": self.smtp_from,
            "smtp_from_name": self.smtp_from_name,
            "email_enabled": self.email_enabled,
            "slack_webhook_url": "***" if self.slack_webhook_url else "",  # Mask URL
            "slack_channel": self.slack_channel,
            "slack_enabled": self.slack_enabled,
            "notify_on_leave_created": self.notify_on_leave_created,
            "notify_on_leave_approved": self.notify_on_leave_approved,
            "notify_on_leave_rejected": self.notify_on_leave_rejected,
            "notify_on_expiring_days": self.notify_on_expiring_days,
            "notify_on_compliance_warning": self.notify_on_compliance_warning,
            "manager_emails": self.manager_emails
        }


@dataclass
class NotificationLog:
    """Registro de una notificación enviada."""
    id: Optional[int] = None
    notification_type: str = ""  # email, slack
    event_type: str = ""  # leave_created, leave_approved, etc.
    recipient: str = ""
    subject: str = ""
    status: str = ""  # sent, failed
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class NotificationService:
    """
    Servicio principal de notificaciones.

    Gestiona el envío de emails y mensajes de Slack para eventos
    relacionados con solicitudes de vacaciones y cumplimiento.
    """

    def __init__(self):
        self.settings = self._load_settings_from_env()
        self._ensure_tables()

    def _load_settings_from_env(self) -> NotificationSettings:
        """Carga la configuración desde variables de entorno."""
        return NotificationSettings(
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_from=os.getenv("SMTP_FROM", "noreply@yukyu.app"),
            smtp_from_name=os.getenv("SMTP_FROM_NAME", "YuKyuDATA システム"),
            email_enabled=os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true",
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
            slack_channel=os.getenv("SLACK_CHANNEL", "#yukyu-notifications"),
            slack_enabled=os.getenv("SLACK_NOTIFICATIONS_ENABLED", "false").lower() == "true",
            notify_on_leave_created=os.getenv("NOTIFY_LEAVE_CREATED", "true").lower() == "true",
            notify_on_leave_approved=os.getenv("NOTIFY_LEAVE_APPROVED", "true").lower() == "true",
            notify_on_leave_rejected=os.getenv("NOTIFY_LEAVE_REJECTED", "true").lower() == "true",
            notify_on_expiring_days=os.getenv("NOTIFY_EXPIRING_DAYS", "true").lower() == "true",
            notify_on_compliance_warning=os.getenv("NOTIFY_COMPLIANCE_WARNING", "true").lower() == "true",
            manager_emails=os.getenv("MANAGER_EMAILS", "")
        )

    def _ensure_tables(self):
        """Crea las tablas necesarias para el sistema de notificaciones."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()

            # Tabla de configuración de notificaciones
            c.execute("""
                CREATE TABLE IF NOT EXISTS notification_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabla de logs de notificaciones
            c.execute("""
                CREATE TABLE IF NOT EXISTS notification_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_type TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    subject TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Índices para búsquedas eficientes
            c.execute("""
                CREATE INDEX IF NOT EXISTS idx_notification_logs_type
                ON notification_logs(notification_type, event_type)
            """)
            c.execute("""
                CREATE INDEX IF NOT EXISTS idx_notification_logs_created
                ON notification_logs(created_at DESC)
            """)

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error creating notification tables: {e}")

    def _log_notification(self, log: NotificationLog):
        """Registra una notificación en la base de datos."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute("""
                INSERT INTO notification_logs
                (notification_type, event_type, recipient, subject, status, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                log.notification_type,
                log.event_type,
                log.recipient,
                log.subject,
                log.status,
                log.error_message,
                log.created_at.isoformat()
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging notification: {e}")

    def reload_settings(self):
        """Recarga la configuración desde las variables de entorno."""
        self.settings = self._load_settings_from_env()

    def get_settings(self) -> Dict:
        """Retorna la configuración actual (con passwords enmascarados)."""
        return self.settings.to_dict()

    def update_settings(self, new_settings: Dict) -> bool:
        """
        Actualiza la configuración de notificaciones.

        Args:
            new_settings: Diccionario con las nuevas configuraciones

        Returns:
            True si se actualizó correctamente
        """
        try:
            # Actualizar solo los campos proporcionados
            for key, value in new_settings.items():
                if hasattr(self.settings, key):
                    # No actualizar passwords vacíos o enmascarados
                    if key in ['smtp_password', 'slack_webhook_url']:
                        if value and value != "***":
                            setattr(self.settings, key, value)
                    else:
                        setattr(self.settings, key, value)

            # Persistir en base de datos
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()

            for key, value in new_settings.items():
                if hasattr(self.settings, key):
                    # No guardar passwords enmascarados
                    if key in ['smtp_password', 'slack_webhook_url']:
                        if value and value != "***":
                            c.execute("""
                                INSERT OR REPLACE INTO notification_settings (key, value, updated_at)
                                VALUES (?, ?, ?)
                            """, (key, str(value), datetime.now().isoformat()))
                    else:
                        c.execute("""
                            INSERT OR REPLACE INTO notification_settings (key, value, updated_at)
                            VALUES (?, ?, ?)
                        """, (key, str(value), datetime.now().isoformat()))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating notification settings: {e}")
            return False

    def _load_template(self, template_name: str) -> Optional[str]:
        """Carga un template HTML desde el directorio de templates."""
        template_path = TEMPLATE_DIR / template_name
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        return None

    def _render_template(self, template_content: str, variables: Dict) -> str:
        """Renderiza un template reemplazando variables {{variable}}."""
        result = template_content
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    # ============================================
    # EMAIL METHODS
    # ============================================

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        event_type: str = "general"
    ) -> Dict:
        """
        Envía un email.

        Args:
            to: Dirección de email del destinatario
            subject: Asunto del email
            body: Cuerpo en texto plano
            html: Cuerpo en HTML (opcional)
            event_type: Tipo de evento para logging

        Returns:
            Dict con status y mensaje
        """
        if not self.settings.email_enabled:
            logger.info(f"Email notifications disabled. Would send to {to}: {subject}")
            return {"status": "disabled", "message": "Email notifications are disabled"}

        if not self.settings.smtp_user or not self.settings.smtp_password:
            return {"status": "error", "message": "SMTP credentials not configured"}

        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((self.settings.smtp_from_name, self.settings.smtp_from))
            msg['To'] = to

            # Agregar versión de texto plano
            part1 = MIMEText(body, 'plain', 'utf-8')
            msg.attach(part1)

            # Agregar versión HTML si está disponible
            if html:
                part2 = MIMEText(html, 'html', 'utf-8')
                msg.attach(part2)

            # Enviar
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                server.starttls()
                server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.sendmail(self.settings.smtp_from, to, msg.as_string())

            # Log success
            self._log_notification(NotificationLog(
                notification_type="email",
                event_type=event_type,
                recipient=to,
                subject=subject,
                status="sent"
            ))

            logger.info(f"Email sent to {to}: {subject}")
            return {"status": "success", "message": f"Email sent to {to}"}

        except smtplib.SMTPAuthenticationError as e:
            error_msg = "SMTP authentication failed. Check credentials."
            self._log_notification(NotificationLog(
                notification_type="email",
                event_type=event_type,
                recipient=to,
                subject=subject,
                status="failed",
                error_message=error_msg
            ))
            logger.error(f"SMTP auth error: {e}")
            return {"status": "error", "message": error_msg}

        except Exception as e:
            error_msg = str(e)
            self._log_notification(NotificationLog(
                notification_type="email",
                event_type=event_type,
                recipient=to,
                subject=subject,
                status="failed",
                error_message=error_msg
            ))
            logger.error(f"Email error: {e}")
            return {"status": "error", "message": error_msg}

    # ============================================
    # SLACK METHODS
    # ============================================

    def send_slack(
        self,
        channel: Optional[str] = None,
        message: str = "",
        blocks: Optional[List[Dict]] = None,
        event_type: str = "general"
    ) -> Dict:
        """
        Envía un mensaje a Slack.

        Args:
            channel: Canal de Slack (usa el default si no se especifica)
            message: Mensaje en texto plano
            blocks: Bloques de Slack para formato rico
            event_type: Tipo de evento para logging

        Returns:
            Dict con status y mensaje
        """
        if not self.settings.slack_enabled:
            logger.info(f"Slack notifications disabled. Would send: {message}")
            return {"status": "disabled", "message": "Slack notifications are disabled"}

        if not self.settings.slack_webhook_url:
            return {"status": "error", "message": "Slack webhook URL not configured"}

        try:
            channel = channel or self.settings.slack_channel

            # Construir payload
            payload = {
                "channel": channel,
                "text": message,
                "username": "YuKyuDATA Bot",
                "icon_emoji": ":calendar:"
            }

            if blocks:
                payload["blocks"] = blocks

            # Enviar request
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.settings.slack_webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read().decode('utf-8')

            # Log success
            self._log_notification(NotificationLog(
                notification_type="slack",
                event_type=event_type,
                recipient=channel,
                subject=message[:100],
                status="sent"
            ))

            logger.info(f"Slack message sent to {channel}")
            return {"status": "success", "message": f"Slack message sent to {channel}"}

        except urllib.error.HTTPError as e:
            error_msg = f"Slack HTTP error: {e.code}"
            self._log_notification(NotificationLog(
                notification_type="slack",
                event_type=event_type,
                recipient=channel or self.settings.slack_channel,
                subject=message[:100],
                status="failed",
                error_message=error_msg
            ))
            logger.error(f"Slack HTTP error: {e}")
            return {"status": "error", "message": error_msg}

        except Exception as e:
            error_msg = str(e)
            self._log_notification(NotificationLog(
                notification_type="slack",
                event_type=event_type,
                recipient=channel or self.settings.slack_channel,
                subject=message[:100],
                status="failed",
                error_message=error_msg
            ))
            logger.error(f"Slack error: {e}")
            return {"status": "error", "message": error_msg}

    # ============================================
    # LEAVE REQUEST NOTIFICATIONS
    # ============================================

    def notify_leave_request_created(self, request: Dict) -> Dict:
        """
        Notifica la creación de una solicitud de vacaciones.

        Args:
            request: Diccionario con los datos de la solicitud
                - employee_num, employee_name, start_date, end_date,
                - days_requested, leave_type, reason

        Returns:
            Dict con los resultados de las notificaciones
        """
        results = {"email": None, "slack": None}

        if not self.settings.notify_on_leave_created:
            return {"status": "disabled", "message": "Leave created notifications disabled"}

        employee_name = request.get('employee_name', 'Unknown')
        employee_num = request.get('employee_num', 'N/A')
        start_date = request.get('start_date', '')
        end_date = request.get('end_date', '')
        days = request.get('days_requested', 0)
        leave_type = request.get('leave_type', 'full')
        reason = request.get('reason', '理由なし')

        # Traducir tipo de licencia
        leave_type_ja = {
            'full': '全日',
            'half_am': '午前半休',
            'half_pm': '午後半休',
            'hourly': '時間休'
        }.get(leave_type, leave_type)

        # Email a managers
        if self.settings.email_enabled and self.settings.manager_emails:
            subject = f"【新規申請】有給休暇申請 - {employee_name}"

            # Cargar y renderizar template
            template = self._load_template('leave_request_created.html')
            if template:
                html = self._render_template(template, {
                    'employee_name': employee_name,
                    'employee_num': employee_num,
                    'start_date': start_date,
                    'end_date': end_date,
                    'days_requested': days,
                    'leave_type': leave_type_ja,
                    'reason': reason,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
            else:
                html = None

            body = f"""
新しい有給休暇申請が提出されました。

従業員: {employee_name} ({employee_num})
期間: {start_date} ～ {end_date}
日数: {days}日
種別: {leave_type_ja}
理由: {reason}

申請時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---
YuKyuDATA システム
            """

            for email in self.settings.manager_emails.split(','):
                email = email.strip()
                if email:
                    results["email"] = self.send_email(
                        to=email,
                        subject=subject,
                        body=body,
                        html=html,
                        event_type="leave_created"
                    )

        # Slack notification
        if self.settings.slack_enabled:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📅 新規有給休暇申請",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*従業員:*\n{employee_name}"},
                        {"type": "mrkdwn", "text": f"*社員番号:*\n{employee_num}"},
                        {"type": "mrkdwn", "text": f"*期間:*\n{start_date} ～ {end_date}"},
                        {"type": "mrkdwn", "text": f"*日数:*\n{days}日 ({leave_type_ja})"}
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"理由: {reason}"}
                    ]
                },
                {"type": "divider"}
            ]

            results["slack"] = self.send_slack(
                message=f"新規有給休暇申請: {employee_name} ({days}日)",
                blocks=blocks,
                event_type="leave_created"
            )

        return results

    def notify_leave_request_approved(self, request: Dict) -> Dict:
        """
        Notifica la aprobación de una solicitud de vacaciones.

        Args:
            request: Diccionario con los datos de la solicitud
                - employee_num, employee_name, employee_email (optional),
                - start_date, end_date, days_requested, approved_by

        Returns:
            Dict con los resultados de las notificaciones
        """
        results = {"email": None, "slack": None}

        if not self.settings.notify_on_leave_approved:
            return {"status": "disabled", "message": "Leave approved notifications disabled"}

        employee_name = request.get('employee_name', 'Unknown')
        employee_num = request.get('employee_num', 'N/A')
        employee_email = request.get('employee_email')
        start_date = request.get('start_date', '')
        end_date = request.get('end_date', '')
        days = request.get('days_requested', 0)
        approved_by = request.get('approved_by', 'Manager')
        balance_after = request.get('balance_after', 'N/A')

        # Email al empleado (si tiene email)
        if self.settings.email_enabled and employee_email:
            subject = f"【承認済み】有給休暇申請が承認されました"

            template = self._load_template('leave_approved.html')
            if template:
                html = self._render_template(template, {
                    'employee_name': employee_name,
                    'employee_num': employee_num,
                    'start_date': start_date,
                    'end_date': end_date,
                    'days_requested': days,
                    'approved_by': approved_by,
                    'balance_after': balance_after,
                    'approved_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
            else:
                html = None

            body = f"""
{employee_name} 様

有給休暇申請が承認されました。

期間: {start_date} ～ {end_date}
日数: {days}日
承認者: {approved_by}
承認日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}

残り有給日数: {balance_after}日

---
YuKyuDATA システム
            """

            results["email"] = self.send_email(
                to=employee_email,
                subject=subject,
                body=body,
                html=html,
                event_type="leave_approved"
            )

        # Slack notification
        if self.settings.slack_enabled:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ 有給休暇申請が承認されました",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*従業員:*\n{employee_name}"},
                        {"type": "mrkdwn", "text": f"*承認者:*\n{approved_by}"},
                        {"type": "mrkdwn", "text": f"*期間:*\n{start_date} ～ {end_date}"},
                        {"type": "mrkdwn", "text": f"*日数:*\n{days}日"}
                    ]
                },
                {"type": "divider"}
            ]

            results["slack"] = self.send_slack(
                message=f"有給休暇承認: {employee_name} ({days}日) - 承認者: {approved_by}",
                blocks=blocks,
                event_type="leave_approved"
            )

        return results

    def notify_leave_request_rejected(self, request: Dict, reason: str) -> Dict:
        """
        Notifica el rechazo de una solicitud de vacaciones.

        Args:
            request: Diccionario con los datos de la solicitud
            reason: Razón del rechazo

        Returns:
            Dict con los resultados de las notificaciones
        """
        results = {"email": None, "slack": None}

        if not self.settings.notify_on_leave_rejected:
            return {"status": "disabled", "message": "Leave rejected notifications disabled"}

        employee_name = request.get('employee_name', 'Unknown')
        employee_num = request.get('employee_num', 'N/A')
        employee_email = request.get('employee_email')
        start_date = request.get('start_date', '')
        end_date = request.get('end_date', '')
        days = request.get('days_requested', 0)
        rejected_by = request.get('rejected_by', 'Manager')

        # Email al empleado (si tiene email)
        if self.settings.email_enabled and employee_email:
            subject = f"【却下】有給休暇申請について"

            template = self._load_template('leave_rejected.html')
            if template:
                html = self._render_template(template, {
                    'employee_name': employee_name,
                    'employee_num': employee_num,
                    'start_date': start_date,
                    'end_date': end_date,
                    'days_requested': days,
                    'rejected_by': rejected_by,
                    'rejection_reason': reason,
                    'rejected_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
            else:
                html = None

            body = f"""
{employee_name} 様

申し訳ございませんが、有給休暇申請が却下されました。

期間: {start_date} ～ {end_date}
日数: {days}日
却下理由: {reason}
却下日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}

ご不明な点がございましたら、管理者までお問い合わせください。

---
YuKyuDATA システム
            """

            results["email"] = self.send_email(
                to=employee_email,
                subject=subject,
                body=body,
                html=html,
                event_type="leave_rejected"
            )

        # Slack notification
        if self.settings.slack_enabled:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ 有給休暇申請が却下されました",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*従業員:*\n{employee_name}"},
                        {"type": "mrkdwn", "text": f"*却下者:*\n{rejected_by}"},
                        {"type": "mrkdwn", "text": f"*期間:*\n{start_date} ～ {end_date}"},
                        {"type": "mrkdwn", "text": f"*日数:*\n{days}日"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*却下理由:*\n{reason}"
                    }
                },
                {"type": "divider"}
            ]

            results["slack"] = self.send_slack(
                message=f"有給休暇却下: {employee_name} - 理由: {reason}",
                blocks=blocks,
                event_type="leave_rejected"
            )

        return results

    # ============================================
    # COMPLIANCE NOTIFICATIONS
    # ============================================

    def notify_expiring_days(
        self,
        employee: Dict,
        days_expiring: float,
        deadline: str
    ) -> Dict:
        """
        Notifica sobre días de vacaciones que están por vencer.

        Args:
            employee: Diccionario con datos del empleado
            days_expiring: Número de días que vencerán
            deadline: Fecha límite para usar los días

        Returns:
            Dict con los resultados de las notificaciones
        """
        results = {"email": None, "slack": None}

        if not self.settings.notify_on_expiring_days:
            return {"status": "disabled", "message": "Expiring days notifications disabled"}

        employee_name = employee.get('name', 'Unknown')
        employee_num = employee.get('employee_num', 'N/A')
        employee_email = employee.get('email')

        # Email al empleado (si tiene email)
        if self.settings.email_enabled and employee_email:
            subject = f"【重要】有給休暇の期限が近づいています"

            template = self._load_template('expiring_days_warning.html')
            if template:
                html = self._render_template(template, {
                    'employee_name': employee_name,
                    'employee_num': employee_num,
                    'days_expiring': days_expiring,
                    'deadline': deadline
                })
            else:
                html = None

            body = f"""
{employee_name} 様

重要なお知らせ: 有給休暇の期限が近づいています。

期限切れになる日数: {days_expiring}日
使用期限: {deadline}

期限を過ぎると、これらの日数は無効になります。
お早めにご利用ください。

---
YuKyuDATA システム
            """

            results["email"] = self.send_email(
                to=employee_email,
                subject=subject,
                body=body,
                html=html,
                event_type="expiring_days"
            )

        # Also notify managers
        if self.settings.email_enabled and self.settings.manager_emails:
            manager_subject = f"【注意】従業員の有給休暇期限 - {employee_name}"
            manager_body = f"""
従業員の有給休暇が間もなく期限切れになります。

従業員: {employee_name} ({employee_num})
期限切れになる日数: {days_expiring}日
使用期限: {deadline}

フォローアップをお願いします。

---
YuKyuDATA システム
            """

            for email in self.settings.manager_emails.split(','):
                email = email.strip()
                if email:
                    self.send_email(
                        to=email,
                        subject=manager_subject,
                        body=manager_body,
                        event_type="expiring_days_manager"
                    )

        # Slack notification
        if self.settings.slack_enabled:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "⚠️ 有給休暇期限警告",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*従業員:*\n{employee_name}"},
                        {"type": "mrkdwn", "text": f"*社員番号:*\n{employee_num}"},
                        {"type": "mrkdwn", "text": f"*期限切れ日数:*\n{days_expiring}日"},
                        {"type": "mrkdwn", "text": f"*使用期限:*\n{deadline}"}
                    ]
                },
                {"type": "divider"}
            ]

            results["slack"] = self.send_slack(
                message=f"有給休暇期限警告: {employee_name} - {days_expiring}日が{deadline}に期限切れ",
                blocks=blocks,
                event_type="expiring_days"
            )

        return results

    def notify_compliance_warning(self, employees_at_risk: List[Dict]) -> Dict:
        """
        Notifica sobre empleados que no cumplen con la obligación de 5 días.

        Args:
            employees_at_risk: Lista de empleados en riesgo de incumplimiento
                Cada empleado debe tener: employee_num, name, days_used, days_required

        Returns:
            Dict con los resultados de las notificaciones
        """
        results = {"email": None, "slack": None}

        if not self.settings.notify_on_compliance_warning:
            return {"status": "disabled", "message": "Compliance warning notifications disabled"}

        if not employees_at_risk:
            return {"status": "skipped", "message": "No employees at risk"}

        count = len(employees_at_risk)

        # Build employee list
        employee_list_text = ""
        for emp in employees_at_risk[:20]:  # Limit to 20 for readability
            name = emp.get('name', 'Unknown')
            emp_num = emp.get('employee_num', 'N/A')
            used = emp.get('days_used', 0)
            required = emp.get('days_required', 5)
            remaining = required - used
            employee_list_text += f"- {name} ({emp_num}): 残り{remaining}日必要\n"

        if count > 20:
            employee_list_text += f"\n... 他 {count - 20} 名\n"

        # Email to managers
        if self.settings.email_enabled and self.settings.manager_emails:
            subject = f"【重要】5日取得義務 未達成者 {count}名"

            body = f"""
5日取得義務の未達成者がいます。

対象従業員数: {count}名

{employee_list_text}

労働基準法に基づき、年10日以上の有給休暇が付与される従業員は、
年5日以上の有給休暇を取得させる義務があります。

早急な対応をお願いします。

---
YuKyuDATA システム
            """

            for email in self.settings.manager_emails.split(','):
                email = email.strip()
                if email:
                    results["email"] = self.send_email(
                        to=email,
                        subject=subject,
                        body=body,
                        event_type="compliance_warning"
                    )

        # Slack notification
        if self.settings.slack_enabled:
            # Build Slack blocks
            employee_fields = []
            for emp in employees_at_risk[:10]:  # Limit for Slack
                name = emp.get('name', 'Unknown')
                used = emp.get('days_used', 0)
                required = emp.get('days_required', 5)
                employee_fields.append({
                    "type": "mrkdwn",
                    "text": f"*{name}:* {used}/{required}日 取得済み"
                })

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 5日取得義務 コンプライアンス警告",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{count}名*の従業員が5日取得義務を満たしていません。"
                    }
                },
                {
                    "type": "section",
                    "fields": employee_fields[:10]  # Slack limit
                }
            ]

            if count > 10:
                blocks.append({
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"他 {count - 10} 名..."}
                    ]
                })

            blocks.append({"type": "divider"})

            results["slack"] = self.send_slack(
                message=f"コンプライアンス警告: {count}名が5日取得義務未達成",
                blocks=blocks,
                event_type="compliance_warning"
            )

        return results

    # ============================================
    # TEST METHODS
    # ============================================

    def test_email(self, to: str) -> Dict:
        """
        Envía un email de prueba.

        Args:
            to: Dirección de email del destinatario

        Returns:
            Dict con el resultado del envío
        """
        subject = "【テスト】YuKyuDATA 通知システムテスト"
        body = f"""
これはYuKyuDATAシステムからのテストメールです。

送信日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

このメールが届いた場合、メール通知が正しく設定されています。

---
YuKyuDATA システム
        """

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
        .footer {{ text-align: center; padding: 10px; color: #64748b; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>YuKyuDATA</h1>
        <p>通知システムテスト</p>
    </div>
    <div class="content">
        <h2>テストメール</h2>
        <p>これはYuKyuDATAシステムからのテストメールです。</p>
        <p><strong>送信日時:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>このメールが届いた場合、メール通知が正しく設定されています。</p>
    </div>
    <div class="footer">
        <p>YuKyuDATA システム</p>
    </div>
</body>
</html>
        """

        # Temporarily enable email for test
        original_enabled = self.settings.email_enabled
        self.settings.email_enabled = True

        result = self.send_email(to=to, subject=subject, body=body, html=html, event_type="test")

        self.settings.email_enabled = original_enabled
        return result

    def test_slack(self) -> Dict:
        """
        Envía un mensaje de prueba a Slack.

        Returns:
            Dict con el resultado del envío
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🧪 YuKyuDATA 通知テスト",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"これはSlack通知のテストメッセージです。\n*送信日時:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "このメッセージが表示された場合、Slack通知は正しく設定されています。"}
                ]
            },
            {"type": "divider"}
        ]

        # Temporarily enable slack for test
        original_enabled = self.settings.slack_enabled
        self.settings.slack_enabled = True

        result = self.send_slack(
            message="YuKyuDATA 通知システムテスト",
            blocks=blocks,
            event_type="test"
        )

        self.settings.slack_enabled = original_enabled
        return result

    # ============================================
    # LOGS & HISTORY
    # ============================================

    def get_notification_logs(
        self,
        limit: int = 100,
        notification_type: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtiene el historial de notificaciones.

        Args:
            limit: Número máximo de registros
            notification_type: Filtrar por tipo (email, slack)
            event_type: Filtrar por evento (leave_created, etc.)

        Returns:
            Lista de registros de notificaciones
        """
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            query = "SELECT * FROM notification_logs WHERE 1=1"
            params = []

            if notification_type:
                query += " AND notification_type = ?"
                params.append(notification_type)

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            c.execute(query, params)
            rows = c.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting notification logs: {e}")
            return []


# Singleton instance
notification_service = NotificationService()
