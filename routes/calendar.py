"""
Calendar Routes
Endpoints de calendario y eventos
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta

from .dependencies import (
    database,
    logger,
    get_active_employee_nums,
)

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


@router.get("/events")
async def get_calendar_events(
    year: int = None,
    month: int = None,
    source: str = 'requests',
    active_only: bool = True
):
    """
    Get calendar event data.
    Returns only approved leave requests by default.

    カレンダー用のイベントデータを取得。
    承認済み休暇申請のみを返す（デフォルト）。

    Args:
        year: Year filter
        month: Month filter
        source: Data source
            - 'requests': Approved requests only (default, recommended)
            - 'excel': Excel usage details only
            - 'all': Both (may have duplicates)
        active_only: Show only active employees (default: True)
    """
    try:
        if not year:
            year = datetime.now().year

        active_nums = get_active_employee_nums() if active_only else None

        events = []
        filtered_count = 0

        # Color coding by leave type
        type_colors = {
            'full': '#38bdf8',      # Full day - blue
            'half_am': '#818cf8',   # AM half - purple
            'half_pm': '#f472b6',   # PM half - pink
            'hourly': '#fbbf24'     # Hourly - yellow
        }
        type_labels = {
            'full': '全日',
            'half_am': '午前半休',
            'half_pm': '午後半休',
            'hourly': '時間休'
        }

        # Get approved leave requests (source = 'requests' or 'all')
        if source in ['requests', 'all']:
            approved_requests = database.get_leave_requests(status='APPROVED', year=year)
            for req in approved_requests:
                emp_num = str(req.get('employee_num', ''))

                if active_only and active_nums and emp_num not in active_nums:
                    filtered_count += 1
                    continue

                leave_type = req.get('leave_type', 'full')
                events.append({
                    'id': f"request_{req['id']}",
                    'title': f"{req['employee_name']} ({type_labels.get(leave_type, '休暇')})",
                    'start': req['start_date'],
                    'end': req['end_date'],
                    'color': type_colors.get(leave_type, '#38bdf8'),
                    'type': 'approved_request',
                    'employee_num': req['employee_num'],
                    'employee_name': req['employee_name'],
                    'leave_type': leave_type,
                    'days': req.get('days_requested', 0),
                    'hours': req.get('hours_requested', 0)
                })

        # Get usage details from Excel (source = 'excel' or 'all')
        if source in ['excel', 'all']:
            usage_details = database.get_yukyu_usage_details(year=year, month=month)
            for detail in usage_details:
                emp_num = str(detail.get('employee_num', ''))

                if active_only and active_nums and emp_num not in active_nums:
                    filtered_count += 1
                    continue

                events.append({
                    'id': f"usage_{detail.get('id', '')}",
                    'title': f"{detail['name']} ({detail.get('days_used', 1)}日)",
                    'start': detail['use_date'],
                    'end': detail['use_date'],
                    'color': '#34d399',  # Green
                    'type': 'usage_detail',
                    'employee_num': detail['employee_num'],
                    'employee_name': detail['name'],
                    'days': detail.get('days_used', 1)
                })

        return {
            "status": "success",
            "year": year,
            "month": month,
            "source": source,
            "active_only": active_only,
            "count": len(events),
            "filtered_out": filtered_count,
            "events": events
        }
    except Exception as e:
        logger.error(f"Failed to get calendar events: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/summary/{year}/{month}")
async def get_calendar_month_summary(year: int, month: int, source: str = 'requests'):
    """
    Get monthly calendar summary.
    Returns leave count per day.

    月別カレンダーサマリーを取得。
    各日の休暇取得人数を返す。

    Args:
        source: Data source ('requests', 'excel', 'all') - default is 'requests'
    """
    try:
        import calendar
        from collections import defaultdict

        _, days_in_month = calendar.monthrange(year, month)

        daily_counts = defaultdict(lambda: {'count': 0, 'employees': []})

        # Approved requests (source = 'requests' or 'all')
        if source in ['requests', 'all']:
            approved = database.get_leave_requests(status='APPROVED', year=year)
            for req in approved:
                start = datetime.strptime(req['start_date'], '%Y-%m-%d')
                end = datetime.strptime(req['end_date'], '%Y-%m-%d')

                current = start
                while current <= end:
                    if current.year == year and current.month == month:
                        day_key = current.strftime('%Y-%m-%d')
                        daily_counts[day_key]['count'] += 1
                        daily_counts[day_key]['employees'].append({
                            'name': req['employee_name'],
                            'type': req.get('leave_type', 'full')
                        })
                    current = current + timedelta(days=1)

        # Usage details (source = 'excel' or 'all')
        if source in ['excel', 'all']:
            usage = database.get_yukyu_usage_details(year=year, month=month)
            for detail in usage:
                day_key = detail['use_date']
                exists = any(e['name'] == detail['name'] for e in daily_counts[day_key]['employees'])
                if not exists:
                    daily_counts[day_key]['count'] += 1
                    daily_counts[day_key]['employees'].append({
                        'name': detail['name'],
                        'type': 'usage'
                    })

        return {
            "status": "success",
            "year": year,
            "month": month,
            "source": source,
            "days_in_month": days_in_month,
            "daily_summary": dict(daily_counts)
        }
    except Exception as e:
        logger.error(f"Failed to get calendar month summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
