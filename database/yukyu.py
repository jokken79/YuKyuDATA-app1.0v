from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import func, and_
from orm import SessionLocal, YukyuUsageDetail


def get_yukyu_usage_details(
    employee_num: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get yukyu usage details with optional filters."""
    with SessionLocal() as session:
        query = session.query(YukyuUsageDetail)

        if employee_num:
            query = query.filter(YukyuUsageDetail.employee_num == employee_num)
        if year:
            query = query.filter(YukyuUsageDetail.year == year)
        if month:
            query = query.filter(YukyuUsageDetail.month == month)

        details = query.order_by(YukyuUsageDetail.use_date).all()
        return [d.to_dict() for d in details]


def get_usage_detail_by_id(detail_id) -> Optional[Dict[str, Any]]:
    """Get a single usage detail record by ID."""
    with SessionLocal() as session:
        detail = session.query(YukyuUsageDetail).filter(
            YukyuUsageDetail.id == str(detail_id)
        ).first()
        return detail.to_dict() if detail else None


def create_yukyu_usage_detail(
    employee_num: str,
    name: str,
    use_date: str,
    days_used: float,
    year: int
) -> str:
    """Create a new yukyu usage detail record."""
    with SessionLocal() as session:
        use_dt = datetime.strptime(use_date, '%Y-%m-%d')
        detail = YukyuUsageDetail(
            employee_num=employee_num,
            name=name,
            use_date=use_date,
            days_used=days_used,
            year=year,
            month=use_dt.month,
            source='manual',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(detail)
        session.commit()
        session.refresh(detail)
        return detail.id


def update_yukyu_usage_detail(
    detail_id,
    updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update a yukyu usage detail record."""
    with SessionLocal() as session:
        detail = session.query(YukyuUsageDetail).filter(
            YukyuUsageDetail.id == str(detail_id)
        ).first()
        if not detail:
            return None

        for key, value in updates.items():
            if hasattr(detail, key):
                setattr(detail, key, value)

        detail.updated_at = datetime.now()
        session.commit()
        session.refresh(detail)
        return detail.to_dict()


def delete_yukyu_usage_detail(detail_id):
    """Delete a yukyu usage detail record."""
    with SessionLocal() as session:
        detail = session.query(YukyuUsageDetail).filter(
            YukyuUsageDetail.id == str(detail_id)
        ).first()
        if detail:
            session.delete(detail)
            session.commit()


def get_monthly_usage_summary(year: int) -> List[Dict[str, Any]]:
    """Get monthly usage summary for a year."""
    with SessionLocal() as session:
        results = session.query(
            YukyuUsageDetail.month,
            func.count(func.distinct(YukyuUsageDetail.employee_num)).label('employee_count'),
            func.sum(YukyuUsageDetail.days_used).label('total_days'),
            func.count(YukyuUsageDetail.id).label('usage_count')
        ).filter(
            YukyuUsageDetail.year == year
        ).group_by(
            YukyuUsageDetail.month
        ).order_by(
            YukyuUsageDetail.month
        ).all()

        summary = []
        for row in results:
            summary.append({
                'month': row.month,
                'employee_count': row.employee_count,
                'total_days': float(row.total_days or 0),
                'usage_count': row.usage_count,
            })
        return summary
