"""
Pagination Utilities
Helper functions and models for paginating API responses
"""

from typing import Generic, List, TypeVar, Optional
from pydantic import BaseModel, Field
from math import ceil


T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints
    
    Usage:
        @app.get("/items")
        async def get_items(pagination: PaginationParams = Depends()):
            return paginate(all_items, pagination)
    """
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page (max 1000)")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database queries"""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response model
    
    Example:
        {
            "items": [...],
            "total": 1399,
            "page": 1,
            "page_size": 50,
            "total_pages": 28,
            "has_next": true,
            "has_prev": false
        }
    """
    items: List[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


def paginate(
    items: List[T],
    params: PaginationParams,
    total: Optional[int] = None
) -> PaginatedResponse[T]:
    """
    Paginate a list of items
    
    Args:
        items: List of items to paginate (can be full list or just page items)
        params: Pagination parameters
        total: Total count (if items is already sliced, provide total count)
    
    Returns:
        PaginatedResponse with pagination metadata
    
    Example:
        # Option 1: Paginate full list (simple but inefficient for large datasets)
        all_employees = database.get_all_employees()
        result = paginate(all_employees, pagination_params)
        
        # Option 2: Pre-sliced with total count (efficient)
        employees, total = database.get_employees_paginated(
            offset=params.offset,
            limit=params.limit
        )
        result = paginate(employees, params, total=total)
    """
    # If total not provided, assume items is the full list
    if total is None:
        total = len(items)
        # Slice the items
        start = params.offset
        end = start + params.page_size
        page_items = items[start:end]
    else:
        # Items is already sliced
        page_items = items
    
    total_pages = ceil(total / params.page_size) if params.page_size > 0 else 0
    
    return PaginatedResponse(
        items=page_items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
        has_next=params.page < total_pages,
        has_prev=params.page > 1
    )


def create_pagination_links(
    base_url: str,
    params: PaginationParams,
    total_pages: int
) -> dict:
    """
    Create pagination navigation links (REST HATEOAS style)
    
    Args:
        base_url: Base URL for the endpoint
        params: Current pagination parameters
        total_pages: Total number of pages
    
    Returns:
        Dict with navigation links
    
    Example:
        {
            "self": "/api/employees?page=2&page_size=50",
            "first": "/api/employees?page=1&page_size=50",
            "prev": "/api/employees?page=1&page_size=50",
            "next": "/api/employees?page=3&page_size=50",
            "last": "/api/employees?page=28&page_size=50"
        }
    """
    links = {
        "self": f"{base_url}?page={params.page}&page_size={params.page_size}",
        "first": f"{base_url}?page=1&page_size={params.page_size}"
    }
    
    if params.page > 1:
        links["prev"] = f"{base_url}?page={params.page - 1}&page_size={params.page_size}"
    
    if params.page < total_pages:
        links["next"] = f"{base_url}?page={params.page + 1}&page_size={params.page_size}"
    
    if total_pages > 0:
        links["last"] = f"{base_url}?page={total_pages}&page_size={params.page_size}"
    
    return links
