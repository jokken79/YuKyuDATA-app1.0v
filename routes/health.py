"""
Health & Status Routes
Endpoints de salud del sistema y estado del proyecto
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
from datetime import datetime, timedelta, timezone
import subprocess
import psutil

from .dependencies import (
    database,
    logger,
    FISCAL_CONFIG,
    DEFAULT_EXCEL_PATH,
    EMPLOYEE_REGISTRY_PATH,
)

router = APIRouter(tags=["Health"])

# Track server start time for uptime calculation
SERVER_START_TIME = datetime.now(timezone.utc)
PROJECT_VERSION = "2.1.0"


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_git_commits(limit: int = 5) -> list:
    """Get recent git commits."""
    try:
        result = subprocess.run(
            ["git", "log", f"--oneline", f"-{limit}", "--format=%H|%s|%an|%ad", "--date=iso"],
            cwd=str(Path(__file__).parent.parent),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0][:7],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3]
                        })
            return commits
    except Exception as e:
        logger.warning(f"Failed to get git commits: {e}")
    return []


def get_commits_per_day(days: int = 7) -> dict:
    """Get commit count per day for the last N days."""
    try:
        result = subprocess.run(
            ["git", "log", f"--since={days} days ago", "--format=%ad", "--date=short"],
            cwd=str(Path(__file__).parent.parent),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            from collections import Counter
            dates = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            counts = Counter(dates)
            today = datetime.now().date()
            result_dict = {}
            for i in range(days - 1, -1, -1):
                day = (today - timedelta(days=i)).isoformat()
                result_dict[day] = counts.get(day, 0)
            return result_dict
    except Exception as e:
        logger.warning(f"Failed to get commits per day: {e}")
    return {}


def load_memory_store() -> dict:
    """Load memory_store.json if it exists."""
    memory_path = Path(__file__).parent.parent / "agents" / "memory_store.json"
    if memory_path.exists():
        try:
            import json
            with open(memory_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load memory_store.json: {e}")
    return {}


def get_system_info() -> dict:
    """Get system resource information."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": round(disk.percent, 1)
            }
        }
    except Exception as e:
        logger.warning(f"Failed to get system info: {e}")
        return {}


def get_uptime() -> dict:
    """Get server uptime."""
    now = datetime.now(timezone.utc)
    uptime_delta = now - SERVER_START_TIME
    total_seconds = int(uptime_delta.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return {
        "started_at": SERVER_START_TIME.isoformat(),
        "uptime_seconds": total_seconds,
        "uptime_human": f"{days}d {hours}h {minutes}m {seconds}s"
    }


# ============================================
# HEALTH ENDPOINTS
# ============================================

@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": PROJECT_VERSION
    }


@router.get("/health")
async def health_check_detailed():
    """Health check endpoint with database and connection pool status."""
    try:
        employees_count = len(database.get_employees())

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": {
                "type": "postgresql" if database.USE_POSTGRESQL else "sqlite",
                "connected": True,
                "employees_count": employees_count
            }
        }

        if database.USE_POSTGRESQL:
            try:
                from database.connection import PostgreSQLConnectionPool
                pool = PostgreSQLConnectionPool._pool
                if pool:
                    health_status["database"]["connection_pool"] = {
                        "status": "initialized",
                        "min_connections": pool._minconn,
                        "max_connections": pool._maxconn
                    }
            except Exception as e:
                health_status["database"]["connection_pool"] = {
                    "status": "error",
                    "message": str(e)
                }

        return health_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


