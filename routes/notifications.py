"""
Notifications Routes
Endpoints de notificaciones del sistema
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from .dependencies import (
    get_current_user,
    get_admin_user,
    CurrentUser,
    database,
    logger,
    check_5day_compliance,
    check_expiring_soon,
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# ============================================
# PYDANTIC MODELS
# ============================================

class MarkAllNotificationsReadRequest(BaseModel):
    """Request body for marking multiple notifications as read."""
    notification_ids: List[str] = Field(..., description="List of notification IDs")


class NotificationSettingsUpdate(BaseModel):
    """Model for updating notification settings."""
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_from_name: Optional[str] = None
    email_enabled: Optional[bool] = None
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    slack_enabled: Optional[bool] = None
    notify_on_leave_created: Optional[bool] = None
    notify_on_leave_approved: Optional[bool] = None
    notify_on_leave_rejected: Optional[bool] = None
    notify_on_expiring_days: Optional[bool] = None
    notify_on_compliance_warning: Optional[bool] = None
    manager_emails: Optional[str] = None


class TestEmailRequest(BaseModel):
    """Model for sending test email."""
    to: str = Field(..., description="Recipient email")


# ============================================
# NOTIFICATION ENDPOINTS
# ============================================

@router.get("")
async def get_notifications(
    employee_num: str = None,
    unread_only: bool = False,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get system notifications.
    Notifications include compliance alerts, approved/rejected requests, etc.

    Obtiene notificaciones del sistema.
    """
    try:
        from agents.compliance import get_compliance
        compliance = get_compliance()

        # Get alerts as notifications
        alerts = compliance.get_active_alerts()

        # Get read notification IDs for this user
        read_ids = database.get_read_notification_ids(user.username)

        notifications = []
        unread_count = 0

        for alert in alerts:
            if employee_num and alert.employee_num != employee_num:
                continue

            is_read = alert.alert_id in read_ids

            if unread_only and is_read:
                continue

            if not is_read:
                unread_count += 1

            notifications.append({
                "id": alert.alert_id,
                "type": alert.type,
                "level": alert.level.value,
                "title": alert.type.replace('_', ' ').title(),
                "message": alert.message_ja,
                "employee_num": alert.employee_num,
                "created_at": alert.created_at,
                "is_read": is_read
            })

        return {
            "status": "success",
            "count": len(notifications),
            "unread_count": unread_count,
            "notifications": notifications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/mark-read")
async def mark_notification_as_read(
    notification_id: str,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Mark a specific notification as read for the current user.
    Marca una notificacion especifica como leida.
    """
    try:
        was_unread = database.mark_notification_read(notification_id, user.username)
        return {
            "status": "success",
            "notification_id": notification_id,
            "was_unread": was_unread,
            "message": "Notification marked as read" if was_unread else "Notification was already read"
        }
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-all-read")
async def mark_all_notifications_as_read(
    request: MarkAllNotificationsReadRequest,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Mark multiple notifications as read for the current user.
    Marca multiples notificaciones como leidas.
    """
    try:
        marked_count = database.mark_all_notifications_read(user.username, request.notification_ids)
        return {
            "status": "success",
            "marked_count": marked_count,
            "total_requested": len(request.notification_ids),
            "message": f"Marked {marked_count} notifications as read"
        }
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_notification_count(
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get the count of unread notifications for the current user.
    Obtiene el conteo de notificaciones no leidas.
    """
    try:
        from agents.compliance import get_compliance
        compliance = get_compliance()

        alerts = compliance.get_active_alerts()
        all_ids = [alert.alert_id for alert in alerts]

        unread_count = database.get_unread_count(user.username, all_ids)

        return {
            "status": "success",
            "unread_count": unread_count,
            "total_count": len(all_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings")
async def get_notification_settings(user: CurrentUser = Depends(get_current_user)):
    """
    Get current notification settings.
    Passwords and sensitive URLs are masked.

    Obtiene la configuracion actual de notificaciones.
    """
    try:
        from notifications import notification_service
        settings = notification_service.get_settings()
        return {
            "status": "success",
            "settings": settings
        }
    except Exception as e:
        logger.error(f"Error getting notification settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_notification_settings(
    settings_update: NotificationSettingsUpdate,
    user: CurrentUser = Depends(get_admin_user)
):
    """
    Update notification settings.
    Only provided fields will be updated.
    Requires admin authentication.

    Actualiza la configuracion de notificaciones.
    """
    try:
        from notifications import notification_service

        # Convert to dict excluding None
        update_data = {k: v for k, v in settings_update.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No settings to update")

        success = notification_service.update_settings(update_data)

        if success:
            logger.info(f"Notification settings updated by {user.username}")
            return {
                "status": "success",
                "message": "Settings updated successfully",
                "updated_fields": list(update_data.keys())
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update settings")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-email")
async def test_email_notification(
    request: TestEmailRequest,
    user: CurrentUser = Depends(get_admin_user)
):
    """
    Send a test email to verify SMTP configuration.
    Requires admin authentication.

    Envia un email de prueba para verificar la configuracion SMTP.
    """
    try:
        from notifications import notification_service
        result = notification_service.test_email(request.to)

        if result["status"] == "success":
            logger.info(f"Test email sent to {request.to} by {user.username}")
            return {
                "status": "success",
                "message": f"Test email sent to {request.to}"
            }
        else:
            logger.warning(f"Test email failed: {result['message']}")
            return {
                "status": "error",
                "message": result["message"]
            }

    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-slack")
async def test_slack_notification(user: CurrentUser = Depends(get_admin_user)):
    """
    Send a test message to Slack to verify configuration.
    Requires admin authentication.

    Envia un mensaje de prueba a Slack.
    """
    try:
        from notifications import notification_service
        result = notification_service.test_slack()

        if result["status"] == "success":
            logger.info(f"Test Slack message sent by {user.username}")
            return {
                "status": "success",
                "message": "Test Slack message sent successfully"
            }
        else:
            logger.warning(f"Test Slack failed: {result['message']}")
            return {
                "status": "error",
                "message": result["message"]
            }

    except Exception as e:
        logger.error(f"Error sending test Slack: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_notification_logs(
    limit: int = 100,
    notification_type: Optional[str] = None,
    event_type: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get notification history.

    Obtiene el historial de notificaciones enviadas.
    """
    try:
        from notifications import notification_service
        logs = notification_service.get_notification_logs(
            limit=limit,
            notification_type=notification_type,
            event_type=event_type
        )

        return {
            "status": "success",
            "count": len(logs),
            "logs": logs
        }

    except Exception as e:
        logger.error(f"Error getting notification logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-expiring-warnings")
async def send_expiring_days_warnings(
    threshold_months: int = 3,
    year: Optional[int] = None,
    user: CurrentUser = Depends(get_admin_user)
):
    """
    Send warning notifications to employees with days about to expire.
    Requires admin authentication.

    Envia notificaciones de advertencia a empleados con dias que estan por vencer.
    """
    try:
        from notifications import notification_service

        if year is None:
            year = datetime.now().year

        expiring_employees = check_expiring_soon(year, threshold_months)

        if not expiring_employees:
            return {
                "status": "success",
                "message": "No employees with expiring days found",
                "notifications_sent": 0
            }

        sent_count = 0
        errors = []

        for emp in expiring_employees:
            try:
                result = notification_service.notify_expiring_days(
                    employee=emp,
                    days_expiring=emp.get('days_expiring', 0),
                    deadline=emp.get('expiry_date', 'N/A')
                )

                if result.get('email', {}).get('status') == 'success' or \
                   result.get('slack', {}).get('status') == 'success':
                    sent_count += 1
            except Exception as e:
                errors.append(f"{emp.get('name', 'Unknown')}: {str(e)}")

        logger.info(f"Expiring days warnings sent: {sent_count}/{len(expiring_employees)}")

        return {
            "status": "success",
            "message": f"Sent {sent_count} notifications",
            "notifications_sent": sent_count,
            "total_employees": len(expiring_employees),
            "errors": errors if errors else None
        }

    except Exception as e:
        logger.error(f"Error sending expiring warnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-compliance-warning")
async def send_compliance_warnings(
    year: Optional[int] = None,
    user: CurrentUser = Depends(get_admin_user)
):
    """
    Send 5-day compliance warning notifications.
    Notifies about employees who have not met the 5-day obligation.
    Requires admin authentication.

    Envia notificaciones de advertencia de cumplimiento de 5 dias.
    """
    try:
        from notifications import notification_service

        if year is None:
            year = datetime.now().year

        compliance = check_5day_compliance(year)

        at_risk = compliance.get('at_risk', [])
        non_compliant = compliance.get('non_compliant', [])

        all_at_risk = at_risk + non_compliant

        if not all_at_risk:
            return {
                "status": "success",
                "message": "All employees are compliant",
                "notifications_sent": 0
            }

        result = notification_service.notify_compliance_warning(all_at_risk)

        email_sent = result.get('email', {}).get('status') == 'success'
        slack_sent = result.get('slack', {}).get('status') == 'success'

        logger.info(f"Compliance warning sent for {len(all_at_risk)} employees")

        return {
            "status": "success",
            "message": f"Compliance warning sent for {len(all_at_risk)} employees",
            "employees_at_risk": len(all_at_risk),
            "email_sent": email_sent,
            "slack_sent": slack_sent
        }

    except Exception as e:
        logger.error(f"Error sending compliance warning: {e}")
        raise HTTPException(status_code=500, detail=str(e))
