"""
Pagination Module for YuKyuDATA
Provides pagination utilities for API endpoints to improve performance

Features:
- Offset-based pagination
- Cursor-based pagination (for large datasets)
- Configurable page sizes
- Safe query parameter validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, TypeVar, Generic, Any
from math import ceil

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination query parameters"""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(20, ge=1, le=100, description="Items per page (max 100)")
    sort_by: Optional[str] = Field(None, description="Sort column")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="Sort order")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "per_page": 20,
                "sort_by": "name",
                "sort_order": "asc"
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    data: List[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether next page exists")
    has_prev: bool = Field(..., description="Whether previous page exists")

    @classmethod
    def create(cls, data: List[T], total: int, page: int, per_page: int):
        """Factory method to create paginated response"""
        total_pages = ceil(total / per_page) if per_page > 0 else 0
        return cls(
            data=data,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


def paginate_list(
    items: List[Any],
    page: int = 1,
    per_page: int = 20
) -> tuple[List[Any], int]:
    """
    Paginate a list of items

    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (paginated_items, total_count)
    """
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page

    paginated = items[start:end]
    return paginated, total


def paginate_query(
    query,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
) -> tuple[List[Any], int]:
    """
    Paginate a SQLAlchemy query

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page
        sort_by: Column name to sort by
        sort_order: Sort direction (asc/desc)

    Returns:
        Tuple of (paginated_results, total_count)
    """
    # Get total count before limiting
    total = query.count()

    # Apply offset and limit
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Apply sorting if specified
    if sort_by:
        try:
            # Safely get the column - prevent SQL injection
            sort_column = getattr(query.column_descriptions[0]['entity'], sort_by, None)
            if sort_column is not None:
                if sort_order.lower() == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
        except (AttributeError, IndexError):
            pass  # Silently ignore invalid sort columns

    results = query.all()
    return results, total


def paginate_sqlite_query(
    cursor,
    query: str,
    params: tuple = (),
    page: int = 1,
    per_page: int = 20,
    count_query: Optional[str] = None,
    count_params: tuple = ()
) -> tuple[List[Any], int]:
    """
    Paginate a SQLite query

    Args:
        cursor: SQLite cursor
        query: SELECT query with placeholder for LIMIT and OFFSET
        params: Query parameters
        page: Page number (1-indexed)
        per_page: Items per page
        count_query: Separate COUNT query (optional, auto-generated if not provided)
        count_params: Parameters for count query

    Returns:
        Tuple of (paginated_results, total_count)
    """
    # Get total count
    if count_query:
        cursor.execute(count_query, count_params)
    else:
        # Auto-generate count query
        # Simple heuristic: replace SELECT ... FROM with SELECT COUNT(*) FROM
        count_q = "SELECT COUNT(*) FROM " + query.split("FROM", 1)[1].split("LIMIT")[0].split("ORDER")[0]
        cursor.execute(count_q, params)

    total = cursor.fetchone()[0]

    # Apply limit and offset
    offset = (page - 1) * per_page
    paginated_query = f"{query} LIMIT {per_page} OFFSET {offset}"

    cursor.execute(paginated_query, params)
    results = cursor.fetchall()

    return results, total


class CursorPagination:
    """Cursor-based pagination for large datasets (more efficient than offset)"""

    @staticmethod
    def encode_cursor(value: Any, encoding: str = "utf-8") -> str:
        """Encode cursor value"""
        import base64
        return base64.b64encode(str(value).encode(encoding)).decode('ascii')

    @staticmethod
    def decode_cursor(cursor: str, encoding: str = "utf-8") -> str:
        """Decode cursor value"""
        import base64
        try:
            return base64.b64decode(cursor.encode('ascii')).decode(encoding)
        except Exception:
            return None

    @staticmethod
    def paginate_by_cursor(
        items: List[Any],
        cursor: Optional[str] = None,
        per_page: int = 20,
        get_cursor_value=None
    ) -> tuple[List[Any], Optional[str], bool]:
        """
        Paginate using cursor-based approach

        Args:
            items: List of items (should be sorted)
            cursor: Cursor from previous request
            per_page: Items to return
            get_cursor_value: Function to extract cursor value from item

        Returns:
            Tuple of (items, next_cursor, has_more)
        """
        if get_cursor_value is None:
            get_cursor_value = lambda x: x.get('id') if isinstance(x, dict) else x.id

        # Find starting position
        start_idx = 0
        if cursor:
            decoded = CursorPagination.decode_cursor(cursor)
            for idx, item in enumerate(items):
                if str(get_cursor_value(item)) == decoded:
                    start_idx = idx + 1
                    break

        # Get items for this page
        end_idx = start_idx + per_page
        page_items = items[start_idx:end_idx]

        # Determine if there are more items
        has_more = end_idx < len(items)

        # Create cursor for next page
        next_cursor = None
        if has_more and page_items:
            next_value = get_cursor_value(page_items[-1])
            next_cursor = CursorPagination.encode_cursor(next_value)

        return page_items, next_cursor, has_more


def get_pagination_params(
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    max_per_page: int = 100
) -> tuple[int, int]:
    """
    Validate and return safe pagination parameters

    Args:
        page: Page number from query parameter
        per_page: Items per page from query parameter
        max_per_page: Maximum allowed items per page

    Returns:
        Tuple of (safe_page, safe_per_page)
    """
    # Safe defaults
    safe_page = max(1, page or 1)
    safe_per_page = min(max(1, per_page or 20), max_per_page)

    return safe_page, safe_per_page
