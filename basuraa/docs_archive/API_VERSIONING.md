# API Versioning Strategy

## Overview

YuKyuDATA API implements versioning to support backward compatibility while allowing for future improvements.

**Current Status:**
- **v0 (Deprecated):** Original endpoints at `/api/*` - Will be sunset on Mar 31, 2026
- **v1 (Current):** New endpoints at `/api/v1/*` - Primary version

## API Versions

### v0 (Deprecated - /api/*)

All original endpoints are available at `/api/*` but are marked as deprecated.

**Deprecation Timeline:**
- **Now:** Available with deprecation warnings
- **Mar 31, 2026:** Shutdown deadline (Sunset header)
- **Migrate to v1** by this date

**Example:**
```bash
GET /api/health
GET /api/employees
POST /api/leave-requests
```

**Response Headers:**
```
Deprecation: true
API-Deprecated: true
Sunset: Sun, 31 Mar 2026 23:59:59 GMT
Link: </api/v1/{path}>; rel="successor-version"
API-Supported-Versions: v0 (deprecated), v1
Warning: 299 - "Deprecated API endpoint. Migrate to /api/v1/ by 31 Mar 2026."
```

### v1 (Current - /api/v1/*)

All endpoints are now available under `/api/v1/` with enhanced features:

- **Standardized Response Format:** All responses use the `APIResponse` model
- **Improved Pagination:** Enhanced page/limit parameters on list endpoints
- **Better Documentation:** Enhanced docstrings and OpenAPI metadata
- **Consistent Error Handling:** Standardized error response format

**Example:**
```bash
GET /api/v1/health
GET /api/v1/employees
POST /api/v1/leave-requests
GET /api/v1/compliance/5day
```

## Endpoint Structure

### Total Endpoints: 156

```
/api/v1/
├── auth/              (12 endpoints)
│   ├── POST   /login
│   ├── POST   /refresh
│   ├── POST   /logout
│   └── ...
│
├── employees/         (21 endpoints)
│   ├── GET    /          (list with pagination)
│   ├── GET    /{emp}/{year}
│   ├── POST   /          (create)
│   ├── PUT    /{emp}/{year}
│   └── ...
│
├── leave-requests/    (9 endpoints)
│   ├── GET    /          (list pending requests)
│   ├── POST   /          (create)
│   ├── PATCH  /{id}/approve
│   └── ...
│
├── yukyu/             (9 endpoints)
│   ├── GET    /usage-details/{emp}/{year}
│   ├── POST   /usage-details
│   ├── PUT    /usage-details/{id}
│   └── ...
│
├── compliance/        (19 endpoints)
│   ├── GET    /5day?year=2025
│   ├── GET    /advanced/matrix
│   ├── GET    /expiring-soon
│   └── ...
│
├── fiscal/            (7 endpoints)
│   ├── POST   /carryover
│   ├── GET    /period
│   └── ...
│
├── analytics/         (7 endpoints)
│   ├── GET    /stats
│   ├── GET    /trends
│   └── ...
│
├── reports/           (11 endpoints)
│   ├── GET    /monthly
│   ├── GET    /annual
│   ├── POST   /pdf
│   └── ...
│
├── notifications/     (13 endpoints)
│   ├── GET    /
│   ├── PATCH  /{id}/read
│   ├── PATCH  /read-all
│   └── ...
│
├── system/            (17 endpoints)
│   ├── GET    /health
│   ├── GET    /status
│   └── ...
│
└── (+ other domains)
```

## Standard Response Format

All v1 endpoints return responses in this format:

### Success Response (2xx)
```json
{
  "success": true,
  "status": "success",
  "data": { /* response data */ },
  "message": "Operation completed successfully",
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150,
    "total_pages": 3
  },
  "timestamp": "2026-01-17T10:30:45.123456Z",
  "version": "v1"
}
```

### Error Response (4xx/5xx)
```json
{
  "success": false,
  "status": "error",
  "error": "ValidationError",
  "message": "Invalid input data",
  "errors": ["Field 'employee_num' is required"],
  "timestamp": "2026-01-17T10:30:45.123456Z",
  "version": "v1"
}
```

## Pagination

All list endpoints in v1 support pagination:

**Query Parameters:**
```
GET /api/v1/employees?page=1&limit=50&year=2025

Query Parameters:
- page: int (default: 1, minimum: 1)
- limit: int (default: 50, minimum: 1, maximum: 500)
- Additional filters: year, active_only, etc.
```

**Response Pagination Info:**
```json
{
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 156,
    "total_pages": 4
  }
}
```

## Migration Guide

### For Clients

#### Step 1: Update Endpoint Paths
Change from `/api/*` to `/api/v1/*`

Before:
```javascript
const response = await fetch('/api/employees');
```

After:
```javascript
const response = await fetch('/api/v1/employees');
```

#### Step 2: Handle New Response Format
v1 responses are wrapped in the APIResponse format.

Before (v0):
```javascript
// v0 returned mixed formats
const employees = response.data;
const count = employees.length;
```

After (v1):
```javascript
const result = await response.json();
const employees = result.data;
const pagination = result.pagination;
const total = pagination.total;
```

