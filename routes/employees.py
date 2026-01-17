"""
Employees Routes
Endpoints de gestion de empleados y datos de vacaciones
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Query, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .dependencies import (
    get_current_user,
    get_admin_user,
    CurrentUser,
    database,
    logger,
    log_sync_event,
    log_audit_action,
    get_active_employee_nums,
    invalidate_employee_cache,
    DEFAULT_EXCEL_PATH,
    UPLOAD_DIR,
)
import excel_service
from services.search_service import SearchService

router = APIRouter(prefix="/api", tags=["Employees"])

# Thread pool for Excel parsing
_excel_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="excel_parser")


# ============================================
# PYDANTIC MODELS
# ============================================

class EmployeeUpdate(BaseModel):
    """Model for updating employee data."""
    name: Optional[str] = None
    haken: Optional[str] = None
    granted: Optional[float] = Field(None, ge=0, le=40)
    used: Optional[float] = Field(None, ge=0, le=40)
    validate_limit: bool = True


class BulkUpdateRequest(BaseModel):
    """Model for bulk updating multiple employees."""
    employee_nums: List[str] = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=2000, le=2100)
    updates: dict = Field(...)
    validate_limit: bool = True

    @field_validator('employee_nums')
    @classmethod
    def validate_employee_nums(cls, v):
        if len(v) > 50:
            raise ValueError('Maximum 50 employees per operation')
        if len(v) == 0:
            raise ValueError('At least one employee is required')
        return v

    @field_validator('updates')
    @classmethod
    def validate_updates(cls, v):
        if not v:
            raise ValueError('At least one field to update is required')
        valid_fields = {'add_granted', 'add_used', 'set_haken', 'set_granted', 'set_used'}
        invalid = set(v.keys()) - valid_fields
        if invalid:
            raise ValueError(f'Invalid fields: {invalid}. Valid: {valid_fields}')
        return v


class BulkUpdatePreview(BaseModel):
    """Model for previewing bulk update changes."""
    employee_nums: List[str] = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=2000, le=2100)
    updates: dict


# ============================================
# EMPLOYEE ENDPOINTS
# ============================================

@router.get("/employees")
async def get_employees(year: int = None, enhanced: bool = False, active_only: bool = False):
    """
    Returns list of employees from database.

    Args:
        year: Filter by year
        enhanced: If True, includes employee_type and employment_status
        active_only: If True, only returns employees with status '在職中'
    """
    try:
        if enhanced:
            data = database.get_employees_enhanced(year, active_only)
        else:
            data = database.get_employees(year)
        years = database.get_available_years()
        return {"status": "success", "data": data, "years": years}
    except Exception as e:
        logger.error(f"Failed to get employees: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/v1/employees")
async def get_employees_v1(
    year: Optional[int] = None,
    status: Optional[str] = None,
    haken: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=500)
):
    """
    Get employees with enhanced filtering and pagination (v1 API).
    """
    try:
        data = database.get_employees(year=year)

        # Apply filters
        if status:
            genzai_statuses = {str(g['employee_num']): g.get('status', '') for g in database.get_genzai()}
            data = [e for e in data if genzai_statuses.get(str(e['employee_num'])) == status]

        if haken:
            data = [e for e in data if e.get('haken', '').lower() == haken.lower()]

        # Calculate pagination
        total = len(data)
        start = (page - 1) * limit
        end = start + limit
        paginated_data = data[start:end]

        return {
            "status": "success",
            "data": paginated_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Failed to get employees v1: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/v1/genzai")
async def get_genzai_v1(
    status: Optional[str] = None,
    dispatch_name: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=500)
):
    """Get genzai employees with filtering and pagination (v1 API)."""
    try:
        data = database.get_genzai(status=status)

        if dispatch_name:
            data = [e for e in data if e.get('dispatch_name', '').lower() == dispatch_name.lower()]

        total = len(data)
        start = (page - 1) * limit
        end = start + limit

        return {
            "status": "success",
            "data": data[start:end],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Failed to get genzai v1: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/v1/ukeoi")
async def get_ukeoi_v1(
    status: Optional[str] = None,
    contract_business: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=500)
):
    """Get ukeoi employees with filtering and pagination (v1 API)."""
    try:
        data = database.get_ukeoi(status=status)

        if contract_business:
            data = [e for e in data if e.get('contract_business', '').lower() == contract_business.lower()]

        total = len(data)
        start = (page - 1) * limit
        end = start + limit

        return {
            "status": "success",
            "data": data[start:end],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Failed to get ukeoi v1: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sync")
async def sync_employees(request: Request, user: CurrentUser = Depends(get_current_user)):
    """
    Sync vacation data from Excel file.
    Sincroniza datos de vacaciones desde archivo Excel.
    """
    try:
        if not DEFAULT_EXCEL_PATH.exists():
            logger.error(f"Excel file not found: {DEFAULT_EXCEL_PATH}")
            raise HTTPException(
                status_code=404,
                detail="Excel file not found"
            )

        # Run Excel parsing in thread pool
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            _excel_executor,
            excel_service.parse_excel_file,
            DEFAULT_EXCEL_PATH
        )

        database.save_employees(data)
        invalidate_employee_cache()

        # Also parse usage details
        usage_details = await loop.run_in_executor(
            _excel_executor,
            excel_service.parse_yukyu_usage_details,
            DEFAULT_EXCEL_PATH
        )
        database.save_yukyu_usage_details(usage_details)

        log_sync_event("SYNC_EMPLOYEES", {
            "count": len(data),
            "usage_details": len(usage_details),
            "user": user.username if user else None
        })

        logger.info(f"Synced {len(data)} employees + {len(usage_details)} usage details")

        years = database.get_available_years()

        return {
            "status": "success",
            "message": f"Synced {len(data)} employees + {len(usage_details)} usage details",
            "count": len(data),
            "usage_details_count": len(usage_details),
            "years": years
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Upload and process Excel file.
    Carga y procesa archivo Excel.
    """
    try:
        if not file.filename.endswith(('.xlsx', '.xlsm', '.xls')):
            raise HTTPException(status_code=400, detail="File must be an Excel file")

        # Save uploaded file
        upload_path = UPLOAD_DIR / file.filename
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse the file
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            _excel_executor,
            excel_service.parse_excel_file,
            upload_path
        )

        database.save_employees(data)
        invalidate_employee_cache()

        # Parse usage details if available
        try:
            usage_details = await loop.run_in_executor(
                _excel_executor,
                excel_service.parse_yukyu_usage_details,
                upload_path
            )
            database.save_yukyu_usage_details(usage_details)
        except Exception:
            usage_details = []

        log_sync_event("UPLOAD_EXCEL", {
            "filename": file.filename,
            "count": len(data),
            "user": user.username if user else None
        })

        return {
            "status": "success",
            "message": f"Uploaded and synced {len(data)} employees",
            "count": len(data),
            "usage_details_count": len(usage_details)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/reset")
async def reset_employees(user: CurrentUser = Depends(get_admin_user)):
    """
    Clear all employee data from database.
    Requires admin authentication.
    """
    try:
        database.reset_employees()
        invalidate_employee_cache()
        logger.info(f"Employee data reset by {user.username}")
        return {"status": "success", "message": "All employee data has been cleared"}
    except Exception as e:
        logger.error(f"Failed to reset employees: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# SEARCH ENDPOINTS
# ============================================

@router.get("/employees/search")
async def search_employees(
    q: str = Query(..., min_length=1),
    year: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=200)
):
    """
    Search employees by name or employee number.
    Busca empleados por nombre o numero de empleado.
    """
    try:
        search_service = SearchService()
        results = search_service.search_employees(query=q, year=year, limit=limit)

        return {
            "status": "success",
            "query": q,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Failed to search employees: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/full-text")
async def full_text_search(
    q: str = Query(..., min_length=1),
    table: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=500)
):
    """
    Full text search across all employee tables.
    Busqueda de texto completo en todas las tablas de empleados.
    """
    try:
        search_service = SearchService()
        results = search_service.full_text_search(
            query=q,
            table=table,
            year=year,
            limit=limit
        )

        return {
            "status": "success",
            "query": q,
            "table_filter": table,
            "results": results
        }
    except Exception as e:
        logger.error(f"Failed to full text search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/employees")
async def search_employees_detailed(
    q: str = Query(..., min_length=1),
    year: Optional[int] = None,
    haken: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200)
):
    """Search employees with detailed results."""
    try:
        search_service = SearchService()
        results = search_service.search_employees(query=q, year=year, limit=limit)

        if haken:
            results = [r for r in results if r.get('haken', '').lower() == haken.lower()]

        return {
            "status": "success",
            "query": q,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Failed to search employees detailed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/genzai")
async def search_genzai(
    q: str = Query(..., min_length=1),
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200)
):
    """Search genzai employees."""
    try:
        search_service = SearchService()
        results = search_service.search_genzai(query=q, status=status, limit=limit)

        return {
            "status": "success",
            "query": q,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Failed to search genzai: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/ukeoi")
async def search_ukeoi(
    q: str = Query(..., min_length=1),
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200)
):
    """Search ukeoi employees."""
    try:
        search_service = SearchService()
        results = search_service.search_ukeoi(query=q, status=status, limit=limit)

        return {
            "status": "success",
            "query": q,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Failed to search ukeoi: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/staff")
async def search_staff(
    q: str = Query(..., min_length=1),
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200)
):
    """Search staff employees."""
    try:
        search_service = SearchService()
        results = search_service.search_staff(query=q, status=status, limit=limit)

        return {
            "status": "success",
            "query": q,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Failed to search staff: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# EMPLOYEE INFO & UPDATE ENDPOINTS
# ============================================

@router.get("/employees/{employee_num}/leave-info")
async def get_employee_leave_info(employee_num: str, year: Optional[int] = None):
    """
    Get detailed leave information for an employee.
    Obtiene informacion detallada de vacaciones de un empleado.
    """
    try:
        if year is None:
            year = datetime.now().year

        # Get yukyu history
        history = database.get_employee_yukyu_history(employee_num, year)
        if not history:
            raise HTTPException(
                status_code=404,
                detail="Employee data not found"
            )

        # Calculate totals
        total_available = sum(record.get('balance', 0) for record in history)
        total_hours_available = total_available * 8

        # Get hourly wage from genzai or ukeoi
        hourly_wage = 0
        genzai_list = database.get_genzai()
        for emp in genzai_list:
            if emp.get('employee_num') == employee_num:
                hourly_wage = emp.get('hourly_wage', 0)
                break

        if hourly_wage == 0:
            ukeoi_list = database.get_ukeoi()
            for emp in ukeoi_list:
                if emp.get('employee_num') == employee_num:
                    hourly_wage = emp.get('hourly_wage', 0)
                    break

        # Get employee basic data
        employee_data = {
            'employee_num': employee_num,
            'name': history[0].get('name', '') if history else '',
            'haken': history[0].get('haken', '') if history else ''
        }

        # Get pending requests
        pending_requests = database.get_leave_requests(
            status='PENDING',
            employee_num=employee_num,
            year=year
        )

        # Get usage history
        usage_details = database.get_yukyu_usage_details(
            employee_num=employee_num,
            year=year
        )
        usage_history = []
        for detail in usage_details:
            usage_history.append({
                'id': detail.get('id'),
                'date': detail.get('use_date'),
                'days': detail.get('days_used', 1),
                'type': 'usage_detail'
            })

        usage_history.sort(key=lambda x: x.get('date', ''), reverse=True)

        return {
            "status": "success",
            "employee": employee_data,
            "yukyu_history": history,
            "usage_history": usage_history,
            "total_available": round(total_available, 1),
            "total_hours_available": round(total_hours_available, 1),
            "hourly_wage": hourly_wage,
            "pending_requests": pending_requests
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get employee leave info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/employees/{employee_num}/{year}")
async def update_employee(
    request: Request,
    employee_num: str,
    year: int,
    update_data: EmployeeUpdate,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Update employee vacation data.
    Actualiza datos de vacaciones de un empleado.
    """
    try:
        # Get current data
        old_data = database.get_employee_by_num_year(employee_num, year)
        if not old_data:
            raise HTTPException(
                status_code=404,
                detail="Employee not found"
            )

        # Validate balance limit if enabled
        if update_data.validate_limit:
            new_granted = update_data.granted if update_data.granted is not None else old_data.get('granted', 0)
            new_used = update_data.used if update_data.used is not None else old_data.get('used', 0)
            if new_granted - new_used > 40:
                raise HTTPException(
                    status_code=400,
                    detail="Balance cannot exceed 40 days"
                )

        # Prepare update dict
        updates = {}
        if update_data.name is not None:
            updates['name'] = update_data.name
        if update_data.haken is not None:
            updates['haken'] = update_data.haken
        if update_data.granted is not None:
            updates['granted'] = update_data.granted
        if update_data.used is not None:
            updates['used'] = update_data.used

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Update in database
        updated_employee = database.update_employee(employee_num, year, updates)
        invalidate_employee_cache()

        # Audit log
        await log_audit_action(
            request=request,
            action="UPDATE",
            entity_type="employee",
            entity_id=f"{employee_num}_{year}",
            old_value=old_data,
            new_value=updated_employee,
            user=user
        )

        logger.info(f"Employee {employee_num} updated by {user.username}: {updates}")

        return {
            "status": "success",
            "message": f"Employee {employee_num} updated successfully",
            "updated_employee": updated_employee
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update employee error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# BULK UPDATE ENDPOINTS
# ============================================

@router.post("/employees/bulk-update")
async def bulk_update_employees(
    request: Request,
    bulk_data: BulkUpdateRequest,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Bulk update multiple employees in one operation.
    Actualiza multiples empleados en una sola operacion.
    """
    try:
        results = database.bulk_update_employees(
            employee_nums=bulk_data.employee_nums,
            year=bulk_data.year,
            updates=bulk_data.updates,
            updated_by=user.username if user else 'system',
            validate_limit=bulk_data.validate_limit
        )

        invalidate_employee_cache()
        log_sync_event("BULK_UPDATE", {
            "operation_id": results.get("operation_id"),
            "count": results.get("updated_count"),
            "user": user.username if user else None
        })

        return {
            "status": "success" if results["success"] else "partial",
            "message": f"Updated {results['updated_count']} employees",
            "operation_id": results["operation_id"],
            "updated_count": results["updated_count"],
            "errors": results.get("errors", []),
            "warnings": results.get("warnings", [])
        }
    except ValueError as e:
        logger.warning(f"Bulk update validation error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid bulk update request")
    except Exception as e:
        logger.error(f"Bulk update error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/employees/bulk-update/preview")
async def preview_bulk_update(bulk_data: BulkUpdatePreview):
    """
    Preview bulk update changes without applying them.
    Previsualiza cambios de bulk update sin aplicarlos.
    """
    try:
        preview_results = []
        not_found = []
        warnings = []

        for emp_num in bulk_data.employee_nums:
            current = database.get_employee_by_num_year(emp_num, bulk_data.year)
            if not current:
                not_found.append(emp_num)
                continue

            proposed = dict(current)

            # Apply proposed changes
            if 'add_granted' in bulk_data.updates:
                proposed['granted'] = current.get('granted', 0) + bulk_data.updates['add_granted']
            if 'add_used' in bulk_data.updates:
                proposed['used'] = current.get('used', 0) + bulk_data.updates['add_used']
            if 'set_haken' in bulk_data.updates:
                proposed['haken'] = bulk_data.updates['set_haken']
            if 'set_granted' in bulk_data.updates:
                proposed['granted'] = bulk_data.updates['set_granted']
            if 'set_used' in bulk_data.updates:
                proposed['used'] = bulk_data.updates['set_used']

            proposed['balance'] = proposed.get('granted', 0) - proposed.get('used', 0)

            # Check warnings
            if proposed['balance'] < 0:
                warnings.append({
                    "employee_num": emp_num,
                    "name": current['name'],
                    "type": "negative_balance",
                    "message": f"Negative balance: {proposed['balance']:.1f}"
                })
            if proposed['granted'] > 40:
                warnings.append({
                    "employee_num": emp_num,
                    "name": current['name'],
                    "type": "excess_granted",
                    "message": f"Granted exceeds 40: {proposed['granted']:.1f}"
                })

            preview_results.append({
                "employee_num": emp_num,
                "name": current['name'],
                "current": current,
                "proposed": proposed,
                "changes": {
                    k: {"from": current.get(k), "to": proposed.get(k)}
                    for k in ['granted', 'used', 'balance', 'haken']
                    if current.get(k) != proposed.get(k)
                }
            })

        return {
            "status": "preview",
            "total_employees": len(bulk_data.employee_nums),
            "found": len(preview_results),
            "not_found": not_found,
            "warnings": warnings,
            "has_warnings": len(warnings) > 0,
            "preview": preview_results
        }
    except Exception as e:
        logger.error(f"Bulk update preview error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/employees/bulk-update/history")
async def get_bulk_update_history(
    operation_id: Optional[str] = None,
    employee_num: Optional[str] = None,
    limit: int = 100
):
    """Get bulk update operation history."""
    try:
        history = database.get_bulk_update_history(
            operation_id=operation_id,
            employee_num=employee_num,
            limit=limit
        )

        operations = {}
        for record in history:
            op_id = record['operation_id']
            if op_id not in operations:
                operations[op_id] = {
                    "operation_id": op_id,
                    "year": record['year'],
                    "updated_at": record['updated_at'],
                    "updated_by": record['updated_by'],
                    "batch_size": record['batch_size'],
                    "changes": []
                }
            operations[op_id]['changes'].append({
                "employee_num": record['employee_num'],
                "field": record['field_name'],
                "old_value": record['old_value'],
                "new_value": record['new_value']
            })

        return {
            "status": "success",
            "total_records": len(history),
            "operations": list(operations.values())
        }
    except Exception as e:
        logger.error(f"Failed to get bulk update history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/employees/bulk-update/revert/{operation_id}")
async def revert_bulk_update(request: Request, operation_id: str):
    """
    Revert a bulk update operation.
    Revierte una operacion de bulk update.
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        reverted_by = f"user@{client_ip}"

        results = database.revert_bulk_update(
            operation_id=operation_id,
            reverted_by=reverted_by
        )

        log_sync_event("BULK_UPDATE_REVERT", {
            "operation_id": operation_id,
            "reverted_count": results.get("reverted_count")
        })

        return {
            "status": "success" if results["success"] else "error",
            "message": f"Reverted {results['reverted_count']} employees",
            "original_operation_id": operation_id,
            "reverted_count": results["reverted_count"],
            "errors": results.get("errors", []),
            "reverted_at": results["reverted_at"]
        }
    except ValueError as e:
        logger.warning(f"Bulk update revert not found: {str(e)}")
        raise HTTPException(status_code=404, detail="Operation not found")
    except Exception as e:
        logger.error(f"Bulk update revert error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# ACTIVE EMPLOYEES ENDPOINTS
# ============================================

@router.get("/employees/active")
async def get_active_employees(year: int = None):
    """
    Get only ACTIVE employees (status = '在職中') with their yukyu data.
    Obtiene solo empleados ACTIVOS (在職中) con sus datos de yukyu.
    """
    try:
        active_nums = get_active_employee_nums()
        employees = database.get_employees(year=year)

        active_employees = [
            emp for emp in employees
            if str(emp.get('employee_num', '')) in active_nums
        ]

        years = database.get_available_years()

        return {
            "status": "success",
            "data": active_employees,
            "count": len(active_employees),
            "total_in_db": len(employees),
            "filtered_out": len(employees) - len(active_employees),
            "available_years": years
        }
    except Exception as e:
        logger.error(f"Failed to get active employees: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/employees/by-type")
async def get_employees_by_type(
    year: int = None,
    active_only: bool = True,
    filter_by_year: bool = True
):
    """
    Get employees separated by type: Haken, Ukeoi, Staff.
    Obtiene empleados separados por tipo: Haken, Ukeoi, Staff.
    """
    try:
        employees = database.get_employees(year=year)

        genzai_list = database.get_genzai(
            status='在職中' if active_only else None,
            year=year if filter_by_year else None,
            active_in_year=filter_by_year
        )
        ukeoi_list = database.get_ukeoi(
            status='在職中' if active_only else None,
            year=year if filter_by_year else None,
            active_in_year=filter_by_year
        )
        staff_list = database.get_staff(
            status='在職中' if active_only else None,
            year=year if filter_by_year else None,
            active_in_year=filter_by_year
        )

        # Pre-index for O(1) lookup instead of O(n) - fixes N+1 query pattern
        genzai_index = {str(g['employee_num']): g for g in genzai_list if g.get('employee_num')}
        ukeoi_index = {str(u['employee_num']): u for u in ukeoi_list if u.get('employee_num')}
        staff_index = {str(s['employee_num']): s for s in staff_list if s.get('employee_num')}

        genzai_nums = set(genzai_index.keys())
        ukeoi_nums = set(ukeoi_index.keys())
        staff_nums = set(staff_index.keys())

        haken_employees = []
        ukeoi_employees = []
        staff_employees = []

        for emp in employees:
            emp_num = str(emp.get('employee_num', ''))
            emp_enriched = dict(emp)

            if emp_num in genzai_nums:
                genzai_data = genzai_index.get(emp_num, {})  # O(1) lookup
                emp_enriched['type'] = 'haken'
                emp_enriched['dispatch_name'] = genzai_data.get('dispatch_name', '')
                emp_enriched['status'] = genzai_data.get('status', '')
                emp_enriched['hourly_wage'] = genzai_data.get('hourly_wage', 0)
                emp_enriched['hire_date'] = genzai_data.get('hire_date', '')
                emp_enriched['leave_date'] = genzai_data.get('leave_date', '')
                haken_employees.append(emp_enriched)

            elif emp_num in ukeoi_nums:
                ukeoi_data = ukeoi_index.get(emp_num, {})  # O(1) lookup
                emp_enriched['type'] = 'ukeoi'
                emp_enriched['contract_business'] = ukeoi_data.get('contract_business', '')
                emp_enriched['status'] = ukeoi_data.get('status', '')
                emp_enriched['hourly_wage'] = ukeoi_data.get('hourly_wage', 0)
                emp_enriched['hire_date'] = ukeoi_data.get('hire_date', '')
                emp_enriched['leave_date'] = ukeoi_data.get('leave_date', '')
                ukeoi_employees.append(emp_enriched)

            elif emp_num in staff_nums:
                staff_data = staff_index.get(emp_num, {})  # O(1) lookup
                emp_enriched['type'] = 'staff'
                emp_enriched['office'] = staff_data.get('office', '')
                emp_enriched['status'] = staff_data.get('status', '')
                emp_enriched['hire_date'] = staff_data.get('hire_date', '')
                emp_enriched['leave_date'] = staff_data.get('leave_date', '')
                staff_employees.append(emp_enriched)

            elif not active_only:
                emp_enriched['type'] = 'unknown'
                staff_employees.append(emp_enriched)

        return {
            "status": "success",
            "year": year,
            "active_only": active_only,
            "haken": {
                "count": len(haken_employees),
                "employees": haken_employees,
                "total_used": sum(e.get('used', 0) for e in haken_employees),
                "total_granted": sum(e.get('granted', 0) for e in haken_employees)
            },
            "ukeoi": {
                "count": len(ukeoi_employees),
                "employees": ukeoi_employees,
                "total_used": sum(e.get('used', 0) for e in ukeoi_employees),
                "total_granted": sum(e.get('granted', 0) for e in ukeoi_employees)
            },
            "staff": {
                "count": len(staff_employees),
                "employees": staff_employees,
                "total_used": sum(e.get('used', 0) for e in staff_employees),
                "total_granted": sum(e.get('granted', 0) for e in staff_employees)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get employees by type: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
