"""
Leave Requests Routes
Endpoints de solicitudes de vacaciones
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
from datetime import datetime

from ..dependencies import (
    get_current_user,
    CurrentUser,
    database,
    logger,
    log_leave_request,
    log_audit_action,
)

# Import centralized Pydantic models
from models import LeaveRequestCreate

router = APIRouter(prefix="", tags=["Leave Requests"])


# ============================================
# LEAVE REQUEST ENDPOINTS
# ============================================

# ✅ FIX 3: Added Pydantic validation for leave requests
@router.post("/leave-requests")
async def create_leave_request(
    request: Request,
    request_data: LeaveRequestCreate,  # ✅ Pydantic model instead of dict
    user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new leave request with support for hourly leave (時間単位有給).
    Crea una nueva solicitud de vacaciones con soporte para tiempo parcial.

    Validation is performed automatically by Pydantic model.
    """
    try:
        current_year = datetime.now().year

        # Validate employee has sufficient balance
        history = database.get_employee_yukyu_history(request_data.employee_num, current_year)
        total_available = sum(record.get('balance', 0) for record in history)

        # Convert hours to days for validation (8 hours = 1 day)
        total_days_equivalent = request_data.days_requested + (request_data.hours_requested / 8)

        if total_days_equivalent > total_available:
            raise HTTPException(
                status_code=422,  # ✅ FIX: Use 422 for validation errors
                detail="残日数が不足しています"
            )

        # ✅ FIX 4: Use optimized query instead of N+1
        hourly_wage = database.get_employee_hourly_wage(request_data.employee_num)

        # Create request with new fields
        new_request_id = database.create_leave_request(
            employee_num=request_data.employee_num,
            employee_name=request_data.employee_name,
            start_date=request_data.start_date,
            end_date=request_data.end_date,
            days_requested=request_data.days_requested,
            reason=request_data.reason or '',
            year=current_year,
            hours_requested=request_data.hours_requested,
            leave_type=request_data.leave_type,
            hourly_wage=hourly_wage
        )

        # Audit log
        await log_audit_action(
            request=request,
            action="CREATE",
            entity_type="leave_request",
            entity_id=str(new_request_id),
            new_value=request_data.dict(),
            user=user
        )

        # Send notification
        try:
            from services.notifications import notification_service
            notification_service.notify_leave_request_created({
                'employee_num': request_data.employee_num,
                'employee_name': request_data.employee_name,
                'start_date': request_data.start_date,
                'end_date': request_data.end_date,
                'days_requested': request_data.days_requested,
                'leave_type': request_data.leave_type,
                'reason': request_data.reason or ''
            })
        except Exception as notif_error:
            logger.warning(f"Failed to send leave request notification: {notif_error}")

        return {
            "status": "success",
            "message": "申請が作成されました",
            "request_id": new_request_id,
            "hourly_wage": hourly_wage,
            "cost_estimate": ((request_data.days_requested * 8) + request_data.hours_requested) * hourly_wage
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create leave request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/leave-requests")
async def get_leave_requests_list(
    status: str = None,
    employee_num: str = None,
    year: int = None
):
    """
    Get list of leave requests with optional filters.
    Obtiene lista de solicitudes con filtros opcionales.
    """
    try:
        requests = database.get_leave_requests(
            status=status,
            employee_num=employee_num,
            year=year
        )
        return {"status": "success", "data": requests, "count": len(requests)}
    except Exception as e:
        logger.error(f"Failed to get leave requests: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/leave-requests/{request_id}/approve")
@router.post("/leave-requests/{request_id}/approve")  # Deprecated: Use PATCH instead
async def approve_leave_request(
    request: Request,
    request_id: int,
    approval_data: dict,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Approve a leave request and automatically update yukyu balance.
    Aprueba una solicitud y actualiza automaticamente el balance.

    Note: PATCH is the preferred method. POST is deprecated and kept for backwards compatibility.
    """
    try:
        approved_by = approval_data.get('approved_by', user.username if user else 'Manager')
        validate_limit = approval_data.get('validate_limit', True)

        # Get old value before approval
        old_requests = database.get_leave_requests()
        old_value = next((r for r in old_requests if r.get('id') == request_id), None)

        # Validate balance limit before approval
        if validate_limit and old_value:
            employee_num = old_value.get('employee_num')
            year = old_value.get('year')
            if employee_num and year:
                database.validate_balance_limit(employee_num, year)

        # Approve request (also updates yukyu balance)
        database.approve_leave_request(request_id, approved_by)

        # Audit log
        await log_audit_action(
            request=request,
            action="APPROVE",
            entity_type="leave_request",
            entity_id=str(request_id),
            old_value=old_value,
            new_value={"status": "APPROVED", "approved_by": approved_by},
            user=user
        )

        # Send notification
        try:
            from services.notifications import notification_service
            if old_value:
                current_year = datetime.now().year
                history = database.get_employee_yukyu_history(old_value.get('employee_num'), current_year)
                balance_after = sum(record.get('balance', 0) for record in history)

                notification_service.notify_leave_request_approved({
                    'employee_num': old_value.get('employee_num'),
                    'employee_name': old_value.get('employee_name'),
                    'employee_email': old_value.get('employee_email'),
                    'start_date': old_value.get('start_date'),
                    'end_date': old_value.get('end_date'),
                    'days_requested': old_value.get('days_requested'),
                    'approved_by': approved_by,
                    'balance_after': balance_after
                })
        except Exception as notif_error:
            logger.warning(f"Failed to send approval notification: {notif_error}")

        return {
            "status": "success",
            "message": "Request approved and yukyu balance updated"
        }
    except ValueError as ve:
        logger.warning(f"Approve request validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid approval request")
    except Exception as e:
        logger.error(f"Failed to approve leave request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/leave-requests/{request_id}/reject")
@router.post("/leave-requests/{request_id}/reject")  # Deprecated: Use PATCH instead
async def reject_leave_request(
    request: Request,
    request_id: int,
    rejection_data: dict,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Reject a leave request.
    Rechaza una solicitud de vacaciones.

    Note: PATCH is the preferred method. POST is deprecated and kept for backwards compatibility.
    """
    try:
        rejected_by = rejection_data.get('rejected_by', user.username if user else 'Manager')

        # Get old value before rejection
        old_requests = database.get_leave_requests()
        old_value = next((r for r in old_requests if r.get('id') == request_id), None)

        database.reject_leave_request(request_id, rejected_by)

        # Audit log
        await log_audit_action(
            request=request,
            action="REJECT",
            entity_type="leave_request",
            entity_id=str(request_id),
            old_value=old_value,
            new_value={"status": "REJECTED", "rejected_by": rejected_by},
            user=user
        )

        # Send notification
        try:
            from services.notifications import notification_service
            if old_value:
                rejection_reason = rejection_data.get('reason', 'No reason provided')
                notification_service.notify_leave_request_rejected(
                    request={
                        'employee_num': old_value.get('employee_num'),
                        'employee_name': old_value.get('employee_name'),
                        'employee_email': old_value.get('employee_email'),
                        'start_date': old_value.get('start_date'),
                        'end_date': old_value.get('end_date'),
                        'days_requested': old_value.get('days_requested'),
                        'rejected_by': rejected_by
                    },
                    reason=rejection_reason
                )
        except Exception as notif_error:
            logger.warning(f"Failed to send rejection notification: {notif_error}")

        return {
            "status": "success",
            "message": "Request rejected"
        }
    except ValueError as ve:
        logger.warning(f"Reject request validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid rejection request")
    except Exception as e:
        logger.error(f"Failed to reject leave request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/leave-requests/{request_id}")
async def cancel_leave_request(
    request: Request,
    request_id: int,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Cancel a PENDING leave request - requires authentication.
    Only works if status is 'PENDING'. Request is completely deleted.

    Cancela una solicitud PENDIENTE - requiere autenticacion.
    Solo funciona si el status es 'PENDING'. La solicitud se elimina completamente.
    """
    try:
        # Get old value before cancellation
        old_requests = database.get_leave_requests()
        old_value = next((r for r in old_requests if r.get('id') == request_id), None)

        result = database.cancel_leave_request(request_id)
        logger.info(f"Leave request {request_id} cancelled by {user.username}: {result}")

        # Audit log
        await log_audit_action(
            request=request,
            action="DELETE",
            entity_type="leave_request",
            entity_id=str(request_id),
            old_value=old_value,
            user=user
        )

        return {
            "status": "success",
            "message": f"申請 #{request_id} がキャンセルされました",
            "cancelled": result
        }
    except ValueError as ve:
        logger.warning(f"Cancel request validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid cancellation request")
    except Exception as e:
        logger.error(f"Cancel request error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/leave-requests/{request_id}/revert")
@router.post("/leave-requests/{request_id}/revert")  # Deprecated: Use PATCH instead
async def revert_leave_request(
    request: Request,
    request_id: int,
    revert_data: dict = None,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Revert an APPROVED leave request.
    Returns the used days to the employee's balance.
    Status changes to 'CANCELLED'.

    Revierte una solicitud YA APROBADA.
    Devuelve los dias usados al balance del empleado.
    El status cambia a 'CANCELLED'.

    Note: PATCH is the preferred method. POST is deprecated and kept for backwards compatibility.
    """
    try:
        if revert_data is None:
            revert_data = {}

        reverted_by = revert_data.get('reverted_by', user.username if user else 'Manager')

        # Get old value before revert
        old_requests = database.get_leave_requests()
        old_value = next((r for r in old_requests if r.get('id') == request_id), None)

        result = database.revert_approved_request(request_id, reverted_by)
        logger.info(f"Leave request {request_id} reverted: {result}")

        # Audit log
        await log_audit_action(
            request=request,
            action="REVERT",
            entity_type="leave_request",
            entity_id=str(request_id),
            old_value=old_value,
            new_value={
                "status": "CANCELLED",
                "reverted_by": reverted_by,
                "days_returned": result['days_returned']
            },
            user=user
        )

        return {
            "status": "success",
            "message": f"申請 #{request_id} が取り消されました。{result['days_returned']}日が返却されました",
            "reverted": result
        }
    except ValueError as ve:
        logger.warning(f"Revert request validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid revert request")
    except Exception as e:
        logger.error(f"Revert request error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