@router.get("/api/db-status")
async def get_db_status():
    """
    Return current database status.
    Useful for debugging and verifying data persistence.

    Retorna el estado actual de la base de datos.
    """
    try:
        employees = database.get_employees()
        genzai = database.get_genzai()
        ukeoi = database.get_ukeoi()
        years = database.get_available_years()

        vacation_excel_exists = DEFAULT_EXCEL_PATH.exists()
        registry_excel_exists = EMPLOYEE_REGISTRY_PATH.exists()

        return {
            "status": "success",
            "database": {
                "employees_count": len(employees),
                "genzai_count": len(genzai),
                "ukeoi_count": len(ukeoi),
                "available_years": years,
                "is_empty": len(employees) == 0
            },
            "excel_files": {
                "vacation_excel": {
                    "path": str(DEFAULT_EXCEL_PATH),
                    "exists": vacation_excel_exists
                },
                "employee_registry": {
                    "path": str(EMPLOYEE_REGISTRY_PATH),
                    "exists": registry_excel_exists
                }
            },
            "message": "データは正常に保存されています" if len(employees) > 0 else "データベースは空です - Syncボタンを押してください"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/api/info")
async def app_info():
    """Application information."""
    return {
        "name": "YuKyuDATA-app",
        "version": PROJECT_VERSION,
        "description": "Employee Paid Leave Management System (有給休暇管理システム)",
        "features": [
            "Vacation tracking and balance management",
            "Leave request workflow",
            "Monthly reports (21日〜20日 period)",
            "5-day compliance monitoring",
            "LIFO deduction logic",
            "Year-end carry-over processing",
            "Excel bidirectional sync",
            "Annual ledger generation"
        ],
        "fiscal_config": FISCAL_CONFIG
    }


@router.get("/api/project-status")
async def get_project_status():
    """
    Return complete project status for the dashboard.
    Includes: version, commits, TODOs, features, DB status, system, errors.

    Retorna el estado completo del proyecto para el dashboard.
    """
    try:
        memory = load_memory_store()

        employees = database.get_employees()
        genzai = database.get_genzai()
        ukeoi = database.get_ukeoi()

        try:
            staff = database.get_staff()
            staff_count = len(staff)
        except Exception:
            staff_count = 0

        try:
            leave_requests = database.get_leave_requests()
            leave_count = len(leave_requests) if leave_requests else 0
        except Exception:
            leave_count = 0

        try:
            with database.get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM yukyu_usage_details")
                usage_count = c.fetchone()[0]
        except Exception:
            usage_count = 0

        todos = []
        if memory.get("todos"):
            for todo_id, todo in memory["todos"].items():
                todos.append({
                    "id": todo_id,
                    "title": todo.get("title", ""),
                    "description": todo.get("description", ""),
                    "priority": todo.get("priority", "medium"),
                    "category": todo.get("category", "general"),
                    "completed": todo.get("completed", False),
                    "created_at": todo.get("created_at")
                })

        features = memory.get("features", [])

        errors = []
        if memory.get("errors"):
            for err_id, err in memory["errors"].items():
                errors.append({
                    "id": err_id,
                    "pattern": err.get("error_pattern", ""),
                    "solution": err.get("solution", ""),
                    "files": err.get("related_files", []),
                    "verified": err.get("verified", False)
                })

        learnings_count = sum(len(cat) for cat in memory.get("learnings", {}).values())

        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": {
                "name": "YuKyuDATA-app",
                "version": PROJECT_VERSION,
                "description": "Employee Paid Leave Management System"
            },
            "git": {
                "recent_commits": get_git_commits(5),
                "commits_per_day": get_commits_per_day(7)
            },
            "database": {
                "type": "postgresql" if database.USE_POSTGRESQL else "sqlite",
                "tables": {
                    "employees": len(employees),
                    "genzai": len(genzai),
                    "ukeoi": len(ukeoi),
                    "staff": staff_count,
                    "leave_requests": leave_count,
                    "usage_details": usage_count
                },
                "total_records": len(employees) + len(genzai) + len(ukeoi) + staff_count + leave_count + usage_count
            },
            "todos": {
                "items": todos,
                "pending_count": sum(1 for t in todos if not t.get("completed")),
                "completed_count": sum(1 for t in todos if t.get("completed"))
            },
            "features": {
                "items": features,
                "total_count": len(features),
                "completed_count": sum(1 for f in features if f.get("status") == "completed")
            },
            "errors": {
                "items": errors,
                "unresolved_count": sum(1 for e in errors if not e.get("verified"))
            },
            "learnings_count": learnings_count,
            "system": {
                **get_system_info(),
                **get_uptime()
            }
        }
    except Exception as e:
        logger.error(f"Error getting project status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/status", response_class=HTMLResponse)
async def status_page():
    """
    Serve the status dashboard HTML page.
    Sirve la pagina HTML del dashboard de estado.
    """
    try:
        template_path = Path(__file__).parent.parent / "templates" / "status.html"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return """
            <html>
            <head><title>Status</title></head>
            <body>
                <h1>YuKyuDATA Status</h1>
                <p>Status template not found. Use <a href="/api/project-status">/api/project-status</a> for JSON data.</p>
            </body>
            </html>
            """
    except Exception as e:
        return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>"