#### Step 3: Use Pagination
v1 list endpoints support consistent pagination.

```javascript
// With pagination
const response = await fetch('/api/v1/employees?page=1&limit=50');
const result = await response.json();
console.log(`Showing ${result.data.length} of ${result.pagination.total} employees`);
```

### For Developers

#### Creating v1 Endpoints

1. **Location:** Create endpoint in `routes/v1/{domain}.py`
2. **Prefix:** Use empty prefix `prefix=""` (parent router has `/api/v1`)
3. **Response:** Use `APIResponse` model or response helpers
4. **Pagination:** Add `page` and `limit` query parameters for lists

```python
from fastapi import APIRouter, Query
from routes.responses import APIResponse, paginated_response

router = APIRouter(prefix="/employees", tags=["Employees v1"])

@router.get("", response_model=APIResponse)
async def list_employees_v1(
    year: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
):
    """Get employees with pagination"""
    # Get employees from database
    employees = get_employees(year=year)
    
    # Paginate results
    total = len(employees)
    start = (page - 1) * limit
    end = start + limit
    page_data = employees[start:end]
    
    # Return paginated response
    return paginated_response(
        data=page_data,
        page=page,
        limit=limit,
        total=total,
        message="Employees retrieved successfully"
    )
```

## Deprecation Headers

### Understanding RFC 7234 Deprecation Header

All v0 endpoint responses include:

| Header | Value | Meaning |
|--------|-------|---------|
| `Deprecation` | `true` | This endpoint is deprecated |
| `API-Deprecated` | `true` | API level deprecation |
| `Sunset` | `Sun, 31 Mar 2026 23:59:59 GMT` | When v0 will be shutdown |
| `Link` | `</api/v1/{path}>; rel="successor-version"` | Link to v1 equivalent |
| `Warning` | `299 - "Deprecated API endpoint..."` | Human-readable warning |
| `API-Supported-Versions` | `v0 (deprecated), v1` | Supported versions |

### Detecting Deprecation in Code

```javascript
// Check if endpoint is deprecated
fetch('/api/employees')
  .then(response => {
    if (response.headers.get('deprecation') === 'true') {
      console.warn('This endpoint is deprecated. Use /api/v1/employees instead.');
      // Get successor version
      const link = response.headers.get('link');
      console.log('Migrate to:', link);
    }
    return response.json();
  });
```

## Version Header Support

All responses include version information:

```
API-Version: v1
API-Supported-Versions: v0 (deprecated), v1
X-API-Version: v1
```

### Accept-Version Header

Clients can optionally request a specific API version:

```bash
curl -H "Accept-Version: v1" http://localhost:8000/api/health
```

## Implementation Details

### Router Structure
```
routes/
├── v0/                    # Original endpoints
│   ├── __init__.py       # Routers (v0 endpoints)
│   ├── employees.py
│   ├── leave_requests.py
│   └── ...
│
└── v1/                    # New versioned endpoints
    ├── __init__.py       # Router factory: router_v1
    ├── employees.py      # Adapted from v0 (prefix: "")
    ├── leave_requests.py
    └── ...
```

### Middleware

**DeprecationHeaderMiddleware**
- Detects v0 endpoints (`/api/*` but not `/api/v*`)
- Adds deprecation headers
- Provides migration path via Link header

**VersionHeaderMiddleware**
- Adds version information to all responses
- Respects `Accept-Version` header from client

### Response Helpers

All v1 endpoints should use response helpers from `routes.responses`:

```python
from routes.responses import (
    success_response,
    error_response,
    paginated_response,
    created_response,
    updated_response,
    deleted_response,
)
```

## Timeline

| Date | Event |
|------|-------|
| **2026-01-17** | v1 launched alongside v0 |
| **2026-01-17 to 2026-03-31** | Grace period - both versions available |
| **2026-03-31** | v0 sunset deadline - v1 becomes only version |

## Testing

Run API versioning tests:

```bash
# Test both v0 and v1 endpoints
pytest tests/test_api_versioning.py -v

# Test specific endpoint versions
pytest tests/test_api_versioning.py::TestV0Endpoints -v
pytest tests/test_api_versioning.py::TestV1Endpoints -v
```

## FAQ

**Q: Can I continue using v0 endpoints?**
A: Yes, until Mar 31, 2026. You'll receive deprecation warnings.

**Q: What happens on the sunset date?**
A: v0 endpoints will be removed. Only v1 will be available.

**Q: How long is the migration period?**
A: 2.5 months (Jan 17 - Mar 31, 2026)

**Q: Are there breaking changes in v1?**
A: Response format has changed. See Migration Guide above.

**Q: Can I mix v0 and v1 endpoints?**
A: Yes, both work simultaneously during grace period.

**Q: How do I know which endpoints I'm using?**
A: Check request URLs or look for deprecation headers in responses.

## Support

For API versioning issues or questions:
1. Check this document
2. Review test file: `tests/test_api_versioning.py`
3. Check endpoint documentation: `http://localhost:8000/docs` (v1 marked as v1)
4. Review migration examples in CLAUDE_MEMORY.md
